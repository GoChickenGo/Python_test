# -*- coding: utf-8 -*-
"""
Created on Thu Jul 16 15:47:20 2020

@author: xinmeng
"""

import os

# Ensure that the Widget can be run either independently or as part of Tupolev.
if __name__ == "__main__":
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname+'/../')
    # os.chdir(os.getcwd()+'/')
from NIDAQ.DAQoperator import DAQmission
# Backend
    
import numpy as np
import math
from scipy import signal
import matplotlib.pyplot as plt
import time

class Servo:
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sampling_rate = 10000
        self.PWM_frequency = 50
        self.mission = DAQmission()
        
    def power_on(self):
        self.mission.sendSingleDigital(channel = 'servo_power_1', value = True)
#        time.sleep(1.5)
        
    def power_off(self):
        self.mission.sendSingleDigital(channel = 'servo_power_1', value = False)
    
    def rotate(self, degree):
        # Convert degree to duty cycle in PWM.
        if degree >= 0 and degree <= 360:
            dutycycle = 0.02#round((degree/180) * 0.05 + 0.05, 6)
            
            PWM_wave = self.blockWave(self.sampling_rate, self.PWM_frequency, dutycycle, repeats = 50)
            
            PWM_wave = np.where(PWM_wave == 0, False, True)
#            plt.figure()
#            plt.plot(PWM_wave)
#            plt.show()
            PWM_wave_organized = np.array([('servo_modulation_1', PWM_wave), ('servo_power_1', np.ones(len(PWM_wave), dtype = bool))],
                          dtype=[('Sepcification', 'U20'), ('Waveform', bool, (len(PWM_wave),))])
            
            self.mission.runWaveforms(clock_source = "DAQ", sampling_rate = self.sampling_rate, analog_signals = {},\
                                    digital_signals = PWM_wave_organized, readin_channels = {})
            
        else:
            print('Rotation degree out of range!')
    
    def blockWave(self, sampleRate, frequency, dutycycle, repeats, voltMin = 0, voltMax = 5):
        """
        Generates a one period blockwave. 
        sampleRate      samplerate set on the DAQ (int)
        frequency       frequency you want for the block wave (int)
        voltMin         minimum value of the blockwave (float)
        voltMax         maximum value of the blockwave (float)
        dutycycle       duty cycle of the wave (wavelength at voltMax) (float)
        """
        wavelength = int(sampleRate/frequency) #Wavelength in number of samples
        #The high values 
        high = np.ones(math.ceil(wavelength*dutycycle))*voltMax
        #Low values
        low = np.ones(math.floor(wavelength*(1-dutycycle)))*voltMin
        #Adding them
        single_period = np.append(high, low)
        """
        Repeats the wave a set number of times and returns a new repeated wave.
        """        
        extendedWave = np.array([])
        for i in range(repeats):
            extendedWave = np.append(extendedWave, single_period)
            
        return extendedWave        


if __name__ == "__main__":
     
     servo= Servo()
#     servo.power_on()
     servo.rotate(0)
     servo.rotate(180)
#     servo.power_off()
