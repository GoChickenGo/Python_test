# -*- coding: utf-8 -*-
"""
Created on Mon Jul  1 19:52:48 2019

@author: Meng
"""
from __future__ import division
import sys
import numpy as np
from matplotlib import pyplot as plt
from IPython import get_ipython
from matplotlib.ticker import FormatStrFormatter
import wavegenerator
from generalDaqer import execute_analog_readin_optional_digital, execute_digital
from generalDaqerThread import execute_analog_readin_optional_digital_thread
from configuration import Configuration
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QWidget,QLineEdit, QLabel, QGridLayout, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox, QPlainTextEdit, QGroupBox, QTabWidget, QCheckBox
from adfunctiongenerator import generate_AO_for640, generate_AO_for488, generate_DO_forcameratrigger, generate_DO_for640blanking, generate_AO_for532, generate_AO_forpatch, generate_DO_forblankingall, generate_DO_for532blanking, generate_DO_for488blanking, generate_DO_forPerfusion
import pyqtgraph as pg
from pyqtgraph import PlotDataItem, TextItem

class adgenerator(QWidget, QThread):
    measurement = pyqtSignal(object, object, list, int)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        get_ipython().run_line_magic('matplotlib', 'qt') # before start, set spyder back to inline
        #----------------------------------------------------------------------
        #----------------------------------GUI---------------------------------
        #----------------------------------------------------------------------
        #self.setMinimumSize(300,120)
        self.setWindowTitle("Buon appetito!")
        
        self.Galvo_samples = self.finalwave_640 = self.finalwave_488 = self.finalwave_532=self.finalwave_patch =None
        self.finalwave_cameratrigger=self.final_galvotrigger=self.finalwave_blankingall=self.finalwave_640blanking=self.finalwave_532blanking=self.finalwave_488blanking=self.finalwave_Perfusion_1 = None
        
        AnalogContainer = QGroupBox("Analog signals")
        self.AnalogLayout = QGridLayout() #self.AnalogLayout manager
        
        
        self.button_execute = QPushButton('EXECUTE AD', self)
        self.AnalogLayout.addWidget(self.button_execute, 3, 3)
        
        self.button_execute.clicked.connect(self.execute_tread)    
        
        self.textbox2A = QComboBox()
        self.textbox2A.addItems(['galvos', '640 AO','532 AO', '488 AO', 'V-patch'])
        self.AnalogLayout.addWidget(self.textbox2A, 3, 0)
        
        self.button2 = QPushButton('Add', self)
        self.AnalogLayout.addWidget(self.button2, 3, 1)
        
        self.button_del_analog = QPushButton('Delete', self)
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
        # Add tabs
        self.wavetabs.addTab(self.wavetab1,"Block")
        self.wavetabs.addTab(self.wavetab2,"Ramp")
        self.wavetabs.addTab(self.wavetab3,"Matlab")
        self.wavetabs.addTab(self.wavetab4,"Galvo")
        
        #------------------------------------------------------------------------------------------------------------------
        #----------------------------------------------------------General settings-------------------------------------------------
        #------------------------------------------------------------------------------------------------------------------       
        ReadContainer = QGroupBox("General settings")
        self.ReadLayout = QGridLayout() #self.AnalogLayout manager

        self.textboxBB = QComboBox()
        self.textboxBB.addItems(['galvos', '640AO', '488AO', '532AO', 'patchAO','cameratrigger', 'blankingall', '640blanking','532blanking','488blanking', 'Perfusion_1'])
        self.ReadLayout.addWidget(self.textboxBB, 0, 1)
        self.ReadLayout.addWidget(QLabel("Reference waveform:"), 0, 0)

        self.button_all = QPushButton('Show waveforms', self)
        self.ReadLayout.addWidget(self.button_all, 0, 4)
        self.button_all.clicked.connect(self.show_all)

        self.button_stop_waveforms = QPushButton('Stop', self)
        self.ReadLayout.addWidget(self.button_stop_waveforms, 0, 5)
        self.button_stop_waveforms.clicked.connect(self.stopMeasurement_daqer)        
                
        self.button_clear_canvas = QPushButton('Clear canvas', self)
        self.ReadLayout.addWidget(self.button_clear_canvas, 1, 5)
        
        self.button_clear_canvas.clicked.connect(self.clear_canvas)  
        
        self.textboxAA = QComboBox()
        self.textboxAA.addItems(['500000', '50000'])
        self.ReadLayout.addWidget(self.textboxAA, 0, 3)
        self.ReadLayout.addWidget(QLabel("Sampling rate for all:"), 0, 2)
        
        # Read-in channels
        self.textbox111A = QCheckBox("PMT")
        self.ReadLayout.addWidget(self.textbox111A, 1, 1)     

        self.textbox222A = QCheckBox("Vp")
        self.ReadLayout.addWidget(self.textbox222A, 1, 2)   
        
        self.textbox333A = QCheckBox("Ip")
        self.ReadLayout.addWidget(self.textbox333A, 1, 3)
        
        self.ReadLayout.addWidget(QLabel("Recording channels: "), 1, 0)
        
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
        self.wavetablayout.addWidget(QLabel("Period (ms, 1 cycle):"), 0, 2)   
        
        self.textbox2E = QLineEdit(self)
        self.textbox2E.setPlaceholderText('1')
        self.wavetablayout.addWidget(self.textbox2E, 1, 3)
        self.wavetablayout.addWidget(QLabel("Repeat:"), 1, 2) 
        
        self.wavetablayout.addWidget(QLabel("DC (%):"), 0, 4)
        self.textbox2F = QComboBox()
        self.textbox2F.addItems(['50','10'])
        self.wavetablayout.addWidget(self.textbox2F, 0, 5)
        
        self.textbox2G = QLineEdit(self)
        self.textbox2G.setPlaceholderText('0')
        self.wavetablayout.addWidget(self.textbox2G, 1, 5)
        self.wavetablayout.addWidget(QLabel("Gap between repeat (samples):"), 1, 4)
        
        self.wavetablayout.addWidget(QLabel("Starting amplitude (V):"), 2, 0)
        self.textbox2H = QComboBox()
        self.textbox2H.addItems(['5','1'])
        self.wavetablayout.addWidget(self.textbox2H, 2, 1)        

        self.textbox2I = QLineEdit(self)
        self.textbox2I.setPlaceholderText('0')
        self.wavetablayout.addWidget(self.textbox2I, 3, 1)
        self.wavetablayout.addWidget(QLabel("Baseline (V):"), 3, 0)

        self.wavetablayout.addWidget(QLabel("Step (V):"), 2, 2)
        self.textbox2J = QComboBox()
        self.textbox2J.addItems(['0','1', '2'])
        self.wavetablayout.addWidget(self.textbox2J, 2, 3)

        self.wavetablayout.addWidget(QLabel("Cycles:"), 3, 2)
        self.textbox2K = QComboBox()
        self.textbox2K.addItems(['1','2', '3'])
        self.wavetablayout.addWidget(self.textbox2K, 3, 3)
                
        self.wavetab1.setLayout(self.wavetablayout)
        
        #----------------------------------------------Tab for galvo------------------------------------------------
        #----------------------------------------------Galvo scanning----------------------------------------------
        
        self.galvotablayout= QGridLayout()
        
        self.textbox1B = QComboBox()
        self.textbox1B.addItems(['-5','-3','-1'])
        self.galvotablayout.addWidget(self.textbox1B, 0, 1)
        self.galvotablayout.addWidget(QLabel("voltXMin"), 0, 0)

        self.textbox1C = QComboBox()
        self.textbox1C.addItems(['5','3','1'])
        self.galvotablayout.addWidget(self.textbox1C, 1, 1)
        self.galvotablayout.addWidget(QLabel("voltXMax"), 1, 0)

        self.textbox1D = QComboBox()
        self.textbox1D.addItems(['-5','-3','-1'])
        self.galvotablayout.addWidget(self.textbox1D, 0, 3)
        self.galvotablayout.addWidget(QLabel("voltYMin"), 0, 2)

        self.textbox1E = QComboBox()
        self.textbox1E.addItems(['5','3','1'])
        self.galvotablayout.addWidget(self.textbox1E, 1, 3)
        self.galvotablayout.addWidget(QLabel("voltYMax"), 1, 2)

        self.textbox1F = QComboBox()
        self.textbox1F.addItems(['500','256'])
        self.galvotablayout.addWidget(self.textbox1F, 0, 5)
        self.galvotablayout.addWidget(QLabel("X pixel number"), 0, 4)

        self.textbox1G = QComboBox()
        self.textbox1G.addItems(['500','256'])
        self.galvotablayout.addWidget(self.textbox1G, 1, 5)
        self.galvotablayout.addWidget(QLabel("Y pixel number"), 1, 4)
        
        self.textbox1I = QLineEdit(self)
        self.textbox1I.setPlaceholderText('0')
        self.galvotablayout.addWidget(self.textbox1I, 2, 1)
        self.galvotablayout.addWidget(QLabel("Offset (ms):"), 2, 0)
        
        self.textbox1J = QLineEdit(self)
        self.textbox1J.setPlaceholderText('0')
        self.galvotablayout.addWidget(self.textbox1J, 2, 3)
        self.galvotablayout.addWidget(QLabel("Gap between scans:"), 2, 2)       
        
        self.textbox1H = QComboBox()
        self.textbox1H.addItems(['5','2','3','8','1'])
        self.galvotablayout.addWidget(self.textbox1H, 2, 5)
        self.galvotablayout.addWidget(QLabel("average over:"), 2, 4)
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
                                  'Perfusion_1'])
        self.DigitalLayout.addWidget(self.textbox3A, 0, 0)
        
        self.button3 = QPushButton('Add', self)
        self.DigitalLayout.addWidget(self.button3, 0, 1)
        self.button3.clicked.connect(self.chosen_wave_digital)
        #---------------------------------------------------------------------------------------------------------------------------        
        self.button_execute_digital = QPushButton('EXECUTE DIGITAL', self)
        self.DigitalLayout.addWidget(self.button_execute_digital, 0, 3)
        
        self.button_del_digital = QPushButton('Delete', self)
        self.DigitalLayout.addWidget(self.button_del_digital, 0, 2)
        
        self.button_execute_digital.clicked.connect(self.execute_digital)
        self.button_del_digital.clicked.connect(self.del_chosen_wave_digital)
        # ------------------------------------------------------Wave settings------------------------------------------
        self.digitalwavetablayout= QGridLayout()
        
        self.digitalwavetabs = QTabWidget()
        self.digitalwavetab1 = QWidget()
        self.digitalwavetab2 = QWidget()
        self.digitalwavetab3 = QWidget()

        # Add tabs
        self.digitalwavetabs.addTab(self.digitalwavetab1,"Block")
        self.digitalwavetabs.addTab(self.digitalwavetab2,"Ramp")
        self.digitalwavetabs.addTab(self.digitalwavetab3,"Matlab")

        
        self.textbox11B = QLineEdit(self)
        self.digitalwavetablayout.addWidget(self.textbox11B, 0, 1)
        self.digitalwavetablayout.addWidget(QLabel("Frequency in period:"), 0, 0)

        self.textbox11C = QLineEdit(self)
        self.textbox11C.setPlaceholderText('0')
        self.digitalwavetablayout.addWidget(self.textbox11C, 1, 1)
        self.digitalwavetablayout.addWidget(QLabel("Offset (ms):"), 1, 0)
        
        self.textbox11D = QLineEdit(self)
        self.digitalwavetablayout.addWidget(self.textbox11D, 0, 3)
        self.digitalwavetablayout.addWidget(QLabel("Period (ms):"), 0, 2)   
        
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
        #------------------------------------------------------------------------------------------------------------------
        #----------------------------------------------------------Data win-------------------------------------------------
        #------------------------------------------------------------------------------------------------------------------  
        self.pw_data = pg.PlotWidget(title='Data')
        self.pw_data.setLabel('bottom', 'Time', units='s')
        #self.pw_data.setLabel('left', 'Value', units='V')
        #--------------Adding to master----------------------------------------
        master = QGridLayout()
        master.addWidget(AnalogContainer, 1, 0)
        master.addWidget(DigitalContainer, 2, 0)
        master.addWidget(ReadContainer, 0, 0)
        master.addWidget(self.pw, 3, 0)
        master.addWidget(self.pw_data, 4, 0)
        self.setLayout(master)

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
            elif self.textbox2A.currentText() == 'galvos':
                if self.Galvo_samples is not None:
                    self.pw.removeItem(self.PlotDataItem_galvos) 
                    self.pw.removeItem(self.textitem_galvos)
                self.generate_galvos()
                self.generate_galvos_graphy()
                self.set_switch('galvos')
            
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
        elif self.textbox3A.currentText() == 'Perfusion_1':
            if self.finalwave_Perfusion_1 is not None:
                self.pw.removeItem(self.PlotDataItem_Perfusion_1) 
                self.pw.removeItem(self.textitem_Perfusion_1)
            self.generate_Perfusion_1()
            self.generate_Perfusion_1_graphy()
            self.set_switch('Perfusion_1')     

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
        elif self.textbox3A.currentText() == 'Perfusion_1':
            self.pw.removeItem(self.PlotDataItem_Perfusion_1)   
            self.pw.removeItem(self.textitem_Perfusion_1)
            self.finalwave_Perfusion_1 = None
            self.del_set_switch('Perfusion_1')                           
                                     
    def generate_galvos(self):
        
        self.Daq_sample_rate = int(self.textboxAA.currentText())
        
        #Scanning settings
        #if int(self.textbox1A.currentText()) == 1:
        Value_voltXMin = int(self.textbox1B.currentText())
        Value_voltXMax = int(self.textbox1C.currentText())
        Value_voltYMin = int(self.textbox1D.currentText())
        Value_voltYMax = int(self.textbox1E.currentText())
        Value_xPixels = int(self.textbox1F.currentText())
        Value_yPixels = int(self.textbox1G.currentText())
        self.averagenum =int(self.textbox1H.currentText())
        
        if not self.textbox1I.text():
            self.Galvo_samples_offset = 1
            self.offsetsamples_galvo = []

        else:
            self.Galvo_samples_offset = int(self.textbox1I.text())
            
            self.offsetsamples_number_galvo = int((self.Galvo_samples_offset/1000)*self.Daq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
            self.offsetsamples_galvo = np.zeros(self.offsetsamples_number_galvo) # Be default offsetsamples_number is an integer.    
        #Generate galvo samples            
        self.samples_1, self.samples_2= wavegenerator.waveRecPic(sampleRate = self.Daq_sample_rate, imAngle = 0, voltXMin = Value_voltXMin, voltXMax = Value_voltXMax, 
                         voltYMin = Value_voltYMin, voltYMax = Value_voltYMax, xPixels = Value_xPixels, yPixels = Value_yPixels, 
                         sawtooth = True)
        #ScanArrayX = wavegenerator.xValuesSingleSawtooth(sampleRate = Daq_sample_rate, voltXMin = Value_voltXMin, voltXMax = Value_voltXMax, xPixels = Value_xPixels, sawtooth = True)
        #Totalscansamples = len(self.samples_1)*self.averagenum # Calculate number of samples to feed to scanner, by default it's one frame 
        self.ScanArrayXnum = int (len(self.samples_1)/Value_yPixels) # number of samples of each individual line of x scanning
        
        #print(self.Digital_container_feeder[:, 0])
        
        self.repeated_samples_1 = np.tile(self.samples_1, self.averagenum)
        self.repeated_samples_2_yaxis = np.tile(self.samples_2, self.averagenum)

        self.repeated_samples_1 = np.append(self.offsetsamples_galvo, self.repeated_samples_1)
        self.repeated_samples_2_yaxis = np.append(self.offsetsamples_galvo, self.repeated_samples_2_yaxis)
        
        self.Galvo_samples = np.vstack((self.repeated_samples_1,self.repeated_samples_2_yaxis))
        
        return self.Galvo_samples
            
    def generate_galvos_graphy(self):

        self.xlabelhere_galvos = np.arange(len(self.repeated_samples_2_yaxis))/self.Daq_sample_rate
        self.PlotDataItem_galvos = PlotDataItem(self.xlabelhere_galvos, self.repeated_samples_2_yaxis)
        self.PlotDataItem_galvos.setPen('w')
        self.pw.addItem(self.PlotDataItem_galvos)
        self.textitem_galvos = pg.TextItem(text='galvos', color=('w'), anchor=(1, 1))
        self.textitem_galvos.setPos(0, 5)
        self.pw.addItem(self.textitem_galvos)

            
    def generate_galvotrigger(self):
        self.Daq_sample_rate = int(self.textboxAA.currentText())
        #Scanning settings
        #if int(self.textbox1A.currentText()) == 1:
        Value_voltXMin = int(self.textbox1B.currentText())
        Value_voltXMax = int(self.textbox1C.currentText())
        Value_voltYMin = int(self.textbox1D.currentText())
        Value_voltYMax = int(self.textbox1E.currentText())
        Value_xPixels = int(self.textbox1F.currentText())
        Value_yPixels = int(self.textbox1G.currentText())
        self.averagenum =int(self.textbox1H.currentText())
        
        if not self.textbox1I.text():
            self.Galvo_samples_offset = 1
            self.offsetsamples_galvo = []

        else:
            self.Galvo_samples_offset = int(self.textbox1I.text())
            
            self.offsetsamples_number_galvo = int((self.Galvo_samples_offset/1000)*self.Daq_sample_rate) # By default one 0 is added so that we have a rising edge at the beginning.
            self.offsetsamples_galvo = np.zeros(self.offsetsamples_number_galvo) # Be default offsetsamples_number is an integer.    
        #Generate galvo samples            
        self.samples_1, self.samples_2= wavegenerator.waveRecPic(sampleRate = self.Daq_sample_rate, imAngle = 0, voltXMin = Value_voltXMin, voltXMax = Value_voltXMax, 
                         voltYMin = Value_voltYMin, voltYMax = Value_voltYMax, xPixels = Value_xPixels, yPixels = Value_yPixels, 
                         sawtooth = True)
        self.ScanArrayXnum = int (len(self.samples_1)/Value_yPixels) # number of samples of each individual line of x scanning
        
        #print(self.Digital_container_feeder[:, 0])
        
        self.repeated_samples_1 = np.tile(self.samples_1, self.averagenum)
        self.repeated_samples_2_yaxis = np.tile(self.samples_2, self.averagenum)

        self.repeated_samples_1 = np.append(self.offsetsamples_galvo, self.repeated_samples_1)
        self.repeated_samples_2_yaxis = np.append(self.offsetsamples_galvo, self.repeated_samples_2_yaxis)
   
        samplenumber_oneframe = len(self.samples_1)
        
        self.true_sample_num_singleperiod_galvotrigger = round((20/1000)*self.Daq_sample_rate) # Default the trigger lasts for 20 ms.
        self.false_sample_num_singleperiod_galvotrigger = samplenumber_oneframe - self.true_sample_num_singleperiod_galvotrigger
        
        self.true_sample_singleperiod_galvotrigger = np.ones(self.true_sample_num_singleperiod_galvotrigger, dtype=bool)
        self.true_sample_singleperiod_galvotrigger[0] = False  # first one False to give a rise.
        
        self.sample_singleperiod_galvotrigger = np.append(self.true_sample_singleperiod_galvotrigger, np.zeros(self.false_sample_num_singleperiod_galvotrigger, dtype=bool))
        
        self.sample_repeatedperiod_galvotrigger = np.tile(self.sample_singleperiod_galvotrigger, self.averagenum)
        
        self.offset_galvotrigger = np.array(self.offsetsamples_galvo, dtype=bool)
        
        self.final_galvotrigger = np.append(self.offset_galvotrigger, self.sample_repeatedperiod_galvotrigger)
        return self.final_galvotrigger
        
    def generate_galvotrigger_graphy(self):
        self.xlabelhere_galvos = np.arange(len(self.repeated_samples_2_yaxis))/self.Daq_sample_rate
        self.final_galvotrigger_forgraphy = self.final_galvotrigger.astype(int)
        self.PlotDataItem_galvotrigger = PlotDataItem(self.xlabelhere_galvos, self.final_galvotrigger_forgraphy)
        self.PlotDataItem_galvotrigger.setPen(100,100,200)
        self.pw.addItem(self.PlotDataItem_galvotrigger)
        
        self.textitem_galvotrigger = pg.TextItem(text='galvotrigger', color=(100,100,200), anchor=(1, 1))
        self.textitem_galvotrigger.setPos(0, -5)
        self.pw.addItem(self.textitem_galvotrigger)

        
    def generate_640AO(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.currentText())
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
        self.uiwavestartamplitude_2 = float(self.textbox2H.currentText())
        if not self.textbox2I.text():
            self.uiwavebaseline_2 = 0
        else:
            self.uiwavebaseline_2 = float(self.textbox2I.text())
        self.uiwavestep_2 = int(self.textbox2J.currentText())
        self.uiwavecycles_2 = int(self.textbox2K.currentText())   
        
            
        s = generate_AO_for640(self.uiDaq_sample_rate, self.uiwavefrequency_2, self.uiwaveoffset_2, self.uiwaveperiod_2, self.uiwaveDC_2
                               , self.uiwaverepeat_2, self.uiwavegap_2, self.uiwavestartamplitude_2, self.uiwavebaseline_2, self.uiwavestep_2, self.uiwavecycles_2)
        self.finalwave_640 = s.generate()
        return self.finalwave_640
            
    def generate_640AO_graphy(self):            
        xlabelhere_640 = np.arange(len(self.finalwave_640))/self.uiDaq_sample_rate
        #plt.plot(xlabelhere_galvo, samples_1)
        self.PlotDataItem_640AO = PlotDataItem(xlabelhere_640, self.finalwave_640)
        self.PlotDataItem_640AO.setPen('r')
        self.pw.addItem(self.PlotDataItem_640AO)
        
        self.textitem_640AO = pg.TextItem(text='640 AO', color=('r'), anchor=(1, 1))
        self.textitem_640AO.setPos(0, 4)
        self.pw.addItem(self.textitem_640AO)
           

    def generate_488AO(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.currentText())
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
        self.uiwavestartamplitude_488AO = float(self.textbox2H.currentText())
        if not self.textbox2I.text():
            self.uiwavebaseline_488AO = 0
        else:
            self.uiwavebaseline_488AO = float(self.textbox2I.text())
        self.uiwavestep_488AO = int(self.textbox2J.currentText())
        self.uiwavecycles_488AO = int(self.textbox2K.currentText())   
                    
        s = generate_AO_for488(self.uiDaq_sample_rate, self.uiwavefrequency_488AO, self.uiwaveoffset_488AO, self.uiwaveperiod_488AO, self.uiwaveDC_488AO
                               , self.uiwaverepeat_488AO, self.uiwavegap_488AO, self.uiwavestartamplitude_488AO, self.uiwavebaseline_488AO, self.uiwavestep_488AO, self.uiwavecycles_488AO)
        self.finalwave_488 = s.generate()
        return self.finalwave_488
            
    def generate_488AO_graphy(self):
        xlabelhere_488 = np.arange(len(self.finalwave_488))/self.uiDaq_sample_rate
        #plt.plot(xlabelhere_galvo, samples_1)
        self.PlotDataItem_488AO = PlotDataItem(xlabelhere_488, self.finalwave_488)
        self.PlotDataItem_488AO.setPen('b')
        self.pw.addItem(self.PlotDataItem_488AO)
        
        self.textitem_488AO = pg.TextItem(text='488 AO', color=('b'), anchor=(1, 1))
        self.textitem_488AO.setPos(0, 2)
        self.pw.addItem(self.textitem_488AO)

        
    def generate_532AO(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.currentText())
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
        self.uiwavestartamplitude_532AO = float(self.textbox2H.currentText())
        if not self.textbox2I.text():
            self.uiwavebaseline_532AO = 0
        else:
            self.uiwavebaseline_532AO = float(self.textbox2I.text())
        self.uiwavestep_532AO = int(self.textbox2J.currentText())
        self.uiwavecycles_532AO = int(self.textbox2K.currentText())   
        
        #if int(self.textbox4A.currentText()) == 1:
            
        s = generate_AO_for532(self.uiDaq_sample_rate, self.uiwavefrequency_532AO, self.uiwaveoffset_532AO, self.uiwaveperiod_532AO, self.uiwaveDC_532AO
                               , self.uiwaverepeat_532AO, self.uiwavegap_532AO, self.uiwavestartamplitude_532AO, self.uiwavebaseline_532AO, self.uiwavestep_532AO, self.uiwavecycles_532AO)
        self.finalwave_532 = s.generate()
        return self.finalwave_532
            
    def generate_532AO_graphy(self):
        xlabelhere_532 = np.arange(len(self.finalwave_532))/self.uiDaq_sample_rate
        self.PlotDataItem_532AO = PlotDataItem(xlabelhere_532, self.finalwave_532)
        self.PlotDataItem_532AO.setPen('g')
        self.pw.addItem(self.PlotDataItem_532AO)
        
        self.textitem_532AO = pg.TextItem(text='532 AO', color=('g'), anchor=(1, 1))
        self.textitem_532AO.setPos(0, 3)
        self.pw.addItem(self.textitem_532AO)
        
    def generate_patchAO(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.currentText())
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
        self.uiwavestartamplitude_patchAO = float(self.textbox2H.currentText())
        if not self.textbox2I.text():
            self.uiwavebaseline_patchAO = 0
        else:
            self.uiwavebaseline_patchAO = float(self.textbox2I.text())
        self.uiwavestep_patchAO = int(self.textbox2J.currentText())
        self.uiwavecycles_patchAO = int(self.textbox2K.currentText())   
        
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
        
        self.textitem_patch = pg.TextItem(text='patch '+str(self.uiwavefrequency_patchAO)+'hz', color=(100, 100, 0), anchor=(1, 1))
        self.textitem_patch.setPos(0, 1)
        self.pw.addItem(self.textitem_patch)


    def generate_cameratrigger(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.currentText())
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
        self.pw.addItem(self.PlotDataItem_cameratrigger)
        
        self.textitem_cameratrigger = pg.TextItem(text='cameratrigger '+str(self.uiwavefrequency_cameratrigger)+'hz', color=('c'), anchor=(1, 1))
        self.textitem_cameratrigger.setPos(0, 0)
        self.pw.addItem(self.textitem_cameratrigger)
    
            
    def generate_640blanking(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.currentText())
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
        
        self.uiDaq_sample_rate = int(self.textboxAA.currentText())
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
        
        self.uiDaq_sample_rate = int(self.textboxAA.currentText())
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
        
        self.uiDaq_sample_rate = int(self.textboxAA.currentText())
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
        
    def generate_Perfusion_1(self):
        
        self.uiDaq_sample_rate = int(self.textboxAA.currentText())
        self.uiwavefrequency_Perfusion_1 = float(self.textbox11B.text())
        if not self.textbox11C.text():
            self.uiwaveoffset_Perfusion_1 = 0
        else:
            self.uiwaveoffset_Perfusion_1 = int(self.textbox11C.text())
        self.uiwaveperiod_Perfusion_1 = int(self.textbox11D.text())
        self.uiwaveDC_Perfusion_1 = int(self.textbox11F.currentText())
        if not self.textbox11E.text():
            self.uiwaverepeat_Perfusion_1_number = 1
        else:
            self.uiwaverepeat_Perfusion_1_number = int(self.textbox11E.text())
        if not self.textbox11G.text():
            self.uiwavegap_Perfusion_1 = 0
        else:
            self.uiwavegap_Perfusion_1 = int(self.textbox11G.toPlainText())
        
        #if int(self.textbox66A.currentText()) == 1:
            
        Perfusion_1 = generate_DO_forPerfusion(self.uiDaq_sample_rate, self.uiwavefrequency_Perfusion_1, self.uiwaveoffset_Perfusion_1,
                                                     self.uiwaveperiod_Perfusion_1, self.uiwaveDC_Perfusion_1, self.uiwaverepeat_Perfusion_1_number, self.uiwavegap_Perfusion_1)
        self.finalwave_Perfusion_1 = Perfusion_1.generate()
        return self.finalwave_Perfusion_1
            
    def generate_Perfusion_1_graphy(self):    

        xlabelhere_Perfusion_1 = np.arange(len(self.finalwave_Perfusion_1))/self.uiDaq_sample_rate
        self.final_Perfusion_1_forgraphy = self.finalwave_Perfusion_1.astype(int)
        self.PlotDataItem_Perfusion_1 = PlotDataItem(xlabelhere_Perfusion_1, self.final_Perfusion_1_forgraphy)
        self.PlotDataItem_Perfusion_1.setPen(102,0,51)
        self.pw.addItem(self.PlotDataItem_Perfusion_1)
        
        self.textitem_Perfusion_1 = pg.TextItem(text='Perfusion_1', color=(102,0,51), anchor=(1, 1))
        self.textitem_Perfusion_1.setPos(0, -6)
        self.pw.addItem(self.textitem_Perfusion_1)
        
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
        #self.finalwave_cameratrigger=self.final_galvotrigger=self.finalwave_blankingall=self.finalwave_640blanking=self.finalwave_532blanking=self.finalwave_488blanking=self.finalwave_Perfusion_1 = None
        #self.switch_galvos=self.switch_640AO=self.switch_488AO=self.switch_532AO=self.switch_patchAO=self.switch_cameratrigger=self.switch_galvotrigger=self.switch_blankingall=self.switch_640blanking=self.switch_532blanking=self.switch_488blanking=self.switch_Perfusion_1=0        
        
    def show_all(self):

        self.switch_galvos=self.switch_640AO=self.switch_488AO=self.switch_532AO=self.switch_patchAO=self.switch_cameratrigger=self.switch_galvotrigger=self.switch_blankingall=self.switch_640blanking=self.switch_532blanking=self.switch_488blanking=self.switch_Perfusion_1=0
        color_dictionary = {'galvos':[255,255,255],
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
                              'Perfusion_1':[102,0,51]
                            }
        # Use dictionary to execute functions: https://stackoverflow.com/questions/9168340/using-a-dictionary-to-select-function-to-execute/9168387#9168387
        dictionary_analog = {'galvos':[self.switch_galvos,self.Galvo_samples],
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
                              'Perfusion_1':[self.switch_Perfusion_1, self.finalwave_Perfusion_1]
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
        
        if self.textboxBB.currentText() == 'galvos': # in case of using galvos as reference wave
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
            self.analog_data_container['galvosx'+'avgnum_'+str(int(self.textbox1H.currentText()))] = self.generate_galvos()[0, :]
            self.analog_data_container['galvosy'+'ypixels_'+str(int(self.textbox1G.currentText()))] = self.generate_galvos()[1, :]
            del self.analog_data_container['galvos']
        
        # reform all waves according to the length of reference wave
        for key in self.analog_data_container:
            if len(self.analog_data_container[key]) >= self.reference_length:
                self.analog_data_container[key] = self.analog_data_container[key][0:self.reference_length]
            else:
                append_zeros = np.zeros(self.reference_length-len(self.analog_data_container[key]))
                self.analog_data_container[key] = np.append(self.analog_data_container[key], append_zeros)
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
            else:
                append_zeros = np.zeros(self.reference_length-len(self.digital_data_container[key]))
                self.digital_data_container[key] = np.append(self.digital_data_container[key], append_zeros)
            #print(len(self.digital_data_container[key]))
        self.digitalcontainer_array = np.zeros(len(self.digital_data_container), dtype =tp_digital)
        digitalloopnum = 0
        for key in self.digital_data_container:
            self.digitalcontainer_array[digitalloopnum] = np.array([(self.digital_data_container[key], key)], dtype =tp_digital)
            digitalloopnum = digitalloopnum+ 1
        print(self.digitalcontainer_array['Sepcification'])
                
        self.xlabelhere_all = np.arange(self.reference_length)/int(self.textboxAA.currentText())
        
        self.pw.clear()
        for i in range(analogloopnum):
                                        
            if self.analogcontainer_array['Sepcification'][i] != 'galvosx'+'avgnum_'+str(int(self.textbox1H.currentText())): #skip the galvoX, as it is too intense
                if self.analogcontainer_array['Sepcification'][i] == 'galvosy'+'ypixels_'+str(int(self.textbox1G.currentText())):
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
            if self.analogcontainer_array['Sepcification'][i] != 'galvosx'+'avgnum_'+str(int(self.textbox1H.currentText())): #skip the galvoX, as it is too intense
                plt.plot(xlabelhere_all, self.analogcontainer_array['Waveform'][i])
        for i in range(digitalloopnum):
            plt.plot(xlabelhere_all, self.digitalcontainer_array['Waveform'][i])
        plt.text(0.1, 1.1, 'Time lasted:'+str(xlabelhere_all[-1])+'s', fontsize=12)
        plt.show()
        '''
        self.readinchan = []
        
        if self.textbox111A.isChecked():
            self.readinchan.append('PMT')
        if self.textbox222A.isChecked():
            self.readinchan.append('Vp')
        if self.textbox333A.isChecked():
            self.readinchan.append('Ip')       
        
        print(self.readinchan)
        self.measurement.emit(self.analogcontainer_array, self.digitalcontainer_array, self.readinchan, int(self.textboxAA.currentText()))
        #execute(int(self.textboxAA.currentText()), self.analogcontainer_array, self.digitalcontainer_array, self.readinchan)
        return self.analogcontainer_array, self.digitalcontainer_array, self.readinchan
    
    def execute_tread(self):
        self.adcollector = execute_analog_readin_optional_digital_thread()
        self.adcollector.set_waves(int(self.textboxAA.currentText()), self.analogcontainer_array, self.digitalcontainer_array, self.readinchan)
        self.adcollector.collected_data.connect(self.recive_data)
        self.adcollector.start()
        
    def execute(self):
        
        execute_analog_readin_optional_digital(int(self.textboxAA.currentText()), self.analogcontainer_array, self.digitalcontainer_array, self.readinchan)

    def execute_digital(self):
        
        execute_digital(int(self.textboxAA.currentText()), self.digitalcontainer_array)
        
    def recive_data(self, data):
        
        self.channel_number = len(data)
        if self.channel_number == 1:            
            self.data_collected_0 = data[0]
        
        self.PlotDataItem_patch_voltage = PlotDataItem(self.xlabelhere_all, self.data_collected_0)
        #use the same color as before, taking advantages of employing same keys in dictionary
        self.PlotDataItem_patch_voltage.setPen('w')
        self.pw_data.addItem(self.PlotDataItem_patch_voltage)
    
        self.textitem_patch_voltage = pg.TextItem(('Vp'), color=('w'), anchor=(1, 1))
        self.textitem_patch_voltage.setPos(0, 1)
        self.pw_data.addItem(self.textitem_patch_voltage)
        
    def stopMeasurement_daqer(self):
        """Stop """
        self.adcollector.aboutToQuitHandler()
        
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        mainwin = adgenerator()
        mainwin.show()
        app.exec_()
    run_app()