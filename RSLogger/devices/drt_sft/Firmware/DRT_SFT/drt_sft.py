from DRT_SFT import stimuli, config, utilities, sft_exp, switch, timers
from time import ticks_ms, ticks_diff
import uasyncio as asyncio
from urandom import randrange
from time import time


class SystemsFactorialTechnology:
    def __init__(self, serial):
        
        self.serial = serial
        
        self.diagnostics = utilities.Diagnostics()
        
        # Switch
        self.sw = switch.DebouncedSwitch()
        self.sw.set_closure_1_callback(self.response_cb)
        self.sw.set_click_cnt_callback(self.click_cb)
        
        # Stimuli
        self.led = stimuli.LEDVib(pin='X9', channel=3)
        self.vib = stimuli.LEDVib(pin='X10', channel=4)
        self.aud = stimuli.AuditoryStimulus()
        
        
        # Config
        self.cn = config.Configurator('drt_sft/config.jsn')
        
        # Experiment
        self.tic = 0
        self.running = False
        self.complete = True
        self.selected_set = list()
        self.stim_set = sft_exp.StimulusSelector(self.cn.config)
        self.trial_countdown = timers.Countdown(self.trial_end_cb)
        self.stim_countdown = timers.Countdown(self.stim_off_cb)
        
        # Results
        self.trial =0
        self.rt = 0
    
    async def run(self):
        await asyncio.gather(
            # self.diagnostics.heartbeat(),
            self.serial_listen(),
            self.sw.run(),
            )
        
    def start_trial(self, reset=False):
        self.sw.reset()
        self.complete = False
        isi = randrange(int(self.cn.config['ISI:L']), int(self.cn.config['ISI:H']))
        asyncio.create_task(self.stim_countdown.start(int(self.cn.config['STM:DUR'])))
        asyncio.create_task(self.trial_countdown.start(isi))
        
        self.selected_set = self.stim_set.draw()
        
        
        for draw in self.selected_set:
            s, v = draw.split('.')
            val = self.cn.config[s + ':' + v]
            stim = None
            if s is "LED":
                self.led.intensity = val
                state = self.led.set_on()
            elif s is "VIB":
                self.vib.intensity = val
                state = self.vib.set_on()
            elif s is "AUD":
                self.aud.intensity = val
                state = self.aud.set_on()
        
            self.send_stim_state(s, v)

                
        self.tic = ticks_ms()
        self.sw.reset()
        
        if reset:
            self.trial = 1
        else:
            self.trial += 1
            
        print(f'trl>{self.trial}')
            
        self.rt = -1
        
    def stim_off_cb(self, t=None):
        if self.led.stm_on:
            state = self.led.set_off()
            self.send_stim_state('LED', not state)
        if self.vib.stm_on:
            state = self.vib.set_off()
            self.send_stim_state('VIB', not state)
        if self.aud.stm_on:
            state = self.aud.set_off()
            self.send_stim_state('AUD', not state)
        
    def trial_end_cb(self, t=None):
        self.send_results()
        if self.running:
            self.start_trial()
        
    def response_cb(self, val):
        self.rt = ticks_diff(val, self.tic)
        self.stim_off_cb()
        print(f"rt>{self.rt}")
        
    def click_cb(self, clicks):
        print(f'clk>{clicks}')
        
    def send_results(self):
        selected_set = "[" + ": ".join(self.selected_set) + "]"
        results = f'dta>DRT,SFT,{time()},{946684800},{self.trial},{self.rt},{self.sw.closure_cnt}, {selected_set}'
        print(results)
        self.complete = True
        
    def send_stim_state(self, stim, state):
        print(f'{stim}>{state}'[:5])
        
        
     ################
     # Serial Commands
    async def serial_listen(self):
        while True:
            if self.serial.any():
                msg = self.serial.read()
                msg = msg.strip().decode('utf-8')
                kv = msg.split(":")
                if len(kv) == 1:
                    self.run_command(kv[0])
                else:
                    self.update_config(kv[0], kv[1])
            await asyncio.sleep(0)
     
    def run_command(self, cmd):
        if 'init' in cmd:
            pass
        elif 'close' in cmd:
            pass
        elif 'start' in cmd:
            if not self.running and self.complete:
                self.running = True
                self.start_trial(reset=True)
        elif 'stop' in cmd:
            self.running = False
        elif 'config' in cmd:
            print(f'cnf>{self.cn.get_config_str()}')
        
        elif 'VIB' in cmd or 'LED' in cmd or 'AUD' in cmd:
            kv = cmd.split('.')
            if len(kv) >1:
                intensity = self.cn.config[f'{kv[0]}:{kv[1]}']
                if kv[0] == 'VIB': self.vib.toggle(intensity)
                elif kv[0] == 'LED': self.led.toggle(intensity)
                elif kv[0] == 'AUD': self.aud.toggle(intensity)

        else:
            print(f'What is this: {cmd}')
        
    def update_config(self, cmd, arg):
        '''
        Gets and Sets the probability of HMS (How Many Stimuli), WS (Which Stimuli), and HS (How Salient)
        
        Ex: HMS:0,0.1 (10% chance of no stimuli),
              WS:B,0.5   (Stimulus B has a 50% chance of being selected - First draw probabiliy)
              HS:C,1       (Stimulus C has a 100% chance of being low saliance)
        '''
        if ',' in arg:
            # Set value and return new value set
            key, val = arg.split(',')
            val = int(val)
            if 'ISI' not in cmd:
                if val > 100:
                    val = 100
                elif val < 0:
                    val = 0
            
            self.cn.config[f'{cmd}:{key}'] = int(val)
            self.cn.run(self.cn.config)
            print(f'cfg>{cmd}:{key},{val}')
        else:
            # Get value and return
            val = self.cn.config[f'{cmd}:{arg}']
            print(f'cfg>{cmd}:{arg},{val}')
    
        

        

            
        
