import uasyncio as asyncio
from wVOG.switch import DebouncedSwitch

class SwitchTest:
    def __init__(self, verbose=False):
        self._verbose = verbose
        
        self._resp_a = DebouncedSwitch('Y9')
        self._resp_a.set_click_cnt_callback(self.click_n_a)
        self._resp_a.set_closure_1_callback(self.click_1_a)
        self._resp_a_detected = False
        
        self._resp_b = DebouncedSwitch('Y10')
        self._resp_b.set_click_cnt_callback(self.click_n_b)
        self._resp_b.set_closure_1_callback(self.click_1_b)
        self._resp_b_detected = False
    
    async def run_test(self, secs = 20):
        if self._verbose:
            print(f"Switch test running for {secs} seconds")
            print("Close A or B switches to test.\n")
        
        a = asyncio.create_task(self._resp_a.update())
        b = asyncio.create_task(self._resp_b.update())
        
        await asyncio.sleep(secs)
        
        if self._verbose:
            print("Switch test complete.\n")
            print(f"Switch A detected: {self._resp_a_detected}")
            print(f"Switch B detected: {self._resp_b_detected}\n")
        
        a.cancel()
        b.cancel()
    
    async def reset_closure_1_a(self):
        await asyncio.sleep(2)
        print("Resetting closure A.\n")
        self._resp_a.reset()
        
    async def reset_closure_1_b(self):
        await asyncio.sleep(2)
        print("Resetting closure B.")
        self._resp_b.reset()
        
    def click_1_a(self, mils):
        print(f"ms A: {mils}\n")
        asyncio.create_task(self.reset_closure_1_a())
        self._resp_a_detected = True
        
    def click_n_a(self, cnt):
        print(f"A: {cnt}")
        
    def click_1_b(self, mils):
        print(f"ms B: {mils}\n")
        asyncio.create_task(self.reset_closure_1_b())
        self._resp_b_detected
        
    def click_n_b(self, cnt):
        print(f"B: {cnt}")

    
    
################################################
# Test call example. Copy and paste into REPL
'''
from uasyncio import run
from tests import switch_test
run(switch_test.SwitchTest(verbose = True).run_test(25))
'''