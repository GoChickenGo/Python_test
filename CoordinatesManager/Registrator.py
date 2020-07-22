# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 10:30:41 2020

@author: Izak de Heer
"""
import sys
import json
import os

import numpy as np
import time
import datetime
from PyQt5.QtCore import QThread, pyqtSignal
import matplotlib.pyplot as plt
import skimage.external.tifffile as skimtiff
import scipy.optimize
import skimage.draw
from CoordinatesManager.backend import readRegistrationImages
from CoordinatesManager.backend.polynomialTransformation import polynomialRegression
from CoordinatesManager import CoordinateTransformations
from CoordinatesManager import DMDActuator
from NIDAQ.DAQoperator import DAQmission

from HamamatsuCam.HamamatsuActuator import CamActuator
from SampleStageControl.Stagemovement_Thread import StagemovementRelativeThread, StagemovementAbsoluteThread

import matplotlib.pyplot as plt

class GalvoRegistrator:
    def __init__(self, *args, **kwargs):
        self.cam = CamActuator()
        self.cam.initializeCamera()
        
    def registration(self, grid_points_x = 3, grid_points_y = 3):
        galvothread = DAQmission()
        readinchan = []
        
        x_coords = np.linspace(-10, 10, grid_points_x+2)[1:-1]
        y_coords = np.linspace(-10, 10, grid_points_y+2)[1:-1]
        
        xy_mesh = np.reshape(np.meshgrid(x_coords, y_coords), (2, -1), order='F').transpose()
        
        galvo_coordinates = xy_mesh
        camera_coordinates = np.zeros((galvo_coordinates.shape))
        
        for i in range(galvo_coordinates.shape[0]):
            
            galvothread.sendSingleAnalog('galvosx', galvo_coordinates[i,0])
            galvothread.sendSingleAnalog('galvosy', galvo_coordinates[i,1])
            time.sleep(1)
            
            image = self.cam.SnapImage(0.06)
            plt.imsave(os.getcwd()+'/CoordinatesManager/Registration_Images/2P/image_'+str(i)+'.png', image)
            
            camera_coordinates[i,:] = readRegistrationImages.gaussian_fitting(image)
            
        print('Galvo Coordinate')
        print(galvo_coordinates)
        print('Camera coordinates')
        print(camera_coordinates)
        del galvothread
        self.cam.Exit()
        
        transformation = CoordinateTransformations.polynomial2DFit(camera_coordinates, galvo_coordinates, order=1)
        
        print('Transformation found for x:')
        print(transformation[:,:,0])
        print('Transformation found for y:')
        print(transformation[:,:,1])
        return transformation

class DMDRegistator:
    def __init__(self, DMD, *args, **kwargs):
        self.DMD = DMD
        self.cam = CamActuator()
        self.cam.initializeCamera()
        
    def registration(self, laser = '640', grid_points_x = 2, grid_points_y = 3, registration_pattern = 'circles'):
        x_coords = np.linspace(0, 768, grid_points_x+2)[1:-1]
        y_coords = np.linspace(0, 1024, grid_points_y+2)[1:-1]
        
        x_mesh, y_mesh = np.meshgrid(x_coords, y_coords)
        
        x_coords = np.ravel(x_mesh)
        y_coords = np.ravel(y_mesh)
        
        dmd_coordinates = np.stack((x_coords, y_coords), axis=1)
        
        camera_coordinates = np.zeros(dmd_coordinates.shape)
        
        for i in range(dmd_coordinates.shape[0]):
            x = int(dmd_coordinates[i,0])
            y = int(dmd_coordinates[i,1])
            
            if registration_pattern == 'squares':    
                mask = create_registration_image_touching_squares(x,y)
            else:
                mask = create_registration_image_circle(x,y)
                
            self.DMD.send_data_to_DMD(mask)
            self.DMD.start_projection()
            
            image = self.cam.SnapImage(0.04)
            plt.imsave(os.getcwd()+'/CoordinatesManager/Registration_Images/TouchingSquares/image_'+str(i)+'.png', image)
            camera_coordinates[i, :] = readRegistrationImages.touchingCoordinateFinder(image, method = 'curvefit')
            
            self.DMD.stop_projection()
        
        print('DMD coordinates:')
        print(dmd_coordinates)
        print('Found camera coordinates:')
        print(camera_coordinates)
        
        self.DMD.free_memory()
        self.cam.Exit()
        
        transformation = CoordinateTransformations.polynomial2DFit(camera_coordinates, dmd_coordinates, order=1)
        print('Transformation found for x:')
        print(transformation[:,:,0])
        print('Transformation found for y:')
        print(transformation[:,:,1])
        return transformation
    
    def create_registration_image_touching_squares(x, y, sigma = 75):
        array = np.zeros((768, 1024))
        array[skimage.draw.rectangle((x-sigma, y-sigma), (x,y))] = 255
        array[skimage.draw.rectangle((x+sigma, y+sigma), (x,y))] = 255
        return array
    
    def create_registration_image_circle(x, y, sigma = 75):
        array = np.zeros((768, 1024))
        array[skimage.draw.circle(x, y, sigma)] = 255
        return array
        
# class RegistrationThread(QThread):
    
#     sig_finished_registration = pyqtSignal(dict)
    
#     def __init__(self, parent, laser = None):
#         QThread.__init__(self)
#         self.flag_finished = [0, 0, 0]
#         self.backend = parent
#         self.dmd = self.backend.DMD
        
#         if not isinstance(laser, list):    
#             self.laser_list = [laser]
#         else:
#             self.laser_list = laser
            
#         self.dict_transformators = {}
        
#         self.dict_transformations = {}
#         self.dtype_ref_co = np.dtype([('camera', int, (3,2)), ('dmd', int, (3,2)), ('galvos', int, (3,2)), ('stage', int, (3,2))])
#         self.reference_coordinates = {}
    
#     def set_device_to_register(self, device_1, device_2 = 'camera'):
#         self.device_1 = device_1
#         self.device_2 = device_2
    
#     def run(self):
#         #Make sure registration can only start when camera is connected
#         try:
#             self.cam = CamActuator()
#             self.cam.initializeCamera()
#         except:
#             print(sys.exc_info())
#             self.backend.ui_widget.normalOutputWritten('Unable to connect Hamamatsu camera')
#             return        
        
#         self.cam.setROI(0, 0, 2048, 2048)
        
#         if self.device_1 == 'galvos':
#             reference_coordinates = self.gather_reference_coordinates_galvos()
#             self.dict_transformations['camera-galvos'] = findTransform(reference_coordinates[0], \
#                                                                        reference_coordinates[1])
#         elif self.device_1 == 'dmd':
#             reference_coordinates = self.gather_reference_coordinates_dmd()
#             for laser in self.laser_list:
#                 self.dict_transformations['camera-dmd-'+laser] = findTransform(reference_coordinates[0], \
#                                                                                reference_coordinates[1])
                    
#         elif self.device_1 == 'stage':
#             reference_coordinates = self.gather_reference_coordinates_stage()
#             self.dict_transformations['camera-stage'] = findTransform(reference_coordinates[0], \
#                                                                       reference_coordinates[1])
            
#         self.cam.Exit()
        
#         ## Save transformation to file
#         with open('CoordinatesManager/Registration/transformation.txt', 'w') as json_file:
            
#             dict_transformations_list_format = {}
#             for key, value in self.dict_transformations.items():
#                 dict_transformations_list_format[key] = value.tolist()
            
#             json.dump(dict_transformations_list_format, json_file)
            
#         self.sig_finished_registration.emit(self.dict_transformations)
    
#     def gather_reference_coordinates_stage(self):
#         image = np.zeros((2048, 2048, 3))        
#         stage_coordinates = np.array([[-2800, 100], [-2500, 400], [-1900, -200]])
        
#         self.backend.loadMask(mask = np.ones((768,1024)))
#         self.backend.startProjection()
        
#         for idx, pos in enumerate(stage_coordinates):
            
#             stage_movement_thread = StagemovementAbsoluteThread(pos[0], pos[1])
#             stage_movement_thread.start()
#             time.sleep(0.5)
#             stage_movement_thread.quit()
#             stage_movement_thread.wait()
            
#             image[:,:,idx] = self.cam.SnapImage(0.04)
        
#         camera_coordinates = find_subimage_location(image, save=True)
        
#         self.backend.stopProjection()
#         self.backend.freeMemory()
        
#         return np.array([camera_coordinates, stage_coordinates])
            
#     def gather_reference_coordinates_galvos(self):
#         galvothread = DAQmission()
#         readinchan = []
        
#         camera_coordinates = np.zeros((3,2))
#         galvo_coordinates = np.array([ [0, 3], [3, -3], [-3, -3] ])
        
#         for i in range(3):
#             pos_x = galvo_coordinates[i,0]
#             pos_y = galvo_coordinates[i,1]
            
#             galvothread.sendSingleAnalog('galvosx', pos_x)
#             galvothread.sendSingleAnalog('galvosy', pos_y)
            
#             image = self.cam.SnapImage(0.04)
            
#             camera_coordinates[i,:] = gaussian_fitting(image)
        
#         del galvothread
#         return np.array([camera_coordinates, galvo_coordinates])
        
#     def gather_reference_coordinates_dmd(self):
#         galvo_coordinates = np.zeros((3,2))
        
#         for laser in self.laser_list:
#             self.flag_finished = [0, 0, 0]
            
#             self.backend.ui_widget.sig_control_laser.emit(laser, 5)
            
#             self.registration_single_laser(laser)
            
#             self.backend.ui_widget.sig_control_laser.emit(laser, 0)
            
#         return np.array([self.camera_coordinates, self.dmd_coordinates, galvo_coordinates])
        
#     def registration_single_laser(self,laser):        
#         date_time = datetime.datetime.now().timetuple()
#         image_id = ''
#         for i in range(5):    
#             image_id += str(date_time[i])+'_'
#         image_id += str(date_time[5]) + '_l'+laser

#         self.camera_coordinates = np.zeros((3,2))
#         self.touchingCoordinateFinder = []
            
#         for i in range(3):
#             self.touchingCoordinateFinder.append(touchingCoordinateFinder_Thread(i, method='curvefit'))    
#             self.touchingCoordinateFinder[i].sig_finished_coordinatefinder.connect(self.touchingCoordinateFinder_finished)

#         for i in range(3):
#             self.loadFileName = './CoordinatesManager/Registration_Images/TouchingSquares/registration_mask_'+str(i)+'.png'
            
#             # Transpose because mask in file is rotated by 90 degrees.
#             mask = np.transpose(plt.imread(self.loadFileName))
            
#             self.backend.loadMask(mask)
#             self.backend.startProjection()
            
#             time.sleep(0.5)
#             self.image = self.cam.SnapImage(0.0015)
#             time.sleep(0.5)
            
#             self.backend.stopProjection()
#             self.backend.freeMemory()
            
#             # Start touchingCoordinateFinder thread
#             self.touchingCoordinateFinder[i].put_image(self.image)
#             self.touchingCoordinateFinder[i].start()
            
#         self.dmd_coordinates = self.read_dmd_coordinates_from_file()
        
#         # Block till all touchingCoordinateFinder_Thread threads are finished
#         while np.prod(self.flag_finished) == 0:
#             time.sleep(0.1)
        
        
#     def read_dmd_coordinates_from_file(self):
#         file = open('./CoordinatesManager/Registration_Images/TouchingSquares/positions.txt', 'r')
        
#         self.dmd_coordinates = []
#         for ln in file.readlines():
#             self.dmd_coordinates.append(ln.strip().split(','))
#         file.close()
        
#         return np.asarray(self.dmd_coordinates).astype(int)
        
#     def touchingCoordinateFinder_finished(self, sig):
#         self.camera_coordinates[sig,:] = np.flip(self.touchingCoordinateFinder[sig].coordinates)
#         self.flag_finished[sig] = 1
        
if __name__ == "__main__":
    pass    

    
    
    
    