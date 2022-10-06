from utime import ticks_ms, ticks_us, ticks_diff
import uasyncio as asyncio


class Stopwatch:
    def __init__(self, precision='ms'):
        self._precision = precision
        self._tic = None
        self._duration = None
        self._running = False

    def start(self):
        self._running = True
        if self._precision == 'ms':
            self._tic = ticks_ms()
        elif self._precision == 'us':
            self._tic = ticks_us()

    def read(self):
        if self._running:
            if self._precision == 'ms':
                return ticks_diff(ticks_ms(), self._tic)
            elif self._precision == 'us':
                return ticks_diff(ticks_us(), self._tic)
        else:
            return 0

    def stop(self, in_t=None):
        if self._running:
            self._running = False

            if in_t:
                toc = in_t
            else:
                if self._precision == 'ms':
                    toc = ticks_ms()
                elif self._precision == 'us':
                    toc = ticks_us()

            return ticks_diff(toc, self._tic)
        else:
            return 0


class Countdown:
    def __init__(self, callback, duration=None):
        self._duration = duration
        self._callback = callback
        self._stop = False

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, val):
        if isinstance(val, int) and val >= 0:
            self._duration = val

    async def start(self, start_t=None, duration=None, init_us=None):
        if duration:
            self._duration = duration
        if not start_t:
            start_t = ticks_ms()
        print(ticks_diff(ticks_us(), init_us))
        while True:
            elapsed = ticks_diff(ticks_ms(), start_t)
            if elapsed >= self._duration:
                self._callback(elapsed)
                break
            await asyncio.sleep(0)


class ABTimeAccumulator:
    def __init__(self):
        # point time variables
        self._start_ms = 0
        self._stop_ms = 0
        self._change_ms = 0

        # time accumulators
        self._accumulator = [int(), int()]
        self._data = [str(), int(), int(), int()]

        # state tracker
        self._i = False
        self.running = False

    def start(self, now=None, start_open=True):
        if not now:
            now = ticks_ms()
        self._start_ms, self._toggle_ms = now, now
        self._accumulator = [0, 0]
        self.running = True
        self._i = start_open
        return self._state(now)

    def stop(self):
        now = ticks_ms()
        self._update_accumulator(now)
        self.running = False
        return self._state(now, tag='X')

    def toggle(self, now=None):
        if not now:
            now = ticks_ms()

        self._update_accumulator(now)

        self._toggle_ms = now
        self._i = not self._i

        return self._state(now)

    def _update_accumulator(self, now):
        elapsed = ticks_diff(now, self._toggle_ms)
        self._accumulator[self._i] += elapsed

    def _state(self, now, tag=None):
        if tag:
            self._data[0] = tag
        else:
            self._data[0] = '1' if self._i else '0'

        self._data[1] = ticks_diff(now, self._start_ms)
        self._data[2:4] = self._accumulator

        return self._data