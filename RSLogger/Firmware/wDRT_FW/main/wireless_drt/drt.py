from uasyncio import create_task, run, gather, sleep_ms
from time import ticks_us, sleep
from random import randrange
from time import time, ticks_ms, ticks_diff
import gc

from main.utilities import config
from main.hardware import stimuli, switch

'''
ONTM: The time the the stimulus stays on in milliseconds
DBNC: The debounce time of the switch (e.g., the lockout period for responses)
ISIH: The higher bound of the inter-stimulus interval for a trial duration
ISIL: The lower bound ""
SPCT: The stimulus power in percentage (e.g., 100 = full power, 50 = half power)
'''

class BaseDRT:
    CFG_TEMPLATE = {"ONTM": 1000, "DBNC": 100, "ISIH": 5000, "ISIL": 3000, "SPCT": 100}
    HEADERS = "Device ID, Label, Unix time in UTC, Milliseconds Since Record, Trial Number, Responses, Reaction Time, Battery Percent, Device time in UTC\n"
    CONFIG_FILE_PATH = 'main/wireless_drt/config.jsn'
    def __init__(self, broadcast=None, debug=False):
        self._debug = debug
        if self._debug: print("{} drt.__init___".format(ticks_us()))
        
        self._broadcast = None
        if broadcast:
            self._broadcast = broadcast
        
        #Config
        self.configurator = config.Configurator(BaseDRT.CONFIG_FILE_PATH)
        self._verify_config()

        # Stimulus
        self._stimulus = stimuli.Stimulus()
        self._stimulus_on = False
        
        # Response
        self._resp = switch.DebouncedSwitchIRQ()
        self._resp.set_closure_callback(self._response_cb)
        self._responded = False
        self._response_n = 0
        self._reaction_time = -1

        # Block
        self._block_running = False
        self._block_stopping = False
        self._block_start_us = 0

        # Trial
        self._trial_start_us = 0
        self._trial_duration = 0
        self._trial_running = False

        # Return Metrics
        self._stop_utc = time() + 946684800
        self._trial_number = 0
        
        # Experiment Loop
        create_task(self._exp_loop())
        
    def handle_msg(self, key, value):
        """
        Update the experiment state based on the given action and value.

        Args:
            action (str): The action to be performed, either "exp" for experiment or "trl" for trial.
            value (str): The value associated with the action, either "1" for start or "0" for stop.
        """
        if self._debug: print(f'{ticks_us()} BaseVOG.handle_exp_msg {action} {value}')
        
        if key == "exp":
            if value == "1":
                self._init_exp()
            elif value == "0":
                self._end_exp()
        if key == "trl":
            if value == "1":
                self._init_block()
            elif value == "0":
                self._trial_running = False
        elif key == "dev":
            if value == "iso": self._set_iso()
            elif value == "1": self._stimulus.on()
            elif value == "0": self._stimulus.off()
        
    async def _exp_loop(self):
        while True:
            if self._trial_running:
                self._init_trial()
                await gather(self._stimulus_runner(), self._trial_runner())
                self._send_results()
                self._memory_check()
            await sleep_ms(0)
    
    def _init_exp(self):
        pass
    
    def _end_exp(self):
        pass
    
    def _init_block(self):
        self._trial_number = 0
        self._trial_running = True
        self._stimulus.pulse()
        sleep(randrange(int(self.configurator.config['ISIL']), int(self.configurator.config['ISIH']))/1000)
        self._block_start_us = ticks_us()
        
        
    def _init_trial(self):
        self._trial_duration = randrange(int(self.configurator.config['ISIL']), int(self.configurator.config['ISIH']))
        self._response_n = 0
        self._responded = False
        self._reaction_time = -1
        self._trial_start_us = ticks_us()
    
    async def _stimulus_runner(self):
        self._turn_stimulus_on()
        await sleep_ms(int(self.configurator.config['ONTM']))
        self._turn_stimulus_off()
    
    async def _trial_runner(self):
        self._trial_number += 1
        if self._broadcast:
            self._broadcast(f"trl>{self._trial_number}")
        else:
            print(f"trl>{self._trial_number}")
        await sleep_ms(self._trial_duration)
        
          
    def _response_cb(self, clk_us):
        if self._trial_number > 0 and not self._responded:
            self._responded = True
            
            self._reaction_time = ticks_diff(clk_us, self._trial_start_us)
            self._broadcast(f"rt>{self._reaction_time}") if self._broadcast else print(f"rt>{self._reaction_time}")

                
        self._response_n += 1
        self._broadcast(f"clk>{self._response_n}") if self._broadcast else print(f"clk>{self._response_n}")


        if self._stimulus_on:
            self._turn_stimulus_off()
        
    def _turn_stimulus_on(self):
        if not self._stimulus_on:
            self._stimulus_on = True
            self._stimulus.on()
            if self._broadcast:
                self._broadcast("stm>1")
            else:
                print("stm>1")
    
    def _turn_stimulus_off(self):
        if self._stimulus_on:
            self._stimulus_on = False
            self._stimulus.off()
            if self._broadcast:
                self._broadcast("stm>0")
            else:
                print("stm>0")
        
    def _send_results(self):
        if self._debug: print("{} drt._trial_over_cb".format(ticks_us()))
        if self._trial_number >0:
            if self._reaction_time != -1:
                self._reaction_time = round(self._reaction_time/1000)
            block_run_ms = ticks_diff(ticks_us(), self._block_start_us)
            results = f"dta>{round(block_run_ms/1000)},{self._trial_number},{self._response_n},{self._reaction_time}"
            if self._broadcast:
                self._broadcast(results)
            else:
                 print(results)
        self._memory_check()
        
    def _verify_config(self):
        """
        Method to check if the configuration matches the template in length. 
        If not, it updates the configuration to match the original template.
        """
        if self._debug: print(f'{ticks_us()} RSDeviceController.verify_config')
        
        if len(BaseDRT.CFG_TEMPLATE) != len(self.configurator.config):
            self.configurator.update(BaseDRT.CFG_TEMPLATE)
        for key in self.configurator.config:
            if self.configurator.config[key] == "":
                self.configurator.update(BaseDRT.CFG_TEMPLATE)
                break

    def _memory_check(self):
        if self._debug: print(f"{ticks_us()} drt._memory_check {gc.mem_free()}")
        if gc.mem_free() < 20_000:
            gc.collect()
            
    def _set_iso(self):
        self.configurator.update('ONTM:1000,ISIL:3000,ISIH:5000,DBNC:100,SPCT:100')
        cfg_str = self.configurator.get_config_str()
        self._broadcast(f'cfg>{cfg_str}')
 
def create_exp():
    return BaseDRT

##############################################
# TEST
async def _run_test():
    exp = create_exp()()
    exp.handle_msg('trl', '1')
    await sleep_ms(20000)
    exp.handle_msg('trl', '0')

if __name__ == '__main__':
    run(_run_test())
