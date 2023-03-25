import uasyncio as asyncio
from wVOG.lenses import Lenses

class LensTest:
    def __init__(self, verbose=False, delay=1.0):
        self._verbose = verbose
        self._lenses = Lenses()
        self._delay = delay
    
    async def run_test(self, repeats=5):
        print("Initiating lens test\n")

        scenarios = [
            ("Toggle both lenses", [Lenses.LENS_A, Lenses.LENS_B]),
            ("Toggle lens A", [Lenses.LENS_A]),
            ("Toggle lens B", [Lenses.LENS_B]),
            ("Wink lens A", Lenses.LENS_A),
            ("Wink lens B", Lenses.LENS_B),
        ]

        for description, lenses in scenarios:
            print(f"Scenario: {description}")
            if isinstance(lenses, list):
                await self._toggle(times=repeats, lenses=lenses)
            else:
                await self._wink(times=repeats, wink=lenses)
            print()

        print("\nLens test complete\n")

    async def _toggle(self, times, lenses):
        for i in range(times):
            if self._verbose:
                print(f"Toggle {lenses}: {i+1} / {times}")

            self._lenses.clear(lenses)
            await asyncio.sleep(self._delay)

            self._lenses.opaque(lenses)
            await asyncio.sleep(self._delay)

    async def _wink(self, times, wink):
        _open = Lenses.LENS_A if wink == Lenses.LENS_B else Lenses.LENS_B
        _close = Lenses.LENS_A if wink == Lenses.LENS_A else Lenses.LENS_B

        self._lenses.clear([Lenses.LENS_A, Lenses.LENS_B])

        for i in range(times):
            if self._verbose:
                print(f"Wink {wink}: {i+1} / {times}")

            await asyncio.sleep(self._delay)
            self._lenses.opaque(_close)
            self._lenses.clear(_open)

            await asyncio.sleep(self._delay)
            self._lenses.clear([Lenses.LENS_A, Lenses.LENS_B])

if __name__ == "__main__":
    asyncio.run(LensTest(verbose=True, delay=1.0).run_test(5))