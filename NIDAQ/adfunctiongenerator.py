# -*- coding: utf-8 -*-
"""
Created on Fri Jul  5 11:12:44 2019

@author: Meng
"""

import numpy as np
from scipy import signal

class generate_AO_for640():
    def __init__(self, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11):
        self.Daq_sample_rate = value1
        self.wavefrequency_2 = value2
        self.waveoffset_2 = value3
        self.waveperiod_2 = value4
        self.waveDC_2 = value5
        self.waverepeat_2 = value6
        self.wavegap_2 = value7
        self.wavestartamplitude_2 = value8
        self.wavebaseline_2 = value9
        self.wavestep_2 = value10
        self.wavecycles_2 = value11
        
    def generate(self):
        self.offsetsamples_number_2 = int(1 + (self.waveoffset_2/1000)*self.Daq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
        self.offsetsamples_2 = self.wavebaseline_2 * np.ones(self.offsetsamples_number_2) # Be default offsetsamples_number is an integer.
        
        self.sample_num_singleperiod_2 = round(self.Daq_sample_rate/self.wavefrequency_2)#round((int((self.waveperiod_2/1000)*self.Daq_sample_rate))/self.wavefrequency_2)
        self.true_sample_num_singleperiod_2 = round((self.waveDC_2/100)*self.sample_num_singleperiod_2)
        self.false_sample_num_singleperiod_2 = self.sample_num_singleperiod_2 - self.true_sample_num_singleperiod_2
        
        self.sample_singleperiod_2 = np.append(self.wavestartamplitude_2 * np.ones(self.true_sample_num_singleperiod_2), self.wavebaseline_2 * np.ones(self.false_sample_num_singleperiod_2))
        self.repeatnumberintotal_2 = int(self.wavefrequency_2*(self.waveperiod_2/1000))
        # In default, pulses * sample_singleperiod_2 = period
        self.sample_singlecycle_2 = np.tile(self.sample_singleperiod_2, int(self.repeatnumberintotal_2)) # At least 1 rise and fall during one cycle
        
        self.waveallcycle_2 = []
        # Adding steps to cycles
        for i in range(self.wavecycles_2):
            cycle_roof_value = self.wavestep_2 * i
            self.cycleappend = np.where(self.sample_singlecycle_2 < self.wavestartamplitude_2, self.wavebaseline_2, self.wavestartamplitude_2 + cycle_roof_value)
            self.waveallcycle_2 = np.append(self.waveallcycle_2, self.cycleappend)
        
        if self.wavegap_2 != 0:
            self.gapsample = self.wavebaseline_2 * np.ones(self.wavegap_2)
            self.waveallcyclewithgap_2 = np.append(self.waveallcycle_2, self.gapsample)
        else:
            self.waveallcyclewithgap_2 = self.waveallcycle_2
            
        self.waverepeated = np.tile(self.waveallcyclewithgap_2, self.waverepeat_2)
        
        self.finalwave_640 = np.append(self.offsetsamples_2, self.waverepeated)    
        self.finalwave_640 = np.append(self.finalwave_640, 0)
        return self.finalwave_640
    
class generate_AO_for488():
    def __init__(self, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11):
        self.Daq_sample_rate = value1
        self.wavefrequency_488 = value2
        self.waveoffset_488 = value3
        self.waveperiod_488 = value4
        self.waveDC_488 = value5
        self.waverepeat_488 = value6
        self.wavegap_488 = value7
        self.wavestartamplitude_488 = value8
        self.wavebaseline_488 = value9
        self.wavestep_488 = value10
        self.wavecycles_488 = value11
        
    def generate(self):
        self.offsetsamples_number_488 = int(1 + (self.waveoffset_488/1000)*self.Daq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
        self.offsetsamples_488 = self.wavebaseline_488 * np.ones(self.offsetsamples_number_488) # Be default offsetsamples_number is an integer.
        
        self.sample_num_singleperiod_488 =  round(self.Daq_sample_rate/self.wavefrequency_488)
        self.true_sample_num_singleperiod_488 = round((self.waveDC_488/100)*self.sample_num_singleperiod_488)
        self.false_sample_num_singleperiod_488 = self.sample_num_singleperiod_488 - self.true_sample_num_singleperiod_488
        
        self.sample_singleperiod_488 = np.append(self.wavestartamplitude_488 * np.ones(self.true_sample_num_singleperiod_488), self.wavebaseline_488 * np.ones(self.false_sample_num_singleperiod_488))
        self.repeatnumberintotal_488 = int(self.wavefrequency_488*(self.waveperiod_488/1000))
        # In default, pulses * sample_singleperiod_2 = period
        self.sample_singlecycle_488 = np.tile(self.sample_singleperiod_488, int(self.repeatnumberintotal_488)) # At least 1 rise and fall during one cycle
        
        self.waveallcycle_488 = []
        # Adding steps to cycles
        for i in range(self.wavecycles_488):
            cycle_roof_value = self.wavestep_488 * i
            self.cycleappend = np.where(self.sample_singlecycle_488 < self.wavestartamplitude_488, self.wavebaseline_488, self.wavestartamplitude_488 + cycle_roof_value)
            self.waveallcycle_488 = np.append(self.waveallcycle_488, self.cycleappend)
        
        if self.wavegap_488 != 0:
            self.gapsample = self.wavebaseline_488 * np.ones(self.wavegap_488)
            self.waveallcyclewithgap_488 = np.append(self.waveallcycle_488, self.gapsample)
        else:
            self.waveallcyclewithgap_488 = self.waveallcycle_488
            
        self.waverepeated = np.tile(self.waveallcyclewithgap_488, self.waverepeat_488)
        
        self.finalwave_488 = np.append(self.offsetsamples_488, self.waverepeated)    
        self.finalwave_488 = np.append(self.finalwave_488, 0)        
        return self.finalwave_488
    
class generate_AO_for532():
    def __init__(self, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11):
        self.Daq_sample_rate = value1
        self.wavefrequency_532 = value2
        self.waveoffset_532 = value3
        self.waveperiod_532 = value4
        self.waveDC_532 = value5
        self.waverepeat_532 = value6
        self.wavegap_532 = value7
        self.wavestartamplitude_532 = value8
        self.wavebaseline_532 = value9
        self.wavestep_532 = value10
        self.wavecycles_532 = value11
        
    def generate(self):
        self.offsetsamples_number_532 = int(1 + (self.waveoffset_532/1000)*self.Daq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
        self.offsetsamples_532 = self.wavebaseline_532 * np.ones(self.offsetsamples_number_532) # Be default offsetsamples_number is an integer.
        
        self.sample_num_singleperiod_532 = round(self.Daq_sample_rate/self.wavefrequency_532)
        self.true_sample_num_singleperiod_532 = round((self.waveDC_532/100)*self.sample_num_singleperiod_532)
        self.false_sample_num_singleperiod_532 = self.sample_num_singleperiod_532 - self.true_sample_num_singleperiod_532
        
        self.sample_singleperiod_532 = np.append(self.wavestartamplitude_532 * np.ones(self.true_sample_num_singleperiod_532), self.wavebaseline_532 * np.ones(self.false_sample_num_singleperiod_532))
        self.repeatnumberintotal_532 = int(self.wavefrequency_532*(self.waveperiod_532/1000))
        # In default, pulses * sample_singleperiod_2 = period
        self.sample_singlecycle_532 = np.tile(self.sample_singleperiod_532, int(self.repeatnumberintotal_532)) # At least 1 rise and fall during one cycle
        
        self.waveallcycle_532 = []
        # Adding steps to cycles
        for i in range(self.wavecycles_532):
            cycle_roof_value = self.wavestep_532 * i
            self.cycleappend = np.where(self.sample_singlecycle_532 < self.wavestartamplitude_532, self.wavebaseline_532, self.wavestartamplitude_532 + cycle_roof_value)
            self.waveallcycle_532 = np.append(self.waveallcycle_532, self.cycleappend)
        
        if self.wavegap_532 != 0:
            self.gapsample = self.wavebaseline_532 * np.ones(self.wavegap_532)
            self.waveallcyclewithgap_532 = np.append(self.waveallcycle_532, self.gapsample)
        else:
            self.waveallcyclewithgap_532 = self.waveallcycle_532
            
        self.waverepeated = np.tile(self.waveallcyclewithgap_532, self.waverepeat_532)
        
        self.finalwave_532 = np.append(self.offsetsamples_532, self.waverepeated)    
        self.finalwave_532 = np.append(self.finalwave_532, 0)        
        return self.finalwave_532
    
class generate_AO_forpatch():
    def __init__(self, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11):
        self.Daq_sample_rate = value1
        self.wavefrequency_patch = value2
        self.waveoffset_patch = value3
        self.waveperiod_patch = value4
        self.waveDC_patch = value5
        self.waverepeat_patch = value6
        self.wavegap_patch = value7
        self.wavestartamplitude_patch = value8
        self.wavebaseline_patch = value9
        self.wavestep_patch = value10
        self.wavecycles_patch = value11
        
    def generate(self):
        self.offsetsamples_number_patch = int(1 + (self.waveoffset_patch/1000)*self.Daq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
        self.offsetsamples_patch = self.wavebaseline_patch * np.ones(self.offsetsamples_number_patch) # Be default offsetsamples_number is an integer.
        
        self.sample_num_singleperiod_patch = round(self.Daq_sample_rate/self.wavefrequency_patch)
        self.true_sample_num_singleperiod_patch = round((self.waveDC_patch/100)*self.sample_num_singleperiod_patch)
        self.false_sample_num_singleperiod_patch = self.sample_num_singleperiod_patch - self.true_sample_num_singleperiod_patch
        
        self.sample_singleperiod_patch = np.append(self.wavestartamplitude_patch * np.ones(self.true_sample_num_singleperiod_patch), self.wavebaseline_patch * np.ones(self.false_sample_num_singleperiod_patch))
        self.repeatnumberintotal_patch = int(self.wavefrequency_patch*(self.waveperiod_patch/1000))
        # In default, pulses * sample_singleperiod_2 = period
        self.sample_singlecycle_patch = np.tile(self.sample_singleperiod_patch, int(self.repeatnumberintotal_patch)) # At least 1 rise and fall during one cycle
        
        self.waveallcycle_patch = []
        # Adding steps to cycles
        for i in range(self.wavecycles_patch):
            cycle_roof_value = self.wavestep_patch * i
            self.cycleappend = np.where(self.sample_singlecycle_patch < self.wavestartamplitude_patch, self.wavebaseline_patch, self.wavestartamplitude_patch + cycle_roof_value)
            self.waveallcycle_patch = np.append(self.waveallcycle_patch, self.cycleappend)
        
        if self.wavegap_patch != 0:
            self.gapsample = self.wavebaseline_patch * np.ones(self.wavegap_patch)
            self.waveallcyclewithgap_patch = np.append(self.waveallcycle_patch, self.gapsample)
        else:
            self.waveallcyclewithgap_patch = self.waveallcycle_patch
            
        self.waverepeated = np.tile(self.waveallcyclewithgap_patch, self.waverepeat_patch)
        
        self.finalwave_patch = np.append(self.offsetsamples_patch, self.waverepeated)    
        self.finalwave_patch = np.append(self.finalwave_patch, 0)        
        return self.finalwave_patch
    
class generate_DO_forcameratrigger():
    def __init__(self, value1, value2, value3, value4, value5, value6, value7):
        self.Daq_sample_rate = value1
        self.wavefrequency_cameratrigger = value2
        self.waveoffset_cameratrigger = value3
        self.waveperiod_cameratrigger = value4
        self.waveDC_cameratrigger = value5
        self.waverepeat_cameratrigger_number = value6
        self.wavegap_cameratrigger = value7
        
    def generate(self):
        
        self.offsetsamples_number_cameratrigger = int(1 + (self.waveoffset_cameratrigger/1000)*self.Daq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
        self.offsetsamples_cameratrigger = np.zeros(self.offsetsamples_number_cameratrigger, dtype=bool) # Be default offsetsamples_number is an integer.
        
        self.sample_num_singleperiod_cameratrigger = round(self.Daq_sample_rate/self.wavefrequency_cameratrigger)
        self.true_sample_num_singleperiod_cameratrigger = round((self.waveDC_cameratrigger/100)*self.sample_num_singleperiod_cameratrigger)
        self.false_sample_num_singleperiod_cameratrigger = self.sample_num_singleperiod_cameratrigger - self.true_sample_num_singleperiod_cameratrigger
        
        self.sample_singleperiod_cameratrigger = np.append(np.ones(self.true_sample_num_singleperiod_cameratrigger, dtype=bool), np.zeros(self.false_sample_num_singleperiod_cameratrigger, dtype=bool))
        self.repeatnumberintotal_cameratrigger = int(self.wavefrequency_cameratrigger*(self.waveperiod_cameratrigger/1000))
        # In default, pulses * sample_singleperiod_2 = period
        self.sample_singlecycle_cameratrigger = np.tile(self.sample_singleperiod_cameratrigger, int(self.repeatnumberintotal_cameratrigger)) # At least 1 rise and fall during one cycle
        
        if self.wavegap_cameratrigger != 0:
            self.gapsample_cameratrigger = np.zeros(self.wavegap_cameratrigger, dtype=bool)
            self.waveallcyclewithgap_cameratrigger = np.append(self.sample_singlecycle_cameratrigger, self.gapsample_cameratrigger)
        else:
            self.waveallcyclewithgap_cameratrigger = self.sample_singlecycle_cameratrigger
            
        self.waverepeated_cameratrigger = np.tile(self.waveallcyclewithgap_cameratrigger, self.waverepeat_cameratrigger_number)
        
        self.finalwave_cameratrigger = np.append(self.offsetsamples_cameratrigger, self.waverepeated_cameratrigger)
        self.finalwave_cameratrigger = np.append(self.finalwave_cameratrigger, False)
   
        return self.finalwave_cameratrigger
    
class generate_DO_for640blanking():
    def __init__(self, value1, value2, value3, value4, value5, value6, value7):
        self.Daq_sample_rate = value1
        self.wavefrequency_640blanking = value2
        self.waveoffset_640blanking = value3
        self.waveperiod_640blanking = value4
        self.waveDC_640blanking = value5
        self.waverepeat_640blanking_number = value6
        self.wavegap_640blanking = value7
        
    def generate(self):
        
        self.offsetsamples_number_640blanking = int(1 + (self.waveoffset_640blanking/1000)*self.Daq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
        self.offsetsamples_640blanking = np.zeros(self.offsetsamples_number_640blanking, dtype=bool) # Be default offsetsamples_number is an integer.
        
        self.sample_num_singleperiod_640blanking = round(self.Daq_sample_rate/self.wavefrequency_640blanking)
        self.true_sample_num_singleperiod_640blanking = round((self.waveDC_640blanking/100)*self.sample_num_singleperiod_640blanking)
        self.false_sample_num_singleperiod_640blanking = self.sample_num_singleperiod_640blanking - self.true_sample_num_singleperiod_640blanking
        
        self.sample_singleperiod_640blanking = np.append(np.ones(self.true_sample_num_singleperiod_640blanking, dtype=bool), np.zeros(self.false_sample_num_singleperiod_640blanking, dtype=bool))
        self.repeatnumberintotal_640blanking = int(self.wavefrequency_640blanking*(self.waveperiod_640blanking/1000))
        # In default, pulses * sample_singleperiod_2 = period
        self.sample_singlecycle_640blanking = np.tile(self.sample_singleperiod_640blanking, int(self.repeatnumberintotal_640blanking)) # At least 1 rise and fall during one cycle
        
        if self.wavegap_640blanking != 0:
            self.gapsample_640blanking = np.zeros(self.wavegap_640blanking, dtype=bool)
            self.waveallcyclewithgap_640blanking = np.append(self.sample_singlecycle_640blanking, self.gapsample_640blanking)
        else:
            self.waveallcyclewithgap_640blanking = self.sample_singlecycle_640blanking
            
        self.waverepeated_640blanking = np.tile(self.waveallcyclewithgap_640blanking, self.waverepeat_640blanking_number)
        
        self.finalwave_640blanking = np.append(self.offsetsamples_640blanking, self.waverepeated_640blanking)
        self.finalwave_640blanking = np.append(self.finalwave_640blanking, False)       
        return self.finalwave_640blanking
    
class generate_DO_for532blanking():
    def __init__(self, value1, value2, value3, value4, value5, value6, value7):
        self.Daq_sample_rate = value1
        self.wavefrequency_532blanking = value2
        self.waveoffset_532blanking = value3
        self.waveperiod_532blanking = value4
        self.waveDC_532blanking = value5
        self.waverepeat_532blanking_number = value6
        self.wavegap_532blanking = value7
        
    def generate(self):
        
        self.offsetsamples_number_532blanking = int(1 + (self.waveoffset_532blanking/1000)*self.Daq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
        self.offsetsamples_532blanking = np.zeros(self.offsetsamples_number_532blanking, dtype=bool) # Be default offsetsamples_number is an integer.
        
        self.sample_num_singleperiod_532blanking = round(self.Daq_sample_rate/self.wavefrequency_532blanking)
        self.true_sample_num_singleperiod_532blanking = round((self.waveDC_532blanking/100)*self.sample_num_singleperiod_532blanking)
        self.false_sample_num_singleperiod_532blanking = self.sample_num_singleperiod_532blanking - self.true_sample_num_singleperiod_532blanking
        
        self.sample_singleperiod_532blanking = np.append(np.ones(self.true_sample_num_singleperiod_532blanking, dtype=bool), np.zeros(self.false_sample_num_singleperiod_532blanking, dtype=bool))
        self.repeatnumberintotal_532blanking = int(self.wavefrequency_532blanking*(self.waveperiod_532blanking/1000))
        # In default, pulses * sample_singleperiod_2 = period
        self.sample_singlecycle_532blanking = np.tile(self.sample_singleperiod_532blanking, int(self.repeatnumberintotal_532blanking)) # At least 1 rise and fall during one cycle
        
        if self.wavegap_532blanking != 0:
            self.gapsample_532blanking = np.zeros(self.wavegap_532blanking, dtype=bool)
            self.waveallcyclewithgap_532blanking = np.append(self.sample_singlecycle_532blanking, self.gapsample_532blanking)
        else:
            self.waveallcyclewithgap_532blanking = self.sample_singlecycle_532blanking
            
        self.waverepeated_532blanking = np.tile(self.waveallcyclewithgap_532blanking, self.waverepeat_532blanking_number)
        
        self.finalwave_532blanking = np.append(self.offsetsamples_532blanking, self.waverepeated_532blanking)
        self.finalwave_532blanking = np.append(self.finalwave_532blanking, False)         
        return self.finalwave_532blanking
    
class generate_DO_for488blanking():
    def __init__(self, value1, value2, value3, value4, value5, value6, value7):
        self.Daq_sample_rate = value1
        self.wavefrequency_488blanking = value2
        self.waveoffset_488blanking = value3
        self.waveperiod_488blanking = value4
        self.waveDC_488blanking = value5
        self.waverepeat_488blanking_number = value6
        self.wavegap_488blanking = value7
        
    def generate(self):
        
        self.offsetsamples_number_488blanking = int(1 + (self.waveoffset_488blanking/1000)*self.Daq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
        self.offsetsamples_488blanking = np.zeros(self.offsetsamples_number_488blanking, dtype=bool) # Be default offsetsamples_number is an integer.
        
        self.sample_num_singleperiod_488blanking = round(self.Daq_sample_rate/self.wavefrequency_488blanking)
        self.true_sample_num_singleperiod_488blanking = round((self.waveDC_488blanking/100)*self.sample_num_singleperiod_488blanking)
        self.false_sample_num_singleperiod_488blanking = self.sample_num_singleperiod_488blanking - self.true_sample_num_singleperiod_488blanking
        
        self.sample_singleperiod_488blanking = np.append(np.ones(self.true_sample_num_singleperiod_488blanking, dtype=bool), np.zeros(self.false_sample_num_singleperiod_488blanking, dtype=bool))
        self.repeatnumberintotal_488blanking = int(self.wavefrequency_488blanking*(self.waveperiod_488blanking/1000))
        # In default, pulses * sample_singleperiod_2 = period
        self.sample_singlecycle_488blanking = np.tile(self.sample_singleperiod_488blanking, int(self.repeatnumberintotal_488blanking)) # At least 1 rise and fall during one cycle
        
        if self.wavegap_488blanking != 0:
            self.gapsample_488blanking = np.zeros(self.wavegap_488blanking, dtype=bool)
            self.waveallcyclewithgap_488blanking = np.append(self.sample_singlecycle_488blanking, self.gapsample_488blanking)
        else:
            self.waveallcyclewithgap_488blanking = self.sample_singlecycle_488blanking
            
        self.waverepeated_488blanking = np.tile(self.waveallcyclewithgap_488blanking, self.waverepeat_488blanking_number)
        
        self.finalwave_488blanking = np.append(self.offsetsamples_488blanking, self.waverepeated_488blanking)
        self.finalwave_488blanking = np.append(self.finalwave_488blanking, False)         
        return self.finalwave_488blanking
    
class generate_DO_forblankingall():
    def __init__(self, value1, value2, value3, value4, value5, value6, value7):
        self.Daq_sample_rate = value1
        self.wavefrequency_blankingall = value2
        self.waveoffset_blankingall = value3
        self.waveperiod_blankingall = value4
        self.waveDC_blankingall = value5
        self.waverepeat_blankingall_number = value6
        self.wavegap_blankingall = value7
        
    def generate(self):
        
        self.offsetsamples_number_blankingall = int(1 + (self.waveoffset_blankingall/1000)*self.Daq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
        self.offsetsamples_blankingall = np.zeros(self.offsetsamples_number_blankingall, dtype=bool) # Be default offsetsamples_number is an integer.
        
        self.sample_num_singleperiod_blankingall = round(self.Daq_sample_rate/self.wavefrequency_blankingall)
        self.true_sample_num_singleperiod_blankingall = round((self.waveDC_blankingall/100)*self.sample_num_singleperiod_blankingall)
        self.false_sample_num_singleperiod_blankingall = self.sample_num_singleperiod_blankingall - self.true_sample_num_singleperiod_blankingall
        
        self.sample_singleperiod_blankingall = np.append(np.ones(self.true_sample_num_singleperiod_blankingall, dtype=bool), np.zeros(self.false_sample_num_singleperiod_blankingall, dtype=bool))
        self.repeatnumberintotal_blankingall = int(self.wavefrequency_blankingall*(self.waveperiod_blankingall/1000))
        # In default, pulses * sample_singleperiod_2 = period
        self.sample_singlecycle_blankingall = np.tile(self.sample_singleperiod_blankingall, int(self.repeatnumberintotal_blankingall)) # At least 1 rise and fall during one cycle
        
        if self.wavegap_blankingall != 0:
            self.gapsample_blankingall = np.zeros(self.wavegap_blankingall, dtype=bool)
            self.waveallcyclewithgap_blankingall = np.append(self.sample_singlecycle_blankingall, self.gapsample_blankingall)
        else:
            self.waveallcyclewithgap_blankingall = self.sample_singlecycle_blankingall
            
        self.waverepeated_blankingall = np.tile(self.waveallcyclewithgap_blankingall, self.waverepeat_blankingall_number)
        
        self.finalwave_blankingall = np.append(self.offsetsamples_blankingall, self.waverepeated_blankingall)
        self.finalwave_blankingall = np.append(self.finalwave_blankingall, False)         
        return self.finalwave_blankingall
    
class generate_DO_forPerfusion():
    def __init__(self, value1, value2, value3, value4, value5, value6, value7):
        self.Daq_sample_rate = value1
        self.wavefrequency_Perfusion = value2
        self.waveoffset_Perfusion = value3
        self.waveperiod_Perfusion = value4
        self.waveDC_Perfusion = value5
        self.waverepeat_Perfusion_number = value6
        self.wavegap_Perfusion = value7
        
    def generate(self):
        
        self.offsetsamples_number_Perfusion = int(1 + (self.waveoffset_Perfusion/1000)*self.Daq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
        self.offsetsamples_Perfusion = np.zeros(self.offsetsamples_number_Perfusion, dtype=bool) # Be default offsetsamples_number is an integer.
        
        self.sample_num_singleperiod_Perfusion = round(self.Daq_sample_rate/self.wavefrequency_Perfusion)
        self.true_sample_num_singleperiod_Perfusion = round((self.waveDC_Perfusion/100)*self.sample_num_singleperiod_Perfusion)
        self.false_sample_num_singleperiod_Perfusion = self.sample_num_singleperiod_Perfusion - self.true_sample_num_singleperiod_Perfusion
        
        self.sample_singleperiod_Perfusion = np.append(np.ones(self.true_sample_num_singleperiod_Perfusion, dtype=bool), np.zeros(self.false_sample_num_singleperiod_Perfusion, dtype=bool))
        self.repeatnumberintotal_Perfusion = int(self.wavefrequency_Perfusion*(self.waveperiod_Perfusion/1000))
        # In default, pulses * sample_singleperiod_2 = period
        self.sample_singlecycle_Perfusion = np.tile(self.sample_singleperiod_Perfusion, int(self.repeatnumberintotal_Perfusion)) # At least 1 rise and fall during one cycle
        
        if self.wavegap_Perfusion != 0:
            self.gapsample_Perfusion = np.zeros(self.wavegap_Perfusion, dtype=bool)
            self.waveallcyclewithgap_Perfusion = np.append(self.sample_singlecycle_Perfusion, self.gapsample_Perfusion)
        else:
            self.waveallcyclewithgap_Perfusion = self.sample_singlecycle_Perfusion
            
        self.waverepeated_Perfusion = np.tile(self.waveallcyclewithgap_Perfusion, self.waverepeat_Perfusion_number)
        
        self.finalwave_Perfusion = np.append(self.offsetsamples_Perfusion, self.waverepeated_Perfusion)
        
        if self.finalwave_Perfusion[-1] == True:
            self.finalwave_Perfusion = np.append(self.finalwave_Perfusion, True)   # Adding a True or False to reset the channel.     
        else:
            self.finalwave_Perfusion = np.append(self.finalwave_Perfusion, False)
            
        return self.finalwave_Perfusion
    
class generate_DO_for2Pshutter():
    def __init__(self, value1, value2, value3, value4, value5, value6, value7):
        self.Daq_sample_rate = value1
        self.wavefrequency_2Pshutter = value2
        self.waveoffset_2Pshutter = value3
        self.waveperiod_2Pshutter = value4
        self.waveDC_2Pshutter = value5
        self.waverepeat_2Pshutter_number = value6
        self.wavegap_2Pshutter = value7
        
    def generate(self):
        
        self.offsetsamples_number_2Pshutter = int(1 + (self.waveoffset_2Pshutter/1000)*self.Daq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
        self.offsetsamples_2Pshutter = np.zeros(self.offsetsamples_number_2Pshutter, dtype=bool) # Be default offsetsamples_number is an integer.
        
        self.sample_num_singleperiod_2Pshutter = round(self.Daq_sample_rate/self.wavefrequency_2Pshutter)
        self.true_sample_num_singleperiod_2Pshutter = round((self.waveDC_2Pshutter/100)*self.sample_num_singleperiod_2Pshutter)
        self.false_sample_num_singleperiod_2Pshutter = self.sample_num_singleperiod_2Pshutter - self.true_sample_num_singleperiod_2Pshutter
        
        self.sample_singleperiod_2Pshutter = np.append(np.ones(self.true_sample_num_singleperiod_2Pshutter, dtype=bool), np.zeros(self.false_sample_num_singleperiod_2Pshutter, dtype=bool))
        self.repeatnumberintotal_2Pshutter = int(self.wavefrequency_2Pshutter*(self.waveperiod_2Pshutter/1000))
        # In default, pulses * sample_singleperiod_2 = period
        self.sample_singlecycle_2Pshutter = np.tile(self.sample_singleperiod_2Pshutter, int(self.repeatnumberintotal_2Pshutter)) # At least 1 rise and fall during one cycle
        
        if self.wavegap_2Pshutter != 0:
            self.gapsample_2Pshutter = np.zeros(self.wavegap_2Pshutter, dtype=bool)
            self.waveallcyclewithgap_2Pshutter = np.append(self.sample_singlecycle_2Pshutter, self.gapsample_2Pshutter)
        else:
            self.waveallcyclewithgap_2Pshutter = self.sample_singlecycle_2Pshutter
            
        self.waverepeated_2Pshutter = np.tile(self.waveallcyclewithgap_2Pshutter, self.waverepeat_2Pshutter_number)
        
        self.finalwave_2Pshutter = np.append(self.offsetsamples_2Pshutter, self.waverepeated_2Pshutter)
        self.finalwave_2Pshutter = np.append(self.finalwave_2Pshutter, False)         
        return self.finalwave_2Pshutter
    
class generate_ramp():
    def __init__(self, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11):
        self.Daq_sample_rate = value1
        self.wavefrequency = value2
        self.waveoffset = value3
        self.waveperiod = value4
        self.wavesymmetry = value5
        self.waverepeat = value6
        self.wavegap = value7
        self.waveheight = value8
        self.wavebaseline = value9
        self.wavestep = value10
        self.wavecycles = value11
    def generate(self):
        self.offsetsamples_number_ramp = int(1 + (self.waveoffset/1000)*self.Daq_sample_rate) # By default one 0 is added 
        self.offsetsamples_ramp = self.wavebaseline * np.ones(self.offsetsamples_number_ramp) # Be default offsetsamples_number is an integer.
        
        t = np.linspace(0, (self.waveperiod/1000), self.Daq_sample_rate*(self.waveperiod/1000))
        triangle_in_1s = self.waveheight/2 * (signal.sawtooth(2 * np.pi * self.wavefrequency * t, self.wavesymmetry))
        self.sample_singlecycle_ramp = triangle_in_1s + self.waveheight/2 + self.wavebaseline
        
        #self.repeatnumberintotal_ramp = int(self.wavefrequency*(self.waveperiod/1000))
        # In default, pulses * sample_singleperiod_2 = period
        #self.sample_singlecycle_ramp = np.tile(self.sample_singleperiod_ramp, int(self.repeatnumberintotal_ramp)) # At least 1 rise and fall during one cycle
        '''
        self.waveallcycle_ramp = []
        # Adding steps to cycles
        for i in range(self.wavecycles):
            cycle_roof_value = self.wavestep * i
            self.cycleappend = np.where(self.sample_singlecycle_ramp < self.waveheight, self.wavebaseline, self.waveheight + cycle_roof_value)
            self.waveallcycle_ramp = np.append(self.waveallcycle_ramp, self.cycleappend)
        '''
        if self.wavegap != 0:
            self.gapsample = self.wavebaseline * np.ones(self.wavegap)
            self.waveallcyclewithgap_ramp = np.append(self.sample_singlecycle_ramp, self.gapsample)
        else:
            self.waveallcyclewithgap_ramp = self.sample_singlecycle_ramp
            
        self.waverepeated = np.tile(self.waveallcyclewithgap_ramp, self.waverepeat)
        
        self.finalwave_ramp = np.append(self.offsetsamples_ramp, self.waverepeated)    
        self.finalwave_ramp = np.append(self.finalwave_ramp, 0)         
        return self.finalwave_ramp
        