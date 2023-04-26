import uasyncio as asyncio
from wVOG.switch import DebouncedSwitch

class SwitchTest:
    def __init__(self, verbose=False):
        self._verbose = verbose

        # Initialize DebouncedSwitch objects for two switches
        self._switch_a = DebouncedSwitch('Y9')
        self._switch_b = DebouncedSwitch('Y10')

        # Set up callbacks for the switches
        self._switch_a.set_click_cnt_callback(self.click_count_a)
        self._switch_a.set_closure_1_callback(self.click_duration_a)
        self._switch_b.set_click_cnt_callback(self.click_count_b)
        self._switch_b.set_closure_1_callback(self.click_duration_b)

        # Track if each switch has been detected
        self._switch_a_detected = False
        self._switch_b_detected = False

    async def run_test(self, duration=20):
        if self._verbose:
            print(f"Switch test running for {duration} seconds")
            print("Close switches A or B to test.\n")

        # Create tasks for switch updates
        task_a = asyncio.create_task(self._switch_a.update())
        task_b = asyncio.create_task(self._switch_b.update())

        # Wait for the specified duration
        await asyncio.sleep(duration)

        if self._verbose:
            print("Switch test complete.\n")
            print(f"Switch A detected: {self._switch_a_detected}")
            print(f"Switch B detected: {self._switch_b_detected}\n")

        # Cancel the tasks
        task_a.cancel()
        task_b.cancel()

    # Callback functions and tasks for switch events
    async def reset_closure_a(self):
        await asyncio.sleep(2)
        print("Resetting closure A.\n")
        self._switch_a.reset()

    async def reset_closure_b(self):
        await asyncio.sleep(2)
        print("Resetting closure B.")
        self._switch_b.reset()

    def click_duration_a(self, duration_ms):
        print(f"Duration A: {duration_ms} ms\n")
        asyncio.create_task(self.reset_closure_a())
        self._switch_a_detected = True

    def click_count_a(self, count):
        print(f"Click count A: {count}")

    def click_duration_b(self, duration_ms):
        print(f"Duration B: {duration_ms} ms\n")
        asyncio.create_task(self.reset_closure_b())
        self._switch_b_detected = True

    def click_count_b(self, count):
        print(f"Click count B: {count}")

# Run the test if the script is executed directly
if __name__ == "__main__":
    test = SwitchTest(verbose=True)
    asyncio.run(test.run_test(25))