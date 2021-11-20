from threading import Thread
from queue import SimpleQueue
from multiprocessing import freeze_support

from RSLogger.UserInterface import UserInterface
from RSLogger.HardwareInterface import HardwareInterface

__version__ = '0.1.3'

# Inter-thread communication queue dictionary
queues = {'main': SimpleQueue(),
          'ui_logger': SimpleQueue(),

          'hi_sft': SimpleQueue(),
          'ui_sft': SimpleQueue(),

          'hi_drt': SimpleQueue(),
          'ui_drt': SimpleQueue(),

          'hi_vog': SimpleQueue(),
          'ui_vog': SimpleQueue(),

          'hi_wdrt': SimpleQueue(),
          'ui_wdrt': SimpleQueue()
          }


def main():
    # Controller Thread - This is a newly spawned thread where an asyncio loop is used
    t = Thread(target=HardwareInterface.LoggerHI, args=(queues,), daemon=True)
    t.start()

    UserInterface.LoggerUI(queues)


if __name__ == "__main__":
    freeze_support()
    main()
