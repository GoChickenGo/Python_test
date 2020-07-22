#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  4 14:38:04 2020

@author: Izak de Heer
"""

# Backend
from DMDManager.backend.dmd_manager import DMD_manager
import DMDManager.backend.polynomialTransformation
from DMDManager.backend.readRegistrationImages import touchingCoordinateFinder_Thread
from DMDManager.backend.polynomialTransformation import polynomialRegression
from DMDManager.backend.registrator import RegistrationThread
from HamamatsuCam.HamamatsuActuator import CamActuator

# Image processing
import matplotlib.pyplot as plt
from skimage.draw import line, polygon2mask, polygon_perimeter
from skimage.morphology import binary_dilation
from skimage.external import tifffile as skimtiff
from PIL import Image

# General libraries
import sys
import os
import numpy as np
import time
import datetime

from PyQt5.QtCore import pyqtSignal

class BACKEND_DMD_Widget():
    
    def __init__(self, *args, **kwargs):
        
        self.flag_dmd_connected = False
        self.flag_registrating = False
        self.flag_registered = False
        self.flag_mask_created = False
        self.flag_mask_in_memory = False
        self.flag_projecting = False        
        self.flag_camera_connected = False
        
        self.mask = {}
        self.mask_transformed = {}
        self.lasers = ['488', '532', '640']
        for laser in self.lasers:
            self.mask[laser] = np.zeros((1024, 768))
            self.mask_transformed[laser] = np.zeros((1024, 768))
            
        self.lasers_status = {}
        self.lasers_status['488'] = [False, 0]
        self.lasers_status['532'] = [False, 0]
        self.lasers_status['640'] = [False, 0]
        
    def snapImage_deprecated(self, saveToDir = None, fileName = None):
        """
        This function snaps an image using the functions written in 
        ui_camera_lab_5.py and camera_backend_lab_5.py by Douwe van der Heijden. 
        """
        
        if self.flag_camera_connected == False:
            self.ui_widget.normalOutputWritten("Camera not connected; connect camera to snap picture")
            return
        
        self.ui_widget.CameraUI.cam.snap()
        self.image = self.ui_widget.CameraUI.cam.image
        
        # Save image when checkbox is checked.
        if self.ui_widget.saveImageCheckBox.isChecked():
            if not saveToDir:
                saveToDir = "./DMDWidget/Pictures"
                
            if not fileName:
                timestr = time.strftime("%m-%d-%Y_%H;%M;%S")
                picture_name = saveToDir + "/picture_"+"{}".format(timestr)+".tiff"    
            else:
                picture_name = saveToDir + "/"+fileName+".tiff"
            skimtiff.imsave(picture_name, self.image, compress=0)
            
        self.ui_widget.update_image()
        
        return self.image

    def save_mask(self):
        if not (self.ui_widget.freehandSaveMaskButton.isChecked() and self.ui_widget.selectionMode == 'freehandMode' 
                or self.ui_widget.polygonSaveMaskButton.isChecked() and self.ui_widget.selectionMode == 'polygonMode'):
            return
        
        image = Image.fromarray((self.mask[self.ui_widget.drawing_laser]*255).astype(np.uint8))
        image = image.convert("L")
        date_time = datetime.datetime.now().timetuple()
        image_id = ''
        for i in range(5):    
            image_id += str(date_time[i])+'_'
        image_id += str(date_time[5])+'_'+self.ui_widget.drawing_laser
        image.save("DMDManager/Saved_masks/"+image_id+".png","PNG")    
    
    def createMaskSingleROI(self, vertices):
        if self.ui_widget.selectionMode == 'polygonMode':
            flag_fill_contour = self.ui_widget.polygonFillContourButton.isChecked()
        else:
            flag_fill_contour = self.ui_widget.freehandFillContourButton.isChecked()
        
        if flag_fill_contour:
            return polygon2mask((1024, 768), vertices)
        else:
            mask = np.zeros((1024,768))
            mask[polygon_perimeter(vertices[:,0], vertices[:,1], (1024,768))] = 1
            
            # The mask now created contains a one pixel thick perimeter. In order
            # to make the perimeter thicker, binary dilation is performed. 
            mask = binary_dilation(binary_dilation(mask))
            return mask
        
    def createMask(self):
        """
        This function organizes the mask creation, depending on the mask settings. 
        The function will preview the mask in the ROI window. 
        """
        
        if not self.flag_registered:
            self.ui_widget.normalOutputWritten("Warning: Camera and DMD not registered!")        
        
        if self.ui_widget.selectionMode == 'polygonMode':
            roi_list = self.ui_widget.polygon_roi_list[self.ui_widget.drawing_laser]
            width = 2048/self.ui_widget.polygonSelectionView.getView().viewRect().width()
            height = 2048/self.ui_widget.polygonSelectionView.getView().viewRect().height()
            flag_invert_mode = self.ui_widget.polygonInvertMaskButton.isChecked()
            ImageWidget = self.ui_widget.polygonSelectionView
        else:
            roi_list = self.ui_widget.freehandSelectionView.roilist[self.ui_widget.drawing_laser]
            width = 2048/self.ui_widget.freehandSelectionView.getView().viewRect().width()
            height = 2048/self.ui_widget.freehandSelectionView.getView().viewRect().height()
            flag_invert_mode = self.ui_widget.freehandInvertMaskButton.isChecked()
            ImageWidget = self.ui_widget.freehandSelectionView
            
        mask = np.zeros((1024, 768))
        if self.flag_registered:
            mask_transformed = np.zeros((1024, 768))
        
        for roi in roi_list:
            roi_handle_positions = roi.getSceneHandlePositions()
            
            for idx, pos in enumerate(roi_handle_positions):
                roi_handle_positions[idx] = ImageWidget.getView().mapToView(pos[1])
            
            num_vertices = len(roi_handle_positions)
            vertices = np.zeros([num_vertices,2])

            for idx, vertex in enumerate(roi_handle_positions):
                vertices[idx,:] = np.array([vertex.x(), vertex.y()])
            
            vertices[:,0] *= width
            vertices[:,1] *= height
            
            if self.flag_registered:
                laser = self.ui_widget.drawing_laser
                vertices_transformed = self.regthread.dict_transformators[laser].transform(vertices)

                mask_transformed += self.createMaskSingleROI(vertices_transformed)
                
            vertices[:,0] = vertices[:,0] / 2048*1024
            vertices[:,1] = vertices[:,1] / 2048*768
        
            mask += self.createMaskSingleROI(vertices)
        
        mask = (mask > 0)*1
        if self.flag_registered:
            mask_transformed = (mask_transformed > 0)*1
        
        if flag_invert_mode:
            mask = 1 - mask
            if self.flag_registered:
                mask_transformed= 1 - mask_transformed

        self.mask[self.ui_widget.drawing_laser] = np.transpose(mask)
        if self.flag_registered:
            self.mask_transformed[self.ui_widget.drawing_laser] = np.transpose(mask_transformed)
        
        self.save_mask()
        self.ui_widget.update_mask_preview()
        
        self.flag_mask_created = True
        self.ui_widget.update_buttons()
    
    def get_active_laser(self):
        """
        Retrieve which laser is active. If multiple lasers are active, use the most
        intens laser for registration. 
        """
        laser_max_intensity = '640'
        max_intensity = 0
        for laser, state in self.lasers_status.items():
            value = state[1]
            if value > max_intensity:
                max_intensity = value
                laser_max_intensity = laser
            
        return laser_max_intensity
    
    def loadMask(self):
        self.dmd.loadMask(self.mask_transformed[self.ui_widget.drawing_laser])
        self.flag_mask_in_memory = True
        self.ui_widget.update_buttons()
        
    def freeMemory(self):
        self.dmd.freeMemory()
        self.flag_mask_in_memory = False
        self.ui_widget.update_buttons()
        
    def startProjection(self):
        """
        Illuminate the ROI of the sample using the white field beam, modulated
        by the DMD. 
        """
        
        frame_rate = self.ui_widget.setFrameRateTextBox.text()
        if frame_rate == '' and self.dmd.seq_length > 1:
            self.ui_widget.normalOutputWritten("Please enter frame rate in microseconds")
            return 
        elif not frame_rate == '':
            frame_rate = int(frame_rate)
        else:
            frame_rate = None
            
        self.dmd.startProjection(frame_rate)
        
        self.flag_projecting = True
        self.ui_widget.update_buttons()
        
    def stopProjection(self):
        """
        Stop illuminating the ROI. Image stays in memory of DMD
        """
        
        self.dmd.stopProjection()
        self.flag_projecting = False
        self.ui_widget.update_buttons()
        
    def connectDMD(self):
        """
        Check whether there is an open DMD connection. If not, create one.
        """
        
        self.dmd = DMD_manager()
        self.dmd_resolutionx = self.dmd.resolutionx
        self.dmd_resolutiony = self.dmd.resolutiony
        
        self.ui_widget.normalOutputWritten('DMD connected')
        self.flag_dmd_connected = True
        self.ui_widget.update_buttons()
        
#        if self.flag_dmd_connected == False:
#            try:
#                self.dmd = DMD_manager()
#                self.dmd_resolutionx = self.dmd.resolutionx
#                self.dmd_resolutiony = self.dmd.resolutiony
#                self.flag_dmd_connected = True
#                
#                self.dmdConnectButton.setEnabled(False)
#                self.dmdDisconnectButton.setEnabled(True)
#                self.dmdRegistrationButton.setEnabled(True)
#        
#                self.normalOutputWritten('DMD connected')
#            except:
#                self.flag_dmd_connected = False
#                self.normalOutputWritten('Connection DMD failed')
            
    def disconnectDMD(self):
        """
        
        Check whether there is an open DMD connection. If so, close connection
        
        """
        
        if not self.flag_dmd_connected:
            return
            
        self.dmd_resolutionx = None
        self.dmd_resolutiony = None
        
        # Clear onboard memory and disconnect
        self.dmd.deallocDevide()
        
        self.dmd = None
        self.ui_widget.normalOutputWritten('DMD disconnected')
        
        self.flag_dmd_connected = False
        self.ui_widget.update_buttons()
    
    def registration(self):
        lasers_to_register = []
        if self.ui_widget.laser488.isChecked():
            lasers_to_register.append('488')
        if self.ui_widget.laser532.isChecked():
            lasers_to_register.append('532')
        if self.ui_widget.laser640.isChecked():
            lasers_to_register.append('640')
        
        if not lasers_to_register:
            self.ui_widget.normalOutputWritten('No lasers selected to be registered')
            return
        
        self.ui_widget.sig_start_registration.emit()        
        
        self.flag_registrating = True
        self.ui_widget.update_buttons()
        
        self.regthread = RegistrationThread(self, lasers_to_registrate)
        
        self.regthread.start()
        self.regthread.sig_finished_registration.connect(self.registration_finished)
        
    def registration_finished(self):
        self.dict_transformators = self.regthread.dict_transformators
            
        self.ui_widget.dmdRegistrationButton.setStyleSheet("background-color: light gray")
        self.ui_widget.normalOutputWritten("Registration finished succesfully")

        self.ui_widget.sig_finished_registration.emit()
        self.flag_registered = True
        self.flag_registrating = False
        self.flag_projecting = False
        self.ui_widget.update_buttons()
        
    def check_mask_format_valid(self, mask):
        if len(mask.shape) == 3:
            self.ui_widget.normalOutputWritten('Image is stack; make sure to load a binary image; for now max projection used')
            mask = np.max(mask, axis=2)
        
        if mask.shape[0] == 1024 and mask.shape[1] == 768:
            mask = mask.transpose()
            
        elif mask.shape[0] != 768 or mask.shape[1] != 1024:
            self.ui_widget.normalOutputWritten('Image has shape '+str(mask.shape[0])+'x'+str(mask.shape[1])+'; should be 768x1024')
            return False, None
        
        return True, mask
        
    def loadFile(self):
        """
        Load file from path and put image to mask display.
        """
        try:
            mask = plt.imread(self.loadFileName)
        except:
            self.ui_widget.normalOutputWritten("Invalid file path or file")
            return
        
        valid, valid_mask = self.check_mask_format_valid(mask)
        if not valid:
            return
        else:
            self.mask_transformed[self.ui_widget.drawing_laser] = valid_mask
        
        self.ui_widget.update_mask_preview()
        
        self.flag_mask_created = True
        self.ui_widget.update_buttons()
        
    def loadFolder(self):
        """
        Load files from folder using path and save frames in multidimensional array. 
        """
        
        # appears to be an error here, still to be examined.
        list_dir_raw = sorted(os.listdir(self.loadFolderName))
        
        list_dir = [file for file in list_dir_raw if file[-3:] == 'png']
        list_nr = len(list_dir)
        img = np.zeros([768, 1024, list_nr])
        for i in range(list_nr):
            single_mask = plt.imread(self.loadFolderName + '/' + list_dir[i])
            valid, valid_single_mask = self.check_mask_format_valid(single_mask)
            if not valid:
                return
            else:
                img[:,:,i] = valid_single_mask
        
        self.mask_transformed[self.ui_widget.drawing_laser] = img
        self.flag_mask_created = True
        self.ui_widget.update_buttons()