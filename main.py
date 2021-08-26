from threading import Thread
from queue import SimpleQueue
from multiprocessing import freeze_support
import view as view_main
import controller as controller_main


class Main:
    def __init__(self):
        self.run = True

        # Queues to communicate with the view and controller between threads
        self.q2v = SimpleQueue()
        self.q2c = SimpleQueue()

        # View Thread - This is the main thread where a tkinter loop is used
        self.view_main = view_main.MainWindow(self.q2v, self.q2c)

        # Controller Thread - This is a newly spawned thread where an asyncio loop is used
        self.t = Thread(target=controller_main.MessageRouter, args=(self.q2v, self.q2c), daemon=True)
        self.t.start()


if __name__ == "__main__":
    freeze_support()
    Main()
