import asyncio


class MessageRouter:
    def __init__(self, q2v, q2c):
        self._q2v = q2v
        self._q2c = q2c

        self._route_messages = True

    async def run(self):
        asyncio.create_task(self._monitor_main2c())

    async def _monitor_main2c(self):
        while self._route_messages:
            while not self._q2c.empty():
                msg = self._q2c.get()
                kv = msg.split(">")

                if 'ctrl' in kv:
                    # Send to all device controllers
                    pass

                elif kv[0] == 'exit':
                    self._route_messages = False

                else:
                    print(f"controller_main: {msg} message not routed")

            await asyncio.sleep(.01)

