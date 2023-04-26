import uasyncio as asyncio
from pyb import Pin
from wVOG import lenses, timers
import time


class VOG:
    def __init__(self, config, results_cb, update_lens, broadcast):
        self._cfg = config
        self._results_cb = results_cb
        self._update_lens = update_lens
        self._broadcast = broadcast

        # Lenses
        self._lens_is_clear = False

        # Switches
        self._debounced = True
        self._resp_value_old = 0
        self._response = Pin('Y9', mode=Pin.IN, pull=Pin.PULL_UP)
        asyncio.create_task(self._response_listener())

        # Toggle Timer
        self._ab_timer = timers.ABTimeAccumulator()

        # Experiment
        self._exp_running = False
        self._exp_task = None

        # Trial
        self._trial_running = False
        self._request_peek = False
        
        self._first_peek = True
    #############################################
    # Public Methods
    #############################################
    def begin_experiment(self):
        self._broadcast('exp>1')
        self._exp_running = True
        self._exp_task = asyncio.create_task(self._exp_loop())
        
    def end_experiment(self):
        self._broadcast('exp>0')
        self._exp_running = False
        self._exp_task.cancel()
        
    def begin_trial(self):
        self._lens_is_clear = not int(self._cfg['srt'])
        if not self._trial_running:
            self._broadcast('trl>1')
            self._trial_running = True
        self._first_peek = True

    def end_trial(self):
        if self._trial_running:
            results = self._ab_timer.stop()
            self._trial_running = False
            self._broadcast('trl>0')
            self._update_lens('x', 0)
            print('end')
            self._lens_is_clear = False
            self._send_results(results)

    #############################################
    # Private Utility Functions
    #############################################
    async def _response_listener(self):
        response_ms = 0
        old_state = 0
        then = 0
        debounced = True
        debounce_dur = int(self._cfg['dbc'])

        while True:
            now_ms = time.ticks_ms()
            
            if self._cfg['typ'] == 'direct':
                now = self._response.value()
                d = now - then
                if d < 0:
                    self._update_lens('x', 1, 0)
                elif d > 0:
                    self._update_lens('x', 0, 0)
                then = now

            if debounced:
                state = self._response.value()
                clicked = old_state - state == 1
                old_state = state

                if clicked and debounced:
                    debounced = False
                    response_ms = now_ms
                    self._handle_valid_response()
            else:
                if time.ticks_diff(now_ms, response_ms) >= debounce_dur:
                    debounced = True

            await asyncio.sleep(0)

    def _toggle_lenses(self, now_ms, results = None):
        self._lens_is_clear = not self._lens_is_clear
        self._update_lens('x', self._lens_is_clear)
        if not results:
            results = self._ab_timer.toggle(now_ms)
        self._send_results(results)

    def _handle_valid_response(self):
        type = self._cfg["typ"]
        if self._exp_running:
            if self._trial_running:
                if type == "cycle":
                    self.end_trial()
                elif type == "peek":
                    self._request_peek = True
                elif type == "eBlindfold":
                    self.end_trial()

    def _send_results(self, dta):
        if int(self._cfg['dta']):  # Send all if data
            results_string = ','.join([str(i) for i in dta])
            self._results_cb(results_string)
        elif dta[0] == 'X':  # Else just send last transition
            results_string = ','.join([str(i) for i in dta])
            self._results_cb(results_string)

    #############################################
    # TRIAL TYPES -- CORE LOOPING FUNCTIONALITY
    #############################################

    async def _exp_loop(self):
        exp_type = self._cfg['typ']
        open_ms = int(self._cfg['opn'])
        close_ms = int(self._cfg['cls'])
        transition_time = 0
        
        start_open = int(self._cfg['srt'])
        
        
        while True:
            if self._trial_running:
                time_now = time.ticks_ms()

                # Run this code once at trial startup
                if not self._ab_timer.running:
                    times = self._ab_timer.start(time_now, start_open = not start_open)
                    self._toggle_lenses(time_now)
                    transition_time = time_now

                delta = time.ticks_diff(time_now, transition_time)

                # Check if lenses are clear and should be opaque
                if self._lens_is_clear:
                    if delta >= open_ms:  # Is the open time expired?
                        self._toggle_lenses(time_now)
                        transition_time = time_now

                # Check if lenses are opaque and should be clear
                else:
                    if delta >= close_ms or (exp_type == 'peek' and self._first_peek):
                        if exp_type == 'peek':
                            if self._request_peek:
                                self._toggle_lenses(time_now)
                                self._request_peek = False
                                self._first_peek = False
                                transition_time = time_now
                        else:
                            transition_time = time_now
                            self._toggle_lenses(time_now)

            await asyncio.sleep(0)


