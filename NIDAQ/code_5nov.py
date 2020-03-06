#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 15:13:14 2019

@author: sabinejonkman
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 15:06:25 2019

@author: sabinejonkman
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  1 11:57:51 2019

@author: sabinejonkman
"""
import matplotlib.pyplot as plt
import numpy as np
'''
class Sabine():
    def __init__(self):      
        # Here we initialize the attributes of object Sabine
        self.Daq_sample_rate = int(50000)
        self.wave_frequency = float(10)# within the single period 
        self.wave_offset = int(100) # in ms when the first wave starts
        self.wave_period = int(1000) # in ms
        self.wave_dutycircle = int(50)# of single period
        self.wave_repeatnumber = int(15) # how many times u want to repeat the period
        self.wave_gap_inbetween = [int(100000)] # gap between repeat
        self.wavestartamplitude = float(2) #hight of the first 
        self.wavebaseline = float(0)
        self.wavestep = float(1) #change between neighbour cycle
        self.wavecycles = int(1) #repeats of the exact same waveform 
        self.start_point = int(2) 
        self.start_time = int(5)
        self.control_amplitude = float(0.25)
        
    def generate_waveform(self):      
        #Here we call the function below(generate_AO), feed in the parameters and get the waveform                         
        s = generate_AO(self.Daq_sample_rate, self.wave_frequency, self.wave_offset, self.wave_period, self.wave_dutycircle
                               , self.wave_repeatnumber, self.wave_gap_inbetween, self.wavestartamplitude, self.wavebaseline, self.wavestep, self.wavecycles, self.start_time, self.control_amplitude)
        self.finalwave = s.generate()
        return self.finalwave
'''

class generate_AO():
    def __init__(self, Daq_sample_rate, wavefrequency_2, waveoffset_2, waveperiod_2, waveDC_2, waverepeat_2, wavegap_2, wavestartamplitude_2, wavebaseline_2, wavestep_2, wavecycles_2, start_time_2, control_amp2):
        self.Daq_sample_rate = Daq_sample_rate
        self.wavefrequency_2 = wavefrequency_2
        self.waveoffset_2 = waveoffset_2
        self.waveperiod_2 = waveperiod_2
        self.waveDC_2 = waveDC_2
        self.waverepeat_2 = waverepeat_2
        self.wavegap_2 = wavegap_2
        self.wavestartamplitude_2 = wavestartamplitude_2
        self.wavebaseline_2 = wavebaseline_2
        self.wavestep_2 = wavestep_2
        self.wavecycles_2 = wavecycles_2
        self.start_time_2 = start_time_2
        self.controlamp_2 = control_amp2
        
    def generate(self):
        def rect(T):
            """create a centered rectangular pulse of width $T"""
            return lambda t: (-T/2 <= t) & (t < T/2)
            
        def pulse_train(t, at, shape):
            """create a train of pulses over $t at times $at and shape $shape"""
            return np.sum(shape(t - at[:,np.newaxis]), axis=0)
        
        self.shape = 0.5*(1/self.wavefrequency_2 )
        sig = pulse_train(
                t=np.arange((self.waveperiod_2/1000)*self.Daq_sample_rate), # time domain
                at=np.array([(self.start_time_2*self.Daq_sample_rate)]),    # times of pulses
                shape=rect(self.shape*self.Daq_sample_rate)                 # shape of pulse
                )
            
        sig = self.wavestep_2*sig
        number = 1       
        sigdouble = []
        #print(sig)  
        while number<=self.waverepeat_2 :
            number = number + 1
            #print(number)
            sigdouble = number*sig[0:(int(self.waveperiod_2/1000)*self.Daq_sample_rate)]
            sig = np.append(sig,sigdouble)
            #print(sig)
        
        #define the control signal
        self.time_control = (self.waveperiod_2/1000)
        at_control = []
        while self.time_control<((self.waveperiod_2/1000)*self.waverepeat_2):
            self.time_control = self.time_control + (self.waveperiod_2/1000)
            self.time_control_2 = self.time_control*self.Daq_sample_rate
            at_control.append(self.time_control_2)
        #print(at_control)
        #print([10*self.Daq_sample_rate, 20*self.Daq_sample_rate, 30*self.Daq_sample_rate, 40*self.Daq_sample_rate, 50*self.Daq_sample_rate, 60*self.Daq_sample_rate, 70*self.Daq_sample_rate, 80*self.Daq_sample_rate, 90*self.Daq_sample_rate, 100*self.Daq_sample_rate, 110*self.Daq_sample_rate])
        
        
        sig2 = pulse_train(
                t=np.arange((self.waverepeat_2+1)*(self.waveperiod_2/1000)*self.Daq_sample_rate),              # time domain      
                at=np.array([1*self.Daq_sample_rate, 2*self.Daq_sample_rate, 3*self.Daq_sample_rate, 4*self.Daq_sample_rate, 5*self.Daq_sample_rate, 6*self.Daq_sample_rate, 7*self.Daq_sample_rate, 8*self.Daq_sample_rate, 9*self.Daq_sample_rate, 10*self.Daq_sample_rate, 11*self.Daq_sample_rate, 12*self.Daq_sample_rate, 13*self.Daq_sample_rate, 14*self.Daq_sample_rate, 15*self.Daq_sample_rate]),  # times of pulses
                shape=rect(self.shape*self.Daq_sample_rate)                 # shape of pulse
                )

        sig2 = self.controlamp_2*sig2
        
        self.finalwave_ = sig+sig2      
        return self.finalwave_
'''
wave = Sabine()
returned_waveform = wave.generate_waveform()
returned_waveform = np.array([returned_waveform]) # Here we change size into (1,n)
print(returned_waveform.shape)
#xlabel = np.arange(len(returned_waveform))/50000
#get_ipython().run_line_magic('matplotlib', 'qt')

plt.figure(1)
plt.plot(returned_waveform[0]) # plot
plt.ylabel('Amplitude')
plt.show()
'''