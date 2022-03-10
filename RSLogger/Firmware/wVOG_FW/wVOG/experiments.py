import uasyncio as asyncio
from pyb import Pin
from wVOG import lenses, timers
import time


class Peek:
    def __init__(self, config=None, results_cb=None, start_clear=True):
        self._cfg = config
        self._results_cb = results_cb
        self._start_clear = start_clear

        self._start_t = time.ticks_ms()

        # Lenses
        self._transition_ms = 0
        self._lenses_open = False
        self._lenses = lenses.Lenses()

        # Switches
        self._debounced = True
        self._resp_value_old = 0
        self._response = Pin('Y9', mode=Pin.IN, pull=Pin.PULL_UP)

        # Toggle Timer
        self._ab_timer = timers.ABTimeAccumulator()

        # Results
        self._results = None

        # Experiment
        self._exp_async_loop = None

    def begin_trial(self):
        self._exp_async_loop = asyncio.create_task(self._exp_loop())

    def end_trial(self):
        self._ab_timer.stop()
        self._lenses.opaque()

        self._exp_async_loop.cancel()

    async def _exp_loop(self):
        close_time = 0
        response_state_old = self._response.value()

        now = time.ticks_ms()
        self._start_t = now

        if self._start_clear:
            self._ab_timer.start(now, start_closed=False)
            request_to_open = True
        else:
            self._results = self._ab_timer.start(now, start_closed=False)
            print(self._results)
            request_to_open = False
        clear_to_open = True

        while True:
            time_now = time.ticks_ms()

            # Check if enough time has passed since lenses closed

            if not clear_to_open and not self._lenses_open:
                close_ms_time_elapsed = time.ticks_diff(time_now, close_time) >= int(self._cfg['close_ms'])
                if close_ms_time_elapsed:
                    clear_to_open = True

            # Check switch
            if not self._lenses_open and not request_to_open and self._valid_press(response_state_old):  # Open Lens
                request_to_open = True

            # Check if lenses are close dand should be open
            if request_to_open and clear_to_open:
                self._open()
                self._transition_ms = time_now
                clear_to_open = False
                request_to_open = False

            # Check if lenses are open and should be closed
            if self._lenses_open and self._elapsed(self._cfg['open_ms'], time_now):  # Is the open time expired?
                self._close()
                close_time = time_now

            # Check if button has been debounced
            if not self._debounced and self._elapsed(self._cfg['debounce'],
                                                     time_now):  # Is the debounced lockout expired?
                self._debounced = True

            await asyncio.sleep(0)

    def _open(self):
        self._results = self._ab_timer.toggle()
        self._lenses.clear()
        self._lenses_open = True

        print(self._results)

    def _close(self):
        self._results = self._ab_timer.toggle()
        self._lenses.opaque()
        self._lenses_open = False

        print(self._results)

    def _elapsed(self, duration, now_ms):
        elapsed = time.ticks_diff(now_ms, self._transition_ms)
        if elapsed >= duration:
            return True
        else:
            return False

    def _valid_press(self, prior):
        resp_value = self._response.value()
        clicked = self._resp_value_old - resp_value == 1
        self._resp_value_old = resp_value
        if clicked and self._debounced:
            return True
        else:
            return False

        return state


