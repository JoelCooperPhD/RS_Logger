import asyncio
from time import sleep


class ResultsWriter:
    def __init__(self, device_type):
        self._device_type = device_type
        self.file_path = None
        self.loop = asyncio.get_running_loop()

    def _threaded_write(self, data):
        try:
            with open(self.file_path, 'a') as outfile:
                outfile.writelines(data)
        except (PermissionError, OSError):
            sleep(.05)
            self._threaded_write(data)
            print("Permission Error, retrying")

    async def write(self, unit_id, data, timestamp):
        if self.file_path:
            data = f"{self._device_type},{unit_id},{timestamp},{data}"
            await self.loop.run_in_executor(None, self._threaded_write, data)

