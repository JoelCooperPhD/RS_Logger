import uasyncio as asyncio
from pyb import Pin
from wVOG import lenses, timers
import time


class VOG:
    def __init__(self, config=None, results_cb=None):
        self._cfg = config
        self._results_cb = results_cb

        # Lenses
        self._lenses_open = False
        self._lenses = lenses.Lenses()

        # Switches
        self._debounced = True
        self._resp_value_old = 0
        self._response = Pin('Y9', mode=Pin.IN, pull=Pin.PULL_UP)
        asyncio.create_task(self._response_listener())

        # Toggle Timer
        self._ab_timer = timers.ABTimeAccumulator()

        # Experiment
        self._exp_task = None

        # Trial
        self._trial_running = False
        self._request_peek = False

    #############################################
    # Public Methods
    #############################################
    def begin_experiment(self):
        self._exp_task = asyncio.create_task(self._exp_loop())

    def end_experiment(self):
        self._exp_task.cancel()

    def begin_trial(self):
        self._trial_running = True

    def end_trial(self):
        self._trial_running = False

        results = self._ab_timer.stop()
        self._lenses.opaque()
        self._lenses_open = False
        self._send_results(results)

    #############################################
    # Private Utility Functions
    #############################################
    async def _response_listener(self):
        response_ms = 0
        old_state = 0
        debounced = True
        debounce_dur = self._cfg['debounce']

        while True:
            now_ms = time.ticks_ms()

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

    def _open(self):
        results = self._ab_timer.toggle()
        self._lenses.clear()
        self._lenses_open = True

        self._send_results(results)

    def _close(self):
        results = self._ab_timer.toggle()
        self._lenses.opaque()
        self._lenses_open = False
        self._send_results(results)

    def _handle_valid_response(self):
        type = self._cfg["type"]
        if self._trial_running:
            if type == "cycle":
                self.end_trial()
            elif type == "peek":
                self._request_peek = True
        else:
            if type == "cycle": self.begin_trial()

    def _send_results(self, dta):
        if self._cfg['data']:  # Send all if data
            results_string = ','.join([str(i) for i in dta])
            self._results_cb(results_string)
        elif dta[0] == 'X':  # Else just send last transition
            results_string = ','.join([str(i) for i in dta])
            self._results_cb(results_string)

    #############################################
    # TRIAL TYPES -- CORE LOOPING FUNCTIONALITY
    #############################################

    async def _exp_loop(self):
        exp_type = self._cfg['type']
        open_ms = self._cfg['open_ms']
        close_ms = self._cfg['close_ms']
        transition_time = 0

        while True:
            if self._trial_running:
                time_now = time.ticks_ms()

                # Run this code once at trial startup
                if not self._ab_timer.running:
                    self._send_results(self._ab_timer.start(time_now, start_closed=self._cfg["start"]))
                    if self._cfg["start"]:
                        self._lenses.clear()
                        self._lenses_open = True
                    transition_time = time_now

                delta = time.ticks_diff(time_now, transition_time)

                # Check if lenses are open and should be closed
                if self._lenses_open:
                    if delta >= open_ms:  # Is the open time expired?
                        self._close()
                        transition_time = time_now

                # Check if lenses are closed and should be open
                elif delta >= close_ms:
                    if exp_type == 'peek':
                        if self._request_peek:
                            self._open()
                            self._request_peek = False
                            transition_time = time_now
                    else:
                        self._open()
                        transition_time = time_now

            await asyncio.sleep(0)