# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 23:04:00 2019

@author: Meng
================================================================================
    
    Inidival GUI for waveform generating and executing using NI-DAQ
    
================================================================================

"""

from __future__ import division
import sys
sys.path.append('../')
import numpy as np
from matplotlib import pyplot as plt
from IPython import get_ipython
from matplotlib.ticker import FormatStrFormatter
import NIDAQ.wavegenerator
from NIDAQ.generalDaqerThread import execute_analog_readin_optional_digital_thread, execute_tread_singlesample_analog, execute_tread_singlesample_digital, execute_analog_and_readin_digital_optional_camtrig_thread, DaqProgressBar
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QWidget,QLineEdit, QLabel, QGridLayout, QPushButton, QVBoxLayout, QProgressBar, QHBoxLayout, QComboBox, QMessageBox, QPlainTextEdit, QGroupBox, QTabWidget, QCheckBox, QDoubleSpinBox, QSpinBox
from NIDAQ.adfunctiongenerator import generate_AO_for640, generate_AO_for488, generate_DO_forcameratrigger, generate_DO_for640blanking, generate_AO_for532, generate_AO_forpatch, generate_DO_forblankingall, generate_DO_for532blanking, generate_DO_for488blanking, generate_DO_forPerfusion, generate_DO_for2Pshutter, generate_ramp
import pyqtgraph as pg
from pyqtgraph import PlotDataItem, TextItem
import os
from PIL import Image
from NIDAQ.code_5nov import generate_AO
from datetime import datetime
from Oldversions.generalDaqer import execute_digital

class WaveformGenerator(QWidget):
    
    WaveformPackage = pyqtSignal(object)
    GalvoScanInfor = pyqtSignal(object)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        get_ipython().run_line_magic('matplotlib', 'qt') # before start, set spyder back to inline
        
        self.layout = QGridLayout(self)
        # Setting tabs
        self.tabs = QTabWidget()
        self.tab2 = QWidget()
        self.savedirectory = None#r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Patch clamp\2020-2-19 patch-perfusion-Archon1\cell1'
        self.handle_viewbox_coordinate_position_array_expanded_forDaq_waveform = None
        self.time_per_contour = None
        self.handle_viewbox_coordinate_position_array_expanded_x = None
        self.handle_viewbox_coordinate_position_array_expanded_y = None
        self.Daq_sample_rate_pmt = None
        # Add tabs
        self.tabs.addTab(self.tab2,"Waveform")
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------GUI for Waveform tab-------------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************
        self.setMinimumSize(1000,650)
        self.setWindowTitle("Buon appetito!")

        self.Galvo_samples = self.finalwave_640 = self.finalwave_488 = self.finalwave_532=self.finalwave_patch =self.handle_viewbox_coordinate_position_array_expanded_forDaq_waveform=None
        self.finalwave_cameratrigger=self.final_galvotrigger=self.finalwave_blankingall=self.finalwave_640blanking=self.finalwave_532blanking=self.finalwave_488blanking=self.finalwave_Perfusion_8 = self.finalwave_Perfusion_7 = self.finalwave_Perfusion_6 = self.finalwave_Perfusion_2 = self.finalwave_2Pshutter =  None
        
        AnalogContainer = QGroupBox("Analog signals")
        self.AnalogLayout = QGridLayout() #self.AnalogLayout manager
        
        
        self.button_execute = QPushButton('EXECUTE !', self)
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
        self.textbox2A.addItems(['galvos', '640 AO', '532 AO', '488 AO', 'V-patch'])
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
        
        self.wavetabs.setCurrentIndex(3)
        
        #------------------------------------------------------------------------------------------------------------------------------------
        #----------------------------------------------------------Waveform General settings-------------------------------------------------
        #------------------------------------------------------------------------------------------------------------------------------------
        ReadContainer = QGroupBox("General settings")
        self.ReadLayout = QGridLayout() #self.AnalogLayout manager

        self.textboxBB = QComboBox()
        self.textboxBB.addItems(['galvos', '640AO', 'galvos_contour', '488AO', '532AO', 'patchAO','cameratrigger', 'blankingall', '640blanking','532blanking','488blanking', 'Perfusion_8', 'Perfusion_7', 'Perfusion_6', 'Perfusion_2'])
        self.ReadLayout.addWidget(self.textboxBB, 0, 1)
        self.ReadLayout.addWidget(QLabel("Reference waveform:"), 0, 0)

        self.button_all = QPushButton('Organize waveforms', self)
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
        
        self.SamplingRateTextbox = QSpinBox(self)
        self.SamplingRateTextbox.setMinimum(0)
        self.SamplingRateTextbox.setMaximum(1000000)
        self.SamplingRateTextbox.setValue(500000)
        self.SamplingRateTextbox.setSingleStep(100000)        
        self.ReadLayout.addWidget(self.SamplingRateTextbox, 0, 3)
        self.ReadLayout.addWidget(QLabel("Sampling rate for all:"), 0, 2)
        
        # Checkbox for saving waveforms
        self.textboxsavingwaveforms= QCheckBox("Save wavefroms")
#        self.textboxsavingwaveforms.setChecked(True)
        self.textboxsavingwaveforms.setStyleSheet('color:CadetBlue;font:bold "Times New Roman"')
        self.ReadLayout.addWidget(self.textboxsavingwaveforms, 0, 4) 
        
        # Read-in channels
        self.ReadChanPMTTextbox = QCheckBox("---PMT---")
        self.ReadChanPMTTextbox.setStyleSheet('color:CadetBlue;font:bold "Times New Roman"')
        self.ReadLayout.addWidget(self.ReadChanPMTTextbox, 1, 1)     

        self.ReadChanVpTextbox = QCheckBox("---Vp---")
        self.ReadChanVpTextbox.setStyleSheet('color:Indigo;font:bold "Times New Roman"')
        self.ReadLayout.addWidget(self.ReadChanVpTextbox, 1, 2)   
        
        self.ReadChanIpTextbox = QCheckBox("---Ip---")
        self.ReadChanIpTextbox.setStyleSheet('color:DarkSlateGray	;font:bold "Times New Roman"')
        self.ReadLayout.addWidget(self.ReadChanIpTextbox, 1, 3)
        
        self.ReadLayout.addWidget(QLabel("Recording channels: "), 1, 0)
        
        self.clock_source = QComboBox()
        self.clock_source.addItems(['Dev1 as clock source', 'Cam as clock source'])
        self.ReadLayout.addWidget(self.clock_source, 1, 4)
        
        self.saving_prefix = ''
        self.savedirectorytextbox = QtWidgets.QLineEdit(self)
        self.ReadLayout.addWidget(self.savedirectorytextbox, 2, 1)
        
        self.prefixtextbox = QtWidgets.QLineEdit(self)
        self.prefixtextbox.setPlaceholderText('Prefix')
        self.ReadLayout.addWidget(self.prefixtextbox, 2, 2)
        
        self.toolButtonOpenDialog = QtWidgets.QPushButton('Saving directory')
        self.toolButtonOpenDialog.setStyleSheet("QPushButton {color:teal;background-color: pink; border-style: outset;border-radius: 3px;border-width: 2px;font: bold 14px;padding: 1px}"
                                                "QPushButton:pressed {color:yellow;background-color: pink; border-style: outset;border-radius: 3px;border-width: 2px;font: bold 14px;padding: 1px}")

        self.toolButtonOpenDialog.setObjectName("toolButtonOpenDialog")
        self.toolButtonOpenDialog.clicked.connect(self._open_file_dialog)
        
        self.ReadLayout.addWidget(self.toolButtonOpenDialog, 2, 0)
        
        ReadContainer.setLayout(self.ReadLayout)

        # ------------------------------------------------------ANALOG-----------------------------------------------------------        

        
        # Tab for general block wave
        self.AnalogFreqTextbox = QLineEdit(self)
        self.wavetablayout.addWidget(self.AnalogFreqTextbox, 0, 1)
        self.wavetablayout.addWidget(QLabel("Frequency in period:"), 0, 0)

        self.AnalogOffsetTextbox = QLineEdit(self)
        self.AnalogOffsetTextbox.setPlaceholderText('0')
        self.wavetablayout.addWidget(self.AnalogOffsetTextbox, 1, 1)
        self.wavetablayout.addWidget(QLabel("Offset (ms):"), 1, 0)
        
        self.AnalogDurationTextbox = QLineEdit(self)
        self.wavetablayout.addWidget(self.AnalogDurationTextbox, 0, 3)
        self.wavetablayout.addWidget(QLabel("Duration (ms, 1 cycle):"), 0, 2)   
        
        self.AnalogRepeatTextbox = QLineEdit(self)
        self.AnalogRepeatTextbox.setPlaceholderText('1')
        self.wavetablayout.addWidget(self.AnalogRepeatTextbox, 1, 3)
        self.wavetablayout.addWidget(QLabel("Repeat:"), 1, 2) 
        
        self.wavetablayout.addWidget(QLabel("DC (%):"), 0, 4)
        self.AnalogDCTextbox = QComboBox()
        self.AnalogDCTextbox.addItems(['50','100','10','5','0'])
        self.wavetablayout.addWidget(self.AnalogDCTextbox, 0, 5)
        
        self.AnalogGapTextbox = QLineEdit(self)
        self.AnalogGapTextbox.setPlaceholderText('0')
        self.wavetablayout.addWidget(self.AnalogGapTextbox, 1, 5)
        self.wavetablayout.addWidget(QLabel("Gap between repeat (samples):"), 1, 4)
        
        self.wavetablayout.addWidget(QLabel("Starting amplitude (V):"), 2, 0)
        self.AnalogStartingAmpTextbox = QDoubleSpinBox(self)
        self.AnalogStartingAmpTextbox.setMinimum(-10)
        self.AnalogStartingAmpTextbox.setMaximum(10)
        self.AnalogStartingAmpTextbox.setValue(5)
        self.AnalogStartingAmpTextbox.setSingleStep(0.5)  
        self.wavetablayout.addWidget(self.AnalogStartingAmpTextbox, 2, 1)        

        self.AnalogBaselineTextbox = QLineEdit(self)
        self.AnalogBaselineTextbox.setPlaceholderText('0')
        self.wavetablayout.addWidget(self.AnalogBaselineTextbox, 3, 1)
        self.wavetablayout.addWidget(QLabel("Baseline (V):"), 3, 0)

        self.wavetablayout.addWidget(QLabel("Step (V):"), 2, 2)
        self.AnalogStepTextbox = QDoubleSpinBox(self)
        self.AnalogStepTextbox.setMinimum(-10)
        self.AnalogStepTextbox.setMaximum(10)
        self.AnalogStepTextbox.setValue(5)
        self.AnalogStepTextbox.setSingleStep(0.5)
        self.wavetablayout.addWidget(self.AnalogStepTextbox, 2, 3)

        self.wavetablayout.addWidget(QLabel("Cycles:"), 3, 2)
        self.AnalogCyclesTextbox = QSpinBox(self)
        self.AnalogCyclesTextbox.setMinimum(0)
        self.AnalogCyclesTextbox.setMaximum(100)
        self.AnalogCyclesTextbox.setValue(1)
        self.AnalogCyclesTextbox.setSingleStep(1) 
        self.wavetablayout.addWidget(self.AnalogCyclesTextbox, 3, 3)
                
        self.wavetab1.setLayout(self.wavetablayout)
        
        # Tab for general Pramp wave
        self.wavetablayout_ramp= QGridLayout()
        self.AnalogFreqTextbox_ramp = QLineEdit(self)
        self.wavetablayout_ramp.addWidget(self.AnalogFreqTextbox_ramp, 0, 1)
        self.wavetablayout_ramp.addWidget(QLabel("Frequency in period:"), 0, 0)

        self.AnalogOffsetTextbox_ramp = QLineEdit(self)
        self.AnalogOffsetTextbox_ramp.setPlaceholderText('0')
        self.wavetablayout_ramp.addWidget(self.AnalogOffsetTextbox_ramp, 1, 1)
        self.wavetablayout_ramp.addWidget(QLabel("Offset (ms):"), 1, 0)
        
        self.AnalogDurationTextbox_ramp = QLineEdit(self)
        self.wavetablayout_ramp.addWidget(self.AnalogDurationTextbox_ramp, 0, 3)
        self.wavetablayout_ramp.addWidget(QLabel("Duration (ms, 1 cycle):"), 0, 2)  
        
        self.AnalogDCTextbox_ramp = QLineEdit(self)
        self.AnalogDCTextbox_ramp.setPlaceholderText('0.5')
        self.wavetablayout_ramp.addWidget(self.AnalogDCTextbox_ramp, 0, 5)
        self.wavetablayout_ramp.addWidget(QLabel("Symmetry:"), 0, 4)
        
        
        self.AnalogRepeatTextbox_ramp = QLineEdit(self)
        self.AnalogRepeatTextbox_ramp.setPlaceholderText('1')
        self.wavetablayout_ramp.addWidget(self.AnalogRepeatTextbox_ramp, 1, 3)
        self.wavetablayout_ramp.addWidget(QLabel("Repeat:"), 1, 2) 
        
        self.AnalogGapTextbox_ramp = QLineEdit(self)
        self.AnalogGapTextbox_ramp.setPlaceholderText('0')
        self.wavetablayout_ramp.addWidget(self.AnalogGapTextbox_ramp, 1, 5)
        self.wavetablayout_ramp.addWidget(QLabel("Gap between repeat (samples):"), 1, 4)
        
        self.wavetablayout_ramp.addWidget(QLabel("Height (V):"), 2, 0)
        self.AnalogStartingAmpTextbox_ramp = QDoubleSpinBox(self)
        self.AnalogStartingAmpTextbox_ramp.setMinimum(-10)
        self.AnalogStartingAmpTextbox_ramp.setMaximum(10)
        self.AnalogStartingAmpTextbox_ramp.setValue(2)
        self.AnalogStartingAmpTextbox_ramp.setSingleStep(0.5)  
        self.wavetablayout_ramp.addWidget(self.AnalogStartingAmpTextbox_ramp, 2, 1)        

        self.AnalogBaselineTextbox_ramp = QLineEdit(self)
        self.AnalogBaselineTextbox_ramp.setPlaceholderText('0')
        self.wavetablayout_ramp.addWidget(self.AnalogBaselineTextbox_ramp, 3, 1)
        self.wavetablayout_ramp.addWidget(QLabel("Baseline (V):"), 3, 0)

        self.wavetablayout_ramp.addWidget(QLabel("Step (V):"), 2, 2)
        self.AnalogStepTextbox_ramp = QDoubleSpinBox(self)
        self.AnalogStepTextbox_ramp.setMinimum(-10)
        self.AnalogStepTextbox_ramp.setMaximum(10)
        self.AnalogStepTextbox_ramp.setValue(1)
        self.AnalogStepTextbox_ramp.setSingleStep(0.5)
        self.wavetablayout_ramp.addWidget(self.AnalogStepTextbox_ramp, 2, 3)

        self.wavetablayout_ramp.addWidget(QLabel("Cycles:"), 3, 2)
        self.AnalogCyclesTextbox_ramp = QSpinBox(self)
        self.AnalogCyclesTextbox_ramp.setMinimum(0)
        self.AnalogCyclesTextbox_ramp.setMaximum(100)
        self.AnalogCyclesTextbox_ramp.setValue(1)
        self.AnalogCyclesTextbox_ramp.setSingleStep(1) 
        self.wavetablayout_ramp.addWidget(self.AnalogCyclesTextbox_ramp, 3, 3)
                
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
        self.GalvoVoltXMinTextbox = QSpinBox(self)
        self.GalvoVoltXMinTextbox.setMinimum(-10)
        self.GalvoVoltXMinTextbox.setMaximum(10)
        self.GalvoVoltXMinTextbox.setValue(-5)
        self.GalvoVoltXMinTextbox.setSingleStep(1)        
        self.galvo_raster_tablayout.addWidget(self.GalvoVoltXMinTextbox, 0, 1)
        self.galvo_raster_tablayout.addWidget(QLabel("voltXMin"), 0, 0)

        self.GalvoVoltXMaxTextbox = QSpinBox(self)
        self.GalvoVoltXMaxTextbox.setMinimum(-10)
        self.GalvoVoltXMaxTextbox.setMaximum(10)
        self.GalvoVoltXMaxTextbox.setValue(5)
        self.GalvoVoltXMaxTextbox.setSingleStep(1)   
        self.galvo_raster_tablayout.addWidget(self.GalvoVoltXMaxTextbox, 1, 1)
        self.galvo_raster_tablayout.addWidget(QLabel("voltXMax"), 1, 0)

        self.GalvoVoltYMinTextbox = QSpinBox(self)
        self.GalvoVoltYMinTextbox.setMinimum(-10)
        self.GalvoVoltYMinTextbox.setMaximum(10)
        self.GalvoVoltYMinTextbox.setValue(-5)
        self.GalvoVoltYMinTextbox.setSingleStep(1)   
        self.galvo_raster_tablayout.addWidget(self.GalvoVoltYMinTextbox, 0, 3)
        self.galvo_raster_tablayout.addWidget(QLabel("voltYMin"), 0, 2)

        self.GalvoVoltYMaxTextbox = QSpinBox(self)
        self.GalvoVoltYMaxTextbox.setMinimum(-10)
        self.GalvoVoltYMaxTextbox.setMaximum(10)
        self.GalvoVoltYMaxTextbox.setValue(5)
        self.GalvoVoltYMaxTextbox.setSingleStep(1)   
        self.galvo_raster_tablayout.addWidget(self.GalvoVoltYMaxTextbox, 1, 3)
        self.galvo_raster_tablayout.addWidget(QLabel("voltYMax"), 1, 2)

        self.GalvoXpixelNumTextbox = QComboBox()
        self.GalvoXpixelNumTextbox.addItems(['500','256'])
        self.galvo_raster_tablayout.addWidget(self.GalvoXpixelNumTextbox, 0, 5)
        self.galvo_raster_tablayout.addWidget(QLabel("X pixel number"), 0, 4)

        self.GalvoYpixelNumTextbox = QComboBox()
        self.GalvoYpixelNumTextbox.addItems(['500','256'])
        self.galvo_raster_tablayout.addWidget(self.GalvoYpixelNumTextbox, 1, 5)
        self.galvo_raster_tablayout.addWidget(QLabel("Y pixel number"), 1, 4)
        
        self.GalvoOffsetTextbox = QLineEdit(self)
        self.GalvoOffsetTextbox.setPlaceholderText('0')
        self.galvo_raster_tablayout.addWidget(self.GalvoOffsetTextbox, 2, 1)
        self.galvo_raster_tablayout.addWidget(QLabel("Offset (ms):"), 2, 0)
        
        self.GalvoGapTextbox = QLineEdit(self)
        self.GalvoGapTextbox.setPlaceholderText('0')
        self.galvo_raster_tablayout.addWidget(self.GalvoGapTextbox, 2, 3)
        self.galvo_raster_tablayout.addWidget(QLabel("Gap between scans(ms):"), 2, 2)       

        self.GalvoAvgNumTextbox = QSpinBox(self)
        self.GalvoAvgNumTextbox.setMinimum(1)
        self.GalvoAvgNumTextbox.setMaximum(20)
        self.GalvoAvgNumTextbox.setValue(1)
        self.GalvoAvgNumTextbox.setSingleStep(1)
        self.galvo_raster_tablayout.addWidget(self.GalvoAvgNumTextbox, 2, 5)
        self.galvo_raster_tablayout.addWidget(QLabel("average over:"), 2, 4)        

        self.GalvoRepeatTextbox = QSpinBox(self)
        self.GalvoRepeatTextbox.setMinimum(1)
        self.GalvoRepeatTextbox.setMaximum(20)
        self.GalvoRepeatTextbox.setValue(1)
        self.GalvoRepeatTextbox.setSingleStep(1)
        self.galvo_raster_tablayout.addWidget(self.GalvoRepeatTextbox, 0, 7)
        self.galvo_raster_tablayout.addWidget(QLabel("Repeat:"), 0, 6)  
        
        self.galvo_contour_label_1 = QLabel("Points in contour:")
        self.galvo_contour_tablayout.addWidget(self.galvo_contour_label_1, 0, 0)
        
        self.galvo_contour_label_2 = QLabel("Sampling rate: ")
        self.galvo_contour_tablayout.addWidget(self.galvo_contour_label_2, 0, 1)
        
        self.GalvoContourLastTextbox = QSpinBox(self)
        self.GalvoContourLastTextbox.setMinimum(000000)
        self.GalvoContourLastTextbox.setMaximum(200000)
        self.GalvoContourLastTextbox.setValue(1000)
        self.GalvoContourLastTextbox.setSingleStep(500)
        self.galvo_contour_tablayout.addWidget(self.GalvoContourLastTextbox, 0, 3)
        self.galvo_contour_tablayout.addWidget(QLabel("Last(ms):"), 0, 2)        
        
        self.normal_galvo_tab.setLayout(self.galvo_raster_tablayout)
        self.contour_galvo_tab.setLayout(self.galvo_contour_tablayout)
        self.galvos_tabs.addTab(self.normal_galvo_tab, 'Raster scanning')
        self.galvos_tabs.addTab(self.contour_galvo_tab, 'Contour scanning')

        self.galvotablayout.addWidget(self.galvos_tabs,0,0)
        '''
        self.button1 = QPushButton('SHOW WAVE', self)
        self.galvotablayout.addWidget(self.button1, 1, 11)
        
        self.button1.clicked.connect(self.generate_galvos)
        self.button1.clicked.connect(self.generate_galvos_graphy)
        
        self.button_triggerforcam = QPushButton('With trigger!', self)
        self.galvotablayout.addWidget(self.button_triggerforcam, 2, 9)
        
        self.GalvoRepeatTextbox = QComboBox()
        self.GalvoRepeatTextbox.addItems(['0','1'])
        self.galvotablayout.addWidget(self.GalvoRepeatTextbox, 2, 10)
        
        self.button_triggerforcam.clicked.connect(self.generate_galvotrigger)        
        self.button_triggerforcam.clicked.connect(self.generate_galvotrigger_graphy)
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
        #---------------!!!!!!!!!!!!!!!!! now 'EXECUTE DIGITAL' button is depreceted----------------------------------------------
#        self.button_execute_digital = QPushButton('EXECUTE DIGITAL', self)
#        self.button_execute_digital.setStyleSheet("QPushButton {color:white;background-color: BlueViolet; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
#                                                  "QPushButton:pressed {color:black;background-color: BlueViolet; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
#        self.DigitalLayout.addWidget(self.button_execute_digital, 0, 3)
        
        self.button_del_digital = QPushButton('Delete', self)
        self.button_del_digital.setStyleSheet("QPushButton {color:white;background-color: Crimson; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                              "QPushButton:pressed {color:black;background-color: Crimson; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
  
        self.DigitalLayout.addWidget(self.button_del_digital, 0, 2)
        
#        self.button_execute_digital.clicked.connect(self.execute_digital)
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

        
        self.DigFreqTextbox = QLineEdit(self)
        self.digitalwavetablayout.addWidget(self.DigFreqTextbox, 0, 1)
        self.digitalwavetablayout.addWidget(QLabel("Frequency in period:"), 0, 0)

        self.DigOffsetTextbox = QLineEdit(self)
        self.DigOffsetTextbox.setPlaceholderText('0')
        self.digitalwavetablayout.addWidget(self.DigOffsetTextbox, 1, 1)
        self.digitalwavetablayout.addWidget(QLabel("Offset (ms):"), 1, 0)
        
        self.DigDurationTextbox = QLineEdit(self)
        self.digitalwavetablayout.addWidget(self.DigDurationTextbox, 0, 3)
        self.digitalwavetablayout.addWidget(QLabel("Duration (ms):"), 0, 2)   
        
        self.DigRepeatTextbox = QLineEdit(self)
        self.DigRepeatTextbox.setPlaceholderText('1')
        self.digitalwavetablayout.addWidget(self.DigRepeatTextbox, 1, 3)
        self.digitalwavetablayout.addWidget(QLabel("Repeat:"), 1, 2) 
        
        self.digitalwavetablayout.addWidget(QLabel("DC (%):"), 0, 4)
        self.DigDCTextbox = QComboBox()
        self.DigDCTextbox.addItems(['50','10','0','100'])
        self.digitalwavetablayout.addWidget(self.DigDCTextbox, 0, 5)

        self.DigGapTextbox = QLineEdit(self)
        self.DigGapTextbox.setPlaceholderText('0')
        self.digitalwavetablayout.addWidget(self.DigGapTextbox, 1, 5)
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
#        master_waveform.addWidget(self.pw_data, 4, 0)
        self.tab2.setLayout(master_waveform)        
        #**************************************************************************************************************************************        
#        self.setLayout(pmtmaster)
        self.layout.addWidget(self.tabs, 0, 0)
        self.setLayout(self.layout)
        
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
                
        if self.uiDaq_sample_rate != int(self.SamplingRateTextbox.value()):
            print('ERROR: Sampling rates is different!')
        
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
            
            
    def generate_contour_for_waveform(self):
        self.contour_time = int(self.GalvoContourLastTextbox.value())
        
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
                                     
    def generate_galvos(self):
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        
        #Scanning settings
        #if int(self.textbox1A.currentText()) == 1:
        Value_voltXMin = int(self.GalvoVoltXMinTextbox.value())
        Value_voltXMax = int(self.GalvoVoltXMaxTextbox.value())
        Value_voltYMin = int(self.GalvoVoltYMinTextbox.value())
        Value_voltYMax = int(self.GalvoVoltYMaxTextbox.value())
        Value_xPixels = int(self.GalvoXpixelNumTextbox.currentText())
        Value_yPixels = int(self.GalvoYpixelNumTextbox.currentText())
        self.averagenum =int(self.GalvoAvgNumTextbox.value())
        self.repeatnum = int(self.GalvoRepeatTextbox.value())
        if not self.GalvoOffsetTextbox.text():
            self.Galvo_samples_offset = 1
            self.offsetsamples_galvo = []

        else:
            self.Galvo_samples_offset = int(self.GalvoOffsetTextbox.text())
            
            self.offsetsamples_number_galvo = int((self.Galvo_samples_offset/1000)*self.uiDaq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
            self.offsetsamples_galvo = np.zeros(self.offsetsamples_number_galvo) # Be default offsetsamples_number is an integer.    
        #Generate galvo samples            
        self.samples_1, self.samples_2= NIDAQ.wavegenerator.waveRecPic(sampleRate = self.uiDaq_sample_rate, imAngle = 0, voltXMin = Value_voltXMin, voltXMax = Value_voltXMax, 
                         voltYMin = Value_voltYMin, voltYMax = Value_voltYMax, xPixels = Value_xPixels, yPixels = Value_yPixels, 
                         sawtooth = True)
        #ScanArrayX = wavegenerator.xValuesSingleSawtooth(sampleRate = Daq_sample_rate, voltXMin = Value_voltXMin, voltXMax = Value_voltXMax, xPixels = Value_xPixels, sawtooth = True)
        #Totalscansamples = len(self.samples_1)*self.averagenum # Calculate number of samples to feed to scanner, by default it's one frame 
        self.ScanArrayXnum = int (len(self.samples_1)/Value_yPixels) # number of samples of each individual line of x scanning
        if not self.GalvoGapTextbox.text():
            gap_sample = 0
            self.gapsamples_number_galvo = 0
        else:
            gap_sample = int(self.GalvoGapTextbox.text())
            
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
        
        # self.PMT_data_index_array_repeated is created to help locate pmt data at different pre-set average or repeat scanning scheme.
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
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        #Scanning settings
        #if int(self.textbox1A.currentText()) == 1:
        Value_voltXMin = int(self.GalvoVoltXMinTextbox.value())
        Value_voltXMax = int(self.GalvoVoltXMaxTextbox.value())
        Value_voltYMin = int(self.GalvoVoltYMinTextbox.value())
        Value_voltYMax = int(self.GalvoVoltYMaxTextbox.value())
        Value_xPixels = int(self.GalvoXpixelNumTextbox.currentText())
        Value_yPixels = int(self.GalvoYpixelNumTextbox.currentText())
        self.averagenum =int(self.GalvoAvgNumTextbox.value())
        repeatnum = int(self.GalvoRepeatTextbox.value())
        if not self.GalvoOffsetTextbox.text():
            self.Galvo_samples_offset = 1
            self.offsetsamples_galvo = []

        else:
            self.Galvo_samples_offset = int(self.GalvoOffsetTextbox.text())
            
            self.offsetsamples_number_galvo = int((self.Galvo_samples_offset/1000)*self.uiDaq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
            self.offsetsamples_galvo = np.zeros(self.offsetsamples_number_galvo) # Be default offsetsamples_number is an integer.    
        #Generate galvo samples            
        self.samples_1, self.samples_2= NIDAQ.wavegenerator.waveRecPic(sampleRate = self.uiDaq_sample_rate, imAngle = 0, voltXMin = Value_voltXMin, voltXMax = Value_voltXMax, 
                         voltYMin = Value_voltYMin, voltYMax = Value_voltYMax, xPixels = Value_xPixels, yPixels = Value_yPixels, 
                         sawtooth = True)
        self.ScanArrayXnum = int (len(self.samples_1)/Value_yPixels) # number of samples of each individual line of x scanning
        if not self.GalvoGapTextbox.text():
            gap_sample = 0
            self.gapsamples_number_galvo = 0
        else:
            gap_sample = int(self.GalvoGapTextbox.text())
            
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
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        self.uiwavefrequency_2 = float(self.AnalogFreqTextbox.text())
        if not self.AnalogOffsetTextbox.text():
            self.uiwaveoffset_2 = 0
        else:
            self.uiwaveoffset_2 = int(self.AnalogOffsetTextbox.text()) # in ms
        self.uiwaveperiod_2 = int(self.AnalogDurationTextbox.text())
        self.uiwaveDC_2 = int(self.AnalogDCTextbox.currentText())
        if not self.AnalogRepeatTextbox.text():
            self.uiwaverepeat_2 = 1
        else:
            self.uiwaverepeat_2 = int(self.AnalogRepeatTextbox.text())
        if not self.AnalogGapTextbox.text():
            self.uiwavegap_2 = 0
        else:
            self.uiwavegap_2 = int(self.AnalogGapTextbox.text())
        self.uiwavestartamplitude_2 = float(self.AnalogStartingAmpTextbox.value())
        if not self.AnalogBaselineTextbox.text():
            self.uiwavebaseline_2 = 0
        else:
            self.uiwavebaseline_2 = float(self.AnalogBaselineTextbox.text())
        self.uiwavestep_2 = float(self.AnalogStepTextbox.value())
        self.uiwavecycles_2 = int(self.AnalogCyclesTextbox.value())   
        
            
        s = generate_AO_for640(self.uiDaq_sample_rate, self.uiwavefrequency_2, self.uiwaveoffset_2, self.uiwaveperiod_2, self.uiwaveDC_2
                               , self.uiwaverepeat_2, self.uiwavegap_2, self.uiwavestartamplitude_2, self.uiwavebaseline_2, self.uiwavestep_2, self.uiwavecycles_2)
        self.finalwave_640 = s.generate()
        return self.finalwave_640
            
    def generate_640AO_graphy(self):            
        xlabelhere_640 = np.arange(len(self.finalwave_640))/self.uiDaq_sample_rate
        #plt.plot(xlabelhere_galvo, samples_1)
        self.PlotDataItem_640AO = PlotDataItem(xlabelhere_640, self.finalwave_640, downsample = 10)
        self.PlotDataItem_640AO.setPen('r')
        self.PlotDataItem_640AO.setDownsampling(ds=(int(self.SamplingRateTextbox.value())/10), method='mean')
        self.pw.addItem(self.PlotDataItem_640AO)
        
        self.textitem_640AO = pg.TextItem(text='640 AO', color=('r'), anchor=(1, 1))
        self.textitem_640AO.setPos(0, 4)
        self.pw.addItem(self.textitem_640AO)
           

    def generate_488AO(self):
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        self.uiwavefrequency_488AO = float(self.AnalogFreqTextbox.text())
        if not self.AnalogOffsetTextbox.text():
            self.uiwaveoffset_488AO = 0
        else:
            self.uiwaveoffset_488AO = int(self.AnalogOffsetTextbox.text()) # in ms
        self.uiwaveperiod_488AO = int(self.AnalogDurationTextbox.text())
        self.uiwaveDC_488AO = int(self.AnalogDCTextbox.currentText())
        if not self.AnalogRepeatTextbox.text():
            self.uiwaverepeat_488AO = 1
        else:
            self.uiwaverepeat_488AO = int(self.AnalogRepeatTextbox.text())
        if not self.AnalogGapTextbox.text():
            self.uiwavegap_488AO = 0
        else:
            self.uiwavegap_488AO = int(self.AnalogGapTextbox.text())
        self.uiwavestartamplitude_488AO = float(self.AnalogStartingAmpTextbox.value())
        if not self.AnalogBaselineTextbox.text():
            self.uiwavebaseline_488AO = 0
        else:
            self.uiwavebaseline_488AO = float(self.AnalogBaselineTextbox.text())
        self.uiwavestep_488AO = float(self.AnalogStepTextbox.value())
        self.uiwavecycles_488AO = int(self.AnalogCyclesTextbox.value())   
                    
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
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        self.uiwavefrequency_532AO = float(self.AnalogFreqTextbox.text())
        if not self.AnalogOffsetTextbox.text():
            self.uiwaveoffset_532AO = 0
        else:
            self.uiwaveoffset_532AO = int(self.AnalogOffsetTextbox.text()) # in ms
        self.uiwaveperiod_532AO = int(self.AnalogDurationTextbox.text())
        self.uiwaveDC_532AO = int(self.AnalogDCTextbox.currentText())
        if not self.AnalogRepeatTextbox.text():
            self.uiwaverepeat_532AO = 1
        else:
            self.uiwaverepeat_532AO = int(self.AnalogRepeatTextbox.text())
        if not self.AnalogGapTextbox.text():
            self.uiwavegap_532AO = 0
        else:
            self.uiwavegap_532AO = int(self.AnalogGapTextbox.text())
        self.uiwavestartamplitude_532AO = float(self.AnalogStartingAmpTextbox.value())
        if not self.AnalogBaselineTextbox.text():
            self.uiwavebaseline_532AO = 0
        else:
            self.uiwavebaseline_532AO = float(self.AnalogBaselineTextbox.text())
        self.uiwavestep_532AO = float(self.AnalogStepTextbox.value())
        self.uiwavecycles_532AO = int(self.AnalogCyclesTextbox.value())   
        
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
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        self.uiwavefrequency_patchAO = float(self.AnalogFreqTextbox.text())
        if not self.AnalogOffsetTextbox.text():
            self.uiwaveoffset_patchAO = 0
        else:
            self.uiwaveoffset_patchAO = int(self.AnalogOffsetTextbox.text()) # in ms
        self.uiwaveperiod_patchAO = int(self.AnalogDurationTextbox.text())
        self.uiwaveDC_patchAO = int(self.AnalogDCTextbox.currentText())
        if not self.AnalogRepeatTextbox.text():
            self.uiwaverepeat_patchAO = 1
        else:
            self.uiwaverepeat_patchAO = int(self.AnalogRepeatTextbox.text())
        if not self.AnalogGapTextbox.text():
            self.uiwavegap_patchAO = 0
        else:
            self.uiwavegap_patchAO = int(self.AnalogGapTextbox.text())
        self.uiwavestartamplitude_patchAO = float(self.AnalogStartingAmpTextbox.value())
        if not self.AnalogBaselineTextbox.text():
            self.uiwavebaseline_patchAO = 0
        else:
            self.uiwavebaseline_patchAO = float(self.AnalogBaselineTextbox.text())
        self.uiwavestep_patchAO = float(self.AnalogStepTextbox.value())
        self.uiwavecycles_patchAO = int(self.AnalogCyclesTextbox.value())   
        
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
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        self.uiwavefrequency_ramp = float(self.AnalogFreqTextbox_ramp.text())
        if not self.AnalogOffsetTextbox_ramp.text():
            self.uiwaveoffset_ramp = 0
        else:
            self.uiwaveoffset_ramp = int(self.AnalogOffsetTextbox_ramp.text()) # in ms
        self.uiwaveperiod_ramp = int(self.AnalogDurationTextbox_ramp.text())
        if not self.AnalogDCTextbox_ramp.text():
            self.uiwavesymmetry_ramp = 0.5
        else:
            self.uiwavesymmetry_ramp = float(self.AnalogDCTextbox_ramp.text())
        if not self.AnalogRepeatTextbox_ramp.text():
            self.uiwaverepeat_ramp = 1
        else:
            self.uiwaverepeat_ramp = int(self.AnalogRepeatTextbox_ramp.text())
        if not self.AnalogGapTextbox_ramp.text():
            self.uiwavegap_ramp = 0
        else:
            self.uiwavegap_ramp = int(self.AnalogGapTextbox_ramp.text())
        self.uiwavestartamplitude_ramp = float(self.AnalogStartingAmpTextbox_ramp.value())
        if not self.AnalogBaselineTextbox_ramp.text():
            self.uiwavebaseline_ramp = 0
        else:
            self.uiwavebaseline_ramp = float(self.AnalogBaselineTextbox_ramp.text())
        self.uiwavestep_ramp = float(self.AnalogStepTextbox_ramp.value())
        self.uiwavecycles_ramp = int(self.AnalogCyclesTextbox_ramp.value())   
        
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
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        self.uiwavefrequency_cameratrigger = float(self.DigFreqTextbox.text())
        if not self.DigOffsetTextbox.text():
            self.uiwaveoffset_cameratrigger = 0
        else:
            self.uiwaveoffset_cameratrigger = int(self.DigOffsetTextbox.text())
        self.uiwaveperiod_cameratrigger = int(self.DigDurationTextbox.text())
        self.uiwaveDC_cameratrigger = int(self.DigDCTextbox.currentText())
        if not self.DigRepeatTextbox.text():
            self.uiwaverepeat_cameratrigger_number = 1
        else:
            self.uiwaverepeat_cameratrigger_number = int(self.DigRepeatTextbox.text())
        if not self.DigGapTextbox.text():
            self.uiwavegap_cameratrigger = 0
        else:
            self.uiwavegap_cameratrigger = int(self.DigGapTextbox.text())
        
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
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        self.uiwavefrequency_640blanking = float(self.DigFreqTextbox.text())
        if not self.DigOffsetTextbox.text():
            self.uiwaveoffset_640blanking = 0
        else:
            self.uiwaveoffset_640blanking = int(self.DigOffsetTextbox.text())
        self.uiwaveperiod_640blanking = int(self.DigDurationTextbox.text())
        self.uiwaveDC_640blanking = int(self.DigDCTextbox.currentText())
        if not self.DigRepeatTextbox.text():
            self.uiwaverepeat_640blanking_number = 1
        else:
            self.uiwaverepeat_640blanking_number = int(self.DigRepeatTextbox.text())
        if not self.DigGapTextbox.text():
            self.uiwavegap_640blanking = 0
        else:
            self.uiwavegap_640blanking = int(self.DigGapTextbox.text())
        
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
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        self.uiwavefrequency_532blanking = float(self.DigFreqTextbox.text())
        if not self.DigOffsetTextbox.text():
            self.uiwaveoffset_532blanking = 0
        else:
            self.uiwaveoffset_532blanking = int(self.DigOffsetTextbox.text())
        self.uiwaveperiod_532blanking = int(self.DigDurationTextbox.text())
        self.uiwaveDC_532blanking = int(self.DigDCTextbox.currentText())
        if not self.DigRepeatTextbox.text():
            self.uiwaverepeat_532blanking_number = 1
        else:
            self.uiwaverepeat_532blanking_number = int(self.DigRepeatTextbox.text())
        if not self.DigGapTextbox.text():
            self.uiwavegap_532blanking = 0
        else:
            self.uiwavegap_532blanking = int(self.DigGapTextbox.text())
        
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
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        self.uiwavefrequency_488blanking = float(self.DigFreqTextbox.text())
        if not self.DigOffsetTextbox.text():
            self.uiwaveoffset_488blanking = 0
        else:
            self.uiwaveoffset_488blanking = int(self.DigOffsetTextbox.text())
        self.uiwaveperiod_488blanking = int(self.DigDurationTextbox.text())
        self.uiwaveDC_488blanking = int(self.DigDCTextbox.currentText())
        if not self.DigRepeatTextbox.text():
            self.uiwaverepeat_488blanking_number = 1
        else:
            self.uiwaverepeat_488blanking_number = int(self.DigRepeatTextbox.text())
        if not self.DigGapTextbox.text():
            self.uiwavegap_488blanking = 0
        else:
            self.uiwavegap_488blanking = int(self.DigGapTextbox.text())
        
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
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        self.uiwavefrequency_blankingall = float(self.DigFreqTextbox.text())
        if not self.DigOffsetTextbox.text():
            self.uiwaveoffset_blankingall = 0
        else:
            self.uiwaveoffset_blankingall = int(self.DigOffsetTextbox.text())
        self.uiwaveperiod_blankingall = int(self.DigDurationTextbox.text())
        self.uiwaveDC_blankingall = int(self.DigDCTextbox.currentText())
        if not self.DigRepeatTextbox.text():
            self.uiwaverepeat_blankingall_number = 1
        else:
            self.uiwaverepeat_blankingall_number = int(self.DigRepeatTextbox.text())
        if not self.DigGapTextbox.text():
            self.uiwavegap_blankingall = 0
        else:
            self.uiwavegap_blankingall = int(self.DigGapTextbox.text())
        
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
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        self.uiwavefrequency_Perfusion_8 = float(self.DigFreqTextbox.text())
        if not self.DigOffsetTextbox.text():
            self.uiwaveoffset_Perfusion_8 = 0
        else:
            self.uiwaveoffset_Perfusion_8 = int(self.DigOffsetTextbox.text())
        self.uiwaveperiod_Perfusion_8 = int(self.DigDurationTextbox.text())
        self.uiwaveDC_Perfusion_8 = int(self.DigDCTextbox.currentText())
        if not self.DigRepeatTextbox.text():
            self.uiwaverepeat_Perfusion_8_number = 1
        else:
            self.uiwaverepeat_Perfusion_8_number = int(self.DigRepeatTextbox.text())
        if not self.DigGapTextbox.text():
            self.uiwavegap_Perfusion_8 = 0
        else:
            self.uiwavegap_Perfusion_8 = int(self.DigGapTextbox.toPlainText())
        
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
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        self.uiwavefrequency_Perfusion_7 = float(self.DigFreqTextbox.text())
        if not self.DigOffsetTextbox.text():
            self.uiwaveoffset_Perfusion_7 = 0
        else:
            self.uiwaveoffset_Perfusion_7 = int(self.DigOffsetTextbox.text())
        self.uiwaveperiod_Perfusion_7 = int(self.DigDurationTextbox.text())
        self.uiwaveDC_Perfusion_7 = int(self.DigDCTextbox.currentText())
        if not self.DigRepeatTextbox.text():
            self.uiwaverepeat_Perfusion_7_number = 1
        else:
            self.uiwaverepeat_Perfusion_7_number = int(self.DigRepeatTextbox.text())
        if not self.DigGapTextbox.text():
            self.uiwavegap_Perfusion_7 = 0
        else:
            self.uiwavegap_Perfusion_7 = int(self.DigGapTextbox.toPlainText())
        
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
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        self.uiwavefrequency_Perfusion_6 = float(self.DigFreqTextbox.text())
        if not self.DigOffsetTextbox.text():
            self.uiwaveoffset_Perfusion_6 = 0
        else:
            self.uiwaveoffset_Perfusion_6 = int(self.DigOffsetTextbox.text())
        self.uiwaveperiod_Perfusion_6 = int(self.DigDurationTextbox.text())
        self.uiwaveDC_Perfusion_6 = int(self.DigDCTextbox.currentText())
        if not self.DigRepeatTextbox.text():
            self.uiwaverepeat_Perfusion_6_number = 1
        else:
            self.uiwaverepeat_Perfusion_6_number = int(self.DigRepeatTextbox.text())
        if not self.DigGapTextbox.text():
            self.uiwavegap_Perfusion_6 = 0
        else:
            self.uiwavegap_Perfusion_6 = int(self.DigGapTextbox.toPlainText())
        
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
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        self.uiwavefrequency_Perfusion_2 = float(self.DigFreqTextbox.text())
        if not self.DigOffsetTextbox.text():
            self.uiwaveoffset_Perfusion_2 = 0
        else:
            self.uiwaveoffset_Perfusion_2 = int(self.DigOffsetTextbox.text())
        self.uiwaveperiod_Perfusion_2 = int(self.DigDurationTextbox.text())
        self.uiwaveDC_Perfusion_2 = int(self.DigDCTextbox.currentText())
        if not self.DigRepeatTextbox.text():
            self.uiwaverepeat_Perfusion_2_number = 1
        else:
            self.uiwaverepeat_Perfusion_2_number = int(self.DigRepeatTextbox.text())
        if not self.DigGapTextbox.text():
            self.uiwavegap_Perfusion_2 = 0
        else:
            self.uiwavegap_Perfusion_2 = int(self.DigGapTextbox.toPlainText())
        
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
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
        self.uiwavefrequency_2Pshutter = float(self.DigFreqTextbox.text())
        if not self.DigOffsetTextbox.text():
            self.uiwaveoffset_2Pshutter = 0
        else:
            self.uiwaveoffset_2Pshutter = int(self.DigOffsetTextbox.text())
        self.uiwaveperiod_2Pshutter = int(self.DigDurationTextbox.text())
        self.uiwaveDC_2Pshutter = int(self.DigDCTextbox.currentText())
        if not self.DigRepeatTextbox.text():
            self.uiwaverepeat_2Pshutter_number = 1
        else:
            self.uiwaverepeat_2Pshutter_number = int(self.DigRepeatTextbox.text())
        if not self.DigGapTextbox.text():
            self.uiwavegap_2Pshutter = 0
        else:
            self.uiwavegap_2Pshutter = int(self.DigGapTextbox.toPlainText())
        
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
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
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
                    
        s = generate_AO(self.uiDaq_sample_rate, self.uiwavefrequency_photocycle_640, self.uiwavefrequency_offset_photocycle_640, self.uiwaveperiod_photocycle_640, self.uiwaveDC_photocycle_640, self.uiwaverepeat_photocycle_640
                               , self.uiwavegap_photocycle_640, self.uiwavestartamplitude_photocycle_640, self.uiwavebaseline_photocycle_640, self.uiwavestep_photocycle_640, self.uiwavecycles_photocycle_640, self.uiwavestart_time_photocycle_640,self.uiwavecontrol_amplitude_photocycle_640)
        self.finalwave_640 = s.generate()
        return self.finalwave_640
    
    def generate_photocycle_532(self):
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
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
                    
        s = generate_AO(self.uiDaq_sample_rate, self.uiwavefrequency_photocycle_532, self.uiwavefrequency_offset_photocycle_532, self.uiwaveperiod_photocycle_532, self.uiwaveDC_photocycle_532, self.uiwaverepeat_photocycle_532
                               , self.uiwavegap_photocycle_532, self.uiwavestartamplitude_photocycle_532, self.uiwavebaseline_photocycle_532, self.uiwavestep_photocycle_532, self.uiwavecycles_photocycle_532, self.uiwavestart_time_photocycle_532,self.uiwavecontrol_amplitude_photocycle_532)
        self.finalwave_532 = s.generate()
        return self.finalwave_532
    
    def generate_photocycle_488(self):
        
        self.uiDaq_sample_rate = int(self.SamplingRateTextbox.value())
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
                    
        s = generate_AO(self.uiDaq_sample_rate, self.uiwavefrequency_photocycle_488, self.uiwavefrequency_offset_photocycle_488, self.uiwaveperiod_photocycle_488, self.uiwaveDC_photocycle_488, self.uiwaverepeat_photocycle_488
                               , self.uiwavegap_photocycle_488, self.uiwavestartamplitude_photocycle_488, self.uiwavebaseline_photocycle_488, self.uiwavestep_photocycle_488, self.uiwavecycles_photocycle_488, self.uiwavestart_time_photocycle_488,self.uiwavecontrol_amplitude_photocycle_488)
        self.finalwave_488 = s.generate()
        return self.finalwave_488
       
    def set_switch(self, name):
        #self.generate_dictionary_switch_instance[name] = 1
        if name not in self.dictionary_switch_list:
            self.dictionary_switch_list.append(name)
            print(self.dictionary_switch_list)
    def del_set_switch(self, name):
        #self.generate_dictionary_switch_instance[name] = 1
        if name in self.dictionary_switch_list:
            self.dictionary_switch_list.remove(name)
            print(self.dictionary_switch_list)
    def clear_canvas(self):
        #Back to initial state
        self.pw.clear()
        self.dictionary_switch_list =[]
        #self.Galvo_samples = self.finalwave_640 = self.finalwave_488 = self.finalwave_532=self.finalwave_patch =None
        #self.finalwave_cameratrigger=self.final_galvotrigger=self.finalwave_blankingall=self.finalwave_640blanking=self.finalwave_532blanking=self.finalwave_488blanking=self.finalwave_Perfusion_8 = None
        #self.switch_galvos=self.switch_640AO=self.switch_488AO=self.switch_532AO=self.switch_patchAO=self.switch_cameratrigger=self.switch_galvotrigger=self.switch_blankingall=self.switch_640blanking=self.switch_532blanking=self.switch_488blanking=self.switch_Perfusion_8=0        
        
    def show_all(self):

        self.switch_galvos=self.switch_galvos_contour=self.switch_640AO=self.switch_488AO=self.switch_532AO=self.switch_patchAO=self.switch_cameratrigger=self.switch_galvotrigger=self.switch_blankingall=self.switch_640blanking=self.switch_532blanking=self.switch_488blanking=self.switch_Perfusion_8=self.switch_Perfusion_7=self.switch_Perfusion_6=self.switch_Perfusion_2=self.switch_2Pshutter=0
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
            self.analog_data_container['galvosx'+'avgnum_'+str(int(self.GalvoAvgNumTextbox.value()))] = self.generate_galvos()[0, :]
            self.analog_data_container['galvosy'+'ypixels_'+str(int(self.GalvoYpixelNumTextbox.currentText()))] = self.generate_galvos()[1, :]
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
        print(self.digitalcontainer_array['Sepcification'])
                
        self.xlabelhere_all = np.arange(self.reference_length)/int(self.SamplingRateTextbox.value())
        
        self.pw.clear()
        for i in range(analogloopnum):
                                        
            if self.analogcontainer_array['Sepcification'][i] != 'galvosx'+'avgnum_'+str(int(self.GalvoAvgNumTextbox.value())) and self.analogcontainer_array['Sepcification'][i] != 'galvos_X'+'_contour': #skip the galvoX, as it is too intense
                if self.analogcontainer_array['Sepcification'][i] == 'galvosy'+'ypixels_'+str(int(self.GalvoYpixelNumTextbox.currentText())) or self.analogcontainer_array['Sepcification'][i] == 'galvos_Y'+'_contour':
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
        plt.figure()
        for i in range(analogloopnum):
            if self.analogcontainer_array['Sepcification'][i] != 'galvosx'+'avgnum_'+str(int(self.GalvoAvgNumTextbox.value())): #skip the galvoX, as it is too intense
                plt.plot(xlabelhere_all, self.analogcontainer_array['Waveform'][i])
        for i in range(digitalloopnum):
            plt.plot(xlabelhere_all, self.digitalcontainer_array['Waveform'][i])
        plt.text(0.1, 1.1, 'Time lasted:'+str(xlabelhere_all[-1])+'s', fontsize=12)
        plt.show()
        '''
        # Saving configed waveforms
        if self.textboxsavingwaveforms.isChecked():
            #temp_save_wave = np.empty((len(self.analogcontainer_array['Sepcification'])+len(self.digitalcontainer_array['Sepcification']), 1), dtype=np.object)
            ciao=[] # Variable name 'ciao' was defined by Nicolo Ceffa.

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
            np.save(os.path.join(self.savedirectory, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_'+self.saving_prefix+'_'+'Wavefroms_sr_'+ str(int(self.SamplingRateTextbox.value()))), ciao)
        
        self.readinchan = []
        
        if self.ReadChanPMTTextbox.isChecked():
            self.readinchan.append('PMT')
        if self.ReadChanVpTextbox.isChecked():
            self.readinchan.append('Vp')
        if self.ReadChanIpTextbox.isChecked():
            self.readinchan.append('Ip')       
        
        print(self.readinchan)
        
        self.GeneratedWaveformPackage = (int(self.SamplingRateTextbox.value()), self.analogcontainer_array, self.digitalcontainer_array, self.readinchan)
        self.WaveformPackage.emit(self.GeneratedWaveformPackage)
        
        try:
            self.GalvoScanInforPackage = (self.readinchan, self.repeatnum, self.PMT_data_index_array_repeated, self.averagenum, len(self.samples_1), self.ScanArrayXnum) # Emit a tuple
            self.GalvoScanInfor.emit(self.GalvoScanInforPackage)
        except:
            self.GalvoScanInfor.emit('NoGalvo') # Emit a string
        #execute(int(self.SamplingRateTextbox.currentText()), self.analogcontainer_array, self.digitalcontainer_array, self.readinchan)
        return self.analogcontainer_array, self.digitalcontainer_array, self.readinchan
    
    def execute_tread(self):
        if self.clock_source.currentText() == 'Dev1 as clock source':
            self.adcollector = execute_analog_readin_optional_digital_thread()
            self.adcollector.set_waves(int(self.SamplingRateTextbox.value()), self.analogcontainer_array, self.digitalcontainer_array, self.readinchan)
            self.adcollector.collected_data.connect(self.recive_data)
            self.adcollector.start()
#            self.adcollector.wait()
#            self.adcollector.save_as_binary(self.savedirectory)
            #self.ai_dev_scaling_coeff = self.adcollector.get_ai_dev_scaling_coeff()
        elif self.clock_source.currentText() == 'Cam as clock source' :
            self.adcollector = execute_analog_and_readin_digital_optional_camtrig_thread()
            self.adcollector.set_waves(int(self.SamplingRateTextbox.value()), self.analogcontainer_array, self.digitalcontainer_array, self.readinchan)
            self.adcollector.collected_data.connect(self.recive_data)
            self.adcollector.start()
#            self.adcollector.wait()
#            self.adcollector.save_as_binary(self.savedirectory)
            #self.ai_dev_scaling_coeff = self.adcollector.get_ai_dev_scaling_coeff()
            
#    def execute_tread_external(self, WaveformTuple, savedirectory):
#        sampling_rate_from_external, analogcontainer_array, digitalcontainer_array, readinchan = self.load_waveforms(WaveformTuple)
#        self.external_savedirectory = savedirectory
#        
#        if self.clock_source.currentText() == 'Dev1 as clock source':
#            self.adcollector = execute_analog_readin_optional_digital_thread()
#            self.adcollector.set_waves(sampling_rate_from_external, analogcontainer_array, digitalcontainer_array, readinchan)
#            self.adcollector.collected_data.connect(self.recive_data_external)
#            self.adcollector.start()
##            self.adcollector.save_as_binary(savedirectory)
#            #self.ai_dev_scaling_coeff = self.adcollector.get_ai_dev_scaling_coeff()
#        elif self.clock_source.currentText() == 'Cam as clock source' :
#            self.adcollector = execute_analog_and_readin_digital_optional_camtrig_thread()
#            self.adcollector.set_waves(sampling_rate_from_external, analogcontainer_array, digitalcontainer_array, readinchan)
#            self.adcollector.collected_data.connect(self.recive_data_external)
#            self.adcollector.start()
##            self.adcollector.save_as_binary(savedirectory)
#            #self.ai_dev_scaling_coeff = self.adcollector.get_ai_dev_scaling_coeff()
            
    def load_waveforms(self, WaveformTuple):
        self.WaveformSamplingRate = WaveformTuple[0]
        self.WaveformAnalogContainer = WaveformTuple[1]
        self.WaveformDigitalContainer = WaveformTuple[2]
        self.WaveformRecordingChannContainer = WaveformTuple[3]
        
        return self.WaveformSamplingRate, self.WaveformAnalogContainer, self.WaveformDigitalContainer, self.WaveformRecordingChannContainer
    
    def execute_digital(self):
        
        execute_digital(int(self.SamplingRateTextbox.value()), self.digitalcontainer_array)
        
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
            elif 'PMT' in self.readinchan:  # repeatnum, PMT_data_index_array, averagenum, ScanArrayXnum
                self.data_collected_0 = data_waveformreceived[0]*-1
                self.data_collected_0 = self.data_collected_0[0:len(self.data_collected_0)-1]
                
                # pmt data could come from raster scanning mode or from contour scanning mode.
                try:
                    for i in range(self.repeatnum):
                        self.PMT_image_reconstructed_array = self.data_collected_0[np.where(self.PMT_data_index_array_repeated == i+1)]
                        Dataholder_average = np.mean(self.PMT_image_reconstructed_array.reshape(self.averagenum, -1), axis=0)
                        Value_yPixels = int(len(self.samples_1)/self.ScanArrayXnum)
                        self.PMT_image_reconstructed = np.reshape(Dataholder_average, (Value_yPixels, self.ScanArrayXnum))
                        
                        # Stack the arrays into a 3d array
                        if i == 0:
                            self.PMT_image_reconstructed_stack = self.PMT_image_reconstructed
                        else:
                            self.PMT_image_reconstructed_stack = np.concatenate((self.PMT_image_reconstructed_stack, self.PMT_image_reconstructed), axis=0)
                        
                        Localimg = Image.fromarray(self.PMT_image_reconstructed) #generate an image object
                        Localimg.save(os.path.join(self.savedirectory, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_PMT_'+self.saving_prefix+'_'+str(i)+'.tif')) #save as tif
                        
                        plt.figure()
                        plt.imshow(self.PMT_image_reconstructed, cmap = plt.cm.gray)
                        plt.show()
                except:
                    np.save(os.path.join(self.savedirectory, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_PMT_'+self.saving_prefix+'_'+'contourscanning'), self.data_collected_0)
                
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
                
                try:
                    for i in range(self.repeatnum):
                        self.PMT_image_reconstructed_array = self.data_collected_0[np.where(self.PMT_data_index_array_repeated == i+1)]
                        Dataholder_average = np.mean(self.PMT_image_reconstructed_array.reshape(self.averagenum, -1), axis=0)
                        Value_yPixels = int(len(self.samples_1)/self.ScanArrayXnum)
                        self.PMT_image_reconstructed = np.reshape(Dataholder_average, (Value_yPixels, self.ScanArrayXnum))
                        
                        # Stack the arrays into a 3d array
                        if i == 0:
                            self.PMT_image_reconstructed_stack = self.PMT_image_reconstructed
                        else:
                            self.PMT_image_reconstructed_stack = np.concatenate((self.PMT_image_reconstructed_stack, self.PMT_image_reconstructed), axis=0)
                        
                        Localimg = Image.fromarray(self.PMT_image_reconstructed) #generate an image object
                        Localimg.save(os.path.join(self.savedirectory, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_PMT_'+self.saving_prefix+'_'+str(i)+'.tif')) #save as tif
                        
                        plt.figure()
                        plt.imshow(self.PMT_image_reconstructed, cmap = plt.cm.gray)
                        plt.show()
                except:
                    np.save(os.path.join(self.savedirectory, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_PMT_'+self.saving_prefix+'_'+'contourscanning'), self.data_collected_0)
                    
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
                    
#    def recive_data_external(self, data_waveformreceived):
#        
#        self.channel_number = len(data_waveformreceived)
#        if self.channel_number == 1:            
#            if 'Vp' in self.readinchan:
#                pass
#            elif 'Ip' in self.readinchan:
#                pass
#            elif 'PMT' in self.readinchan:  # repeatnum, PMT_data_index_array, averagenum, ScanArrayXnum
#                self.data_collected_0 = data_waveformreceived[0]
#                for i in range(self.repeatnum):
#                    self.PMT_image_reconstructed_array = self.data_collected_0[np.where(self.PMT_data_index_array == i+1)]
#                    Dataholder_average = np.mean(self.PMT_image_reconstructed_array.reshape(self.averagenum, -1), axis=0)
#                    Value_yPixels = int(len(self.samples_1)/self.ScanArrayXnum)
#                    self.PMT_image_reconstructed = np.reshape(Dataholder_average, (Value_yPixels, self.ScanArrayXnum))
#                    
#                    # Stack the arrays into a 3d array
#                    if i == 0:
#                        self.PMT_image_reconstructed_stack = self.PMT_image_reconstructed
#                    else:
#                        self.PMT_image_reconstructed_stack = np.stack(self.PMT_image_reconstructed_stack, self.PMT_image_reconstructed, axis=0)
#                    
#                    Localimg = Image.fromarray(self.PMT_image_reconstructed) #generate an image object
#                    Localimg.save(os.path.join(self.external_savedirectory, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_PMT_'+str(i)+'.tif')) #save as tif
#                    
#                    plt.figure()
#                    plt.imshow(self.PMT_image_reconstructed, cmap = plt.cm.gray)
#                    plt.show()
#                
#        elif self.channel_number == 2: 
#            if 'PMT' not in self.readinchan:
#                pass
#            elif 'PMT' in self.readinchan:
#                self.data_collected_0 = data_waveformreceived[0]
#                for i in range(self.repeatnum):
#                    self.PMT_image_reconstructed_array = self.data_collected_0[np.where(self.PMT_data_index_array == i+1)]
#                    Dataholder_average = np.mean(self.PMT_image_reconstructed_array.reshape(self.averagenum, -1), axis=0)
#                    Value_yPixels = int(len(self.samples_1)/self.ScanArrayXnum)
#                    self.PMT_image_reconstructed = np.reshape(Dataholder_average, (Value_yPixels, self.ScanArrayXnum))
#                    
#                    # Stack the arrays into a 3d array
#                    if i == 0:
#                        self.PMT_image_reconstructed_stack = self.PMT_image_reconstructed
#                    else:
#                        self.PMT_image_reconstructed_stack = np.stack(self.PMT_image_reconstructed_stack, self.PMT_image_reconstructed, axis=0)
#                    
#                    Localimg = Image.fromarray(self.PMT_image_reconstructed) #generate an image object
#                    Localimg.save(os.path.join(self.external_savedirectory, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_PMT_'+str(self.prefixtextbox.text())+'_'+str(i)+'.tif')) #save as tif
#                    
#                    plt.figure()
#                    plt.imshow(self.PMT_image_reconstructed, cmap = plt.cm.gray)
#                    plt.show()
#                    
            
    def startProgressBar(self):
        self.DaqProgressBar_thread = DaqProgressBar()
        self.TotalTimeProgressBar = round((self.reference_length)/int(self.SamplingRateTextbox.value()), 6)
        self.DaqProgressBar_thread.setlength(self.TotalTimeProgressBar)
        self.DaqProgressBar_thread.change_value.connect(self.setProgressVal)
        self.DaqProgressBar_thread.start()
 
    def setProgressVal(self, val):
        self.waveform_progressbar.setValue(val)
        
    def _open_file_dialog(self):
        self.saving_prefix = str(self.prefixtextbox.text())        
        self.savedirectory = str(QtWidgets.QFileDialog.getExistingDirectory())
        self.savedirectorytextbox.setText(self.savedirectory)

    def stopMeasurement_daqer(self):
        """Stop """
        self.adcollector.aboutToQuitHandler()
        
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        mainwin = WaveformGenerator()
        mainwin.show()
        app.exec_()
    run_app()