import time
import asyncio
import psutil
from tkinter import Tk


class LoopMonitor:
    def __init__(self, interval=.25):
        self._end_t = time.monotonic()
        self._interval = interval
        self._run = True

    async def run_asyncio(self):
        while self._run:
            lag = self._get_loop_lag()
            load = self._get_cpu_load()
            tasks = self._get_running_tasks()
            print(f"Lag: {lag} Load: {load} Tasks: {tasks}")
            await asyncio.sleep(self._interval)

    def run_tk(self, win: Tk):
        while self._run:
            lag = self._get_loop_lag()
            load = self._get_cpu_load()
            print(f"Lag: {lag}, Load: {load}")
            win.after(self._interval, self.run_tk(win))

    def stop(self):
        self._run = False

    def _get_loop_lag(self):
        time_slept = time.monotonic() - self._end_t
        self._end_t = time.monotonic()
        return round(time_slept - self._interval, 5)

    @staticmethod
    def _get_cpu_load():
        return psutil.cpu_percent()

    @staticmethod
    def _get_running_tasks():
        return len(asyncio.tasks.all_tasks())
