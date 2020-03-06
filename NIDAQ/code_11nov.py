#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 15:20:54 2019

@author: sabinejonkman
"""

import matplotlib.pyplot as plt
import numpy as np
import os

class Sabine():
    def __init__(self):      
        # Here we initialize the attributes of object Sabine
        self.Daq_sample_rate = int(50000)
        self.wave_frequency = float(2)# within the single period 
        self.wave_offset = int(0) # in ms when the first wave starts
        self.wave_period = int(1000) # in ms
        self.wave_dutycircle = int(50)# of single period
        self.wave_repeatnumber = int(10) # how many times u want to repeat the period
        self.wave_gap_inbetween = [int(100000)] # gap between repeat
        self.wavestartamplitude = float(2) #hight of the first 
        self.wavebaseline = float(0)
        self.wavestep = float(0.20) # change between neighbour cycle
        self.wavecycles = int(1) # repeats of the exact same waveform 
        self.start_time = float(0.5) # the location in time of the first wave 
        self.control_amplitude = float(0.33) # the height of the control amplitude 
        
    def generate_waveform(self):      
        #Here we call the function below(generate_AO), feed in the parameters and get the waveform                         
        s = generate_AO(self.Daq_sample_rate, self.wave_frequency, self.wave_offset, self.wave_period, self.wave_dutycircle
                               , self.wave_repeatnumber, self.wave_gap_inbetween, self.wavestartamplitude, self.wavebaseline, self.wavestep, self.wavecycles, self.start_time, self.control_amplitude)
        self.finalwave = s.generate()
        return self.finalwave

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
                t=np.arange(int(self.waveperiod_2/1000)*self.Daq_sample_rate), # time domain
                at=np.array([(self.start_time_2*self.Daq_sample_rate)]),    # times of pulses
                shape=rect(self.shape*self.Daq_sample_rate)                 # shape of pulse
                )
            
        sig = self.wavestep_2*sig
        number = 1       
        sigdouble = []
        print(sig)  
        while number<=self.waverepeat_2 :
            number = number + 1
            print(number)
            sigdouble = number*sig[0:(int(self.waveperiod_2/1000)*self.Daq_sample_rate)]
            sig = np.append(sig,sigdouble)
            print(sig)
        
        #define the control signal
        self.time_control = 0
        at_control = []
        while self.time_control<=((self.waveperiod_2/1000)*self.waverepeat_2):
            self.time_control = self.time_control + (self.waveperiod_2/1000)
            self.time_control_2 = self.time_control*self.Daq_sample_rate
            at_control.append(self.time_control_2)
        
        sig2 = pulse_train(
                t=np.arange((self.waverepeat_2+1)*int(self.waveperiod_2/1000)*self.Daq_sample_rate),              # time domain      
                at=np.array(at_control),  # times of pulses
                shape=rect(self.shape*self.Daq_sample_rate)                 # shape of pulse
                )

        sig2 = self.controlamp_2*sig2
        
        self.finalwave_640 = sig+sig2      
        return self.finalwave_640

'''Now we execute the preset functions'''
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

tp_analog = np.dtype([('Waveform', float, (len(returned_waveform[0]),)), ('Sepcification', 'U20')])
analogcontainer_array = np.zeros(1, dtype =tp_analog)
analogloopnum = 0

key = ['640AO']

savedirectory = r'C:\Users\Meng\Desktop'
for i in range(1):
    analogcontainer_array[i] = np.array([(returned_waveform[i], key[i])], dtype =tp_analog)
np.save(os.path.join(savedirectory, 'Import_wavefroms_sr_'+ str(wave.Daq_sample_rate)), analogcontainer_array)
