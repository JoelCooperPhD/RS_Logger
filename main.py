import asyncio
from threading import Thread
from queue import SimpleQueue
from multiprocessing import freeze_support
import user_interface as view_main
import hardware_interface as controller


class Main:
    def __init__(self):
        self.run = True

        # Queues to communicate with the view and controller between threads
        self.queues = {'main': SimpleQueue(),

                       'hi_root': SimpleQueue(),
                       'ui_root': SimpleQueue(),

                       'hi_sft': SimpleQueue(),
                       'ui_sft': SimpleQueue()}

        # Controller Thread - This is a newly spawned thread where an asyncio loop is used
        self.t = Thread(target=self.async_controller_thread, daemon=True)
        self.t.start()

        # UserInterface Thread - This is the main thread where a tkinter loop is used
        self.view_main = view_main.MainWindow(self.queues)

    def async_controller_thread(self):
        asyncio.run(self.run_main_async())

    async def run_main_async(self):
        main_controller = controller.HardwareInterface(self.queues)
        await asyncio.gather(main_controller.run(),
                             self.main_message_router())

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

            await asyncio.sleep(.1)


if __name__ == "__main__":
    freeze_support()
    Main()
