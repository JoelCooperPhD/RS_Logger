import pyb
import uasyncio as asyncio
from uasyncio.event import Event
from uasyncio.lock import Lock


class XB:
    def __init__(self, debug=False):
        
        self._debug = debug

        self.name_NI = None
        
        self.ACK = False

        # Commands
        self._cmd = None
        self._cmd_event = Event()

        # UART
        self._uart = pyb.UART(1, 921600)
        self._uart_lock = Lock()
        self._reader = asyncio.StreamReader(self._uart, {})
        self._writer = asyncio.StreamWriter(self._uart, {})

        # AT Commands
        self._AT = None
        self._AT_event = Event()
        self._AT_lock = Lock()
        self._dest_addr = None

        asyncio.create_task(self._sync_dest_addr())
        asyncio.create_task(self._get_xb_name())

    ##################
    # UART
    async def run(self):
        while True:
            msg = await self._reader.read(-1)
            if msg[3:4] == b'\x90':
                self._API_0x90(msg)  # Receive Packet
            elif msg[3:4] == b'\x88':
                self._API_0x88(msg)  # AT Command Response
            elif msg[3:4] == b'\x8b':
                self._API_0x8B(msg)  # Transmit Status
            else:
                print("Message not handled: {}".format(msg[3:4]))

    async def _send_AT_frame(self, cmd):
        async with self._uart_lock:
            # 7E 00 04 08 01 41 49 6C
            self._writer.write(cmd)
            await self._writer.drain()

    ##################
    # AT Commands
    async def get_AT(self, cmd):
        '''
        EA: ACK Failures
        EC: Clear Channel Faulures
        AI: Association Indication
        DH: Destitination High Address
        DL: Destination Low Address
        '''
        async with self._AT_lock:
            
            packet = self._AT_packetize(cmd)
            asyncio.create_task(self._send_AT_frame(packet))
            
            await self._AT_event.wait()
            
            self._AT_event.clear()
        return self._AT

    # ---- AT Command Response Callback
    def _API_0x88(self, arg):
        self._AT = arg[8:-1]
        self._AT_event.set()

    # ---- AT helper
    def _AT_packetize(self, cmd):
        start = b'\x7E'  # Start byte
        typ = b'\x08'  # Frame type
        fid = b'\x01'  # Frame ID
        packet = typ + fid + cmd  # Completed packet
        csum = bytes([255 - (sum(packet) & 0xFF)])  # Checksum
        mlen = bytes([0x00, len(packet)])  # Packet Length
        return start + mlen + packet + csum

    async def _sync_dest_addr(self):
        while True:  # Wait until the radio has found a controller
            if b'\x00' == await asyncio.create_task(self.get_AT(b'AI')):
                DH = await asyncio.create_task(self.get_AT(b'DH'))
                DL = await asyncio.create_task(self.get_AT(b'DL'))
                self._dest_addr = DH + DL
                break
            await asyncio.sleep_ms(500)

    async def _get_xb_name(self):
        n = await asyncio.create_task(self.get_AT(b'NI'))
        self.name_NI = n.decode('utf-8').strip()

    ##################
    # Transmit Status
    def _API_0x8B(self, msg):
        if self._debug:
            self.ACK = False if msg[8:9] != b'\x00' else True

    ##################
    # Transmit Request
    # ----send: 0x10
    async def transmit(self, msg):
        if self._dest_addr:
            packet = self._xmit_packetize(msg)
            asyncio.create_task(self._send_AT_frame(packet))
            await asyncio.sleep(0)

    def _xmit_packetize(self, cmd):
        start = b'\x7E'  # Start byte
        typ = b'\x10'  # Frame type
        fid = b'\x01'  # Frame ID
        dest_64 = self._dest_addr
        dest_16 = b'\xFF\xFE'
        br = b'\x00'
        opt = b'\x00'
        packet = typ + fid + dest_64 + dest_16 + br + opt + cmd  # Completed packet
        csum = bytes([255 - (sum(packet) & 0xFF)])  # Checksum
        mlen = bytes([0x00, len(packet)])  # Packet Length
        return start + mlen + packet + csum

    # ---- Receive Packet Callback :0x90
    def _API_0x90(self, msg):
        try:
            self._cmd = msg[15:-1].decode('utf-8')
            self._cmd_event.set()
        except UnicodeError:
            if self._debug:
                print("Xbee: Unicode Error")
        
    async def new_cmd(self):  # Await this to return command when available
        await self._cmd_event.wait()
        self._cmd_event.clear()

        return self._cmd


