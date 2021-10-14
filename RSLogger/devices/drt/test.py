from rs_logger.rsdevices.DRT import drtController, drtView
from time import sleep
from tkinter import Tk
from threading import Thread
from queue import SimpleQueue
from sys import exit
import asyncio


class Main:
    def __init__(self):
        self.win = Tk()
        self.win.protocol("WM_DELETE_WINDOW", self._close_event)

        self.ctrl_qs = {"DRT2c": SimpleQueue(),
                        "DRTfc": SimpleQueue()}

        self.ctrl_out = SimpleQueue()
        self.ctrl_in = SimpleQueue()

        # Main thread Control
        self.v = drtView.DRTMainWindow(self.win, self.ctrl_qs)
        # Async Thread Control & Model
        self.t = Thread(target=self.controller_thread, daemon=True, args=(self.ctrl_qs, ))
        self.t.start()

        self.win.mainloop()

    def controller_thread(self, ctrl_qs):
        asyncio.run(self.run_main_async(ctrl_qs))

    @staticmethod
    async def run_main_async(ctrl_qs):
        c = drtController.DRTController(ctrl_qs)
        await c.run()

    def _close_event(self):
        self.ctrl_in.put("exit")
        sleep(.05)
        self.win.destroy()
        exit()


if __name__ == "__main__":
    Main()
