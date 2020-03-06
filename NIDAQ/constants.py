# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 11:54:58 2019

@author: lhuismans

This class contains all the constants that are frequently used and will stay unchanged
(for a long time).
"""

class MeasurementConstants:
    def __init__(self):
        #Seal test
        self.patchSealSampRate = 10000 #Samples/s
        self.patchSealMinVol = 0
        self.patchSealMaxVol = 0.01
        self.patchSealFreq = 100
        self.patchSealDuty = 0.5
        
class HardwareConstants:
    def __init__(self):
        self.maxGalvoSpeed = 20000.0 #Volt/s
        self.maxGalvoAccel = 1.54*10**8 #Acceleration galvo in volt/s^2
        
        self.pmt_3v_indentation_pixels = 52