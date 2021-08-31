import asyncio


class SFTModel:
    def __init__(self):
        self.clicks = dict()
        self.results = dict()

    @staticmethod
    async def send(serial_conn, cmd, value=None):
        if value:
            msg = str.encode(f'{cmd},{value}\n')
        else:
            msg = str.encode(f'{cmd}\n')
        serial_conn.write(msg)
