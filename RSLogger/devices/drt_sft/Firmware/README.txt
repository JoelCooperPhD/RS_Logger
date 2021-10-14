Config.jsn file description.

{"HMS:0": 0.1,
"HMS:1": 0.4,
"HMS:2": 0.4,
"HMS:3": 0.1,
"WS:LED": 0.6,
"WS:VIB": 0.2,
"WS:AUD": 0.2,
"HS:LED": 0.5,
"HS:VIB": 0.5,
"HS:AUD": 0.1,
"LED:L": 100,
"LED:H": 5000,
"VIB:L": 100,
"VIB:H": 5000,
"AUD:L": 100,
"AUD:H": 5000,
"ISI:L": 3000,
"ISI:H": 5000,
"STM:ON": 1000}

########################################################
SFT specific parameters

How Many Stimuli will be chosen. Values represent the probability that a particular number of stimuli will be selected.
"HMS:0": 0.2,
"HMS:1": 0.2,
"HMS:2": 0.5,
"HMS:3": 0.1,

Which Stimuli will be selected. This applies when 1 or 2 stimuli will be presented. If three are presented all three stimuli will be shown
"WS:LED": 0.5,
"WS:VIB": 0,
"WS:AUD": 0.5,

Probability of Low stimulus salience. The probability of a high salience stimulus is 1-pL
"HS:LED": 0.5,
"HS:VIB": 0.5,
"HS:AUD": 0.5,

Definition of a Low and High salence stimulus
"LED:L": 100,
"LED:H": 5000,
"VIB:L": 100
"VIB:H": 5000,
"AUD:L": 100,
"AUD:H": 5000,

########################################################
Standard DRT parameters

Inter Stimulus Interval in ms
"ISI:L": 3000,
"ISI:H": 5000,

Stimulus On time in ms
"STM:ON": 1000,


