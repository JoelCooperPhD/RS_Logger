from wDRT import wdrt
from uasyncio import run


def run_wdrt():
    wdrt_ = wdrt.wDRT()
    run(wdrt_.update())


if __name__ is '__main__':
    run_wdrt()