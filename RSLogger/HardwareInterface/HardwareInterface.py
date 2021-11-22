from asyncio import gather, run, sleep

# Hardware Interface
from RSLogger.HardwareInterface.SFT_HI import SFT_HIController
from RSLogger.HardwareInterface.DRT_HI import DRT_HIController
from RSLogger.HardwareInterface.VOG_HI import VOG_HIController
from RSLogger.HardwareInterface.wDRT_HI import WDRT_HIController


class LoggerHI:
    def __init__(self, queues):
        self.queues = queues
        self.async_controller_thread()

    def async_controller_thread(self):
        run(self.run_main_async())
    
    async def run_main_async(self):
        devices = {'SFT':  SFT_HIController.SFTController(self.queues['main'], self.queues['hi_sft']),
                   'DRT':  DRT_HIController.DRTController(self.queues['main'], self.queues['hi_drt']),
                   'WDRT': WDRT_HIController.WDRTController(self.queues['main'], self.queues['hi_wdrt']),
                   'VOG':  VOG_HIController.VOGController(self.queues['main'], self.queues['hi_vog'])
                   }
        for d in devices:
            devices[d].run()
    
        await gather(self.main_message_router())
    
    async def main_message_router(self):
        while 1:
            while not self.queues['main'].empty():
                try:
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
                except ValueError:
                    print(f'Hardware Interface Value Error in main_message_router')
            await sleep(.0001)
    

    
