# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 17:27:04 2020

@author: xinmeng

-------------------------------------------------------------------------------------------------------------------------------------
                                Image analysis GUI
-------------------------------------------------------------------------------------------------------------------------------------
"""

from __future__ import division
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPoint, QRect, QObject
from PyQt5.QtGui import QColor, QPen, QPixmap, QIcon, QTextCursor, QFont

from PyQt5.QtWidgets import (QWidget, QButtonGroup, QLabel, QSlider, QSpinBox, QDoubleSpinBox, QGridLayout, QPushButton, QGroupBox, 
                             QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox, QTabWidget, QCheckBox, QRadioButton, 
                             QFileDialog, QProgressBar, QTextEdit)
import os
from datetime import datetime
import pyqtgraph as pg
from pyqtgraph import PlotDataItem, TextItem
from IPython import get_ipython
import sys
import csv
import numpy as np
from PIL import Image
try:
    from ImageAnalysis.matlabAnalysis import readbinaryfile, extractV
    import ImageAnalysis.Plotanalysis
except:
    from matlabAnalysis import readbinaryfile, extractV
    import Plotanalysis
from skimage.io import imread
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from PyQt5.QtCore import pyqtSignal, QThread

class AnalysisWidgetUI(QWidget):
    
#    waveforms_generated = pyqtSignal(object, object, list, int)
#    SignalForContourScanning = pyqtSignal(int, int, int, np.ndarray, np.ndarray)
    MessageBack = pyqtSignal(str)
    
    #------------------------------------------------------------------------------------------------------------------------------------------
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
#        os.chdir('./')# Set directory to current folder.
        self.setFont(QFont("Arial"))
        
        self.setMinimumSize(1250,850)
        self.setWindowTitle("AnalysisWidget")
        self.layout = QGridLayout(self)
        
        self.OC = 0.1 # Patch clamp constant
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------GUI for Data analysis tab--------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************
        readimageContainer = QGroupBox("Readin images")
        self.readimageLayout = QGridLayout()
        
        self.switch_Vp_or_camtrace = QComboBox()
        self.switch_Vp_or_camtrace.addItems(['With Vp', 'Camera trace'])
        self.readimageLayout.addWidget(self.switch_Vp_or_camtrace, 1, 1)
        
        self.readimageLayout.addWidget(QLabel('Video of interest:'), 1, 0)
       
        self.textbox_filename = QLineEdit(self)        
        self.readimageLayout.addWidget(self.textbox_filename, 1, 2)
        
        self.button_browse = QPushButton('Browse', self)
        self.readimageLayout.addWidget(self.button_browse, 1, 3) 
        
        self.button_browse.clicked.connect(self.getfile)

        self.button_load = QPushButton('Load', self)
        self.button_load.setStyleSheet("QPushButton {color:white;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                       "QPushButton:pressed {color:black;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.readimageLayout.addWidget(self.button_load, 1, 4) 
        
        self.Spincamsamplingrate = QSpinBox(self)
        self.Spincamsamplingrate.setMaximum(2000)
        self.Spincamsamplingrate.setValue(250)
        self.Spincamsamplingrate.setSingleStep(250)
        self.readimageLayout.addWidget(self.Spincamsamplingrate, 1, 6)
        self.readimageLayout.addWidget(QLabel("Camera FPS:"), 1, 5)
        
        self.button_clearpolts = QPushButton('Clear', self)
        self.readimageLayout.addWidget(self.button_clearpolts, 1, 7)         
        
        self.button_clearpolts.clicked.connect(self.clearplots)
        
        self.button_load.clicked.connect(self.loadtiffile)
        self.button_load.clicked.connect(lambda: self.loadcurve(self.fileName))
        
        # Background substraction
        self.switch_bg_Video_or_image = QComboBox()
        self.switch_bg_Video_or_image.addItems(['Video', 'Image','ROI'])
        self.readimageLayout.addWidget(self.switch_bg_Video_or_image, 2, 1)
       
        self.readimageLayout.addWidget(QLabel('Background:'), 2, 0)
       
        self.textbox_Background_filename = QLineEdit(self)        
        self.readimageLayout.addWidget(self.textbox_Background_filename, 2, 2)
        
        self.button_Background_browse = QPushButton('Browse', self)
        self.readimageLayout.addWidget(self.button_Background_browse, 2, 3) 
        
        self.button_Background_browse.clicked.connect(self.getfile_background)

        self.button_Background_load = QPushButton('Substract', self)
        self.button_Background_load.setStyleSheet("QPushButton {color:white;background-color: orange; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                       "QPushButton:pressed {color:black;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.readimageLayout.addWidget(self.button_Background_load, 2, 4) 
        
        self.button_Background_load.clicked.connect(self.substract_background)        
        
        self.button_display_trace = QPushButton('Display', self)
        self.button_display_trace.setStyleSheet("QPushButton {color:white;background-color: Green; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                       "QPushButton:pressed {color:black;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.readimageLayout.addWidget(self.button_display_trace, 2, 6) 
        
        self.button_display_trace.clicked.connect(lambda: self.displayElectricalsignal())
        self.button_display_trace.clicked.connect(lambda: self.displayConfiguredWaveform())
        self.button_display_trace.clicked.connect(lambda: self.displaycamtrace())        
               
        self.switch_export_trace = QComboBox()
        self.switch_export_trace.addItems(['Cam trace', 'Weighted trace'])
        self.readimageLayout.addWidget(self.switch_export_trace, 2, 5)
        
        self.button_export_trace = QPushButton('Export', self)
        self.button_export_trace.setStyleSheet("QPushButton {color:white;background-color: Green; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                       "QPushButton:pressed {color:black;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.readimageLayout.addWidget(self.button_export_trace, 2, 7) 
        
        self.button_export_trace.clicked.connect(self.export_trace)
        
        readimageContainer.setLayout(self.readimageLayout)
        readimageContainer.setMaximumHeight(120)
        
        #-----------------------------------------------------Image analysis display Tab-------------------------------------------------------
        Display_Container = QGroupBox("Image analysis display")
        Display_Layout = QGridLayout()
        # Setting tabs
        Display_Container_tabs = QTabWidget()
        
        #------------------------------------------------------I, V display window-------------------------------------------------------
        self.VIdisplay_Layout = QGridLayout()

        #Wavefrom window
        self.pw_preset_waveform = pg.PlotWidget(title='Executed waveform')
        self.pw_preset_waveform.setLabel('bottom', 'Time', units='s')
        self.pw_preset_waveform.setLabel('left', 'Voltage', units='V')
        self.VIdisplay_Layout.addWidget(self.pw_preset_waveform, 0,0) 
        
        #Voltage window
        self.pw_patch_voltage = pg.PlotWidget(title='Voltage plot')
        self.pw_patch_voltage.setLabel('bottom', 'Time', units='s')
        self.pw_patch_voltage.setLabel('left', 'Voltage', units='mV')        
        
        self.VIdisplay_Layout.addWidget(self.pw_patch_voltage, 1,0)
        
        #Current window
        self.pw_patch_current = pg.PlotWidget(title='Current plot')
        self.pw_patch_current.setLabel('bottom', 'Time', units='s')
        self.pw_patch_current.setLabel('left', 'Current', units='pA')
        self.VIdisplay_Layout.addWidget(self.pw_patch_current, 2,0) 
        
        '''        
        self.datadislay_label = pg.LabelItem(justify='right')
        self.pw_patch_current.addItem(self.datadislay_label)
        '''
        #cross hair
        self.vLine = pg.InfiniteLine(pos=0.4, angle=90, movable=True)
        self.pw_patch_current.addItem(self.vLine, ignoreBounds=True)
        
        #Camera trace window
        self.pw_patch_camtrace = pg.PlotWidget(title='Trace plot')
        self.pw_patch_camtrace.setLabel('bottom', 'Time', units='s')
        self.pw_patch_camtrace.setLabel('left', 'signal', units=' counts/ms')
        
        
        #self.pw_patch_camtrace.addLegend(offset=(20,5)) # Add legend here, Plotitem with name will be automated displayed.
        self.VIdisplay_Layout.addWidget(self.pw_patch_camtrace, 3,0) 

        self.vLine_cam = pg.InfiniteLine(pos=0.4, angle=90, movable=True)
        self.pw_patch_camtrace.addItem(self.vLine_cam, ignoreBounds=True)

#        self.Curvedisplay_Container.setLayout(self.Curvedisplay_Layout)
#        self.Curvedisplay_Container.setMaximumHeight(550)
        
        self.vLine.sigPositionChangeFinished.connect(self.showpointdata)
        self.vLine_cam.sigPositionChangeFinished.connect(self.showpointdata_camtrace)                
# =============================================================================
#         #------------------------------------------------------Matplot display window-------------------------------------------------------
# #        self.Curvedisplay_Layout = QGridLayout()
# #
# #        # a figure instance to plot on
# #        self.Matdisplay_figure = Figure()
# #
# #        # this is the Canvas Widget that displays the `figure`
# #        # it takes the `figure` instance as a parameter to __init__
# #        self.Matdisplay_figure_canvas = FigureCanvas(self.Matdisplay_figure)
# #
# #        # this is the Navigation widget
# #        # it takes the Canvas widget and a parent
# #        self.Matdisplay_toolbar = NavigationToolbar(self.Matdisplay_figure_canvas, self)
# #
# #        # Just some button connected to `plot` method
# #        self.Matdisplay_button =QPushButton('Select nest folder')
# #        self.Matdisplay_button.clicked.connect(self.Matdisplay_plot)
# #        self.Matdisplay_draw_button =QPushButton('Draw!')
# #        self.Matdisplay_draw_button.clicked.connect(self.matdisplay_draw)       
# #        
# #        self.Matdisplay_clear_button =QPushButton('Clear')
# #        self.Matdisplay_clear_button.clicked.connect(self.matdisplay_clear)       
# #        
# #        self.Curvedisplay_savedirectorytextbox = QtWidgets.QLineEdit(self)
# #        self.Curvedisplay_Layout.addWidget(self.Curvedisplay_savedirectorytextbox, 0, 3)
# #        # set the layout
# #        self.Curvedisplay_Layout.addWidget(self.Matdisplay_toolbar, 1, 0, 1, 5)
# #        self.Curvedisplay_Layout.addWidget(self.Matdisplay_figure_canvas, 2, 0, 1, 5)
# #        self.Curvedisplay_Layout.addWidget(self.Matdisplay_button, 0, 4)
# #        self.Curvedisplay_Layout.addWidget(self.Matdisplay_draw_button, 0, 5)
# #        self.Curvedisplay_Layout.addWidget(self.Matdisplay_clear_button, 0, 6)
# #        
# #        self.checkboxWaveform = QCheckBox("Waveform")
# #        self.checkboxWaveform.setStyleSheet('color:CadetBlue;font:bold "Times New Roman"')
# #        self.checkboxWaveform.setChecked(True)
# #        self.Curvedisplay_Layout.addWidget(self.checkboxWaveform, 0, 0)  
# #        
# #        self.checkboxTrace = QCheckBox("Recorded trace")
# #        self.checkboxTrace.setStyleSheet('color:CadetBlue;font:bold "Times New Roman"')
# #        self.Curvedisplay_Layout.addWidget(self.checkboxTrace, 0, 1)  
# #        
# #        self.checkboxCam = QCheckBox("Cam trace")
# #        self.checkboxCam.setStyleSheet('color:CadetBlue;font:bold "Times New Roman"')
# #        
# #        self.Curvedisplay_Layout.addWidget(self.checkboxCam, 0, 2)
# =============================================================================
        

        #------------------------------------------------------Image Analysis-Average window-------------------------------------------------------
        image_display_container_layout = QGridLayout()
        
        imageanalysis_average_Container = QGroupBox("Image Analysis-Average window")
        self.imageanalysisLayout_average = QGridLayout()
                
        #self.pw_averageimage = averageimagewindow()
        self.pw_averageimage = pg.ImageView()
        self.pw_averageimage.ui.roiBtn.hide()
        self.pw_averageimage.ui.menuBtn.hide()   

        self.roi_average = pg.PolyLineROI([[0,0], [10,10], [10,30], [30,10]], closed=True)
        self.pw_averageimage.view.addItem(self.roi_average)
        #self.pw_weightimage = weightedimagewindow()
        self.imageanalysisLayout_average.addWidget(self.pw_averageimage, 0, 0, 5, 3)
    
        #self.imageanalysisLayout_average.addWidget(self.pw_averageimage, 0, 0, 3, 3)
        
        self.button_average = QPushButton('Average', self)
        self.button_average.setMaximumWidth(120)
        self.imageanalysisLayout_average.addWidget(self.button_average, 0, 3) 
        self.button_average.clicked.connect(self.calculateaverage)
        
        self.button_bg_average = QPushButton('Background Mean', self)
        self.button_bg_average.setMaximumWidth(120)
        self.imageanalysisLayout_average.addWidget(self.button_bg_average, 1, 3) 
        self.button_bg_average.clicked.connect(self.calculateaverage_bg)
        
        imageanalysis_average_Container.setLayout(self.imageanalysisLayout_average)
        imageanalysis_average_Container.setMinimumHeight(180)
        #------------------------------------------------------Image Analysis-weighV window-------------------------------------------------------
        imageanalysis_weight_Container = QGroupBox("Image Analysis-Weight window")
        self.imageanalysisLayout_weight = QGridLayout()
                
        #self.pw_averageimage = averageimagewindow()
        self.pw_weightimage = pg.ImageView()
        self.pw_weightimage.ui.roiBtn.hide()
        self.pw_weightimage.ui.menuBtn.hide()
        
        self.roi_weighted = pg.PolyLineROI([[0,0], [10,10], [10,30], [30,10]], closed=True)
        self.pw_weightimage.view.addItem(self.roi_weighted)
        #self.pw_weightimage = weightedimagewindow()
        self.imageanalysisLayout_weight.addWidget(self.pw_weightimage, 0, 0, 5, 3)
        
        self.button_weight = QPushButton('Weight', self)
        self.button_weight.setMaximumWidth(120)
        self.imageanalysisLayout_weight.addWidget(self.button_weight, 0, 3) 
        self.button_weight.clicked.connect(self.calculateweight)
        
        self.button_weighttrace = QPushButton('Weighted Trace', self)
        self.button_weighttrace.setMaximumWidth(120)
        self.imageanalysisLayout_weight.addWidget(self.button_weighttrace, 1, 3) 
        self.button_weighttrace.clicked.connect(self.displayweighttrace)
        
        self.button_roi_weighttrace = QPushButton('ROI-Weighted Trace', self)
        self.button_roi_weighttrace.setMaximumWidth(120)
        self.imageanalysisLayout_weight.addWidget(self.button_roi_weighttrace, 2, 3) 
        self.button_roi_weighttrace.clicked.connect(self.displayROIweighttrace)
        
        self.button_weight_save = QPushButton('Save image', self)
        self.button_weight_save.setMaximumWidth(120)
        self.imageanalysisLayout_weight.addWidget(self.button_weight_save, 3, 3) 
        self.button_weight_save.clicked.connect(lambda: self.save_analyzed_image('weight_image'))
        
        self.button_weight_save_trace = QPushButton('Save trace', self)
        self.button_weight_save_trace.setMaximumWidth(120)
        self.imageanalysisLayout_weight.addWidget(self.button_weight_save_trace, 4, 3) 
        self.button_weight_save_trace.clicked.connect(lambda: self.save_analyzed_image('weight_trace'))
        
        imageanalysis_weight_Container.setLayout(self.imageanalysisLayout_weight)
        imageanalysis_weight_Container.setMinimumHeight(180)
        
        image_display_container_layout.addWidget(imageanalysis_average_Container, 0, 0)
        image_display_container_layout.addWidget(imageanalysis_weight_Container, 1, 0)
        
        try:
            Display_Container_tabs_tab3 = Plotanalysis.PlotAnalysisGUI()
        except:
            Display_Container_tabs_tab3 = ImageAnalysis.Plotanalysis.PlotAnalysisGUI()
#        Display_Container_tabs_tab3.setLayout(self.Curvedisplay_Layout)
        
        Display_Container_tabs_tab2 = QWidget()
        Display_Container_tabs_tab2.setLayout(self.VIdisplay_Layout)        
        
        Display_Container_tabs_Galvo_WidgetInstance = QWidget()
        Display_Container_tabs_Galvo_WidgetInstance.setLayout(image_display_container_layout)
        
        # Add tabs
        Display_Container_tabs.addTab(Display_Container_tabs_Galvo_WidgetInstance,"Graph display")
        Display_Container_tabs.addTab(Display_Container_tabs_tab2,"Patch display")        
        Display_Container_tabs.addTab(Display_Container_tabs_tab3,"Patch perfusion")   
        
        Display_Layout.addWidget(Display_Container_tabs, 0, 0)  
        Display_Container.setLayout(Display_Layout)        

        self.layout.addWidget(readimageContainer, 0, 0, 1, 2)
        self.layout.addWidget(Display_Container, 1, 0, 1, 2)
#        master_data_analysis.addWidget(imageanalysis_average_Container, 2, 0, 1,1)
#        master_data_analysis.addWidget(imageanalysis_weight_Container, 2, 1, 1,1)
        
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #------------------------------------------------Functions for Data analysis Tab------------------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------  
        #**************************************************************************************************************************************        
    def getfile(self):
        self.fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Single File', 'M:/tnw/ist/do/projects/Neurophotonics/Brinkslab/Data',"Image files (*.jpg *.tif)")
        self.textbox_filename.setText(self.fileName)
        
    def loadtiffile(self):
        print('Loading...')
        self.MessageToMainGUI('Loading...'+'\n')        
        loadtif_thread = loadtif_Thread(self.fileName)
        loadtif_thread.videostack_signal.connect(self.ReceiveVideo)
        loadtif_thread.start()
        loadtif_thread.wait()

    def ReceiveVideo(self, videosentin):  

        self.videostack = videosentin
        print(self.videostack.shape)
        self.MessageToMainGUI('Video size: '+str(self.videostack.shape)+'\n')
        self.roi_average.maxBounds= QRectF(0,0,self.videostack.shape[2],self.videostack.shape[1])
        self.roi_weighted.maxBounds= QRectF(0,0,self.videostack.shape[2],self.videostack.shape[1])
        print('Loading complete, ready to fire')
        self.MessageToMainGUI('Loading complete, ready to fire'+'\n')
        
    def loadcurve(self, filepath):
        for file in os.listdir(os.path.dirname(self.fileName)):
            if file.endswith(".Ip"):
                self.Ipfilename = os.path.dirname(self.fileName) + '/'+file
                curvereadingobjective_i =  readbinaryfile(self.Ipfilename)               
                self.Ip, self.samplingrate_curve = curvereadingobjective_i.readbinarycurve()                
                
            elif file.endswith(".Vp"):
                self.Vpfilename = os.path.dirname(self.fileName) + '/'+file
                curvereadingobjective_V =  readbinaryfile(self.Vpfilename)               
                self.Vp, self.samplingrate_curve = curvereadingobjective_V.readbinarycurve()                
                
            elif file.startswith('Vp'):
                self.Vpfilename_npy = os.path.dirname(self.fileName) + '/'+file
                curvereadingobjective_V =  np.load(self.Vpfilename_npy)
                self.Vp = curvereadingobjective_V[5:len(curvereadingobjective_V)]
                self.samplingrate_curve = curvereadingobjective_V[0]
                
            elif file.startswith('Ip'):
                self.Ipfilename_npy = os.path.dirname(self.fileName) + '/'+file
                curvereadingobjective_I =  np.load(self.Ipfilename_npy)
                self.Ip = curvereadingobjective_I[5:len(curvereadingobjective_I)]
                self.samplingrate_curve = curvereadingobjective_I[0]
            elif 'Wavefroms_sr_' in file:
                self.Waveform_filename_npy = os.path.dirname(self.fileName) + '/'+file
                # Read in configured waveforms
                configwave_wavenpfileName = self.Waveform_filename_npy
                self.waveform_display_temp_loaded_container = np.load(configwave_wavenpfileName, allow_pickle=True)
                self.samplingrate_display_curve = int(float(configwave_wavenpfileName[configwave_wavenpfileName.find('sr_')+3:-4]))
                
    def getfile_background(self):
        self.fileName_background, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Single File', 'M:/tnw/ist/do/projects/Neurophotonics/Brinkslab/Data',"Image files (*.jpg *.tif)")
        self.textbox_Background_filename.setText(self.fileName_background)
        
    def substract_background(self):
        print('Loading...')
        if self.switch_bg_Video_or_image.currentText() == 'Video':
            self.videostack_background = imread(self.fileName_background)
            print(self.videostack_background.shape)
            self.videostack = self.videostack - self.videostack_background
            print('Substraction complete.')
        elif self.switch_bg_Video_or_image.currentText() == 'ROI':
            unique, counts = np.unique(self.averageimage_ROI_mask,return_counts=True)
            count_dict = dict(zip(unique, counts))
            print('number of 1 and 0:'+str(count_dict))
            for i in range(self.videostack.shape[0]):
                ROI_bg = self.videostack[i][self.roi_avg_coord_raw_start:self.roi_avg_coord_raw_start+self.averageimage_ROI_mask.shape[0], self.roi_avg_coord_col_start:self.roi_avg_coord_col_start+self.averageimage_ROI_mask.shape[1]] * self.averageimage_ROI_mask
                bg_mean = np.sum(ROI_bg)/count_dict[1] # Sum of all pixel values and devided by non-zero pixel number
                self.videostack[i] = np.where(self.videostack[i] - bg_mean < 0, 0, self.videostack[i] - bg_mean)
            print('ROI background correction done.')

    def displayElectricalsignal(self):
        if self.switch_Vp_or_camtrace.currentText() == 'With Vp':
            self.patchcurrentlabel = np.arange(len(self.Ip))/self.samplingrate_curve
            
            self.PlotDataItem_patchcurrent = PlotDataItem(self.patchcurrentlabel, self.Ip*1000/self.OC)
            self.PlotDataItem_patchcurrent.setPen('b')
            self.pw_patch_current.addItem(self.PlotDataItem_patchcurrent)
            
            self.patchvoltagelabel = np.arange(len(self.Vp))/self.samplingrate_curve
            
            self.PlotDataItem_patchvoltage = PlotDataItem(self.patchvoltagelabel, self.Vp*1000/10)
            self.PlotDataItem_patchvoltage.setPen('w')
            self.pw_patch_voltage.addItem(self.PlotDataItem_patchvoltage)
        else:
            pass
            
    def displayConfiguredWaveform(self):
        try:
            reference_length=len(self.waveform_display_temp_loaded_container[0]['Waveform'])
            self.time_xlabel_all_waveform = np.arange(reference_length)/self.samplingrate_display_curve
            
            for i in range(len(self.waveform_display_temp_loaded_container)):
                if self.waveform_display_temp_loaded_container[i]['Sepcification'] == '640AO':
                    self.display_finalwave_640AO = self.waveform_display_temp_loaded_container[i]['Waveform']
                    self.display_PlotDataItem_640AO = PlotDataItem(self.time_xlabel_all_waveform, self.display_finalwave_640AO, downsample = 10)
                    self.display_PlotDataItem_640AO.setPen('r')
                    #self.Display_PlotDataItem_640AO.setDownsampling(ds=(int(self.textboxAA.value())/10), method='mean')
                    self.pw_preset_waveform.addItem(self.display_PlotDataItem_640AO)
                    
                    self.displaytextitem_640AO = pg.TextItem(text='640 AO', color=('r'), anchor=(0, 0))
                    self.displaytextitem_640AO.setPos(1, 4)
                    self.pw_preset_waveform.addItem(self.displaytextitem_640AO)
                if self.waveform_display_temp_loaded_container[i]['Sepcification'] == '488AO':
                    self.display_finalwave_488AO = self.waveform_display_temp_loaded_container[i]['Waveform']
                    self.display_PlotDataItem_488AO = PlotDataItem(self.time_xlabel_all_waveform, self.display_finalwave_488AO, downsample = 10)
                    self.display_PlotDataItem_488AO.setPen('b')
                    #self.Display_PlotDataItem_640AO.setDownsampling(ds=(int(self.textboxAA.value())/10), method='mean')
                    self.pw_preset_waveform.addItem(self.display_PlotDataItem_488AO)
                    
                    self.displaytextitem_488AO = pg.TextItem(text='488 AO', color=('b'), anchor=(0, 0))
                    self.displaytextitem_488AO.setPos(1, 2)
                    self.pw_preset_waveform.addItem(self.displaytextitem_488AO)
                if self.waveform_display_temp_loaded_container[i]['Sepcification'] == 'Perfusion_8':
                    self.display_finalwave_Perfusion_8 = self.waveform_display_temp_loaded_container[i]['Waveform']
                    self.display_PlotDataItem_Perfusion_8 = PlotDataItem(self.time_xlabel_all_waveform, self.display_finalwave_Perfusion_8, downsample = 10)
                    self.display_PlotDataItem_Perfusion_8.setPen(154,205,50)
                    #self.Display_PlotDataItem_640AO.setDownsampling(ds=(int(self.textboxAA.value())/10), method='mean')
                    self.pw_preset_waveform.addItem(self.display_PlotDataItem_Perfusion_8)
                    
                    self.displaytextitem_Perfusion_8 = pg.TextItem(text='Perfusion_8', color=(154,205,50), anchor=(0, 0))
                    self.displaytextitem_Perfusion_8.setPos(1, -6)
                    self.pw_preset_waveform.addItem(self.displaytextitem_Perfusion_8)
                if self.waveform_display_temp_loaded_container[i]['Sepcification'] == 'Perfusion_7':
                    self.display_finalwave_Perfusion_7 = self.waveform_display_temp_loaded_container[i]['Waveform']
                    self.display_PlotDataItem_Perfusion_7 = PlotDataItem(self.time_xlabel_all_waveform, self.display_finalwave_Perfusion_7, downsample = 10)
                    self.display_PlotDataItem_Perfusion_7.setPen(127,255,212)
                    #self.Display_PlotDataItem_640AO.setDownsampling(ds=(int(self.textboxAA.value())/10), method='mean')
                    self.pw_preset_waveform.addItem(self.display_PlotDataItem_Perfusion_7)
                    
                    self.displaytextitem_Perfusion_7 = pg.TextItem(text='Perfusion_7', color=(127,255,212), anchor=(0, 0))
                    self.displaytextitem_Perfusion_7.setPos(1, -5)
                    self.pw_preset_waveform.addItem(self.displaytextitem_Perfusion_7)
        except:
            pass
        
    def showpointdata(self):
        try:
            self.pw_patch_current.removeItem(self.currenttextitem)
        except:
            self.currenttextitem=pg.TextItem(text='0',color=(255,204,255), anchor=(0, 1))
            self.currenttextitem.setPos(round(self.vLine.value(), 2), 0)
            self.pw_patch_current.addItem(self.currenttextitem)
            
            index = (np.abs(np.arange(len(self.Ip))-self.vLine.value()*self.samplingrate_curve)).argmin()
            
            self.currenttextitem.setText(str(round(self.vLine.value(), 2))+' s,I='+str(round(self.Ip[int(index)]*1000/self.OC, 2))+' pA')
        else:
            self.currenttextitem=pg.TextItem(text='0',color=(255,204,255), anchor=(0, 1))
            self.currenttextitem.setPos(round(self.vLine.value(), 2), 0)
            self.pw_patch_current.addItem(self.currenttextitem)
            
            index = (np.abs(np.arange(len(self.Ip))-self.vLine.value()*self.samplingrate_curve)).argmin()
            
            self.currenttextitem.setText(str(round(self.vLine.value(), 2))+' s,I='+str(round(self.Ip[int(index)]*1000/self.OC, 2))+' pA')    

    def showpointdata_camtrace(self):
        if self.line_cam_trace_selection == 1:
            try:
                self.pw_patch_camtrace.removeItem(self.camtracetextitem)
            except:
                self.camtracetextitem=pg.TextItem(text='0',color=(255,204,255), anchor=(0, 1))
                self.camtracetextitem.setPos(round(self.vLine_cam.value(), 2), 0)
                self.pw_patch_camtrace.addItem(self.camtracetextitem)
                
                index = (np.abs(np.arange(len(self.camsignalsum))-self.vLine_cam.value()*self.samplingrate_cam)).argmin()
                
                self.camtracetextitem.setText('Sum of pixel values:'+str(self.camsignalsum[int(index)]))
            else:
                self.camtracetextitem=pg.TextItem(text='0',color=(255,204,255), anchor=(0, 1))
                self.camtracetextitem.setPos(round(self.vLine_cam.value(), 2), 0)
                self.pw_patch_camtrace.addItem(self.camtracetextitem)
                
                index = (np.abs(np.arange(len(self.camsignalsum))-self.vLine_cam.value()*self.samplingrate_cam)).argmin()
                
                self.camtracetextitem.setText('Sum of pixel values:'+str(self.camsignalsum[int(index)]))
        else:
            try:
                self.pw_patch_camtrace.removeItem(self.camtracetextitem)
            except:
                self.camtracetextitem=pg.TextItem(text='0',color=(255,204,255), anchor=(0, 1))
                self.camtracetextitem.setPos(round(self.vLine_cam.value(), 2), 0)
                self.pw_patch_camtrace.addItem(self.camtracetextitem)
                
                index = (np.abs(np.arange(len(self.weighttrace_data))-self.vLine_cam.value()*self.samplingrate_cam)).argmin()
                
                self.camtracetextitem.setText('Weighted trace:'+str(self.weighttrace_data[int(index)]))
            else:
                self.camtracetextitem=pg.TextItem(text='0',color=(255,204,255), anchor=(0, 1))
                self.camtracetextitem.setPos(round(self.vLine_cam.value(), 2), 0)
                self.pw_patch_camtrace.addItem(self.camtracetextitem)
                
                index = (np.abs(np.arange(len(self.weighttrace_data))-self.vLine_cam.value()*self.samplingrate_cam)).argmin()
                
                self.camtracetextitem.setText('Weighted trace:'+str(self.weighttrace_data[int(index)]))
    
    def displaycamtrace(self):
        self.line_cam_trace_selection = 1
        self.line_cam_weightedtrace_selection = 0
        
        self.samplingrate_cam = self.Spincamsamplingrate.value()
        
        self.camsignalsum = np.zeros(len(self.videostack))
        for i in range(len(self.videostack)):
            self.camsignalsum[i] = np.sum(self.videostack[i])
            
        self.patchcamtracelabel = np.arange(len(self.camsignalsum))/self.samplingrate_cam
        
        self.PlotDataItem_patchcam = PlotDataItem(self.patchcamtracelabel, self.camsignalsum, name = 'Pixel sum trace')
        self.PlotDataItem_patchcam.setPen('w')
        self.pw_patch_camtrace.addItem(self.PlotDataItem_patchcam)        
        
    def Matdisplay_plot(self):
        self.Nest_data_directory = str(QtWidgets.QFileDialog.getExistingDirectory())
        self.Curvedisplay_savedirectorytextbox.setText(self.Nest_data_directory)
        
    def matdisplay_draw(self):
        self.Nest_data_directory = self.Curvedisplay_savedirectorytextbox.text()
        get_ipython().run_line_magic('matplotlib', 'qt')
        
        self.cam_trace_fluorescence_dictionary = {}
        self.cam_trace_fluorescence_filename_dictionary = {}
        self.region_file_name = []
        
        for file in os.listdir(self.Nest_data_directory):
            if 'Wavefroms_sr_' in file:
                self.wave_fileName = os.path.join(self.Nest_data_directory, file)
            elif file.endswith('csv'): # Quick dirty fix
                self.recorded_cam_fileName = os.path.join(self.Nest_data_directory, file)
                
                self.samplingrate_cam = self.Spincamsamplingrate.value()
                self.cam_trace_time_label = np.array([])
                self.cam_trace_fluorescence_value = np.array([])
                
                with open(self.recorded_cam_fileName, newline='') as csvfile:
                    spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
                    for column in spamreader:
                        coords = column[0].split(",")
                        if coords[0] != 'X': # First row and column is 'x, y'
                            self.cam_trace_time_label = np.append(self.cam_trace_time_label, int(coords[0]))
                            self.cam_trace_fluorescence_value = np.append(self.cam_trace_fluorescence_value, float(coords[1]))
                self.cam_trace_fluorescence_dictionary["region_{0}".format(len(self.region_file_name)+1)] = self.cam_trace_fluorescence_value
                self.cam_trace_fluorescence_filename_dictionary["region_{0}".format(len(self.region_file_name)+1)] = file
                self.region_file_name.append(file)
            elif 'Vp' in file:
                self.recorded_wave_fileName = os.path.join(self.Nest_data_directory, file)

        # Read in configured waveforms
        configwave_wavenpfileName = self.wave_fileName#r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Patch clamp\2019-11-29 patch-perfusion-Archon1\trial-1\perfusion2\2019-11-29_15-51-16__Wavefroms_sr_100.npy'
        temp_loaded_container = np.load(configwave_wavenpfileName, allow_pickle=True)

        Daq_sample_rate = int(float(configwave_wavenpfileName[configwave_wavenpfileName.find('sr_')+3:-4]))
        
        self.Checked_display_list = ['Waveform']
        if self.checkboxTrace.isChecked():
            self.Checked_display_list = np.append(self.Checked_display_list, 'Recorded_trace')
        if self.checkboxCam.isChecked():
            self.Checked_display_list = np.append(self.Checked_display_list, 'Cam_trace')
        
#            Vm_diff = round(np.mean(Vm[100:200]) - np.mean(Vm[-200:-100]), 2)
        
        reference_length=len(temp_loaded_container[0]['Waveform'])
        xlabel_all = np.arange(reference_length)/Daq_sample_rate
        
        #plt.figure()
        if len(self.Checked_display_list) == 2:
            ax1 = self.Matdisplay_figure.add_subplot(211)
            ax2 = self.Matdisplay_figure.add_subplot(212)
#                self.Matdisplay_figure, (ax1, ax2) = plt.subplots(2, 1)
        elif len(self.Checked_display_list) == 3:
#                self.Matdisplay_figure, (ax1, ax2, ax3) = plt.subplots(3, 1)
            ax1 = self.Matdisplay_figure.add_subplot(221)
            ax2 = self.Matdisplay_figure.add_subplot(222)
            ax3 = self.Matdisplay_figure.add_subplot(223)
        for i in range(len(temp_loaded_container)):
            if temp_loaded_container[i]['Sepcification'] == '640AO':
                ax1.plot(xlabel_all, temp_loaded_container[i]['Waveform'], label='640AO', color='r')
            elif temp_loaded_container[i]['Sepcification'] == '488AO':
                ax1.plot(xlabel_all, temp_loaded_container[i]['Waveform'], label='488AO', color='b')
            elif temp_loaded_container[i]['Sepcification'] == 'Perfusion_8':
                ax1.plot(xlabel_all, temp_loaded_container[i]['Waveform'], label='KCL')
            elif temp_loaded_container[i]['Sepcification'] == 'Perfusion_7':
                ax1.plot(xlabel_all, temp_loaded_container[i]['Waveform'], label='EC')
            elif temp_loaded_container[i]['Sepcification'] == 'Perfusion_2':
                ax1.plot(xlabel_all, temp_loaded_container[i]['Waveform'], label='Suction')
        ax1.set_title('Output waveforms')        
        ax1.set_xlabel('time(s)')
        ax1.set_ylabel('Volt')
        ax1.legend()

        if 'Recorded_trace' in self.Checked_display_list:
    #        plt.yticks(np.round(np.arange(min(Vm), max(Vm), 0.05), 2))      
            # Read in recorded waves
            Readin_fileName = self.recorded_wave_fileName#r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Patch clamp\2019-11-29 patch-perfusion-Archon1\trial-2\Vp2019-11-29_17-31-18.npy'
            
            if 'Vp' in os.path.split(Readin_fileName)[1]: # See which channel is recorded
                Vm = np.load(Readin_fileName, allow_pickle=True)
                Vm = Vm[4:-1]# first 5 are sampling rate, Daq coffs
                Vm[0]=Vm[1]
            
            ax2.set_xlabel('time(s)')        
            ax2.set_title('Recording')
            ax2.set_ylabel('V (Vm*10)')
            ax2.plot(xlabel_all, Vm, label = 'Vm')
            #ax2.annotate('Vm diff = '+str(Vm_diff*100)+'mV', xy=(0, max(Vm)-0.1))        
            ax2.legend()
        elif 'Recorded_trace' not in self.Checked_display_list and len(self.Checked_display_list) == 2:
            ax2.plot(self.cam_trace_time_label/self.samplingrate_cam, self.cam_trace_fluorescence_dictionary["region_{0}".format(0+1)], label = 'Fluorescence')
            ax2.set_xlabel('time(s)')        
            ax2.set_title('ROI Fluorescence')#+' ('+str(self.cam_trace_fluorescence_filename_dictionary["region_{0}".format(region_number+1)])+')')
            ax2.set_ylabel('CamCounts')
            ax2.legend()
            
        if len(self.Checked_display_list) == 3:
            ax3.plot(self.cam_trace_time_label/self.samplingrate_cam, self.cam_trace_fluorescence_dictionary["region_{0}".format(0+1)], label = 'Fluorescence')
            ax3.set_xlabel('time(s)')        
            ax3.set_title('ROI Fluorescence')#+' ('+str(self.cam_trace_fluorescence_filename_dictionary["region_{0}".format(region_number+1)])+')')
            ax3.set_ylabel('CamCounts')
            ax3.legend()
        #plt.autoscale(enable=True, axis="y", tight=False)
        self.Matdisplay_figure.tight_layout()
        self.Matdisplay_figure_canvas.draw()
        #get_ipython().run_line_magic('matplotlib', 'inline')
        
    def matdisplay_clear(self):
        self.Matdisplay_figure.clear()
        
    def calculateaverage(self):
        self.imganalysis_averageimage = np.mean(self.videostack, axis = 0)
        self.pw_averageimage.setImage(self.imganalysis_averageimage)
        #self.pw_averageimage.average_imgItem.setImage(self.imganalysis_averageimage)
    
    def calculateaverage_bg(self):
        self.averageimage_imageitem = self.pw_averageimage.getImageItem()
        self.averageimage_ROI = self.roi_average.getArrayRegion(self.imganalysis_averageimage, self.averageimage_imageitem)
        self.averageimage_ROI_mask = np.where(self.averageimage_ROI > 0, 1, 0)
        
        #self.roi_average_pos = self.roi_average.pos()
        self.roi_average_Bounds = self.roi_average.parentBounds()
        self.roi_avg_coord_col_start = round(self.roi_average_Bounds.topLeft().x())
        self.roi_avg_coord_col_end = round(self.roi_average_Bounds.bottomRight().x())
        self.roi_avg_coord_raw_start = round(self.roi_average_Bounds.topLeft().y())
        self.roi_avg_coord_raw_end = round(self.roi_average_Bounds.bottomRight().y())

        #print(self.roi_average_pos)
#        plt.figure()
#        plt.imshow(self.averageimage_ROI_mask, cmap = plt.cm.gray)
#        plt.show()
        
#        plt.figure()
#        plt.imshow(self.imganalysis_averageimage[self.roi_coord_raw_start:self.roi_coord_raw_end, self.roi_coord_col_start:self.roi_coord_col_end], cmap = plt.cm.gray)
#        plt.show()
        
#        print(self.averageimage_ROI[13:15,13:15])
#        print(self.imganalysis_averageimage[self.roi_coord_raw_start:self.roi_coord_raw_end, self.roi_coord_col_start:self.roi_coord_col_end][13:15,13:15])
    
    def calculateweight(self):        
        if self.switch_Vp_or_camtrace.currentText() == 'With Vp':
            self.samplingrate_cam = self.Spincamsamplingrate.value()
            self.downsample_ratio = int(self.samplingrate_curve/self.samplingrate_cam)            
            self.Vp_downsample = self.Vp.reshape(-1, self.downsample_ratio).mean(axis=1)
            
            self.Vp_downsample = self.Vp_downsample[0:len(self.videostack)]
            
            weight_ins = extractV(self.videostack, self.Vp_downsample*1000/10)
            self.corrimage, self.weightimage, self.sigmaimage= weight_ins.cal()
    
            self.pw_weightimage.setImage(self.weightimage)
            
        elif self.switch_Vp_or_camtrace.currentText() == 'Camera trace':
            weight_ins = extractV(self.videostack, self.camsignalsum*1000/10)
            self.corrimage, self.weightimage, self.sigmaimage= weight_ins.cal()
    
            self.pw_weightimage.setImage(self.weightimage)
        #print(self.pw_weightimage.levelMax)
        #print(self.pw_weightimage.levelMin)
        #self.pw_weightimage.weightedimgItem.setImage(self.weightimage)
        #k=self.pw_weightimage.hiswidget_weight.getLevels()
        #print(k)
        
    def displayweighttrace(self):     
        try:
            self.pw_patch_camtrace.removeItem(self.camtracetextitem) # try to remove text besides line, not a good way to do so.
            
            self.line_cam_trace_selection = 0 #This is the vertical line for easy value display
            self.line_cam_weightedtrace_selection = 1
            
            self.samplingrate_cam = self.Spincamsamplingrate.value()
            self.videolength = len(self.videostack)
            self.pw_patch_camtrace.removeItem(self.PlotDataItem_patchcam)      
    
            k=np.tile(self.weightimage/np.sum(self.weightimage)*self.videostack.shape[1]*self.videostack.shape[2], (self.videolength,1,1))# datv = squeeze(mean(mean(mov.*repmat(Wv./sum(Wv(:))*movsize(1)*movsize(2), [1 1 length(sig)]))));
            self.weighttrace_tobetime = self.videostack*k
            
            self.weighttrace_data = np.zeros(self.videolength)
            for i in range(self.videolength):
                self.weighttrace_data[i] = np.mean(self.weighttrace_tobetime[i])
                
            self.patchcamtracelabel_weighted = np.arange(self.videolength)/self.samplingrate_cam
            
            self.PlotDataItem_patchcam_weighted = PlotDataItem(self.patchcamtracelabel_weighted, self.weighttrace_data, name = 'Weighted signal trace')
            self.PlotDataItem_patchcam_weighted.setPen('c')
            self.pw_patch_camtrace.addItem(self.PlotDataItem_patchcam_weighted)       
        except:
            self.line_cam_trace_selection = 0
            self.line_cam_weightedtrace_selection = 1
            
            self.samplingrate_cam = self.Spincamsamplingrate.value()
            self.videolength = len(self.videostack)
            self.pw_patch_camtrace.removeItem(self.PlotDataItem_patchcam)      
    
            k=np.tile(self.weightimage/np.sum(self.weightimage)*self.videostack.shape[1]*self.videostack.shape[2], (self.videolength,1,1))
            self.weighttrace_tobetime = self.videostack*k
            
            self.weighttrace_data = np.zeros(self.videolength)
            for i in range(self.videolength):
                self.weighttrace_data[i] = np.mean(self.weighttrace_tobetime[i])
                
            self.patchcamtracelabel_weighted = np.arange(self.videolength)/self.samplingrate_cam
            
            self.PlotDataItem_patchcam_weighted = PlotDataItem(self.patchcamtracelabel_weighted, self.weighttrace_data, name = 'Weighted signal trace')
            self.PlotDataItem_patchcam_weighted.setPen('c')
            self.pw_patch_camtrace.addItem(self.PlotDataItem_patchcam_weighted)
            
            
    def displayROIweighttrace(self):
        print('Under construction!')
        try:
            self.pw_patch_camtrace.removeItem(self.camtracetextitem) # try to remove text besides line, not a good way to do so.
            
            self.line_cam_trace_selection = 0
            self.line_cam_weightedtrace_selection = 1
            
            self.samplingrate_cam = self.Spincamsamplingrate.value()
            self.videolength = len(self.videostack)
            self.pw_patch_camtrace.removeItem(self.PlotDataItem_patchcam)      
            
            self.weightimage_imageitem = self.pw_weightimage.getImageItem()
            self.weightimage_ROI = self.roi_weighted.getArrayRegion(self.weightimage, self.weightimage_imageitem)
            k=np.tile(self.weightimage_ROI/np.sum(self.weightimage_ROI)*self.videostack.shape[1]*self.videostack.shape[2], (self.videolength,1,1)) #itrace = squeeze(sum(sum(movie_in.*repmat(inpoly, [1, 1, nframes]))))/sum(inpoly(:));
            self.weighttrace_tobetime = self.videostack*k 
            
            self.weighttrace_data = np.zeros(self.videolength)
            for i in range(self.videolength):
                self.weighttrace_data[i] = np.mean(self.weighttrace_tobetime[i])
                
            self.patchcamtracelabel_weighted = np.arange(self.videolength)/self.samplingrate_cam
            
            self.PlotDataItem_patchcam_weighted = PlotDataItem(self.patchcamtracelabel_weighted, self.weighttrace_data, name = 'Weighted signal trace')
            self.PlotDataItem_patchcam_weighted.setPen('c')
            self.pw_patch_camtrace.addItem(self.PlotDataItem_patchcam_weighted)       
        except:
            self.line_cam_trace_selection = 0
            self.line_cam_weightedtrace_selection = 1
            
            self.samplingrate_cam = self.Spincamsamplingrate.value()
            self.videolength = len(self.videostack)
            self.pw_patch_camtrace.removeItem(self.PlotDataItem_patchcam)      
    
            self.weightimage_imageitem = self.pw_weightimage.getImageItem()
            self.weightimage_ROI = self.roi_weighted.getArrayRegion(self.weightimage, self.weightimage_imageitem)
            k=np.tile(self.weightimage_ROI/np.sum(self.weightimage_ROI)*self.videostack.shape[1]*self.videostack.shape[2], (self.videolength,1,1))
            self.weighttrace_tobetime = self.videostack*k
            
            self.weighttrace_data = np.zeros(self.videolength)
            for i in range(self.videolength):
                self.weighttrace_data[i] = np.mean(self.weighttrace_tobetime[i])
                
            self.patchcamtracelabel_weighted = np.arange(self.videolength)/self.samplingrate_cam
            
            self.PlotDataItem_patchcam_weighted = PlotDataItem(self.patchcamtracelabel_weighted, self.weighttrace_data, name = 'Weighted signal trace')
            self.PlotDataItem_patchcam_weighted.setPen('c')
            self.pw_patch_camtrace.addItem(self.PlotDataItem_patchcam_weighted)
        
    def save_analyzed_image(self, catag):
        if catag == 'weight_image':
            Localimg = Image.fromarray(self.weightimage) #generate an image object
            Localimg.save(os.path.join(self.savedirectory, 'Weight_'+ str(self.prefixtextbox.text()) + '_' +datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'.tif')) #save as tif
     
    def export_trace(self):
        if self.switch_export_trace.currentText() == 'Cam trace':
            np.save(os.path.join(self.savedirectory,'Cam_trace'), self.camsignalsum)
        elif self.switch_export_trace.currentText() == 'Weighted trace':
            np.save(os.path.join(self.savedirectory,'Weighted_trace'), self.weighttrace_data)
        
    def clearplots(self):
        self.pw_patch_voltage.clear()
        self.pw_patch_current.clear()
        self.pw_patch_camtrace.clear()
                
        self.vLine_cam = pg.InfiniteLine(pos=0.4, angle=90, movable=True)
        self.pw_patch_camtrace.addItem(self.vLine_cam, ignoreBounds=True)
        self.vLine = pg.InfiniteLine(pos=0.4, angle=90, movable=True)
        self.pw_patch_current.addItem(self.vLine, ignoreBounds=True)
        
        self.vLine.sigPositionChangeFinished.connect(self.showpointdata)
        self.vLine_cam.sigPositionChangeFinished.connect(self.showpointdata_camtrace)

    def MessageToMainGUI(self, text):
        self.MessageBack.emit(text)
        
class loadtif_Thread(QThread):
    videostack_signal = pyqtSignal(np.ndarray)
    def __init__(self, fileName, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fileName = fileName
#        self.xRel = xRel
#        self.yRel = yRel
        
    def run(self):
        videostack = imread(self.fileName)
        self.videostack_signal.emit(videostack)
        
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        pg.setConfigOptions(imageAxisOrder='row-major')
        mainwin = AnalysisWidgetUI()
        mainwin.show()
        app.exec_()
    run_app() 