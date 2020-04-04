# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 10:21:11 2019

Data acquisition class for the camera. 

TO DO:
    -When in external triggering mode, the program functions very slow/crashes
    when the camera stops receiving triggers (ergo does not gather any more 
    images). This is an important point to fix. Probably has to do with the UI,
    not the backend..
    
    -It is possible to write to disk while acquiring images, but unfortunately
    the isbufferoverflowed check will not work then. Possible solution would be 
    to thread the isbufferoverflowed check, and still write out data to disk!
    

@author: dvanderheijden
"""
import numpy as np
import sys
import os
import cv2
import time
import skimage

import skimage.external.tifffile as skimtiff
from skimage.external import tifffile

from PyQt5 import QtCore as qtc
from PyQt5.QtCore import pyqtSignal, QThread

# Append MM directory to path

'''
IMPORTANT

1. You must be running python 3.6.x for this to work! If you are using anaconda
you can use the conda install function to downgrade python. Otherwise do so
manually. 

2. Follow these instructions to get micro-manager to work with python 3.6;
 https://github.com/zfphil/micro-manager-python3 
 
3. Make sure you download a nightly build of micro-manager from between 
2016-06-09 and 2017-11-07!

The following lines of code will append the micro-manager to the python path so 
you can use all of its functionality.
'''
try:
    sys.path.append(r'C:\Program Files\Micro-Manager-2.0beta')
    prev_dir = os.getcwd()    
    os.chdir(r'C:\Program Files\Micro-Manager-2.0beta') 
    #Must change to micro-manager directory for method to work!
    
    import MMCorePy
    
    mmc = MMCorePy.CMMCore()
    os.chdir(('./'))
    # Success!
    print("Micro-manager was loaded sucessfully!")  
except:
    pass

class Camera(QThread):
    '''
    trying to create a QThread class so I can thread the camera while running the ui
    '''
    timed_filming_done = pyqtSignal(bool) 
    
    def __init__(self, DEVICE, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mmc = MMCorePy.CMMCore()
        self.name = DEVICE[0]
        self.mmc.loadDevice(*DEVICE)
        self.mmc.initializeDevice(self.name)
        self.mmc.setCameraDevice(self.name)
        self.mmc.initializeCircularBuffer()

        self.mmc.setProperty(self.name,'EXPOSURE FULL RANGE', 'ENABLE')
        #this should enable exposure values between

        self.initial_picture = cv2.imread('neuron.png', 0)
        self.image = self.initial_picture

        self.image_roi = self.initial_picture
        self.exp_time = 50
        self.height = self.mmc.getImageHeight()
        self.width = self.mmc.getImageWidth()
        
        self.frames = 0
        
        self.tot_ims = 10
        self.interval = 1 #Does not matter for orca flash 4!

        self.mode = "Continuous"

        self.done = False  
    def print_properties(self):
        ''' print all properties. Change the mutable ones with:
            self.mmc.setProperty('device_name', '' property_name'. 'value')
        '''
        prop_ro = list()
        print('\nDEVICE PROPERTIES LIST:\n')
        for prop in self.mmc.getDevicePropertyNames(self.name):
            if self.mmc.isPropertyReadOnly(self.name, prop):
                prop_ro.append(prop)
            else:
                low = self.mmc.getPropertyLowerLimit(self.name, prop)
                up =self.mmc.getPropertyUpperLimit(self.name, prop)
                available_vals=\
                ', '.join(self.mmc.getAllowedPropertyValues(self.name, prop))
                if(available_vals):
                    print(str(prop) +'= '+ \
                                    self.mmc.getProperty(self.name, prop)+\
                                    ' --> possibe values from this set: {' \
                                                    + available_vals + '}\n')
                else:
                    print(str(prop) +'= '+ \
                                    self.mmc.getProperty(self.name, prop)\
                                    + ', choose from '+ \
                                            str(low)+ ' to ' + str(up) +' \n')
        print ('\nRead-only prop:\n', prop_ro)
        return None
    #-----------------------Setting Properties---------------------------------
    def set_buf_size(self,size):
        self.mmc.setCircularBufferMemoryFootprint(size)
    
    def get_framerate(self):
        exp_time = self.mmc.getExposure()/1000
        Readout_time = float(self.mmc.getProperty('Camera','ReadoutTime'))
        time = Readout_time
        
        if time > exp_time:
            FPS = int(1/time)
        else:
            FPS = int(1/exp_time)  
        return FPS

    def set_exposure_time(self, exptime):
        exposure_time = exptime #unchanged for miliseconds
        self.mmc.setExposure(exposure_time)
        
    def get_exposure_time(self):
        return(self.mmc.getExposure())     
        
    def imsize(self):
        '''
        returns the image size in bytes, handy for calculating the required 
        buffer size!
        '''
        pixelbytes = self.mmc.getBytesPerPixel()
        pixels = self.mmc.getImageBufferSize()
        imsize = pixels*pixelbytes/1000000
        return imsize
    
    #-----------------------Recording Thread-----------------------------------           
    def start_recording(self):
        self.mode = "Continuous"
        self.start()
        
    def timed_recording(self,frames):
        self.mode = "Timed"
        self.tot_ims = frames
        self.start()
        
    def run(self):
        self.timed_filming_done.emit(False)        
        self.mmc.clearCircularBuffer()
        self.mmc.prepareSequenceAcquisition(self.name)        
        timestr = time.strftime("%m-%d-%Y_%H;%M;%S")
        video_name = "Videos/video_"+"{}".format(timestr)+".tif"               
        self.frames = 0              
        
        if self.mode == "Continuous":
            print("Starting continuous video")               
            self.mmc.startContinuousSequenceAcquisition(self.interval) 
            start_time = time.time()      
            while not self.isInterruptionRequested():                    
                if self.mmc.isBufferOverflowed():
                    print("Circular buffer overflowed") 
                    self.mmc.stopSequenceAcquisition()                                                   
                    break     
            self.rec_time = time.time() - start_time
            self.mmc.stopSequenceAcquisition()    
            with skimtiff.TiffWriter(video_name, append = True, imagej = True)\
            as tif:                       
                while self.mmc.getRemainingImageCount() > 0: 
                    self.image = self.mmc.popNextImage() 
                    self.frames += 1
                    tif.save(self.image, compress=0)
            print("Done writing " + str(self.frames) + " frames, recorded for "\
            + str(round(self.rec_time,1)) + " seconds." )
            self.timed_filming_done.emit(True)                          
 
        elif self.mode == "Timed":    
            print("Start recording " + str(self.tot_ims) + " frames.")              
            self.mmc.startContinuousSequenceAcquisition(self.interval)  
            '''
            The self.interval only works for some camera models. It makes no 
            difference for the Hamamatsu orca flash 4!
            '''
            start_time = time.time()
            while self.mmc.getRemainingImageCount() < self.tot_ims - 1:
                if self.mmc.isBufferOverflowed():
                    print("Circular buffer overflowed") 
                    self.mmc.stopSequenceAcquisition()
                    break
                if self.isInterruptionRequested():
                    print("Stopped recording manually")
                    self.mmc.stopSequenceAcquisition()
                    break                       
            self.mmc.stopSequenceAcquisition()
            self.rec_time = time.time() - start_time
            with skimtiff.TiffWriter(video_name, append = True, imagej = True) \
            as tif:
                while self.mmc.getRemainingImageCount() > 0: 
                    self.image = self.mmc.popNextImage() 
                    self.frames += 1
                    tif.save(self.image, compress=0)                    
            print("Done writing " + str(self.frames) + " frames, recorded for " \
                  + str(round(self.rec_time,1)) + " seconds." )               
            self.timed_filming_done.emit(True)
            
        #----------------------Beta modes and testing functions----------------    
        elif self.mode == "Timed_v2":    
            '''
            This mode works perfectly fine while testing with the democam, but 
            for some reason the hamamatsu camera can't hande the 
            startSequenceAcquisitionfunction if called upon the second time. 
            This mode would be ideal (as startsequenceacquisition automaticaLly
            stops when the circular buffer overflows) but for now can't be used.
            '''
            print("Starting timed video")      
            self.mmc.startSequenceAcquisition(self.name, self.tot_ims, \
                                              self.interval, True)      
            with skimtiff.TiffWriter(video_name, append = True, imagej = True)\
            as tif:                
                for n in range(0,self.tot_ims):                  
                    if self.mmc.isBufferOverflowed():
                        print("Circular buffer overflowed") 
                        self.mmc.stopSequenceAcquisition()                                                   
                        break
                    elif self.isInterruptionRequested():
                        print("Stopped recording manually")
                        self.mmc.stopSequenceAcquisition()
                        break                   
                    while self.mmc.getRemainingImageCount() == 0: 
                        """
                        I'm using a for loop, so the if getRemainingImageCount>0
                        function does not work here (the number of iterations 
                        would not be correct.) Therefore I'm using a while loop
                        with a sleep. Could also use a pass statement but that
                        would be more computationally expensive. 
                        """
                        time.sleep(0.001) #waiting a ms             
                    self.image = self.mmc.popNextImage()
                    tif.save(self.image,compress=0, photometric = 'minisblack')
                    self.frames += 1     
            print("Done writing " + str(self.frames) + " frames.")
            self.timed_filming_done.emit(True)     
            
        elif self.mode == "framerate_tester":
            '''
            This mode has been built to check the framerate of the camera 
            without writing out files. Should not be used except for testing.
            '''
            print("Start recording " + str(self.tot_ims) + " frames with the tester.")              
            self.mmc.startContinuousSequenceAcquisition(self.interval)  

                  
            start_time = time.time()
            while self.mmc.getRemainingImageCount() < self.tot_ims - 1:
                if self.mmc.isBufferOverflowed():
                    print("Circular buffer overflowed") 
                    self.mmc.stopSequenceAcquisition()
                    break
                if self.isInterruptionRequested():
                    print("Stopped recording manually")
                    self.mmc.stopSequenceAcquisition()
                    break                       
            self.mmc.stopSequenceAcquisition()
            self.rec_time = time.time() - start_time
            self.frames = self.mmc.getRemainingImageCount()                
            print("Done writing " + str(self.frames) + " frames, recorded for " \
                  + str(round(self.rec_time,1)) + "seconds")   
            self.done = True 
                  
    def stop_recording(self):
        self.requestInterruption()
        
    #-----------------------ROI selection--------------------------------------

    def set_cam_roi(self, x, y, x_size, y_size):
        '''
        The Hamamatsu flash 4 ROI only works with multiples of 4! Here I make 
        sure that only multiples of 4 are passed on to the camera. Don't know if 
        this has to do with binning. I also make sure it doesn't pass a ROI of 
        0 size since this crashes the program!
        '''
        x_4 = 4*int(x/4)

        y_4 = 4*int(y/4)

        x_size_4 = 4*int(x_size/4)
        if x_size_4 == 0:
            x_size_4 += 4
            
        y_size_4 = 4*int(y_size/4)
        if y_size_4 == 0:
            y_size_4 += 4

        self.mmc.setROI(x_4, y_4, x_size_4, y_size_4)

    def snap_roi(self):
        if self.mmc.getProperty(self.name, 'TRIGGER SOURCE') == "EXTERNAL":
            self.mmc.setProperty(self.name, 'TRIGGER SOURCE', "INTERNAL")        
            self.mmc.clearROI()
            self.mmc.snapImage()
            self.image_roi = self.mmc.getImage()
            self.mmc.setProperty(self.name, 'TRIGGER SOURCE', "EXTERNAL")
        else:
            self.mmc.clearROI()
            self.mmc.snapImage()
            self.image_roi = self.mmc.getImage()
            
            
    def clear_roi(self):
        self.mmc.clearROI()
   
    #-----------------------Getting a view------------------------------------- 
    def startseqacq(self):
        self.mmc.clearCircularBuffer()
        self.mmc.prepareSequenceAcquisition(self.name)
        self.mmc.startContinuousSequenceAcquisition(1)
        
    def stopseqacq(self):
        self.mmc.stopSequenceAcquisition()
    
    def get_frame(self):
        if self.mmc.getRemainingImageCount() > 0:
            self.image = self.mmc.getLastImage()
    
    def get_single_frame(self):
        self.mmc.snapImage()
        self.image = self.mmc.getImage()


    #-----------------------Taking picture-------------------------------------   
    def snap(self, saveToDir, fileName):
        if self.mmc.isSequenceRunning():
            self.stopseqacq()
            self.mmc.snapImage()
            self.image = self.mmc.getImage()
            self.startseqacq()
            self.save_picture(self.image, saveToDir, fileName)
        else:
            self.mmc.snapImage()
            self.image = self.mmc.getImage()
            self.save_picture(self.image, saveToDir, fileName)
            
    def save_picture(self, picture, saveToDir, fileName):    
        if fileName == None:
            timestr = time.strftime("%m-%d-%Y_%H;%M;%S")
            picture_name = saveToDir + "/picture_"+"{}".format(timestr)+".tiff"    
        else:
            picture_name = saveToDir + "/"+fileName+".tiff"
        skimtiff.imsave(picture_name, picture, compress=0)
#        print("picture taken")

    #-----------------------Closing Camera-------------------------------------
    def close_camera(self):
        self.mmc.reset()      
    
    
if __name__ == "__main__": 
    def test():  
        mmc.reset()
        DEVICE = ['Camera', 'HamamatsuHam', 'HamamatsuHam_DCAM']
        cam = Camera(DEVICE)
#        cam.set_buf_size(250)
#        cam.mode = "Test"
#        cam.interval = 1
#        cam.timed_recording(100)
#        time.sleep(15)
        cam.print_properties()
    test()

