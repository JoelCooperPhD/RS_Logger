import uasyncio as asyncio
import time
from wVOG.lenses import Lenses


class LensTest:
    def __init__(self, verbose=False):
        self._verbose = verbose
        self._lenses = Lenses()
    
    def run_test(self, repeats=5):
        print("Initiating lens test\n")
        await asyncio.create_task(self._toggle(times=repeats, lenses=['a', 'b']))
        await asyncio.create_task(self._toggle(times=repeats, lenses=['a']))
        await asyncio.create_task(self._toggle(times=repeats, lenses=['b']))
        await asyncio.create_task(self._wink(times=repeats, wink='a'))
        await asyncio.create_task(self._wink(times=repeats, wink='b'))
        
        self._lenses.clear()
        await asyncio.sleep(.5)
        self._lenses.opaque()
        await asyncio.sleep(.5)
        
        print("\nLens test complete\n")
        
    async def _toggle(self, times, lenses=['a', 'b']):
        for i in range(times):
            if self._verbose:
                print(f"Toggle {lenses}: {i+1} / {times}")
                
            self._lenses.clear(lenses)
            await asyncio.sleep(.5)
            
            self._lenses.opaque(lenses)
            await asyncio.sleep(.5)
    
    async def _wink(self, times, wink='a'):
        _open = 'a' if wink == 'b' else 'b'
        _close = 'a' if wink == 'a' else 'b'
        
        self._lenses.clear(['a', 'b'])
        
        for i in range(times):
            if self._verbose:
                print(f"Wink {wink}: {i+1} / {times}")
            
            await asyncio.sleep(.5)
            self._lenses.opaque(_close)
            self._lenses.clear(_open)
            
            await asyncio.sleep(.5)
            self._lenses.clear(['a', 'b'])
            


################################################
# Test call example. Copy and paste into REPL
'''
from uasyncio import run
from tests.lens_test import LensTest
run(LensTest(verbose = True).run_test(5))
'''