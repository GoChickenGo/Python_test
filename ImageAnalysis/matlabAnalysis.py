# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 09:59:08 2019

@author: xinmeng

Based on basicanalysis matlab code: 'import2pdaq.m'
"""

import numpy as np
import os
#sizebytes = os.path.getsize('M:/tnw/ist/do/projects/Neurophotonics/Brinkslab/Data/Patch clamp/2019-03-01/20190301-165244/20190301-165244--data.Ip')
#inputfilename = 'M:/tnw/ist/do/projects/Neurophotonics/Brinkslab/Data/Patch clamp/2019-03-01/20190301-165244/20190301-165244--data.Ip'

class readbinaryfile():
    def __init__(self, filepath):
        self.filepath = filepath
        
    def readbinarycurve(self):    
        
        sizebytes = os.path.getsize(self.filepath)
        inputfilename = (self.filepath)
        
        with open(inputfilename, 'rb') as fid:
            data_array_h1 = np.fromfile(fid, count=2, dtype='>d')
            data_array_sc = np.fromfile(fid, count=(int(data_array_h1[0])*int(data_array_h1[1])), dtype='>d')
            data_array_sc=np.reshape(data_array_sc, (int(data_array_h1[0]), int(data_array_h1[1])), order='F')
            
            data_array_h1[1]=1
            data_array_sc = data_array_sc[:,1]
            
            data_array_samplesperchannel =  (sizebytes-fid.tell())/2/data_array_h1[1]
            
            data_array_udat = np.fromfile(fid, count=(int(data_array_h1[1])*int(data_array_samplesperchannel)), dtype='>H')#read as uint16
            data_array_udat_1 = data_array_udat.astype(np.int32)#convertdtype here as data might be saturated, out of uint16 range
            data_array_sdat = data_array_udat_1-(2**15)
            
        temp=np.ones(int(data_array_samplesperchannel))*data_array_sc[1]
        
        for i in range(1, int(data_array_h1[0])-1):
            L=(np.ones(int(data_array_samplesperchannel))*data_array_sc[i+1])*np.power(data_array_sdat, i)
            temp=temp+L
        
        data = temp
        srate= data_array_sc[0]
        
        return data, srate
    
class extractV():
    def __init__(self, images, Vin):
        self.readin_images_patch = images.copy()
        #self.readin_images_patch
        self.readin_voltage_patch = Vin.copy()
        
        sizex = self.readin_images_patch.shape[1]
        sizey = self.readin_images_patch.shape[2]
        
        self.matanalysis_averageimage = np.mean(self.readin_images_patch, axis = 0) # This is the mean intensity image of the whole video stack.
        self.average_voltage = np.mean(self.readin_voltage_patch) # Mean value of the waveform that you want to correlate with(patch clamp voltage signal or camera trace).
        self.voltage_diff = self.readin_voltage_patch - self.average_voltage
        self.voltagelength = len(self.readin_voltage_patch)
        
        #subtract off background
        #for i in range(len(self.readin_images_patch)): # readin_images_patch = imgs in matlab
        self.matanalysis_averageimage_tos = np.tile(self.matanalysis_averageimage, (self.voltagelength,1,1))
        self.readin_images_patch = self.readin_images_patch - self.matanalysis_averageimage_tos
            
        #correlate the changes in intensity with the applied voltage
        self.dv2 = np.resize(self.voltage_diff,(self.voltagelength,1,1))
        
        #self.dvmat = np.tile(self.dv2, (1,sizex,sizey))
        
        self.corrimage = self.readin_images_patch.copy()
        #for i in range(self.voltagelength):
        for i in range(self.voltagelength):
            self.corrimage[i] = self.corrimage[i]*self.dv2[i]  
        self.corrimage = np.mean(self.corrimage, axis = 0)/np.mean(((self.voltage_diff)**2)) #normalize to magnitude of voltage changes (DV*DF./DV^2)
        
        #calculate a dV estimate at each pixel, based on the linear regression.
        self.images2 = np.zeros(self.readin_images_patch.shape)
        corrmat = np.tile(self.corrimage, (self.voltagelength,1,1))
        #for i in range(self.voltagelength):
        self.images2 = self.readin_images_patch/corrmat
          
        self.imtermediate = np.zeros(self.images2.shape)
    
        #Look at the residuals to get a noise at each pixel
        for i in range(self.voltagelength):
            self.imtermediate[i] = (self.images2[i] - self.dv2[i])**2
        self.sigmaimage = np.mean(self.imtermediate, axis = 0)
        
        self.weightimage = 1/self.sigmaimage#weightimg scales inverted with variance between input voltage and measured "voltage": 
                                            #variance is expressed in units of voltage squared. standard way to do it would be to cast input voltage in form of fit and leave data as data. 
        self.weightimage[np.isnan(self.weightimage)] = 0
        self.weightimage = self.weightimage/np.mean(self.weightimage)
        
        self.images2[np.isnan(self.images2)] = 0 #Set places where imgs2 == NaN to zero
        '''
        dVout = squeeze(mean(mean(imgs2.*repmat(weightimg, [1 1 L])))) #squeeze takes something along the time axis and puts it 1xn vector

        Vout = dVout + avgV
        offsetimg = avgimg - avgV*corrimg
        '''
    def cal(self):
        return self.corrimage, self.weightimage, self.sigmaimage