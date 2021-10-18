from DRT_SFT import sft_exp, config

class sft_exp_test:
    def __init__(self):
        
        self.cn = config.Configurator('sft/config.jsn')
        self.sft = sft_exp.StimulusSelector(self.cn.config)
        
        self.stim_count = {'zero': 0, 'one': 0, 'two': 0, 'three': 0}
        self.stim_type = {'LED.L': 0, 'LED.H': 0, 'VIB.L':0, 'VIB.H': 0, 'AUD.L': 0, 'AUD.H': 0}
    
    def draw(self, n=100):
        self.stim_count = {'zero': 0, 'one': 0, 'two': 0, 'three': 0}
        self.stim_type = {'LED.L': 0, 'LED.H': 0, 'VIB.L':0, 'VIB.H': 0, 'AUD.L': 0, 'AUD.H': 0}
        tot = 0
        
        for i in range(n):
            stims = self.sft.draw()
            tot += len(stims)
            self.len_count(len(stims))
            self.type_count(stims)
        
        for v in self.stim_count:
            print("{}: {}".format(v, self.stim_count[v]/n))
            
        print()    
        print('WS:LED: {}'.format((self.stim_type['LED.L'] + self.stim_type['LED.H'])/ tot))
        print('WS:VIB: {}'.format((self.stim_type['VIB.L'] + self.stim_type['VIB.H']) / tot))
        print('WS:AUD: {}'.format((self.stim_type['AUD.L'] + self.stim_type['AUD.H']) / tot))
        print()
        if (self.stim_type['LED.L'] + self.stim_type['LED.H']) > 0:
            print('HS:LED: {}'.format(self.stim_type['LED.L'] / (self.stim_type['LED.L'] + self.stim_type['LED.H'])))
        else:
            print('HS:LED: 0.0')
        if (self.stim_type['VIB.L'] + self.stim_type['VIB.H']) > 0:
            print('HS:VIB: {}'.format(self.stim_type['VIB.L'] / (self.stim_type['VIB.L'] + self.stim_type['VIB.H'])))
        else:
            print('HS:VIB: 0.0')
        if (self.stim_type['AUD.L'] + self.stim_type['AUD.H']) > 0:
            print('HS:AUD: {}'.format(self.stim_type['AUD.L'] / (self.stim_type['AUD.L'] + self.stim_type['AUD.H'])))
        else:
            print('HS:VIB: 0.0')

    
    def len_count(self, cnt):
        if cnt == 0:
            self.stim_count['zero'] += 1
        elif cnt == 1:
            self.stim_count['one'] += 1
        elif cnt == 2:
            self.stim_count['two'] += 1
        elif cnt == 3:
            self.stim_count['three'] += 1
            
    def type_count(self, stims):
        for stim in stims:
            if 'LED.L' in stim:
                self.stim_type['LED.L'] += 1
            elif 'LED.H' in stim:
                self.stim_type['LED.H'] += 1
            elif 'VIB.L' in stim:
                self.stim_type['VIB.L'] += 1
            elif 'VIB.H' in stim:
                self.stim_type['VIB.H'] += 1
            elif 'AUD.L' in stim:
                self.stim_type['AUD.L'] += 1
            elif 'AUD.H' in stim:
                self.stim_type['AUD.H'] += 1
                

        
            
