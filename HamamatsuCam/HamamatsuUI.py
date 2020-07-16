# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 18:47:31 2020

@author: xinmeng
"""

from __future__ import division
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPoint, QRect, QObject, QSize, QTimer
from PyQt5.QtGui import QImage, QPalette, QBrush, QFont, QPainter, QColor, QPen, QIcon, QMovie

from PyQt5.QtWidgets import (QWidget, QButtonGroup, QLabel, QSlider, QSpinBox, QDoubleSpinBox, QGridLayout, QPushButton, QGroupBox, 
                             QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox, QTabWidget, QCheckBox, QRadioButton, 
                             QFileDialog, QProgressBar, QTextEdit, QStyleFactory, QMainWindow, QMenu, QAction, QStackedWidget)
import pyqtgraph as pg
import sys
import os
import time
import threading
import numpy as np
import ctypes
import ctypes.util
import skimage.external.tifffile as skimtiff
from skimage.measure import block_reduce
from PIL import Image
try:
    from HamamatsuDCAM import *
except:
    from HamamatsuCam.HamamatsuDCAM import *
# Append parent folder to system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import StylishQT

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
    
    signal_SnapImg = pyqtSignal(np.ndarray)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.isLiving = False
        self.isStreaming = False
        self.Live_item_autolevel = True
        self.ShowROIImgSwitch = False
        self.ROIselector_ispresented = False
        self.Live_sleeptime = 0.04 # default 25 camera live fps
        #----------------------------------------------------------------------
        #----------------------------------GUI---------------------------------
        #----------------------------------------------------------------------
        self.setWindowTitle("Hamamatsu Orca Flash")
        self.setFont(QFont("Arial"))
        self.setMinimumSize(1200,900)
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
        CameraSettingContainer.setStyleSheet("QGroupBox {\
                                        font: bold;\
                                        border: 1px solid silver;\
                                        border-radius: 6px;\
                                        margin-top: 10px;\
                                        color:Navy}\
                                        font-size: 14px;\
                                        QGroupBox::title{subcontrol-origin: margin;\
                                                         left: 7px;\
                                                         padding: 5px 5px 5px 5px;}")
        CameraSettingContainer.setMaximumHeight(400)
        CameraSettingContainer.setMaximumWidth(365)
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
        self.ReadoutSpeedSwitchButton = StylishQT.MySwitch('Normal', 'yellow', 'Fast', 'cyan', width = 50)
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
        CameraImageFormatContainer.setStyleSheet("QGroupBox { background-color:#F5F5F5;}")
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
        self.SubArrayModeSwitchButton = StylishQT.MySwitch('Sub Array Mode', 'lemon chiffon', 'Full Image Size', 'lavender', width = 100)
        self.SubArrayModeSwitchButton.setChecked(False)
        self.SubArrayModeSwitchButton.clicked.connect(self.SubArrayModeSwitchEvent)
        CameraSettingTab_2.layout.addWidget(self.SubArrayModeSwitchButton, 0, 1, 1, 3)
        
        # Adapted from Douwe's ROI part.
        self.center_roiButton = QPushButton()
        self.center_roiButton.setText("Symmetric to Center Line")        
        self.center_roiButton.clicked.connect(lambda: self.set_roi_flag())
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
        CameraSettingTab_2.layout.addWidget(self.ShowROISelectorButton, 2, 1, 1, 2)
        
        self.ShowROIImgButton = QPushButton()
        self.ShowROIImgButton.setText("Check ROI (R)")
        self.ShowROIImgButton.setToolTip("Short key: R ")
        self.ShowROIImgButton.clicked.connect(self.SetShowROIImgSwitch)
        self.ShowROIImgButton.setShortcut('r')
        self.ShowROIImgButton.setCheckable(True)
        self.ShowROIImgButton.setEnabled(False)
        CameraSettingTab_2.layout.addWidget(self.ShowROIImgButton, 2, 3, 1, 1)
        
        #----------------------------------------------------------------------
        CameraROIPosContainer = QGroupBox("ROI position")
        CameraROIPosContainer.setStyleSheet("QGroupBox { background-color:#F5F5F5;}")
        CameraROIPosLayout = QGridLayout()
        
        OffsetLabel = QLabel("Offset")
        OffsetLabel.setFixedHeight(30)
        ROISizeLabel = QLabel("Size")
        ROISizeLabel.setFixedHeight(30)
        
        CameraROIPosLayout.addWidget(OffsetLabel, 0, 1)
        CameraROIPosLayout.addWidget(ROISizeLabel, 0, 2)
        
        self.ROI_hpos_spinbox = QSpinBox()
        self.ROI_hpos_spinbox.setMaximum(2048)
        self.ROI_hpos_spinbox.setValue(0)
        self.ROI_hpos_spinbox.valueChanged.connect(self.spin_value_changed)
        CameraROIPosLayout.addWidget(self.ROI_hpos_spinbox, 1, 1)
        
        self.ROI_vpos_spinbox = QSpinBox()
        self.ROI_vpos_spinbox.setMaximum(2048)
        self.ROI_vpos_spinbox.setValue(0)
        self.ROI_vpos_spinbox.valueChanged.connect(self.spin_value_changed)
        CameraROIPosLayout.addWidget(self.ROI_vpos_spinbox, 2, 1)
        
        self.ROI_hsize_spinbox = QSpinBox()
        self.ROI_hsize_spinbox.setMaximum(2048)
        self.ROI_hsize_spinbox.setValue(2048)
        self.ROI_hsize_spinbox.valueChanged.connect(self.spin_value_changed)
        CameraROIPosLayout.addWidget(self.ROI_hsize_spinbox, 1, 2)
        
        self.ROI_vsize_spinbox = QSpinBox()
        self.ROI_vsize_spinbox.setMaximum(2048)
        self.ROI_vsize_spinbox.setValue(2048)
        self.ROI_vsize_spinbox.valueChanged.connect(self.spin_value_changed)
        CameraROIPosLayout.addWidget(self.ROI_vsize_spinbox, 2, 2)
        
        CameraROIPosLayout.addWidget(QLabel("Horizontal"), 1, 0)
        CameraROIPosLayout.addWidget(QLabel("Vertical"), 2, 0)
        
        CameraROIPosContainer.setLayout(CameraROIPosLayout)
        CameraROIPosContainer.setFixedHeight(105)
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
        
        self.TriggerButtongroup = QButtonGroup(self)
        self.TriggerButton_1 = QPushButton("Intern")
        self.TriggerButton_1.setCheckable(True)
        # self.TriggerButton_1.setChecked(True)
        self.TriggerButtongroup.addButton(self.TriggerButton_1, 1)
        self.TriggerButton_1.clicked.connect(lambda: self.TimingstackedWidget.setCurrentIndex(0))
        
        self.TriggerButton_2 = QPushButton("Extern")
        self.TriggerButton_2.setCheckable(True)
        self.TriggerButtongroup.addButton(self.TriggerButton_2, 2)
        self.TriggerButton_2.clicked.connect(lambda: self.TimingstackedWidget.setCurrentIndex(1))
        
        self.TriggerButton_3 = QPushButton("MasterPulse")
        self.TriggerButton_3.setCheckable(True)
        self.TriggerButtongroup.addButton(self.TriggerButton_3, 3)
        self.TriggerButton_3.clicked.connect(lambda: self.TimingstackedWidget.setCurrentIndex(2))
        self.TriggerButtongroup.setExclusive(True)
        
        self.TriggerButtongroup.buttonClicked[int].connect(self.SetTimingTrigger)
        
        CameraSettingTab_3.layout.addWidget(QLabel('Acquisition Control:'), 0, 0, 1, 2)
        CameraSettingTab_3.layout.addWidget(self.TriggerButton_1, 1, 1)
        CameraSettingTab_3.layout.addWidget(self.TriggerButton_2, 1, 2)
        CameraSettingTab_3.layout.addWidget(self.TriggerButton_3, 1, 3)
        
        InternTriggerWidget =  QWidget()
        ExternTriggerWidget =  QWidget()
        MasterPulseWidget =  QWidget()
        
        self.TimingstackedWidget =  QStackedWidget()
        self.TimingstackedWidget.addWidget(InternTriggerWidget)
        self.TimingstackedWidget.addWidget(ExternTriggerWidget)
        self.TimingstackedWidget.addWidget(MasterPulseWidget)
        self.TimingstackedWidget.setCurrentIndex(0)
        
        #-------------------------ExternTrigger--------------------------------
        ExternTriggerWidget.layout = QGridLayout()
        ExternTriggerWidget.layout.addWidget(QLabel("Trigger Signal:"), 0, 0)
        self.ExternTriggerSingalComboBox = QComboBox()
        self.ExternTriggerSingalComboBox.addItems(['EDGE', 'LEVEL', 'SYNCREADOUT'])
        self.ExternTriggerSingalComboBox.activated.connect(self.SetTriggerActive)
        ExternTriggerWidget.layout.addWidget(self.ExternTriggerSingalComboBox, 0, 1)
                
        ExternTriggerWidget.setLayout(ExternTriggerWidget.layout)
        
        CameraSettingTab_3.layout.addWidget(self.TimingstackedWidget, 2, 0, 4, 4)

        CameraSettingTab_3.setLayout(CameraSettingTab_3.layout)        
        #----------------------------------------------------------------------
        CameraSettingTab.addTab(CameraSettingTab_1,"Camera") 
        CameraSettingTab.addTab(CameraSettingTab_2,"ROI")
        CameraSettingTab.addTab(CameraSettingTab_3,"Timing")
        
        CameraSettingTab.setStyleSheet('QTabBar { width: 200px; font-size: 8pt; font: bold;}')
        CameraSettingLayout.addWidget(CameraSettingTab, 1, 0, 1, 1)
        
        CameraSettingContainer.setLayout(CameraSettingLayout)
        MainWinCentralWidget.layout.addWidget(CameraSettingContainer, 0, 0)
        
        """
        # =============================================================================
        #         Camera acquisition container.
        # =============================================================================
        """

        CameraAcquisitionContainer = QGroupBox('Acquisition')
        CameraAcquisitionContainer.setStyleSheet("QGroupBox {\
                                        font: bold;\
                                        border: 1px solid silver;\
                                        border-radius: 6px;\
                                        margin-top: 10px;\
                                        color:Navy}\
                                        font-size: 14px;\
                                        QGroupBox::title{subcontrol-origin: margin;\
                                                         left: 7px;\
                                                         padding: 5px 5px 5px 5px;}")
        CameraAcquisitionContainer.setMaximumHeight(438)
        CameraAcquisitionContainer.setMaximumWidth(365)
        CameraAcquisitionLayout = QGridLayout()
        
        #----------------------------------------------------------------------
        CamSpecContainer = QGroupBox("浜松 Hamamastu specs")
        CamSpecContainer.setStyleSheet("QGroupBox {\
                                        font: bold;\
                                        border: 1px solid silver;\
                                        border-radius: 6px;\
                                        margin-top: 6px;\
                                        color:olive;background-color:azure;}\
                                        QGroupBox::title{subcontrol-origin: margin;\
                                                         left: 7px;\
                                                         padding: 0px 5px 0px 5px;}")
        CamSpectLayout = QGridLayout()
        
        self.CamFPSLabel = QLabel("Internal frame rate:     ")
        self.CamFPSLabel.setStyleSheet("QLabel { background-color : azure; color : teal; }")
#        self.CamFPSLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        CamSpectLayout.addWidget(self.CamFPSLabel, 0, 0, 1, 1)
        
        self.CamExposureTimeLabel = QLabel("Exposure time:     ")
        self.CamExposureTimeLabel.setStyleSheet("QLabel { background-color : azure; color : teal; }")
#        self.CamFPSLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        CamSpectLayout.addWidget(self.CamExposureTimeLabel, 1, 0, 1, 1)
        
        self.CamReadoutTimeLabel = QLabel("Readout speed:     ")
        self.CamReadoutTimeLabel.setStyleSheet("QLabel { background-color : azure; color : teal; }")
#        self.CamFPSLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        CamSpectLayout.addWidget(self.CamReadoutTimeLabel, 2, 0, 1, 1)
        
        CamSpecContainer.setFixedHeight(130)
        
        CamSpecContainer.setLayout(CamSpectLayout)
        CameraAcquisitionLayout.addWidget(CamSpecContainer, 0, 0)
        
        
        #----------------------------------------------------------------------
        self.AcquisitionROIstackedWidget =  QStackedWidget()
        
        #---------------------------AcquisitionTabs----------------------------
        CameraAcquisitionTab = QTabWidget()
        CameraAcquisitionTab.layout = QGridLayout()
        """
        ------------------------------Live tab---------------------------------
        """
        CameraAcquisitionTab_1 = QWidget()
        CameraAcquisitionTab_1.layout = QGridLayout()
        
        CamLiveActionContainer = QGroupBox()
        CamLiveActionContainer.setFixedHeight(110)
        CamLiveActionContainer.setStyleSheet("QGroupBox { background-color:#F5F5F5;}")
        CamLiveActionLayout = QGridLayout()
        
        self.LiveSwitchLabel = QLabel("Live switch:")
        self.LiveSwitchLabel.setStyleSheet("QLabel { color : navy; font-size: 10pt; }")
        self.LiveSwitchLabel.setFixedHeight(45)
        self.LiveSwitchLabel.setAlignment(Qt.AlignCenter)
        CamLiveActionLayout.addWidget(self.LiveSwitchLabel, 0, 0)
        self.LiveButton = StylishQT.MySwitch('LIVING', 'spring green', 'STOPPED', 'indian red', width = 60)
        self.LiveButton.clicked.connect(self.LiveSwitchEvent)
        CamLiveActionLayout.addWidget(self.LiveButton, 0, 1, 1, 2)
        
        SnapImgButton = StylishQT.FancyPushButton(23, 32, color1=(255,204,229), color2=(153,153,255))
        SnapImgButton.setIcon(QIcon('./Icons/snap.png'))
        SnapImgButton.clicked.connect(self.SnapImg)
        CamLiveActionLayout.addWidget(SnapImgButton, 1, 1, 1, 1)         
        
        SaveLiveImgButton = StylishQT.saveButton()
        SaveLiveImgButton.clicked.connect(lambda: self.SaveLiveImg())
        CamLiveActionLayout.addWidget(SaveLiveImgButton, 1, 2, 1, 1)
        
        CamLiveActionContainer.setLayout(CamLiveActionLayout)
        CameraAcquisitionTab_1.layout.addWidget(CamLiveActionContainer, 0, 0, 1, 4)
        
        self.LiveImgViewResetButton = QPushButton()
        self.LiveImgViewResetButton.setText("Reset ImageView")
        self.LiveImgViewResetButton.clicked.connect(self.ResetLiveImgView)
        CameraAcquisitionTab_1.layout.addWidget(self.LiveImgViewResetButton, 1, 0, 1, 2)
        
        self.LiveAutoLevelSwitchButton = QPushButton()
        self.LiveAutoLevelSwitchButton.setText("Auto Level(A)")
        self.LiveAutoLevelSwitchButton.setShortcut('a')
        self.LiveAutoLevelSwitchButton.clicked.connect(self.AutoLevelSwitchEvent)
        self.LiveAutoLevelSwitchButton.setCheckable(True)
        self.LiveAutoLevelSwitchButton.setChecked(True)
        CameraAcquisitionTab_1.layout.addWidget(self.LiveAutoLevelSwitchButton, 1, 2, 1, 2)
        

        
        CameraAcquisitionTab_1.setLayout(CameraAcquisitionTab_1.layout)
        
        """
        ----------------------------Stream tab---------------------------------
        """
        CameraAcquisitionTab_2 = QWidget()
        CameraAcquisitionTab_2.layout = QGridLayout()
        
        self.CamStreamActionContainer = QGroupBox()
        self.CamStreamActionContainer.setFixedHeight(120)
        CamStreamActionLayout = QGridLayout()
        
        self.StreamStopSingalComBox = QComboBox()
#        self.StreamStopSingalComBox.lineEdit().setAlignment(Qt.AlignCenter)
        self.StreamStopSingalComBox.addItems(['Stop signal: Frames', 'Stop signal: Time'])
        CamStreamActionLayout.addWidget(self.StreamStopSingalComBox, 1, 0)

        EstFPSLabel = QLabel("Estimated FPS")
        EstFPSLabel.setFixedHeight(30)
        TotalTimeLabel = QLabel("Total time(s)")
        TotalTimeLabel.setFixedHeight(30)
        
        CamStreamActionLayout.addWidget(EstFPSLabel, 0, 1)
        CamStreamActionLayout.addWidget(TotalTimeLabel, 0, 2)
        
        self.EstFPS_spinbox = QSpinBox()
        self.EstFPS_spinbox.setMaximum(4048)
        self.EstFPS_spinbox.setValue(1000)
        CamStreamActionLayout.addWidget(self.EstFPS_spinbox, 1, 1)
        self.EstFPS_spinbox.valueChanged.connect(self.UpdateBufferNumber)
        
        self.StreamTotalTime_spinbox = QSpinBox()
        self.StreamTotalTime_spinbox.setMaximum(1200)
        self.StreamTotalTime_spinbox.setValue(0)
        CamStreamActionLayout.addWidget(self.StreamTotalTime_spinbox, 1, 2)
        self.StreamTotalTime_spinbox.valueChanged.connect(self.UpdateBufferNumber)
        
        self.StreamBufferTotalFrames_spinbox = QSpinBox()
        self.StreamBufferTotalFrames_spinbox.setMaximum(120000)
        self.StreamBufferTotalFrames_spinbox.setValue(0)
        CamStreamActionLayout.addWidget(self.StreamBufferTotalFrames_spinbox, 2, 2)
        CamStreamActionLayout.addWidget(QLabel("Buffers:"), 2, 1)
        
        self.StreamMemMethodComBox = QComboBox()
#        self.StreamStopSingalComBox.lineEdit().setAlignment(Qt.AlignCenter)
        self.StreamMemMethodComBox.addItems(['Stream to RAM', 'Stream to Hard disk'])
        CamStreamActionLayout.addWidget(self.StreamMemMethodComBox, 2, 0)
        
        #----------------------------------------------------------------------
        self.Streamdirectorytextbox = QLineEdit(self)
        self.Streamdirectorytextbox.setPlaceholderText('Stream File')
        CameraAcquisitionTab_2.layout.addWidget(self.Streamdirectorytextbox, 5, 0)
        
        self.BrowseStreamFileButton = QPushButton()
        self.BrowseStreamFileButton.setIcon(QIcon('./Icons/Browse.png')) 
        self.BrowseStreamFileButton.clicked.connect(lambda: self.SetStreamFileName())
        CameraAcquisitionTab_2.layout.addWidget(self.BrowseStreamFileButton, 5, 1)
        
        ApplyStreamSettingButton = StylishQT.FancyPushButton(50, 22)
        ApplyStreamSettingButton.setText("Apply")
        ApplyStreamSettingButton.clicked.connect(self.SetStreamSpecs)
        CameraAcquisitionTab_2.layout.addWidget(ApplyStreamSettingButton, 5, 2)     
        
        self.StartStreamButton = QPushButton()
        self.StartStreamButton.setToolTip("Stream")
        self.StartStreamButton.setIcon(QIcon('./Icons/StartStreaming.png'))        
        self.StartStreamButton.setCheckable(True)
        self.StartStreamButton.clicked.connect(self.StreamingSwitchEvent)
        CameraAcquisitionTab_2.layout.addWidget(self.StartStreamButton, 5, 3)
        
        """
        ------------------------Acquisition status-----------------------------
        """

        self.CamStreamIsFree = QLabel("No Stream Activity")
        self.CamStreamIsFree.setStyleSheet("QLabel { background-color : azure; color : teal; font: bold;}")
        self.CamStreamIsFree.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        
        CamStreamBusyWidget =  QWidget()        
        CamStreamSavingWidget =  QWidget()
        
        self.StreamStatusStackedWidget =  QStackedWidget()
        self.StreamStatusStackedWidget.setFixedHeight(50)
        self.StreamStatusStackedWidget.setStyleSheet("QStackedWidget { background-color : #F0F8FF;}")
        
        self.StreamStatusStackedWidget.addWidget(self.CamStreamIsFree)
        self.StreamStatusStackedWidget.addWidget(CamStreamBusyWidget)        
        self.StreamStatusStackedWidget.addWidget(CamStreamSavingWidget)
        self.StreamStatusStackedWidget.setCurrentIndex(0)
        
        #----------------------------------------------------------------------
        CamStreamBusyWidget.layout = QGridLayout()
        CamStreamBusylabel = QLabel()
        CamStreamBusylabel.setFixedHeight(35)
        CamStreamBusylabel.setAlignment(Qt.AlignVCenter)
        self.StreamBusymovie = QMovie("./Icons/progressbar.gif")

        CamStreamBusylabel.setMovie(self.StreamBusymovie)
        CamStreamBusyWidget.layout.addWidget(CamStreamBusylabel, 0, 1)
        
        self.CamStreamingLabel = QLabel("Recording")
        self.CamStreamingLabel.setFixedWidth(135)
        self.CamStreamingLabel.setStyleSheet("QLabel { color : #208000; font: Times New Roman;}")
        self.CamStreamingLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        CamStreamBusyWidget.layout.addWidget(self.CamStreamingLabel, 0, 0)
        CamStreamBusyWidget.setLayout(CamStreamBusyWidget.layout)
  
        
        #-----------------------Saving prograssbar-----------------------------
        CamStreamSavingWidget.layout = QGridLayout()
        CamStreamSavingWidget.layout.addWidget(QLabel('File saving progress:'), 0, 0)
        self.CamStreamSaving_progressbar = QProgressBar(self)
        self.CamStreamSaving_progressbar.setMaximumWidth(250)
        self.CamStreamSaving_progressbar.setMaximum(100)
        self.CamStreamSaving_progressbar.setStyleSheet('QProgressBar {color: black;border: 1px solid grey; border-radius:3px;text-align: center;}'
                                                 'QProgressBar::chunk {background-color: #E6E6FA; width: 5px; margin: 1px;}')
        CamStreamSavingWidget.layout.addWidget(self.CamStreamSaving_progressbar, 0, 1, 1, 4)
        CamStreamSavingWidget.setLayout(CamStreamSavingWidget.layout)
        
#        CamStreamProgressContainer.layout.addWidget(self.StreamStatusStackedWidget, 6, 0, 1, 4)
#        CamStreamProgressContainer.setLayout(CamStreamProgressContainer.layout)
        CameraAcquisitionTab_2.layout.addWidget(self.StreamStatusStackedWidget, 6, 0, 1, 4)
         #----------------------------------------------------------------------
        self.CamStreamActionContainer.setLayout(CamStreamActionLayout)
        
        CameraAcquisitionTab_2.layout.addWidget(self.CamStreamActionContainer, 0, 0, 5, 4)
    
        CameraAcquisitionTab_2.setLayout(CameraAcquisitionTab_2.layout)
        
        CameraAcquisitionTab.addTab(CameraAcquisitionTab_1,"Live")
        CameraAcquisitionTab.addTab(CameraAcquisitionTab_2,"Stream")
        CameraAcquisitionTab.setStyleSheet('QTabBar { width: 200px; font-size: 8pt; font: bold; color: #003366}')
        self.AcquisitionROIstackedWidget.addWidget(CameraAcquisitionTab)
        
        """
        #----------------------------Check ROI---------------------------------
        """
        ShowROIWidgetContainer = QGroupBox()
#        LiveWidgetContainer.setMaximumHeight(920)
#        LiveWidgetContainer.setMaximumWidth(950)
        ShowROIWidgetContainerLayout = QGridLayout()
        
        self.ShowROIWidget = pg.ImageView()
        self.ShowROIitem = self.ShowROIWidget.getImageItem() #setLevels
        self.ShowROIview = self.ShowROIWidget.getView()
        self.ShowROIitem.setAutoDownsample("subsample")
        
        self.ShowROIWidget.ui.roiBtn.hide()
        self.ShowROIWidget.ui.menuBtn.hide() 
        self.ShowROIWidget.ui.normGroup.hide()
        self.ShowROIWidget.ui.roiPlot.hide()
        self.ShowROIWidget.ui.histogram.hide()

        ShowROIWidgetContainerLayout.addWidget(self.ShowROIWidget, 1, 0)
        ShowROIWidgetContainer.setLayout(ShowROIWidgetContainerLayout)
        
        self.AcquisitionROIstackedWidget.addWidget(ShowROIWidgetContainer)
        #----------------------------------------------------------------------
        self.AcquisitionROIstackedWidget.setCurrentIndex(0)
        CameraAcquisitionLayout.addWidget(self.AcquisitionROIstackedWidget, 1, 0)
        
        CameraAcquisitionContainer.setLayout(CameraAcquisitionLayout)
        MainWinCentralWidget.layout.addWidget(CameraAcquisitionContainer, 1, 0)
        
        """
        # =============================================================================
        # --------------------------------Live Screen----------------------------------
        #   Initiating an imageview object for the main Livescreen. Hiding the pre
        # existing ROI and menubuttons.
        # =============================================================================        
        """
        LiveWidgetContainer = QGroupBox()
        # LiveWidgetContainer.setMaximumHeight(920)
        # LiveWidgetContainer.setMaximumWidth(950)
        self.LiveWidgetLayout = QGridLayout()
        
        self.LiveWidget = pg.ImageView()
        self.Live_item = self.LiveWidget.getImageItem() #setLevels
        self.Live_view = self.LiveWidget.getView()
        self.Live_item.setAutoDownsample(True)
        
        self.LiveWidget.ui.roiBtn.hide()
        self.LiveWidget.ui.menuBtn.hide() 
        self.LiveWidget.ui.normGroup.hide()
        self.LiveWidget.ui.roiPlot.hide()
        
        self.LiveWidgetLayout.addWidget(self.LiveWidget, 1, 0)
        
        LiveWidgetContainer.setLayout(self.LiveWidgetLayout)
        MainWinCentralWidget.layout.addWidget(LiveWidgetContainer, 0, 1, 2, 2)
        
        MainWinCentralWidget.setLayout(MainWinCentralWidget.layout)
        self.setCentralWidget(MainWinCentralWidget)
        
        #----------------Once open GUI, try to connect the camera--------------
        try:
            self.ConnectCamera()
        except:
            pass
        
        """
        #=========================================================================================================================================
        #--------------------------------------------------------------END of GUI-----------------------------------------------------------------
        #=========================================================================================================================================
        """
    
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
            self.CamExposureTimeText = str(self.CamExposureTime).replace(".", "p")
            self.CamExposureBox.setValue(round(self.CamExposureTime, 6))
            
            self.GetKeyCameraProperties()
                    
            if self.subarray_hsize == 2048 and self.subarray_vsize == 2048:
                self.hcam.setPropertyValue("subarray_mode", "OFF")
                self.SubArrayModeSwitchButton.setChecked(False)
            else:
                self.hcam.setPropertyValue("subarray_mode", "ON")
                self.SubArrayModeSwitchButton.setChecked(True)                

            self.UpdateStatusLabel()

            # Get the trigger active button updated
            if self.trigger_source == "INTERNAL":
                self.TriggerButton_1.setChecked(True)
            elif self.trigger_source == "EXTERNAL":
                self.TriggerButton_2.setChecked(True)
            elif self.trigger_source == "MASTER PULSE":
                self.TriggerButton_3.setChecked(True)
            # Get the trigger button updated
            if self.trigger_active == "EDGE":
                self.ExternTriggerSingalComboBox.setCurrentIndex(1)
            elif self.trigger_active == "LEVEL":
                self.ExternTriggerSingalComboBox.setCurrentIndex(2)
            elif self.trigger_active == "SYNCREADOUT":
                self.ExternTriggerSingalComboBox.setCurrentIndex(3)
            
    def DisconnectCamera(self):
        self.hcam.shutdown()
        dcam.dcamapi_uninit()
        self.CamStatusLabel.setText('Camera disconnected.')


        """
        # =============================================================================
        #                              Properties Settings
        # =============================================================================
        """         
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
                    
    def GetKeyCameraProperties(self):
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

        #                      "image_height",
        #                      "image_width",

        #                      "buffer_rowbytes",
        #                      "buffer_top_offset_bytes",
        #                      "subarray_hsize",
        #                      "subarray_vsize",
        #                      "binning"]
        for param in params:
            if param == "subarray_hsize":
                self.subarray_hsize = self.hcam.getPropertyValue(param)[0]
                self.ROI_hsize_spinbox.setValue(self.subarray_hsize)
            if param == "subarray_hpos":
                self.subarray_hpos = self.hcam.getPropertyValue(param)[0]   
                self.ROI_hpos_spinbox.setValue(self.subarray_hpos)
            if param == "subarray_vsize":
                self.subarray_vsize = self.hcam.getPropertyValue(param)[0]
                self.ROI_vsize_spinbox.setValue(self.subarray_vsize)
            if param == "subarray_vpos":
                self.subarray_vpos = self.hcam.getPropertyValue(param)[0]
                self.ROI_vpos_spinbox.setValue(self.subarray_vpos)
            if param == "internal_frame_rate":
                self.internal_frame_rate = self.hcam.getPropertyValue(param)[0]
            if param == "image_framebytes":
                self.image_framebytes = self.hcam.getPropertyValue(param)[0]
            if param == "buffer_framebytes":
                self.buffer_framebytes = self.hcam.getPropertyValue(param)[0]
            if param == "timing_readout_time":
                self.timing_readout_time = self.hcam.getPropertyValue(param)[0]
            if param == "trigger_source":
                if self.hcam.getPropertyValue(param)[0] == 1:
                    self.trigger_source = "INTERNAL"
                elif self.hcam.getPropertyValue(param)[0] == 2:
                    self.trigger_source = "EXTERNAL"
                elif self.hcam.getPropertyValue(param)[0] == 4:
                    self.trigger_source = "MASTER PULSE"
            if param == "trigger_active":
                if self.hcam.getPropertyValue(param)[0] == 1:
                    self.trigger_active = "EDGE"
                elif self.hcam.getPropertyValue(param)[0] == 2:
                    self.trigger_active = "LEVEL"
                elif self.hcam.getPropertyValue(param)[0] == 3:
                    self.trigger_active = "SYNCREADOUT"
    
    def UpdateStatusLabel(self):
        # Get the frame rate and update in the tag
        self.internal_frame_rate = self.hcam.getPropertyValue("internal_frame_rate")[0]        
        self.CamFPSLabel.setText("Frame rate: {}".format(round(self.internal_frame_rate, 2)))
        # Get the Readout time and update in the tag
        self.timing_readout_time = self.hcam.getPropertyValue("timing_readout_time")[0]        
        self.CamReadoutTimeLabel.setText("Readout speed: {}".format(round(1/self.timing_readout_time, 2)))
        # Get the exposure time
        self.CamExposureTime = self.hcam.getPropertyValue("exposure_time")[0]
        self.CamExposureTimeLabel.setText("Exposure time: {}".format(round(self.CamExposureTime, 5)))
        
    def GeneralsetPropertyValue(self, property_name, property_value):
        self.hcam.setPropertyValue(property_name, property_value)
        
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
        # Set property only works strating living/recording next time
        if self.isLiving == True:
            self.StopLIVE()
            
        if self.SubArrayModeSwitchButton.isChecked():
            self.hcam.setPropertyValue("subarray_mode", "ON")
        else:
            self.hcam.setPropertyValue("subarray_mode", "OFF")        
            self.hcam.setPropertyValue("subarray_hsize", 2048)
            self.hcam.setPropertyValue("subarray_vsize", 2048)
            self.hcam.setPropertyValue("subarray_hpos", 0)
            self.hcam.setPropertyValue("subarray_vpos", 0)
            self.subarray_vsize = 2048
            self.subarray_hsize = 2048 

        self.LiveSwitchEvent()
         
    def SetExposureTime(self):
        # Change the live fps if the exposure time is set to be larger
        self.Live_sleeptime = max(0.04, self.CamExposureBox.value() + 0.005)
        # print(self.Live_sleeptime)
        self.CamExposureTime = self.hcam.setPropertyValue("exposure_time", self.CamExposureBox.value())
        self.CamExposureBox.setValue(round(self.CamExposureTime, 6))
        
        self.UpdateStatusLabel()
        
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
            
    def SetTimingTrigger(self):
        if self.TriggerButtongroup.checkedId() == 1:
            self.hcam.setPropertyValue("trigger_source", "INTERNAL")
        elif self.TriggerButtongroup.checkedId() == 2:
            self.hcam.setPropertyValue("trigger_source", "EXTERNAL")
        elif self.TriggerButtongroup.checkedId() == 3:
            self.hcam.setPropertyValue("trigger_source", "MASTER PULSE")        
    
    def SetTriggerActive(self):
        if self.ExternTriggerSingalComboBox.currentText() == "LEVEL":
            self.hcam.setPropertyValue("trigger_active", "LEVEL")
        elif self.ExternTriggerSingalComboBox.currentText() == "EDGE":
            self.hcam.setPropertyValue("trigger_active", "EDGE")
        elif self.ExternTriggerSingalComboBox.currentText() == "SYNCREADOUT":
            self.hcam.setPropertyValue("trigger_active", "SYNCREADOUT")
        
        """
        # =============================================================================
        #                               ROI functions
        # =============================================================================
        """            
    def ShowROISelector(self):
        if self.ShowROISelectorButton.isChecked():
            self.ShowROIImgButton.setEnabled(True)
            self.ROIselector_ispresented = True
            
            # Wait for ImageView to update a full-sized image
            time.sleep(0.1)
        
            ROIpen = QPen()  # creates a default pen
            ROIpen.setStyle(Qt.DashDotLine)
            ROIpen.setWidth(0.5)
            ROIpen.setBrush(QColor(0,191,255))
            
            try:                            # Initialize the position and size of the ROI widget.
                if self.hcam.getPropertyValue("subarray_hsize")[0] == 2048 and self.hcam.getPropertyValue("subarray_vsize")[0] == 2048:
                    
                    if self.ROI_vpos_spinbox.value() == 0 and self.ROI_vsize_spinbox.value() == 2048: 
                        # If it's the first time opening ROI selector, respawn it at a imageview center.
                        self.ROIitem = pg.RectROI([924,924],
                                                  [200,200],
                                                  pen=ROIpen)
                        ## Create text object, use HTML tags to specify color/size
                        self.ROIitemText = pg.TextItem \
                        (html='<div style="text-align: center"><span style="color: #FFF;">Estimated max fps: </span><span style="color: #FF0; \
                            font-size: 10pt;">0</span></div>', anchor=(1, 1))
                        self.ROIitemText.setPos(924, 924)
                        
                    else: 
                        # If in the ROI position spinboxes there are numbers left from last ROI selection
                        self.ROIitem = pg.RectROI([self.ROI_hpos_spinbox.value(),self.ROI_vpos_spinbox.value()],
                                                  [self.ROI_hsize_spinbox.value(),self.ROI_vsize_spinbox.value()],
                                                  pen=ROIpen)
                        ## Create text object, use HTML tags to specify color/size
                        self.ROIitemText = pg.TextItem \
                        (html='<div style="text-align: center"><span style="color: #FFF;">Estimated max fps: </span><span style="color: #FF0; \
                            font-size: 10pt;">0</span></div>', anchor=(1, 1))
                        self.ROIitemText.setPos(self.ROI_hpos_spinbox.value(),self.ROI_vpos_spinbox.value())                   
                        
                        
                else:                       # If the camera is already in subarray mode        
                    self.ROIitem = pg.RectROI([self.hcam.getPropertyValue("subarray_hpos")[0],self.hcam.getPropertyValue("subarray_vpos")[0]],
                                                [self.hcam.getPropertyValue("subarray_hsize")[0],self.hcam.getPropertyValue("subarray_vsize")[0]],
                                                pen=ROIpen)
                    ## Create text object, use HTML tags to specify color/size
                    self.ROIitemText = pg.TextItem \
                    (html='<div style="text-align: center"><span style="color: #FFF;">Estimated max fps: </span><span style="color: #FF0; \
                        font-size: 10pt;">0</span></div>', anchor=(1, 1))
                    self.ROIitemText.setPos(self.hcam.getPropertyValue("subarray_hpos")[0],self.hcam.getPropertyValue("subarray_vpos")[0])
            except:
                self.ROIitem = pg.RectROI([0,0], [200,200], pen=ROIpen)
                ## Create text object, use HTML tags to specify color/size
                self.ROIitemText = pg.TextItem \
                (html='<div style="text-align: center"><span style="color: #FFF;">Estimated max fps: </span><span style="color: #FF0; \
                    font-size: 10pt;">0</span></div>', anchor=(0, 0))
                
            self.Live_view.addItem(self.ROIitem)# add ROIs to main image    
            self.ROIitem.maxBounds= QRectF(0,0,2048,2048) 
            #setting the max ROI bounds to be within the camera resolution
            
            self.ROIitem.sigRegionChanged.connect(self.update_ROI_spinbox_coordinates)
            #This function ensures the spinboxes show the actual roi coordinates
            
#            #Note that clicking is disabled by default to prevent stealing clicks from objects behind the ROI. 
#            self.ROIitem.setAcceptedMouseButtons(Qt.LeftButton)
#            self.ROIitem.sigClicked.connect(self.ShowROIImage)
            
            self.Live_view.addItem(self.ROIitemText)            
        else:
            self.ShowROIImgButton.setEnabled(False)
            self.Live_view.removeItem(self.ROIitem)
            self.Live_view.removeItem(self.ROIitemText)
            self.ROIselector_ispresented = False
            
    #-----------------------Center ROI part from Douwe-------------------------
    def set_roi_flag(self):
        if self.center_roiButton.isChecked():
            self.ROI_vpos_spinbox.setReadOnly(True)
#            self.ResetROI()
            self.center_frame = 0.5*2048#self.hcam.getPropertyValue("subarray_vsize")[0]
            """
            I've put the center frame in the set_roi_flag so it automatically
            adjusts to the number of pixels (which is dependent on the binning
            settings for example.)
            """
            # self.SetROI()
            self.ROIitem.sigRegionChanged.connect(lambda: self.center_roi()) 
            #setting the ROI to the center every move
            """
            If the ROI centering performs poorly it is also possible to use the 
            sigRegionChanged() function. I like this better for now.
            """
        
        else:
            self.ROI_vpos_spinbox.setReadOnly(False)
            self.ROIitem.sigRegionChanged.disconnect() 
            '''
            I do not know how to disconnect one specific function, so I 
            disconnect both and then reconnect the update_ROI_spinbox_coordinates 
            function.
            '''
            self.ROIitem.sigRegionChanged.connect(self.update_ROI_spinbox_coordinates)

    def update_ROI_spinbox_coordinates(self):
        self.ROI_hpos = int(self.ROIitem.pos()[0])
        self.ROI_vpos = int(self.ROIitem.pos()[1])
        self.ROI_vsize = int(self.ROIitem.size()[1])
        self.ROI_hsize = int(self.ROIitem.size()[0])
        
        self.ROI_hpos_spinbox.setValue(self.ROI_hpos)
        self.ROI_vpos_spinbox.setValue(self.ROI_vpos)
        self.ROI_hsize_spinbox.setValue(self.ROI_hsize)
        self.ROI_vsize_spinbox.setValue(self.ROI_vsize)
        
        self.update_ROI_estimateMaxFps()
        
    def update_ROI_estimateMaxFps(self):
        self.ROIupperRowDis = abs(1024 - self.ROI_vpos)
        self.ROIlowerRowDis = abs(1024 - self.ROI_vpos - self.ROI_vsize)
        self.ROIEstimatedMaxFPS = 1 / (max(self.ROIupperRowDis, self.ROIlowerRowDis) * 0.00000976)
        
        try:
            self.Live_view.removeItem(self.ROIitemText)
        except:
            pass
        
        ## Create text object, use HTML tags to specify color/size
        self.ROIitemText = pg.TextItem(html='<div style="text-align: center"><span style="color: #FFF;">Estimated max fps: </span><span style="color: #FF0; \
            font-size: 10pt;">{}</span></div>'.format(round(self.ROIEstimatedMaxFPS, 2)), anchor=(1, 1))
        self.ROIitemText.setPos(self.ROI_hpos,self.ROI_vpos)
        self.Live_view.addItem(self.ROIitemText)
        
    def spin_value_changed(self):
        
        if self.ROI_hsize_spinbox.value() != self.ROI_hsize or self.ROI_vsize_spinbox.value() != self.ROI_vsize:

            self.ROIitem.setSize([self.ROI_hsize_spinbox.value(),self.ROI_vsize_spinbox.value()])
        
        
        if self.center_roiButton.isChecked():
            if self.ROI_hpos_spinbox.value() != self.ROI_hpos:
                self.ROIitem.setPos(self.ROI_hpos_spinbox.value())
        else:
            if self.ROI_hpos_spinbox.value() != self.ROI_hpos or self.ROI_vpos_spinbox.value() != self.ROI_vpos:
                self.ROIitem.setPos(self.ROI_hpos_spinbox.value(),self.ROI_vpos_spinbox.value())
                
        self.UpdateStatusLabel()
        self.update_ROI_estimateMaxFps()
        
    #----------------------------ROI centering functions-----------------------
    def center_roi(self):
        
        self.v_center = int(self.center_frame-0.5*self.ROI_vsize)
        if  self.ROI_vpos != self.v_center:
           self.ROIitem.setPos(self.ROI_hpos, self.v_center)
           self.update_ROI_spinbox_coordinates()
    #--------------------------------------------------------------------------
    
    def SetROI(self):
        # Set property only works strating living/recording next time
        if self.isLiving == True:
            self.StopLIVE()
        # Remove the ROI
        self.Live_view.removeItem(self.ROIitem)
        self.Live_view.removeItem(self.ROIitemText)
        self.ROIselector_ispresented = False
        
        self.ROI_hsize = self.ROI_hsize_spinbox.value()
        self.ROI_vsize = self.ROI_vsize_spinbox.value()
        self.ROI_hpos = self.ROI_hpos_spinbox.value()
        self.ROI_vpos = self.ROI_vpos_spinbox.value()
        
        '''
        The Hamamatsu flash 4 ROI only works with multiples of 4! Here I make 
        sure that only multiples of 4 are passed on to the camera. Don't know if 
        this has to do with binning. I also make sure it doesn't pass a ROI of 
        0 size since this crashes the program!
        '''
        self.ROI_hpos = 4*int(self.ROI_hpos/4)

        self.ROI_vpos = 4*int(self.ROI_vpos/4)

        self.ROI_hsize = 4*int(self.ROI_hsize/4)
        if self.ROI_hsize == 0:
            self.ROI_hsize += 4
            
        self.ROI_vsize = 4*int(self.ROI_vsize/4)
        if self.ROI_vsize == 0:
            self.ROI_vsize += 4
        
        if self.ROI_hsize == 2048 and self.ROI_vsize == 2048:
            self.hcam.setPropertyValue("subarray_mode", "OFF")
            self.SubArrayModeSwitchButton.setChecked(False)
            
            self.subarray_vsize = 2048
            self.subarray_hsize = 2048    
            
        else:
        # set subarray mode off. This setting is not mandatory, but you have to control the setting order of offset and size when mode is on.
            self.hcam.setPropertyValue("subarray_mode", "OFF")
            self.hcam.setPropertyValue("subarray_hsize", self.ROI_hsize)
            self.hcam.setPropertyValue("subarray_vsize", self.ROI_vsize)
            self.hcam.setPropertyValue("subarray_hpos", self.ROI_hpos)
            self.hcam.setPropertyValue("subarray_vpos", self.ROI_vpos)
            self.hcam.setPropertyValue("subarray_mode", "ON")
            self.SubArrayModeSwitchButton.setChecked(True)
            
            self.subarray_vsize = self.ROI_vsize
            self.subarray_hsize = self.ROI_hsize 
            
        # Auto scale and pan the view around the image such that the image fills the view.    
        # self.LiveWidget.autoRange()
        self.UpdateStatusLabel()
        self.ShowROISelectorButton.setChecked(False)
        self.ShowROIImgButton.setEnabled(False)
        self.LiveSwitchEvent()
        
    def SetShowROIImgSwitch(self):
        if self.ShowROIImgButton.isChecked():
            self.AcquisitionROIstackedWidget.setCurrentIndex(1)
            self.ShowROIImgSwitch = True
#            .setImage(self.ROIitem.getArrayRegion(image, self.Live_item), autoLevels=False)
        else:
            self.AcquisitionROIstackedWidget.setCurrentIndex(0)
            self.ShowROIImgSwitch = False
            # self.Live_view.addItem(self.ROIitem)
            
        """
        # =============================================================================
        #                               LIVE functions
        # =============================================================================
        """            
    def LiveSwitchEvent(self):
        if self.LiveButton.isChecked():
            try:
                # self.LiveWidget.scene.clear()
                # self.Live_view.addItem(self.Live_item)
                self.ResetLiveImgView()
            except:
               print('clear failed.')
                
            StartLiveThread = threading.Thread(target = self.LIVE)
            StartLiveThread.start()
        else:
            StopLiveThread = threading.Thread(target = self.StopLIVE)
            StopLiveThread.start()
    
    def AutoLevelSwitchEvent(self):
        if self.LiveAutoLevelSwitchButton.isChecked():
            self.Live_item_autolevel = True
        else:
            self.Live_item_autolevel = False
        
    def LIVE(self):
        self.UpdateStatusLabel()
        
        self.isLiving = True
        self.hcam.acquisition_mode = "run_till_abort"
        self.hcam.startAcquisition()
        
        while self.isLiving == True: 
            [frames, dims] = self.hcam.getFrames() # frames is a list with HCamData type, with np_array being the image.
            self.Live_image = np.resize(frames[-1].np_array, (dims[1], dims[0]))
            
            self.subarray_vsize = dims[1]
            self.subarray_hsize = dims[0]
            
            time.sleep(self.Live_sleeptime)

            self.UpdateScreen(self.Live_image)
        
    def StopLIVE(self):
        self.isLiving = False
        self.hcam.stopAcquisition()
        
    def SaveLiveImg(self):

        files_types = "Tif (*.tif);;Pickle (*.pickle);;YAML (*.yml)"
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
                    self, 'Save as... File', 'InterFps_{}.tif'.format(int(self.internal_frame_rate)), filter=files_types,options=options)
        if len(filename) > 3:
            Localimg = Image.fromarray(self.Live_image) #generate an image object
            Localimg.save(filename) #save as tif
        
    def UpdateScreen(self, image):
        if self.Live_item_autolevel == True:
            # Down sample the image when it's full resolution
            if self.subarray_vsize == 2048 and self.subarray_hsize == 2048 and self.ROIselector_ispresented == False:
                
                self.Live_item.setImage(block_reduce(image, block_size=(2,2), func=np.mean, cval=np.mean(image)), autoLevels=None)
            else:
                self.Live_item.setImage(image, autoLevels=None)
                
        elif self.Live_item_autolevel == False:
            """
            Set image scaling levels. Can be one of:
                [blackLevel, whiteLevel]
                [[minRed, maxRed], [minGreen, maxGreen], [minBlue, maxBlue]]
            """
            
            if self.subarray_vsize == 2048 and self.subarray_hsize == 2048 and self.ROIselector_ispresented == False:
                
                self.Live_item.setImage(block_reduce(image, block_size=(2,2), func=np.mean, cval=np.mean(image)), autoLevels=False)
            else:
                self.Live_item.setImage(image, autoLevels=False)
        
        # Update ROI checking screen
        if self.ShowROIImgSwitch == True:
            self.ShowROIitem.setImage(self.ROIitem.getArrayRegion(image, self.Live_item), autoLevels=None)
#            self.ShowROIitem.setAutoDownsample("subsample")
            
    def SnapImg(self):
        self.StartStream_Thread = threading.Thread(target = self.SNAP)
        self.StartStream_Thread.start()
            
    def SNAP(self):
        """
        It's actually start acquisition with buffer being 1 image.
        """
        if self.isStreaming == False and self.isLiving == False:
#            self.hcam.setACQMode("fixed_length", number_frames = 1)
            self.hcam.startAcquisition()              
            # Start pulling out frames from buffer
            self.video_list = []
            self.imageCount = 0 # The actual frame number that gets recorded.
            for _ in range(1): # Record for range() number of images.
                [frames, self.dims] = self.hcam.getFrames() # frames is a list with HCamData type, with np_array being the image.
                for aframe in frames:
                    self.video_list.append(aframe.np_array)
                    self.imageCount += 1
                
            self.SnapImage = np.resize(self.video_list[-1], (self.dims[1], self.dims[0]))
            
            self.hcam.stopAcquisition()
            
            self.UpdateScreen(self.SnapImage)
            
            self.signal_SnapImg.emit(self.SnapImage)
            
        elif self.isStreaming == False and self.isLiving == True:
            
            self.hcam.stopAcquisition()
                
            self.SnapImage = self.Live_image
                  
            self.UpdateScreen(self.SnapImage)
            
            self.signal_SnapImg.emit(self.SnapImage)
            
    def ResetLiveImgView(self):
        """Closes the widget nicely, making sure to clear the graphics scene and release memory."""
        self.LiveWidget.close()
        
        # Replot the imageview
        self.LiveWidget = pg.ImageView()
        self.Live_item = self.LiveWidget.getImageItem() #setLevels
        self.Live_view = self.LiveWidget.getView()
        self.Live_item.setAutoDownsample(True)
        
        self.LiveWidget.ui.roiBtn.hide()
        self.LiveWidget.ui.menuBtn.hide() 
        self.LiveWidget.ui.normGroup.hide()
        self.LiveWidget.ui.roiPlot.hide()
        
        self.LiveWidgetLayout.addWidget(self.LiveWidget, 1, 0)
        
            
    def closeEvent(self, event):
        try:
            self.hcam.shutdown()
            dcam.dcamapi_uninit()
        except:
            pass
        self.close()

        """
        # =============================================================================
        #                              STREAM functions
        # =============================================================================
        """           
    def SetStreamFileName(self):

        files_types = "Tif (*.tif);;Pickle (*.pickle);;YAML (*.yml)"
        options = QFileDialog.Options()
        self.Streamfilename, _ = QFileDialog.getSaveFileName(
                    self, 'Save as... File', 'InternalFps_{}.tif'.format(int(self.internal_frame_rate)), filter=files_types,options=options)
        
#        self.Streamdirectorytextbox.setEnabled(True)
        
        if len(self.Streamfilename) > 35:
            self.Streamdirectorytextbox.setText('...' + self.Streamfilename[len(self.Streamfilename)-35:len(self.Streamfilename)])
        elif len(self.Streamfilename) > 1:
            self.Streamdirectorytextbox.setText(self.Streamfilename)
            
    def UpdateBufferNumber(self):
        self.BufferNumber = self.EstFPS_spinbox.value() * self.StreamTotalTime_spinbox.value()
        self.StreamBufferTotalFrames_spinbox.setValue(self.BufferNumber)
        
    def SetStreamSpecs(self):
        self.UpdateStatusLabel()
        
        if self.CamStreamActionContainer.isEnabled():
            self.CamStreamActionContainer.setEnabled(False)
            self.Streamdirectorytextbox.setEnabled(False)
        else:
            self.CamStreamActionContainer.setEnabled(True)
            self.Streamdirectorytextbox.setEnabled(True)      
            
        # Set the number of buffers get prepared.
        self.BufferNumber = self.StreamBufferTotalFrames_spinbox.value()
        
        if self.StreamStopSingalComBox.currentText() == 'Stop signal: Time':
            self.StopSignal = "Time"
            self.StreamDuration = self.StreamTotalTime_spinbox.value()
            self.hcam.acquisition_mode = "fixed_length"
            
        elif self.StreamStopSingalComBox.currentText() == 'Stop signal: Frames':
            self.StopSignal = "Frames"
            self.StreamDuration = -1
            self.hcam.acquisition_mode = "fixed_length"
    
    def StreamingSwitchEvent(self):
        if self.StartStreamButton.isChecked():
            self.StreamBusymovie.start()
            self.StreamStatusStackedWidget.setCurrentIndex(1)
            self.StartStreamButton.setIcon(QIcon('./Icons/STOP.png'))
            self.StartStreamingThread()
        else:
            self.StartStreamButton.setIcon(QIcon('./Icons/StartStreaming.png'))
            self.StopStreamingThread()
            
    def StartStreamingThread(self):
        if self.isStreaming == False and self.isLiving == False:
            self.StartStream_Thread = threading.Thread(target = self.StartStreaming, args=(self.StopSignal, self.BufferNumber, self.StreamDuration))
            self.StartStream_Thread.start()
    
    def StopStreamingThread(self):
        if self.isStreaming == True and self.isLiving == False:
            self.StartStreamButton.setChecked(False)
            self.StartStreamButton.setIcon(QIcon('./Icons/StartStreaming.png'))
            self.StartStreamButton.setEnabled(False)
            self.CamStreamActionContainer.setEnabled(False)
            
            self.StopStream_Thread = threading.Thread(target = self.StopStreaming, args=(True,))
            self.StopStream_Thread.start()            
            
    def StartStreaming(self, StopSignal, BufferNumber, StreamDuration):
            #--------------------Start the acquisition-------------------------
            # Duration hard limit:
            if StopSignal == "Time":
                # Set the timeout timer.
#                self.StreamDuration_timer = QTimer()
#                self.StreamDuration_timer.setSingleShot(True)
#                self.StreamDuration_timer.timeout.connect(self.StopStreamingThread)
                self.isStreaming = True
                
                self.hcam.setACQMode("fixed_length", number_frames = BufferNumber)
                self.hcam.startAcquisition()
                QTimer.singleShot(StreamDuration*1000, self.StopStreamingThread)
#                self.StreamDuration_timer.start(StreamDuration*1000) # Starts or restarts the timer with a timeout of duration msec milliseconds.                
                
                # Start pulling out frames from buffer
                self.video_list = []
                self.imageCount = 0 # The actual frame number that gets recorded.
                while self.isStreaming == True: # Record for range() number of images.
                    [frames, self.dims] = self.hcam.getFrames() # frames is a list with HCamData type, with np_array being the image.
                    for aframe in frames:
                        self.video_list.append(aframe.np_array)
                        self.imageCount += 1
                        
                        self.CamStreamingLabel.setText("Recording, {} frames..".format(self.imageCount))
                        
            # Frame number hard limit
            elif StopSignal == "Frames":
                self.isStreaming = True
                self.imageCount = 0 # The actual frame number that gets recorded.
                self.CamStreamingLabel.setText("Recording, {} frames..".format(self.imageCount))
                
                self.hcam.setACQMode("fixed_length", number_frames = BufferNumber)
                self.hcam.startAcquisition()              
                
                # Start pulling out frames from buffer
                self.video_list = []

                for _ in range(BufferNumber): # Record for range() number of images.
                    [frames, self.dims] = self.hcam.getFrames() # frames is a list with HCamData type, with np_array being the image.
                    for aframe in frames:
                        self.video_list.append(aframe.np_array)
                        self.imageCount += 1  
                        
                        self.CamStreamingLabel.setText("Recording, {} frames..".format(self.imageCount))
                        
                self.StopStreamingThread()
                
    def StopStreaming(self, saveFile):
        # Stop the acquisition
        AcquisitionEndTime = time.time()
        print("Frames acquired: " + str(self.imageCount))
        print('Total time is: {} s.'.format(AcquisitionEndTime-self.hcam.AcquisitionStartTime))
        print('Estimated fps: {} hz.'.format(int(self.imageCount/(AcquisitionEndTime-self.hcam.AcquisitionStartTime))))
        self.hcam.stopAcquisition()        
        self.isStreaming = False
        self.StreamBusymovie.stop()
        self.StreamStatusStackedWidget.setCurrentIndex(2)
        
        if saveFile == True:
            # Save the file.
            with skimtiff.TiffWriter(self.Streamfilename, append = True, imagej = True)\
            as tif:                
                write_starttime = time.time()
                for eachframe in range(self.imageCount): 
                    image = np.resize(self.video_list[eachframe], (self.dims[1], self.dims[0]))
                    tif.save(image, compress=0)
                    #---------Update file saving progress bar------------
                    if eachframe/self.imageCount*100 - int(eachframe/self.imageCount*100) <= 0.1:
                        self.CamStreamSaving_progressbar.setValue(int(eachframe/self.imageCount*100))
                    
            print("Done writing " + str(self.imageCount) + " frames, recorded for "\
            + str(round(AcquisitionEndTime,2)) + " seconds, saving video takes {} seconds.".format(round(time.time()-write_starttime, 2)))
        
        
        self.StartStreamButton.setEnabled(True)
        self.CamStreamActionContainer.setEnabled(True)
        self.StreamStatusStackedWidget.setCurrentIndex(0)
        self.CamStreamIsFree.setText("Acquisition done. Frames acquired: {}.".format(self.imageCount))
        
        
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        QtWidgets.QApplication.setStyle(QStyleFactory.create('Fusion'))
        mainwin = CameraUI()
        mainwin.show()
        app.exec_()
    run_app()