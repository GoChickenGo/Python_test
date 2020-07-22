#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 09:38:26 2020

@author: Izak de Heer
"""

from CoordinatesManager.backend.ALP4 import *
import numpy as np
import os

class DMDActuator:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initialize_DMD()
        self.repeat = True
        
    def initialize_DMD(self):
        # Load the Vialux .dll
        cdir = os.getcwd()+'\\CoordinatesManager'
        self.DMD = ALP4(version = '4.3', libDir = r''+cdir) #Use version 4.3 for the alp4395.dll
        
        # Initialize the device
        self.DMD.Initialize(13388)
        print('DMD Initialized')
        
    def disconnect_DMD(self):
        # Clear onboard memory and disconnect
        self.DMD.Free()
        print('DMD disconnected')
    
    def send_data_to_DMD(self, img_seq):
        """
        Load image or image sequence to onboard memory of DMD. 
        In case of binary illumination, bit depth of image should be 1. 
        
        param mask: 2d binary numpy array or stack of 2d arrays
        type mask: Illumination mask
        """
        
        if len(img_seq.shape) == 2:
            self.seq_length = 1
            self.image = img_seq.ravel()
        else:
            self.seq_length = img_seq.shape[2]
                
            self.image = np.concatenate([img_seq[:,:,0].ravel(), img_seq[:,:,1].ravel()])
            for i in range(2,self.seq_length):
                self.image = np.hstack([self.image, img_seq[:,:,i].ravel()])
        
        self.image = (self.image > 0)*1 #First part makes it True/False, multiplying by 1 converts it to binary
        
        # Binary amplitude image (0 or 1)
        bitDepth = 1    
        self.image*=(2**8-1)
        self.image = self.image.astype(int)
        # Allocate the onboard memory for the image sequence
        # nbImg defines the number of masks
        
        self.DMD.SeqAlloc(nbImg = self.seq_length, bitDepth = bitDepth)
        
        # Send the image sequence as a 1D list/array/numpy array
        self.DMD.SeqPut(imgData = self.image)
        print('Data loaded to DMD')
        
    def start_projection(self):
        """
        In case of a image sequence, the loop parameter determines whether the 
        sequence is projected once of repeatedly. 
        """
        self.DMD.Run(loop = self.repeat)
        
        print('Projection started')
        
    def stop_projection(self):
        self.DMD.Halt()
        print('Projection stopped')
        
    def set_timing(self, frame_rate):
        """
        Set the duration of one frame in a image sequence. NB: time is in microseconds.
        """
        self.DMD.SetTiming(illuminationTime=frame_rate)
        print('Timing set')
        
    def set_repeat(self, repeat):
        self.repeat = repeat
        
    def free_memory(self):
        self.DMD.Halt()
        self.DMD.FreeSeq()
        
        self.repeat = True
     
        