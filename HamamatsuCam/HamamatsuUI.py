# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 18:47:31 2020

@author: xinmeng
"""

from __future__ import division
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPoint, QRect, QObject, QSize
from PyQt5.QtGui import QImage, QPalette, QBrush, QFont, QPainter, QColor, QPen, QIcon

from PyQt5.QtWidgets import (QWidget, QButtonGroup, QLabel, QSlider, QSpinBox, QDoubleSpinBox, QGridLayout, QPushButton, QGroupBox, 
                             QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox, QTabWidget, QCheckBox, QRadioButton, 
                             QFileDialog, QProgressBar, QTextEdit, QStyleFactory, QMainWindow, QMenu, QAction)
import pyqtgraph as pg
import sys
import numpy as np
import ctypes
import ctypes.util
import skimage.external.tifffile as skimtiff
from HamamatsuDCAM import *

'''
Some general settings for pyqtgraph, these only have to do with appearance 
except for row-major, which inverts the image and puts mirrors some axes.
'''

pg.setConfigOptions(imageAxisOrder='row-major')
pg.setConfigOption('background', 'k')
pg.setConfigOption('foreground', 'w')
pg.setConfigOption('useOpenGL', True)
pg.setConfigOption('leftButtonPan', False)

class CameraUI(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        #----------------------------------------------------------------------
        #----------------------------------GUI---------------------------------
        #----------------------------------------------------------------------
        self.setWindowTitle("Hamamatsu Orca Flash")
        self.setFont(QFont("Arial"))
        self.setMinimumSize(1200,980)
        self.layout = QGridLayout()        
        #----------------Create menu bar and add action------------------------
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&Camera')
        
        ActConnectCamera = QAction(QIcon('.\Icons\on.png'), 'Connect camera', self)
        ActConnectCamera.setShortcut('Ctrl+c')
        ActConnectCamera.setStatusTip('Connect camera')
        ActConnectCamera.triggered.connect(self.ConnectCamera)
        
        ActDisconnectCamera = QAction(QIcon('.\Icons\off.png'), 'Disconnect camera', self)    
        ActDisconnectCamera.setShortcut('Ctrl+d')
        ActDisconnectCamera.triggered.connect(self.DisconnectCamera)
        
        ActListCameraProperties = QAction('List properties', self)    
        ActListCameraProperties.setShortcut('Ctrl+l')
        ActListCameraProperties.triggered.connect(self.ListCameraProperties)
        
        fileMenu.addAction(ActConnectCamera)
        fileMenu.addAction(ActDisconnectCamera)
        fileMenu.addAction(ActListCameraProperties)

        MainWinCentralWidget = QWidget()
        MainWinCentralWidget.layout = QGridLayout()
        """
        # =============================================================================
        #         Camera settings container.
        # =============================================================================
        """
        CameraSettingContainer = QGroupBox('General settings')
        CameraSettingContainer.setMaximumHeight(400)
        CameraSettingContainer.setMaximumWidth(360)
        CameraSettingLayout = QGridLayout()
        
        self.CamStatusLabel = QLabel('Camera not connected.')
        self.CamStatusLabel.setStyleSheet("QLabel { background-color : azure; color : blue; }")
        self.CamStatusLabel.setFixedHeight(30)
        self.CamStatusLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        CameraSettingLayout.addWidget(self.CamStatusLabel, 0, 0, 1, 1)
        
        #----------------------------------------------------------------------
        CameraSettingTab = QTabWidget()
        CameraSettingTab.layout = QGridLayout()
        
        """
        ----------------------------Camera tab---------------------------------
        """
        CameraSettingTab_1 = QWidget()
        CameraSettingTab_1.layout = QGridLayout()
        
        CameraSettingTab_1.layout.addWidget(QLabel("Readout speed:"), 2, 0)
        self.ReadoutSpeedSwitchButton = MySwitch('Normal', 'yellow', 'Fast', 'cyan', width = 50)
        self.ReadoutSpeedSwitchButton.clicked.connect(self.ReadoutSpeedSwitchEvent)
        CameraSettingTab_1.layout.addWidget(self.ReadoutSpeedSwitchButton, 2, 1, 1, 2)
        
        self.DefectCorrectionButton = QPushButton("Pixel correction")
#        self.DefectCorrectionButton.setFixedWidth(100)
        self.DefectCorrectionButton.setCheckable(True)
        self.DefectCorrectionButton.setChecked(True)
        self.DefectCorrectionButton.clicked.connect(self.DefectCorrectionSwitchEvent)
        CameraSettingTab_1.layout.addWidget(self.DefectCorrectionButton, 2, 3)
        
        #----------------------------------------------------------------------
        CameraImageFormatContainer = QGroupBox("Image format")
        CameraImageFormatLayout = QGridLayout()
        
        self.BinningButtongroup = QButtonGroup(self)
        self.BinningButton_1 = QPushButton("1x1")
        self.BinningButton_1.setCheckable(True)
        self.BinningButton_1.setChecked(True)
        self.BinningButtongroup.addButton(self.BinningButton_1, 1)
        self.BinningButton_2 = QPushButton("2x2")
        self.BinningButton_2.setCheckable(True)
        self.BinningButtongroup.addButton(self.BinningButton_2, 2)
        self.BinningButton_4 = QPushButton("4x4")
        self.BinningButton_4.setCheckable(True)
        self.BinningButtongroup.addButton(self.BinningButton_4, 3)
        self.BinningButtongroup.setExclusive(True)
        self.BinningButtongroup.buttonClicked[int].connect(self.SetBinning)
        
        CameraImageFormatLayout.addWidget(QLabel("Binning:"), 0, 0)
        CameraImageFormatLayout.addWidget(self.BinningButton_1, 0, 1)  
        CameraImageFormatLayout.addWidget(self.BinningButton_2, 0, 2) 
        CameraImageFormatLayout.addWidget(self.BinningButton_4, 0, 3)
        
        self.PixelTypeButtongroup = QButtonGroup(self)
        self.PixelTypeButton_1 = QPushButton("8")
        self.PixelTypeButton_1.setCheckable(True)
        self.PixelTypeButtongroup.addButton(self.PixelTypeButton_1, 1)
        self.PixelTypeButton_2 = QPushButton("12")
        self.PixelTypeButton_2.setCheckable(True)
        self.PixelTypeButtongroup.addButton(self.PixelTypeButton_2, 2)
        self.PixelTypeButton_3 = QPushButton("16")
        self.PixelTypeButton_3.setCheckable(True)
        self.PixelTypeButton_3.setChecked(True)
        self.PixelTypeButtongroup.addButton(self.PixelTypeButton_3, 3)
        self.PixelTypeButtongroup.setExclusive(True)
        self.PixelTypeButtongroup.buttonClicked[int].connect(self.SetPixelType)
        
        CameraImageFormatLayout.addWidget(QLabel("Pixel type:"), 1, 0)
        CameraImageFormatLayout.addWidget(self.PixelTypeButton_1, 1, 1)  
        CameraImageFormatLayout.addWidget(self.PixelTypeButton_2, 1, 2) 
        CameraImageFormatLayout.addWidget(self.PixelTypeButton_3, 1, 3)
        
        CameraImageFormatContainer.setLayout(CameraImageFormatLayout)
        CameraImageFormatContainer.setFixedHeight(100)
        CameraSettingTab_1.layout.addWidget(CameraImageFormatContainer, 0, 0, 1, 4)
        
        #----------------------------------------------------------------------
        self.CamExposureBox = QDoubleSpinBox(self)
        self.CamExposureBox.setDecimals(6)
        self.CamExposureBox.setMinimum(0)
        self.CamExposureBox.setMaximum(100)
        self.CamExposureBox.setValue(0.001501)
        self.CamExposureBox.setSingleStep(0.001)  
        CameraSettingTab_1.layout.addWidget(self.CamExposureBox, 4, 2, 1, 2)  
        CameraSettingTab_1.layout.addWidget(QLabel("Exposure time:"), 4, 0, 1, 2)
        
        self.CamExposureBox.setKeyboardTracking(False)
        self.CamExposureBox.valueChanged.connect(self.SetExposureTime)
        #----------------------------------------------------------------------
        
        CameraSettingTab_1.setLayout(CameraSettingTab_1.layout)
        
        """
        -----------------------------------ROI tab-----------------------------
        """
        CameraSettingTab_2 = QWidget()
        CameraSettingTab_2.layout = QGridLayout()
        
        CameraSettingTab_2.layout.addWidget(QLabel("Sub Array:"), 0, 0)
        self.SubArrayModeSwitchButton = MySwitch('Sub Array Mode', 'lemon chiffon', 'Full Image Size', 'lavender', width = 100)
        self.SubArrayModeSwitchButton.setChecked(False)
        self.SubArrayModeSwitchButton.clicked.connect(self.SubArrayModeSwitchEvent)
        CameraSettingTab_2.layout.addWidget(self.SubArrayModeSwitchButton, 0, 1, 1, 3)
        
        # Adapted from Douwe's ROI part.
        self.center_roiButton = QPushButton()
        self.center_roiButton.setText("Symmetric to Center Line")        
#        self.center_roiButton.clicked.connect(lambda: self.set_roi_flag())
        '''
        set_roi_flag checks whether the centering button is pushed and 
        acts accordingly.
        '''
        self.center_roiButton.setCheckable(True)
        CameraSettingTab_2.layout.addWidget(self.center_roiButton, 1, 1, 1, 3)
        '''
        The ROI needs to be centered to maximise the framerate of the hamamatsu
        CMOS. When not centered it will count the outermost vertical pixel and
        treats it as the size of the ROI. See the camera manual for a more 
        detailed explanation.
        '''
        
        self.ShowROISelectorButton = QPushButton()
        self.ShowROISelectorButton.setText("Show ROI Selector")
        self.ShowROISelectorButton.clicked.connect(self.ShowROISelector)
        self.ShowROISelectorButton.setCheckable(True)
        CameraSettingTab_2.layout.addWidget(self.ShowROISelectorButton, 2, 1, 1, 3)
        
        #----------------------------------------------------------------------
        CameraROIPosContainer = QGroupBox("ROI position")
        CameraROIPosLayout = QGridLayout()
        
        CameraROIPosLayout.addWidget(QLabel("Offset"), 0, 1)
        CameraROIPosLayout.addWidget(QLabel("Size"), 0, 2)
        
        self.x_position = QSpinBox()
        self.x_position.setMaximum(2048)
        self.x_position.setValue(0)
        self.x_position.valueChanged.connect(self.spin_value_changed)
        CameraROIPosLayout.addWidget(self.x_position, 1, 1)
        
        self.y_position = QSpinBox()
        self.y_position.setMaximum(2048)
        self.y_position.setValue(0)
        self.x_position.valueChanged.connect(self.spin_value_changed)
        CameraROIPosLayout.addWidget(self.y_position, 2, 1)
        
        self.x_size = QSpinBox()
        self.x_size.setMaximum(2048)
        self.x_size.setValue(2048)
        self.x_position.valueChanged.connect(self.spin_value_changed)
        CameraROIPosLayout.addWidget(self.x_size, 1, 2)
        
        self.y_size = QSpinBox()
        self.y_size.setMaximum(2048)
        self.y_size.setValue(2048)
        self.x_position.valueChanged.connect(self.spin_value_changed)
        CameraROIPosLayout.addWidget(self.y_size, 2, 2)
        
        CameraROIPosLayout.addWidget(QLabel("Horizontal"), 1, 0)
        CameraROIPosLayout.addWidget(QLabel("Vertical"), 2, 0)
        
        CameraROIPosContainer.setLayout(CameraROIPosLayout)
        CameraROIPosContainer.setFixedHeight(120)
        CameraSettingTab_2.layout.addWidget(CameraROIPosContainer, 3, 0, 1, 4)
        
        self.ApplyROIButton = QPushButton()
        self.ApplyROIButton.setText("Apply ROI")
        self.ApplyROIButton.clicked.connect(self.SetROI)
        CameraSettingTab_2.layout.addWidget(self.ApplyROIButton, 4, 0, 1, 2)
        
        self.ClearROIButton = QPushButton()
        self.ClearROIButton.setText("Clear ROI")
        
        CameraSettingTab_2.layout.addWidget(self.ClearROIButton, 4, 2, 1, 2)
        
        CameraSettingTab_2.setLayout(CameraSettingTab_2.layout)        
        
        """
        --------------------------------Timing tab-----------------------------
        """
        CameraSettingTab_3 = QWidget()
        CameraSettingTab_3.layout = QGridLayout()

        CameraSettingTab_3.setLayout(CameraSettingTab_3.layout)        
        #----------------------------------------------------------------------
        CameraSettingTab.addTab(CameraSettingTab_1,"Camera") 
        CameraSettingTab.addTab(CameraSettingTab_2,"ROI")
        CameraSettingTab.addTab(CameraSettingTab_3,"Timing")
        CameraSettingLayout.addWidget(CameraSettingTab, 1, 0, 1, 1)
        
        CameraSettingContainer.setLayout(CameraSettingLayout)
        MainWinCentralWidget.layout.addWidget(CameraSettingContainer, 0, 0)
        
        """
        # =============================================================================
        #         Camera acquisition container.
        # =============================================================================
        """

        CameraAcquisitionContainer = QGroupBox('Acquisition settings')
        CameraAcquisitionContainer.setMaximumHeight(430)
        CameraAcquisitionContainer.setMaximumWidth(360)
        CameraAcquisitionLayout = QGridLayout()
        
        
        
        CameraAcquisitionContainer.setLayout(CameraAcquisitionLayout)
        MainWinCentralWidget.layout.addWidget(CameraAcquisitionContainer, 1, 0)
        
        """
        # =============================================================================
        # --------------------------------Livescreen---------------------------------
        #   Initiating an imageview object for the main Livescreen. Hiding the pre
        # existing ROI and menubuttons.
        # =============================================================================        
        """
        LiveWidgetContainer = QGroupBox()
        LiveWidgetContainer.setMaximumHeight(900)
        LiveWidgetContainer.setMaximumWidth(950)
        LiveWidgetLayout = QGridLayout()
        
        self.LiveWidget = pg.ImageView()
        self.Live_item = self.LiveWidget.getImageItem()
        self.Live_view = self.LiveWidget.getView()
        self.Live_item.setAutoDownsample(True)
        self.LiveWidget.ui.roiBtn.hide()
        self.LiveWidget.ui.menuBtn.hide() 
        self.LiveWidget.ui.normGroup.hide()
        self.LiveWidget.ui.roiPlot.hide()
        
        LiveWidgetLayout.addWidget(self.LiveWidget, 1, 0)
        
        LiveWidgetContainer.setLayout(LiveWidgetLayout)
        MainWinCentralWidget.layout.addWidget(LiveWidgetContainer, 0, 1, 2, 2)
        
        MainWinCentralWidget.setLayout(MainWinCentralWidget.layout)
        self.setCentralWidget(MainWinCentralWidget)
        
        #----------------Once open GUI, try to connect the camera--------------
        try:
            self.ConnectCamera()
        except:
            pass
    
    
    
    def ConnectCamera(self):
        """
        # =============================================================================
        #         Initialization of the camera.
        #         Load dcamapi.dll version: 19.12.641.5901
        # =============================================================================
        """
        dcam = ctypes.WinDLL(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\People\Xin Meng\Code\Python_test\HamamatsuCam\19_12\dcamapi.dll')
        
        paraminit = DCAMAPI_INIT(0, 0, 0, 0, None, None) 
        paraminit.size = ctypes.sizeof(paraminit)
        error_code = dcam.dcamapi_init(ctypes.byref(paraminit))
        #if (error_code != DCAMERR_NOERROR):
        #    raise DCAMException("DCAM initialization failed with error code " + str(error_code))
        
        n_cameras = paraminit.iDeviceCount
    
        print("found:", n_cameras, "cameras")
        
        if (n_cameras > 0):
            #------------------------Initialization----------------------------
            self.hcam = HamamatsuCameraMR(camera_id = 0)
            
            # Enable defect correction
            self.hcam.setPropertyValue("defect_correct_mode", 2)
            self.CamStatusLabel.setText(self.hcam.getModelInfo(0))
            # Set the readout speed to fast.
            self.hcam.setPropertyValue("readout_speed", 2)
            # Set the binning to 1.
            self.hcam.setPropertyValue("binning", "1x1")
            # Get current exposure time and set to the spinbox
            self.CamExposureTime = self.hcam.getPropertyValue("exposure_time")[0]
            self.CamExposureBox.setValue(round(self.CamExposureTime, 6))
            
            params = ["internal_frame_rate",
                      "timing_readout_time",
                      "exposure_time",
                      "subarray_hsize",
                      "subarray_hpos",
                      "subarray_vsize",
                      "subarray_vpos",
                      "subarray_mode"]

            #                      "image_height",
            #                      "image_width",
            #                      "image_framebytes",
            #                      "buffer_framebytes",
            #                      "buffer_rowbytes",
            #                      "buffer_top_offset_bytes",
            #                      "subarray_hsize",
            #                      "subarray_vsize",
            #                      "binning"]
            for param in params:
                if param == "subarray_hsize":
                    self.subarray_hsize = self.hcam.getPropertyValue(param)[0]
                    self.x_size.setValue(self.subarray_hsize)
                if param == "subarray_hpos":
                    self.subarray_hpos = self.hcam.getPropertyValue(param)[0]   
                    self.x_position.setValue(self.subarray_hpos)
                if param == "subarray_vsize":
                    self.subarray_vsize = self.hcam.getPropertyValue(param)[0]
                    self.y_size.setValue(self.subarray_vsize)
                if param == "subarray_vpos":
                    self.subarray_vpos = self.hcam.getPropertyValue(param)[0]
                    self.y_position.setValue(self.subarray_vpos)
                    
            if self.subarray_hsize == 2048 and self.subarray_vsize == 2048:
                self.hcam.setPropertyValue("subarray_mode", "OFF")
                self.SubArrayModeSwitchButton.setChecked(False)
            else:
                self.hcam.setPropertyValue("subarray_mode", "ON")
                self.SubArrayModeSwitchButton.setChecked(True)                
                    
    def DisconnectCamera(self):
        self.hcam.shutdown()
        dcam.dcamapi_uninit()
        self.CamStatusLabel.setText('Camera disconnected.')
        
    def ListCameraProperties(self):
        
        print("Supported properties:")
        props = self.hcam.getProperties()
        for i, id_name in enumerate(sorted(props.keys())):
            [p_value, p_type] = self.hcam.getPropertyValue(id_name)
            p_rw = self.hcam.getPropertyRW(id_name)
            read_write = ""
            if (p_rw[0]):
                read_write += "read"
            if (p_rw[1]):
                read_write += ", write"
            print("  ", i, ")", id_name, " = ", p_value, " type is:", p_type, ",", read_write)
            text_values = self.hcam.getPropertyText(id_name)
            if (len(text_values) > 0):
                print("          option / value")
                for key in sorted(text_values, key = text_values.get):
                    print("         ", key, "/", text_values[key])
                    
    def ReadoutSpeedSwitchEvent(self):
        """
        Set the readout speed. Default is fast, corresponding to 2 in "readout_speed".
        """
        if self.ReadoutSpeedSwitchButton.isChecked():
            self.hcam.setPropertyValue("defect_correct_mode", 2)
        else:
            self.hcam.setPropertyValue("defect_correct_mode", 1)
            
    def DefectCorrectionSwitchEvent(self):
        """
        There are a few pixels in CMOS image sensor that have slightly higher readout noise performance compared to surrounding pixels. 
        And the extended exposures may cause a few white spots which is caused by failure in part of the silicon wafer in CMOS image sensor. 
        The camera has real-time variant pixel correction features to improve image quality.
        The correction is performed in real-time without sacrificing the readout speed at all. This function can be turned ON and OFF. (Default is ON)
        User can choose the correction level for white spots depend on the exposure time.
        """
        if self.DefectCorrectionButton.isChecked():
            self.hcam.setPropertyValue("readout_speed", 1)
        else:
            self.hcam.setPropertyValue("readout_speed", 2)
            
    def SubArrayModeSwitchEvent(self):
        if self.SubArrayModeSwitchButton.isChecked():
            self.hcam.setPropertyValue("subarray_mode", "ON")
        else:
            self.hcam.setPropertyValue("subarray_mode", "OFF")        
            
    def SetExposureTime(self):
        self.CamExposureTime = self.hcam.setPropertyValue("exposure_time", self.CamExposureBox.value())
        self.CamExposureBox.setValue(round(self.CamExposureTime, 6))
        
    def SetBinning(self):
        if self.BinningButtongroup.checkedId() == 1:
            self.hcam.setPropertyValue("binning", "1x1")
        elif self.BinningButtongroup.checkedId() == 2:
            self.hcam.setPropertyValue("binning", "2x2")
        elif self.BinningButtongroup.checkedId() == 3:
            self.hcam.setPropertyValue("binning", "4x4")
            
    def SetPixelType(self):
        if self.PixelTypeButtongroup.checkedId() == 1:
            self.hcam.setPropertyValue("image_pixeltype", "MONO8")
        elif self.PixelTypeButtongroup.checkedId() == 2:
            self.hcam.setPropertyValue("image_pixeltype", "MONO12")
        elif self.PixelTypeButtongroup.checkedId() == 3:
            self.hcam.setPropertyValue("image_pixeltype", "MONO16")
            
        """
        # =============================================================================
        #                               ROI functions
        # =============================================================================
        """            
    def ShowROISelector(self):
        if self.ShowROISelectorButton.isChecked():
            try:
                self.ROIWidget = pg.RectROI([self.hcam.getPropertyValue("subarray_hpos")[0],self.hcam.getPropertyValue("subarray_vpos")[0]],
                                             [self.hcam.getPropertyValue("subarray_hsize")[0],self.hcam.getPropertyValue("subarray_vsize")[0]], pen=(0,9))
            except:
                self.ROIWidget = pg.RectROI([0,0], [200,200], pen=(0,9))
                
            self.Live_view.addItem(self.ROIWidget)# add ROIs to main image    
            self.ROIWidget.maxBounds= QRectF(0,0,2048,2048) 
            #setting the max ROI bounds to be within the camera resolution
            
            self.ROIWidget.sigRegionChanged.connect(self.update_roi_coordinates) 
            #This function ensures the spinboxes show the actual roi coordinates
        else:
            self.Live_view.removeItem(self.ROIWidget)
    
    #------------------------------ROI part from Douwe-------------------------
    def set_roi_flag(self):
        if self.center_roiButton.isChecked():
            self.y_position.setReadOnly(True)
            self.clear_roi()
            self.center_frame = 0.5*self.camdev.mmc.getImageHeight()
            """
            I've put the center frame in the set_roi_flag so it automatically
            adjusts to the number of pixels (which is dependent on the binning
            settings for example.)
            """
            self.set_roi()
            self.ROIWidget.sigRegionChanged.connect(lambda: self.center_roi()) 
            #setting the ROI to the center every move
            """
            If the ROI centering performs poorly it is also possible to use the 
            sigRegionChangeFinished() function. I like this better for now.
            """
        
        else:
            self.y_position.setReadOnly(False)
            self.ROIWidget.sigRegionChanged.disconnect() 
            '''
            I do not know how to disconnect one specific function, so I 
            disconnect both and then reconnect the update_roi_coordinates 
            function.
            '''
            self.ROIWidget.sigRegionChanged.connect(self.update_roi_coordinates)

    def update_roi_coordinates(self):
        self.roi_x = int(self.ROIWidget.pos()[0])
        self.roi_y = int(self.ROIWidget.pos()[1])
        self.roi_height = int(self.ROIWidget.size()[1])
        self.roi_width = int(self.ROIWidget.size()[0])
        
        self.x_position.setValue(self.roi_x)
        self.y_position.setValue(self.roi_y)
        self.x_size.setValue(self.roi_width)
        self.y_size.setValue(self.roi_height)
      
    def spin_value_changed(self):
        
        if self.x_size.value() != self.roi_x_size or self.y_size.value() != self.roi_y_size:

            self.ROIWidget.setSize([self.x_size.value(),self.y_size.value()])
        
        
        if self.center_roiButton.isChecked():
            if self.x_position.value() != self.roi_x:
                self.ROIWidget.setPos(self.x_position.value())
        else:
            if self.x_position.value() != self.roi_x or self.y_position.value() != self.roi_y:
                self.ROIWidget.setPos(self.x_position.value(),self.y_position.value())

    #----------------------------ROI centering functions-----------------------
    def center_roi(self):
        
        self.y_center = int(self.center_frame-0.5*self.roi_height)
        
        if  self.roi_y != self.y_center:
           self.ROIWidget.setPos(self.roi_x, self.y_center)
           self.update_roi_coordinates()
    #--------------------------------------------------------------------------
    
    def SetROI(self):
        self.subarray_hsize = self.x_size.value()
        self.subarray_vsize = self.y_size.value()
        self.subarray_hpos = self.x_position.value()
        self.subarray_vpos = self.y_position.value()
        
        if self.subarray_hsize == 2048 and self.subarray_vsize == 2048:
            self.hcam.setPropertyValue("subarray_mode", "OFF")
            self.SubArrayModeSwitchButton.setChecked(False)

        else:
        # set subarray mode off. This setting is not mandatory, but you have to control the setting order of offset and size when mode is on.
            self.hcam.setPropertyValue("subarray_mode", "OFF")
            self.hcam.setPropertyValue("subarray_hsize", self.subarray_hsize)
            self.hcam.setPropertyValue("subarray_vsize", self.subarray_vsize)
            self.hcam.setPropertyValue("subarray_hpos", self.subarray_hpos)
            self.hcam.setPropertyValue("subarray_vpos", self.subarray_vpos)
            self.hcam.setPropertyValue("subarray_mode", "ON")
            self.SubArrayModeSwitchButton.setChecked(True)
        
    def closeEvent(self, event):
        try:
            self.hcam.shutdown()
            dcam.dcamapi_uninit()
        except:
            pass
        self.close()
        
class MySwitch(QtWidgets.QPushButton):
    """
    General switch button widget.
    """
    def __init__(self, label_1, color_1, label_2, color_2, width, parent = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setMinimumWidth(66)
        self.setMinimumHeight(22)
        self.switch_label_1 = label_1
        self.switch_label_2 = label_2
        self.switch_color_1 = color_1
        self.switch_color_2 = color_2
        self.width = width
        
    def paintEvent(self, event):
        label = self.switch_label_1 if self.isChecked() else self.switch_label_2
        
        if self.isChecked():
            bg_color = QColor(self.switch_color_1)
        else:
            bg_color = QColor(self.switch_color_2)
                
        radius = 10
        width = self.width
        center = self.rect().center()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(center)
        painter.setBrush(QColor(0,0,0))

        pen = QPen(Qt.black)
        pen.setWidth(2)
        painter.setPen(pen)

        painter.drawRoundedRect(QRect(-width, -radius, 2*width, 2*radius), radius, radius)
        painter.setBrush(QBrush(bg_color))
        sw_rect = QRect(-radius, -radius, width + radius, 2*radius)
        if not self.isChecked():
            sw_rect.moveLeft(-width)
        painter.drawRoundedRect(sw_rect, radius, radius)
        painter.drawText(sw_rect, Qt.AlignCenter, label)
        
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        QtWidgets.QApplication.setStyle(QStyleFactory.create('Fusion'))
        mainwin = CameraUI()
        mainwin.show()
        app.exec_()
    run_app()