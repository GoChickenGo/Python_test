#c -*- coding: utf-8 -*-
"""
Created on Sat Aug 10 20:54:40 2019

@author: xinmeng
    ============================== ==============================================
    
    For general experiments in Dr. Daan's lab
    
    ============================== ==============================================
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
import PatchClamp.ui_patchclamp_sealtest
import NIDAQ.Waveformer_for_screening
from scipy import interpolate
import time
from datetime import datetime
from skimage.io import imread
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from NIDAQ.constants import HardwareConstants
import pyqtgraph.console
from PI_ObjectiveMotor.focuser import PIMotor
import ui_camera_lab

#Setting graph settings
#"""
#pg.setConfigOption('background', 'w')
#pg.setConfigOption('foreground', 'k')
#pg.setConfigOption('useOpenGL', True)
#pg.setConfigOption('leftButtonPan', False)
#""" 
class EmittingStream(QObject): #https://stackoverflow.com/questions/8356336/how-to-capture-output-of-pythons-interpreter-and-show-in-a-text-widget
    textWritten = pyqtSignal(str)
    def write(self, text):
        self.textWritten.emit(str(text)) # For updating notice from console.   

class Mainbody(QWidget):
    
    waveforms_generated = pyqtSignal(object, object, list, int)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        os.chdir(os.path.dirname(sys.argv[0]))# Set directory to current folder.
        self.setWindowIcon(QIcon('./Icons/Icon.png'))
        self.setFont(QFont("Arial"))
#        print(str(os.getcwd())+'Tupo')
#        sys.stdout = EmittingStream(textWritten = self.normalOutputWritten) # Uncomment here to link console output to textedit.
#        sys.stdout = sys.__stdout__
        #------------------------Initiating patchclamp class-------------------
        self.pmtTest = pmtimagingTest()
        self.pmtTest_contour = pmtimagingTest_contour()
        self.OC = 0.1
        #----------------------------------------------------------------------
        #----------------------------------GUI---------------------------------
        #----------------------------------------------------------------------
        self.setMinimumSize(1700,1200)
        self.setWindowTitle("Tupolev v1.0")
        self.layout = QGridLayout(self)
        # Setting tabs
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = NIDAQ.Waveformer_for_screening.WaveformGenerator()
        self.tab3 = PatchClamp.ui_patchclamp_sealtest.PatchclampSealTestUI()
        #self.tab4 = ui_camera_lab_5.CameraUI()
        self.tab5 = QWidget()
        
        # Add tabs
        self.tabs.addTab(self.tab1,"PMT imaging")
        self.tabs.addTab(self.tab2,"Waveform")
        self.tabs.addTab(self.tab3,"Patch clamp")
        #self.tabs.addTab(self.tab4,"Camera")        
        self.tabs.addTab(self.tab5,"Image analysis")
        
        self.savedirectory = os.path.join(os.path.expanduser("~"), "Desktop") #'M:/tnw/ist/do/projects/Neurophotonics/Brinkslab/Data'
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------GUI for set directory------------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************
        setdirectoryContainer = QGroupBox("Set directory")
        self.setdirectorycontrolLayout = QGridLayout()        
        
        self.saving_prefix = ''
        self.savedirectorytextbox = QLineEdit(self)
        self.savedirectorytextbox.setPlaceholderText('Saving directory')
        self.setdirectorycontrolLayout.addWidget(self.savedirectorytextbox, 0, 1)
        
        self.prefixtextbox = QLineEdit(self)
        self.prefixtextbox.setPlaceholderText('Prefix')
        self.setdirectorycontrolLayout.addWidget(self.prefixtextbox, 0, 0)
        
        #self.setdirectorycontrolLayout.addWidget(QLabel("Saving prefix:"), 0, 0)
        
        self.toolButtonOpenDialog = QtWidgets.QPushButton('Click me!')
        self.toolButtonOpenDialog.setStyleSheet("QPushButton {color:teal;background-color: pink; border-style: outset;border-radius: 5px;border-width: 2px;font: bold 14px;padding: 2px}"
                                                "QPushButton:pressed {color:yellow;background-color: pink; border-style: outset;border-radius: 5px;border-width: 2px;font: bold 14px;padding: 2px}")

        self.toolButtonOpenDialog.setObjectName("toolButtonOpenDialog")
        self.toolButtonOpenDialog.clicked.connect(self._open_file_dialog)
        
        self.setdirectorycontrolLayout.addWidget(self.toolButtonOpenDialog, 0, 2)
        
        setdirectoryContainer.setLayout(self.setdirectorycontrolLayout)
        setdirectoryContainer.setMaximumHeight(70)
        
        self.layout.addWidget(setdirectoryContainer, 0, 0)        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------GUI for AOTF---------------------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************
        AOTFcontrolContainer = QGroupBox("AOTF control")
        self.AOTFcontrolLayout = QGridLayout()
        
        self.slider640 = QSlider(Qt.Horizontal)
        self.slider640.setMinimum(0)
        self.slider640.setMaximum(500)
        self.slider640.setTickPosition(QSlider.TicksBothSides)
        self.slider640.setTickInterval(100)
        self.slider640.setSingleStep(1)
        self.line640 = QLineEdit(self)
        self.line640.setFixedWidth(60)
        self.slider640.sliderReleased.connect(lambda:self.updatelinevalue(640))
        self.slider640.sliderReleased.connect(lambda:self.execute_tread_single_sample_analog('640AO'))
        self.line640.returnPressed.connect(lambda:self.updatesider(640))
        
        self.ICON_off_AOTF = "./Icons/AOTF_off.png"
        self.AOTF_red_iconlabel = QLabel(self)
        self.AOTF_red_iconlabel.setPixmap(QPixmap(self.ICON_off_AOTF))
        self.AOTFcontrolLayout.addWidget(self.AOTF_red_iconlabel, 0, 0)
        
        self.switchbutton_640 = QPushButton("640")
        self.switchbutton_640.setStyleSheet("QPushButton {color:white;background-color: red; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:black;background-color: red; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.switchbutton_640.setCheckable(True)
        #self.holdingbutton.toggle()
        
        self.switchbutton_640.clicked.connect(lambda: self.execute_tread_single_sample_digital('640blanking'))
        self.switchbutton_640.clicked.connect(lambda: self.change_AOTF_icon('640blanking'))
        self.AOTFcontrolLayout.addWidget(self.switchbutton_640, 0, 1)
                
        self.slider532 = QSlider(Qt.Horizontal)
        self.slider532.setMinimum(0)
        self.slider532.setMaximum(500)
        self.slider532.setTickPosition(QSlider.TicksBothSides)
        self.slider532.setTickInterval(100)
        self.slider532.setSingleStep(1)
        self.line532 = QLineEdit(self)
        self.line532.setFixedWidth(60)
        self.slider532.sliderReleased.connect(lambda:self.updatelinevalue(532))
        self.slider532.sliderReleased.connect(lambda:self.execute_tread_single_sample_analog('532AO'))
        self.line532.returnPressed.connect(lambda:self.updatesider(532))
        
        self.AOTF_green_iconlabel = QLabel(self)
        self.AOTF_green_iconlabel.setPixmap(QPixmap(self.ICON_off_AOTF))
        self.AOTFcontrolLayout.addWidget(self.AOTF_green_iconlabel, 1, 0)
        
        self.switchbutton_532 = QPushButton("532")
        self.switchbutton_532.setStyleSheet("QPushButton {color:white;background-color: green; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:black;background-color: green; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.switchbutton_532.setCheckable(True)
        #self.holdingbutton.toggle()
        
        self.switchbutton_532.clicked.connect(lambda: self.execute_tread_single_sample_digital('532blanking'))
        self.switchbutton_532.clicked.connect(lambda: self.change_AOTF_icon('532blanking'))
        self.AOTFcontrolLayout.addWidget(self.switchbutton_532, 1, 1)
        
        self.slider488 = QSlider(Qt.Horizontal)
        self.slider488.setMinimum(0)
        self.slider488.setMaximum(500)
        self.slider488.setTickPosition(QSlider.TicksBothSides)
        self.slider488.setTickInterval(100)
        self.slider488.setSingleStep(1)
        self.line488 = QLineEdit(self)
        self.line488.setFixedWidth(60)
        self.slider488.sliderReleased.connect(lambda:self.updatelinevalue(488))
        self.slider488.sliderReleased.connect(lambda:self.execute_tread_single_sample_analog('488AO'))
        self.line488.returnPressed.connect(lambda:self.updatesider(488))
        
        self.AOTF_blue_iconlabel = QLabel(self)
        self.AOTF_blue_iconlabel.setPixmap(QPixmap(self.ICON_off_AOTF))
        self.AOTFcontrolLayout.addWidget(self.AOTF_blue_iconlabel, 2, 0)
        
        self.switchbutton_488 = QPushButton("488")
        self.switchbutton_488.setStyleSheet("QPushButton {color:white;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:black;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.switchbutton_488.setCheckable(True)
        #self.holdingbutton.toggle()
        
        self.switchbutton_488.clicked.connect(lambda: self.execute_tread_single_sample_digital('488blanking'))
        self.switchbutton_488.clicked.connect(lambda: self.change_AOTF_icon('488blanking'))
        self.AOTFcontrolLayout.addWidget(self.switchbutton_488, 2, 1)        
        
        self.AOTFcontrolLayout.addWidget(self.slider640, 0, 2)
        self.AOTFcontrolLayout.addWidget(self.line640, 0, 3)
        self.AOTFcontrolLayout.addWidget(self.slider532, 1, 2)
        self.AOTFcontrolLayout.addWidget(self.line532, 1, 3)
        self.AOTFcontrolLayout.addWidget(self.slider488, 2, 2)
        self.AOTFcontrolLayout.addWidget(self.line488, 2, 3)
        
        AOTFcontrolContainer.setLayout(self.AOTFcontrolLayout)
        AOTFcontrolContainer.setMaximumHeight(300)
        self.layout.addWidget(AOTFcontrolContainer, 1, 0)
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------GUI for Stage--------------------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************
        stagecontrolContainer = QGroupBox("Stage control")
        self.stagecontrolLayout = QGridLayout()
        
        self.stage_upwards = QPushButton("↑")
        self.stage_upwards.setStyleSheet("QPushButton {color:white;background-color: Olive; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        self.stagecontrolLayout.addWidget(self.stage_upwards, 1, 2)
        self.stage_upwards.clicked.connect(lambda: self.sample_stage_move_upwards())
        self.stage_upwards.setShortcut('w')
        
        self.stage_left = QPushButton("←")
        self.stage_left.setStyleSheet("QPushButton {color:white;background-color: Olive; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        self.stagecontrolLayout.addWidget(self.stage_left, 2, 1)
        self.stage_left.clicked.connect(lambda: self.sample_stage_move_leftwards())
        self.stage_left.setShortcut('a')
        
        self.stage_right = QPushButton("→")
        self.stage_right.setStyleSheet("QPushButton {color:white;background-color: Olive; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        self.stagecontrolLayout.addWidget(self.stage_right, 2, 3)
        self.stage_right.clicked.connect(lambda: self.sample_stage_move_rightwards())
        self.stage_right.setShortcut('d')
        
        self.stage_down = QPushButton("↓")
        self.stage_down.setStyleSheet("QPushButton {color:white;background-color: Olive; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        self.stagecontrolLayout.addWidget(self.stage_down, 2, 2)
        self.stage_down.clicked.connect(lambda: self.sample_stage_move_downwards())
        self.stage_down.setShortcut('s')
        
        self.stage_speed = QSpinBox(self)
        self.stage_speed.setMinimum(-10000)
        self.stage_speed.setMaximum(10000)
        self.stage_speed.setValue(300)
        self.stage_speed.setSingleStep(100)        
        self.stagecontrolLayout.addWidget(self.stage_speed, 0, 1)
        self.stagecontrolLayout.addWidget(QLabel("Moving speed:"), 0, 0)
        
        self.led_Label = QLabel("White LED: ")
        self.stagecontrolLayout.addWidget(self.led_Label, 0, 2)
        
        self.switchbutton_LED = QPushButton()
        #self.switchbutton_LED.setStyleSheet("QPushButton {color:white;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            #"QPushButton:pressed {color:black;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.switchbutton_LED.setCheckable(True)
        self.switchbutton_LED.setIcon(QIcon('./Icons/AOTF_off.png'))
        #self.holdingbutton.toggle()
        
        self.switchbutton_LED.clicked.connect(lambda: self.execute_tread_single_sample_digital('LED'))
        self.switchbutton_LED.clicked.connect(lambda: self.change_AOTF_icon('LED'))
        self.stagecontrolLayout.addWidget(self.switchbutton_LED, 0, 3)
        
        self.stage_current_pos_Label = QLabel("Current position: ")
        self.stagecontrolLayout.addWidget(self.stage_current_pos_Label, 1, 0)
        
        self.stage_goto = QPushButton("Move to:")
        self.stage_goto.setStyleSheet("QPushButton {color:white;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        self.stagecontrolLayout.addWidget(self.stage_goto, 3, 0)
        self.stage_goto.clicked.connect(lambda: self.sample_stage_move_towards())
        
        self.stage_goto_x = QLineEdit(self)
        self.stage_goto_x.setFixedWidth(60)
        self.stagecontrolLayout.addWidget(self.stage_goto_x, 3, 1)
        
        self.stage_goto_y = QLineEdit(self)
        self.stage_goto_y.setFixedWidth(60)
        self.stagecontrolLayout.addWidget(self.stage_goto_y, 3, 2)
        
        self.stagecontrolLayout.addWidget(QLabel('Click arrow to enable WASD keyboard control'), 4, 0, 1, 3)
        
        stagecontrolContainer.setLayout(self.stagecontrolLayout)
        stagecontrolContainer.setMaximumHeight(300)
        self.layout.addWidget(stagecontrolContainer, 2, 0)        
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------GUI for Filter movement----------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************
        ND_filtercontrolContainer = QGroupBox("ND filter control")
        self.NDfiltercontrolLayout = QGridLayout()
        
        bGBackupFromIntExt = QButtonGroup(self)

        self.filter1_pos0 = QPushButton('0')
        self.filter1_pos0.setCheckable(True)
        bGBackupFromIntExt.addButton(self.filter1_pos0)
        self.NDfiltercontrolLayout.addWidget(self.filter1_pos0, 0, 1)
        self.filter1_pos0.clicked.connect(lambda: self.filter_move_towards("COM9", 0))

        self.filter1_pos1 = QPushButton('1')
        self.filter1_pos1.setCheckable(True)
        bGBackupFromIntExt.addButton(self.filter1_pos1)
        self.NDfiltercontrolLayout.addWidget(self.filter1_pos1, 0, 2)    
        self.filter1_pos1.clicked.connect(lambda: self.filter_move_towards("COM9", 1))
        
        self.filter1_pos2 = QPushButton('2')
        self.filter1_pos2.setCheckable(True)
        bGBackupFromIntExt.addButton(self.filter1_pos2)
        self.NDfiltercontrolLayout.addWidget(self.filter1_pos2, 0, 3)
        self.filter1_pos2.clicked.connect(lambda: self.filter_move_towards("COM9", 2))
        
        self.filter1_pos3 = QPushButton('3')
        self.filter1_pos3.setCheckable(True)
        bGBackupFromIntExt.addButton(self.filter1_pos3)
        self.NDfiltercontrolLayout.addWidget(self.filter1_pos3, 0, 4)
        self.filter1_pos3.clicked.connect(lambda: self.filter_move_towards("COM9", 3)) 
        
        self.NDfiltercontrolLayout.addWidget(QLabel('Filter-1 pos: '), 0, 0)

        self.NDfiltercontrolLayout.addWidget(QLabel('Filter-2 pos: '), 1, 0)        
        bGBackupFromIntExt_1 = QButtonGroup(self)

        self.filter2_pos0 = QPushButton('0')
        self.filter2_pos0.setCheckable(True)
        bGBackupFromIntExt_1.addButton(self.filter2_pos0)
        self.NDfiltercontrolLayout.addWidget(self.filter2_pos0, 1, 1)
        self.filter2_pos0.clicked.connect(lambda: self.filter_move_towards("COM7", 0))

        self.filter2_pos1 = QPushButton('0.1')
        self.filter2_pos1.setCheckable(True)
        bGBackupFromIntExt_1.addButton(self.filter2_pos1)
        self.NDfiltercontrolLayout.addWidget(self.filter2_pos1, 1, 2)    
        self.filter2_pos1.clicked.connect(lambda: self.filter_move_towards("COM7", 1))
        
        self.filter2_pos2 = QPushButton('0.3')
        self.filter2_pos2.setCheckable(True)
        bGBackupFromIntExt_1.addButton(self.filter2_pos2)
        self.NDfiltercontrolLayout.addWidget(self.filter2_pos2, 1, 3)
        self.filter2_pos2.clicked.connect(lambda: self.filter_move_towards("COM7", 2))
        
        self.filter2_pos3 = QPushButton('0.5')
        self.filter2_pos3.setCheckable(True)
        bGBackupFromIntExt_1.addButton(self.filter2_pos3)
        self.NDfiltercontrolLayout.addWidget(self.filter2_pos3, 1, 4)
        self.filter2_pos3.clicked.connect(lambda: self.filter_move_towards("COM7", 3)) 
       
        ND_filtercontrolContainer.setLayout(self.NDfiltercontrolLayout)
        ND_filtercontrolContainer.setMaximumHeight(200)
        self.layout.addWidget(ND_filtercontrolContainer, 3, 0) 

        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------GUI for Objective Motor----------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************
        
        # Movement based on relative positions.
        ObjMotorcontrolContainer = QGroupBox("Objective motor control")
        self.ObjMotorcontrolLayout = QGridLayout()
        
        self.ObjMotor_connect = QPushButton("Connect")
        self.ObjMotor_connect.setStyleSheet("QPushButton {color:white;background-color: green; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        self.ObjMotorcontrolLayout.addWidget(self.ObjMotor_connect, 0, 0)
        self.ObjMotor_connect.clicked.connect(lambda: self.ConnectMotor())       
        
        self.ObjMotor_disconnect = QPushButton("Disconnect")
        self.ObjMotor_disconnect.setStyleSheet("QPushButton {color:white;background-color: firebrick; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        self.ObjMotorcontrolLayout.addWidget(self.ObjMotor_disconnect, 0, 1)
        self.ObjMotor_disconnect.clicked.connect(lambda: self.DisconnectMotor()) 
        
        self.ObjMotor_upwards = QPushButton("↑")
        self.ObjMotor_upwards.setStyleSheet("QPushButton {color:white;background-color: teal; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        self.ObjMotorcontrolLayout.addWidget(self.ObjMotor_upwards, 2, 2)
        self.ObjMotor_upwards.clicked.connect(lambda: self.Motor_move_upwards())
#        self.ObjMotor_upwards.setShortcut('w')
        
        self.ObjMotor_down = QPushButton("↓")
        self.ObjMotor_down.setStyleSheet("QPushButton {color:white;background-color: teal; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        self.ObjMotorcontrolLayout.addWidget(self.ObjMotor_down, 3, 2)
        self.ObjMotor_down.clicked.connect(lambda: self.Motor_move_downwards())
#        self.stage_down.setShortcut('s')
        
        self.ObjMotor_target = QDoubleSpinBox(self)
        self.ObjMotor_target.setMinimum(-10000)
        self.ObjMotor_target.setMaximum(10000)
        self.ObjMotor_target.setDecimals(6)
#        self.ObjMotor_target.setValue(3.45)
        self.ObjMotor_target.setSingleStep(0.001)        
        self.ObjMotorcontrolLayout.addWidget(self.ObjMotor_target, 1, 1)
        self.ObjMotorcontrolLayout.addWidget(QLabel("Target:"), 1, 0)
        
        self.ObjMotor_current_pos_Label = QLabel("Current position: ")
        self.ObjMotorcontrolLayout.addWidget(self.ObjMotor_current_pos_Label, 2, 0)
        
        self.ObjMotor_goto = QPushButton("Move")
        self.ObjMotor_goto.setStyleSheet("QPushButton {color:white;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        self.ObjMotorcontrolLayout.addWidget(self.ObjMotor_goto, 1, 2)
        self.ObjMotor_goto.clicked.connect(self.MoveMotor)
        
        self.ObjMotor_step = QDoubleSpinBox(self)
        self.ObjMotor_step.setMinimum(-10000)
        self.ObjMotor_step.setMaximum(10000)
        self.ObjMotor_step.setDecimals(6)
        self.ObjMotor_step.setValue(0.001)
        self.ObjMotor_step.setSingleStep(0.001)        
        self.ObjMotorcontrolLayout.addWidget(self.ObjMotor_step, 3, 1)
        self.ObjMotorcontrolLayout.addWidget(QLabel("Step: "), 3, 0)  
        
        ObjMotorcontrolContainer.setLayout(self.ObjMotorcontrolLayout)
        ObjMotorcontrolContainer.setMaximumHeight(300)
        self.layout.addWidget(ObjMotorcontrolContainer, 4, 0)          
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------GUI for camera button------------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------  
        #**************************************************************************************************************************************        
        self.open_cam = QPushButton('Open Camera')
        self.open_cam.clicked.connect(self.open_camera)
        self.layout.addWidget(self.open_cam,5,0)
        
        self.console_text_edit = QTextEdit()
        self.console_text_edit.setFontItalic(True)
        self.console_text_edit.setPlaceholderText('Notice board from console.')
        self.console_text_edit.setMaximumHeight(200)
        self.layout.addWidget(self.console_text_edit, 6, 0)
         
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
        self.pmtvideoWidget.resize(150,150)
        self.pmt_roiwidget.addLabel('ROI', row=0, col=0) 
        # create ROI
        self.vb_2 = self.pmt_roiwidget.addViewBox(row=1, col=0, lockAspect=True, colspan=1)
        self.vb_2.name = 'ROI'
        
        self.pmtimgroi = pg.ImageItem()
        self.vb_2.addItem(self.pmtimgroi)        
        #self.roi = pg.RectROI([20, 20], [20, 20], pen=(0,9))
        #r1 = QRectF(0, 0, 895, 500)
        self.roi = pg.PolyLineROI([[0,0], [80,0], [80,80], [0,80]], closed=True, pen=(0,9))#, maxBounds=r1
        #self.roi.addScaleHandle([1,0], [1, 0])
        self.roi.sigHoverEvent.connect(lambda: self.show_handle_num()) # update handle numbers
        
        self.pmtvb = self.pmtvideoWidget.getView()
        self.pmtimageitem = self.pmtvideoWidget.getImageItem()
        self.pmtvb.addItem(self.roi)# add ROIs to main image
        
        self.pmtimageroiLayout.addWidget(self.pmt_roiwidget, 0, 0)
        
        pmtimageContainer.setMinimumWidth(1000)
        pmtroiContainer.setMaximumHeight(380)
        pmtroiContainer.setMaximumWidth(300)
        
        pmtimageContainer.setLayout(self.pmtimageLayout)
        pmtroiContainer.setLayout(self.pmtimageroiLayout)
        #----------------------------Contour-----------------------------------        
        pmtContourContainer = QGroupBox("Contour selection")
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
        self.contour_samprate.setSingleStep(10000)        
        self.pmtContourLayout.addWidget(self.contour_samprate, 3, 1)        
        self.pmtContourLayout.addWidget(QLabel("Sampling rate:"), 3, 0)
        
        self.generate_contour_sacn = QPushButton("Generate contour")
        self.generate_contour_sacn.setStyleSheet("QPushButton {color:white;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                                 "QPushButton:pressed {color:red;background-color: DarkOliveGreen; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        self.pmtContourLayout.addWidget(self.generate_contour_sacn, 4, 1)
        self.generate_contour_sacn.clicked.connect(lambda: self.generate_contour())
#        self.generate_contour_sacn.clicked.connect(lambda: self.generate_contour_for_waveform())
        
        self.do_contour_sacn = QPushButton("Continuous scan")
        self.do_contour_sacn.setStyleSheet("QPushButton {color:black;background-color: Aquamarine; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                           "QPushButton:pressed {color:red;background-color: Turquoise; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        self.pmtContourLayout.addWidget(self.do_contour_sacn, 5, 0)
        self.do_contour_sacn.clicked.connect(lambda: self.measure_pmt_contourscan())
        
        self.stopButton_contour = QPushButton("Stop")
        self.stopButton_contour.setStyleSheet("QPushButton {color:white;background-color: FireBrick; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                      "QPushButton:pressed {color:black;background-color: FireBrick; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.stopButton_contour.clicked.connect(lambda: self.stopMeasurement_pmt_contour())
        self.pmtContourLayout.addWidget(self.stopButton_contour, 5, 1)
        
        pmtContourContainer.setLayout(self.pmtContourLayout)
        #----------------------------Control-----------------------------------
        controlContainer = QGroupBox("Galvo Scanning Panel")
        self.controlLayout = QGridLayout()
        
        self.pmt_fps_Label = QLabel("Per frame: ")
        self.controlLayout.addWidget(self.pmt_fps_Label, 3, 5)
    
        self.saveButton_pmt = QPushButton("Save image")
        self.saveButton_pmt.setStyleSheet("QPushButton {color:DarkGreen;background-color: LimeGreen; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                          "QPushButton:pressed {color:DarkGreen;background-color: DarkOliveGreen; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.saveButton_pmt.clicked.connect(lambda: self.saveimage_pmt())
        self.controlLayout.addWidget(self.saveButton_pmt, 3, 6)
    
        self.startButton_pmt = QPushButton("Start")
        self.startButton_pmt.setStyleSheet("QPushButton {color:black;background-color: Aquamarine; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                           "QPushButton:pressed {color:black;background-color: Turquoise; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        self.startButton_pmt.clicked.connect(lambda: self.measure_pmt())

        self.controlLayout.addWidget(self.startButton_pmt, 3, 7)
        
        self.stopButton = QPushButton("Stop")
        self.stopButton.setStyleSheet("QPushButton {color:white;background-color: FireBrick; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                      "QPushButton:pressed {color:black;background-color: FireBrick; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.stopButton.clicked.connect(lambda: self.stopMeasurement_pmt())
        self.controlLayout.addWidget(self.stopButton, 3, 8)
        
        #-----------------------------------Galvo scanning------------------------------------------------------------------------
        self.textboxAA_pmt = QSpinBox(self)
        self.textboxAA_pmt.setMinimum(0)
        self.textboxAA_pmt.setMaximum(1000000)
        self.textboxAA_pmt.setValue(500000)
        self.textboxAA_pmt.setSingleStep(100000)        
        self.controlLayout.addWidget(self.textboxAA_pmt, 2, 0)        
        self.controlLayout.addWidget(QLabel("Sampling rate:"), 1, 0)
        
        #self.controlLayout.addWidget(QLabel("Galvo raster scanning : "), 1, 0)
        self.textbox1B_pmt = QSpinBox(self)
        self.textbox1B_pmt.setMinimum(-10)
        self.textbox1B_pmt.setMaximum(10)
        self.textbox1B_pmt.setValue(-3)
        self.textbox1B_pmt.setSingleStep(1)        
        self.controlLayout.addWidget(self.textbox1B_pmt, 1, 2)
        self.controlLayout.addWidget(QLabel("voltXMin"), 1, 1)

        self.textbox1C_pmt = QSpinBox(self)
        self.textbox1C_pmt.setMinimum(-10)
        self.textbox1C_pmt.setMaximum(10)
        self.textbox1C_pmt.setValue(3)
        self.textbox1C_pmt.setSingleStep(1)   
        self.controlLayout.addWidget(self.textbox1C_pmt, 2, 2)
        self.controlLayout.addWidget(QLabel("voltXMax"), 2, 1)

        self.textbox1D_pmt = QSpinBox(self)
        self.textbox1D_pmt.setMinimum(-10)
        self.textbox1D_pmt.setMaximum(10)
        self.textbox1D_pmt.setValue(-3)
        self.textbox1D_pmt.setSingleStep(1)   
        self.controlLayout.addWidget(self.textbox1D_pmt, 1, 4)
        self.controlLayout.addWidget(QLabel("voltYMin"), 1, 3)

        self.textbox1E_pmt = QSpinBox(self)
        self.textbox1E_pmt.setMinimum(-10)
        self.textbox1E_pmt.setMaximum(10)
        self.textbox1E_pmt.setValue(3)
        self.textbox1E_pmt.setSingleStep(1)   
        self.controlLayout.addWidget(self.textbox1E_pmt, 2, 4)
        self.controlLayout.addWidget(QLabel("voltYMax"), 2, 3)

        self.textbox1F_pmt = QComboBox()
        self.textbox1F_pmt.addItems(['500','256'])
        self.controlLayout.addWidget(self.textbox1F_pmt, 1, 6)
        self.controlLayout.addWidget(QLabel("X pixel number"), 1, 5)

        self.textbox1G_pmt = QComboBox()
        self.textbox1G_pmt.addItems(['500','256'])
        self.controlLayout.addWidget(self.textbox1G_pmt, 2, 6)
        self.controlLayout.addWidget(QLabel("Y pixel number"), 2, 5)

        self.textbox1H_pmt = QSpinBox(self)
        self.textbox1H_pmt.setMinimum(1)
        self.textbox1H_pmt.setMaximum(20)
        self.textbox1H_pmt.setValue(1)
        self.textbox1H_pmt.setSingleStep(1)
        self.controlLayout.addWidget(self.textbox1H_pmt, 1, 8)
        self.controlLayout.addWidget(QLabel("average over:"), 1, 7)
        
        controlContainer.setLayout(self.controlLayout)
        
        #---------------------------Set tab1 layout---------------------------
        pmtmaster = QGridLayout()
        pmtmaster.addWidget(pmtimageContainer, 0,0,2,1)
        pmtmaster.addWidget(pmtroiContainer,0,1)       
        pmtmaster.addWidget(pmtContourContainer,1,1)
        pmtmaster.addWidget(controlContainer,2,0,1,2)
        
        self.tab1.setLayout(pmtmaster)
        
        '''
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------GUI for Waveform tab-------------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************
        self.Galvo_samples = self.finalwave_640 = self.finalwave_488 = self.finalwave_532=self.finalwave_patch =self.handle_viewbox_coordinate_position_array_expanded_forDaq_waveform=None
        self.finalwave_cameratrigger=self.final_galvotrigger=self.finalwave_blankingall=self.finalwave_640blanking=self.finalwave_532blanking=self.finalwave_488blanking=self.finalwave_Perfusion_8 = self.finalwave_Perfusion_7 = self.finalwave_Perfusion_6 = self.finalwave_Perfusion_2 = self.finalwave_2Pshutter =  None
        
        AnalogContainer = QGroupBox("Analog signals")
        self.AnalogLayout = QGridLayout() #self.AnalogLayout manager
        
        
        self.button_execute = QPushButton('EXECUTE AD', self)
        self.button_execute.setStyleSheet("QPushButton {color:white;background-color: BlueViolet; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                          "QPushButton:pressed {color:black;background-color: BlueViolet; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.AnalogLayout.addWidget(self.button_execute, 3, 3)
        
        self.button_execute.clicked.connect(self.execute_tread)   
        self.button_execute.clicked.connect(self.startProgressBar)
        
        self.AnalogLayout.addWidget(QLabel('     Executing progress:'), 3, 4)
        self.waveform_progressbar = QProgressBar(self)
        self.waveform_progressbar.setMaximumWidth(250)
        self.waveform_progressbar.setMaximum(100)
        self.waveform_progressbar.setStyleSheet('QProgressBar {color: black;border: 2px solid grey; border-radius:8px;text-align: center;}'
                                                'QProgressBar::chunk {background-color: #CD96CD; width: 10px; margin: 0.5px;}')
        self.AnalogLayout.addWidget(self.waveform_progressbar, 3, 5)      
        
        self.textbox2A = QComboBox()
        self.textbox2A.addItems(['640 AO', 'galvos', '532 AO', '488 AO', 'V-patch'])
        self.AnalogLayout.addWidget(self.textbox2A, 3, 0)
        
        self.button2 = QPushButton('Add', self)
        self.button2.setStyleSheet("QPushButton {color:white;background-color: LimeGreen; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                   "QPushButton:pressed {color:OrangeRed;background-color: LimeGreen; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.AnalogLayout.addWidget(self.button2, 3, 1)
        
        self.button_del_analog = QPushButton('Delete', self)
        self.button_del_analog.setStyleSheet("QPushButton {color:white;background-color: Crimson; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                             "QPushButton:pressed {color:black;background-color: Crimson; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}") 
        self.AnalogLayout.addWidget(self.button_del_analog, 3, 2)        
        
        
        self.dictionary_switch_list = []

        self.button2.clicked.connect(self.chosen_wave)
        self.button_del_analog.clicked.connect(self.del_chosen_wave)
        #self.textbox2A.currentIndexChanged.connect(self.chosen_wave)
        self.wavetablayout= QGridLayout()
        
        self.wavetabs = QTabWidget()
        self.wavetab1 = QWidget()
        self.wavetab2 = QWidget()
        self.wavetab3 = QWidget()
        self.wavetab4 = QWidget()
        self.wavetab5 = QWidget()
        # Add tabs
        self.wavetabs.addTab(self.wavetab1,"Block")
        self.wavetabs.addTab(self.wavetab2,"Ramp")
        self.wavetabs.addTab(self.wavetab3,"Import")
        self.wavetabs.addTab(self.wavetab4,"Galvo")
        self.wavetabs.addTab(self.wavetab5,"Photocycle")        
      
        #------------------------------------------------------------------------------------------------------------------------------------
        #----------------------------------------------------------Waveform General settings-------------------------------------------------
        #------------------------------------------------------------------------------------------------------------------------------------
        ReadContainer = QGroupBox("General settings")
        self.ReadLayout = QGridLayout() #self.AnalogLayout manager

        self.textboxBB = QComboBox()
        self.textboxBB.addItems(['640AO', 'galvos', 'galvos_contour', '488AO', '532AO', 'patchAO','cameratrigger', 'blankingall', '640blanking','532blanking','488blanking', 'Perfusion_8', 'Perfusion_7', 'Perfusion_6', 'Perfusion_2'])
        self.ReadLayout.addWidget(self.textboxBB, 0, 1)
        self.ReadLayout.addWidget(QLabel("Reference waveform:"), 0, 0)

        self.button_all = QPushButton('Show waveforms', self)
        self.button_all.setStyleSheet("QPushButton {color:white;background-color: DeepSkyBlue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                      "QPushButton:pressed {color:black;background-color: DeepSkyBlue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.ReadLayout.addWidget(self.button_all, 0, 5)
        self.button_all.clicked.connect(self.show_all)

        self.button_stop_waveforms = QPushButton('Stop', self)
        self.button_stop_waveforms.setStyleSheet("QPushButton {color:white;background-color: red; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                                 "QPushButton:pressed {color:black;background-color: red; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        self.ReadLayout.addWidget(self.button_stop_waveforms, 0, 6)
        self.button_stop_waveforms.clicked.connect(self.stopMeasurement_daqer)        
                
        self.button_clear_canvas = QPushButton('Clear canvas', self)
        self.ReadLayout.addWidget(self.button_clear_canvas, 1, 6)
        
        self.button_clear_canvas.clicked.connect(self.clear_canvas)  
        
        self.textboxAA = QSpinBox(self)
        self.textboxAA.setMinimum(0)
        self.textboxAA.setMaximum(1000000)
        self.textboxAA.setValue(50000)
        self.textboxAA.setSingleStep(100000)        
        self.ReadLayout.addWidget(self.textboxAA, 0, 3)
        self.ReadLayout.addWidget(QLabel("Sampling rate for all:"), 0, 2)
        
        # Checkbox for saving waveforms
        self.textboxsavingwaveforms= QCheckBox("Save wavefroms")
        self.textboxsavingwaveforms.setChecked(True)
        self.textboxsavingwaveforms.setStyleSheet('color:CadetBlue;font:bold "Times New Roman"')
        self.ReadLayout.addWidget(self.textboxsavingwaveforms, 0, 4) 
        
        # Read-in channels
        self.textbox111A = QCheckBox("---PMT---")
        self.textbox111A.setStyleSheet('color:CadetBlue;font:bold "Times New Roman"')
        self.ReadLayout.addWidget(self.textbox111A, 1, 1)     

        self.textbox222A = QCheckBox("---Vp---")
        self.textbox222A.setStyleSheet('color:Indigo;font:bold "Times New Roman"')
        self.ReadLayout.addWidget(self.textbox222A, 1, 2)   
        
        self.textbox333A = QCheckBox("---Ip---")
        self.textbox333A.setStyleSheet('color:DarkSlateGray	;font:bold "Times New Roman"')
        self.ReadLayout.addWidget(self.textbox333A, 1, 3)
        
        self.ReadLayout.addWidget(QLabel("Recording channels: "), 1, 0)
        
        self.clock_source = QComboBox()
        self.clock_source.addItems(['Dev1 as clock source', 'Cam as clock source'])
        self.ReadLayout.addWidget(self.clock_source, 1, 4)
        
        ReadContainer.setLayout(self.ReadLayout)

        # ------------------------------------------------------ANALOG-----------------------------------------------------------        

        
        # Tab for general block wave
        self.textbox2B = QLineEdit(self)
        self.wavetablayout.addWidget(self.textbox2B, 0, 1)
        self.wavetablayout.addWidget(QLabel("Frequency in period:"), 0, 0)

        self.textbox2C = QLineEdit(self)
        self.textbox2C.setPlaceholderText('0')
        self.wavetablayout.addWidget(self.textbox2C, 1, 1)
        self.wavetablayout.addWidget(QLabel("Offset (ms):"), 1, 0)
        
        self.textbox2D = QLineEdit(self)
        self.wavetablayout.addWidget(self.textbox2D, 0, 3)
        self.wavetablayout.addWidget(QLabel("Duration (ms, 1 cycle):"), 0, 2)   
        
        self.textbox2E = QLineEdit(self)
        self.textbox2E.setPlaceholderText('1')
        self.wavetablayout.addWidget(self.textbox2E, 1, 3)
        self.wavetablayout.addWidget(QLabel("Repeat:"), 1, 2) 
        
        self.wavetablayout.addWidget(QLabel("DC (%):"), 0, 4)
        self.textbox2F = QComboBox()
        self.textbox2F.addItems(['50','100','10','5','0'])
        self.wavetablayout.addWidget(self.textbox2F, 0, 5)
        
        self.textbox2G = QLineEdit(self)
        self.textbox2G.setPlaceholderText('0')
        self.wavetablayout.addWidget(self.textbox2G, 1, 5)
        self.wavetablayout.addWidget(QLabel("Gap between repeat (samples):"), 1, 4)
        
        self.wavetablayout.addWidget(QLabel("Starting amplitude (V):"), 2, 0)
        self.textbox2H = QDoubleSpinBox(self)
        self.textbox2H.setMinimum(-10)
        self.textbox2H.setMaximum(10)
        self.textbox2H.setValue(5)
        self.textbox2H.setSingleStep(0.5)  
        self.wavetablayout.addWidget(self.textbox2H, 2, 1)        

        self.textbox2I = QLineEdit(self)
        self.textbox2I.setPlaceholderText('0')
        self.wavetablayout.addWidget(self.textbox2I, 3, 1)
        self.wavetablayout.addWidget(QLabel("Baseline (V):"), 3, 0)

        self.wavetablayout.addWidget(QLabel("Step (V):"), 2, 2)
        self.textbox2J = QDoubleSpinBox(self)
        self.textbox2J.setMinimum(-10)
        self.textbox2J.setMaximum(10)
        self.textbox2J.setValue(5)
        self.textbox2J.setSingleStep(0.5)
        self.wavetablayout.addWidget(self.textbox2J, 2, 3)

        self.wavetablayout.addWidget(QLabel("Cycles:"), 3, 2)
        self.textbox2K = QSpinBox(self)
        self.textbox2K.setMinimum(0)
        self.textbox2K.setMaximum(100)
        self.textbox2K.setValue(1)
        self.textbox2K.setSingleStep(1) 
        self.wavetablayout.addWidget(self.textbox2K, 3, 3)
                
        self.wavetab1.setLayout(self.wavetablayout)
        
        # Tab for general Pramp wave
        self.wavetablayout_ramp= QGridLayout()
        self.textbox2B_ramp = QLineEdit(self)
        self.wavetablayout_ramp.addWidget(self.textbox2B_ramp, 0, 1)
        self.wavetablayout_ramp.addWidget(QLabel("Frequency in period:"), 0, 0)

        self.textbox2C_ramp = QLineEdit(self)
        self.textbox2C_ramp.setPlaceholderText('0')
        self.wavetablayout_ramp.addWidget(self.textbox2C_ramp, 1, 1)
        self.wavetablayout_ramp.addWidget(QLabel("Offset (ms):"), 1, 0)
        
        self.textbox2D_ramp = QLineEdit(self)
        self.wavetablayout_ramp.addWidget(self.textbox2D_ramp, 0, 3)
        self.wavetablayout_ramp.addWidget(QLabel("Duration (ms, 1 cycle):"), 0, 2)  
        
        self.textbox2F_ramp = QLineEdit(self)
        self.textbox2F_ramp.setPlaceholderText('0.5')
        self.wavetablayout_ramp.addWidget(self.textbox2F_ramp, 0, 5)
        self.wavetablayout_ramp.addWidget(QLabel("Symmetry:"), 0, 4)
        
        
        self.textbox2E_ramp = QLineEdit(self)
        self.textbox2E_ramp.setPlaceholderText('1')
        self.wavetablayout_ramp.addWidget(self.textbox2E_ramp, 1, 3)
        self.wavetablayout_ramp.addWidget(QLabel("Repeat:"), 1, 2) 
        
        self.textbox2G_ramp = QLineEdit(self)
        self.textbox2G_ramp.setPlaceholderText('0')
        self.wavetablayout_ramp.addWidget(self.textbox2G_ramp, 1, 5)
        self.wavetablayout_ramp.addWidget(QLabel("Gap between repeat (samples):"), 1, 4)
        
        self.wavetablayout_ramp.addWidget(QLabel("Height (V):"), 2, 0)
        self.textbox2H_ramp = QDoubleSpinBox(self)
        self.textbox2H_ramp.setMinimum(-10)
        self.textbox2H_ramp.setMaximum(10)
        self.textbox2H_ramp.setValue(2)
        self.textbox2H_ramp.setSingleStep(0.5)  
        self.wavetablayout_ramp.addWidget(self.textbox2H_ramp, 2, 1)        

        self.textbox2I_ramp = QLineEdit(self)
        self.textbox2I_ramp.setPlaceholderText('0')
        self.wavetablayout_ramp.addWidget(self.textbox2I_ramp, 3, 1)
        self.wavetablayout_ramp.addWidget(QLabel("Baseline (V):"), 3, 0)

        self.wavetablayout_ramp.addWidget(QLabel("Step (V):"), 2, 2)
        self.textbox2J_ramp = QDoubleSpinBox(self)
        self.textbox2J_ramp.setMinimum(-10)
        self.textbox2J_ramp.setMaximum(10)
        self.textbox2J_ramp.setValue(1)
        self.textbox2J_ramp.setSingleStep(0.5)
        self.wavetablayout_ramp.addWidget(self.textbox2J_ramp, 2, 3)

        self.wavetablayout_ramp.addWidget(QLabel("Cycles:"), 3, 2)
        self.textbox2K_ramp = QSpinBox(self)
        self.textbox2K_ramp.setMinimum(0)
        self.textbox2K_ramp.setMaximum(100)
        self.textbox2K_ramp.setValue(1)
        self.textbox2K_ramp.setSingleStep(1) 
        self.wavetablayout_ramp.addWidget(self.textbox2K_ramp, 3, 3)
                
        self.wavetab2.setLayout(self.wavetablayout_ramp)
        # ------------------------------------------------------photocycle-----------------------------------------------------------        
        self.photocycletablayout = QGridLayout()
        
        # Tab for general block wave
        self.textbox_photocycleA = QLineEdit(self)
        self.photocycletablayout.addWidget(self.textbox_photocycleA, 0, 1)
        self.photocycletablayout.addWidget(QLabel("Frequency in period:"), 0, 0)

        self.textbox_photocycleB = QLineEdit(self)
        self.textbox_photocycleB.setPlaceholderText('100')
        self.photocycletablayout.addWidget(self.textbox_photocycleB, 1, 1)
        self.photocycletablayout.addWidget(QLabel("Offset (ms):"), 1, 0)
        
        self.textbox_photocycleC = QLineEdit(self)
        self.photocycletablayout.addWidget(self.textbox_photocycleC, 0, 3)
        self.photocycletablayout.addWidget(QLabel("Duration (ms, 1 cycle):"), 0, 2)   
        
        self.textbox_photocycleD = QLineEdit(self)
        self.textbox_photocycleD.setPlaceholderText('10')
        self.photocycletablayout.addWidget(self.textbox_photocycleD, 1, 3)
        self.photocycletablayout.addWidget(QLabel("Repeat:"), 1, 2) 
        
        self.photocycletablayout.addWidget(QLabel("DC (%):"), 0, 4)
        self.textbox_photocycleE = QComboBox()
        self.textbox_photocycleE.addItems(['50','100','0'])
        self.photocycletablayout.addWidget(self.textbox_photocycleE, 0, 5)
        
        self.textbox_photocycleF = QLineEdit(self)
        self.textbox_photocycleF.setPlaceholderText('100000')
        self.photocycletablayout.addWidget(self.textbox_photocycleF, 1, 5)
        self.photocycletablayout.addWidget(QLabel("Gap between repeat (samples):"), 1, 4)
        
        self.photocycletablayout.addWidget(QLabel("Starting amplitude (V):"), 2, 0)
        self.textbox_photocycleG = QDoubleSpinBox(self)
        self.textbox_photocycleG.setMinimum(-10)
        self.textbox_photocycleG.setMaximum(10)
        self.textbox_photocycleG.setValue(2)
        self.textbox_photocycleG.setSingleStep(0.5)  
        self.photocycletablayout.addWidget(self.textbox_photocycleG, 2, 1)        

        self.textbox_photocycleH = QLineEdit(self)
        self.textbox_photocycleH.setPlaceholderText('0')
        self.photocycletablayout.addWidget(self.textbox_photocycleH, 3, 1)
        self.photocycletablayout.addWidget(QLabel("Baseline (V):"), 3, 0)

        self.photocycletablayout.addWidget(QLabel("Step (V):"), 2, 2)
        self.textbox_photocycleI = QDoubleSpinBox(self)
        self.textbox_photocycleI.setMinimum(-10)
        self.textbox_photocycleI.setMaximum(10)
        self.textbox_photocycleI.setValue(0.33)
        self.textbox_photocycleI.setSingleStep(0.5)
        self.photocycletablayout.addWidget(self.textbox_photocycleI, 2, 3)

        self.photocycletablayout.addWidget(QLabel("Cycles:"), 3, 2)
        self.textbox_photocycleJ = QSpinBox(self)
        self.textbox_photocycleJ.setMinimum(0)
        self.textbox_photocycleJ.setMaximum(100)
        self.textbox_photocycleJ.setValue(1)
        self.textbox_photocycleJ.setSingleStep(1) 
        self.photocycletablayout.addWidget(self.textbox_photocycleJ, 3, 3)
        
        self.photocycletablayout.addWidget(QLabel("start_point:"), 3, 4)
        self.textbox_photocycleK = QSpinBox(self)
        self.textbox_photocycleK.setMinimum(0)
        self.textbox_photocycleK.setMaximum(100)
        self.textbox_photocycleK.setValue(2)
        self.textbox_photocycleK.setSingleStep(1) 
        self.photocycletablayout.addWidget(self.textbox_photocycleK, 3, 5)
        
        self.photocycletablayout.addWidget(QLabel("start_time:"), 3, 6)
        self.textbox_photocycleL = QDoubleSpinBox(self)
        self.textbox_photocycleL.setMinimum(0)
        self.textbox_photocycleL.setMaximum(100)
        self.textbox_photocycleL.setValue(0.5)
        self.textbox_photocycleL.setSingleStep(1) 
        self.photocycletablayout.addWidget(self.textbox_photocycleL, 3, 7)
        
        self.photocycletablayout.addWidget(QLabel("control_amplitude:"), 2, 4)
        self.textbox_photocycleM = QDoubleSpinBox(self)
        self.textbox_photocycleM.setMinimum(0)
        self.textbox_photocycleM.setMaximum(100)
        self.textbox_photocycleM.setValue(0.33)
        self.textbox_photocycleM.setSingleStep(1) 
        self.photocycletablayout.addWidget(self.textbox_photocycleM, 2, 5)
        
                
        self.wavetab5.setLayout(self.photocycletablayout)
        
        #----------------------------------------------Tab for importing waveform------------------------------------------------
        
        self.importtablayout= QGridLayout()
        self.import_tabs = QTabWidget()
        self.npy_import_tab = QWidget()
        self.npy_import_tablayout= QGridLayout()
        self.matlab_import_tab = QWidget()
        self.matlab_import_tablayout= QGridLayout()
        
        self.npy_import_tab.setLayout(self.npy_import_tablayout)
        self.matlab_import_tab.setLayout(self.matlab_import_tablayout)
        self.import_tabs.addTab(self.npy_import_tab, 'Python')
        self.import_tabs.addTab(self.matlab_import_tab, 'Matlab')
        
        # Python import tab
        self.textbox_loadwave = QLineEdit(self)        
        self.npy_import_tablayout.addWidget(self.textbox_loadwave, 0, 0)
        
        self.button_import_np_browse = QPushButton('Browse', self)
        self.npy_import_tablayout.addWidget(self.button_import_np_browse, 0, 1) 
        
        self.button_import_np_browse.clicked.connect(self.get_wave_file_np)
        
        self.button_import_np_load = QPushButton('Load', self)
        self.npy_import_tablayout.addWidget(self.button_import_np_load, 0, 2)
        self.button_import_np_load.clicked.connect(self.load_wave_np)

        self.importtablayout.addWidget(self.import_tabs,0,0)
        self.wavetab3.setLayout(self.importtablayout)
        
        #----------------------------------------------Tab for galvo------------------------------------------------
        #----------------------------------------------Galvo scanning----------------------------------------------
        
        self.galvotablayout= QGridLayout()
        self.galvos_tabs = QTabWidget()
        self.normal_galvo_tab = QWidget()
        self.galvo_raster_tablayout= QGridLayout()
        self.contour_galvo_tab = QWidget()
        self.galvo_contour_tablayout= QGridLayout()
        #self.controlLayout.addWidget(QLabel("Galvo raster scanning : "), 1, 0)
        self.textbox1B = QSpinBox(self)
        self.textbox1B.setMinimum(-10)
        self.textbox1B.setMaximum(10)
        self.textbox1B.setValue(-3)
        self.textbox1B.setSingleStep(1)        
        self.galvo_raster_tablayout.addWidget(self.textbox1B, 0, 1)
        self.galvo_raster_tablayout.addWidget(QLabel("voltXMin"), 0, 0)

        self.textbox1C = QSpinBox(self)
        self.textbox1C.setMinimum(-10)
        self.textbox1C.setMaximum(10)
        self.textbox1C.setValue(3)
        self.textbox1C.setSingleStep(1)   
        self.galvo_raster_tablayout.addWidget(self.textbox1C, 1, 1)
        self.galvo_raster_tablayout.addWidget(QLabel("voltXMax"), 1, 0)

        self.textbox1D = QSpinBox(self)
        self.textbox1D.setMinimum(-10)
        self.textbox1D.setMaximum(10)
        self.textbox1D.setValue(-3)
        self.textbox1D.setSingleStep(1)   
        self.galvo_raster_tablayout.addWidget(self.textbox1D, 0, 3)
        self.galvo_raster_tablayout.addWidget(QLabel("voltYMin"), 0, 2)

        self.textbox1E = QSpinBox(self)
        self.textbox1E.setMinimum(-10)
        self.textbox1E.setMaximum(10)
        self.textbox1E.setValue(3)
        self.textbox1E.setSingleStep(1)   
        self.galvo_raster_tablayout.addWidget(self.textbox1E, 1, 3)
        self.galvo_raster_tablayout.addWidget(QLabel("voltYMax"), 1, 2)

        self.textbox1F = QComboBox()
        self.textbox1F.addItems(['500','256'])
        self.galvo_raster_tablayout.addWidget(self.textbox1F, 0, 5)
        self.galvo_raster_tablayout.addWidget(QLabel("X pixel number"), 0, 4)

        self.textbox1G = QComboBox()
        self.textbox1G.addItems(['500','256'])
        self.galvo_raster_tablayout.addWidget(self.textbox1G, 1, 5)
        self.galvo_raster_tablayout.addWidget(QLabel("Y pixel number"), 1, 4)
        
        self.textbox1I = QLineEdit(self)
        self.textbox1I.setPlaceholderText('0')
        self.galvo_raster_tablayout.addWidget(self.textbox1I, 2, 1)
        self.galvo_raster_tablayout.addWidget(QLabel("Offset (ms):"), 2, 0)
        
        self.textbox1J = QLineEdit(self)
        self.textbox1J.setPlaceholderText('0')
        self.galvo_raster_tablayout.addWidget(self.textbox1J, 2, 3)
        self.galvo_raster_tablayout.addWidget(QLabel("Gap between scans:"), 2, 2)       

        self.textbox1H = QSpinBox(self)
        self.textbox1H.setMinimum(1)
        self.textbox1H.setMaximum(20)
        self.textbox1H.setValue(1)
        self.textbox1H.setSingleStep(1)
        self.galvo_raster_tablayout.addWidget(self.textbox1H, 2, 5)
        self.galvo_raster_tablayout.addWidget(QLabel("average over:"), 2, 4)        

        self.textbox1K = QSpinBox(self)
        self.textbox1K.setMinimum(1)
        self.textbox1K.setMaximum(20)
        self.textbox1K.setValue(1)
        self.textbox1K.setSingleStep(1)
        self.galvo_raster_tablayout.addWidget(self.textbox1K, 0, 7)
        self.galvo_raster_tablayout.addWidget(QLabel("Repeat:"), 0, 6)  
        
        self.galvo_contour_label_1 = QLabel("Points in contour:")
        self.galvo_contour_tablayout.addWidget(self.galvo_contour_label_1, 0, 0)
        
        self.galvo_contour_label_2 = QLabel("Sampling rate: ")
        self.galvo_contour_tablayout.addWidget(self.galvo_contour_label_2, 0, 1)
        
        self.textbox1L = QSpinBox(self)
        self.textbox1L.setMinimum(000000)
        self.textbox1L.setMaximum(200000)
        self.textbox1L.setValue(1000)
        self.textbox1L.setSingleStep(500)
        self.galvo_contour_tablayout.addWidget(self.textbox1L, 0, 3)
        self.galvo_contour_tablayout.addWidget(QLabel("Last(ms):"), 0, 2)        
        
        self.normal_galvo_tab.setLayout(self.galvo_raster_tablayout)
        self.contour_galvo_tab.setLayout(self.galvo_contour_tablayout)
        self.galvos_tabs.addTab(self.normal_galvo_tab, 'Raster scanning')
        self.galvos_tabs.addTab(self.contour_galvo_tab, 'Contour scanning')

        self.galvotablayout.addWidget(self.galvos_tabs,0,0)
        '''
        '''
        self.button1 = QPushButton('SHOW WAVE', self)
        self.galvotablayout.addWidget(self.button1, 1, 11)
        
        self.button1.clicked.connect(self.generate_galvos)
        self.button1.clicked.connect(self.generate_galvos_graphy)
        
        self.button_triggerforcam = QPushButton('With trigger!', self)
        self.galvotablayout.addWidget(self.button_triggerforcam, 2, 9)
        
        self.textbox1K = QComboBox()
        self.textbox1K.addItems(['0','1'])
        self.galvotablayout.addWidget(self.textbox1K, 2, 10)
        
        self.button_triggerforcam.clicked.connect(self.generate_galvotrigger)        
        self.button_triggerforcam.clicked.connect(self.generate_galvotrigger_graphy)
        '''
        '''
        self.wavetab4.setLayout(self.galvotablayout)
        
        self.AnalogLayout.addWidget(self.wavetabs, 4, 0, 2, 6) 
        
        AnalogContainer.setLayout(self.AnalogLayout)
        
        #------------------------------------------------------------------------------------------------------------------@@@@@
        #----------------------------------------------------------Digital-------------------------------------------------@@@@@
        #------------------------------------------------------------------------------------------------------------------@@@@@       
        DigitalContainer = QGroupBox("Digital signals")
        self.DigitalLayout = QGridLayout() #self.AnalogLayout manager
        
        self.textbox3A = QComboBox()
        self.textbox3A.addItems(['cameratrigger',
                                  'galvotrigger', 
                                  'blankingall',
                                  '640blanking',
                                  '532blanking',
                                  '488blanking',
                                  'Perfusion_8',
                                  'Perfusion_7',
                                  'Perfusion_6',
                                  'Perfusion_2',
                                  '2Pshutter'])
        self.DigitalLayout.addWidget(self.textbox3A, 0, 0)
        
        self.button3 = QPushButton('Add', self)
        self.button3.setStyleSheet("QPushButton {color:white;background-color: LimeGreen; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                   "QPushButton:pressed {color:OrangeRed;background-color: LimeGreen; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.DigitalLayout.addWidget(self.button3, 0, 1)
        self.button3.clicked.connect(self.chosen_wave_digital)
        #---------------------------------------------------------------------------------------------------------------------------        
        self.button_execute_digital = QPushButton('EXECUTE DIGITAL', self)
        self.button_execute_digital.setStyleSheet("QPushButton {color:white;background-color: BlueViolet; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                                  "QPushButton:pressed {color:black;background-color: BlueViolet; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.DigitalLayout.addWidget(self.button_execute_digital, 0, 3)
        
        self.button_del_digital = QPushButton('Delete', self)
        self.button_del_digital.setStyleSheet("QPushButton {color:white;background-color: Crimson; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                              "QPushButton:pressed {color:black;background-color: Crimson; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
  
        self.DigitalLayout.addWidget(self.button_del_digital, 0, 2)
        
        self.button_execute_digital.clicked.connect(self.execute_digital)
        #self.button_execute_digital.clicked.connect(self.startProgressBar)
        self.button_del_digital.clicked.connect(self.del_chosen_wave_digital)
        # ------------------------------------------------------Wave settings------------------------------------------
        self.digitalwavetablayout= QGridLayout()
        
        self.digitalwavetabs = QTabWidget()
        self.digitalwavetab1 = QWidget()
        self.digitalwavetab2 = QWidget()
        self.digitalwavetab3 = QWidget()

        # Add tabs
        self.digitalwavetabs.addTab(self.digitalwavetab1,"Block")
        #self.digitalwavetabs.addTab(self.digitalwavetab2,"Ramp")
        #self.digitalwavetabs.addTab(self.digitalwavetab3,"Matlab")

        
        self.textbox11B = QLineEdit(self)
        self.digitalwavetablayout.addWidget(self.textbox11B, 0, 1)
        self.digitalwavetablayout.addWidget(QLabel("Frequency in period:"), 0, 0)

        self.textbox11C = QLineEdit(self)
        self.textbox11C.setPlaceholderText('0')
        self.digitalwavetablayout.addWidget(self.textbox11C, 1, 1)
        self.digitalwavetablayout.addWidget(QLabel("Offset (ms):"), 1, 0)
        
        self.textbox11D = QLineEdit(self)
        self.digitalwavetablayout.addWidget(self.textbox11D, 0, 3)
        self.digitalwavetablayout.addWidget(QLabel("Duration (ms):"), 0, 2)   
        
        self.textbox11E = QLineEdit(self)
        self.textbox11E.setPlaceholderText('1')
        self.digitalwavetablayout.addWidget(self.textbox11E, 1, 3)
        self.digitalwavetablayout.addWidget(QLabel("Repeat:"), 1, 2) 
        
        self.digitalwavetablayout.addWidget(QLabel("DC (%):"), 0, 4)
        self.textbox11F = QComboBox()
        self.textbox11F.addItems(['50','10','0','100'])
        self.digitalwavetablayout.addWidget(self.textbox11F, 0, 5)

        self.textbox11G = QLineEdit(self)
        self.textbox11G.setPlaceholderText('0')
        self.digitalwavetablayout.addWidget(self.textbox11G, 1, 5)
        self.digitalwavetablayout.addWidget(QLabel("Gap between repeat (samples):"), 1, 4)
        
        self.digitalwavetab1.setLayout(self.digitalwavetablayout)      
        self.DigitalLayout.addWidget(self.digitalwavetabs, 2, 0, 3, 6) 

        DigitalContainer.setLayout(self.DigitalLayout)

        
        #------------------------------------------------------------------------------------------------------------------
        #----------------------------------------------------------Display win-------------------------------------------------
        #------------------------------------------------------------------------------------------------------------------  
        self.pw = pg.PlotWidget(title='Waveform plot')
        self.pw.setLabel('bottom', 'Time', units='s')
        self.pw.setLabel('left', 'Value', units='V')
        self.pw.addLine(x=0)
        self.pw.addLine(y=0)
        self.pw.setMinimumHeight(180)
        #------------------------------------------------------------------------------------------------------------------
        #----------------------------------------------------------Data win-------------------------------------------------
        #------------------------------------------------------------------------------------------------------------------  
        self.pw_data = pg.PlotWidget(title='Data')
        self.pw_data.setLabel('bottom', 'Time', units='s')
        self.pw_data.setMinimumHeight(180)
        #self.pw_data.setLabel('left', 'Value', units='V')
        #-------------------------------------------------------------Adding to master----------------------------------------
        master_waveform = QGridLayout()
        master_waveform.addWidget(AnalogContainer, 1, 0)
        master_waveform.addWidget(DigitalContainer, 2, 0)
        master_waveform.addWidget(ReadContainer, 0, 0)
        master_waveform.addWidget(self.pw, 3, 0)
        master_waveform.addWidget(self.pw_data, 4, 0)
        self.tab2.setLayout(master_waveform)
        '''
        #**************************************************************************************************************************************        
        #self.setLayout(pmtmaster)
        self.layout.addWidget(self.tabs, 0, 1, 8, 4)
        self.setLayout(self.layout)
        
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
                
        #------------------------------------------------------V, I curve display window-------------------------------------------------------
        self.Curvedisplay_Layout = QGridLayout()

        # a figure instance to plot on
        self.Matdisplay_figure = Figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.Matdisplay_figure_canvas = FigureCanvas(self.Matdisplay_figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.Matdisplay_toolbar = NavigationToolbar(self.Matdisplay_figure_canvas, self)

        # Just some button connected to `plot` method
        self.Matdisplay_button =QPushButton('Select nest folder')
        self.Matdisplay_button.clicked.connect(self.Matdisplay_plot)
        self.Matdisplay_draw_button =QPushButton('Draw!')
        self.Matdisplay_draw_button.clicked.connect(self.matdisplay_draw)       
        
        self.Matdisplay_clear_button =QPushButton('Clear')
        self.Matdisplay_clear_button.clicked.connect(self.matdisplay_clear)       
        
        self.Curvedisplay_savedirectorytextbox = QtWidgets.QLineEdit(self)
        self.Curvedisplay_Layout.addWidget(self.Curvedisplay_savedirectorytextbox, 0, 3)
        # set the layout
        self.Curvedisplay_Layout.addWidget(self.Matdisplay_toolbar, 1, 0, 1, 5)
        self.Curvedisplay_Layout.addWidget(self.Matdisplay_figure_canvas, 2, 0, 1, 5)
        self.Curvedisplay_Layout.addWidget(self.Matdisplay_button, 0, 4)
        self.Curvedisplay_Layout.addWidget(self.Matdisplay_draw_button, 0, 5)
        self.Curvedisplay_Layout.addWidget(self.Matdisplay_clear_button, 0, 6)
        
        self.checkboxWaveform = QCheckBox("Waveform")
        self.checkboxWaveform.setStyleSheet('color:CadetBlue;font:bold "Times New Roman"')
        self.checkboxWaveform.setChecked(True)
        self.Curvedisplay_Layout.addWidget(self.checkboxWaveform, 0, 0)  
        
        self.checkboxTrace = QCheckBox("Recorded trace")
        self.checkboxTrace.setStyleSheet('color:CadetBlue;font:bold "Times New Roman"')
        self.Curvedisplay_Layout.addWidget(self.checkboxTrace, 0, 1)  
        
        self.checkboxCam = QCheckBox("Cam trace")
        self.checkboxCam.setStyleSheet('color:CadetBlue;font:bold "Times New Roman"')
        
        self.Curvedisplay_Layout.addWidget(self.checkboxCam, 0, 2)
        
        #Wavefrom window
        self.pw_preset_waveform = pg.PlotWidget(title='Executed waveform')
        self.pw_preset_waveform.setLabel('bottom', 'Time', units='s')
        self.pw_preset_waveform.setLabel('left', 'Voltage', units='V')
#        self.Curvedisplay_Layout.addWidget(self.pw_preset_waveform, 0,0) 
        
        #Voltage window
        self.pw_patch_voltage = pg.PlotWidget(title='Voltage plot')
        self.pw_patch_voltage.setLabel('bottom', 'Time', units='s')
        self.pw_patch_voltage.setLabel('left', 'Voltage', units='mV')        
        
#        self.Curvedisplay_Layout.addWidget(self.pw_patch_voltage, 1,0)
        
        #Current window
        self.pw_patch_current = pg.PlotWidget(title='Current plot')
        self.pw_patch_current.setLabel('bottom', 'Time', units='s')
        self.pw_patch_current.setLabel('left', 'Current', units='pA')
        #self.Curvedisplay_Layout.addWidget(self.pw_patch_current, 1,0) 
        
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
#        self.Curvedisplay_Layout.addWidget(self.pw_patch_camtrace, 2,0) 

        self.vLine_cam = pg.InfiniteLine(pos=0.4, angle=90, movable=True)
        self.pw_patch_camtrace.addItem(self.vLine_cam, ignoreBounds=True)

#        self.Curvedisplay_Container.setLayout(self.Curvedisplay_Layout)
#        self.Curvedisplay_Container.setMaximumHeight(550)
        
        self.vLine.sigPositionChangeFinished.connect(self.showpointdata)
        self.vLine_cam.sigPositionChangeFinished.connect(self.showpointdata_camtrace)
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
            
        Display_Container_tabs_tab2 = QWidget()
        Display_Container_tabs_tab2.setLayout(self.Curvedisplay_Layout)
        Display_Container_tabs_tab1 = QWidget()
        Display_Container_tabs_tab1.setLayout(image_display_container_layout)
        
        # Add tabs
        Display_Container_tabs.addTab(Display_Container_tabs_tab1,"Graph display")
        Display_Container_tabs.addTab(Display_Container_tabs_tab2,"Trace display")   
        
        Display_Layout.addWidget(Display_Container_tabs, 0, 0)  
        Display_Container.setLayout(Display_Layout)        

        master_data_analysis = QGridLayout()
        master_data_analysis.addWidget(readimageContainer, 0, 0, 1, 2)
        master_data_analysis.addWidget(Display_Container, 1, 0, 1, 2)
#        master_data_analysis.addWidget(imageanalysis_average_Container, 2, 0, 1,1)
#        master_data_analysis.addWidget(imageanalysis_weight_Container, 2, 1, 1,1)
        self.tab5.setLayout(master_data_analysis)    
        '''
        ***************************************************************************************************************************************
        ************************************************************END of GUI*****************************************************************
        '''
        
    def __del__(self):
        # Restore sys.stdout
        sys.stdout = sys.__stdout__
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
        self.normalOutputWritten('Loading...'+'\n')
        self.videostack = imread(self.fileName)
        print(self.videostack.shape)
        self.normalOutputWritten('Video size: '+str(self.videostack.shape)+'\n')
        self.roi_average.maxBounds= QRectF(0,0,self.videostack.shape[2],self.videostack.shape[1])
        self.roi_weighted.maxBounds= QRectF(0,0,self.videostack.shape[2],self.videostack.shape[1])
        print('Loading complete, ready to fire')
        self.normalOutputWritten('Loading complete, ready to fire'+'\n')
        
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
        self.Matdisplay_figure_canvas.clear()
        
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
        

        
        #self.pw_averageimage.average_imgItem.setImage(self.imganalysis_averageimage)
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #--------------------------------------------------------------------------------------------------------------------------------------
        #------------------------------------------------------Functions for TAB 'PMT'---------------------------------------------------------
        #-------------------------------------------------------------------------------------------------------------------------------------- 
        #**************************************************************************************************************************************
    def measure_pmt(self):
        self.Daq_sample_rate_pmt = int(self.textboxAA_pmt.value())
        
        #Scanning settings
        Value_voltXMin = int(self.textbox1B_pmt.value())
        self.Value_voltXMax = int(self.textbox1C_pmt.value())
        Value_voltYMin = int(self.textbox1D_pmt.value())
        Value_voltYMax = int(self.textbox1E_pmt.value())
        self.Value_xPixels = int(self.textbox1F_pmt.currentText())
        Value_yPixels = int(self.textbox1G_pmt.currentText())
        self.averagenum =int(self.textbox1H_pmt.value())
        
        Totalscansamples = self.pmtTest.setWave(self.Daq_sample_rate_pmt, Value_voltXMin, self.Value_voltXMax, Value_voltYMin, Value_voltYMax, self.Value_xPixels, Value_yPixels, self.averagenum)
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
        
    def saveimage_pmt(self):
        Localimg = Image.fromarray(self.data_pmtcontineous) #generate an image object
        Localimg.save(os.path.join(self.savedirectory, 'PMT_'+ str(self.prefixtextbox.text()) + '_' +datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'.tif')) #save as tif
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
        self.ROIhandles = self.roi.getHandles()
        self.ROIhandles_nubmer = len(self.ROIhandles)
        self.contour_point_number = int(self.pointsinContour.value())
        self.handle_scene_coordinate_position_raw_list = self.roi.getSceneHandlePositions()
        self.handle_local_coordinate_position_raw_list = self.roi.getLocalHandlePositions()
        self.Daq_sample_rate_pmt = int(self.contour_samprate.value())
        self.tab2.galvo_contour_label_1.setText("Points in contour: %.d" % self.contour_point_number)
        self.tab2.galvo_contour_label_2.setText("Sampling rate: %.d" % self.Daq_sample_rate_pmt)
        
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
                    self.handle_viewbox_coordinate_position_array_expanded[:,0] = ((self.handle_viewbox_coordinate_position_array_expanded[:,0]-constants.pmt_3v_indentation_pixels)/500)*6-3
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
                self.normalOutputWritten('Contour speed is OK'+'\n')
            else:
                QMessageBox.warning(self,'OverLoad','Speed too high!',QMessageBox.Ok)
            if aGalvo > np.amax(abs(contour_x_acceleration)) and aGalvo > np.amax(abs(contour_y_acceleration)):
                print('Contour acceleration is OK')
                self.normalOutputWritten('Contour acceleration is OK'+'\n')
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
                    self.handle_viewbox_coordinate_position_array_expanded[:,0] = ((self.handle_viewbox_coordinate_position_array_expanded[:,0]-constants.pmt_3v_indentation_pixels)/500)*6-3
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
                self.normalOutputWritten('Contour speed is OK'+'\n')
            if aGalvo > np.amax(abs(contour_x_acceleration)) and aGalvo > np.amax(abs(contour_y_acceleration)):
                print('Contour acceleration is OK')
                self.normalOutputWritten('Contour acceleration is OK'+'\n')
                
        self.tab2.Daq_sample_rate_pmt = self.Daq_sample_rate_pmt
        self.tab2.handle_viewbox_coordinate_position_array_expanded_x = self.handle_viewbox_coordinate_position_array_expanded_x
        self.tab2.handle_viewbox_coordinate_position_array_expanded_y = self.handle_viewbox_coordinate_position_array_expanded_y
        self.tab2.time_per_contour = (1/int(self.contour_samprate.value())*1000)*self.contour_point_number
                
#    def generate_contour_for_waveform(self):
#        self.contour_time = int(self.textbox1L.value())
#        
#        repeatnum_contour = int(self.contour_time/self.time_per_contour)
#        self.repeated_contoursamples_1 = np.tile(self.handle_viewbox_coordinate_position_array_expanded_x, repeatnum_contour)
#        self.repeated_contoursamples_2 = np.tile(self.handle_viewbox_coordinate_position_array_expanded_y, repeatnum_contour)       
#        
#        self.handle_viewbox_coordinate_position_array_expanded_forDaq_waveform = np.vstack((self.repeated_contoursamples_1,self.repeated_contoursamples_2))
#        
#        self.tab2.handle_viewbox_coordinate_position_array_expanded_forDaq_waveform = self.handle_viewbox_coordinate_position_array_expanded_forDaq_waveform
#        self.tab2.GalvoContourLastTextbox
#        
#        return self.handle_viewbox_coordinate_position_array_expanded_forDaq_waveform
#        
#    def generate_galvos_contour_graphy(self):
#
#        self.xlabelhere_galvos = np.arange(len(self.handle_viewbox_coordinate_position_array_expanded_forDaq_waveform[1,:]))/self.Daq_sample_rate_pmt
#        self.PlotDataItem_galvos = PlotDataItem(self.xlabelhere_galvos, self.handle_viewbox_coordinate_position_array_expanded_forDaq_waveform[1,:])
#        self.PlotDataItem_galvos.setDownsampling(auto=True, method='mean')            
#        self.PlotDataItem_galvos.setPen('w')
#
#        self.pw.addItem(self.PlotDataItem_galvos)
#        self.textitem_galvos = pg.TextItem(text='Contour', color=('w'), anchor=(1, 1))
#        self.textitem_galvos.setPos(0, 5)
#        self.pw.addItem(self.textitem_galvos)
                    
    def stopMeasurement_pmt(self):
        """Stop the seal test."""
        self.pmtTest.aboutToQuitHandler()
        
    def stopMeasurement_pmt_contour(self):
        """Stop the seal test."""
        self.pmtTest_contour.aboutToQuitHandler()
    '''    
    def closeEvent(self, event):
        """On closing the application we have to make sure that the measuremnt
        stops and the device gets freed."""
        self.stopMeasurement()
    '''
    '''
        #--------------------------------------------------------------------------------------------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #------------------------------------------------Functions for Waveform Tab------------------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------  
        #**************************************************************************************************************************************
    def get_wave_file_np(self):
        self.wavenpfileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Single File', 'M:/tnw/ist/do/projects/Neurophotonics/Brinkslab/Data',"(*.npy)")
        self.textbox_loadwave.setText(self.wavenpfileName)
        
    def load_wave_np(self):
        temp_loaded_container = np.load(self.wavenpfileName, allow_pickle=True)

        try:
            self.uiDaq_sample_rate = int(os.path.split(self.wavenpfileName)[1][20:-4])
        except:
            try:
                self.uiDaq_sample_rate = int(float(self.wavenpfileName[self.wavenpfileName.find('sr_')+3:-4])) #Locate sr_ in the file name to get sampling rate.
            except:
                self.uiDaq_sample_rate = 50000
                
        if self.uiDaq_sample_rate != int(self.textboxAA.value()):
            print('ERROR: Sampling rates is different!')
            self.normalOutputWritten('ERROR: Sampling rates is different!'+'\n')
            QMessageBox.warning(self,'ERROR!','Sampling rates is different!',QMessageBox.Ok)
        
        for i in range(len(temp_loaded_container)):
            if temp_loaded_container[i]['Sepcification'] == '640AO':
                self.finalwave_640 = temp_loaded_container[i]['Waveform']
                self.generate_640AO_graphy()            
                self.set_switch('640AO')  
            elif temp_loaded_container[i]['Sepcification'] == '532AO':
                self.finalwave_532 = temp_loaded_container[i]['Waveform']
                self.generate_532AO_graphy()            
                self.set_switch('532AO') 
            elif temp_loaded_container[i]['Sepcification'] == '488AO':
                self.finalwave_488 = temp_loaded_container[i]['Waveform']
                self.generate_488AO_graphy()            
                self.set_switch('488AO') 
            elif temp_loaded_container[i]['Sepcification'] == 'patchAO':
                self.finalwave_patch = temp_loaded_container[i]['Waveform']
                self.generate_patchAO_graphy()            
                self.set_switch('patchAO') 
            elif temp_loaded_container[i]['Sepcification'] == 'cameratrigger':
                self.finalwave_cameratrigger = temp_loaded_container[i]['Waveform']
                self.generate_cameratrigger_graphy()            
                self.set_switch('cameratrigger') 
            elif temp_loaded_container[i]['Sepcification'] == 'galvotrigger':
                self.final_galvotrigger = temp_loaded_container[i]['Waveform']
                self.generate_galvotrigger_graphy()            
                self.set_switch('galvotrigger')                
            elif temp_loaded_container[i]['Sepcification'] == 'blankingall':
                self.finalwave_blankingall = temp_loaded_container[i]['Waveform']
                self.generate_blankingall_graphy()            
                self.set_switch('blankingall')
            elif temp_loaded_container[i]['Sepcification'] == '640blanking':
                self.finalwave_640blanking = temp_loaded_container[i]['Waveform']
                self.generate_640blanking_graphy()            
                self.set_switch('640blanking')
            elif temp_loaded_container[i]['Sepcification'] == '532blanking':
                self.finalwave_532blanking = temp_loaded_container[i]['Waveform']
                self.generate_532blanking_graphy()            
                self.set_switch('532blanking')
            elif temp_loaded_container[i]['Sepcification'] == '488blanking':
                self.finalwave_488blanking = temp_loaded_container[i]['Waveform']
                self.generate_488blanking_graphy()            
                self.set_switch('488blanking')
            elif temp_loaded_container[i]['Sepcification'] == 'Perfusion_8':
                self.finalwave_Perfusion_8 = temp_loaded_container[i]['Waveform']
                self.generate_Perfusion_8_graphy()            
                self.set_switch('Perfusion_8')
            elif temp_loaded_container[i]['Sepcification'] == 'Perfusion_7':
                self.finalwave_Perfusion_7 = temp_loaded_container[i]['Waveform']
                self.generate_Perfusion_7_graphy()            
                self.set_switch('Perfusion_7')
            elif temp_loaded_container[i]['Sepcification'] == 'Perfusion_6':
                self.finalwave_Perfusion_6 = temp_loaded_container[i]['Waveform']
                self.generate_Perfusion_6_graphy()            
                self.set_switch('Perfusion_6')
            elif temp_loaded_container[i]['Sepcification'] == 'Perfusion_2':
                self.finalwave_Perfusion_2 = temp_loaded_container[i]['Waveform']
                self.generate_Perfusion_2_graphy()            
                self.set_switch('Perfusion_2')
            elif temp_loaded_container[i]['Sepcification'] == '2Pshutter':
                self.finalwave_2Pshutter = temp_loaded_container[i]['Waveform']
                self.generate_2Pshutter_graphy()            
                self.set_switch('2Pshutter')
                
    def chosen_wave(self):
        # make sure that the square wave tab is active now
        if self.wavetabs.currentIndex() == 0:
            if self.textbox2A.currentText() == '640 AO':
                if self.finalwave_640 is not None:
                    self.pw.removeItem(self.PlotDataItem_640AO) 
                    self.pw.removeItem(self.textitem_640AO)
                self.generate_640AO()
                self.generate_640AO_graphy()            
                self.set_switch('640AO')            
                    
            elif self.textbox2A.currentText() == '532 AO':
                if self.finalwave_532 is not None:
                    self.pw.removeItem(self.PlotDataItem_532AO) 
                    self.pw.removeItem(self.textitem_532AO)
                self.generate_532AO()
                self.generate_532AO_graphy()
                self.set_switch('532AO')
            elif self.textbox2A.currentText() == '488 AO':
                if self.finalwave_488 is not None:
                    self.pw.removeItem(self.PlotDataItem_488AO) 
                    self.pw.removeItem(self.textitem_488AO)
                self.generate_488AO()
                self.generate_488AO_graphy()
                self.set_switch('488AO')
            elif self.textbox2A.currentText() == 'V-patch':
                if self.finalwave_patch is not None:
                    self.pw.removeItem(self.PlotDataItem_patch) 
                    self.pw.removeItem(self.textitem_patch)
                self.generate_patchAO()
                self.generate_patchAO_graphy()
                self.set_switch('patchAO')
                
        if self.wavetabs.currentIndex() == 1:
            if self.textbox2A.currentText() == '640 AO':
                if self.finalwave_640 is not None:
                    self.pw.removeItem(self.PlotDataItem_640AO) 
                    self.pw.removeItem(self.textitem_640AO)
                self.generate_ramp('640AO')
                self.generate_640AO_graphy()            
                self.set_switch('640AO')            
                    
            elif self.textbox2A.currentText() == '532 AO':
                if self.finalwave_532 is not None:
                    self.pw.removeItem(self.PlotDataItem_532AO) 
                    self.pw.removeItem(self.textitem_532AO)
                self.generate_ramp('532AO')
                self.generate_532AO_graphy()
                self.set_switch('532AO')
            elif self.textbox2A.currentText() == '488 AO':
                if self.finalwave_488 is not None:
                    self.pw.removeItem(self.PlotDataItem_488AO) 
                    self.pw.removeItem(self.textitem_488AO)
                self.generate_ramp('488AO')
                self.generate_488AO_graphy()
                self.set_switch('488AO')
            elif self.textbox2A.currentText() == 'V-patch':
                if self.finalwave_patch is not None:
                    self.pw.removeItem(self.PlotDataItem_patch) 
                    self.pw.removeItem(self.textitem_patch)
                self.generate_ramp('patchAO')
                self.generate_patchAO_graphy()
                self.set_switch('patchAO')                
                
        if self.wavetabs.currentIndex() == 4:
            if self.textbox2A.currentText() == '640 AO':
                if self.finalwave_640 is not None:
                    self.pw.removeItem(self.PlotDataItem_640AO) 
                    self.pw.removeItem(self.textitem_640AO)
                self.generate_photocycle_640()
                self.generate_640AO_graphy()            
                self.set_switch('640AO')            
                    
            elif self.textbox2A.currentText() == '532 AO':
                if self.finalwave_532 is not None:
                    self.pw.removeItem(self.PlotDataItem_532AO) 
                    self.pw.removeItem(self.textitem_532AO)
                self.generate_photocycle_532()
                self.generate_532AO_graphy()
                self.set_switch('532AO')
            elif self.textbox2A.currentText() == '488 AO':
                if self.finalwave_488 is not None:
                    self.pw.removeItem(self.PlotDataItem_488AO) 
                    self.pw.removeItem(self.textitem_488AO)
                self.generate_photocycle_488()
                self.generate_488AO_graphy()
                self.set_switch('488AO')
                
        if self.wavetabs.currentIndex() == 3:
            if self.galvos_tabs.currentIndex() == 0:
                if self.textbox2A.currentText() == 'galvos':
                    if self.Galvo_samples is not None:
                        self.pw.removeItem(self.PlotDataItem_galvos) 
                        self.pw.removeItem(self.textitem_galvos)
                    self.generate_galvos()
                    self.generate_galvos_graphy()
                    self.set_switch('galvos')
            elif self.galvos_tabs.currentIndex() == 1:
                if self.textbox2A.currentText() == 'galvos':
                    if self.handle_viewbox_coordinate_position_array_expanded_forDaq_waveform is not None:
                        self.pw.removeItem(self.PlotDataItem_galvos) 
                        self.pw.removeItem(self.textitem_galvos)
                    self.generate_contour_for_waveform()
                    self.generate_galvos_contour_graphy()
                    self.set_switch('galvos_contour')
            
    def del_chosen_wave(self):
        if self.textbox2A.currentText() == '640 AO':
            #button2.disconnect()
            self.pw.removeItem(self.PlotDataItem_640AO) 
            self.pw.removeItem(self.textitem_640AO)
            self.finalwave_640 = None
            self.del_set_switch('640AO')
            
        elif self.textbox2A.currentText() == '532 AO':
            self.pw.removeItem(self.PlotDataItem_532AO) 
            self.pw.removeItem(self.textitem_532AO)
            self.finalwave_532 = None
            self.del_set_switch('532AO')
        elif self.textbox2A.currentText() == '488 AO':
            self.pw.removeItem(self.PlotDataItem_488AO)   
            self.pw.removeItem(self.textitem_488AO)
            self.finalwave_488 = None
            self.del_set_switch('488AO')
        elif self.textbox2A.currentText() == 'V-patch':
            self.pw.removeItem(self.PlotDataItem_patch) 
            self.pw.removeItem(self.textitem_patch)
            self.finalwave_patch = None
            self.del_set_switch('patchAO')
        elif self.textbox2A.currentText() == 'galvos':
            if self.galvos_tabs.currentIndex() == 0:
                self.pw.removeItem(self.PlotDataItem_galvos)  
                self.pw.removeItem(self.textitem_galvos)
                self.finalwave_galvos = None
                self.del_set_switch('galvos')
            
    def chosen_wave_digital(self):        
        if self.textbox3A.currentText() == 'cameratrigger':
            if self.finalwave_cameratrigger is not None:
                self.pw.removeItem(self.PlotDataItem_cameratrigger) 
                self.pw.removeItem(self.textitem_cameratrigger)
            self.generate_cameratrigger()
            self.generate_cameratrigger_graphy()
            self.set_switch('cameratrigger')           
        elif self.textbox3A.currentText() == 'galvotrigger':
            if self.final_galvotrigger is not None:
                self.pw.removeItem(self.PlotDataItem_galvotrigger) 
                self.pw.removeItem(self.textitem_galvotrigger)
            self.generate_galvotrigger()
            self.generate_galvotrigger_graphy()
            self.set_switch('galvotrigger')
        elif self.textbox3A.currentText() == 'blankingall':
            if self.finalwave_blankingall is not None:
                self.pw.removeItem(self.PlotDataItem_blankingall) 
                self.pw.removeItem(self.textitem_blankingall)
            self.generate_blankingall()
            self.generate_blankingall_graphy()
            self.set_switch('blankingall')                                   
        elif self.textbox3A.currentText() == '640blanking':
            if self.finalwave_640blanking is not None:
                self.pw.removeItem(self.PlotDataItem_640blanking) 
                self.pw.removeItem(self.textitem_640blanking)
            self.generate_640blanking()
            self.generate_640blanking_graphy()
            self.set_switch('640blanking')                                 
        elif self.textbox3A.currentText() == '532blanking':
            if self.finalwave_532blanking is not None:
                self.pw.removeItem(self.PlotDataItem_532blanking) 
                self.pw.removeItem(self.textitem_532blanking)
            self.generate_532blanking()
            self.generate_532blanking_graphy()
            self.set_switch('532blanking')    
        elif self.textbox3A.currentText() == '488blanking':
            if self.finalwave_488blanking is not None:
                self.pw.removeItem(self.PlotDataItem_488blanking) 
                self.pw.removeItem(self.textitem_488blanking)
            self.generate_488blanking()
            self.generate_488blanking_graphy()
            self.set_switch('488blanking')
        elif self.textbox3A.currentText() == 'Perfusion_8':
            if self.finalwave_Perfusion_8 is not None:
                self.pw.removeItem(self.PlotDataItem_Perfusion_8) 
                self.pw.removeItem(self.textitem_Perfusion_8)
            self.generate_Perfusion_8()
            self.generate_Perfusion_8_graphy()
            self.set_switch('Perfusion_8')  
        elif self.textbox3A.currentText() == 'Perfusion_7':
            if self.finalwave_Perfusion_7 is not None:
                self.pw.removeItem(self.PlotDataItem_Perfusion_7) 
                self.pw.removeItem(self.textitem_Perfusion_7)
            self.generate_Perfusion_7()
            self.generate_Perfusion_7_graphy()
            self.set_switch('Perfusion_7')
        elif self.textbox3A.currentText() == 'Perfusion_6':
            if self.finalwave_Perfusion_6 is not None:
                self.pw.removeItem(self.PlotDataItem_Perfusion_6) 
                self.pw.removeItem(self.textitem_Perfusion_6)
            self.generate_Perfusion_6()
            self.generate_Perfusion_6_graphy()
            self.set_switch('Perfusion_6')
        elif self.textbox3A.currentText() == 'Perfusion_2':
            if self.finalwave_Perfusion_2 is not None:
                self.pw.removeItem(self.PlotDataItem_Perfusion_2) 
                self.pw.removeItem(self.textitem_Perfusion_2)
            self.generate_Perfusion_2()
            self.generate_Perfusion_2_graphy()
            self.set_switch('Perfusion_2')
        elif self.textbox3A.currentText() == '2Pshutter':
            if self.finalwave_2Pshutter is not None:
                self.pw.removeItem(self.PlotDataItem_2Pshutter) 
                self.pw.removeItem(self.textitem_2Pshutter)
            self.generate_2Pshutter()
            self.generate_2Pshutter_graphy()
            self.set_switch('2Pshutter') 

    def del_chosen_wave_digital(self):        
        if self.textbox3A.currentText() == 'cameratrigger':
            self.pw.removeItem(self.PlotDataItem_cameratrigger)   
            self.pw.removeItem(self.textitem_cameratrigger)
            self.finalwave_cameratrigger = None
            self.del_set_switch('cameratrigger')
          
        elif self.textbox3A.currentText() == 'galvotrigger':
            self.pw.removeItem(self.PlotDataItem_galvotrigger) 
            self.pw.removeItem(self.textitem_galvotrigger)
            self.final_galvotrigger = None
            self.del_set_switch('galvotrigger')
        elif self.textbox3A.currentText() == 'blankingall':
            self.pw.removeItem(self.PlotDataItem_blankingall) 
            self.pw.removeItem(self.textitem_blankingall)
            self.finalwave_blankingall = None
            self.del_set_switch('blankingall')
                                   
        elif self.textbox3A.currentText() == '640blanking':
            self.pw.removeItem(self.PlotDataItem_640blanking)    
            self.pw.removeItem(self.textitem_640blanking)
            self.finalwave_640blanking = None
            self.del_set_switch('640blanking')
                                 
        elif self.textbox3A.currentText() == '532blanking':
            self.pw.removeItem(self.PlotDataItem_532blanking)
            self.pw.removeItem(self.textitem_532blanking)
            self.finalwave_532blanking = None
            self.del_set_switch('532blanking')   
        elif self.textbox3A.currentText() == '488blanking':
            self.pw.removeItem(self.PlotDataItem_488blanking)   
            self.pw.removeItem(self.textitem_488blanking)
            self.finalwave_488blanking = None
            self.del_set_switch('488blanking')
        elif self.textbox3A.currentText() == 'Perfusion_8':
            self.pw.removeItem(self.PlotDataItem_Perfusion_8)   
            self.pw.removeItem(self.textitem_Perfusion_8)
            self.finalwave_Perfusion_8 = None
            self.del_set_switch('Perfusion_8')    
        elif self.textbox3A.currentText() == 'Perfusion_7':
            self.pw.removeItem(self.PlotDataItem_Perfusion_7)   
            self.pw.removeItem(self.textitem_Perfusion_7)
            self.finalwave_Perfusion_7 = None
            self.del_set_switch('Perfusion_7') 
        elif self.textbox3A.currentText() == 'Perfusion_6':
            self.pw.removeItem(self.PlotDataItem_Perfusion_6)   
            self.pw.removeItem(self.textitem_Perfusion_6)
            self.finalwave_Perfusion_6 = None
            self.del_set_switch('Perfusion_6') 
        elif self.textbox3A.currentText() == 'Perfusion_2':
            self.pw.removeItem(self.PlotDataItem_Perfusion_2)   
            self.pw.removeItem(self.textitem_Perfusion_2)
            self.finalwave_Perfusion_2 = None
            self.del_set_switch('Perfusion_2') 
        elif self.textbox3A.currentText() == '2Pshutter':
            self.pw.removeItem(self.PlotDataItem_2Pshutter)   
            self.pw.removeItem(self.textitem_2Pshutter)
            self.finalwave_2Pshutter = None
            self.del_set_switch('2Pshutter')                

        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #------------------------------------------------Functions for Waveform generating-----------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------  
        #**************************************************************************************************************************************
                              
    def generate_galvos(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        
        #Scanning settings
        #if int(self.textbox1A.currentText()) == 1:
        Value_voltXMin = int(self.textbox1B.value())
        Value_voltXMax = int(self.textbox1C.value())
        Value_voltYMin = int(self.textbox1D.value())
        Value_voltYMax = int(self.textbox1E.value())
        Value_xPixels = int(self.textbox1F.currentText())
        Value_yPixels = int(self.textbox1G.currentText())
        self.averagenum =int(self.textbox1H.value())
        self.repeatnum = int(self.textbox1K.value())
        if not self.textbox1I.text():
            self.Galvo_samples_offset = 1
            self.offsetsamples_galvo = []

        else:
            self.Galvo_samples_offset = int(self.textbox1I.text())
            
            self.offsetsamples_number_galvo = int((self.Galvo_samples_offset/1000)*self.uiDaq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
            self.offsetsamples_galvo = np.zeros(self.offsetsamples_number_galvo) # Be default offsetsamples_number is an integer.    
        #Generate galvo samples            
        self.samples_1, self.samples_2= wavegenerator.waveRecPic(sampleRate = self.uiDaq_sample_rate, imAngle = 0, voltXMin = Value_voltXMin, voltXMax = Value_voltXMax, 
                         voltYMin = Value_voltYMin, voltYMax = Value_voltYMax, xPixels = Value_xPixels, yPixels = Value_yPixels, 
                         sawtooth = True)
        #ScanArrayX = wavegenerator.xValuesSingleSawtooth(sampleRate = Daq_sample_rate, voltXMin = Value_voltXMin, voltXMax = Value_voltXMax, xPixels = Value_xPixels, sawtooth = True)
        #Totalscansamples = len(self.samples_1)*self.averagenum # Calculate number of samples to feed to scanner, by default it's one frame 
        self.ScanArrayXnum = int (len(self.samples_1)/Value_yPixels) # number of samples of each individual line of x scanning
        if not self.textbox1J.text():
            gap_sample = 0
            self.gapsamples_number_galvo = 0
        else:
            gap_sample = int(self.textbox1J.text())
            
            self.gapsamples_number_galvo = int((gap_sample/1000)*self.uiDaq_sample_rate) 

        #print(self.Digital_container_feeder[:, 0])
        
        self.repeated_samples_1 = np.tile(self.samples_1, self.averagenum)
        self.repeated_samples_2_yaxis = np.tile(self.samples_2, self.averagenum)
        
        self.PMT_data_index_array = np.ones(len(self.repeated_samples_1)) # In index array, indexes where there's the first image are 1.
        #Adding gap between scans
        self.gap_samples_1 =self.repeated_samples_1[-1]*np.ones(self.gapsamples_number_galvo)
        self.repeated_samples_1 = np.append(self.repeated_samples_1, self.gap_samples_1)     
        self.gap_samples_2 =self.repeated_samples_2_yaxis[-1]*np.ones(self.gapsamples_number_galvo)
        self.repeated_samples_2_yaxis = np.append(self.repeated_samples_2_yaxis, self.gap_samples_2) 
        
        self.PMT_data_index_array = np.append(self.PMT_data_index_array, np.zeros(self.gapsamples_number_galvo))
        
        self.repeated_samples_1 = np.tile(self.repeated_samples_1, self.repeatnum)
        self.repeated_samples_2_yaxis = np.tile(self.repeated_samples_2_yaxis, self.repeatnum)  
        
        for i in range(self.repeatnum): # Array value where sits the second PMT image will be 2, etc.
            if i == 0:
                self.PMT_data_index_array_repeated = self.PMT_data_index_array
            else:
                self.PMT_data_index_array_repeated = np.append(self.PMT_data_index_array_repeated, self.PMT_data_index_array*(i+1))


        self.repeated_samples_1 = np.append(self.offsetsamples_galvo, self.repeated_samples_1)
        self.repeated_samples_1 = np.append(self.repeated_samples_1 ,0)                        # Add 0 to clear up Daq
        self.repeated_samples_2_yaxis = np.append(self.offsetsamples_galvo, self.repeated_samples_2_yaxis)
        self.repeated_samples_2_yaxis = np.append(self.repeated_samples_2_yaxis ,0)
        
        self.PMT_data_index_array_repeated = np.append(self.offsetsamples_galvo, self.PMT_data_index_array_repeated)
        self.PMT_data_index_array_repeated = np.append(self.PMT_data_index_array_repeated ,0)    
        
        self.Galvo_samples = np.vstack((self.repeated_samples_1,self.repeated_samples_2_yaxis))
        
        return self.Galvo_samples
            
    def generate_galvos_graphy(self):

        self.xlabelhere_galvos = np.arange(len(self.repeated_samples_2_yaxis))/self.uiDaq_sample_rate    
        self.PlotDataItem_galvos = PlotDataItem(self.xlabelhere_galvos, self.repeated_samples_2_yaxis)
        self.PlotDataItem_galvos.setDownsampling(auto=True, method='mean')            
        self.PlotDataItem_galvos.setPen('w')

        self.pw.addItem(self.PlotDataItem_galvos)
        self.textitem_galvos = pg.TextItem(text='galvos', color=('w'), anchor=(1, 1))
        self.textitem_galvos.setPos(0, 5)
        self.pw.addItem(self.textitem_galvos)

            
    def generate_galvotrigger(self):
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        #Scanning settings
        #if int(self.textbox1A.currentText()) == 1:
        Value_voltXMin = int(self.textbox1B.value())
        Value_voltXMax = int(self.textbox1C.value())
        Value_voltYMin = int(self.textbox1D.value())
        Value_voltYMax = int(self.textbox1E.value())
        Value_xPixels = int(self.textbox1F.currentText())
        Value_yPixels = int(self.textbox1G.currentText())
        self.averagenum =int(self.textbox1H.value())
        repeatnum = int(self.textbox1K.value())
        if not self.textbox1I.text():
            self.Galvo_samples_offset = 1
            self.offsetsamples_galvo = []

        else:
            self.Galvo_samples_offset = int(self.textbox1I.text())
            
            self.offsetsamples_number_galvo = int((self.Galvo_samples_offset/1000)*self.uiDaq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
            self.offsetsamples_galvo = np.zeros(self.offsetsamples_number_galvo) # Be default offsetsamples_number is an integer.    
        #Generate galvo samples            
        self.samples_1, self.samples_2= wavegenerator.waveRecPic(sampleRate = self.uiDaq_sample_rate, imAngle = 0, voltXMin = Value_voltXMin, voltXMax = Value_voltXMax, 
                         voltYMin = Value_voltYMin, voltYMax = Value_voltYMax, xPixels = Value_xPixels, yPixels = Value_yPixels, 
                         sawtooth = True)
        self.ScanArrayXnum = int (len(self.samples_1)/Value_yPixels) # number of samples of each individual line of x scanning
        if not self.textbox1J.text():
            gap_sample = 0
            self.gapsamples_number_galvo = 0
        else:
            gap_sample = int(self.textbox1J.text())
            
            self.gapsamples_number_galvo = int((gap_sample/1000)*self.uiDaq_sample_rate)         
        #print(self.Digital_container_feeder[:, 0])
        
        self.repeated_samples_1 = np.tile(self.samples_1, self.averagenum)
        self.repeated_samples_2_yaxis = np.tile(self.samples_2, self.averagenum)

        #Adding gap between scans
        self.gap_samples_1 =self.repeated_samples_1[-1]*np.ones(self.gapsamples_number_galvo)
        self.repeated_samples_1 = np.append(self.repeated_samples_1, self.gap_samples_1)     
        self.gap_samples_2 =self.repeated_samples_2_yaxis[-1]*np.ones(self.gapsamples_number_galvo)
        self.repeated_samples_2_yaxis = np.append(self.repeated_samples_2_yaxis, self.gap_samples_2) 
        
        self.repeated_samples_1 = np.tile(self.repeated_samples_1, repeatnum)
        self.repeated_samples_2_yaxis = np.tile(self.repeated_samples_2_yaxis, repeatnum) 

        self.repeated_samples_1 = np.append(self.offsetsamples_galvo, self.repeated_samples_1)
        self.repeated_samples_2_yaxis = np.append(self.offsetsamples_galvo, self.repeated_samples_2_yaxis)
        
        samplenumber_oneframe = len(self.samples_1)
        
        self.true_sample_num_singleperiod_galvotrigger = round((20/1000)*self.uiDaq_sample_rate) # Default the trigger lasts for 20 ms.
        self.false_sample_num_singleperiod_galvotrigger = samplenumber_oneframe - self.true_sample_num_singleperiod_galvotrigger
        
        self.true_sample_singleperiod_galvotrigger = np.ones(self.true_sample_num_singleperiod_galvotrigger, dtype=bool)
        self.true_sample_singleperiod_galvotrigger[0] = False  # first one False to give a rise.
        
        self.sample_singleperiod_galvotrigger = np.append(self.true_sample_singleperiod_galvotrigger, np.zeros(self.false_sample_num_singleperiod_galvotrigger, dtype=bool))
        
        self.sample_repeatedperiod_galvotrigger = np.tile(self.sample_singleperiod_galvotrigger, self.averagenum)
        
        self.gap_samples_galvotrigger =np.zeros(self.gapsamples_number_galvo, dtype=bool)
        self.gap_samples_galvotrigger = np.append(self.sample_repeatedperiod_galvotrigger, self.gap_samples_galvotrigger)         
        self.repeated_gap_samples_galvotrigger = np.tile(self.gap_samples_galvotrigger, repeatnum)
        self.offset_galvotrigger = np.array(self.offsetsamples_galvo, dtype=bool)
        
        self.final_galvotrigger = np.append(self.offset_galvotrigger, self.repeated_gap_samples_galvotrigger)
        self.final_galvotrigger = np.append(self.final_galvotrigger, False)
        return self.final_galvotrigger
        
    def generate_galvotrigger_graphy(self):
        self.xlabelhere_galvos = np.arange(len(self.repeated_samples_2_yaxis))/self.uiDaq_sample_rate
        self.final_galvotrigger_forgraphy = self.final_galvotrigger.astype(int)
        self.PlotDataItem_galvotrigger = PlotDataItem(self.xlabelhere_galvos, self.final_galvotrigger_forgraphy)
        self.PlotDataItem_galvotrigger.setPen(100,100,200)
        self.PlotDataItem_galvotrigger.setDownsampling(auto=True, method='mean')
        self.pw.addItem(self.PlotDataItem_galvotrigger)
        
        self.textitem_galvotrigger = pg.TextItem(text='galvotrigger', color=(100,100,200), anchor=(1, 1))
        self.textitem_galvotrigger.setPos(0, -5)
        self.pw.addItem(self.textitem_galvotrigger)

        
    def generate_640AO(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_2 = float(self.textbox2B.text())
        if not self.textbox2C.text():
            self.uiwaveoffset_2 = 0
        else:
            self.uiwaveoffset_2 = int(self.textbox2C.text()) # in ms
        self.uiwaveperiod_2 = int(self.textbox2D.text())
        self.uiwaveDC_2 = int(self.textbox2F.currentText())
        if not self.textbox2E.text():
            self.uiwaverepeat_2 = 1
        else:
            self.uiwaverepeat_2 = int(self.textbox2E.text())
        if not self.textbox2G.text():
            self.uiwavegap_2 = 0
        else:
            self.uiwavegap_2 = int(self.textbox2G.text())
        self.uiwavestartamplitude_2 = float(self.textbox2H.value())
        if not self.textbox2I.text():
            self.uiwavebaseline_2 = 0
        else:
            self.uiwavebaseline_2 = float(self.textbox2I.text())
        self.uiwavestep_2 = float(self.textbox2J.value())
        self.uiwavecycles_2 = int(self.textbox2K.value())   
        
            
        s = generate_AO_for640(self.uiDaq_sample_rate, self.uiwavefrequency_2, self.uiwaveoffset_2, self.uiwaveperiod_2, self.uiwaveDC_2
                               , self.uiwaverepeat_2, self.uiwavegap_2, self.uiwavestartamplitude_2, self.uiwavebaseline_2, self.uiwavestep_2, self.uiwavecycles_2)
        self.finalwave_640 = s.generate()
        return self.finalwave_640
            
    def generate_640AO_graphy(self):            
        xlabelhere_640 = np.arange(len(self.finalwave_640))/self.uiDaq_sample_rate
        #plt.plot(xlabelhere_galvo, samples_1)
        self.PlotDataItem_640AO = PlotDataItem(xlabelhere_640, self.finalwave_640, downsample = 10)
        self.PlotDataItem_640AO.setPen('r')
        self.PlotDataItem_640AO.setDownsampling(ds=(int(self.textboxAA.value())/10), method='mean')
        self.pw.addItem(self.PlotDataItem_640AO)
        
        self.textitem_640AO = pg.TextItem(text='640 AO', color=('r'), anchor=(1, 1))
        self.textitem_640AO.setPos(0, 4)
        self.pw.addItem(self.textitem_640AO)
           

    def generate_488AO(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_488AO = float(self.textbox2B.text())
        if not self.textbox2C.text():
            self.uiwaveoffset_488AO = 0
        else:
            self.uiwaveoffset_488AO = int(self.textbox2C.text()) # in ms
        self.uiwaveperiod_488AO = int(self.textbox2D.text())
        self.uiwaveDC_488AO = int(self.textbox2F.currentText())
        if not self.textbox2E.text():
            self.uiwaverepeat_488AO = 1
        else:
            self.uiwaverepeat_488AO = int(self.textbox2E.text())
        if not self.textbox2G.text():
            self.uiwavegap_488AO = 0
        else:
            self.uiwavegap_488AO = int(self.textbox2G.text())
        self.uiwavestartamplitude_488AO = float(self.textbox2H.value())
        if not self.textbox2I.text():
            self.uiwavebaseline_488AO = 0
        else:
            self.uiwavebaseline_488AO = float(self.textbox2I.text())
        self.uiwavestep_488AO = float(self.textbox2J.value())
        self.uiwavecycles_488AO = int(self.textbox2K.value())   
                    
        s = generate_AO_for488(self.uiDaq_sample_rate, self.uiwavefrequency_488AO, self.uiwaveoffset_488AO, self.uiwaveperiod_488AO, self.uiwaveDC_488AO
                               , self.uiwaverepeat_488AO, self.uiwavegap_488AO, self.uiwavestartamplitude_488AO, self.uiwavebaseline_488AO, self.uiwavestep_488AO, self.uiwavecycles_488AO)
        self.finalwave_488 = s.generate()
        return self.finalwave_488
            
    def generate_488AO_graphy(self):
        xlabelhere_488 = np.arange(len(self.finalwave_488))/self.uiDaq_sample_rate
        #plt.plot(xlabelhere_galvo, samples_1)
        self.PlotDataItem_488AO = PlotDataItem(xlabelhere_488, self.finalwave_488)
        self.PlotDataItem_488AO.setPen('b')
        self.PlotDataItem_488AO.setDownsampling(auto=True, method='mean')
        self.pw.addItem(self.PlotDataItem_488AO)
        
        self.textitem_488AO = pg.TextItem(text='488 AO', color=('b'), anchor=(1, 1))
        self.textitem_488AO.setPos(0, 2)
        self.pw.addItem(self.textitem_488AO)

        
    def generate_532AO(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_532AO = float(self.textbox2B.text())
        if not self.textbox2C.text():
            self.uiwaveoffset_532AO = 0
        else:
            self.uiwaveoffset_532AO = int(self.textbox2C.text()) # in ms
        self.uiwaveperiod_532AO = int(self.textbox2D.text())
        self.uiwaveDC_532AO = int(self.textbox2F.currentText())
        if not self.textbox2E.text():
            self.uiwaverepeat_532AO = 1
        else:
            self.uiwaverepeat_532AO = int(self.textbox2E.text())
        if not self.textbox2G.text():
            self.uiwavegap_532AO = 0
        else:
            self.uiwavegap_532AO = int(self.textbox2G.text())
        self.uiwavestartamplitude_532AO = float(self.textbox2H.value())
        if not self.textbox2I.text():
            self.uiwavebaseline_532AO = 0
        else:
            self.uiwavebaseline_532AO = float(self.textbox2I.text())
        self.uiwavestep_532AO = float(self.textbox2J.value())
        self.uiwavecycles_532AO = int(self.textbox2K.value())   
        
        #if int(self.textbox4A.currentText()) == 1:
            
        s = generate_AO_for532(self.uiDaq_sample_rate, self.uiwavefrequency_532AO, self.uiwaveoffset_532AO, self.uiwaveperiod_532AO, self.uiwaveDC_532AO
                               , self.uiwaverepeat_532AO, self.uiwavegap_532AO, self.uiwavestartamplitude_532AO, self.uiwavebaseline_532AO, self.uiwavestep_532AO, self.uiwavecycles_532AO)
        self.finalwave_532 = s.generate()
        return self.finalwave_532
            
    def generate_532AO_graphy(self):
        xlabelhere_532 = np.arange(len(self.finalwave_532))/self.uiDaq_sample_rate
        self.PlotDataItem_532AO = PlotDataItem(xlabelhere_532, self.finalwave_532)
        self.PlotDataItem_532AO.setPen('g')
        self.PlotDataItem_532AO.setDownsampling(auto=True, method='mean')
        self.pw.addItem(self.PlotDataItem_532AO)
        
        self.textitem_532AO = pg.TextItem(text='532 AO', color=('g'), anchor=(1, 1))
        self.textitem_532AO.setPos(0, 3)
        self.pw.addItem(self.textitem_532AO)
        
    def generate_patchAO(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_patchAO = float(self.textbox2B.text())
        if not self.textbox2C.text():
            self.uiwaveoffset_patchAO = 0
        else:
            self.uiwaveoffset_patchAO = int(self.textbox2C.text()) # in ms
        self.uiwaveperiod_patchAO = int(self.textbox2D.text())
        self.uiwaveDC_patchAO = int(self.textbox2F.currentText())
        if not self.textbox2E.text():
            self.uiwaverepeat_patchAO = 1
        else:
            self.uiwaverepeat_patchAO = int(self.textbox2E.text())
        if not self.textbox2G.text():
            self.uiwavegap_patchAO = 0
        else:
            self.uiwavegap_patchAO = int(self.textbox2G.text())
        self.uiwavestartamplitude_patchAO = float(self.textbox2H.value())
        if not self.textbox2I.text():
            self.uiwavebaseline_patchAO = 0
        else:
            self.uiwavebaseline_patchAO = float(self.textbox2I.text())
        self.uiwavestep_patchAO = float(self.textbox2J.value())
        self.uiwavecycles_patchAO = int(self.textbox2K.value())   
        
        #if int(self.textbox5A.currentText()) == 1:
            
        s = generate_AO_forpatch(self.uiDaq_sample_rate, self.uiwavefrequency_patchAO, self.uiwaveoffset_patchAO, self.uiwaveperiod_patchAO, self.uiwaveDC_patchAO
                               , self.uiwaverepeat_patchAO, self.uiwavegap_patchAO, self.uiwavestartamplitude_patchAO, self.uiwavebaseline_patchAO, self.uiwavestep_patchAO, self.uiwavecycles_patchAO)
        self.finalwave_patch = s.generate()
        return self.finalwave_patch
            
    def generate_patchAO_graphy(self):
        xlabelhere_patch = np.arange(len(self.finalwave_patch))/self.uiDaq_sample_rate
        self.PlotDataItem_patch = PlotDataItem(xlabelhere_patch, self.finalwave_patch)
        self.PlotDataItem_patch.setPen(100, 100, 0)
        self.pw.addItem(self.PlotDataItem_patch)
        
        self.textitem_patch = pg.TextItem(text='patch ', color=(100, 100, 0), anchor=(1, 1))
        self.textitem_patch.setPos(0, 1)
        self.pw.addItem(self.textitem_patch)
        
    #--------------------------------------------------------------------------------- for generating ramp voltage signals------------------------------------------------------------------------------
    def generate_ramp(self, channel):
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_ramp = float(self.textbox2B_ramp.text())
        if not self.textbox2C_ramp.text():
            self.uiwaveoffset_ramp = 0
        else:
            self.uiwaveoffset_ramp = int(self.textbox2C_ramp.text()) # in ms
        self.uiwaveperiod_ramp = int(self.textbox2D_ramp.text())
        if not self.textbox2F_ramp.text():
            self.uiwavesymmetry_ramp = 0.5
        else:
            self.uiwavesymmetry_ramp = float(self.textbox2F_ramp.text())
        if not self.textbox2E_ramp.text():
            self.uiwaverepeat_ramp = 1
        else:
            self.uiwaverepeat_ramp = int(self.textbox2E_ramp.text())
        if not self.textbox2G_ramp.text():
            self.uiwavegap_ramp = 0
        else:
            self.uiwavegap_ramp = int(self.textbox2G_ramp.text())
        self.uiwavestartamplitude_ramp = float(self.textbox2H_ramp.value())
        if not self.textbox2I_ramp.text():
            self.uiwavebaseline_ramp = 0
        else:
            self.uiwavebaseline_ramp = float(self.textbox2I_ramp.text())
        self.uiwavestep_ramp = float(self.textbox2J_ramp.value())
        self.uiwavecycles_ramp = int(self.textbox2K_ramp.value())   
        
        ramp_instance = generate_ramp(self.uiDaq_sample_rate, self.uiwavefrequency_ramp, self.uiwaveoffset_ramp,
                                      self.uiwaveperiod_ramp, self.uiwavesymmetry_ramp, self.uiwaverepeat_ramp, self.uiwavegap_ramp,
                                      self.uiwavestartamplitude_ramp, self.uiwavebaseline_ramp, self.uiwavestep_ramp, self.uiwavecycles_ramp)
        
        if channel == '640AO':
            self.finalwave_640 = ramp_instance.generate()
        elif channel == '532AO':
            self.finalwave_532 = ramp_instance.generate()
        elif channel == '488AO':
            self.finalwave_488 = ramp_instance.generate()           
        elif channel == 'patchAO':
            self.finalwave_patch = ramp_instance.generate()

    # --------------------------------------------------------------------------------for generating digital signals------------------------------------------------------------------------------------
    def generate_cameratrigger(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_cameratrigger = float(self.textbox11B.text())
        if not self.textbox11C.text():
            self.uiwaveoffset_cameratrigger = 0
        else:
            self.uiwaveoffset_cameratrigger = int(self.textbox11C.text())
        self.uiwaveperiod_cameratrigger = int(self.textbox11D.text())
        self.uiwaveDC_cameratrigger = int(self.textbox11F.currentText())
        if not self.textbox11E.text():
            self.uiwaverepeat_cameratrigger_number = 1
        else:
            self.uiwaverepeat_cameratrigger_number = int(self.textbox11E.text())
        if not self.textbox11G.text():
            self.uiwavegap_cameratrigger = 0
        else:
            self.uiwavegap_cameratrigger = int(self.textbox11G.text())
        
        #if int(self.textbox11A.currentText()) == 1:
            
        cameratrigger = generate_DO_forcameratrigger(self.uiDaq_sample_rate, self.uiwavefrequency_cameratrigger, self.uiwaveoffset_cameratrigger,
                                                     self.uiwaveperiod_cameratrigger, self.uiwaveDC_cameratrigger, self.uiwaverepeat_cameratrigger_number, self.uiwavegap_cameratrigger)
        self.finalwave_cameratrigger = cameratrigger.generate()
        return self.finalwave_cameratrigger
            
    def generate_cameratrigger_graphy(self):

        xlabelhere_cameratrigger = np.arange(len(self.finalwave_cameratrigger))/self.uiDaq_sample_rate
        self.finalwave_cameratrigger_forgraphy = self.finalwave_cameratrigger.astype(int)
        self.PlotDataItem_cameratrigger = PlotDataItem(xlabelhere_cameratrigger, self.finalwave_cameratrigger_forgraphy)
        self.PlotDataItem_cameratrigger.setPen('c')
        self.PlotDataItem_cameratrigger.setDownsampling(auto=True, method='mean')
        #self.pw.addItem(self.PlotDataItem_cameratrigger)
        
        try:
            self.textitem_cameratrigger = pg.TextItem(text='cameratrigger '+str(self.uiwavefrequency_cameratrigger)+'hz', color=('c'), anchor=(1, 1))
        except:
            self.textitem_cameratrigger = pg.TextItem(text='cameratrigger ', color=('c'), anchor=(1, 1))
        self.textitem_cameratrigger.setPos(0, 0)
        self.pw.addItem(self.textitem_cameratrigger)
    
            
    def generate_640blanking(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_640blanking = float(self.textbox11B.text())
        if not self.textbox11C.text():
            self.uiwaveoffset_640blanking = 0
        else:
            self.uiwaveoffset_640blanking = int(self.textbox11C.text())
        self.uiwaveperiod_640blanking = int(self.textbox11D.text())
        self.uiwaveDC_640blanking = int(self.textbox11F.currentText())
        if not self.textbox11E.text():
            self.uiwaverepeat_640blanking_number = 1
        else:
            self.uiwaverepeat_640blanking_number = int(self.textbox11E.text())
        if not self.textbox11G.text():
            self.uiwavegap_640blanking = 0
        else:
            self.uiwavegap_640blanking = int(self.textbox11G.text())
        
        #if int(self.textbox22A.currentText()) == 1:
            
        blanking640 = generate_DO_for640blanking(self.uiDaq_sample_rate, self.uiwavefrequency_640blanking, self.uiwaveoffset_640blanking,
                                                     self.uiwaveperiod_640blanking, self.uiwaveDC_640blanking, self.uiwaverepeat_640blanking_number, self.uiwavegap_640blanking)
        self.finalwave_640blanking = blanking640.generate()
        return self.finalwave_640blanking
            
    def generate_640blanking_graphy(self):    

        xlabelhere_640blanking = np.arange(len(self.finalwave_640blanking))/self.uiDaq_sample_rate
        self.final_640blanking_forgraphy = self.finalwave_640blanking.astype(int)
        self.PlotDataItem_640blanking = PlotDataItem(xlabelhere_640blanking, self.final_640blanking_forgraphy)
        self.PlotDataItem_640blanking.setPen(255,204,255)
        self.pw.addItem(self.PlotDataItem_640blanking)
        
        self.textitem_640blanking = pg.TextItem(text='640blanking', color=(255,204,255), anchor=(1, 1))
        self.textitem_640blanking.setPos(0, -2)
        self.pw.addItem(self.textitem_640blanking)

        
    def generate_532blanking(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_532blanking = float(self.textbox11B.text())
        if not self.textbox11C.text():
            self.uiwaveoffset_532blanking = 0
        else:
            self.uiwaveoffset_532blanking = int(self.textbox11C.text())
        self.uiwaveperiod_532blanking = int(self.textbox11D.text())
        self.uiwaveDC_532blanking = int(self.textbox11F.currentText())
        if not self.textbox11E.text():
            self.uiwaverepeat_532blanking_number = 1
        else:
            self.uiwaverepeat_532blanking_number = int(self.textbox11E.text())
        if not self.textbox11G.text():
            self.uiwavegap_532blanking = 0
        else:
            self.uiwavegap_532blanking = int(self.textbox11G.text())
        
        #if int(self.textbox33A.currentText()) == 1:
            
        blanking532 = generate_DO_for532blanking(self.uiDaq_sample_rate, self.uiwavefrequency_532blanking, self.uiwaveoffset_532blanking,
                                                     self.uiwaveperiod_532blanking, self.uiwaveDC_532blanking, self.uiwaverepeat_532blanking_number, self.uiwavegap_532blanking)
        self.finalwave_532blanking = blanking532.generate()
        return self.finalwave_532blanking
            
    def generate_532blanking_graphy(self):    

        xlabelhere_532blanking = np.arange(len(self.finalwave_532blanking))/self.uiDaq_sample_rate
        self.final_532blanking_forgraphy = self.finalwave_532blanking.astype(int)
        self.PlotDataItem_532blanking = PlotDataItem(xlabelhere_532blanking, self.final_532blanking_forgraphy)
        self.PlotDataItem_532blanking.setPen('y')
        self.pw.addItem(self.PlotDataItem_532blanking)
        
        self.textitem_532blanking = pg.TextItem(text='532blanking', color=('y'), anchor=(1, 1))
        self.textitem_532blanking.setPos(0, -3)
        self.pw.addItem(self.textitem_532blanking)

        
    def generate_488blanking(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_488blanking = float(self.textbox11B.text())
        if not self.textbox11C.text():
            self.uiwaveoffset_488blanking = 0
        else:
            self.uiwaveoffset_488blanking = int(self.textbox11C.text())
        self.uiwaveperiod_488blanking = int(self.textbox11D.text())
        self.uiwaveDC_488blanking = int(self.textbox11F.currentText())
        if not self.textbox11E.text():
            self.uiwaverepeat_488blanking_number = 1
        else:
            self.uiwaverepeat_488blanking_number = int(self.textbox11E.text())
        if not self.textbox11G.text():
            self.uiwavegap_488blanking = 0
        else:
            self.uiwavegap_488blanking = int(self.textbox11G.text())
        
        #if int(self.textbox44A.currentText()) == 1:
            
        blanking488 = generate_DO_for488blanking(self.uiDaq_sample_rate, self.uiwavefrequency_488blanking, self.uiwaveoffset_488blanking,
                                                     self.uiwaveperiod_488blanking, self.uiwaveDC_488blanking, self.uiwaverepeat_488blanking_number, self.uiwavegap_488blanking)
        self.finalwave_488blanking = blanking488.generate()
        return self.finalwave_488blanking
            
    def generate_488blanking_graphy(self):    

        xlabelhere_488blanking = np.arange(len(self.finalwave_488blanking))/self.uiDaq_sample_rate
        self.final_488blanking_forgraphy = self.finalwave_488blanking.astype(int)
        self.PlotDataItem_488blanking = PlotDataItem(xlabelhere_488blanking, self.final_488blanking_forgraphy)
        self.PlotDataItem_488blanking.setPen(255,51,153)
        self.pw.addItem(self.PlotDataItem_488blanking)
        
        self.textitem_488blanking = pg.TextItem(text='488blanking', color=(255,51,153), anchor=(1, 1))
        self.textitem_488blanking.setPos(0, -4)
        self.pw.addItem(self.textitem_488blanking)

        
    def generate_blankingall(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_blankingall = float(self.textbox11B.text())
        if not self.textbox11C.text():
            self.uiwaveoffset_blankingall = 0
        else:
            self.uiwaveoffset_blankingall = int(self.textbox11C.text())
        self.uiwaveperiod_blankingall = int(self.textbox11D.text())
        self.uiwaveDC_blankingall = int(self.textbox11F.currentText())
        if not self.textbox11E.text():
            self.uiwaverepeat_blankingall_number = 1
        else:
            self.uiwaverepeat_blankingall_number = int(self.textbox11E.text())
        if not self.textbox11G.text():
            self.uiwavegap_blankingall = 0
        else:
            self.uiwavegap_blankingall = int(self.textbox11G.text())
        
        #if int(self.textbox55A.currentText()) == 1:
            
        blankingall = generate_DO_forblankingall(self.uiDaq_sample_rate, self.uiwavefrequency_blankingall, self.uiwaveoffset_blankingall,
                                                     self.uiwaveperiod_blankingall, self.uiwaveDC_blankingall, self.uiwaverepeat_blankingall_number, self.uiwavegap_blankingall)
        self.finalwave_blankingall = blankingall.generate()
        return self.finalwave_blankingall
            
    def generate_blankingall_graphy(self):    

        xlabelhere_blankingall = np.arange(len(self.finalwave_blankingall))/self.uiDaq_sample_rate
        self.final_blankingall_forgraphy = self.finalwave_blankingall.astype(int)
        self.PlotDataItem_blankingall = PlotDataItem(xlabelhere_blankingall, self.final_blankingall_forgraphy)
        self.PlotDataItem_blankingall.setPen(255,229,204)
        self.pw.addItem(self.PlotDataItem_blankingall)
        
        self.textitem_blankingall = pg.TextItem(text='blankingall', color=(255,229,204), anchor=(1, 1))
        self.textitem_blankingall.setPos(0, -1)
        self.pw.addItem(self.textitem_blankingall)
        
    def generate_Perfusion_8(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_Perfusion_8 = float(self.textbox11B.text())
        if not self.textbox11C.text():
            self.uiwaveoffset_Perfusion_8 = 0
        else:
            self.uiwaveoffset_Perfusion_8 = int(self.textbox11C.text())
        self.uiwaveperiod_Perfusion_8 = int(self.textbox11D.text())
        self.uiwaveDC_Perfusion_8 = int(self.textbox11F.currentText())
        if not self.textbox11E.text():
            self.uiwaverepeat_Perfusion_8_number = 1
        else:
            self.uiwaverepeat_Perfusion_8_number = int(self.textbox11E.text())
        if not self.textbox11G.text():
            self.uiwavegap_Perfusion_8 = 0
        else:
            self.uiwavegap_Perfusion_8 = int(self.textbox11G.toPlainText())
        
        #if int(self.textbox66A.currentText()) == 1:
            
        Perfusion_8 = generate_DO_forPerfusion(self.uiDaq_sample_rate, self.uiwavefrequency_Perfusion_8, self.uiwaveoffset_Perfusion_8,
                                                     self.uiwaveperiod_Perfusion_8, self.uiwaveDC_Perfusion_8, self.uiwaverepeat_Perfusion_8_number, self.uiwavegap_Perfusion_8)
        self.finalwave_Perfusion_8 = Perfusion_8.generate()
        return self.finalwave_Perfusion_8
            
    def generate_Perfusion_8_graphy(self):    

        xlabelhere_Perfusion_8 = np.arange(len(self.finalwave_Perfusion_8))/self.uiDaq_sample_rate
        self.final_Perfusion_8_forgraphy = self.finalwave_Perfusion_8.astype(int)
        self.PlotDataItem_Perfusion_8 = PlotDataItem(xlabelhere_Perfusion_8, self.final_Perfusion_8_forgraphy)
        self.PlotDataItem_Perfusion_8.setPen(154,205,50)
        self.pw.addItem(self.PlotDataItem_Perfusion_8)
        
        self.textitem_Perfusion_8 = pg.TextItem(text='Perfusion_8', color=(154,205,50), anchor=(1, 1))
        self.textitem_Perfusion_8.setPos(0, -6)
        self.pw.addItem(self.textitem_Perfusion_8)
        
    def generate_Perfusion_7(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_Perfusion_7 = float(self.textbox11B.text())
        if not self.textbox11C.text():
            self.uiwaveoffset_Perfusion_7 = 0
        else:
            self.uiwaveoffset_Perfusion_7 = int(self.textbox11C.text())
        self.uiwaveperiod_Perfusion_7 = int(self.textbox11D.text())
        self.uiwaveDC_Perfusion_7 = int(self.textbox11F.currentText())
        if not self.textbox11E.text():
            self.uiwaverepeat_Perfusion_7_number = 1
        else:
            self.uiwaverepeat_Perfusion_7_number = int(self.textbox11E.text())
        if not self.textbox11G.text():
            self.uiwavegap_Perfusion_7 = 0
        else:
            self.uiwavegap_Perfusion_7 = int(self.textbox11G.toPlainText())
        
        #if int(self.textbox66A.currentText()) == 1:
            
        Perfusion_7 = generate_DO_forPerfusion(self.uiDaq_sample_rate, self.uiwavefrequency_Perfusion_7, self.uiwaveoffset_Perfusion_7,
                                                     self.uiwaveperiod_Perfusion_7, self.uiwaveDC_Perfusion_7, self.uiwaverepeat_Perfusion_7_number, self.uiwavegap_Perfusion_7)
        self.finalwave_Perfusion_7 = Perfusion_7.generate()
        return self.finalwave_Perfusion_7
            
    def generate_Perfusion_7_graphy(self):    

        xlabelhere_Perfusion_7 = np.arange(len(self.finalwave_Perfusion_7))/self.uiDaq_sample_rate
        self.final_Perfusion_7_forgraphy = self.finalwave_Perfusion_7.astype(int)
        self.PlotDataItem_Perfusion_7 = PlotDataItem(xlabelhere_Perfusion_7, self.final_Perfusion_7_forgraphy)
        self.PlotDataItem_Perfusion_7.setPen(127,255,212)
        self.pw.addItem(self.PlotDataItem_Perfusion_7)
        
        self.textitem_Perfusion_7 = pg.TextItem(text='Perfusion_7', color=(127,255,212), anchor=(1, 1))
        self.textitem_Perfusion_7.setPos(-0.3, -6)
        self.pw.addItem(self.textitem_Perfusion_7)
        
    def generate_Perfusion_6(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_Perfusion_6 = float(self.textbox11B.text())
        if not self.textbox11C.text():
            self.uiwaveoffset_Perfusion_6 = 0
        else:
            self.uiwaveoffset_Perfusion_6 = int(self.textbox11C.text())
        self.uiwaveperiod_Perfusion_6 = int(self.textbox11D.text())
        self.uiwaveDC_Perfusion_6 = int(self.textbox11F.currentText())
        if not self.textbox11E.text():
            self.uiwaverepeat_Perfusion_6_number = 1
        else:
            self.uiwaverepeat_Perfusion_6_number = int(self.textbox11E.text())
        if not self.textbox11G.text():
            self.uiwavegap_Perfusion_6 = 0
        else:
            self.uiwavegap_Perfusion_6 = int(self.textbox11G.toPlainText())
        
        #if int(self.textbox66A.currentText()) == 1:
            
        Perfusion_6 = generate_DO_forPerfusion(self.uiDaq_sample_rate, self.uiwavefrequency_Perfusion_6, self.uiwaveoffset_Perfusion_6,
                                                     self.uiwaveperiod_Perfusion_6, self.uiwaveDC_Perfusion_6, self.uiwaverepeat_Perfusion_6_number, self.uiwavegap_Perfusion_6)
        self.finalwave_Perfusion_6 = Perfusion_6.generate()
        return self.finalwave_Perfusion_6
            
    def generate_Perfusion_6_graphy(self):    

        xlabelhere_Perfusion_6 = np.arange(len(self.finalwave_Perfusion_6))/self.uiDaq_sample_rate
        self.final_Perfusion_6_forgraphy = self.finalwave_Perfusion_6.astype(int)
        self.PlotDataItem_Perfusion_6 = PlotDataItem(xlabelhere_Perfusion_6, self.final_Perfusion_6_forgraphy)
        self.PlotDataItem_Perfusion_6.setPen(102,40,91)
        self.pw.addItem(self.PlotDataItem_Perfusion_6)
        
        self.textitem_Perfusion_6 = pg.TextItem(text='Perfusion_6', color=(102,40,91), anchor=(1, 1))
        self.textitem_Perfusion_6.setPos(-0.6, -6)
        self.pw.addItem(self.textitem_Perfusion_6)
        
    def generate_Perfusion_2(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_Perfusion_2 = float(self.textbox11B.text())
        if not self.textbox11C.text():
            self.uiwaveoffset_Perfusion_2 = 0
        else:
            self.uiwaveoffset_Perfusion_2 = int(self.textbox11C.text())
        self.uiwaveperiod_Perfusion_2 = int(self.textbox11D.text())
        self.uiwaveDC_Perfusion_2 = int(self.textbox11F.currentText())
        if not self.textbox11E.text():
            self.uiwaverepeat_Perfusion_2_number = 1
        else:
            self.uiwaverepeat_Perfusion_2_number = int(self.textbox11E.text())
        if not self.textbox11G.text():
            self.uiwavegap_Perfusion_2 = 0
        else:
            self.uiwavegap_Perfusion_2 = int(self.textbox11G.toPlainText())
        
        #if int(self.textbox66A.currentText()) == 1:
            
        Perfusion_2 = generate_DO_forPerfusion(self.uiDaq_sample_rate, self.uiwavefrequency_Perfusion_2, self.uiwaveoffset_Perfusion_2,
                                                     self.uiwaveperiod_Perfusion_2, self.uiwaveDC_Perfusion_2, self.uiwaverepeat_Perfusion_2_number, self.uiwavegap_Perfusion_2)
        self.finalwave_Perfusion_2 = Perfusion_2.generate()
        return self.finalwave_Perfusion_2
            
    def generate_Perfusion_2_graphy(self):    

        xlabelhere_Perfusion_2 = np.arange(len(self.finalwave_Perfusion_2))/self.uiDaq_sample_rate
        self.final_Perfusion_2_forgraphy = self.finalwave_Perfusion_2.astype(int)
        self.PlotDataItem_Perfusion_2 = PlotDataItem(xlabelhere_Perfusion_2, self.final_Perfusion_2_forgraphy)
        self.PlotDataItem_Perfusion_2.setPen(255,215,0)
        self.pw.addItem(self.PlotDataItem_Perfusion_2)
        
        self.textitem_Perfusion_2 = pg.TextItem(text='Perfusion_2', color=(255,215,0), anchor=(1, 1))
        self.textitem_Perfusion_2.setPos(-0.9, -6)
        self.pw.addItem(self.textitem_Perfusion_2)
        
    def generate_2Pshutter(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_2Pshutter = float(self.textbox11B.text())
        if not self.textbox11C.text():
            self.uiwaveoffset_2Pshutter = 0
        else:
            self.uiwaveoffset_2Pshutter = int(self.textbox11C.text())
        self.uiwaveperiod_2Pshutter = int(self.textbox11D.text())
        self.uiwaveDC_2Pshutter = int(self.textbox11F.currentText())
        if not self.textbox11E.text():
            self.uiwaverepeat_2Pshutter_number = 1
        else:
            self.uiwaverepeat_2Pshutter_number = int(self.textbox11E.text())
        if not self.textbox11G.text():
            self.uiwavegap_2Pshutter = 0
        else:
            self.uiwavegap_2Pshutter = int(self.textbox11G.toPlainText())
        
        #if int(self.textbox66A.currentText()) == 1:
            
        twoPshutter = generate_DO_for2Pshutter(self.uiDaq_sample_rate, self.uiwavefrequency_2Pshutter, self.uiwaveoffset_2Pshutter,
                                                     self.uiwaveperiod_2Pshutter, self.uiwaveDC_2Pshutter, self.uiwaverepeat_2Pshutter_number, self.uiwavegap_2Pshutter)
        self.finalwave_2Pshutter = twoPshutter.generate()
        return self.finalwave_2Pshutter
            
    def generate_2Pshutter_graphy(self):    

        xlabelhere_2Pshutter = np.arange(len(self.finalwave_2Pshutter))/self.uiDaq_sample_rate
        self.final_2Pshutter_forgraphy = self.finalwave_2Pshutter.astype(int)
        self.PlotDataItem_2Pshutter = PlotDataItem(xlabelhere_2Pshutter, self.final_2Pshutter_forgraphy)
        self.PlotDataItem_2Pshutter.setPen(229,204,255)
        self.pw.addItem(self.PlotDataItem_2Pshutter)
        
        self.textitem_2Pshutter = pg.TextItem(text='2Pshutter', color=(229,204,255), anchor=(1, 1))
        self.textitem_2Pshutter.setPos(0, -7)
        self.pw.addItem(self.textitem_2Pshutter)
        
    def generate_photocycle_640(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_photocycle_640 = float(self.textbox_photocycleA.text())
        if not self.textbox_photocycleB.text():
            self.uiwavefrequency_offset_photocycle_640 = 100
        else:
            self.uiwavefrequency_offset_photocycle_640 = int(self.textbox_photocycleB.text())
        self.uiwaveperiod_photocycle_640 = int(self.textbox_photocycleC.text())
        self.uiwaveDC_photocycle_640 = int(self.textbox_photocycleE.currentText())
        if not self.textbox_photocycleD.text():
            self.uiwaverepeat_photocycle_640 = 10
        else:
            self.uiwaverepeat_photocycle_640 = int(self.textbox_photocycleD.text())
        if not self.textbox_photocycleF.text():
            self.uiwavegap_photocycle_640 = 100000
        else:
            self.uiwavegap_photocycle_640 = int(self.textbox_photocycleF.text())
        self.uiwavestartamplitude_photocycle_640 = float(self.textbox_photocycleG.value())
        if not self.textbox_photocycleH.text():
            self.uiwavebaseline_photocycle_640 = 0
        else:
            self.uiwavebaseline_photocycle_640 = float(self.textbox_photocycleH.text())
        self.uiwavestep_photocycle_640 = float(self.textbox_photocycleI.value())
        self.uiwavecycles_photocycle_640 = float(self.textbox_photocycleJ.value())
        self.uiwavestart_time_photocycle_640 = float(self.textbox_photocycleL.value())  
        
        self.uiwavecontrol_amplitude_photocycle_640 = float(self.textbox_photocycleM.value())         
                    
        s = generate_AO(self.uiDaq_sample_rate, self.uiwavefrequency_photocycle_640, self.uiwavefrequency_offset_photocycle_640,
                        self.uiwaveperiod_photocycle_640, self.uiwaveDC_photocycle_640, self.uiwaverepeat_photocycle_640, self.uiwavegap_photocycle_640, 
                        self.uiwavestartamplitude_photocycle_640, self.uiwavebaseline_photocycle_640, self.uiwavestep_photocycle_640, self.uiwavecycles_photocycle_640, 
                        self.uiwavestart_time_photocycle_640,self.uiwavecontrol_amplitude_photocycle_640)
        self.finalwave_640 = s.generate()
        return self.finalwave_640
    
    def generate_photocycle_532(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_photocycle_532 = float(self.textbox_photocycleA.text())
        if not self.textbox_photocycleB.text():
            self.uiwavefrequency_offset_photocycle_532 = 100
        else:
            self.uiwavefrequency_offset_photocycle_532 = int(self.textbox_photocycleB.text())
        self.uiwaveperiod_photocycle_532 = int(self.textbox_photocycleC.text())
        self.uiwaveDC_photocycle_532 = int(self.textbox_photocycleE.currentText())
        if not self.textbox_photocycleD.text():
            self.uiwaverepeat_photocycle_532 = 10
        else:
            self.uiwaverepeat_photocycle_532 = int(self.textbox_photocycleD.text())
        if not self.textbox_photocycleF.text():
            self.uiwavegap_photocycle_532 = 100000
        else:
            self.uiwavegap_photocycle_532 = int(self.textbox_photocycleF.text())
        self.uiwavestartamplitude_photocycle_532 = float(self.textbox_photocycleG.value())
        if not self.textbox_photocycleH.text():
            self.uiwavebaseline_photocycle_532 = 0
        else:
            self.uiwavebaseline_photocycle_532 = float(self.textbox_photocycleH.text())
        self.uiwavestep_photocycle_532 = float(self.textbox_photocycleI.value())
        self.uiwavecycles_photocycle_532 = float(self.textbox_photocycleJ.value())
        self.uiwavestart_time_photocycle_532 = float(self.textbox_photocycleL.value())  
        
        self.uiwavecontrol_amplitude_photocycle_532 = float(self.textbox_photocycleM.value())         
                    
        s = generate_AO(self.uiDaq_sample_rate, self.uiwavefrequency_photocycle_532, self.uiwavefrequency_offset_photocycle_532,
                        self.uiwaveperiod_photocycle_532, self.uiwaveDC_photocycle_532, self.uiwaverepeat_photocycle_532, self.uiwavegap_photocycle_532, 
                        self.uiwavestartamplitude_photocycle_532, self.uiwavebaseline_photocycle_532, self.uiwavestep_photocycle_532, self.uiwavecycles_photocycle_532, 
                        self.uiwavestart_time_photocycle_532,self.uiwavecontrol_amplitude_photocycle_532)
        self.finalwave_532 = s.generate()
        return self.finalwave_532
    
    def generate_photocycle_488(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.value())
        self.uiwavefrequency_photocycle_488 = float(self.textbox_photocycleA.text())
        if not self.textbox_photocycleB.text():
            self.uiwavefrequency_offset_photocycle_488 = 100
        else:
            self.uiwavefrequency_offset_photocycle_488 = int(self.textbox_photocycleB.text())
        self.uiwaveperiod_photocycle_488 = int(self.textbox_photocycleC.text())
        self.uiwaveDC_photocycle_488 = int(self.textbox_photocycleE.currentText())
        if not self.textbox_photocycleD.text():
            self.uiwaverepeat_photocycle_488 = 10
        else:
            self.uiwaverepeat_photocycle_488 = int(self.textbox_photocycleD.text())
        if not self.textbox_photocycleF.text():
            self.uiwavegap_photocycle_488 = 100000
        else:
            self.uiwavegap_photocycle_488 = int(self.textbox_photocycleF.text())
        self.uiwavestartamplitude_photocycle_488 = float(self.textbox_photocycleG.value())
        if not self.textbox_photocycleH.text():
            self.uiwavebaseline_photocycle_488 = 0
        else:
            self.uiwavebaseline_photocycle_488 = float(self.textbox_photocycleH.text())
        self.uiwavestep_photocycle_488 = float(self.textbox_photocycleI.value())
        self.uiwavecycles_photocycle_488 = float(self.textbox_photocycleJ.value())
        self.uiwavestart_time_photocycle_488 = float(self.textbox_photocycleL.value())  
        
        self.uiwavecontrol_amplitude_photocycle_488 = float(self.textbox_photocycleM.value())         
                    
        s = generate_AO(self.uiDaq_sample_rate, self.uiwavefrequency_photocycle_488, self.uiwavefrequency_offset_photocycle_488, self.uiwaveperiod_photocycle_488, 
                        self.uiwaveDC_photocycle_488, self.uiwaverepeat_photocycle_488,self.uiwavegap_photocycle_488, self.uiwavestartamplitude_photocycle_488, 
                        self.uiwavebaseline_photocycle_488, self.uiwavestep_photocycle_488, self.uiwavecycles_photocycle_488, self.uiwavestart_time_photocycle_488,
                        self.uiwavecontrol_amplitude_photocycle_488)
        self.finalwave_488 = s.generate()
        return self.finalwave_488
       
    def set_switch(self, name):
        #self.generate_dictionary_switch_instance[name] = 1
        if name not in self.dictionary_switch_list:
            self.dictionary_switch_list.append(name)
            print(self.dictionary_switch_list)
            self.normalOutputWritten(str(self.dictionary_switch_list)+'\n')
    def del_set_switch(self, name):
        #self.generate_dictionary_switch_instance[name] = 1
        if name in self.dictionary_switch_list:
            self.dictionary_switch_list.remove(name)
            print(self.dictionary_switch_list)
            self.normalOutputWritten(str(self.dictionary_switch_list)+'\n')
    def clear_canvas(self):
        #Back to initial state
        self.pw.clear()
        self.dictionary_switch_list =[]
        #self.Galvo_samples = self.finalwave_640 = self.finalwave_488 = self.finalwave_532=self.finalwave_patch =None
#        self.finalwave_cameratrigger=self.final_galvotrigger=self.finalwave_blankingall=self.finalwave_640blanking=self.finalwave_532blanking=self.finalwave_488blanking=self.finalwave_Perfusion_8 = None
#        self.switch_galvos=self.switch_640AO=self.switch_488AO=self.switch_532AO=self.switch_patchAO=self.switch_cameratrigger=self.switch_galvotrigger=self.switch_blankingall=self.switch_640blanking=self.switch_532blanking=self.switch_488blanking=self.switch_Perfusion_8=0        
    
    '''
    '''
    -----------------------------------------------------------------------Integrating all the waveforms, getting them ready for Daq--------------------------------------------------------------------------------------------------------------------------------------------------------------------
    '''
    '''
    def show_all(self):

        self.switch_galvos=self.switch_galvos_contour=self.switch_640AO=self.switch_488AO=self.switch_532AO=self.switch_patchAO=\
        self.switch_cameratrigger=self.switch_galvotrigger=self.switch_blankingall=self.switch_640blanking=self.switch_532blanking\
        =self.switch_488blanking=self.switch_Perfusion_8=self.switch_Perfusion_7=self.switch_Perfusion_6=self.switch_Perfusion_2\
        =self.switch_2Pshutter=0
        
        color_dictionary = {'galvos':[255,255,255],
                            'galvos_contour':[255,255,255],
                            '640AO':[255,0,0],
                            '488AO':[0,0,255],
                            '532AO':[0,255,0],
                            'patchAO':[100, 100, 0],
                            'cameratrigger':[0,255,255],
                            'galvotrigger':[100,100,200], 
                            'blankingall':[255,229,204],
                            '640blanking':[255,204,255],
                            '532blanking':[255,255,0],
                            '488blanking':[255,51,153],
                            'Perfusion_8':[154,205,50],
                            'Perfusion_7':[127,255,212],
                            'Perfusion_6':[102,40,91],
                            'Perfusion_2':[255,215,0],
                            '2Pshutter':[229,204,255]
                            }
        # Use dictionary to execute functions: https://stackoverflow.com/questions/9168340/using-a-dictionary-to-select-function-to-execute/9168387#9168387
        dictionary_analog = {'galvos':[self.switch_galvos,self.Galvo_samples],
                             'galvos_contour':[self.switch_galvos_contour,self.handle_viewbox_coordinate_position_array_expanded_forDaq_waveform],
                             '640AO':[self.switch_640AO,self.finalwave_640],
                             '488AO':[self.switch_488AO,self.finalwave_488],
                             '532AO':[self.switch_532AO,self.finalwave_532],
                             'patchAO':[self.switch_patchAO,self.finalwave_patch]
                             }
                              
                              
        dictionary_digital = {'cameratrigger':[self.switch_cameratrigger,self.finalwave_cameratrigger],
                              'galvotrigger':[self.switch_galvotrigger,self.final_galvotrigger], 
                              'blankingall':[self.switch_blankingall, self.finalwave_blankingall],
                              '640blanking':[self.switch_640blanking, self.finalwave_640blanking],
                              '532blanking':[self.switch_532blanking, self.finalwave_532blanking],
                              '488blanking':[self.switch_488blanking, self.finalwave_488blanking],
                              'Perfusion_8':[self.switch_Perfusion_8, self.finalwave_Perfusion_8],
                              'Perfusion_7':[self.switch_Perfusion_7, self.finalwave_Perfusion_7],
                              'Perfusion_6':[self.switch_Perfusion_6, self.finalwave_Perfusion_6],
                              'Perfusion_2':[self.switch_Perfusion_2, self.finalwave_Perfusion_2],
                              '2Pshutter':[self.switch_2Pshutter, self.finalwave_2Pshutter]
                              }
        # set switch of selected waves to 1
        for i in range(len(self.dictionary_switch_list)):
            if self.dictionary_switch_list[i] in dictionary_analog:
                dictionary_analog[self.dictionary_switch_list[i]][0] = 1
                #print('switch = '+str(dictionary_analog[self.dictionary_switch_list[i]][0]))
            elif self.dictionary_switch_list[i] in dictionary_digital:
                dictionary_digital[self.dictionary_switch_list[i]][0] = 1
        # Calculate the length of reference wave
        # tags in the dictionary above should be the same as that in reference combox, then the dictionary below can work
       
        if self.textboxBB.currentText() in dictionary_analog.keys():
            reference_wave = dictionary_analog[self.textboxBB.currentText()][1]
        else:
            reference_wave = dictionary_digital[self.textboxBB.currentText()][1]
        
        if self.textboxBB.currentText() == 'galvos' or self.textboxBB.currentText() == 'galvos_contour': # in case of using galvos as reference wave
            self.reference_length = len(reference_wave[0, :])
        else:
            self.reference_length = len(reference_wave)
        print('reference_length: '+str(self.reference_length))
        self.normalOutputWritten('reference_length: '+str(self.reference_length)+'\n')

        # Structured array to contain 
        # https://stackoverflow.com/questions/39622533/numpy-array-as-datatype-in-a-structured-array
        tp_analog = np.dtype([('Waveform', float, (self.reference_length,)), ('Sepcification', 'U20')])
        tp_digital = np.dtype([('Waveform', bool, (self.reference_length,)), ('Sepcification', 'U20')])
        
        self.analog_data_container = {}

        for key in dictionary_analog:
            if dictionary_analog[key][0] == 1: # if the signal line is added
                self.analog_data_container[key] = dictionary_analog[key][1]
        
        # set galvos sampele stack apart
        if 'galvos' in self.analog_data_container:
            self.analog_data_container['galvosx'+'avgnum_'+str(int(self.textbox1H.value()))] = self.generate_galvos()[0, :]
            self.analog_data_container['galvosy'+'ypixels_'+str(int(self.textbox1G.currentText()))] = self.generate_galvos()[1, :]
            del self.analog_data_container['galvos']
            
        if 'galvos_contour' in self.analog_data_container:
            self.analog_data_container['galvos_X'+'_contour'] = self.generate_contour_for_waveform()[0, :]
            self.analog_data_container['galvos_Y'+'_contour'] = self.generate_contour_for_waveform()[1, :]
            del self.analog_data_container['galvos_contour']      
        
        # reform all waves according to the length of reference wave
        for key in self.analog_data_container:
            if len(self.analog_data_container[key]) >= self.reference_length:
                self.analog_data_container[key] = self.analog_data_container[key][0:self.reference_length]
            else:
                append_waveforms = np.zeros(self.reference_length-len(self.analog_data_container[key]))
                self.analog_data_container[key] = np.append(self.analog_data_container[key], append_waveforms)
            #print(len(self.analog_data_container[key]))
        self.analogcontainer_array = np.zeros(len(self.analog_data_container), dtype =tp_analog)
        analogloopnum = 0
        for key in self.analog_data_container:
            self.analogcontainer_array[analogloopnum] = np.array([(self.analog_data_container[key], key)], dtype =tp_analog)
            analogloopnum = analogloopnum+ 1
            
        #num_rows, num_cols = self.analogcontainer_array['Waveform'].shape
        print(self.analogcontainer_array['Sepcification'])
        self.normalOutputWritten(str(self.analogcontainer_array['Sepcification'])+'\n')
        # digital lines
        self.digital_data_container = {}
        
        for key in dictionary_digital:
            if dictionary_digital[key][0] == 1: # if the signal line is added
                self.digital_data_container[key] = dictionary_digital[key][1]
        
        # reform all waves according to the length of reference wave
        for key in self.digital_data_container:
            if len(self.digital_data_container[key]) >= self.reference_length:
                self.digital_data_container[key] = self.digital_data_container[key][0:self.reference_length]
            elif key == 'blankingall':
                append_waveforms = np.ones(self.reference_length-len(self.digital_data_container[key]))
                self.digital_data_container[key] = np.append(self.digital_data_container[key], append_waveforms)                
            else:
                append_waveforms = np.zeros(self.reference_length-len(self.digital_data_container[key]))
                self.digital_data_container[key] = np.append(self.digital_data_container[key], append_waveforms)
            #print(len(self.digital_data_container[key]))
        self.digitalcontainer_array = np.zeros(len(self.digital_data_container), dtype =tp_digital)
        digitalloopnum = 0
        for key in self.digital_data_container:
            self.digitalcontainer_array[digitalloopnum] = np.array([(self.digital_data_container[key], key)], dtype =tp_digital)
            digitalloopnum = digitalloopnum+ 1
        print(str(self.digitalcontainer_array['Sepcification']))
                
        self.xlabelhere_all = np.arange(self.reference_length)/int(self.textboxAA.value())
        
        self.pw.clear()
        for i in range(analogloopnum):
                                        
            if self.analogcontainer_array['Sepcification'][i] != 'galvosx'+'avgnum_'+str(int(self.textbox1H.value())) and self.analogcontainer_array['Sepcification'][i] != 'galvos_X'+'_contour': #skip the galvoX, as it is too intense
                if self.analogcontainer_array['Sepcification'][i] == 'galvosy'+'ypixels_'+str(int(self.textbox1G.currentText())) or self.analogcontainer_array['Sepcification'][i] == 'galvos_Y'+'_contour':
                    self.PlotDataItem_final = PlotDataItem(self.xlabelhere_all, self.analogcontainer_array['Waveform'][i])
                    #use the same color as before, taking advantages of employing same keys in dictionary
                    self.PlotDataItem_final.setPen('w')
                    self.pw.addItem(self.PlotDataItem_final)
                
                    self.textitem_final = pg.TextItem(text=str(self.analogcontainer_array['Sepcification'][i]), color=('w'), anchor=(1, 1))
                    self.textitem_final.setPos(0, i+1)
                    self.pw.addItem(self.textitem_final)
                else:
                    self.PlotDataItem_final = PlotDataItem(self.xlabelhere_all, self.analogcontainer_array['Waveform'][i])
                    #use the same color as before, taking advantages of employing same keys in dictionary
                    self.PlotDataItem_final.setPen(color_dictionary[self.analogcontainer_array['Sepcification'][i]][0],color_dictionary[self.analogcontainer_array['Sepcification'][i]][1],color_dictionary[self.analogcontainer_array['Sepcification'][i]][2])
                    self.pw.addItem(self.PlotDataItem_final)
                    
                    self.textitem_final = pg.TextItem(text=str(self.analogcontainer_array['Sepcification'][i]), color=(color_dictionary[self.analogcontainer_array['Sepcification'][i]][0],color_dictionary[self.analogcontainer_array['Sepcification'][i]][1],color_dictionary[self.analogcontainer_array['Sepcification'][i]][2]), anchor=(1, 1))
                    self.textitem_final.setPos(0, i+1)
                    self.pw.addItem(self.textitem_final)
                i += 1
        for i in range(digitalloopnum):
            digitalwaveforgraphy = self.digitalcontainer_array['Waveform'][i].astype(int)
            self.PlotDataItem_final = PlotDataItem(self.xlabelhere_all, digitalwaveforgraphy)
            self.PlotDataItem_final.setPen(color_dictionary[self.digitalcontainer_array['Sepcification'][i]][0],color_dictionary[self.digitalcontainer_array['Sepcification'][i]][1],color_dictionary[self.digitalcontainer_array['Sepcification'][i]][2])
            self.pw.addItem(self.PlotDataItem_final)
            
            self.textitem_final = pg.TextItem(text=str(self.digitalcontainer_array['Sepcification'][i]), color=(color_dictionary[self.digitalcontainer_array['Sepcification'][i]][0],color_dictionary[self.digitalcontainer_array['Sepcification'][i]][1],color_dictionary[self.digitalcontainer_array['Sepcification'][i]][2]), anchor=(1, 1))
            self.textitem_final.setPos(0, -1*i)
            self.pw.addItem(self.textitem_final)
            i += 1
        '''
    '''
        plt.figure()
        for i in range(analogloopnum):
            if self.analogcontainer_array['Sepcification'][i] != 'galvosx'+'avgnum_'+str(int(self.textbox1H.value())): #skip the galvoX, as it is too intense
                plt.plot(xlabelhere_all, self.analogcontainer_array['Waveform'][i])
        for i in range(digitalloopnum):
            plt.plot(xlabelhere_all, self.digitalcontainer_array['Waveform'][i])
        plt.text(0.1, 1.1, 'Time lasted:'+str(xlabelhere_all[-1])+'s', fontsize=12)
        plt.show()
    '''
    '''
        # Saving configed waveforms
        if self.textboxsavingwaveforms.isChecked():
            #temp_save_wave = np.empty((len(self.analogcontainer_array['Sepcification'])+len(self.digitalcontainer_array['Sepcification']), 1), dtype=np.object)
            ciao=[]

            for i in range(len(self.analogcontainer_array['Sepcification'])):

                ciao.append(self.analogcontainer_array[i])
                #temp_save_wave[i]=self.analogcontainer_array[i]
            
            for i in range(len(self.digitalcontainer_array['Sepcification'])):
                #temp_save_wave[i+len(self.analogcontainer_array['Sepcification'])]=self.digitalcontainer_array[i]
                ciao.append(self.digitalcontainer_array[i])

            #print(temp_save_wave)
            
            #np.append(temp_save_wave, self.analogcontainer_array, axis = 0)
            #np.append(temp_save_wave, self.digitalcontainer_array, axis = 0)
            #print(temp_save_wave)
            np.save(os.path.join(self.savedirectory, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_'+str(self.prefixtextbox.text())+'_'+'Wavefroms_sr_'+ str(int(self.textboxAA.value()))), ciao)
        
    '''
    '''
        # Saving configed waveforms, worked in my laptop numpy v1.15.4, spyder 3.3.2
        if self.textboxsavingwaveforms.isChecked():
            temp_save_wave = np.empty((len(self.analogcontainer_array['Sepcification'])+len(self.digitalcontainer_array['Sepcification']), 1), dtype=np.object)
            for i in range(len(self.analogcontainer_array['Sepcification'])):
                temp_save_wave[i]=self.analogcontainer_array[i]
            for i in range(len(self.digitalcontainer_array['Sepcification'])):
                temp_save_wave[i+len(self.analogcontainer_array['Sepcification'])]=self.digitalcontainer_array[i]
            #np.append(temp_save_wave, self.analogcontainer_array, axis = 0)
            #np.append(temp_save_wave, self.digitalcontainer_array, axis = 0)
            np.save(os.path.join(self.savedirectory, 'Wavefroms_sr_'+ str(int(self.textboxAA.value())) + '_' + str(self.prefixtextbox.text()) + '_' +datetime.now().strftime('%Y-%m-%d_%H-%M-%S')), temp_save_wave)
    '''
    '''
        
        self.readinchan = []
        
        if self.textbox111A.isChecked():
            self.readinchan.append('PMT')
        if self.textbox222A.isChecked():
            self.readinchan.append('Vp')
        if self.textbox333A.isChecked():
            self.readinchan.append('Ip')       
        
        print(str(self.readinchan))
        self.normalOutputWritten(str(self.readinchan)+'\n')
        self.waveforms_generated.emit(self.analogcontainer_array, self.digitalcontainer_array, self.readinchan, int(self.textboxAA.value()))

        return self.analogcontainer_array, self.digitalcontainer_array, self.readinchan
    
    def execute_tread(self):
        if self.clock_source.currentText() == 'Dev1 as clock source':
            self.adcollector = execute_analog_readin_optional_digital_thread()
            self.adcollector.set_waves(int(self.textboxAA.value()), self.analogcontainer_array, self.digitalcontainer_array, self.readinchan)
            self.adcollector.collected_data.connect(self.recive_data)
            self.adcollector.start()
#            self.adcollector.save_as_binary(self.savedirectory)
            #self.ai_dev_scaling_coeff = self.adcollector.get_ai_dev_scaling_coeff()
        elif self.clock_source.currentText() == 'Cam as clock source' :
            self.adcollector = execute_analog_and_readin_digital_optional_camtrig_thread()
            self.adcollector.set_waves(int(self.textboxAA.value()), self.analogcontainer_array, self.digitalcontainer_array, self.readinchan)
            self.adcollector.collected_data.connect(self.recive_data)
            self.adcollector.start()
#            self.adcollector.save_as_binary(self.savedirectory)
            #self.ai_dev_scaling_coeff = self.adcollector.get_ai_dev_scaling_coeff()
            
#    def execute_tread_external(self, WaveformTuple):
#        sampling_rate_from_external, analogcontainer_array, digitalcontainer_array, readinchan = self.load_waveforms(WaveformTuple)
#        
#        if self.clock_source.currentText() == 'Dev1 as clock source':
#            self.adcollector = execute_analog_readin_optional_digital_thread()
#            self.adcollector.set_waves(sampling_rate_from_external, analogcontainer_array, digitalcontainer_array, readinchan)
#            self.adcollector.collected_data.connect(self.recive_data)
#            self.adcollector.start()
#            self.adcollector.save_as_binary(self.savedirectory)
#            #self.ai_dev_scaling_coeff = self.adcollector.get_ai_dev_scaling_coeff()
#        elif self.clock_source.currentText() == 'Cam as clock source' :
#            self.adcollector = execute_analog_and_readin_digital_optional_camtrig_thread()
#            self.adcollector.set_waves(sampling_rate_from_external, analogcontainer_array, digitalcontainer_array, readinchan)
#            self.adcollector.collected_data.connect(self.recive_data)
#            self.adcollector.start()
#            self.adcollector.save_as_binary(self.savedirectory)
#            #self.ai_dev_scaling_coeff = self.adcollector.get_ai_dev_scaling_coeff()
            
#    def load_waveforms(self, WaveformTuple):
#        self.WaveformSamplingRate = WaveformTuple[0]
#        self.WaveformAnalogContainer = WaveformTuple[1]
#        self.WaveformDigitalContainer = WaveformTuple[2]
#        self.WaveformRecordingChannContainer = WaveformTuple[3]
        
#        return self.WaveformSamplingRate, self.WaveformAnalogContainer, self.WaveformDigitalContainer, self.WaveformRecordingChannContainer
        
    def execute_digital(self):
        
        execute_digital(int(self.textboxAA.value()), self.digitalcontainer_array)
        
    def recive_data(self, data_waveformreceived):
        self.adcollector.save_as_binary(self.savedirectory)
        self.channel_number = len(data_waveformreceived)
        if self.channel_number == 1:            
            if 'Vp' in self.readinchan:
                self.data_collected_0 = data_waveformreceived[0]
            
                self.PlotDataItem_patch_voltage = PlotDataItem(self.xlabelhere_all, self.data_collected_0)
                #use the same color as before, taking advantages of employing same keys in dictionary
                self.PlotDataItem_patch_voltage.setPen('w')
                self.pw_data.addItem(self.PlotDataItem_patch_voltage)
            
                self.textitem_patch_voltage = pg.TextItem(('Vp'), color=('w'), anchor=(1, 1))
                self.textitem_patch_voltage.setPos(0, 1)
                self.pw_data.addItem(self.textitem_patch_voltage)
            elif 'Ip' in self.readinchan:
                self.data_collected_0 = data_waveformreceived[0]
            
                self.PlotDataItem_patch_current = PlotDataItem(self.xlabelhere_all, self.data_collected_0)
                #use the same color as before, taking advantages of employing same keys in dictionary
                self.PlotDataItem_patch_current.setPen('c')
                self.pw_data.addItem(self.PlotDataItem_patch_current)
            
                self.textitem_patch_current = pg.TextItem(('Ip'), color=('w'), anchor=(1, 1))
                self.textitem_patch_current.setPos(0, 1)
                self.pw_data.addItem(self.textitem_patch_current) 
            elif 'PMT' in self.readinchan:
                self.data_collected_0 = data_waveformreceived[0]*-1
                self.data_collected_0 = self.data_collected_0[0:len(self.data_collected_0)-1] # Cut out Extra one read out
                for i in range(self.repeatnum):
                    self.PMT_image_reconstructed_array = self.data_collected_0[np.where(self.PMT_data_index_array_repeated == i+1)]
                    Dataholder_average = np.mean(self.PMT_image_reconstructed_array.reshape(self.averagenum, -1), axis=0)
                    Value_yPixels = int(len(self.samples_1)/self.ScanArrayXnum)
                    self.PMT_image_reconstructed = np.reshape(Dataholder_average, (Value_yPixels, self.ScanArrayXnum))
                    
                    self.PMT_image_reconstructed = self.PMT_image_reconstructed[:, 50:550]
                    
                    # Stack the arrays into a 3d array
                    if i == 0:
                        self.PMT_image_reconstructed_stack = self.PMT_image_reconstructed
                    else:
                        self.PMT_image_reconstructed_stack = np.concatenate((self.PMT_image_reconstructed_stack, self.PMT_image_reconstructed), axis=0)
                    
                    Localimg = Image.fromarray(self.PMT_image_reconstructed) #generate an image object
                    Localimg.save(os.path.join(self.savedirectory, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_PMT_'+str(self.prefixtextbox.text())+'_'+str(i)+'.tif')) #save as tif
                    
                    plt.figure()
                    plt.imshow(self.PMT_image_reconstructed, cmap = plt.cm.gray)
                    plt.show()
                
        elif self.channel_number == 2: 
            if 'PMT' not in self.readinchan:
                self.data_collected_0 = data_waveformreceived[0]
            
                self.PlotDataItem_patch_voltage = PlotDataItem(self.xlabelhere_all, self.data_collected_0)
                #use the same color as before, taking advantages of employing same keys in dictionary
                self.PlotDataItem_patch_voltage.setPen('w')
                self.pw_data.addItem(self.PlotDataItem_patch_voltage)
            
                self.textitem_patch_voltage = pg.TextItem(('Vp'), color=('w'), anchor=(1, 1))
                self.textitem_patch_voltage.setPos(0, 1)
                self.pw_data.addItem(self.textitem_patch_voltage)   
                
                self.data_collected_1 = data_waveformreceived[1]
            
                self.PlotDataItem_patch_current = PlotDataItem(self.xlabelhere_all, self.data_collected_1)
                #use the same color as before, taking advantages of employing same keys in dictionary
                self.PlotDataItem_patch_current.setPen('c')
                self.pw_data.addItem(self.PlotDataItem_patch_current)
            
                self.textitem_patch_current = pg.TextItem(('Ip'), color=('w'), anchor=(1, 1))
                self.textitem_patch_current.setPos(0, 1)
                self.pw_data.addItem(self.textitem_patch_current) 
            elif 'PMT' in self.readinchan:
                self.data_collected_0 = data_waveformreceived[0]*-1
                self.data_collected_0 = self.data_collected_0[0:len(self.data_collected_0)-1]
                for i in range(self.repeatnum):
                    self.PMT_image_reconstructed_array = self.data_collected_0[np.where(self.PMT_data_index_array_repeated == i+1)]
                    Dataholder_average = np.mean(self.PMT_image_reconstructed_array.reshape(self.averagenum, -1), axis=0)
                    Value_yPixels = int(len(self.samples_1)/self.ScanArrayXnum)
                    self.PMT_image_reconstructed = np.reshape(Dataholder_average, (Value_yPixels, self.ScanArrayXnum))
                    
                    self.PMT_image_reconstructed = self.PMT_image_reconstructed[:, 50:550]
                    
                    # Stack the arrays into a 3d array
                    if i == 0:
                        self.PMT_image_reconstructed_stack = self.PMT_image_reconstructed
                    else:
                        self.PMT_image_reconstructed_stack = np.concatenate((self.PMT_image_reconstructed_stack, self.PMT_image_reconstructed), axis=0)
                    
                    Localimg = Image.fromarray(self.PMT_image_reconstructed) #generate an image object
                    Localimg.save(os.path.join(self.savedirectory, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_PMT_'+str(self.prefixtextbox.text())+'_'+str(i)+'.tif')) #save as tif
                    
                    plt.figure()
                    plt.imshow(self.PMT_image_reconstructed, cmap = plt.cm.gray)
                    plt.show()
                    
                if 'Vp' in self.readinchan:
                    self.data_collected_1 = data_waveformreceived[1]
                
                    self.PlotDataItem_patch_voltage = PlotDataItem(self.xlabelhere_all, self.data_collected_1)
                    #use the same color as before, taking advantages of employing same keys in dictionary
                    self.PlotDataItem_patch_voltage.setPen('w')
                    self.pw_data.addItem(self.PlotDataItem_patch_voltage)
                
                    self.textitem_patch_voltage = pg.TextItem(('Vp'), color=('w'), anchor=(1, 1))
                    self.textitem_patch_voltage.setPos(0, 1)
                    self.pw_data.addItem(self.textitem_patch_voltage)
                elif 'Ip' in self.readinchan:
                    self.data_collected_1 = data_waveformreceived[1]
                
                    self.PlotDataItem_patch_current = PlotDataItem(self.xlabelhere_all, self.data_collected_1)
                    #use the same color as before, taking advantages of employing same keys in dictionary
                    self.PlotDataItem_patch_current.setPen('c')
                    self.pw_data.addItem(self.PlotDataItem_patch_current)
                
                    self.textitem_patch_current = pg.TextItem(('Ip'), color=('w'), anchor=(1, 1))
                    self.textitem_patch_current.setPos(0, 1)
                    self.pw_data.addItem(self.textitem_patch_current) 
            
    def startProgressBar(self):
        self.DaqProgressBar_thread = DaqProgressBar()
        self.TotalTimeProgressBar = round((self.reference_length)/int(self.textboxAA.value()), 6)
        self.DaqProgressBar_thread.setlength(self.TotalTimeProgressBar)
        self.DaqProgressBar_thread.change_value.connect(self.setProgressVal)
        self.DaqProgressBar_thread.start()
 
    def setProgressVal(self, val):
        self.waveform_progressbar.setValue(val)
            
    def stopMeasurement_daqer(self):
        """Stop """
        self.adcollector.aboutToQuitHandler()
    '''
        #**************************************************************************************************************************************        
        #**************************************************************************************************************************************
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------Fuc for AOTF---------------------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************
    def updatelinevalue(self, wavelength):
        if wavelength == 640:
            self.line640.setText(str(self.slider640.value()/100))
        if wavelength == 532:
            self.line532.setText(str(self.slider532.value()/100))
        if wavelength == 488:
            self.line488.setText(str(self.slider488.value()/100))
        
    def updateslider(self, wavelength):
        #self.slider640.setSliderPosition(int(float((self.line640.text())*100)))
        if wavelength == 640:
            self.slider640.setValue(int(float(self.line640.text())*100))
        if wavelength == 532:
            self.slider532.setValue(int(float(self.line532.text())*100))
        if wavelength == 488:
            self.slider488.setValue(int(float(self.line488.text())*100))
            
    def execute_tread_single_sample_analog(self, channel):
        if channel == '640AO':
            execute_tread_singlesample_AOTF_analog = execute_tread_singlesample_analog()
            execute_tread_singlesample_AOTF_analog.set_waves(channel, self.slider640.value())
            execute_tread_singlesample_AOTF_analog.start()
        elif channel == '532AO':
            execute_tread_singlesample_AOTF_analog = execute_tread_singlesample_analog()
            execute_tread_singlesample_AOTF_analog.set_waves(channel, self.slider532.value())
            execute_tread_singlesample_AOTF_analog.start()
        elif channel == '488AO':
            execute_tread_singlesample_AOTF_analog = execute_tread_singlesample_analog()
            execute_tread_singlesample_AOTF_analog.set_waves(channel, self.slider488.value())
            execute_tread_singlesample_AOTF_analog.start()            
            
    def execute_tread_single_sample_digital(self, channel):
        if channel == '640blanking':
            if self.switchbutton_640.isChecked():
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 1)
                execute_tread_singlesample_AOTF_digital.start()
            else:
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 0)
                execute_tread_singlesample_AOTF_digital.start()
        elif channel == '532blanking':
            if self.switchbutton_532.isChecked():
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 1)
                execute_tread_singlesample_AOTF_digital.start()
            else:
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 0)
                execute_tread_singlesample_AOTF_digital.start()        
        elif channel == '488blanking':
            if self.switchbutton_488.isChecked():
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 1)
                execute_tread_singlesample_AOTF_digital.start()
            else:
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 0)
                execute_tread_singlesample_AOTF_digital.start()  
                
        elif channel == 'LED':
            if self.switchbutton_LED.isChecked():
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 1)
                execute_tread_singlesample_AOTF_digital.start()
            else:
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 0)
                execute_tread_singlesample_AOTF_digital.start() 
                
    def change_AOTF_icon(self, channel):
        if channel == '640blanking':
            if self.switchbutton_640.isChecked():
                self.AOTF_red_iconlabel.setPixmap(QPixmap('./Icons/AOTF_red_on.png'))
            else:
                self.AOTF_red_iconlabel.setPixmap(QPixmap(self.ICON_off_AOTF))
        elif channel == '532blanking':
            if self.switchbutton_532.isChecked():
                self.AOTF_green_iconlabel.setPixmap(QPixmap('./Icons/AOTF_green_on.png'))
            else:
                self.AOTF_green_iconlabel.setPixmap(QPixmap(self.ICON_off_AOTF))        
        elif channel == '488blanking':
            if self.switchbutton_488.isChecked():
                self.AOTF_blue_iconlabel.setPixmap(QPixmap('./Icons/AOTF_blue_on.png'))
            else:
                self.AOTF_blue_iconlabel.setPixmap(QPixmap(self.ICON_off_AOTF)) 
        elif channel == 'LED':
            if self.switchbutton_LED.isChecked():
                self.switchbutton_LED.setIcon(QIcon('./Icons/LED_on.png'))
            else:
                self.switchbutton_LED.setIcon(QIcon('./Icons/AOTF_off.png'))
                
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------Fucs for set directory-----------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************
    def _open_file_dialog(self):
        self.savedirectory = str(QtWidgets.QFileDialog.getExistingDirectory())
        self.savedirectorytextbox.setText(self.savedirectory)
        self.saving_prefix = str(self.prefixtextbox.text())
        
        # Set the savedirectory and prefix of Waveform widget in syn.
        self.tab2.savedirectory = self.savedirectory
        self.tab2.saving_prefix = self.saving_prefix
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------Fucs for stage movement----------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************        
    def sample_stage_move_upwards(self):
        self.sample_move_distance_yRel = int(self.stage_speed.value())
        stage_movement_thread = StagemovementRelativeThread(0, self.sample_move_distance_yRel)
        stage_movement_thread.current_position.connect(self.update_stage_current_pos)
        stage_movement_thread.start()
        time.sleep(0.5)
        stage_movement_thread.quit()
        stage_movement_thread.wait()
        
    def sample_stage_move_downwards(self):
        self.sample_move_distance_yRel = int(self.stage_speed.value())
        stage_movement_thread = StagemovementRelativeThread(0, -1*self.sample_move_distance_yRel)
        stage_movement_thread.current_position.connect(self.update_stage_current_pos)
        stage_movement_thread.start()
        time.sleep(0.5)
        stage_movement_thread.quit()
        stage_movement_thread.wait()

    def sample_stage_move_leftwards(self):
        self.sample_move_distance_xRel = int(self.stage_speed.value())
        stage_movement_thread = StagemovementRelativeThread(self.sample_move_distance_xRel, 0)
        stage_movement_thread.current_position.connect(self.update_stage_current_pos)
        stage_movement_thread.start()
        time.sleep(0.5)
        stage_movement_thread.quit()
        stage_movement_thread.wait()
        
    def sample_stage_move_rightwards(self):
        self.sample_move_distance_xRel = int(self.stage_speed.value())
        stage_movement_thread = StagemovementRelativeThread(-1*self.sample_move_distance_xRel, 0)
        stage_movement_thread.current_position.connect(self.update_stage_current_pos)
        stage_movement_thread.start()
        time.sleep(0.5)
        stage_movement_thread.quit()
        stage_movement_thread.wait()
        
    def sample_stage_move_towards(self):
        self.sample_move_x = int(float(self.stage_goto_x.text()))
        self.sample_move_y = int(float(self.stage_goto_y.text()))
        stage_movement_thread = StagemovementRelativeThread(self.sample_move_x, self.sample_move_y)
        stage_movement_thread.current_position.connect(self.update_stage_current_pos)
        stage_movement_thread.start()
        time.sleep(2)
        stage_movement_thread.quit()
        stage_movement_thread.wait()
        
    def update_stage_current_pos(self, current_pos):
        self.stage_current_pos = current_pos
        self.stage_current_pos_Label.setText('X:'+str(self.stage_current_pos[0])+' Y: '+str(self.stage_current_pos[1]))
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------Fucs for filter movement---------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #************************************************************************************************************************************** 
    def filter_move_towards(self, COMport, pos):
        filter_movement_thread = FiltermovementThread(COMport, pos)
        #filter_movement_thread.filtercurrent_position.connect(self.update_stage_current_pos)
        filter_movement_thread.start()
        time.sleep(1.5)
        filter_movement_thread.quit()
        filter_movement_thread.wait()

        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------Fucs for camera options---------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #************************************************************************************************************************************** 
    def open_camera(self):
        self.camWindow = ui_camera_lab.CameraUI()
        
        '''
        I set the roiwindow immeadiately to save time, however this funcion also 
        sets the ROI. This is why I clear the ROI afterwards.
        '''
        
        self.camWindow.setGeometry(QRect(100, 100, 600, 600))
        self.camWindow.show()
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------Fucs for console display---------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #************************************************************************************************************************************** 
    def normalOutputWritten(self, text):
        """Append text to the QTextEdit."""
        # Maybe QTextEdit.append() works as well, but this is how I do it:
        cursor = self.console_text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.console_text_edit.setTextCursor(cursor)
        self.console_text_edit.ensureCursorVisible()        

        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------Fucs for Motor movement----------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************         
    def ConnectMotor(self):
        self.ObjMotor_connect.setEnabled(False)
        self.ObjMotor_disconnect.setEnabled(True)
        
        self.pi_device_instance = PIMotor()
        self.normalOutputWritten('Objective motor connected.'+'\n')
        
        self.ObjCurrentPos = self.pi_device_instance.pidevice.qPOS(self.pi_device_instance.pidevice.axes)
        self.ObjMotor_current_pos_Label.setText("Current position: {:.4f}".format(self.ObjCurrentPos['1'])) # Axis here is a string.
        self.ObjMotor_target.setValue(self.ObjCurrentPos['1'])
        
    def MoveMotor(self):
        
        pos = PIMotor.move(self.pi_device_instance.pidevice, self.ObjMotor_target.value())
        self.ObjCurrentPos = self.pi_device_instance.pidevice.qPOS(self.pi_device_instance.pidevice.axes)
        self.ObjMotor_current_pos_Label.setText("Current position: {:.4f}".format(self.ObjCurrentPos['1'])) # Axis here is a string.
        self.ObjMotor_target.setValue(self.ObjCurrentPos['1'])        
      
    def DisconnectMotor(self):
        self.ObjMotor_connect.setEnabled(True)
        self.ObjMotor_disconnect.setEnabled(False)
        
        PIMotor.CloseMotorConnection(self.pi_device_instance.pidevice)
        self.normalOutputWritten('Objective motor disconnected.'+'\n')
        
    def Motor_move_upwards(self):
        self.MotorStep = self.ObjMotor_step.value()
        pos = PIMotor.move(self.pi_device_instance.pidevice, (self.ObjCurrentPos['1'] + self.MotorStep))
        self.ObjCurrentPos = self.pi_device_instance.pidevice.qPOS(self.pi_device_instance.pidevice.axes)
        self.ObjMotor_current_pos_Label.setText("Current position: {:.4f}".format(self.ObjCurrentPos['1'])) # Axis here is a string.
        
    def Motor_move_downwards(self):
        self.MotorStep = self.ObjMotor_step.value()
        pos = PIMotor.move(self.pi_device_instance.pidevice, (self.ObjCurrentPos['1'] - self.MotorStep))
        self.ObjCurrentPos = self.pi_device_instance.pidevice.qPOS(self.pi_device_instance.pidevice.axes)
        self.ObjMotor_current_pos_Label.setText("Current position: {:.4f}".format(self.ObjCurrentPos['1'])) # Axis here is a string.

'''-------------------------------------------------------------------------------------Deprecated------------------------------------------------------------------------------------------  

class pmtwindow(pg.GraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) 
        self.l = pg.GraphicsLayout(border=(100,100,100))
        self.setCentralItem(self.l)
        self.show()
        self.setWindowTitle('pyqtgraph example: GraphicsLayout')
        self.resize(800,600)
        #self.win = pg.GraphicsLayoutWidget()
        
        #block 1 containing pmt image
        self.w0 = self.l.addLayout(row=0, col=0)        
        self.w0.addLabel('PMT image', row=0, col=0) 
        self.vb = self.w0.addViewBox(row=1, col=0, lockAspect=True, colspan=2)       
        ## lock the aspect ratio so pixels are always square
        self.setAspectLocked(True)
        
        ## Create image item
        self.pmt_img = pg.ImageItem(border='w')
        self.vb.addItem(self.pmt_img)
        # Add histogram
        #self.w1 = self.l.addLayout(row=0, col=1)
        self.hiswidget = pg.HistogramLUTItem()
        self.l.addItem(self.hiswidget)
        self.hiswidget.setImageItem(self.pmt_img)
        self.hiswidget.autoHistogramRange()
        
        # create ROI
        self.w2 = self.l.addLayout()
        self.w2.addLabel('ROI', row=0, col=0)        
        self.vb2 = self.w2.addViewBox(row=1, col=0, lockAspect=True, colspan=1)
        self.vb2.name = 'ROI'
        
        self.imgroi = pg.ImageItem()
        self.vb2.addItem(self.imgroi)        
        self.roi = pg.RectROI([20, 20], [20, 20], pen=(0,9))
        self.roi.addRotateFreeHandle([1,0], [0.5, 0.5])
        
        #for self.roi in self.rois:
            #roi.sigRegionChanged.connect(update)
        self.vb.addItem(self.roi)# add ROIs to main image
        
    def update_pmt_Window(self, data):
        """Get a window of the most recent 'windowSize' samples (or less if not available)."""
        self.pmt_img.setImage(data)
        self.imgroi.setImage(self.roi.getArrayRegion(data, self.pmt_img), levels=(0, data.max()))

class weightedimagewindow(pg.GraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) 
        self.l_weightedimgwindow = pg.GraphicsLayout(border=(10,10,10))
        self.setCentralItem(self.l_weightedimgwindow)
        self.show()
        self.setWindowTitle('weightedimgwindow')
        self.resize(300,250)
        #self.win = pg.GraphicsLayoutWidget()
        
        #block 1 containing pmt image
        self.w0_weightedimgwindow = self.l_weightedimgwindow.addLayout(row=0, col=0)        
        #self.w0_weightedimgwindow.addLabel('Average image', row=0, col=0) 
        self.vb_weightedimgwindow = self.w0_weightedimgwindow.addViewBox(row=0, col=0, lockAspect=True, colspan=1, invertY=True)# ImageItem issue! invertY : https://github.com/pyqtgraph/pyqtgraph/issues/315
        ## lock the aspect ratio so pixels are always square
        self.setAspectLocked(True)
        
        ## Create image item
        self.weightedimgItem = pg.ImageItem(border='w')
        self.vb_weightedimgwindow.addItem(self.weightedimgItem)
        # Add histogram
        #self.w1 = self.l.addLayout(row=0, col=1)
        self.hiswidget_weight = pg.HistogramLUTItem()
        self.hiswidget_weight.autoHistogramRange()
        self.l_weightedimgwindow.addItem(self.hiswidget_weight)
        self.hiswidget_weight.setImageItem(self.weightedimgItem)
        

        # create ROI
        self.w2 = self.l_averageimagewindow.addLayout()
        self.w2.addLabel('ROI', row=0, col=0)        
        self.vb2 = self.w2.addViewBox(row=1, col=0, lockAspect=True, colspan=1)
        self.vb2.name = 'ROI'
        
        self.imgroi = pg.ImageItem()
        self.vb2.addItem(self.imgroi)        
        
        # create ROI
        self.rois = []
        self.rois.append(pg.RectROI([20, 20], [20, 20], pen=(0,9)))
        self.rois[-1].addRotateHandle([1,0], [0.5, 0.5])
        
        self.roi_weighted = pg.RectROI([20, 20], [20, 20], pen=(0,9))
        self.roi_weighted.addRotateFreeHandle([1,0], [0.5, 0.5])
        
        #for self.roi in self.rois:
            #roi.sigRegionChanged.connect(update)
        self.vb_weightedimgwindow.addItem(self.roi_weighted)# add ROIs to main image

'''   
        
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        pg.setConfigOptions(imageAxisOrder='row-major')
        mainwin = Mainbody()
        mainwin.show()
        app.exec_()
    run_app()