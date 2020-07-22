# -*- coding: utf-8 -*-
"""
Created on Tue Dec  4 14:12:40 2018

@author: Izak de Heer, adapted from Lex Huisman

"""

import os
import numpy as np

cdir = os.getcwd()
from DMDManager.backend.ALP4 import *
os.chdir(cdir)

class DMD_manager():
    def __init__(self):
        """
        
        Initiate class by instantiating DMD from ALP4 software and initializing
        with device serial number as argument. 
        
        """
        # Load the Vialux .dll
        cdir = os.getcwd()+'./DMDManager'
        print(os.getcwd())

        self.DMD = ALP4(version = '4.3', libDir = r''+cdir) #Use version 4.3 for the alp4395.dll
        
        # Initialize the device
        self.DMD.Initialize(13388)
        self.resolutionx = self.DMD.nSizeX
        self.resolutiony = self.DMD.nSizeY

    def loadMask(self, img_seq):
        """
        
        Load image or image sequence to onboard memory of DMD. 
        In case of binary illumination, bit depth of image should be 1. 
        
        param img: 2d binary numpy array
        type img: Illumination mask
        
        """
    
        if len(img_seq.shape) == 2:
            self.seq_length = 1
            self.image = img_seq.ravel()
        else:
            self.seq_length = img_seq.shape[2]
            
            self.image = np.concatenate([img_seq[:,:,0].ravel(), img_seq[:,:,1].ravel()])
            for i in range(2,self.seq_length):
                self.image = np.hstack([self.image, img_seq[:,:,i].ravel()])
            
#            self.image = np.squeeze(np.reshape(img_seq, (1, -1), order='F'))
        
        self.image = (self.image > 0)*1 #First part makes it True/False, multiplying by 1 converts it to binary
        print(self.image.shape)

        # Binary amplitude image (0 or 1)
        bitDepth = 1    
        self.image*=(2**8-1)
        self.image = self.image.astype(int)
        # Allocate the onboard memory for the image sequence
        # nbImg defines the number of masks
        self.DMD.SeqAlloc(nbImg = self.seq_length, bitDepth = bitDepth)
        
        # Send the image sequence as a 1D list/array/numpy array
        self.DMD.SeqPut(imgData = self.image)

    def startProjection(self, frame_rate = None):
        """
        
        Illuminate the sample using a light pattern that is defined by the mask. 
        
        """
        ### Code needed to display a sequence with waiting time frame_rate. 
        
        # Run the sequence in an infinite loop
        if frame_rate != None:
            self.DMD.SetTiming(illuminationTime=frame_rate)
        self.DMD.Run()
        
    def stopProjection(self):
        # Stop the sequence display
        self.DMD.Halt()
#        self.DMD.FreeSeq()
        
    def freeMemory(self):
        """
        
        Free the onboard RAM of the DMD and disconnect the DMD. 
        
        """
        # Free the sequence from the onboard memory
        self.DMD.Halt()
        try:
            self.DMD.FreeSeq()
        except:
            pass
        
    def deallocDevide(self):
        # De-allocate the device
        self.freeMemory()
        self.DMD.Free()