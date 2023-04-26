import pyb
import uasyncio as asyncio
from uasyncio.event import Event
from uasyncio.lock import Lock


class Xbee:
    def __init__(self, debug=False):
        
        self._debug = debug

        self.name_NI = None

        # Commands
        self._cmd = None
        self._cmd_event = Event()

        # UART
        self._uart = pyb.UART(1, 921600)
        self._uart_lock = Lock()
        self._reader = asyncio.StreamReader(self._uart)
        self._writer = asyncio.StreamWriter(self._uart)

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
            if self._debug: print(f"xbee.run: awaiting msg")
            msg = await self._reader.read(-1)
            cmd = msg[3:4]
            if cmd == b'\x90':
                self._API_0x90(msg)  # Receive Packet
            elif cmd == b'\x91':
                self._API_0x91(msg) # Receive Packet
            elif cmd == b'\x8A':
                self._API_0x8A(msg)
            elif cmd == b'\x88':
                self._API_0x88(msg)  # AT Command Response
            elif cmd == b'\x8b':
                self._API_0x8B(msg)  # Transmit Status
            else:
                if self._debug: print(f"xbee.run: Message not handled {cmd} {msg}")

    async def _send_AT_frame(self, cmd):
        if self._debug: print(f"xbee._send_AT_frame: {cmd}")
        async with self._uart_lock:
            await asyncio.create_task(self._writer.awrite(cmd))

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
        if self._debug: print(f"xbee._get_AT: {cmd}")
        async with self._AT_lock:
            packet = self._AT_packetize(cmd)
            asyncio.create_task(self._send_AT_frame(packet))
            await self._AT_event.wait()
            self._AT_event.clear()
        return self._AT

    # ---- AT helper
    def _AT_packetize(self, cmd):
        if self._debug: print(f"xbee._AT_packetize: {cmd}")
        start = b'\x7E'  # Start byte
        typ = b'\x08'  # Frame type
        fid = b'\x01'  # Frame ID
        packet = typ + fid + cmd  # Completed packet
        csum = bytes([255 - (sum(packet) & 0xFF)])  # Checksum
        mlen = bytes([0x00, len(packet)])  # Packet Length
        return start + mlen + packet + csum

    async def _sync_dest_addr(self):
        while True:  # Wait until the radio has found a controller
            if self._debug: print(f"xbee._sync_dest_addr")
            if b'\x00' == await asyncio.create_task(self.get_AT(b'AI')):
                DH = await asyncio.create_task(self.get_AT(b'DH'))
                DL = await asyncio.create_task(self.get_AT(b'DL'))
                self._dest_addr = DH + DL
                break
            await asyncio.sleep_ms(500)

    async def _get_xb_name(self):
        if self._debug: print(f"xbee._get_xb_name")
        n = await asyncio.create_task(self.get_AT(b'NI'))
        self.name_NI = n.decode('utf-8').strip()

    ##################
    # Transmit Request
    # ----send: 0x10
    async def transmit(self, msg):
        if self._debug: print(f"xbee.transmit: {msg}")
        if self._dest_addr:
            packet = self._xmit_packetize(msg)
            asyncio.create_task(self._send_AT_frame(packet))
            await asyncio.sleep(0)

    def _xmit_packetize(self, cmd):
        if self._debug: print(f"xbee._xmit_packetize: {cmd}")
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

    # ---- Receive Packet Callback
    def _API_0x88(self, arg):
        if self._debug: print(f"xbee._API_0x88: {arg}")
        self._AT = arg[8:-1]
        self._AT_event.set()
        
    def _API_0x8B(self, msg):
        if self._debug: print(f"xbee._API_0x8B: {msg}")
        if msg[8:9] != b'\x00':
            if self._debug: print(f"xbee._API_0x8B: MESSAGE NOT DELIVERED")
            
    def _API_0x90(self, msg):
        if self._debug: print(f"xbee._API_0x90: {msg}")
        try:
            self._cmd = msg[15:-1].decode('utf-8')
            self._cmd_event.set()
        except UnicodeError:
            if self._debug:
                print("xbee: Unicode Error")
                
    def _API_0x91(self, msg):
        if self._debug: print(f"xbee._API_0x91: {msg}")
        try:
            cmd = msg[21:-1]
            self._cmd = cmd.decode('utf-8')
            self._cmd_event.set()
        except UnicodeError:
            if self._debug:
                print("xbee: Unicode Error")
                
    def _API_0x8A(self, msg): # Modem status update
        if self._debug: print(f"xbee._API_0x8A: {msg}")
        else:
            pass
        
    async def new_cmd(self):  # Await this to return command when available
        if self._debug: print(f"xbee.new_cmd")
        await self._cmd_event.wait()
        self._cmd_event.clear()

        return self._cmd


