# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 13:34:56 2020

@author: xinmeng
"""
from __future__ import division
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPoint, QRect, QObject
from PyQt5.QtGui import QColor, QPen, QPixmap, QIcon, QTextCursor, QFont

from PyQt5.QtWidgets import (QWidget, QButtonGroup, QLabel, QSlider, QSpinBox, QDoubleSpinBox, QGridLayout, QPushButton, QGroupBox, 
                             QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox, QTabWidget, QCheckBox, QRadioButton, 
                             QFileDialog, QProgressBar, QTextEdit)

import pyqtgraph as pg
from IPython import get_ipython
import sys
sys.path.append('../')
import numpy as np
import csv
from NIDAQ.code_5nov import generate_AO
from GalvoWidget.pmt_thread import pmtimagingTest, pmtimagingTest_contour
from SampleStageControl.Stagemovement_Thread import StagemovementRelativeThread
from ThorlabsFilterSlider.Filtermovement_Thread import FiltermovementThread
from NIDAQ.constants import MeasurementConstants
from Oldversions.generalDaqer import execute_constant_vpatch
import NIDAQ.wavegenerator
from Oldversions.generalDaqer import execute_analog_readin_optional_digital, execute_digital
from NIDAQ.generalDaqerThread import (execute_analog_readin_optional_digital_thread, execute_tread_singlesample_analog,
                                execute_tread_singlesample_digital, execute_analog_and_readin_digital_optional_camtrig_thread, DaqProgressBar)
from PIL import Image
from NIDAQ.adfunctiongenerator import (generate_AO_for640, generate_AO_for488, generate_DO_forcameratrigger, generate_DO_for640blanking,
                                 generate_AO_for532, generate_AO_forpatch, generate_DO_forblankingall, generate_DO_for532blanking,
                                 generate_DO_for488blanking, generate_DO_forPerfusion, generate_DO_for2Pshutter, generate_ramp)
from pyqtgraph import PlotDataItem, TextItem
from ImageAnalysis.matlabAnalysis import readbinaryfile, extractV
import os
import scipy.signal as sg
from datetime import datetime
from skimage.io import imread
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from NIDAQ.constants import HardwareConstants
import StylishQT


class PMTWidgetUI(QWidget):
    
#    waveforms_generated = pyqtSignal(object, object, list, int)
    SignalForContourScanning = pyqtSignal(int, int, int, np.ndarray, np.ndarray)
    MessageBack = pyqtSignal(str)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
#        os.chdir('./')# Set directory to current folder.
        self.setFont(QFont("Arial"))
        
        self.setMinimumSize(1200,850)
        self.setWindowTitle("PMTWidget")
        self.layout = QGridLayout(self)
        #------------------------Initiating class-------------------
        self.pmtTest = pmtimagingTest()
        self.pmtTest_contour = pmtimagingTest_contour()
        
        self.savedirectory = r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\pmt_image_default_dump'
        self.prefixtextboxtext = '_fromGalvoWidget'

        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------GUI for PMT tab------------------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------  
        #**************************************************************************************************************************************        
        pmtimageContainer = QGroupBox("PMT image")
        self.pmtimageLayout = QGridLayout()
        
        self.pmtvideoWidget = pg.ImageView()
        self.pmtvideoWidget.ui.roiBtn.hide()
        self.pmtvideoWidget.ui.menuBtn.hide()  
        self.pmtvideoWidget.resize(400,400)
        self.pmtimageLayout.addWidget(self.pmtvideoWidget, 0, 0)
        
        pmtroiContainer = QGroupBox("PMT ROI")
        self.pmtimageroiLayout = QGridLayout()
        
        self.pmt_roiwidget = pg.GraphicsLayoutWidget()
        self.pmt_roiwidget.resize(150,150)
        self.pmt_roiwidget.addLabel('ROI', row=0, col=0) 
        # create ROI
        self.vb_2 = self.pmt_roiwidget.addViewBox(row=1, col=0, lockAspect=True, colspan=1)
        self.vb_2.name = 'ROI'
        
        self.pmtimgroi = pg.ImageItem()
        self.vb_2.addItem(self.pmtimgroi)        
        #self.roi = pg.RectROI([20, 20], [20, 20], pen=(0,9))
        #r1 = QRectF(0, 0, 895, 500)
        ROIpen = QPen()  # creates a default pen
        ROIpen.setStyle(Qt.DashDotLine)
        ROIpen.setWidth(0.5)
        ROIpen.setBrush(QColor(0,161,255))
        self.roi = pg.PolyLineROI([[0,0], [80,0], [80,80], [0,80]], closed=True, pen=ROIpen)#, maxBounds=r1
        #self.roi.addScaleHandle([1,0], [1, 0])
        self.roi.sigHoverEvent.connect(lambda: self.show_handle_num()) # update handle numbers
        
        self.pmtvb = self.pmtvideoWidget.getView()
        self.pmtimageitem = self.pmtvideoWidget.getImageItem()
        self.pmtvb.addItem(self.roi)# add ROIs to main image
        
        self.pmtimageroiLayout.addWidget(self.pmt_roiwidget, 0, 0)
        
        pmtimageContainer.setMinimumWidth(850)
        pmtroiContainer.setMaximumHeight(380)
#        pmtroiContainer.setMaximumWidth(300)
        
        pmtimageContainer.setLayout(self.pmtimageLayout)
        pmtroiContainer.setLayout(self.pmtimageroiLayout)
        #----------------------------Contour-----------------------------------        
        pmtContourContainer = QGroupBox("Contour selection")
        pmtContourContainer.setFixedWidth(280)
        self.pmtContourLayout = QGridLayout()
        #contour_Description = QLabel("Handle number updates when parking mouse cursor upon ROI. Points in contour are divided evenly between handles.")
        #contour_Description.setStyleSheet('color: blue')        
        #self.pmtContourLayout.addWidget(contour_Description,0,0)
       
        self.pmt_handlenum_Label = QLabel("Handle number: ")
        self.pmtContourLayout.addWidget(self.pmt_handlenum_Label,1,0)
        
        self.contour_strategy = QComboBox()
        self.contour_strategy.addItems(['Manual','Uniform'])
        self.pmtContourLayout.addWidget(self.contour_strategy, 1, 1)        
        
        self.pointsinContour = QSpinBox(self)
        self.pointsinContour.setMinimum(1)
        self.pointsinContour.setMaximum(1000)
        self.pointsinContour.setValue(100)
        self.pointsinContour.setSingleStep(100)        
        self.pmtContourLayout.addWidget(self.pointsinContour, 2, 1)
        self.pmtContourLayout.addWidget(QLabel("Points in contour:"), 2, 0)

        self.contour_samprate = QSpinBox(self)
        self.contour_samprate.setMinimum(0)
        self.contour_samprate.setMaximum(1000000)
        self.contour_samprate.setValue(50000)
        self.contour_samprate.setSingleStep(50000)        
        self.pmtContourLayout.addWidget(self.contour_samprate, 3, 1)        
        self.pmtContourLayout.addWidget(QLabel("Sampling rate:"), 3, 0)
        
        self.generate_contour_sacn = StylishQT.generateButton()
        self.pmtContourLayout.addWidget(self.generate_contour_sacn, 4, 1)
        self.generate_contour_sacn.clicked.connect(lambda: self.generate_contour())
        
        self.do_contour_sacn = StylishQT.runButton("Contour")
        self.do_contour_sacn.setFixedHeight(32)
        self.pmtContourLayout.addWidget(self.do_contour_sacn, 5, 0)
        self.do_contour_sacn.clicked.connect(lambda:self.buttonenabled('contourscan', 'start'))
        self.do_contour_sacn.clicked.connect(lambda: self.measure_pmt_contourscan())
        
        self.stopButton_contour = StylishQT.stop_deleteButton()
        self.stopButton_contour.setFixedHeight(32)
        self.stopButton_contour.clicked.connect(lambda:self.buttonenabled('contourscan', 'stop'))
        self.stopButton_contour.clicked.connect(lambda: self.stopMeasurement_pmt_contour())
        self.stopButton_contour.setEnabled(False)
        self.pmtContourLayout.addWidget(self.stopButton_contour, 5, 1)
        
        pmtContourContainer.setLayout(self.pmtContourLayout)
        #----------------------------Control-----------------------------------
        controlContainer = QGroupBox("Galvo Scanning Panel")
        controlContainer.setFixedWidth(280)
        self.controlLayout = QGridLayout()
        
        self.pmt_fps_Label = QLabel("Per frame: ")
        self.controlLayout.addWidget(self.pmt_fps_Label, 5, 0)
    
        self.saveButton_pmt = StylishQT.saveButton()
        self.saveButton_pmt.clicked.connect(lambda: self.saveimage_pmt())
        self.controlLayout.addWidget(self.saveButton_pmt, 5, 1)
    
        self.startButton_pmt = StylishQT.runButton("")
        self.startButton_pmt.setFixedHeight(32)
        self.startButton_pmt.setCheckable(True)
        self.startButton_pmt.clicked.connect(lambda:self.buttonenabled('rasterscan', 'start'))
        self.startButton_pmt.clicked.connect(lambda: self.measure_pmt())

        self.controlLayout.addWidget(self.startButton_pmt, 6, 0)
        
        self.stopButton = StylishQT.stop_deleteButton()
        self.stopButton.setFixedHeight(32)
        self.stopButton.clicked.connect(lambda:self.buttonenabled('rasterscan', 'stop'))
        self.stopButton.clicked.connect(lambda: self.stopMeasurement_pmt())
        self.stopButton.setEnabled(False)
        self.controlLayout.addWidget(self.stopButton, 6, 1)
        
        #-----------------------------------Galvo scanning------------------------------------------------------------------------
        self.textboxAA_pmt = QSpinBox(self)
        self.textboxAA_pmt.setMinimum(0)
        self.textboxAA_pmt.setMaximum(1000000)
        self.textboxAA_pmt.setValue(500000)
        self.textboxAA_pmt.setSingleStep(100000)        
        self.controlLayout.addWidget(self.textboxAA_pmt, 1, 1)        
        self.controlLayout.addWidget(QLabel("Sampling rate:"), 1, 0)
        
        #self.controlLayout.addWidget(QLabel("Galvo raster scanning : "), 1, 0)
        self.textbox1B_pmt = QSpinBox(self)
        self.textbox1B_pmt.setMinimum(-10)
        self.textbox1B_pmt.setMaximum(10)
        self.textbox1B_pmt.setValue(3)
        self.textbox1B_pmt.setSingleStep(1)        
        self.controlLayout.addWidget(self.textbox1B_pmt, 2, 1)
        self.controlLayout.addWidget(QLabel("Volt range:"), 2, 0)
        
        self.Scanning_pixel_num_combobox = QSpinBox(self)
        self.Scanning_pixel_num_combobox.setMinimum(0)
        self.Scanning_pixel_num_combobox.setMaximum(1000)
        self.Scanning_pixel_num_combobox.setValue(500)
        self.Scanning_pixel_num_combobox.setSingleStep(244)        
        self.controlLayout.addWidget(self.Scanning_pixel_num_combobox, 3, 1)
        self.controlLayout.addWidget(QLabel("Pixel number:"), 3, 0)

        self.textbox1H_pmt = QSpinBox(self)
        self.textbox1H_pmt.setMinimum(1)
        self.textbox1H_pmt.setMaximum(20)
        self.textbox1H_pmt.setValue(1)
        self.textbox1H_pmt.setSingleStep(1)
        self.controlLayout.addWidget(self.textbox1H_pmt, 4, 1)
        self.controlLayout.addWidget(QLabel("average over:"), 4, 0)
        
        controlContainer.setLayout(self.controlLayout)
        
        #---------------------------Set tab1 layout---------------------------
#        pmtmaster = QGridLayout()
        self.layout.addWidget(pmtimageContainer, 0,0,3,1)
        self.layout.addWidget(pmtroiContainer,1,1)       
        self.layout.addWidget(pmtContourContainer,2,1)
        self.layout.addWidget(controlContainer,0,1)
        
#        self.layout.setLayout(pmtmaster)
        
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #--------------------------------------------------------------------------------------------------------------------------------------
        #------------------------------------------------------Functions for TAB 'PMT'---------------------------------------------------------
        #-------------------------------------------------------------------------------------------------------------------------------------- 
        #**************************************************************************************************************************************
    def buttonenabled(self, button, switch):
        
        if button == 'rasterscan':
            if switch == 'start':

                self.startButton_pmt.setEnabled(False)
                self.stopButton.setEnabled(True)
                    
            elif switch == 'stop':
                self.startButton_pmt.setEnabled(True)
                self.stopButton.setEnabled(False)
                    
        elif button == 'contourscan':
            if switch == 'start': #disable start button and enable stop button
                self.do_contour_sacn.setEnabled(False)
                self.stopButton_contour.setEnabled(True)
            elif switch == 'stop':
                self.do_contour_sacn.setEnabled(True)
                self.stopButton_contour.setEnabled(False)
                
                
                
    def measure_pmt(self):
        self.Daq_sample_rate_pmt = int(self.textboxAA_pmt.value())
        
        # Voltage settings, by default it's equal range square.
        self.Value_voltXMax = self.textbox1B_pmt.value()
        self.Value_voltXMin = self.Value_voltXMax*-1
        Value_voltYMin = self.Value_voltXMin
        Value_voltYMax = self.Value_voltXMax
        
        self.Value_xPixels = int(self.Scanning_pixel_num_combobox.value())
        Value_yPixels = self.Value_xPixels
        self.averagenum =int(self.textbox1H_pmt.value())
        
        Totalscansamples = self.pmtTest.setWave(self.Daq_sample_rate_pmt, self.Value_voltXMin, self.Value_voltXMax, Value_voltYMin, Value_voltYMax, self.Value_xPixels, Value_yPixels, self.averagenum)
        time_per_frame_pmt = Totalscansamples/self.Daq_sample_rate_pmt
        
        ScanArrayXnum=int((Totalscansamples/self.averagenum)/Value_yPixels)
        
        #r1 = QRectF(500, 500, ScanArrayXnum, int(Value_yPixels))
        #self.pmtimageitem.setRect(r1)
        
        self.pmtTest.pmtimagingThread.measurement.connect(self.update_pmt_Graphs) #Connecting to the measurement signal 
        self.pmt_fps_Label.setText("Per frame:  %.4f s" % time_per_frame_pmt)
        self.pmtTest.start()
        
    def measure_pmt_contourscan(self):
        self.Daq_sample_rate_pmt = int(self.contour_samprate.value())
        
        self.pmtTest_contour.setWave_contourscan(self.Daq_sample_rate_pmt, self.handle_viewbox_coordinate_position_array_expanded_forDaq, self.contour_point_number)
        contour_freq = self.Daq_sample_rate_pmt/self.contour_point_number
        
        #r1 = QRectF(500, 500, ScanArrayXnum, int(Value_yPixels))
        #self.pmtimageitem.setRect(r1)
        
        #self.pmtTest_contour.pmtimagingThread_contour.measurement.connect(self.update_pmt_Graphs) #Connecting to the measurement signal 
        self.pmt_fps_Label.setText("Contour frequency:  %.4f Hz" % contour_freq)
        self.pmtTest_contour.start()
        self.MessageToMainGUI('---!! Continuous contour scanning !!---'+'\n')
        
    def saveimage_pmt(self):
        Localimg = Image.fromarray(self.data_pmtcontineous) #generate an image object
        Localimg.save(os.path.join(self.savedirectory, 'PMT_'+ self.prefixtextboxtext + '_' +datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'.tif')) #save as tif
        #np.save(os.path.join(self.savedirectory, 'PMT'+ self.saving_prefix +datetime.now().strftime('%Y-%m-%d_%H-%M-%S')), self.data_pmtcontineous)
        
    def update_pmt_Graphs(self, data):
        """Update graphs."""
        
        self.data_pmtcontineous = data
        self.pmtvideoWidget.setImage(data)
        self.pmtimgroi.setImage(self.roi.getArrayRegion(data, self.pmtimageitem), levels=(0, data.max()))
        #

        #self.pmtvideoWidget.update_pmt_Window(self.data_pmtcontineous)
    def show_handle_num(self):
        self.ROIhandles = self.roi.getHandles()
        self.ROIhandles_nubmer = len(self.ROIhandles)
        self.pmt_handlenum_Label.setText("Handle number: %.d" % self.ROIhandles_nubmer)
        
    def generate_contour(self):
        """
        getLocalHandlePositions IS THE FUNCTION TO GRAP COORDINATES FROM IMAGEITEM REGARDLESS OF IMAGEITEM ZOOMING OR PANNING!!!
        """
        self.ROIhandles = self.roi.getHandles()
        self.ROIhandles_nubmer = len(self.ROIhandles)
        self.contour_point_number = int(self.pointsinContour.value())
        self.handle_scene_coordinate_position_raw_list = self.roi.getSceneHandlePositions()
        self.handle_local_coordinate_position_raw_list = self.roi.getLocalHandlePositions()
        self.Daq_sample_rate_pmt = int(self.contour_samprate.value())
#        self.galvo_contour_label_1.setText("Points in contour: %.d" % self.contour_point_number)
#        self.galvo_contour_label_2.setText("Sampling rate: %.d" % self.Daq_sample_rate_pmt)
        
        #put scene positions into numpy array
        self.handle_scene_coordinate_position_array = np.zeros((self.ROIhandles_nubmer, 2))# n rows, 2 columns
        for i in range(self.ROIhandles_nubmer):
            self.handle_scene_coordinate_position_array[i] = np.array([self.handle_scene_coordinate_position_raw_list[i][1].x(), self.handle_scene_coordinate_position_raw_list[i][1].y()])
        
        if self.contour_strategy.currentText() == 'Manual':
            #Interpolation
            self.point_num_per_line = int(self.contour_point_number/self.ROIhandles_nubmer)
            self.Interpolation_number = self.point_num_per_line-1
            
            # try to initialize an array then afterwards we can append on it
            #self.handle_scene_coordinate_position_array_expanded = np.array([[self.handle_scene_coordinate_position_array[0][0], self.handle_scene_coordinate_position_array[0][1]], [self.handle_scene_coordinate_position_array[1][0], self.handle_scene_coordinate_position_array[1][1]]])
            
            # -------------------------------------------------------------------------Interpolation from first to last----------------------------------------------------------------------------
            for i in range(self.ROIhandles_nubmer-1):
                self.Interpolation_x_diff = self.handle_scene_coordinate_position_array[i+1][0] - self.handle_scene_coordinate_position_array[i][0]
                self.Interpolation_y_diff = self.handle_scene_coordinate_position_array[i+1][1] - self.handle_scene_coordinate_position_array[i][1]
                
                self.Interpolation_x_step = self.Interpolation_x_diff/self.point_num_per_line
                self.Interpolation_y_step = self.Interpolation_y_diff/self.point_num_per_line
                
                Interpolation_temp = np.array([[self.handle_scene_coordinate_position_array[i][0], self.handle_scene_coordinate_position_array[i][1]], [self.handle_scene_coordinate_position_array[i+1][0], self.handle_scene_coordinate_position_array[i+1][1]]])
    
                for j in range(self.Interpolation_number):
                    Interpolation_temp=np.insert(Interpolation_temp,1,[self.handle_scene_coordinate_position_array[i+1][0] - (j+1)*self.Interpolation_x_step,self.handle_scene_coordinate_position_array[i+1][1] - (j+1)*self.Interpolation_y_step],axis = 0)
                Interpolation_temp = np.delete(Interpolation_temp, 0, 0)
                if i == 0:
                    self.handle_scene_coordinate_position_array_expanded = Interpolation_temp
                else:
                    self.handle_scene_coordinate_position_array_expanded=np.append(self.handle_scene_coordinate_position_array_expanded, Interpolation_temp, axis=0)
                    #self.handle_scene_coordinate_position_array_expanded=np.delete(self.handle_scene_coordinate_position_array_expanded, 0, 0)
            
            # Interpolation between last and first
            self.Interpolation_x_diff = self.handle_scene_coordinate_position_array[0][0] - self.handle_scene_coordinate_position_array[-1][0]
            self.Interpolation_y_diff = self.handle_scene_coordinate_position_array[0][1] - self.handle_scene_coordinate_position_array[-1][1]
            
            self.Interpolation_x_step = self.Interpolation_x_diff/self.point_num_per_line
            self.Interpolation_y_step = self.Interpolation_y_diff/self.point_num_per_line
            
            Interpolation_temp = np.array([[self.handle_scene_coordinate_position_array[-1][0], self.handle_scene_coordinate_position_array[-1][1]], [self.handle_scene_coordinate_position_array[0][0], self.handle_scene_coordinate_position_array[0][1]]])
    
            for j in range(self.Interpolation_number):
                Interpolation_temp=np.insert(Interpolation_temp,1,[self.handle_scene_coordinate_position_array[0][0] - (j+1)*self.Interpolation_x_step,self.handle_scene_coordinate_position_array[0][1] - (j+1)*self.Interpolation_y_step],axis = 0)
            Interpolation_temp = np.delete(Interpolation_temp, 0, 0)
            #Interpolation_temp = np.flip(Interpolation_temp, 0)
            
            self.handle_scene_coordinate_position_array_expanded=np.append(self.handle_scene_coordinate_position_array_expanded, Interpolation_temp, axis=0)
            #self.handle_scene_coordinate_position_array_expanded=np.delete(self.handle_scene_coordinate_position_array_expanded, 0, 0)
            #-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            
            self.handle_viewbox_coordinate_position_array_expanded = np.zeros((self.contour_point_number, 2))# n rows, 2 columns
            # Maps from scene coordinates to the coordinate system displayed inside the ViewBox
            for i in range(self.contour_point_number):
                qpoint_Scene = QPoint(self.handle_scene_coordinate_position_array_expanded[i][0], self.handle_scene_coordinate_position_array_expanded[i][1])
                qpoint_viewbox = self.pmtvb.mapSceneToView(qpoint_Scene)
                self.handle_viewbox_coordinate_position_array_expanded[i] = np.array([qpoint_viewbox.x(),qpoint_viewbox.y()])
                
            #print(self.handle_scene_coordinate_position_array)
            #print(self.handle_scene_coordinate_position_array_expanded)
            #print(self.handle_viewbox_coordinate_position_array_expanded)
            constants = HardwareConstants()
            '''Transform into Voltages to galvos'''
            '''coordinates in the view box(handle_viewbox_coordinate_position_array_expanded_x) are equivalent to voltages sending out'''
            if self.Value_xPixels == 500:
                if self.Value_voltXMax == 3:
                    # for 500 x axis, the real ramp region sits around 52~552 out of 0~758
                    self.handle_viewbox_coordinate_position_array_expanded[:,0] = ((self.handle_viewbox_coordinate_position_array_expanded[:,0])/500)*6-3 #(self.handle_viewbox_coordinate_position_array_expanded[:,0]-constants.pmt_3v_indentation_pixels)
                    self.handle_viewbox_coordinate_position_array_expanded[:,1] = ((self.handle_viewbox_coordinate_position_array_expanded[:,1])/500)*6-3
                    self.handle_viewbox_coordinate_position_array_expanded = np.around(self.handle_viewbox_coordinate_position_array_expanded, decimals=3)
                    # shape into (n,) and stack
                    self.handle_viewbox_coordinate_position_array_expanded_x = np.resize(self.handle_viewbox_coordinate_position_array_expanded[:,0],(self.contour_point_number,))
                    self.handle_viewbox_coordinate_position_array_expanded_y = np.resize(self.handle_viewbox_coordinate_position_array_expanded[:,1],(self.contour_point_number,))
                    self.handle_viewbox_coordinate_position_array_expanded_forDaq = np.vstack((self.handle_viewbox_coordinate_position_array_expanded_x,self.handle_viewbox_coordinate_position_array_expanded_y))
            print(self.handle_viewbox_coordinate_position_array_expanded)
            '''Speed and acceleration check'''
            #for i in range(self.contour_point_number):
             #   speed_between_points = ((self.handle_viewbox_coordinate_position_array_expanded_x[i+1]-self.handle_viewbox_coordinate_position_array_expanded_x[i])**2+(self.handle_viewbox_coordinate_position_array_expanded_y[i+1]-self.handle_viewbox_coordinate_position_array_expanded_y[i])**2)**(0.5)
            self.Daq_sample_rate_pmt = int(self.contour_samprate.value())
            time_gap = 1/self.Daq_sample_rate_pmt
            contour_x_speed = np.diff(self.handle_viewbox_coordinate_position_array_expanded_x)/time_gap
            contour_y_speed = np.diff(self.handle_viewbox_coordinate_position_array_expanded_y)/time_gap
            
            contour_x_acceleration = np.diff(contour_x_speed)/time_gap
            contour_y_acceleration = np.diff(contour_y_speed)/time_gap
            
            constants = HardwareConstants()
            speedGalvo = constants.maxGalvoSpeed #Volt/s
            aGalvo = constants.maxGalvoAccel #Acceleration galvo in volt/s^2
            print(np.amax(abs(contour_x_speed)))
            print(np.amax(abs(contour_y_speed)))
            print(np.amax(abs(contour_x_acceleration)))
            print(np.amax(abs(contour_y_acceleration)))  

            print(str(np.mean(abs(contour_x_speed)))+' and mean y speed:'+str(np.mean(abs(contour_y_speed))))
            print(str(np.mean(abs(contour_x_acceleration)))+' and mean y acceleration:'+str(np.mean(abs(contour_y_acceleration))))
            
            if speedGalvo > np.amax(abs(contour_x_speed)) and speedGalvo > np.amax(abs(contour_y_speed)):
                print('Contour speed is OK')
                self.MessageToMainGUI('Contour speed is OK'+'\n')
            else:
                QMessageBox.warning(self,'OverLoad','Speed too high!',QMessageBox.Ok)
            if aGalvo > np.amax(abs(contour_x_acceleration)) and aGalvo > np.amax(abs(contour_y_acceleration)):
                print('Contour acceleration is OK')
                self.MessageToMainGUI('Contour acceleration is OK'+'\n')
            else:
                QMessageBox.warning(self,'OverLoad','Acceleration too high!',QMessageBox.Ok)
                
        if self.contour_strategy.currentText() == 'Uniform':
            # Calculate the total distance
            self.total_distance = 0
            for i in range(self.ROIhandles_nubmer):
                if i != (self.ROIhandles_nubmer-1):
                    Interpolation_x_diff = self.handle_scene_coordinate_position_array[i+1][0] - self.handle_scene_coordinate_position_array[i][0]
                    Interpolation_y_diff = self.handle_scene_coordinate_position_array[i+1][1] - self.handle_scene_coordinate_position_array[i][1]
                    distance_vector = (Interpolation_x_diff**2+Interpolation_y_diff**2)**(0.5)
                    self.total_distance = self.total_distance + distance_vector
                else:
                    Interpolation_x_diff = self.handle_scene_coordinate_position_array[0][0] - self.handle_scene_coordinate_position_array[-1][0]
                    Interpolation_y_diff = self.handle_scene_coordinate_position_array[0][1] - self.handle_scene_coordinate_position_array[-1][1]
                    distance_vector = (Interpolation_x_diff**2+Interpolation_y_diff**2)**(0.5)
                    self.total_distance = self.total_distance + distance_vector            
            
            self.averaged_uniform_step = self.total_distance/self.contour_point_number
            
            print(self.averaged_uniform_step)
            print(self.handle_scene_coordinate_position_array)

            for i in range(self.ROIhandles_nubmer):
                if i == 0:
                    Interpolation_x_diff = self.handle_scene_coordinate_position_array[i+1][0] - self.handle_scene_coordinate_position_array[i][0]
                    Interpolation_y_diff = self.handle_scene_coordinate_position_array[i+1][1] - self.handle_scene_coordinate_position_array[i][1]
                    distance_vector = (Interpolation_x_diff**2+Interpolation_y_diff**2)**(0.5)    
                    num_of_Interpolation = distance_vector//self.averaged_uniform_step
                    
                    #Interpolation_remaining = distance_vector%self.averaged_uniform_step
                    self.Interpolation_remaining_fornextround = self.averaged_uniform_step*(1-(distance_vector/self.averaged_uniform_step-num_of_Interpolation))
                    print('Interpolation_remaining_fornextround: '+str(self.Interpolation_remaining_fornextround))
                    self.Interpolation_x_step = Interpolation_x_diff/(distance_vector/self.averaged_uniform_step)
                    self.Interpolation_y_step = Interpolation_y_diff/(distance_vector/self.averaged_uniform_step)
                    
                    Interpolation_temp = np.array([[self.handle_scene_coordinate_position_array[i][0], self.handle_scene_coordinate_position_array[i][1]], [self.handle_scene_coordinate_position_array[i+1][0], self.handle_scene_coordinate_position_array[i+1][1]]])
        
                    for j in range(int(num_of_Interpolation)):
                        Interpolation_temp=np.insert(Interpolation_temp,-1,[self.handle_scene_coordinate_position_array[i][0] + (j+1)*self.Interpolation_x_step,self.handle_scene_coordinate_position_array[i+1][1] + (j+1)*self.Interpolation_y_step],axis = 0)
                    Interpolation_temp = np.delete(Interpolation_temp,-1,axis=0) 
                    
                    self.handle_scene_coordinate_position_array_expanded_uniform = Interpolation_temp
                    
                elif i != (self.ROIhandles_nubmer-1):
                    Interpolation_x_diff = self.handle_scene_coordinate_position_array[i+1][0] - self.handle_scene_coordinate_position_array[i][0]
                    Interpolation_y_diff = self.handle_scene_coordinate_position_array[i+1][1] - self.handle_scene_coordinate_position_array[i][1]
                    distance_vector = (Interpolation_x_diff**2+Interpolation_y_diff**2)**(0.5)                    
                    num_of_Interpolation = (distance_vector-self.Interpolation_remaining_fornextround)//self.averaged_uniform_step       
                    print('Interpolation_remaining_fornextround: '+str(self.Interpolation_remaining_fornextround))
                    
                    if self.Interpolation_remaining_fornextround != 0:
                        self.Interpolation_remaining_fornextround_x =Interpolation_x_diff/(distance_vector/self.Interpolation_remaining_fornextround)#(self.Interpolation_remaining_fornextround/distance_vector)*Interpolation_x_diff
                        self.Interpolation_remaining_fornextround_y =Interpolation_y_diff/(distance_vector/self.Interpolation_remaining_fornextround)#(self.Interpolation_remaining_fornextround/distance_vector)*Interpolation_y_diff
                    else:
                        self.Interpolation_remaining_fornextround_x = 0
                        self.Interpolation_remaining_fornextround_y = 0
                        
                    
                    # Reset the starting point
                    Interpolation_x_diff = self.handle_scene_coordinate_position_array[i+1][0] - self.handle_scene_coordinate_position_array[i][0] - self.Interpolation_remaining_fornextround_x
                    Interpolation_y_diff = self.handle_scene_coordinate_position_array[i+1][1] - self.handle_scene_coordinate_position_array[i][1] - self.Interpolation_remaining_fornextround_y                 
                    
                    
                    self.Interpolation_x_step = Interpolation_x_diff/((distance_vector-self.Interpolation_remaining_fornextround)/self.averaged_uniform_step)
                    self.Interpolation_y_step = Interpolation_y_diff/((distance_vector-self.Interpolation_remaining_fornextround)/self.averaged_uniform_step)
                    
                    Interpolation_temp = np.array([[self.handle_scene_coordinate_position_array[i][0]+self.Interpolation_remaining_fornextround_x, self.handle_scene_coordinate_position_array[i][1]+self.Interpolation_remaining_fornextround_y],
                                                   [self.handle_scene_coordinate_position_array[i+1][0], self.handle_scene_coordinate_position_array[i+1][1]]])
        
                    for j in range(int(num_of_Interpolation)):
                        Interpolation_temp=np.insert(Interpolation_temp,-1,[self.handle_scene_coordinate_position_array[i][0]+self.Interpolation_remaining_fornextround_x + (j+1)*self.Interpolation_x_step,self.handle_scene_coordinate_position_array[i][1]+\
                                                                            self.Interpolation_remaining_fornextround_y + (j+1)*self.Interpolation_y_step],axis = 0)
                    Interpolation_temp = np.delete(Interpolation_temp,-1,axis=0)   
                    
                    self.handle_scene_coordinate_position_array_expanded_uniform=np.append(self.handle_scene_coordinate_position_array_expanded_uniform, Interpolation_temp, axis=0) 
                    
                    self.Interpolation_remaining_fornextround = self.averaged_uniform_step*(1-((distance_vector-self.Interpolation_remaining_fornextround)/self.averaged_uniform_step-num_of_Interpolation))
                    
                else:  # connect the first and the last
                    Interpolation_x_diff = self.handle_scene_coordinate_position_array[0][0] - self.handle_scene_coordinate_position_array[-1][0]
                    Interpolation_y_diff = self.handle_scene_coordinate_position_array[0][1] - self.handle_scene_coordinate_position_array[-1][1]
                    distance_vector = (Interpolation_x_diff**2+Interpolation_y_diff**2)**(0.5)                    
                    num_of_Interpolation = (distance_vector-self.Interpolation_remaining_fornextround)//self.averaged_uniform_step       
                    
                    #self.Interpolation_remaining_fornextround = self.averaged_uniform_step*(1-((distance_vector-self.Interpolation_remaining_fornextround)/self.averaged_uniform_step-num_of_Interpolation))
                    self.Interpolation_remaining_fornextround_x =(self.Interpolation_remaining_fornextround/distance_vector)*Interpolation_x_diff
                    self.Interpolation_remaining_fornextround_y =(self.Interpolation_remaining_fornextround/distance_vector)*Interpolation_y_diff
                    
                    # Reset the starting point
                    Interpolation_x_diff = self.handle_scene_coordinate_position_array[0][0] - self.handle_scene_coordinate_position_array[i][0] + self.Interpolation_remaining_fornextround_x
                    Interpolation_y_diff = self.handle_scene_coordinate_position_array[0][1] - self.handle_scene_coordinate_position_array[i][1] + self.Interpolation_remaining_fornextround_y   
                    
                    self.Interpolation_x_step = Interpolation_x_diff/((distance_vector-self.Interpolation_remaining_fornextround)/self.averaged_uniform_step)
                    self.Interpolation_y_step = Interpolation_y_diff/((distance_vector-self.Interpolation_remaining_fornextround)/self.averaged_uniform_step)  
                    
                    Interpolation_temp = np.array([[self.handle_scene_coordinate_position_array[-1][0]+self.Interpolation_remaining_fornextround_x, self.handle_scene_coordinate_position_array[-1][1]+self.Interpolation_remaining_fornextround_y], 
                                                   [self.handle_scene_coordinate_position_array[0][0], self.handle_scene_coordinate_position_array[0][1]]])
        
                    for j in range(int(num_of_Interpolation)):
                        Interpolation_temp=np.insert(Interpolation_temp,-1,[self.handle_scene_coordinate_position_array[-1][0]+self.Interpolation_remaining_fornextround_x + (j+1)*self.Interpolation_x_step,self.handle_scene_coordinate_position_array[-1][1]+\
                                                     self.Interpolation_remaining_fornextround_y + (j+1)*self.Interpolation_y_step],axis = 0)
                    Interpolation_temp = np.delete(Interpolation_temp,-1,axis=0)   
                    
                    self.handle_scene_coordinate_position_array_expanded_uniform=np.append(self.handle_scene_coordinate_position_array_expanded_uniform, Interpolation_temp, axis=0)        
            
            print(self.handle_scene_coordinate_position_array_expanded_uniform)
            print(self.handle_scene_coordinate_position_array_expanded_uniform.shape)
            #-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            
            self.handle_viewbox_coordinate_position_array_expanded = np.zeros((self.contour_point_number, 2))# n rows, 2 columns
            # Maps from scene coordinates to the coordinate system displayed inside the ViewBox
            for i in range(self.contour_point_number):
                qpoint_Scene = QPoint(self.handle_scene_coordinate_position_array_expanded_uniform[i][0], self.handle_scene_coordinate_position_array_expanded_uniform[i][1])
                qpoint_viewbox = self.pmtvb.mapSceneToView(qpoint_Scene)
                self.handle_viewbox_coordinate_position_array_expanded[i] = np.array([qpoint_viewbox.x(),qpoint_viewbox.y()])
                
            #print(self.handle_scene_coordinate_position_array)
            #print(self.handle_scene_coordinate_position_array_expanded)
            #print(self.handle_viewbox_coordinate_position_array_expanded)
            
            '''Transform into Voltages to galvos'''
            
            constants = HardwareConstants()
            if self.Value_xPixels == 500:
                if self.Value_voltXMax == 3:
                    # for 500 x axis, the real ramp region sits around 52~552 out of 0~758
                    self.handle_viewbox_coordinate_position_array_expanded[:,0] = ((self.handle_viewbox_coordinate_position_array_expanded[:,0])/500)*6-3 #self.handle_viewbox_coordinate_position_array_expanded[:,0]-constants.pmt_3v_indentation_pixels
                    self.handle_viewbox_coordinate_position_array_expanded[:,1] = ((self.handle_viewbox_coordinate_position_array_expanded[:,1])/500)*6-3
                    self.handle_viewbox_coordinate_position_array_expanded = np.around(self.handle_viewbox_coordinate_position_array_expanded, decimals=3)
                    # shape into (n,) and stack
                    self.handle_viewbox_coordinate_position_array_expanded_x = np.resize(self.handle_viewbox_coordinate_position_array_expanded[:,0],(self.contour_point_number,))
                    self.handle_viewbox_coordinate_position_array_expanded_y = np.resize(self.handle_viewbox_coordinate_position_array_expanded[:,1],(self.contour_point_number,))
                    self.handle_viewbox_coordinate_position_array_expanded_forDaq = np.vstack((self.handle_viewbox_coordinate_position_array_expanded_x,self.handle_viewbox_coordinate_position_array_expanded_y))
            print(self.handle_viewbox_coordinate_position_array_expanded)
            '''Speed and acceleration check'''
            #for i in range(self.contour_point_number):
             #   speed_between_points = ((self.handle_viewbox_coordinate_position_array_expanded_x[i+1]-self.handle_viewbox_coordinate_position_array_expanded_x[i])**2+(self.handle_viewbox_coordinate_position_array_expanded_y[i+1]-self.handle_viewbox_coordinate_position_array_expanded_y[i])**2)**(0.5)
            self.Daq_sample_rate_pmt = int(self.contour_samprate.value())
            time_gap = 1/self.Daq_sample_rate_pmt
            contour_x_speed = np.diff(self.handle_viewbox_coordinate_position_array_expanded_x)/time_gap
            contour_y_speed = np.diff(self.handle_viewbox_coordinate_position_array_expanded_y)/time_gap
            
            contour_x_acceleration = np.diff(contour_x_speed)/time_gap
            contour_y_acceleration = np.diff(contour_y_speed)/time_gap
            
            constants = HardwareConstants()
            speedGalvo = constants.maxGalvoSpeed #Volt/s
            aGalvo = constants.maxGalvoAccel #Acceleration galvo in volt/s^2
            print(np.amax(abs(contour_x_speed)))
            print(np.amax(abs(contour_y_speed)))
            print(np.amax(abs(contour_x_acceleration)))
            print(np.amax(abs(contour_y_acceleration)))  

            print(str(np.mean(abs(contour_x_speed)))+' and mean y speed:'+str(np.mean(abs(contour_y_speed))))
            print(str(np.mean(abs(contour_x_acceleration)))+' and mean y acceleration:'+str(np.mean(abs(contour_y_acceleration))))
            
            if speedGalvo > np.amax(abs(contour_x_speed)) and speedGalvo > np.amax(abs(contour_y_speed)):
                print('Contour speed is OK')
                self.MessageToMainGUI('Contour speed is OK'+'\n')
            if aGalvo > np.amax(abs(contour_x_acceleration)) and aGalvo > np.amax(abs(contour_y_acceleration)):
                print('Contour acceleration is OK')
                self.MessageToMainGUI('Contour acceleration is OK'+'\n')
        
        self.SignalForContourScanning.emit(self.contour_point_number, self.Daq_sample_rate_pmt, (1/int(self.contour_samprate.value())*1000)*self.contour_point_number, 
                                           self.handle_viewbox_coordinate_position_array_expanded_x, self.handle_viewbox_coordinate_position_array_expanded_y)
        
    def generate_contour_for_waveform(self):
        self.contour_time = int(self.textbox1L.value())
        self.time_per_contour = (1/int(self.contour_samprate.value())*1000)*self.contour_point_number
        repeatnum_contour = int(self.contour_time/self.time_per_contour)
        self.repeated_contoursamples_1 = np.tile(self.handle_viewbox_coordinate_position_array_expanded_x, repeatnum_contour)
        self.repeated_contoursamples_2 = np.tile(self.handle_viewbox_coordinate_position_array_expanded_y, repeatnum_contour)       
        
        self.handle_viewbox_coordinate_position_array_expanded_forDaq_waveform = np.vstack((self.repeated_contoursamples_1,self.repeated_contoursamples_2))
                
        return self.handle_viewbox_coordinate_position_array_expanded_forDaq_waveform
        
    def generate_galvos_contour_graphy(self):

        self.xlabelhere_galvos = np.arange(len(self.handle_viewbox_coordinate_position_array_expanded_forDaq_waveform[1,:]))/self.Daq_sample_rate_pmt
        self.PlotDataItem_galvos = PlotDataItem(self.xlabelhere_galvos, self.handle_viewbox_coordinate_position_array_expanded_forDaq_waveform[1,:])
        self.PlotDataItem_galvos.setDownsampling(auto=True, method='mean')            
        self.PlotDataItem_galvos.setPen('w')

        self.pw.addItem(self.PlotDataItem_galvos)
        self.textitem_galvos = pg.TextItem(text='Contour', color=('w'), anchor=(1, 1))
        self.textitem_galvos.setPos(0, 5)
        self.pw.addItem(self.textitem_galvos)
        
    def MessageToMainGUI(self, text):
        self.MessageBack.emit(text)
                    
    def stopMeasurement_pmt(self):
        """Stop the seal test."""
        self.pmtTest.aboutToQuitHandler()
        
    def stopMeasurement_pmt_contour(self):
        """Stop the seal test."""
        self.pmtTest_contour.aboutToQuitHandler()
        self.MessageToMainGUI('---!! Contour stopped !!---'+'\n')
        
#    def closeEvent(self, event):
#            
#        QtWidgets.QApplication.quit()
#        event.accept()
    '''    
    def closeEvent(self, event):
        """On closing the application we have to make sure that the measuremnt
        stops and the device gets freed."""
        self.stopMeasurement()
    '''
if __name__ == "__main__":
    
    os.chdir(os.path.dirname(sys.argv[0]))# Set directory to current folder.
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        pg.setConfigOptions(imageAxisOrder='row-major')
        mainwin = PMTWidgetUI()
        mainwin.show()
        app.exec_()
    run_app()