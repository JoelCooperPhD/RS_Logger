import uasyncio as asyncio
import time
from wVOG import xb


class xbTest:
    def __init__(self, verbose = True):
        self._xb = xb.XB(debug=True)
        self._xb.register_incoming_message_cb(self._handle_xb_msg)
        self._result = list()
        self._verbose = verbose
        

    async def run_test(self, repeats=5):
        if self._verbose:
            print(f"Running xbee_test.py {repeats} times")
            print("Messages sent to the device during testing will be printed to the screen\n")
        
        xb_run = asyncio.create_task(self._xb._listen_for_new_messages())
        
        await asyncio.sleep(.1)
        await asyncio.create_task(self._send_cmd(repeats))
        
        xb_run.cancel()
        
        if self._verbose:
            result = "PASS" if sum(self._result) == repeats else "FAIL"
            print(f"\nXbee test result: {result}")
        
        return result
        
    async def _send_cmd(self, repeats):
        for i in range(repeats):
            msg = f"Transmit attempt: {int(i+1)}"
            asyncio.create_task(self._xb.transmit(str(i)))
            
            await asyncio.sleep(1)
            self._result.append(self._xb.ACK)
            
            if self._verbose:
                outcome = "success" if self._xb.ACK else "fail"
                print(f"{msg} {outcome}")
            
    async def _handle_xb_msg(self, msg):
        # Prints out any new command received from the coordinator
        if self._verbose:
            print("Listening for new messages...")
        print(cmd)
            

################################################
# Test call example. Copy and paste into REPL
'''
from uasyncio import run
from tests.xb_test import xbTest
print(run(xbTest(verbose = True).run_test(5)))
'''
