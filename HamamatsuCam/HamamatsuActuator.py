#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 27 17:14:53 2020

@author: xinmeng
"""
import sys
import os 

try:
    from HamamatsuDCAM import *
except:
    from HamamatsuCam.HamamatsuDCAM import *
# Append parent folder to system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from PIL import Image
import skimage.external.tifffile as skimtiff
import ctypes
import time

# =============================================================================
# Script based Hamamatsu camera operations
# =============================================================================

class CamActuator:
    """
    This is a script based operation class for the HamamatsuDCAM which is a ctype based dll wrapper.
    
    Frequent used parameters:
        params = ["internal_frame_rate",
                  "timing_readout_time",
                  "exposure_time",
                  "subarray_hsize",
                  "subarray_hpos",
                  "subarray_vsize",
                  "subarray_vpos",
                  "subarray_mode",
                  "image_framebytes",
                  "buffer_framebytes",
                  "trigger_source",
                  "trigger_active"]
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """
        # =============================================================================
        #         Initialization of the camera.
        #         Load dcamapi.dll version: 19.12.641.5901
        # =============================================================================
        """
        self.isStreaming = False
        
    def initializeCamera(self):
        # =====================================================================
        #         Initialize the camera
        #         Set default camera properties.
        # =====================================================================
        self.dcam = ctypes.WinDLL(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\People\Xin Meng\Code\Python_test\HamamatsuCam\19_12\dcamapi.dll')

        paraminit = DCAMAPI_INIT(0, 0, 0, 0, None, None) 
        paraminit.size = ctypes.sizeof(paraminit)
        error_code = self.dcam.dcamapi_init(ctypes.byref(paraminit))
        #if (error_code != DCAMERR_NOERROR):
        #    raise DCAMException("DCAM initialization failed with error code " + str(error_code))
        
        n_cameras = paraminit.iDeviceCount
        print("found:", n_cameras, "cameras")
        
        if (n_cameras > 0):
            #------------------------Initialization----------------------------
            self.hcam = HamamatsuCameraMR(camera_id = 0)
            
            # Enable defect correction
            self.hcam.setPropertyValue("defect_correct_mode", 2)
            # Set the readout speed to fast.
            self.hcam.setPropertyValue("readout_speed", 2)
            # Set the binning to 1.
            self.hcam.setPropertyValue("binning", "1x1")
            
    def setROI(self, ROI_vpos, ROI_hpos, ROI_vsize, ROI_hsize):
        # Set the roi of caamera, first the roi poitions and then the size.
        if ROI_hsize == 2048 and ROI_vsize == 2048:
            self.hcam.setPropertyValue("subarray_mode", "OFF")
            
        else:
        # set subarray mode off. This setting is not mandatory, but you have to control the setting order of offset and size when mode is on.
            self.hcam.setPropertyValue("subarray_mode", "OFF")
            self.hcam.setPropertyValue("subarray_hsize", ROI_hsize)
            self.hcam.setPropertyValue("subarray_vsize", ROI_vsize)
            self.hcam.setPropertyValue("subarray_hpos", ROI_hpos)
            self.hcam.setPropertyValue("subarray_vpos", ROI_vpos)
            self.hcam.setPropertyValue("subarray_mode", "ON")
            
    def SnapImage(self, exposure_time):
        """
        # =====================================================================
        #         Snap and return captured image.
        #         - exposure_time: Exposure time of the camera.
        # =====================================================================
        """
        self.hcam.setPropertyValue("exposure_time", exposure_time)
        
        self.hcam.setACQMode("fixed_length", number_frames = 1)
        self.hcam.startAcquisition()              
        # Start pulling out frames from buffer
        video_list = []
        imageCount = 0 # The actual frame number that gets recorded.
        for _ in range(1): # Record for range() number of images.
            [frames, dims] = self.hcam.getFrames() # frames is a list with HCamData type, with np_array being the image.
            for aframe in frames:
                video_list.append(aframe.np_array)
                imageCount += 1

        if len(video_list) > 1:
            ImageSnapped = np.resize(video_list[-1], (dims[1], dims[0]))
        else:
            ImageSnapped = np.resize(video_list[0], (dims[1], dims[0]))
        
        self.hcam.stopAcquisition()
        
        return ImageSnapped
    
    def StartStreaming(self, trigger_source, BufferNumber, **kwargs):
        # =====================================================================
        #         Start the camera video streaming.
        #         - trigger_source: specify the camera trigger mode.
        #         - BufferNumber: number of frames assigned for video.
        #         - **kwargs can be set as camera property name and desired value pairs, 
        #           like: trigger_active = "SYNCREADOUT"
        # =====================================================================
        
        # Set the trigger source
        if trigger_source == "INTERNAL":
            self.hcam.setPropertyValue("trigger_source", "INTERNAL")
        elif trigger_source == "EXTERNAL":
            self.hcam.setPropertyValue("trigger_source", "EXTERNAL")
        elif trigger_source == "MASTER PULSE":
            self.hcam.setPropertyValue("trigger_source", "MASTER PULSE") 
        
        # Set extra input settings
        for camProName, value in kwargs.items():
            self.hcam.setPropertyValue("trigger_active", value)
        
        # Start the acquisition
        self.hcam.setACQMode("fixed_length", number_frames = BufferNumber)
        self.hcam.startAcquisition()              
        self.isStreaming = True
        
        # Start pulling out frames from buffer
        self.video_list = []
        self.imageCount = 0 # The actual frame number that gets recorded.
        for _ in range(BufferNumber): # Record for range() number of images.
            [frames, self.dims] = self.hcam.getFrames() # frames is a list with HCamData type, with np_array being the image.
            for aframe in frames:
                self.video_list.append(aframe.np_array)
                self.imageCount += 1
                
    def StopStreaming(self, saving_dir = None):
        # =====================================================================
        #         Stop the streaming and save the file.
        #         - saving_dir: directory in which the video is saved.
        # =====================================================================
        
        # Stop the acquisition
        self.hcam.stopAcquisition()        
        self.isStreaming = False
        
        if saving_dir != None:
            # Save the file.
            with skimtiff.TiffWriter(saving_dir, append = True, imagej = True)\
            as tif:                
                for eachframe in range(self.imageCount): 
                    image = np.resize(self.video_list[eachframe], (self.dims[1], self.dims[0]))
                    tif.save(image, compress=0)
                    
    def Exit(self):
        self.dcam.dcamapi_uninit()
        
if (__name__ == "__main__"):

    import time
    import random
    import numpy as np
    import skimage.external.tifffile as skimtiff
    #
    # Initialization
    # Load dcamapi.dll version 19.12.641.5901
    cam = CamActuator()
    cam.initializeCamera()
    ImgSnapped = cam.SnapImage(exposure_time = 0.0015)
    cam.Exit()