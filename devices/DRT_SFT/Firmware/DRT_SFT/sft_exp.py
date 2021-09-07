import urandom as random
from time import sleep


class StimulusSelector:
    def __init__(self, config):
        # Probability of zero, one, two, or three stimuli being presented
        self.cn = config
    
    def draw(self):
        n = self.HowManyStimuli()
        stim = self.WhichStimuli(n)
        draw = self.HowSalient(stim)
        return draw
        
        
    def HowManyStimuli(self):
        '''
        "HMS:0": 0.2, -20% chance of 0 stimuli being shown
        "HMS:1": 0.2,
        "HMS:2": 0.5,
        "HMS:3": 0.1,
        '''
        val = random.random()
        cum_prob = self.cn['HMS:0'] + self.cn['HMS:1'] + self.cn['HMS:2'] + self.cn['HMS:3']
        
        o = self.cn['HMS:0'] / cum_prob
        l = o + (self.cn['HMS:1'] / cum_prob)
        m = l + (self.cn['HMS:2'] / cum_prob)
        h = m + (self.cn['HMS:3'] / cum_prob)
        
        if val <= o:
            return 0
        elif o < val <= l:
            return 1
        elif l < val <= m:
            return 2
        elif m <  val <= h:
            return 3
            
    def WhichStimuli(self, count):
        '''
        "WS:LED": 0.5, - 50% chance A or B will be shown. C is off
        "WS:VIB": 0.5,
        "WS:AUD": 0,
        '''
        selected = list()
        stimuli = {'LED': self.cn['WS:LED'], 'VIB': self.cn['WS:VIB'], 'AUD': self.cn['WS:AUD']}       
            

        for c in range(count):
            rn = random.random()
            low = 0
            high = 0
            to_remove = ''
            cum_prob = sum(stimuli.values())
            
            for key in stimuli:
                high += stimuli[key] / cum_prob
                if low < rn <= high:
                    selected.append(key)
                    to_remove = key
                low += stimuli[key] / cum_prob
                
            stimuli.pop(to_remove)
        
        return selected

    
    def HowSalient(self, stimuli):
        '''
        "HS:LED": 0.5, - 50% low salience / 50% High Saliance
        "HS:VIB": 0.1, - 10% low salience / 90% High Saliance
        "HS:AUD": 0.5,
        '''
        salience = list()
        if len(stimuli):
            for i in stimuli:
                rn = random.random()
                if i is 'LED':
                    if rn <= self.cn['HS:LED']:
                        salience.append('LED.L')
                    else:
                        salience.append('LED.H')
                elif i is 'VIB':
                    if rn <= self.cn['HS:VIB']:
                        salience.append('VIB.L')
                    else:
                        salience.append('VIB.H')
                elif i is 'AUD':
                    if rn <= self.cn['HS:AUD']:
                        salience.append('AUD.L')
                    else:
                        salience.append('AUD.H')
        return salience
                
        
        
        
        
        
    
    
    