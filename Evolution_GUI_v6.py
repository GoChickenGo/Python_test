# -*- coding: utf-8 -*-
"""
Created on Tue Dec 17 23:40:26 2019

@author: Meng
"""

from __future__ import division
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPoint, QRect, QObject
from PyQt5.QtGui import QColor, QPen, QPixmap, QIcon, QTextCursor, QFont

from PyQt5.QtWidgets import (QWidget, QButtonGroup, QLabel, QSlider, QSpinBox, QDoubleSpinBox, QGridLayout, QPushButton, QGroupBox, 
                             QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox, QTabWidget, QCheckBox, QRadioButton, 
                             QFileDialog, QProgressBar, QTextEdit, QStyleFactory)

import pyqtgraph as pg
from IPython import get_ipython
import sys
import numpy as np
from skimage.io import imread
from skimage.transform import rotate
import threading
import os
import copy
import time
from datetime import datetime
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.express as px
from NIDAQ.constants import HardwareConstants
import NIDAQ.Waveformer_for_screening
from EvolutionScanningThread import ScanningExecutionThread # This is the thread file for execution.
from SampleStageControl.stage import LudlStage
from NIDAQ.generalDaqerThread import execute_tread_singlesample_digital

import FocusCalibrater
import GalvoWidget.PMTWidget
import NIDAQ.AOTFWidget
import ThorlabsFilterSlider.FilterSliderWidget
import InsightX3.TwoPhotonLaserUI
import StylishQT
#import EvolutionAnalysisGUI

class Mainbody(QWidget):
    
    waveforms_generated = pyqtSignal(object, object, list, int)
    #%%
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        os.chdir('./')# Set directory to current folder.
        self.setFont(QFont("Arial"))
        
        self.setMinimumSize(1080, 1920)
        self.setWindowTitle("McDonnell")
        self.layout = QGridLayout(self)
        
        self.RoundQueueDict = {}        
        self.WaveformQueueDict = {}
        self.CamOperationDict = {}
        self.RoundQueueDict['InsightEvents'] = []
        self.RoundQueueDict['FilterEvents'] = []
        
        self.RoundCoordsDict = {}
        self.WaveformQueueDict_GalvoInfor = {}
        self.GeneralSettingDict = {}
        self.FocusCorrectionMatrixDict = {}
        self.FocusStackInfoDict = {}
        self.popnexttopimgcounter = 0

        self.Tag_round_infor = []
        self.Lib_round_infor = []
        
        self.savedirectory = r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data'
        self.ludlStage = LudlStage("COM12")
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for GeneralSettings----------------------------------------------------
        #**************************************************************************************************************************************
        GeneralSettingContainer = StylishQT.roundQGroupBox("Tanto Tanto")
        GeneralSettingContainerLayout = QGridLayout()
        
        self.saving_prefix = ''
        self.savedirectorytextbox = QtWidgets.QLineEdit(self)
        self.savedirectorytextbox.setFixedWidth(300)
        self.savedirectorytextbox.returnPressed.connect(self.update_saving_directory)
        GeneralSettingContainerLayout.addWidget(self.savedirectorytextbox, 0, 1)
        
        self.prefixtextbox = QtWidgets.QLineEdit(self)
        self.prefixtextbox.setPlaceholderText('Prefix')
        self.prefixtextbox.setFixedWidth(80)
        self.prefixtextbox.returnPressed.connect(self.set_prefix)
        GeneralSettingContainerLayout.addWidget(self.prefixtextbox, 0, 2)
        
        self.toolButtonOpenDialog = QtWidgets.QPushButton('Saving directory')
        self.toolButtonOpenDialog.setStyleSheet("QPushButton {color:white;background-color: pink; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                                "QPushButton:pressed {color:yellow;background-color: pink; border-style: outset;border-radius: 3px;border-width: 2px;font: bold 14px;padding: 1px}"
                                                "QPushButton:hover:!pressed {color:gray;background-color: pink; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")

        self.toolButtonOpenDialog.setObjectName("toolButtonOpenDialog")
        self.toolButtonOpenDialog.clicked.connect(self._open_file_dialog)
        
        GeneralSettingContainerLayout.addWidget(self.toolButtonOpenDialog, 0, 0)
        
        ButtonConfigurePipeline = StylishQT.generateButton()
        ButtonConfigurePipeline.clicked.connect(self.ConfigGeneralSettings)
#        ButtonConfigurePipeline.clicked.connect(self.GenerateFocusCorrectionMatrix)
        
        ButtonExePipeline = StylishQT.runButton()
        ButtonExePipeline.clicked.connect(self.ExecutePipeline)
        
        ButtonSavePipeline = StylishQT.saveButton()
        ButtonSavePipeline.clicked.connect(self.Savepipeline)
        
        # Pipeline import
        self.LoadPipelineAddressbox = QLineEdit(self)    
        self.LoadPipelineAddressbox.setFixedWidth(300)
        GeneralSettingContainerLayout.addWidget(self.LoadPipelineAddressbox, 1, 1)
        
        self.BrowsePipelineButton = QPushButton('Browse pipeline', self)
        self.BrowsePipelineButton.setStyleSheet("QPushButton {color:white;background-color:rgb(143,191,224); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                                "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                                "QPushButton:hover:!pressed {color:gray;background-color:rgb(143,191,224); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        
        GeneralSettingContainerLayout.addWidget(self.BrowsePipelineButton, 1, 0) 
        
        self.BrowsePipelineButton.clicked.connect(self.GetPipelineNPFile)
        
        GeneralSettingContainerLayout.addWidget(QLabel('Configure focus correction first.'), 1, 2)
        
        self.ImportPipelineButton = QPushButton('Load', self)
        self.ImportPipelineButton.setStyleSheet("QPushButton {color:white;background-color: rgb(191,216,189); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                                "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                                "QPushButton:hover:!pressed {color:gray;background-color: rgb(191,216,189); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        

        GeneralSettingContainerLayout.addWidget(self.ImportPipelineButton, 1, 3)
        self.ImportPipelineButton.clicked.connect(self.LoadPipelineFile)
        
        GeneralSettingContainerLayout.addWidget(ButtonConfigurePipeline, 0, 3)        
        GeneralSettingContainerLayout.addWidget(ButtonExePipeline, 0, 4)
        GeneralSettingContainerLayout.addWidget(ButtonSavePipeline, 0, 5)    
        GeneralSettingContainer.setLayout(GeneralSettingContainerLayout)
        
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for Focus correction---------------------------------------------------
        #**************************************************************************************************************************************
        FocusCorrectionContainer = StylishQT.roundQGroupBox("Focus correction")
        FocusCorrectionContainerLayout = QGridLayout()
        
        self.ApplyFocusSetCheckbox = QCheckBox("Apply focus set")
        self.ApplyFocusSetCheckbox.setStyleSheet('color:blue;font:bold "Times New Roman"')
        FocusCorrectionContainerLayout.addWidget(self.ApplyFocusSetCheckbox, 0, 0, 1, 1)
        
        self.FocusInterStrategy = QComboBox()
        self.FocusInterStrategy.addItems(['Duplicate', 'Interpolation'])
        FocusCorrectionContainerLayout.addWidget(self.FocusInterStrategy, 0, 1)
        
        FocusCorrectionContainerLayout.addWidget(QLabel("Focus offset:"), 0, 2)
        self.FocusCorrectionOffsetBox = QDoubleSpinBox(self)
        self.FocusCorrectionOffsetBox.setDecimals(4)
        self.FocusCorrectionOffsetBox.setMinimum(-10)
        self.FocusCorrectionOffsetBox.setMaximum(10)
        self.FocusCorrectionOffsetBox.setValue(0.000)
        self.FocusCorrectionOffsetBox.setSingleStep(0.0001)  
        FocusCorrectionContainerLayout.addWidget(self.FocusCorrectionOffsetBox, 0, 3)
        
        self.FocusCalibraterInstance = FocusCalibrater.FocusMatrixFeeder()
        self.FocusCalibraterInstance.FocusCorrectionFomula.connect(self.CaptureFocusCorrectionMatrix)
        self.FocusCalibraterInstance.FocusCorrectionForDuplicateMethod.connect(self.CaptureFocusDuplicateMethodMatrix)
        FocusCorrectionContainerLayout.addWidget(self.FocusCalibraterInstance, 1, 0, 1, 4)
        
        FocusCorrectionContainer.setMinimumWidth(469)
        FocusCorrectionContainer.setLayout(FocusCorrectionContainerLayout)
        
    #--------------------------------------------------------------------------------------------------------------------------------------------
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for tool widgets-------------------------------------------------------
        #**************************************************************************************************************************************
        ToolWidgetsContainer = StylishQT.roundQGroupBox('Tool widgets')
        ToolWidgetsLayout = QGridLayout()
        
        self.OpenPMTWidgetButton = QPushButton('PMT', self)
        ToolWidgetsLayout.addWidget(self.OpenPMTWidgetButton, 0, 1)
        self.OpenPMTWidgetButton.clicked.connect(self.openPMTWidget)   
        
        self.OpenInsightWidgetButton = QPushButton('Insight X3', self)
        ToolWidgetsLayout.addWidget(self.OpenInsightWidgetButton, 1, 1)
        self.OpenInsightWidgetButton.clicked.connect(self.openInsightWidget)    
        
        self.switchbutton_LED = QPushButton('LED')
        self.switchbutton_LED.setCheckable(True)
        self.switchbutton_LED.clicked.connect(lambda: self.execute_tread_single_sample_digital('LED'))
        ToolWidgetsLayout.addWidget(self.switchbutton_LED, 0, 3)
        
#        self.openScreenAnalysisWidgetButton = QPushButton('Screen Analysis', self)
#        ToolWidgetsLayout.addWidget(self.openScreenAnalysisWidgetButton, 1, 3)
#        self.openScreenAnalysisWidgetButton.clicked.connect(self.openScreenAnalysisWidget)  
        
        self.openScreenAnalysisMLWidgetButton = QPushButton('Screen Analysis ML', self)
        ToolWidgetsLayout.addWidget(self.openScreenAnalysisMLWidgetButton, 1, 2)
        self.openScreenAnalysisMLWidgetButton.clicked.connect(self.openScreenAnalysisMLWidget)
        
        ToolWidgetsContainer.setLayout(ToolWidgetsLayout)

        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for Billboard display------------------------------------------------------
        #**************************************************************************************************************************************
        ImageDisplayContainer = QGroupBox()
        ImageDisplayContainerLayout = QGridLayout()        
        
        AOTFWidgetInstance = NIDAQ.AOTFWidget.AOTFWidgetUI()
        ImageDisplayContainerLayout.addWidget(AOTFWidgetInstance, 0, 0, 1, 1)
        
        FilterSliderWidgetInstance = ThorlabsFilterSlider.FilterSliderWidget.FilterSliderWidgetUI()
        ImageDisplayContainerLayout.addWidget(FilterSliderWidgetInstance, 1, 0, 1, 1)
                
        self.ConsoleTextDisplay = QTextEdit()
        self.ConsoleTextDisplay.setFontItalic(True)
        self.ConsoleTextDisplay.setPlaceholderText('Notice board from console.')
        self.ConsoleTextDisplay.setMaximumHeight(200)
        self.ConsoleTextDisplay.setFixedWidth(200)
        ImageDisplayContainerLayout.addWidget(self.ConsoleTextDisplay, 0, 1, 2, 1)
        
        ImageDisplayContainerLayout.addWidget(ToolWidgetsContainer, 2, 0, 1, 1)
        
        ImageDisplayContainer.setLayout(ImageDisplayContainerLayout)
        ImageDisplayContainer.setMinimumHeight(400)
        ImageDisplayContainer.setMinimumWidth(550)



        # ==========================================================================================================================================================
        #         #**************************************************************************************************************************************
        #         #-----------------------------------------------------------GUI for PiplineContainer---------------------------------------------------
        #         #**************************************************************************************************************************************
        # ==========================================================================================================================================================
        PipelineContainer = StylishQT.roundQGroupBox("Pipeline settings")
        PipelineContainerLayout = QGridLayout()
        
        self.RoundOrderBox = QSpinBox(self)
        self.RoundOrderBox.setMinimum(1)
        self.RoundOrderBox.setMaximum(1000)
        self.RoundOrderBox.setValue(1)
        self.RoundOrderBox.setSingleStep(1)
        self.RoundOrderBox.setMaximumWidth(30)
        PipelineContainerLayout.addWidget(self.RoundOrderBox, 0, 1)
        PipelineContainerLayout.addWidget(QLabel("Round sequence:"), 0, 0)
        
#        ButtonAddRound = QPushButton('Add Round', self)
#        ButtonAddRound.setStyleSheet("QPushButton {color:white;background-color: teal; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
#                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        
        ButtonAddRound = StylishQT.addButton()
        ButtonDeleteRound = StylishQT.stop_deleteButton()

        ButtonClearRound = QPushButton('Clear Rounds', self)
        ButtonClearRound.setStyleSheet("QPushButton {color:white;background-color: maroon; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:hover:!pressed {color:gray;background-color: maroon; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        

        PipelineContainerLayout.addWidget(ButtonAddRound, 0, 2)
        ButtonAddRound.clicked.connect(self.AddFreshRound)
        ButtonAddRound.clicked.connect(self.GenerateScanCoords)
        
        PipelineContainerLayout.addWidget(ButtonDeleteRound, 0, 3)
        ButtonDeleteRound.clicked.connect(self.DeleteFreshRound)
        
        PipelineContainerLayout.addWidget(ButtonClearRound, 0, 4)
        ButtonClearRound.clicked.connect(self.ClearRoundQueue)
        
        self.ScanRepeatTextbox = QSpinBox(self)
        self.ScanRepeatTextbox.setMinimum(1)
        self.ScanRepeatTextbox.setValue(1)
        self.ScanRepeatTextbox.setMaximum(100000)
        self.ScanRepeatTextbox.setSingleStep(1)
        PipelineContainerLayout.addWidget(self.ScanRepeatTextbox, 0, 7)
        PipelineContainerLayout.addWidget(QLabel("Meshgrid:"), 0, 6)  
        
        self.OpenTwoPLaserShutterCheckbox = QCheckBox("Open shutter first")
        self.OpenTwoPLaserShutterCheckbox.setStyleSheet('color:blue;font:bold "Times New Roman"')
        self.OpenTwoPLaserShutterCheckbox.setChecked(True)
        PipelineContainerLayout.addWidget(self.OpenTwoPLaserShutterCheckbox, 0, 8)  

        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for StageScanContainer-------------------------------------------------
        #**************************************************************************************************************************************    
        ScanContainer = QWidget()     
        ScanSettingLayout = QGridLayout() #Layout manager
        ScanContainer.layout = ScanSettingLayout
        
        self.ScanStartRowIndexTextbox = QSpinBox(self)
        self.ScanStartRowIndexTextbox.setMinimum(-20000)
        self.ScanStartRowIndexTextbox.setMaximum(100000)
        self.ScanStartRowIndexTextbox.setSingleStep(1650)
        ScanSettingLayout.addWidget(self.ScanStartRowIndexTextbox, 0, 1)
        ScanSettingLayout.addWidget(QLabel("Start index-row:"), 0, 0)
      
        self.ScanEndRowIndexTextbox = QSpinBox(self)
        self.ScanEndRowIndexTextbox.setMinimum(-20000)
        self.ScanEndRowIndexTextbox.setMaximum(100000)
        self.ScanEndRowIndexTextbox.setSingleStep(1650)
        ScanSettingLayout.addWidget(self.ScanEndRowIndexTextbox, 0, 3)
        ScanSettingLayout.addWidget(QLabel("End index-row:"), 0, 2)
        
        self.ScanStartColumnIndexTextbox = QSpinBox(self)
        self.ScanStartColumnIndexTextbox.setMinimum(-20000)
        self.ScanStartColumnIndexTextbox.setMaximum(100000)
        self.ScanStartColumnIndexTextbox.setSingleStep(1650)
        ScanSettingLayout.addWidget(self.ScanStartColumnIndexTextbox, 1, 1)
        ScanSettingLayout.addWidget(QLabel("Start index-column:"), 1, 0)   
        
        self.ScanEndColumnIndexTextbox = QSpinBox(self)
        self.ScanEndColumnIndexTextbox.setMinimum(-20000)
        self.ScanEndColumnIndexTextbox.setMaximum(100000)
        self.ScanEndColumnIndexTextbox.setSingleStep(1650)
        ScanSettingLayout.addWidget(self.ScanEndColumnIndexTextbox, 1, 3)
        ScanSettingLayout.addWidget(QLabel("End index-column:"), 1, 2)      

        self.ScanstepTextbox = QSpinBox(self)
        self.ScanstepTextbox.setMaximum(20000)
        self.ScanstepTextbox.setValue(1650)
        self.ScanstepTextbox.setSingleStep(500)
        ScanSettingLayout.addWidget(self.ScanstepTextbox, 0, 5)
        ScanSettingLayout.addWidget(QLabel("Step size:"), 0, 4)
        
        self.FocusStackNumTextbox = QSpinBox(self)
        self.FocusStackNumTextbox.setMinimum(1)
        self.FocusStackNumTextbox.setMaximum(20000)
        self.FocusStackNumTextbox.setValue(1)
        self.FocusStackNumTextbox.setSingleStep(1)
        ScanSettingLayout.addWidget(self.FocusStackNumTextbox, 1, 5)
        ScanSettingLayout.addWidget(QLabel("Focus stack number:"), 1, 4)
        
        self.FocusStackStepTextbox = QDoubleSpinBox(self)
        self.FocusStackStepTextbox.setMinimum(0)
        self.FocusStackStepTextbox.setMaximum(10000)
        self.FocusStackStepTextbox.setDecimals(6)
        self.FocusStackStepTextbox.setValue(0.001)
        self.FocusStackStepTextbox.setSingleStep(0.001)  
        ScanSettingLayout.addWidget(self.FocusStackStepTextbox, 1, 7)
        ScanSettingLayout.addWidget(QLabel("Focus stack step(mm):"), 1, 6)   
        
        ScanContainer.setLayout(ScanSettingLayout)
        
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for Laser/filter-------------------------------------------------
        #**************************************************************************************************************************************  
        TwoPLaserContainer = QGroupBox()        
        TwoPLaserSettingLayout = QGridLayout() #Layout manager
        
        self.TwoPLaserShutterCheckbox = QCheckBox("Insight Shutter event")
        self.TwoPLaserShutterCheckbox.setStyleSheet('color:blue;font:bold "Times New Roman"')
        TwoPLaserSettingLayout.addWidget(self.TwoPLaserShutterCheckbox, 0, 0)
        
        self.TwoPLaserWavelengthCheckbox = QCheckBox("Insight Wavelength event")
        self.TwoPLaserWavelengthCheckbox.setStyleSheet('color:blue;font:bold "Times New Roman"')
        TwoPLaserSettingLayout.addWidget(self.TwoPLaserWavelengthCheckbox, 1, 0)        
        
        self.TwoPLaserWavelengthbox = QSpinBox(self)
        self.TwoPLaserWavelengthbox.setMinimum(680)
        self.TwoPLaserWavelengthbox.setMaximum(1300)
        self.TwoPLaserWavelengthbox.setSingleStep(100)
        self.TwoPLaserWavelengthbox.setValue(1280)
        TwoPLaserSettingLayout.addWidget(self.TwoPLaserWavelengthbox, 1, 1)
        
        self.TwoPLaserShutterCombox = QComboBox()
        self.TwoPLaserShutterCombox.addItems(['Open', 'Close'])
        TwoPLaserSettingLayout.addWidget(self.TwoPLaserShutterCombox, 0, 1)
        
        ButtonAddInsightEvent = QPushButton('Add Insight event', self)
        TwoPLaserSettingLayout.addWidget(ButtonAddInsightEvent, 0, 2)
        ButtonAddInsightEvent.clicked.connect(self.AddInsightEvent)
        
        ButtonDelInsightEvent = QPushButton('Del Insight event', self)
        TwoPLaserSettingLayout.addWidget(ButtonDelInsightEvent, 1, 2) 
        ButtonDelInsightEvent.clicked.connect(self.DelInsightEvent)
        
        #--------filter------------
        NDfilterlabel = QLabel("ND filter:")
        TwoPLaserSettingLayout.addWidget(NDfilterlabel, 0, 3)
        NDfilterlabel.setAlignment(Qt.AlignRight)
        self.NDfilterCombox = QComboBox()
        self.NDfilterCombox.addItems(['1', '2', '2.3', '2.5', '3', '0.5'])
        TwoPLaserSettingLayout.addWidget(self.NDfilterCombox, 0, 4)
        
        Emifilterlabel = QLabel("Emission filter:")
        TwoPLaserSettingLayout.addWidget(Emifilterlabel, 1, 3)
        Emifilterlabel.setAlignment(Qt.AlignRight)
        self.EmisfilterCombox = QComboBox()
        self.EmisfilterCombox.addItems(['Arch', 'eGFP', 'Citrine'])
        TwoPLaserSettingLayout.addWidget(self.EmisfilterCombox, 1, 4)
        
        ButtonAddFilterEvent = QPushButton('Add filter event', self)
        TwoPLaserSettingLayout.addWidget(ButtonAddFilterEvent, 0, 5)
        ButtonAddFilterEvent.clicked.connect(self.AddFilterEvent)
        
        ButtonDelFilterEvent = QPushButton('Del filter event', self)
        TwoPLaserSettingLayout.addWidget(ButtonDelFilterEvent, 1, 5) 
        ButtonDelFilterEvent.clicked.connect(self.DelFilterEvent)
        
        TwoPLaserContainer.setLayout(TwoPLaserSettingLayout)
                
        #--------------------------------------------------------------------------------------------------------------------------------------
        self.RoundGeneralSettingTabs = QTabWidget()
        self.RoundGeneralSettingTabs.addTab(ScanContainer,"Scanning settings")
        self.RoundGeneralSettingTabs.addTab(TwoPLaserContainer,"Pulse laser/Filter settings")

        PipelineContainerLayout.addWidget(self.RoundGeneralSettingTabs, 2, 0, 1, 10)
        
        
        self.WaveformOrderBox = QSpinBox(self)
        self.WaveformOrderBox.setMinimum(1)
        self.WaveformOrderBox.setMaximum(1000)
        self.WaveformOrderBox.setValue(1)
        self.WaveformOrderBox.setSingleStep(1)
        self.WaveformOrderBox.setMaximumWidth(30)
        PipelineContainerLayout.addWidget(self.WaveformOrderBox, 3, 1)
        PipelineContainerLayout.addWidget(QLabel("Waveform/Camera sequence:"), 3, 0)
        
        ButtonAddWaveform = StylishQT.addButton()
        ButtonDeleteWaveform = StylishQT.stop_deleteButton()
        
        ButtonClearWaveform = QPushButton('Clear Waveforms/Camera', self)
        ButtonClearWaveform.setStyleSheet("QPushButton {color:white;background-color: maroon; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:hover:!pressed {color:gray;background-color: maroon; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        

        PipelineContainerLayout.addWidget(ButtonAddWaveform, 3, 3)
        PipelineContainerLayout.addWidget(ButtonDeleteWaveform, 3, 4)
        PipelineContainerLayout.addWidget(ButtonClearWaveform, 3, 5)
        
        ButtonAddWaveform.clicked.connect(self.AddFreshWaveform)
        ButtonAddWaveform.clicked.connect(self.AddCameraOperation)
        
        ButtonDeleteWaveform.clicked.connect(self.DeleteFreshWaveform)
        ButtonDeleteWaveform.clicked.connect(self.DeleteCameraOperation)
        ButtonClearWaveform.clicked.connect(self.ClearWaveformQueue)
        ButtonClearWaveform.clicked.connect(self.CleanCameraOperation)
        #--------------------------------------------------------------------------------------------------------------------------------------
        self.EachCoordDwellSettingTabs = QTabWidget()
 
        # =============================================================================
        #         Waveforms tab settings
        # =============================================================================
        waveformTab = QWidget()
        waveformTabLayout = QGridLayout()
        
        self.Waveformer_widget_instance = NIDAQ.Waveformer_for_screening.WaveformGenerator()
        self.Waveformer_widget_instance.WaveformPackage.connect(self.UpdateWaveformerSignal)
        self.Waveformer_widget_instance.GalvoScanInfor.connect(self.UpdateWaveformerGalvoInfor)

        waveformTabLayout.addWidget(self.Waveformer_widget_instance, 2, 0, 2, 9)
        waveformTab.setLayout(waveformTabLayout)
        
        # =============================================================================
        #         Camera tab settings
        # =============================================================================
        CameraDwellTab = QWidget()
        CameraDwellTabLayout = QGridLayout()

        self.CamTriggerSettingBox = QComboBox()
        self.CamTriggerSettingBox.addItems(["EXTERNAL", "INTERNAL"])
        
        self.CamTriggerActive_SettingBox = QComboBox()
        self.CamTriggerActive_SettingBox.addItems(['EDGE', 'LEVEL', 'SYNCREADOUT'])
        
        CameraDwellTabLayout.addWidget(QLabel("Trigger:"), 1, 0)
        CameraDwellTabLayout.addWidget(self.CamTriggerSettingBox, 1, 1)
        CameraDwellTabLayout.addWidget(self.CamTriggerActive_SettingBox, 1, 2)
        
        self.StreamBufferTotalFrames_spinbox = QSpinBox()
        self.StreamBufferTotalFrames_spinbox.setMaximum(120000)
        self.StreamBufferTotalFrames_spinbox.setValue(0)
        CameraDwellTabLayout.addWidget(self.StreamBufferTotalFrames_spinbox, 1, 4)
        CameraDwellTabLayout.addWidget(QLabel("Buffers:"), 1, 3)
        
        self.CamExposureBox = QDoubleSpinBox(self)
        self.CamExposureBox.setDecimals(6)
        self.CamExposureBox.setMinimum(0)
        self.CamExposureBox.setMaximum(100)
        self.CamExposureBox.setValue(0.001501)
        self.CamExposureBox.setSingleStep(0.001)  
        CameraDwellTabLayout.addWidget(self.CamExposureBox, 1, 6)  
        CameraDwellTabLayout.addWidget(QLabel("Exposure time:"), 1, 5)
        
        CameraDwellTab.setLayout(CameraDwellTabLayout)
        
        self.EachCoordDwellSettingTabs.addTab(waveformTab,"Waveforms settings")
        self.EachCoordDwellSettingTabs.addTab(CameraDwellTab,"Camera operations")

        PipelineContainerLayout.addWidget(self.EachCoordDwellSettingTabs, 4, 0, 4, 10)    
        
        PipelineContainer.setLayout(PipelineContainerLayout)
        
        self.layout.addWidget(GeneralSettingContainer, 1, 0, 1, 4)
        self.layout.addWidget(FocusCorrectionContainer, 2, 0, 1, 2)
        self.layout.addWidget(ImageDisplayContainer, 2, 2, 1, 2)
#        self.layout.addWidget(ToolWidgetsContainer, 4, 0, 1, 1)
#        self.layout.addWidget(self.PostProcessTab, 4, 1, 1, 3)
        self.layout.addWidget(PipelineContainer, 5, 0, 1, 4)
        self.setLayout(self.layout)
        
        
    #%%
    """
    #     FUNCTIONS FOR EXECUTION
    
    ----------------Screening routine configuration Structure -----------------
    
    ====RoundQueueDict====                              Dictionary=============
    
      -- key: RoundPackage_{}
            |__ WaveformQueueDict                       Dictionary
                key: WaveformPackage_{}                 Waveforms tuple signal from Waveformer. At each coordinate.
                
            |__ CamOperationDict                        Dictionary
                key: CameraPackage_{}
            
      -- key: GalvoInforPackage_{}                   
            |__ WaveformQueueDict_GalvoInfor            Dictionary
                key: GalvoInfor_{}                      Galvo scanning configuration signal from Waveformer. At each coordinate.
                
      -- key: FilterEvents
            |__ List of filter operation strings, in the round.
            
      -- key: InsightEvents
            |__ List of insight laser operation strings, in the round.
        
    ====RoundCoordsDict====                             Dictionary=============
    
      -- key: CoordsPackage_{}
            |__ np.array of scanning coordinates.
            
    ====GeneralSettingDict====                          Dictionary=============
    
      -- key: 'savedirectory'                           screening data saving directory.
      
      -- key: 'FocusCorrectionMatrixDict'               Dictionary
                  |__ key: RoundPackage_{}
                      or RoundPackage_{}_Grid_{}        np.array of pre-calibrated focus positions.
                  
      -- key: 'FocusStackInfoDict'                      Dictionary
                  |__ key: RoundPackage_{}              String specifies 'NumberOfFocus{}WithIncrementBeing{}'.
                  
      -- key: 'Meshgrid'                                int if scanning grid number. meshrepeat
      
      -- key: 'Scanning step'                           Scanning stage step. self.step
      
      -- key: 'StartUpEvents'                           List of strings, like Shutter_Open
    """
    # ==========================================================================================================================================================
    # ------------------------------------------------------------Waveform package functions at each coordinate-------------------------------------------------
    # ==========================================================================================================================================================
    """
    Every time when the 'configure' button in waveformer widget is hit, the 'WaveformPackage' and 'GalvoInfor' signals are sent here.
    """
    def UpdateWaveformerSignal(self, WaveformPackage):
        """
        Capture the newest generated waveform tuple signal from Waveformer, which contains 4 parts in tuple:
        (sampling rate, analogcontainer_array, digitalcontainer_array, recording channel list)
        """
        self.FreshWaveformPackage = WaveformPackage

    def UpdateWaveformerGalvoInfor(self, GalvoInfor):
        self.FreshWaveformGalvoInfor = GalvoInfor
    
    def AddFreshWaveform(self): # Add waveform package for single round.
        CurrentWaveformPackageSequence = self.WaveformOrderBox.value()
        try:
            self.WaveformQueueDict['WaveformPackage_{}'.format(CurrentWaveformPackageSequence)] = self.FreshWaveformPackage
        except AttributeError:
            QMessageBox.warning(self,'Error','Click configure waveform first!',QMessageBox.Ok)
            
        self.WaveformQueueDict_GalvoInfor['GalvoInfor_{}'.format(CurrentWaveformPackageSequence)] = self.FreshWaveformGalvoInfor
        self.normalOutputWritten('Waveform{} added.\n'.format(CurrentWaveformPackageSequence))
        print('Waveform added.')
        
    def DeleteFreshWaveform(self): # Empty the waveform container to avoid crosstalk between rounds.
        CurrentWaveformPackageSequence = self.WaveformOrderBox.value()
        del self.WaveformQueueDict['WaveformPackage_{}'.format(CurrentWaveformPackageSequence)]
        
        del self.WaveformQueueDict_GalvoInfor['GalvoInfor_{}'.format(CurrentWaveformPackageSequence)]
        
    def ClearWaveformQueue(self):
        self.WaveformQueueDict = {}
        self.WaveformQueueDict_GalvoInfor = {}
        
    # ==========================================================================================================================================================
    # --------------------------------------------------------------Camera operation at each coordinate---------------------------------------------------------
    # ==========================================================================================================================================================
    def AddCameraOperation(self):
        CurrentCamPackageSequence = self.WaveformOrderBox.value()
        
        if self.StreamBufferTotalFrames_spinbox.value() != 0:
            CameraOperation = {"Settings": ["trigger_source", self.CamTriggerSettingBox.currentText(), 
                                            "exposure_time", self.CamExposureBox.value(),
                                            "trigger_active", self.CamTriggerActive_SettingBox.currentText()], 
                               "Buffer_number": self.StreamBufferTotalFrames_spinbox.value()}
            
            self.CamOperationDict['CameraPackage_{}'.format(CurrentCamPackageSequence)] = CameraOperation
        else:
            self.CamOperationDict['CameraPackage_{}'.format(CurrentCamPackageSequence)] = {}

    def DeleteCameraOperation(self): # Empty the waveform container to avoid crosstalk between rounds.
        CurrentCamPackageSequence = self.WaveformOrderBox.value()
        del self.CamOperationDict['CameraPackage_{}'.format(CurrentCamPackageSequence)]    
        
    def CleanCameraOperation(self):
        self.CamOperationDict = {}
    # ==========================================================================================================================================================
    # --------------------------------------------------------------Settings at each round----------------------------------------------------------------------
    # ==========================================================================================================================================================
    def AddFreshRound(self):
        CurrentRoundSequence = self.RoundOrderBox.value()
        
        WaveformQueueDict = copy.deepcopy(self.WaveformQueueDict) # Here we make the self.WaveformQueueDict private so that other rounds won't refer to the same variable.
        WaveformQueueDict_GalvoInfor = copy.deepcopy(self.WaveformQueueDict_GalvoInfor)
        CamOperationDict = copy.deepcopy(self.CamOperationDict)
        
        self.RoundQueueDict['RoundPackage_{}'.format(CurrentRoundSequence)] = [WaveformQueueDict, CamOperationDict]
        self.RoundQueueDict['GalvoInforPackage_{}'.format(CurrentRoundSequence)] = WaveformQueueDict_GalvoInfor # Information we need to restore pmt scanning images.
        
        #Configure information for Z-stack
        ZstackNumber = self.FocusStackNumTextbox.value()
        ZstackStep = self.FocusStackStepTextbox.value()
        
        self.FocusStackInfoDict['RoundPackage_{}'.format(CurrentRoundSequence)] = 'NumberOfFocus{}WithIncrementBeing{}'.format(ZstackNumber, ZstackStep)
        
        self.normalOutputWritten('Round{} added.\n'.format(CurrentRoundSequence))
        print('Round added.')
        
    #-----------------------Configure filter event-----------------------------
    def AddFilterEvent(self):
        CurrentRoundSequence = self.RoundOrderBox.value()

        self.RoundQueueDict['FilterEvents'].append('Round_{}_ND_ToPos_{}'.format(CurrentRoundSequence, self.NDfilterCombox.currentText()))
        self.RoundQueueDict['FilterEvents'].append('Round_{}_EM_ToPos_{}'.format(CurrentRoundSequence, self.EmisfilterCombox.currentText()))
        print(self.RoundQueueDict['FilterEvents'])
        self.normalOutputWritten(str(self.RoundQueueDict['FilterEvents'])+'\n')
        
    def DelFilterEvent(self):
        CurrentRoundSequence = self.RoundOrderBox.value()
        
        if 'Round_{}_ND_ToPos_{}'.format(CurrentRoundSequence, self.NDfilterCombox.currentText()) in self.RoundQueueDict['FilterEvents']:
            self.RoundQueueDict['FilterEvents'].remove('Round_{}_ND_ToPos_{}'.format(CurrentRoundSequence, self.NDfilterCombox.currentText()))
            self.RoundQueueDict['FilterEvents'].remove('Round_{}_EM_ToPos_{}'.format(CurrentRoundSequence, self.EmisfilterCombox.currentText()))
        print(self.RoundQueueDict['FilterEvents'])
        self.normalOutputWritten(str(self.RoundQueueDict['FilterEvents'])+'\n')
        
    #-----------------------Configure insight event-----------------------------
    def AddInsightEvent(self):
        CurrentRoundSequence = self.RoundOrderBox.value()
        
        if self.TwoPLaserShutterCheckbox.isChecked():
            self.RoundQueueDict['InsightEvents'].append('Round_{}_Shutter_{}'.format(CurrentRoundSequence, self.TwoPLaserShutterCombox.currentText()))
        if self.TwoPLaserWavelengthCheckbox.isChecked():
            self.RoundQueueDict['InsightEvents'].append('Round_{}_WavelengthTo_{}'.format(CurrentRoundSequence, self.TwoPLaserWavelengthbox.value()))
        print(self.RoundQueueDict['InsightEvents'])
        self.normalOutputWritten(str(self.RoundQueueDict['InsightEvents'])+'\n')
        
    def DelInsightEvent(self):
        CurrentRoundSequence = self.RoundOrderBox.value()
        
        if self.TwoPLaserShutterCheckbox.isChecked():
            self.RoundQueueDict['InsightEvents'].remove('Round_{}_Shutter_{}'.format(CurrentRoundSequence, self.TwoPLaserShutterCombox.currentText()))
        if self.TwoPLaserWavelengthCheckbox.isChecked():
            self.RoundQueueDict['InsightEvents'].remove('Round_{}_WavelengthTo_{}'.format(CurrentRoundSequence, self.TwoPLaserWavelengthbox.value()))
        print(self.RoundQueueDict['InsightEvents'])
        self.normalOutputWritten(str(self.RoundQueueDict['InsightEvents'])+'\n')
   
    #-----------------------------Generate Scan Coords-----------------------------
    def GenerateScanCoords(self):
        self.CoordContainer = np.array([])
        # settings for scanning index
        position_index=[]
        row_start = int(self.ScanStartRowIndexTextbox.value()) #row position index start number
        row_end = int(self.ScanEndRowIndexTextbox.value())+1 #row position index end number
        
        column_start = int(self.ScanStartColumnIndexTextbox.value())
        column_end = int(self.ScanEndColumnIndexTextbox.value())+1  # With additional plus one, the range is fully covered by steps.
        
        self.step = int(self.ScanstepTextbox.value()) #length of each step, 1500 for -5~5V FOV
      
        for i in range(row_start, row_end, self.step):
            position_index.append(int(i))
            for j in range(column_start, column_end, self.step):
                position_index.append(int(j))
                
                self.CoordContainer = np.append(self.CoordContainer, (position_index))
#                print('the coords now: '+ str(self.CoordContainer))
                del position_index[-1]
                
            position_index=[]

        CurrentRoundSequence = self.RoundOrderBox.value()
        self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRoundSequence)] = self.CoordContainer
        
    def DeleteFreshRound(self):
        CurrentRoundSequence = self.RoundOrderBox.value()
        del self.RoundQueueDict['RoundPackage_{}'.format(CurrentRoundSequence)]
        del self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRoundSequence)]
        del self.RoundQueueDict['GalvoInforPackage_{}'.format(CurrentRoundSequence)]
        print(self.RoundQueueDict.keys())    
    
    def ClearRoundQueue(self):
        self.WaveformQueueDict = {}
        self.CamOperationDict = {}
        self.RoundQueueDict = {}
        self.RoundQueueDict['InsightEvents'] = []
        self.RoundQueueDict['FilterEvents'] = []
        self.RoundCoordsDict = {}
        self.WaveformQueueDict_GalvoInfor = {}
        self.GeneralSettingDict = {}
        self.FocusStackInfoDict = {}
        
        self.normalOutputWritten('Rounds cleared.\n')
        print('Rounds cleared.')
    #%%
    """
    # =============================================================================
    #     Configure general settings, get ready for execution      
    # =============================================================================
    """
    def ConfigGeneralSettings(self):
        savedirectory = self.savedirectory
        meshrepeat = self.ScanRepeatTextbox.value()
        StartUpEvents = []
        if self.OpenTwoPLaserShutterCheckbox.isChecked():
            StartUpEvents.append('Shutter_Open')
        #--------------------------------------------------------Generate the focus correction matrix-----------------------------------------------------------
        if self.ApplyFocusSetCheckbox.isChecked():
            self.FocusCorrectionMatrixDict = {}
            if self.FocusInterStrategy.currentText() == 'Interpolation':
            
                for CurrentRound in range(len(self.RoundCoordsDict)):
                    
                    if len(self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRound+1)]) > 2: # If it's more than 1 pos.
                        #---------------numpy.meshgrid method------------------------
                        OriginalCoordsPackage = self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRound+1)]
                        
                        step = OriginalCoordsPackage[3] - OriginalCoordsPackage[1]
                        
                        OriginalCoordsOdd_Row = OriginalCoordsPackage[::2]
                        OriginalCoordsEven_Col = OriginalCoordsPackage[1::2]
                        
                        row_start = np.amin(OriginalCoordsOdd_Row)
                        row_end = np.amax(OriginalCoordsOdd_Row)
                        
                        column_start = np.amin(OriginalCoordsEven_Col)
                        column_end = np.amax(OriginalCoordsEven_Col)     
                        
                        linspace_num = int((row_end-row_start)/step)+1
                        X = np.linspace(row_start,row_end,linspace_num)
                        Y = np.linspace(column_start,column_end,linspace_num)
        #                ExeColumnIndex, ExeRowIndex = np.meshgrid(X,Y)
        #                
        #                self.ExeColumnIndexMeshgrid = ExeColumnIndex.astype(int)
        #                self.ExeRowIndexMeshgrid = ExeRowIndex.astype(int)
                        
                        self.FocusCorrectionMatrix = self.CorrectionFomula(X, Y)
                        
                        self.FocusCorrectionMatrix = self.FocusCorrectionMatrix.flatten()
                        print(self.FocusCorrectionMatrix)
                        
                        FocusCorrectionMatrix = copy.deepcopy(self.FocusCorrectionMatrix)
                        FocusCorrectionMatrix += self.FocusCorrectionOffsetBox.value()
                        self.FocusCorrectionMatrixDict['RoundPackage_{}'.format(CurrentRound+1)] = FocusCorrectionMatrix
    
                    else:
                        self.FocusCorrectionMatrix = self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRound+1)]
                        FocusCorrectionMatrix = copy.deepcopy(self.FocusCorrectionMatrix)
                        
                        FocusCorrectionMatrix += self.FocusCorrectionOffsetBox.value()
                        
                        self.FocusCorrectionMatrixDict['RoundPackage_{}'.format(CurrentRound+1)] = FocusCorrectionMatrix
                        
                        
            elif self.FocusInterStrategy.currentText() == 'Duplicate':
                for EachGrid in range(meshrepeat**2):
                    if len(self.FocusDuplicateMethodInfor['Grid_{}'.format(EachGrid)][0,:]) > 1:
                        RawDuplicateRow = self.FocusDuplicateMethodInfor['Grid_{}'.format(EachGrid)][0,:] # The row index from calibration step (Corresponding to column index in python array)
                        RawDuplicateCol = self.FocusDuplicateMethodInfor['Grid_{}'.format(EachGrid)][1,:]
                        RawDuplicateFocus = self.FocusDuplicateMethodInfor['Grid_{}'.format(EachGrid)][2,:]
                        sparsestep = RawDuplicateCol[1] - RawDuplicateCol[0]
        #                print('sparse step {}'.format(sparsestep))
                        for CurrentRound in range(len(self.RoundCoordsDict)):
                            
                            if len(self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRound+1)]) > 2: # If it's more than 1 pos.
                                #---------------numpy.meshgrid method------------------------
                                OriginalCoordsPackage = self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRound+1)]
                                
                                Originalstep = OriginalCoordsPackage[3] - OriginalCoordsPackage[1]
                                
                                OriginalCoordsOdd_Row = OriginalCoordsPackage[::2]
                                OriginalCoordsEven_Col = OriginalCoordsPackage[1::2]
                                
                                row_start = np.amin(OriginalCoordsOdd_Row)
                                row_end = np.amax(OriginalCoordsOdd_Row)
                                
                                column_start = np.amin(OriginalCoordsEven_Col)
                                column_end = np.amax(OriginalCoordsEven_Col)     
                                
                                linspace_num_x = int((row_end-row_start)/Originalstep)+1
                                linspace_num_y = int((column_end-column_start)/Originalstep)+1
                                X = np.linspace(row_start,row_end,linspace_num_x)
                                Y = np.linspace(column_start,column_end,linspace_num_y)
                                
                                ExeRowIndex, ExeColIndex = np.meshgrid(X,Y)
                                
                                FocusCorrectionMatrixContainer = RawDuplicateFocus[0]*np.ones((len(Y), len(X)))
         
                                c = int(sparsestep/Originalstep)
        #                        print('RawDuplicateFocus'+str(RawDuplicateFocus))
        #                        print(FocusCorrectionMatrixContainer)
                                for i in range(len(RawDuplicateRow)):
                                    row = int(RawDuplicateRow[i]/sparsestep)
                                    col = int(RawDuplicateCol[i]/sparsestep)
                                    
        #                            print('row{},col{}'.format(row, col))
                                    
                                    try:    
                                        FocusCorrectionMatrixContainer[col*c:col*c+c, row*c:row*c+c] = RawDuplicateFocus[i]
                                    except:
                                        pass# Last row should stay the same
                                
                                FocusCorrectionMatrixContainer = copy.deepcopy(FocusCorrectionMatrixContainer)
                                FocusCorrectionMatrixContainer += self.FocusCorrectionOffsetBox.value()
        #                        FocusCorrectionMatrixContainer = FocusCorrectionMatrixContainer.flatten()
                                
        #                        print(FocusCorrectionMatrixContainer.shape)
                                self.FocusCorrectionMatrixDict['RoundPackage_{}_Grid_{}'.format(CurrentRound+1, EachGrid)] = FocusCorrectionMatrixContainer               
                                print(self.FocusCorrectionMatrixDict['RoundPackage_{}_Grid_{}'.format(CurrentRound+1, EachGrid)])
                                
                    elif len(self.FocusDuplicateMethodInfor['Grid_{}'.format(EachGrid)][0,:]) == 1:
                        RawDuplicateFocus = self.FocusDuplicateMethodInfor['Grid_{}'.format(EachGrid)][2,:]

                        for CurrentRound in range(len(self.RoundCoordsDict)):
                            
                            if len(self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRound+1)]) > 2: # If it's more than 1 pos.
                                #---------------numpy.meshgrid method------------------------
                                OriginalCoordsPackage = self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRound+1)]
                                
                                Originalstep = OriginalCoordsPackage[3] - OriginalCoordsPackage[1]
                                
                                OriginalCoordsOdd_Row = OriginalCoordsPackage[::2]
                                OriginalCoordsEven_Col = OriginalCoordsPackage[1::2]
                                
                                row_start = np.amin(OriginalCoordsOdd_Row)
                                row_end = np.amax(OriginalCoordsOdd_Row)
                                
                                column_start = np.amin(OriginalCoordsEven_Col)
                                column_end = np.amax(OriginalCoordsEven_Col)     
                                
                                linspace_num_x = int((row_end-row_start)/Originalstep)+1
                                linspace_num_y = int((column_end-column_start)/Originalstep)+1
                                X = np.linspace(row_start,row_end,linspace_num_x)
                                Y = np.linspace(column_start,column_end,linspace_num_y)
                                
                                ExeRowIndex, ExeColIndex = np.meshgrid(X,Y)
                                
                                FocusCorrectionMatrixContainer = RawDuplicateFocus[0]*np.ones((len(Y), len(X)))
                                
                                FocusCorrectionMatrixContainer = copy.deepcopy(FocusCorrectionMatrixContainer)
                                FocusCorrectionMatrixContainer += self.FocusCorrectionOffsetBox.value()
        #                        FocusCorrectionMatrixContainer = FocusCorrectionMatrixContainer.flatten()
                                
        #                        print(FocusCorrectionMatrixContainer.shape)
                                self.FocusCorrectionMatrixDict['RoundPackage_{}_Grid_{}'.format(CurrentRound+1, EachGrid)] = FocusCorrectionMatrixContainer               
                                print(self.FocusCorrectionMatrixDict['RoundPackage_{}_Grid_{}'.format(CurrentRound+1, EachGrid)])
        else:
            self.FocusCorrectionMatrixDict = {}
            
        generalnamelist = ['savedirectory', 'FocusCorrectionMatrixDict', 'FocusStackInfoDict', 'Meshgrid', 'Scanning step', 'StartUpEvents']
        
        generallist = [savedirectory, self.FocusCorrectionMatrixDict, self.FocusStackInfoDict, meshrepeat, self.step, StartUpEvents]
        
        for item in range(len(generallist)):
            self.GeneralSettingDict[generalnamelist[item]] = generallist[item]
#        print(self.GeneralSettingDict['FocusStackInfoDict'])
        self.normalOutputWritten('Rounds configured.\n')
        
        #---------------------------------------------------------------Show general info---------------------------------------------------------------------------------
        self.normalOutputWritten('--------Pipeline general info--------\n')
        for eachround in range(int(len(self.RoundQueueDict)/2-1)):
            
            waveformPackage = self.RoundQueueDict['RoundPackage_'+str(eachround+1)][0]
            camOperationPackage = self.RoundQueueDict['RoundPackage_'+str(eachround+1)][1]
            waveform_sequence = 1
            
            for eachwaveform in waveformPackage:
                
                #--------------------------------------------------------------
                # show waveform settings
                
                try:
                    if len(waveformPackage[eachwaveform][3]) != 0:
                        self.normalOutputWritten('Round {}, sequence {}, recording channels:{}.\n'.format(eachround+1, waveform_sequence, waveformPackage[eachwaveform][3]))
                        print('Round {}, recording channels:{}.'.format(eachround+1, waveformPackage[eachwaveform][3]))#[1]['Sepcification']
#                    else:
#                        self.normalOutputWritten('Round {} No recording channel.\n'.format(eachround+1))
                except:
                    
                    self.normalOutputWritten('No recording channel.\n')
                    print(waveformPackage[eachwaveform][3])
                    print('No recording channel.')
                    
                try:
                    self.normalOutputWritten('Round {}, Analog signals:{}.\n'.format(eachround+1, waveformPackage[eachwaveform][1]['Sepcification']))
                    print('Round {}, Analog signals:{}.'.format(eachround+1, waveformPackage[eachwaveform][1]['Sepcification']))#
                except:
                    self.normalOutputWritten('No Analog signals.\n')
                    print('No Analog signals.')
                    
                try:
                    if len(waveformPackage[eachwaveform][2]['Sepcification']) != 0:
                        self.normalOutputWritten('Round {}, Digital signals:{}.\n'.format(eachround+1, waveformPackage[eachwaveform][2]['Sepcification']))
                        print('Round {}, Digital signals:{}.'.format(eachround+1, waveformPackage[eachwaveform][2]['Sepcification']))#
#                    else:
#                        self.normalOutputWritten('Round {} No Digital signals.\n'.format(eachround+1))
                except:
                    self.normalOutputWritten('No Digital signals.\n')
                    print('No Digital signals.')
                waveform_sequence += 1
                self.normalOutputWritten('\n')
                
            for eachcamoperation in camOperationPackage:
                #--------------------------------------------------------------
                # Show camera operations
               
                try:
                    if len(camOperationPackage[eachcamoperation]) != 0:
                        self.normalOutputWritten('Round {}, cam Buffer_number:{}.\n'.format(eachround+1, camOperationPackage[eachcamoperation]['Buffer_number']))
                        print('Round {}, cam Buffer_number:{}.\n'.format(eachround+1, camOperationPackage[eachcamoperation]['Buffer_number']))#
#                    else:
#                        self.normalOutputWritten('Round {} No Digital signals.\n'.format(eachround+1))
                except:
                    self.normalOutputWritten('No camera operations.\n')
                    print('No camera operations.')                    
            
            self.normalOutputWritten('-----------end of round-----------\n')
            
        self.normalOutputWritten('----------------------------------------\n')
        
        
    def _open_file_dialog(self):
        self.savedirectory = str(QtWidgets.QFileDialog.getExistingDirectory(directory='M:/tnw/ist/do/projects/Neurophotonics/Brinkslab/Data'))
        self.savedirectorytextbox.setText(self.savedirectory)
        self.set_prefix()
    
    def update_saving_directory(self):
        self.savedirectory = str(self.savedirectorytextbox.text())
        
    def set_prefix(self):
        self.saving_prefix = str(self.prefixtextbox.text())
        
    #--------------------------------------------------------------------GenerateFocusCorrectionMatrix-----------------------------------------
    def CaptureFocusCorrectionMatrix(self, CorrectionFomula):
        self.CorrectionFomula = CorrectionFomula
        
    def CaptureFocusDuplicateMethodMatrix(self, CorrectionDictForDuplicateMethod):
        self.FocusDuplicateMethodInfor = CorrectionDictForDuplicateMethod
        
    def ExecutePipeline(self):
        get_ipython().run_line_magic('matplotlib', 'inline') # before start, set spyder back to inline
        
        self.ExecuteThreadInstance = ScanningExecutionThread(self.RoundQueueDict, self.RoundCoordsDict, self.GeneralSettingDict)
#        self.ExecuteThreadInstance.ScanningResult.connect(self.GetDataForShowingRank)
        self.ExecuteThreadInstance.start()
        
    def Savepipeline(self):
        SavepipelineInstance = []
        SavepipelineInstance.extend([self.RoundQueueDict, self.RoundCoordsDict, self.GeneralSettingDict])
        
        np.save(os.path.join(self.savedirectory, self.saving_prefix, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_Pipeline'), SavepipelineInstance)
        
        
    def GetDataForShowingRank(self, RankedAllCellProperties, FinalMergedCoords, IndexLookUpCellPropertiesDict, PMTimageDict):
        
        self.RankedAllCellProperties = RankedAllCellProperties
        self.FinalMergedCoords = FinalMergedCoords # Stage coordinates of the top cells with same ones merged together.
        self.IndexLookUpCellPropertiesDict = IndexLookUpCellPropertiesDict
        self.PMTimageDict = PMTimageDict
        
        self.TotalCoordsNum = len(self.FinalMergedCoords)
        
        self.TopGeneralInforLabel.setText('Number of coords in total: {}'.format(self.TotalCoordsNum))

#    def PopNextTopCells(self, direction):       
#        if direction == 'next':
#            if self.popnexttopimgcounter > (self.TotalCoordsNum-1):#Make sure it doesn't go beyond the last coords.
#                self.popnexttopimgcounter -= 1
#            CurrentPosIndex = self.FinalMergedCoords[self.popnexttopimgcounter,:].tolist() # self.popnexttopimgcounter is the order number of each Stage coordinates.
#            
#            self.TopCoordsLabel.setText("Row: {} Col: {}".format(CurrentPosIndex[0], CurrentPosIndex[1]))     
#            self.CurrentImgShowTopCells = self.PMTimageDict['RoundPackage_{}'.format(self.GeneralSettingDict['BefRoundNum'])]['row_{}_column_{}'.format(CurrentPosIndex[0], CurrentPosIndex[1])]
#            self.ShowTopCellsInstance = ShowTopCellsThread(self.GeneralSettingDict, self.RankedAllCellProperties, CurrentPosIndex, 
#                                                           self.IndexLookUpCellPropertiesDict, self.CurrentImgShowTopCells, self.Matdisplay_Figure)
#            self.ShowTopCellsInstance.run()
#    #        self.ax = self.ShowTopCellsInstance.gg()
#    #        self.ax = self.Matdisplay_Figure.add_subplot(111)
#            self.Matdisplay_Canvas.draw()
##            if self.popnexttopimgcounter < (self.TotalCoordsNum-1):
#            self.popnexttopimgcounter += 1 # Alwasy plus 1 to get it ready for next move.
#            
#        elif direction == 'previous':
#            self.popnexttopimgcounter -= 2 
#            if self.popnexttopimgcounter >= 0:
#                CurrentPosIndex = self.FinalMergedCoords[self.popnexttopimgcounter,:].tolist() # self.popnexttopimgcounter is the order number of each Stage coordinates.
#                
#                self.TopCoordsLabel.setText("Row: {} Col: {}".format(CurrentPosIndex[0], CurrentPosIndex[1]))     
#                self.CurrentImgShowTopCells = self.PMTimageDict['RoundPackage_{}'.format(self.GeneralSettingDict['BefRoundNum'])]['row_{}_column_{}'.format(CurrentPosIndex[0], CurrentPosIndex[1])]
#                self.ShowTopCellsInstance = ShowTopCellsThread(self.GeneralSettingDict, self.RankedAllCellProperties, CurrentPosIndex, 
#                                                               self.IndexLookUpCellPropertiesDict, self.CurrentImgShowTopCells, self.Matdisplay_Figure)
#                self.ShowTopCellsInstance.run()
#        #        self.ax = self.ShowTopCellsInstance.gg()
#        #        self.ax = self.Matdisplay_Figure.add_subplot(111)
#                self.Matdisplay_Canvas.draw()
#                if self.popnexttopimgcounter < (self.TotalCoordsNum-1):
#                    self.popnexttopimgcounter += 1
#            else:
#                self.popnexttopimgcounter = 0
    #%%
    """
    # =============================================================================
    #     For save and load file.    
    # =============================================================================
    """
    def GetPipelineNPFile(self):
        self.pipelinenpfileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Single File', 'M:/tnw/ist/do/projects/Neurophotonics/Brinkslab/Data',"(*.npy)")
        self.LoadPipelineAddressbox.setText(self.pipelinenpfileName)
        
    def LoadPipelineFile(self):
        temp_loaded_container = np.load(self.pipelinenpfileName, allow_pickle=True)
        self.RoundQueueDict = temp_loaded_container[0]
        self.RoundCoordsDict = temp_loaded_container[1]
        self.GeneralSettingDict = temp_loaded_container[2]

        #--------------------------------------------------------Generate the focus correction matrix-----------------------------------------------------------
        if self.ApplyFocusSetCheckbox.isChecked():
            self.FocusCorrectionMatrixDict = {}
            if self.FocusInterStrategy.currentText() == 'Interpolation':
            
                for CurrentRound in range(len(self.RoundCoordsDict)):
                    
                    if len(self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRound+1)]) > 2: # If it's more than 1 pos.
                        #---------------numpy.meshgrid method------------------------
                        OriginalCoordsPackage = self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRound+1)]
                        
                        step = OriginalCoordsPackage[3] - OriginalCoordsPackage[1]
                        
                        OriginalCoordsOdd_Row = OriginalCoordsPackage[::2]
                        OriginalCoordsEven_Col = OriginalCoordsPackage[1::2]
                        
                        row_start = np.amin(OriginalCoordsOdd_Row)
                        row_end = np.amax(OriginalCoordsOdd_Row)
                        
                        column_start = np.amin(OriginalCoordsEven_Col)
                        column_end = np.amax(OriginalCoordsEven_Col)     
                        
                        linspace_num = int((row_end-row_start)/step)+1
                        X = np.linspace(row_start,row_end,linspace_num)
                        Y = np.linspace(column_start,column_end,linspace_num)
        #                ExeColumnIndex, ExeRowIndex = np.meshgrid(X,Y)
        #                
        #                self.ExeColumnIndexMeshgrid = ExeColumnIndex.astype(int)
        #                self.ExeRowIndexMeshgrid = ExeRowIndex.astype(int)
                        
                        self.FocusCorrectionMatrix = self.CorrectionFomula(X, Y)
                        
                        self.FocusCorrectionMatrix = self.FocusCorrectionMatrix.flatten()
                        print(self.FocusCorrectionMatrix)
                        
                        FocusCorrectionMatrix = copy.deepcopy(self.FocusCorrectionMatrix)
                        FocusCorrectionMatrix += self.FocusCorrectionOffsetBox.value()
                        self.FocusCorrectionMatrixDict['RoundPackage_{}'.format(CurrentRound+1)] = FocusCorrectionMatrix
    
                    else:
                        self.FocusCorrectionMatrix = self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRound+1)]
                        FocusCorrectionMatrix = copy.deepcopy(self.FocusCorrectionMatrix)
                        
                        FocusCorrectionMatrix += self.FocusCorrectionOffsetBox.value()
                        
                        self.FocusCorrectionMatrixDict['RoundPackage_{}'.format(CurrentRound+1)] = FocusCorrectionMatrix
                        
                        
            elif self.FocusInterStrategy.currentText() == 'Duplicate':
                meshrepeat = self.ScanRepeatTextbox.value()
                for EachGrid in range(meshrepeat**2):
                    if len(self.FocusDuplicateMethodInfor['Grid_{}'.format(EachGrid)][0,:]) > 1:
                        RawDuplicateRow = self.FocusDuplicateMethodInfor['Grid_{}'.format(EachGrid)][0,:] # The row index from calibration step (Corresponding to column index in python array)
                        RawDuplicateCol = self.FocusDuplicateMethodInfor['Grid_{}'.format(EachGrid)][1,:]
                        RawDuplicateFocus = self.FocusDuplicateMethodInfor['Grid_{}'.format(EachGrid)][2,:]
                        sparsestep = RawDuplicateCol[1] - RawDuplicateCol[0]
                        print('sparse step {}'.format(sparsestep))
                        for CurrentRound in range(len(self.RoundCoordsDict)):
                            
                            if len(self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRound+1)]) > 2: # If it's more than 1 pos.
                                #---------------numpy.meshgrid method------------------------
                                OriginalCoordsPackage = self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRound+1)]
                                
                                Originalstep = OriginalCoordsPackage[3] - OriginalCoordsPackage[1]
                                
                                OriginalCoordsOdd_Row = OriginalCoordsPackage[::2]
                                OriginalCoordsEven_Col = OriginalCoordsPackage[1::2]
                                
                                row_start = np.amin(OriginalCoordsOdd_Row)
                                row_end = np.amax(OriginalCoordsOdd_Row)
                                
                                column_start = np.amin(OriginalCoordsEven_Col)
                                column_end = np.amax(OriginalCoordsEven_Col)     
                                
                                linspace_num_x = int((row_end-row_start)/Originalstep)+1
                                linspace_num_y = int((column_end-column_start)/Originalstep)+1
                                X = np.linspace(row_start,row_end,linspace_num_x)
                                Y = np.linspace(column_start,column_end,linspace_num_y)
                                
                                ExeRowIndex, ExeColIndex = np.meshgrid(X,Y)
                                
                                FocusCorrectionMatrixContainer = RawDuplicateFocus[0]*np.ones((len(Y), len(X)))
         
                                c = int(sparsestep/Originalstep)
                                print('RawDuplicateFocus'+str(RawDuplicateFocus))
        #                        print(FocusCorrectionMatrixContainer)
                                for i in range(len(RawDuplicateRow)):
                                    row = int(RawDuplicateRow[i]/sparsestep)
                                    col = int(RawDuplicateCol[i]/sparsestep)
                                    
                                    print('row{},col{}'.format(row, col))
                                    
                                    try:    
                                        FocusCorrectionMatrixContainer[col*c:col*c+c, row*c:row*c+c] = RawDuplicateFocus[i]
                                    except:
                                        pass# Last row should stay the same
                                
                                FocusCorrectionMatrixContainer = copy.deepcopy(FocusCorrectionMatrixContainer)
                                FocusCorrectionMatrixContainer += self.FocusCorrectionOffsetBox.value()
        #                        FocusCorrectionMatrixContainer = FocusCorrectionMatrixContainer.flatten()
                                
                                self.FocusCorrectionMatrixDict['RoundPackage_{}_Grid_{}'.format(CurrentRound+1, EachGrid)] = FocusCorrectionMatrixContainer               
                                print(self.FocusCorrectionMatrixDict['RoundPackage_{}_Grid_{}'.format(CurrentRound+1, EachGrid)])
                                
                    elif len(self.FocusDuplicateMethodInfor['Grid_{}'.format(EachGrid)][0,:]) == 1:
                        RawDuplicateFocus = self.FocusDuplicateMethodInfor['Grid_{}'.format(EachGrid)][2,:]

                        for CurrentRound in range(len(self.RoundCoordsDict)):
                            
                            if len(self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRound+1)]) > 2: # If it's more than 1 pos.
                                #---------------numpy.meshgrid method------------------------
                                OriginalCoordsPackage = self.RoundCoordsDict['CoordsPackage_{}'.format(CurrentRound+1)]
                                
                                Originalstep = OriginalCoordsPackage[3] - OriginalCoordsPackage[1]
                                
                                OriginalCoordsOdd_Row = OriginalCoordsPackage[::2]
                                OriginalCoordsEven_Col = OriginalCoordsPackage[1::2]
                                
                                row_start = np.amin(OriginalCoordsOdd_Row)
                                row_end = np.amax(OriginalCoordsOdd_Row)
                                
                                column_start = np.amin(OriginalCoordsEven_Col)
                                column_end = np.amax(OriginalCoordsEven_Col)     
                                
                                linspace_num_x = int((row_end-row_start)/Originalstep)+1
                                linspace_num_y = int((column_end-column_start)/Originalstep)+1
                                X = np.linspace(row_start,row_end,linspace_num_x)
                                Y = np.linspace(column_start,column_end,linspace_num_y)
                                
                                ExeRowIndex, ExeColIndex = np.meshgrid(X,Y)
                                
                                FocusCorrectionMatrixContainer = RawDuplicateFocus[0]*np.ones((len(Y), len(X)))
                                
                                FocusCorrectionMatrixContainer = copy.deepcopy(FocusCorrectionMatrixContainer)
                                FocusCorrectionMatrixContainer += self.FocusCorrectionOffsetBox.value()
        #                        FocusCorrectionMatrixContainer = FocusCorrectionMatrixContainer.flatten()
                                
        #                        print(FocusCorrectionMatrixContainer.shape)
                                self.FocusCorrectionMatrixDict['RoundPackage_{}_Grid_{}'.format(CurrentRound+1, EachGrid)] = FocusCorrectionMatrixContainer               
                                print(self.FocusCorrectionMatrixDict['RoundPackage_{}_Grid_{}'.format(CurrentRound+1, EachGrid)])
        else:
            self.FocusCorrectionMatrixDict = {}
        
        self.GeneralSettingDict['FocusCorrectionMatrixDict'] = self.FocusCorrectionMatrixDict # Refresh the focus correction
        self.GeneralSettingDict['savedirectory'] = self.savedirectory
        
        self.normalOutputWritten('Pipeline loaded.\n')
        print('Pipeline loaded.')
        
        #---------------------------------------------------------------Show general info---------------------------------------------------------------------------------
        self.normalOutputWritten('--------Pipeline general info--------\n')
        for eachround in range(int(len(self.RoundQueueDict)/2-1)):

            #--------------------------------------------------------------
            # show waveform settings
            waveformPackage = self.RoundQueueDict['RoundPackage_'+str(eachround+1)][0]
            camOperationPackage = self.RoundQueueDict['RoundPackage_'+str(eachround+1)][1]
            waveform_sequence = 1
            
            for eachwaveform in waveformPackage:
                try:
                    if len(waveformPackage[eachwaveform][3]) != 0:
                        self.normalOutputWritten('Round {}, sequence {}, recording channels:{}.\n'.format(eachround+1, waveform_sequence, waveformPackage[eachwaveform][3]))
                        print('Round {}, recording channels:{}.'.format(eachround+1, waveformPackage[eachwaveform][3]))#[1]['Sepcification']
#                    else:
#                        self.normalOutputWritten('Round {} No recording channel.\n'.format(eachround+1))
                except:
                    self.normalOutputWritten('No recording channel.\n')
                    print('No recording channel.')
                try:
                    self.normalOutputWritten('Round {}, Analog signals:{}.\n'.format(eachround+1, waveformPackage[eachwaveform][1]['Sepcification']))
                    print('Round {}, Analog signals:{}.'.format(eachround+1, waveformPackage[eachwaveform][1]['Sepcification']))#
                except:
                    self.normalOutputWritten('No Analog signals.\n')
                    print('No Analog signals.')
                try:
                    if len(waveformPackage[2]['Sepcification']) != 0:
                        self.normalOutputWritten('Round {}, Digital signals:{}.\n'.format(eachround+1, waveformPackage[eachwaveform][2]['Sepcification']))
                        self.normalOutputWritten('Lasting time:{} s.\n'.format(len(waveformPackage[eachwaveform][2]['Waveform'][0])/waveformPackage[eachwaveform][0]))
                        
                        print('Lasting time:{} s.\n'.format(len(waveformPackage[eachwaveform][2]['Waveform'][0])/waveformPackage[eachwaveform][0]))
                        print('Round {}, Digital signals:{}.'.format(eachround+1, waveformPackage[eachwaveform][2]['Sepcification']))#
#                    else:
#                        self.normalOutputWritten('Round {} No Digital signals.\n'.format(eachround+1))
                except:
                    self.normalOutputWritten('No Digital signals.\n')
                    print('No Digital signals.')
                waveform_sequence += 1
                self.normalOutputWritten('\n')
                
            for eachcamoperation in camOperationPackage:
                #--------------------------------------------------------------
                # Show camera operations
               
                try:
                    if len(camOperationPackage[eachcamoperation]) != 0:
                        self.normalOutputWritten('Round {}, cam Buffer_number:{}.\n'.format(eachround+1, camOperationPackage[eachcamoperation]['Buffer_number']))
                        print('Round {}, cam Buffer_number:{}.\n'.format(eachround+1, camOperationPackage[eachcamoperation]['Buffer_number']))#
#                    else:
#                        self.normalOutputWritten('Round {} No Digital signals.\n'.format(eachround+1))
                except:
                    self.normalOutputWritten('No camera operations.\n')
                    print('No camera operations.')  
            
            self.normalOutputWritten('-----------end of round-----------\n')
        self.normalOutputWritten('----------------------------------------\n')
        
    #---------------------------------------------------------------functions for console display------------------------------------------------------------        
    def normalOutputWritten(self, text):
        """Append text to the QTextEdit."""
        # Maybe QTextEdit.append() works as well, but this is how I do it:
        cursor = self.ConsoleTextDisplay.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.ConsoleTextDisplay.setTextCursor(cursor)
        self.ConsoleTextDisplay.ensureCursorVisible()  
    #%%
    """
    # =============================================================================
    #     FUNCTIONS FOR TOOL WIDGETS
    # =============================================================================
    """            
    def openPMTWidget(self):
        self.pmtWindow = GalvoWidget.PMTWidget.PMTWidgetUI()
        self.pmtWindow.show()
        
    def openAOTFWidget(self):
        self.AOTFWindow = NIDAQ.AOTFWidget.AOTFWidgetUI()
        self.AOTFWindow.show()
        
    def openFilterSliderWidget(self):
        self.FilterSliderWindow = ThorlabsFilterSlider.FilterSliderWidget.FilterSliderWidgetUI()
        self.FilterSliderWindow.show()
        
    def openInsightWidget(self):
        self.InsightWindow = InsightX3.TwoPhotonLaserUI.InsightWidgetUI()
        self.InsightWindow.show()
        
    def openScreenAnalysisWidget(self):
        from ImageAnalysis import EvolutionAnalysisGUI_ML
        
        self.ScreenAnalysisWindow = EvolutionAnalysisGUI.MainGUI()
        self.ScreenAnalysisWindow.show()
        
    def openScreenAnalysisMLWidget(self):
        from ImageAnalysis import EvolutionAnalysisGUI_ML
        
        self.ScreenAnalysisMLWindow = EvolutionAnalysisGUI_ML.MainGUI()
        self.ScreenAnalysisMLWindow.show()
        
    def execute_tread_single_sample_digital(self, channel):
        if channel == 'LED':
            if self.switchbutton_LED.isChecked():
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 1)
                execute_tread_singlesample_AOTF_digital.start()
            else:
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 0)
                execute_tread_singlesample_AOTF_digital.start()
    
    def closeEvent(self, event):
        QtWidgets.QApplication.quit()
        event.accept()
    #%%
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        QtWidgets.QApplication.setStyle(QStyleFactory.create('Fusion'))
        stylesheet = '.\Icons\gui_style.qss'
#        with open(stylesheet,"r") as style:
#              app.setStyleSheet(style.read())
        mainwin = Mainbody()
        mainwin.show()
        app.exec_()
    run_app()
