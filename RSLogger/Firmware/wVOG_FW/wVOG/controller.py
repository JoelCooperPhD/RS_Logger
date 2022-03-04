import uasyncio as asyncio
from wVOG import xb, config, lenses, battery, mmc


class WirelessVOG:
    def __init__(self, serial):
        self.serial = serial
        
        # Lenses
        self.lenses = lenses.Lenses()
        
        # Battery
        self.battery = battery.LipoReader()
        
        # MMC Save - The flash module stuck to the bottom of the unit
        self.headers = "Device_Unit,,, Block_ms, Trial, Reaction Time, Responses, UTC, Battery\n"
        self.mmc = mmc.MMC()
        
        # XB
        self.xb = xb.XB()
        self.xb.register_incoming_message_cb(self.handle_xb_msg)
        
        # Config
        self.cnf = config.Configurator('wVOG/config.jsn')
    
    async def update(self):
        await asyncio.gather(
            self.handle_serial_msg(),
            )
    
    ################################################
    # Listen for incoming messages
    async def handle_serial_msg(self):
        while True:
            if self.serial.any():
                cmd = self.serial.read()
                cmd = cmd.strip().decode('utf-8')
                self.parse_cmd(cmd)
            await asyncio.sleep(0)
            
    def handle_xb_msg(self, cmd):
        self.parse_cmd(cmd)
            
    def parse_cmd(self, cmd):
        try:
            action, key, val = cmd.split(" ")
            
            if   action == 'do' : self.handle_do(key, val)
            elif action == 'get': self.handle_get(key, val)
            elif action == 'set': self.handle_set(key, val)
        
        except ValueError:
            print("ERROR: Malformed command")
            

    ################################################
    # Handle Incoming Commands
    
    #### DO Commands
    def handle_do(self, key, val):
        if key in ['open', 'close']: self.update_lens_states(key, val)
    
    def update_lens_states(self, key, val):
        # 'do [open, close] [A, B, .]'  :Example - 'do close B' or 'do open .'
        lenses = ['a', 'b']
        if   val == 'A': lenses = 'a'
        elif val == 'B': lenses = 'b'
        
        if key == 'open' : self.lenses.clear(lenses)
        elif key == 'close': self.lenses.opaque(lenses)
    
    #### GET Commands
    def handle_get(self, key, val):
        if   key == 'config': self.get_config()
        elif key == 'bat'   : self.get_battery()
    
    def get_config(self):
        # Example: 'get config .'
        self.broadcast(f'cfg>{self.cnf.get_config_str()}')
        
    def get_battery(self):
        self.broadcast(f'bty>{self.battery.percent()}')
        
    #### SET Commands - Sets configurations in the config.jsn file with the same names
    def handle_set(self, key, val):
        # Example: 'set OPEN 1400' or 'set DBNC 45'
        self.cnf.update(f"{key}:{val}")
        self.get_config()
        
    
    ################################################
    # 
    def broadcast(self, msg):
        self.serial.write(msg+'\n')
        asyncio.create_task(self.xb.transmit(msg+'\n'))
        
    


