import asyncio
from threading import Thread
from queue import SimpleQueue
from multiprocessing import freeze_support
import view as view_main
import rootcontroller as controller


class Main:
    def __init__(self):
        self.run = True

        # Queues to communicate with the view and controller between threads
        self.q2v = SimpleQueue()
        self.q2c = SimpleQueue()

        # Controller Thread - This is a newly spawned thread where an asyncio loop is used
        self.t = Thread(target=self.async_controller_thread, daemon=True)
        self.t.start()

        # UserInterface Thread - This is the main thread where a tkinter loop is used
        self.view_main = view_main.MainWindow(self.q2c, self.q2v)

    def async_controller_thread(self):
        asyncio.run(self.run_main_async())

    async def run_main_async(self):
        main_controller = controller.RootController(self.q2c, self.q2v)
        await asyncio.create_task(main_controller.run())


if __name__ == "__main__":
    freeze_support()
    Main()
