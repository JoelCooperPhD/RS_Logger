import asyncio
from threading import Thread
from queue import SimpleQueue
from multiprocessing import freeze_support
from user_interface import ui_root as view_main
from devices.drt_sft.HardwareInterface import SFT_HIController
from devices.drt.HardwareInterface import DRT_HIController


class Main:
    def __init__(self):
        self.run = True

        # Queues to communicate with the view and controller between threads
        self.queues = {'main': SimpleQueue(),

                       'user_interface': SimpleQueue(),

                       'hi_sft': SimpleQueue(),
                       'ui_sft': SimpleQueue(),

                       'hi_drt': SimpleQueue(),
                       'ui_drt': SimpleQueue()}

        # Controller Thread - This is a newly spawned thread where an asyncio loop is used
        self.t = Thread(target=self.async_controller_thread, daemon=True)
        self.t.start()

        # UserInterface Thread - This is the main thread where a tkinter loop is used
        self.view_main = view_main.MainWindow(self.queues)

    def async_controller_thread(self):
        asyncio.run(self.run_main_async())

    async def run_main_async(self):
        devices = {'SFT': SFT_HIController.SFTController(self.queues['main'], self.queues['hi_sft']),
                   'DRT': DRT_HIController.DRTController(self.queues['main'], self.queues['hi_drt'])}
        for d in devices:
            devices[d].run()

        await asyncio.gather(self.main_message_router())

    async def main_message_router(self):
        while 1:
            while not self.queues['main'].empty():
                msg = self.queues['main'].get()
                if msg == 'exit':
                    print('Main: Handle Exit Stub')
                else:
                    address, key, val = msg.split('>')
                    if address == 'main':
                        if val == 'ALL' or key == 'fpath':
                            for q in self.queues:
                                if q != 'main':
                                    self.queues[q].put(f'{q}>{key}>{val}')

                    else:
                        self.queues[address].put(msg)

            await asyncio.sleep(.01)


if __name__ == "__main__":
    freeze_support()
    Main()
