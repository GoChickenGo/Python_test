# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 10:30:41 2020

@author: Izak de Heer
"""
import sys
import json

import numpy as np
import time
import datetime
from PyQt5.QtCore import QThread, pyqtSignal
import matplotlib.pyplot as plt
import skimage.external.tifffile as skimtiff
import scipy.optimize
from CoordinatesManager.backend.readRegistrationImages import touchingCoordinateFinder
from CoordinatesManager.backend.polynomialTransformation import polynomialRegression
from CoordinatesManager import DMDActuator
from NIDAQ.DAQoperator import DAQmission

from HamamatsuCam.HamamatsuActuator import CamActuator
from SampleStageControl.Stagemovement_Thread import StagemovementRelativeThread, StagemovementAbsoluteThread

import matplotlib.pyplot as plt

class GalvoRegistrator:
    def test(self):
        pass

class DMDRegistator:
    def __init__(self, parent):
        self.DMD = DMDActuator.DMDActuator()
        self.cam = CamActuator()
        self.cam.initializeCamera()
        
    def registration(self, laser = '640', points = 6):
        x_coords = np.linspace(0, 1024, 5)[1:-1]
        y_coords = np.linspace(0, 768, 4)[1:-1]
        
        dmd_coordinates = np.vstack((x_coords, y_coords))
        
        camera_coordinates = np.zeros(dmd_coordinates.shape)
        
        cnt = 0
        for i in range(points):
            for j in range(y_coords.shape[0]):
                mask = create_registration_image(i,j)
                self.DMD.send_data_to_DMD(mask)
                self.DMD.start_projection()
                
                image = self.cam.SnapImage(0.4)
                camera_coordinates[cnt, :] = touchingCoordinateFinder(image, method = 'curvefit')
                cnt += 1
                
                self.DMD.stop_projection()
                self.DMD.free_memory()
        
        self.DMD.disconnect_DMD()
        transformation = findTransformationCurvefit(camera_coordinates, dmd_coordinates, kx = 3, ky = 2)
        return transformation
    
    def create_registration_image(x, y, sigma = 75):
        array = np.zeros((1024, 768))
        array[skd.draw.rectangle((x-sigma, y-sigma), (x,y))] = 255
        array[skd.draw.rectangle((x+sigma, y+sigma), (x,y))] = 255
        return array
        
class RegistrationThread(QThread):
    
    sig_finished_registration = pyqtSignal(dict)
    
    def __init__(self, parent, laser = None):
        QThread.__init__(self)
        self.flag_finished = [0, 0, 0]
        self.backend = parent
        self.dmd = self.backend.DMD
        
        if not isinstance(laser, list):    
            self.laser_list = [laser]
        else:
            self.laser_list = laser
            
        self.dict_transformators = {}
        
        self.dict_transformations = {}
        self.dtype_ref_co = np.dtype([('camera', int, (3,2)), ('dmd', int, (3,2)), ('galvos', int, (3,2)), ('stage', int, (3,2))])
        self.reference_coordinates = {}
    
    def set_device_to_register(self, device_1, device_2 = 'camera'):
        self.device_1 = device_1
        self.device_2 = device_2
    
    def run(self):
        #Make sure registration can only start when camera is connected
        try:
            self.cam = CamActuator()
            self.cam.initializeCamera()
        except:
            print(sys.exc_info())
            self.backend.ui_widget.normalOutputWritten('Unable to connect Hamamatsu camera')
            return        
        
        self.cam.setROI(0, 0, 2048, 2048)
        
        if self.device_1 == 'galvos':
            reference_coordinates = self.gather_reference_coordinates_galvos()
            self.dict_transformations['camera-galvos'] = findTransform(reference_coordinates[0], \
                                                                       reference_coordinates[1])
        elif self.device_1 == 'dmd':
            reference_coordinates = self.gather_reference_coordinates_dmd()
            for laser in self.laser_list:
                self.dict_transformations['camera-dmd-'+laser] = findTransform(reference_coordinates[0], \
                                                                               reference_coordinates[1])
                    
        elif self.device_1 == 'stage':
            reference_coordinates = self.gather_reference_coordinates_stage()
            self.dict_transformations['camera-stage'] = findTransform(reference_coordinates[0], \
                                                                      reference_coordinates[1])
            
        self.cam.Exit()
        
        ## Save transformation to file
        with open('CoordinatesManager/Registration/transformation.txt', 'w') as json_file:
            
            dict_transformations_list_format = {}
            for key, value in self.dict_transformations.items():
                dict_transformations_list_format[key] = value.tolist()
            
            json.dump(dict_transformations_list_format, json_file)
            
        self.sig_finished_registration.emit(self.dict_transformations)
    
    def gather_reference_coordinates_stage(self):
        image = np.zeros((2048, 2048, 3))        
        stage_coordinates = np.array([[-2800, 100], [-2500, 400], [-1900, -200]])
        
        self.backend.loadMask(mask = np.ones((768,1024)))
        self.backend.startProjection()
        
        for idx, pos in enumerate(stage_coordinates):
            
            stage_movement_thread = StagemovementAbsoluteThread(pos[0], pos[1])
            stage_movement_thread.start()
            time.sleep(0.5)
            stage_movement_thread.quit()
            stage_movement_thread.wait()
            
            image[:,:,idx] = self.cam.SnapImage(0.04)
        
        camera_coordinates = find_subimage_location(image, save=True)
        
        self.backend.stopProjection()
        self.backend.freeMemory()
        
        return np.array([camera_coordinates, stage_coordinates])
            
    def gather_reference_coordinates_galvos(self):
        galvothread = DAQmission()
        readinchan = []
        
        camera_coordinates = np.zeros((3,2))
        galvo_coordinates = np.array([ [0, 3], [3, -3], [-3, -3] ])
        
        for i in range(3):
            pos_x = galvo_coordinates[i,0]
            pos_y = galvo_coordinates[i,1]
            
            galvothread.sendSingleAnalog('galvosx', pos_x)
            galvothread.sendSingleAnalog('galvosy', pos_y)
            
            image = self.cam.SnapImage(0.04)
            
            camera_coordinates[i,:] = gaussian_fitting(image)
        
        del galvothread
        return np.array([camera_coordinates, galvo_coordinates])
        
    def gather_reference_coordinates_dmd(self):
        galvo_coordinates = np.zeros((3,2))
        
        for laser in self.laser_list:
            self.flag_finished = [0, 0, 0]
            
            self.backend.ui_widget.sig_control_laser.emit(laser, 5)
            
            self.registration_single_laser(laser)
            
            self.backend.ui_widget.sig_control_laser.emit(laser, 0)
            
        return np.array([self.camera_coordinates, self.dmd_coordinates, galvo_coordinates])
        
    def registration_single_laser(self,laser):        
        date_time = datetime.datetime.now().timetuple()
        image_id = ''
        for i in range(5):    
            image_id += str(date_time[i])+'_'
        image_id += str(date_time[5]) + '_l'+laser

        self.camera_coordinates = np.zeros((3,2))
        self.touchingCoordinateFinder = []
            
        for i in range(3):
            self.touchingCoordinateFinder.append(touchingCoordinateFinder_Thread(i, method='curvefit'))    
            self.touchingCoordinateFinder[i].sig_finished_coordinatefinder.connect(self.touchingCoordinateFinder_finished)

        for i in range(3):
            self.loadFileName = './CoordinatesManager/Registration_Images/TouchingSquares/registration_mask_'+str(i)+'.png'
            
            # Transpose because mask in file is rotated by 90 degrees.
            mask = np.transpose(plt.imread(self.loadFileName))
            
            self.backend.loadMask(mask)
            self.backend.startProjection()
            
            time.sleep(0.5)
            self.image = self.cam.SnapImage(0.0015)
            time.sleep(0.5)
            
            self.backend.stopProjection()
            self.backend.freeMemory()
            
            # Start touchingCoordinateFinder thread
            self.touchingCoordinateFinder[i].put_image(self.image)
            self.touchingCoordinateFinder[i].start()
            
        self.dmd_coordinates = self.read_dmd_coordinates_from_file()
        
        # Block till all touchingCoordinateFinder_Thread threads are finished
        while np.prod(self.flag_finished) == 0:
            time.sleep(0.1)
        
        
    def read_dmd_coordinates_from_file(self):
        file = open('./CoordinatesManager/Registration_Images/TouchingSquares/positions.txt', 'r')
        
        self.dmd_coordinates = []
        for ln in file.readlines():
            self.dmd_coordinates.append(ln.strip().split(','))
        file.close()
        
        return np.asarray(self.dmd_coordinates).astype(int)
        
    def touchingCoordinateFinder_finished(self, sig):
        self.camera_coordinates[sig,:] = np.flip(self.touchingCoordinateFinder[sig].coordinates)
        self.flag_finished[sig] = 1
        
def gaussian_fitting(image):
    p0 = np.ones(5)
    
    p0_x = np.where(image == image.max())[0]
    p0_y = np.where(image == image.max())[1]
    
    print('Maximal value positions in registration image')
    print(p0_x, p0_y)
    
    p0[0] = np.mean(p0_x) 
    p0[1] = np.mean(p0_y)
    
    x = np.repeat(np.arange(image.shape[0]), image.shape[0])
    
    popt, pcov = scipy.optimize.curve_fit(gaussian, x, image.ravel(), p0)    
    
    coordinates = np.array([ popt[0], popt[1] ]).astype(int)
    return coordinates
    
def gaussian(x, y, x0, y0, a, sigma):
    """
    Function that defines the function to be fitted to the data. This is a 
    normal 2D Gaussian.
    """
    return a*np.exp(-((x-x0)**2+(y-y0)**2)/(2*sigma**2))
    
def createRegressionMatrix(q, order):
    size = 2+4*order
    hsize = 1+2*order ## Define half size, just for convenience

    if len(q.shape) != 1 and order == 0:
        num_input_points = q.shape[0]
        print("Number of input points is "+str(num_input_points))
        print("For zeroth order input one point only")
        Q = None
        return
    print(q.shape)
    if q.shape[0] != hsize and order != 0:
        num_input_points = q.shape[0]
        print("Number of input points is "+str(num_input_points))
        print("For N'th order input 1+2N points")
        Q = None
        return
    
    col1 = np.hstack((np.ones(hsize), np.zeros(hsize)))
    col2 = np.flip(col1)
    
    if order == 0:
        return np.vstack((col1, col2)).transpose()
    else:
        col3 = np.hstack((q[:,0], np.zeros(hsize)))
        col4 = np.hstack((q[:,1], np.zeros(hsize)))
        col5 = np.hstack((np.zeros(hsize), q[:,0]))
        col6 = np.hstack((np.zeros(hsize), q[:,1]))
        
        Qx = np.vstack((col1, col2, col3, col4))
        Qy = np.vstack((col5, col6))

    for i in range(2,order+1):
        Qx = np.vstack((Qx, col3**i, col4**i))
        Qy = np.vstack((Qy, col5**i, col6**i))
        
    return np.vstack((Qx, Qy)).transpose()

def findTransform(q, p, order = 1):
    """
    
    This function performs multilinear regression between two sets of points 
    Q and P in different coordinate frames. The function returns the transformation
    matrix T and the translation vector t according to P = t + sum_{n=1}^N (T Q)^n. 
    
    """
    p = np.squeeze(p)
    q = np.squeeze(q)
        
    Q = createRegressionMatrix(q, order)
    if Q is None:
        return None, None
    
    P = np.reshape(p, (-1, 1), order='F')
    
    # Standard regression formula
    try:
        A = np.dot(np.dot(np.linalg.inv(np.dot(Q.transpose(), Q)),Q.transpose()), P)
    except np.linalg.LinAlgError:
        print("Matrix is singular. Try different set of input points. " \
              + "Points should not be colinear")
        return

    t = A[0:2]
    print("Translation vector =")
    print(np.around(t, 5))
    print()
    
    # Because of the order in the A vector, the a_n, b_n, c_n and d_n are not 
    # in consequetive order in A. Therefore, a moveaxis() is performed.
    Areduced = A[2:]
    num = int(Areduced.shape[0]/2)
    tmp = np.hstack((Areduced[0:num], Areduced[num:]))
    
    T = np.zeros((int(tmp.shape[0]/2), 2, 2))
    for i in range(T.shape[0]):
        T[i, :, :] = tmp[2*i:2*i+2, 0:2]
    
    
    # self.T = np.moveaxis(np.reshape(self.A[2:], (2,2,-1)), 0, -2)

    for i in range(order):
        print(str(i+1) + "'th order transformation matrix =")
        print(np.around(T[i,:,:], 5))
        print()
    
    return A