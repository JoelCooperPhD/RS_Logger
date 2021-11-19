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


class Countdown:
    def __init__(self, callback, duration=None):
        self._duration = duration
        self._callback = callback
        self.run = True

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, val):
        if isinstance(val, int) and val >= 0:
            self._duration = val

    async def start(self, duration=None):
        if duration:
            self._duration = duration
        start_t = ticks_ms()
        while self.run:
            elapsed = ticks_diff(ticks_ms(), start_t)
            if elapsed >= self._duration:
                self._callback(elapsed)
                break
            await asyncio.sleep(0)