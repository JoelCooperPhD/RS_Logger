from threading import Thread
from queue import SimpleQueue
from multiprocessing import freeze_support

from RSLogger.hardware_io import hi_controller
from RSLogger.user_interface import ui_controller

__version__ = '1.3'

# Inter-thread communication queue dictionary
queues = {'q_2_hi': SimpleQueue(),
          'q_2_ui': SimpleQueue()
          }


def main():
    # Controller Thread - This is a newly spawned thread where an asyncio loop is used
    t = Thread(target=hi_controller.HWRoot, args=(queues, ), daemon=True)
    t.start()

    ui_controller.UIController(queues)


if __name__ == "__main__":
    freeze_support()
    main()
