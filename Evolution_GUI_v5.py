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
                             QFileDialog, QProgressBar, QTextEdit)

import pyqtgraph as pg
from IPython import get_ipython
import sys
import numpy as np
from NIDAQ.code_5nov import generate_AO
from GalvoWidget.pmt_thread import pmtimagingTest, pmtimagingTest_contour
#from Stagemovement_Thread import StagemovementThread
from ThorlabsFilterSlider.Filtermovement_Thread import FiltermovementThread
from NIDAQ.constants import MeasurementConstants
from Oldversions.generalDaqer import execute_constant_vpatch
from Oldversions.generalDaqer import execute_analog_readin_optional_digital, execute_digital
from NIDAQ.generalDaqerThread import (execute_analog_readin_optional_digital_thread, execute_tread_singlesample_analog,
                                execute_tread_singlesample_digital, execute_analog_and_readin_digital_optional_camtrig_thread, DaqProgressBar)
from PIL import Image
from NIDAQ.adfunctiongenerator import (generate_AO_for640, generate_AO_for488, generate_DO_forcameratrigger, generate_DO_for640blanking,
                                 generate_AO_for532, generate_AO_forpatch, generate_DO_forblankingall, generate_DO_for532blanking,
                                 generate_DO_for488blanking, generate_DO_forPerfusion, generate_DO_for2Pshutter, generate_ramp)
from pyqtgraph import PlotDataItem, TextItem
import os
import copy
import scipy.signal as sg
from scipy import interpolate
import time
from datetime import datetime
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from NIDAQ.constants import HardwareConstants
import NIDAQ.Waveformer_for_screening
from EvolutionScanningThread import ScanningExecutionThread, ShowTopCellsThread # This is the thread file for execution.
import FocusCalibrater

class Mainbody(QWidget):
    
    waveforms_generated = pyqtSignal(object, object, list, int)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        os.chdir('./')# Set directory to current folder.
        self.setFont(QFont("Arial"))
        
        self.setMinimumSize(1080,1920)
        self.setWindowTitle("McDonnell")
        self.layout = QGridLayout(self)
        
        self.WaveformQueueDict = {}
        self.RoundQueueDict = {}
        self.RoundCoordsDict = {}
        self.WaveformQueueDict_GalvoInfor = {}
        self.GeneralSettingDict = {}
        self.FocusCorrectionMatrixDict = {}
        self.FocusStackInfoDict = {}
        self.popnexttopimgcounter = 0

        
        self.savedirectory = './'
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for GeneralSettings----------------------------------------------------
        #**************************************************************************************************************************************
        GeneralSettingContainer = QGroupBox("Tanto Tanto")
        GeneralSettingContainerLayout = QGridLayout()
        
        self.saving_prefix = ''
        self.savedirectorytextbox = QtWidgets.QLineEdit(self)
        self.savedirectorytextbox.setFixedWidth(300)
        GeneralSettingContainerLayout.addWidget(self.savedirectorytextbox, 0, 1)
        
        self.prefixtextbox = QtWidgets.QLineEdit(self)
        self.prefixtextbox.setPlaceholderText('Prefix')
        self.prefixtextbox.setFixedWidth(80)
        GeneralSettingContainerLayout.addWidget(self.prefixtextbox, 0, 2)
        
        self.toolButtonOpenDialog = QtWidgets.QPushButton('Saving directory')
        self.toolButtonOpenDialog.setStyleSheet("QPushButton {color:white;background-color: pink; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                                "QPushButton:pressed {color:yellow;background-color: pink; border-style: outset;border-radius: 3px;border-width: 2px;font: bold 14px;padding: 1px}")

        self.toolButtonOpenDialog.setObjectName("toolButtonOpenDialog")
        self.toolButtonOpenDialog.clicked.connect(self._open_file_dialog)
        
        GeneralSettingContainerLayout.addWidget(self.toolButtonOpenDialog, 0, 0)
        
        ButtonConfigurePipeline = QPushButton('Configure', self)
        ButtonConfigurePipeline.setStyleSheet("QPushButton {color:white;background-color: rgb(184,184,243); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        ButtonConfigurePipeline.clicked.connect(self.ConfigGeneralSettings)
#        ButtonConfigurePipeline.clicked.connect(self.GenerateFocusCorrectionMatrix)
        
        ButtonExePipeline = QPushButton('Execute', self)
        ButtonExePipeline.setStyleSheet("QPushButton {color:white;background-color: rgb(184,184,243); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
#        ButtonExePipeline.clicked.connect(self.ConfigGeneralSettings)      
        ButtonExePipeline.clicked.connect(self.ExecutePipeline)
        
        ButtonSavePipeline = QPushButton('Save pipeline', self)
        ButtonSavePipeline.setStyleSheet("QPushButton {color:white;background-color: rgb(82,153,211); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        ButtonSavePipeline.clicked.connect(self.Savepipeline)
        
        # Pipeline import
        self.LoadPipelineAddressbox = QLineEdit(self)    
        self.LoadPipelineAddressbox.setFixedWidth(300)
        GeneralSettingContainerLayout.addWidget(self.LoadPipelineAddressbox, 1, 1)
        
        self.BrowsePipelineButton = QPushButton('Browse pipeline', self)
        self.BrowsePipelineButton.setStyleSheet("QPushButton {color:white;background-color:rgb(143,191,224); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                                "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        
        GeneralSettingContainerLayout.addWidget(self.BrowsePipelineButton, 1, 0) 
        
        self.BrowsePipelineButton.clicked.connect(self.GetPipelineNPFile)
        
        GeneralSettingContainerLayout.addWidget(QLabel('Configure focus correction first.'), 1, 2)
        
        self.ImportPipelineButton = QPushButton('Load', self)
        self.ImportPipelineButton.setStyleSheet("QPushButton {color:white;background-color: rgb(191,216,189); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                                "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        

        GeneralSettingContainerLayout.addWidget(self.ImportPipelineButton, 1, 3)
        self.ImportPipelineButton.clicked.connect(self.LoadPipelineFile)
        
        GeneralSettingContainerLayout.addWidget(ButtonConfigurePipeline, 0, 3)        
        GeneralSettingContainerLayout.addWidget(ButtonExePipeline, 0, 4)
        GeneralSettingContainerLayout.addWidget(ButtonSavePipeline, 0, 5)    
        GeneralSettingContainer.setLayout(GeneralSettingContainerLayout)
        
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for Focus correction---------------------------------------------------
        #**************************************************************************************************************************************
        FocusCorrectionContainer = QGroupBox("Focus correction")
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

        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for Billboard display------------------------------------------------------
        #**************************************************************************************************************************************
        ImageDisplayContainer = QGroupBox("Billboard")
        ImageDisplayContainerLayout = QGridLayout()        
        # a figure instance to plot on
        self.MatdisplayFigureTopGuys = Figure()
        self.MatdisplayCanvasTopGuys = FigureCanvas(self.MatdisplayFigureTopGuys)

        ImageDisplayContainerLayout.addWidget(self.MatdisplayCanvasTopGuys, 0, 1, 5, 5)
        
        self.TopCoordsLabel = QLabel("Row:      Col:      ")
        ImageDisplayContainerLayout.addWidget(self.TopCoordsLabel, 0, 6)
        
        self.TopGeneralInforLabel = QLabel("  ")
        ImageDisplayContainerLayout.addWidget(self.TopGeneralInforLabel, 1, 6)        
        
        ButtonRankPreviousCoordImg = QPushButton('Previous', self)
        ButtonRankPreviousCoordImg.setStyleSheet("QPushButton {color:white;background-color: rgb(191,216,189); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                             "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        

        ButtonRankPreviousCoordImg.clicked.connect(lambda: self.PopNextTopCells('previous'))
        ImageDisplayContainerLayout.addWidget(ButtonRankPreviousCoordImg, 0, 7)
        
        ButtonRankNextCoordImg = QPushButton('Next', self)
        ButtonRankNextCoordImg.setStyleSheet("QPushButton {color:white;background-color: teal; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                             "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        

        ButtonRankNextCoordImg.clicked.connect(lambda: self.PopNextTopCells('next'))
        ImageDisplayContainerLayout.addWidget(ButtonRankNextCoordImg, 1, 7)
        
        self.ConsoleTextDisplay = QTextEdit()
        self.ConsoleTextDisplay.setFontItalic(True)
        self.ConsoleTextDisplay.setPlaceholderText('Notice board from console.')
        self.ConsoleTextDisplay.setMaximumHeight(200)
        ImageDisplayContainerLayout.addWidget(self.ConsoleTextDisplay, 3, 6, 2, 2)
        
        
        ImageDisplayContainer.setLayout(ImageDisplayContainerLayout)
        ImageDisplayContainer.setMinimumHeight(400)
        ImageDisplayContainer.setMinimumWidth(600)
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for Selection settings Container---------------------------------------
        #**************************************************************************************************************************************
        SelectionsettingContainer = QGroupBox("Selection settings")
        SelectionsettingLayout = QGridLayout()
        
        self.selec_num_box = QSpinBox(self)
        self.selec_num_box.setMaximum(2000)
        self.selec_num_box.setValue(10)
        self.selec_num_box.setSingleStep(1)
        SelectionsettingLayout.addWidget(self.selec_num_box, 0, 1)
        SelectionsettingLayout.addWidget(QLabel("Winners number:"), 0, 0)
        
        self.ComBoxSelectionFactor_1 = QComboBox()
        self.ComBoxSelectionFactor_1.addItems(['Mean intensity in contour weight','Contour soma ratio weight','Change weight'])
        SelectionsettingLayout.addWidget(self.ComBoxSelectionFactor_1, 0, 2)
        
        self.WeightBoxSelectionFactor_1 = QDoubleSpinBox(self)
        self.WeightBoxSelectionFactor_1.setDecimals(4)
        self.WeightBoxSelectionFactor_1.setMinimum(0)
        self.WeightBoxSelectionFactor_1.setMaximum(1)
        self.WeightBoxSelectionFactor_1.setValue(0.5)
        self.WeightBoxSelectionFactor_1.setSingleStep(0.1)  
        SelectionsettingLayout.addWidget(self.WeightBoxSelectionFactor_1, 0, 3)
        
        self.ComBoxSelectionFactor_2 = QComboBox()
        self.ComBoxSelectionFactor_2.addItems(['Contour soma ratio weight', 'Mean intensity in contour weight','Change weight'])
        SelectionsettingLayout.addWidget(self.ComBoxSelectionFactor_2, 0, 4)
        
        self.WeightBoxSelectionFactor_2 = QDoubleSpinBox(self)
        self.WeightBoxSelectionFactor_2.setDecimals(4)
        self.WeightBoxSelectionFactor_2.setMinimum(0)
        self.WeightBoxSelectionFactor_2.setMaximum(1)
        self.WeightBoxSelectionFactor_2.setValue(0.5)
        self.WeightBoxSelectionFactor_2.setSingleStep(0.1)  
        SelectionsettingLayout.addWidget(self.WeightBoxSelectionFactor_2, 0, 5)
        
        self.ComBoxSelectionFactor_3 = QComboBox()
        self.ComBoxSelectionFactor_3.addItems(['Change weight', 'Mean intensity in contour weight','Contour soma ratio weight'])
        SelectionsettingLayout.addWidget(self.ComBoxSelectionFactor_3, 0, 6)
        
        self.WeightBoxSelectionFactor_3 = QDoubleSpinBox(self)
        self.WeightBoxSelectionFactor_3.setDecimals(4)
        self.WeightBoxSelectionFactor_3.setMinimum(0)
        self.WeightBoxSelectionFactor_3.setMaximum(1)
        self.WeightBoxSelectionFactor_3.setValue(0.0)
        self.WeightBoxSelectionFactor_3.setSingleStep(0.1)  
        SelectionsettingLayout.addWidget(self.WeightBoxSelectionFactor_3, 0, 7)
        
        SelectionsettingContainer.setLayout(SelectionsettingLayout)

        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for PiplineContainer---------------------------------------------------
        #**************************************************************************************************************************************
        ImageProcessingContainer = QGroupBox("Image processing settings")
        IPLayout = QGridLayout()
        
        self.IPsizetextbox = QComboBox()
        self.IPsizetextbox.addItems(['200','100'])
        IPLayout.addWidget(self.IPsizetextbox, 1, 7)
        IPLayout.addWidget(QLabel("Smallest size:"), 1, 6)
        
        self.opening_factorBox = QSpinBox(self)
        self.opening_factorBox.setMaximum(2000)
        self.opening_factorBox.setValue(2)
        self.opening_factorBox.setSingleStep(1)
        IPLayout.addWidget(self.opening_factorBox, 2, 5)
        IPLayout.addWidget(QLabel("Mask opening factor:"), 2, 4)
        
        self.closing_factorBox = QSpinBox(self)
        self.closing_factorBox.setMaximum(2000)
        self.closing_factorBox.setValue(2)
        self.closing_factorBox.setSingleStep(1)
        IPLayout.addWidget(self.closing_factorBox, 2, 7)
        IPLayout.addWidget(QLabel("Mask closing factor:"), 2, 6)   
        
        self.binary_adaptive_block_sizeBox = QSpinBox(self)
        self.binary_adaptive_block_sizeBox.setMaximum(2000)
        self.binary_adaptive_block_sizeBox.setValue(335)
        self.binary_adaptive_block_sizeBox.setSingleStep(50)
        IPLayout.addWidget(self.binary_adaptive_block_sizeBox, 1, 1)
        IPLayout.addWidget(QLabel("Adaptive mask size:"), 1, 0)
        
        self.contour_dilation_box = QSpinBox(self)
        self.contour_dilation_box.setMaximum(2000)
        self.contour_dilation_box.setValue(10)
        self.contour_dilation_box.setSingleStep(1)
        IPLayout.addWidget(self.contour_dilation_box, 1, 3)
        IPLayout.addWidget(QLabel("Contour thickness:"), 1, 2)
        
        IPLayout.addWidget(QLabel("Threshold-contour::"), 1, 4)
        self.find_contour_thres_box = QDoubleSpinBox(self)
        self.find_contour_thres_box.setDecimals(4)
        self.find_contour_thres_box.setMinimum(-10)
        self.find_contour_thres_box.setMaximum(10)
        self.find_contour_thres_box.setValue(0.001)
        self.find_contour_thres_box.setSingleStep(0.0001)  
        IPLayout.addWidget(self.find_contour_thres_box, 1, 5)
        
        self.cellopening_factorBox = QSpinBox(self)
        self.cellopening_factorBox.setMaximum(2000)
        self.cellopening_factorBox.setValue(1)
        self.cellopening_factorBox.setSingleStep(1)
        IPLayout.addWidget(self.cellopening_factorBox, 2, 1)
        IPLayout.addWidget(QLabel("Cell opening factor:"), 2, 0)
        
        self.cellclosing_factorBox = QSpinBox(self)
        self.cellclosing_factorBox.setMaximum(2000)
        self.cellclosing_factorBox.setValue(5)
        self.cellclosing_factorBox.setSingleStep(1)
        IPLayout.addWidget(self.cellclosing_factorBox, 2, 3)
        IPLayout.addWidget(QLabel("Cell closing factor:"), 2, 2)
        
        ImageProcessingContainer.setLayout(IPLayout)
        
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for PiplineContainer---------------------------------------------------
        #**************************************************************************************************************************************
        PipelineContainer = QGroupBox("Pipeline settings")
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
        
        ButtonAddRound = QPushButton('Add Round', self)
        ButtonAddRound.setStyleSheet("QPushButton {color:white;background-color: teal; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        

        ButtonDeleteRound = QPushButton('Delete Round', self)
        ButtonDeleteRound.setStyleSheet("QPushButton {color:white;background-color: crimson; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        

        ButtonClearRound = QPushButton('Clear Rounds', self)
        ButtonClearRound.setStyleSheet("QPushButton {color:white;background-color: maroon; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        

        PipelineContainerLayout.addWidget(ButtonAddRound, 0, 2)
        ButtonAddRound.clicked.connect(self.AddFreshRound)
        ButtonAddRound.clicked.connect(self.GenerateScanCoords)
        
        PipelineContainerLayout.addWidget(ButtonDeleteRound, 0, 3)
        ButtonDeleteRound.clicked.connect(self.DeleteFreshRound)
        
        PipelineContainerLayout.addWidget(ButtonClearRound, 0, 4)
        ButtonClearRound.clicked.connect(self.ClearRoundQueue)
        
        self.BefKCLRoundNumBox = QSpinBox(self)
        self.BefKCLRoundNumBox.setMinimum(1)
        self.BefKCLRoundNumBox.setMaximum(1000)
        self.BefKCLRoundNumBox.setValue(1)
        self.BefKCLRoundNumBox.setSingleStep(1)
        self.BefKCLRoundNumBox.setMaximumWidth(30)
        PipelineContainerLayout.addWidget(self.BefKCLRoundNumBox, 0, 7)
        PipelineContainerLayout.addWidget(QLabel("Bef-Round Num:"), 0, 6)

        self.AftKCLRoundNumBox = QSpinBox(self)
        self.AftKCLRoundNumBox.setMinimum(1)
        self.AftKCLRoundNumBox.setMaximum(1000)
        self.AftKCLRoundNumBox.setValue(3)
        self.AftKCLRoundNumBox.setSingleStep(1)
        self.AftKCLRoundNumBox.setMaximumWidth(30)
        PipelineContainerLayout.addWidget(self.AftKCLRoundNumBox, 0, 9)
        PipelineContainerLayout.addWidget(QLabel("Aft-Round Num:"), 0, 8)        
        
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for RoundContainer-----------------------------------------------------
        #**************************************************************************************************************************************
        RoundContainer = QGroupBox("Waveform settings")
        RoundContainerLayout = QGridLayout()
        
        self.WaveformOrderBox = QSpinBox(self)
        self.WaveformOrderBox.setMinimum(1)
        self.WaveformOrderBox.setMaximum(1000)
        self.WaveformOrderBox.setValue(1)
        self.WaveformOrderBox.setSingleStep(1)
        self.WaveformOrderBox.setMaximumWidth(30)
        RoundContainerLayout.addWidget(self.WaveformOrderBox, 0, 1)
        RoundContainerLayout.addWidget(QLabel("Waveform sequence:"), 0, 0)
        
        ButtonAddWaveform = QPushButton('Add Waveform', self)
        ButtonAddWaveform.setStyleSheet("QPushButton {color:white;background-color: teal; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        

        ButtonDeleteWaveform = QPushButton('Delete Waveform', self)
        ButtonDeleteWaveform.setStyleSheet("QPushButton {color:white;background-color: crimson; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        ButtonClearWaveform = QPushButton('Clear Waveforms', self)
        ButtonClearWaveform.setStyleSheet("QPushButton {color:white;background-color: maroon; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        

        RoundContainerLayout.addWidget(ButtonAddWaveform, 0, 3)
        RoundContainerLayout.addWidget(ButtonDeleteWaveform, 0, 4)
        RoundContainerLayout.addWidget(ButtonClearWaveform, 0, 5)
        ButtonAddWaveform.clicked.connect(self.AddFreshWaveform)
        ButtonDeleteWaveform.clicked.connect(self.DeleteFreshWaveform)
        ButtonClearWaveform.clicked.connect(self.ClearWaveformQueue)
        
        self.Waveformer_widget_instance = NIDAQ.Waveformer_for_screening.WaveformGenerator()
        self.Waveformer_widget_instance.WaveformPackage.connect(self.UpdateWaveformerSignal)
        self.Waveformer_widget_instance.GalvoScanInfor.connect(self.UpdateWaveformerGalvoInfor)

        RoundContainerLayout.addWidget(self.Waveformer_widget_instance, 2, 0, 2, 6)
        RoundContainer.setLayout(RoundContainerLayout)
        
        PipelineContainerLayout.addWidget(RoundContainer, 3, 0, 4, 10)       
        #--------------------------------------------------------------------------------------------------------------------------------------     
        
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for StageScanContainer-------------------------------------------------
        #**************************************************************************************************************************************        
        ScanContainer = QGroupBox("Scanning settings")        
        ScanSettingLayout = QGridLayout() #Layout manager
        
        self.ScanStartRowIndexTextbox = QSpinBox(self)
        self.ScanStartRowIndexTextbox.setMinimum(-20000)
        self.ScanStartRowIndexTextbox.setMaximum(20000)
        self.ScanStartRowIndexTextbox.setSingleStep(500)
        ScanSettingLayout.addWidget(self.ScanStartRowIndexTextbox, 0, 1)
        ScanSettingLayout.addWidget(QLabel("Start index-row:"), 0, 0)
      
        self.ScanEndRowIndexTextbox = QSpinBox(self)
        self.ScanEndRowIndexTextbox.setMinimum(-20000)
        self.ScanEndRowIndexTextbox.setMaximum(20000)
        self.ScanEndRowIndexTextbox.setSingleStep(500)
        ScanSettingLayout.addWidget(self.ScanEndRowIndexTextbox, 0, 5)
        ScanSettingLayout.addWidget(QLabel("End index-row:"), 0, 4)
        
        self.ScanStartColumnIndexTextbox = QSpinBox(self)
        self.ScanStartColumnIndexTextbox.setMinimum(-20000)
        self.ScanStartColumnIndexTextbox.setMaximum(20000)
        self.ScanStartColumnIndexTextbox.setSingleStep(500)
        ScanSettingLayout.addWidget(self.ScanStartColumnIndexTextbox, 0, 3)
        ScanSettingLayout.addWidget(QLabel("Start index-column:"), 0, 2)   
        
        self.ScanEndColumnIndexTextbox = QSpinBox(self)
        self.ScanEndColumnIndexTextbox.setMinimum(-20000)
        self.ScanEndColumnIndexTextbox.setMaximum(20000)
        self.ScanEndColumnIndexTextbox.setSingleStep(500)
        ScanSettingLayout.addWidget(self.ScanEndColumnIndexTextbox, 0, 7)
        ScanSettingLayout.addWidget(QLabel("End index-column:"), 0, 6)      

        self.ScanstepTextbox = QSpinBox(self)
        self.ScanstepTextbox.setMaximum(20000)
        self.ScanstepTextbox.setValue(1500)
        self.ScanstepTextbox.setSingleStep(500)
        ScanSettingLayout.addWidget(self.ScanstepTextbox, 1, 1)
        ScanSettingLayout.addWidget(QLabel("Step size:"), 1, 0)
        
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
        
        PipelineContainerLayout.addWidget(ScanContainer, 2, 0, 1, 10)       
        #--------------------------------------------------------------------------------------------------------------------------------------
        
        PipelineContainer.setLayout(PipelineContainerLayout)
        
        self.layout.addWidget(GeneralSettingContainer, 1, 0, 1, 2)
        self.layout.addWidget(FocusCorrectionContainer, 2, 0)
        self.layout.addWidget(ImageDisplayContainer, 2, 1)
        self.layout.addWidget(SelectionsettingContainer, 3, 0, 1, 2)
        self.layout.addWidget(ImageProcessingContainer, 4, 0, 1, 2)
        self.layout.addWidget(PipelineContainer, 5, 0, 1, 2)
        self.setLayout(self.layout)
        
        #------------------------------------------------------------Waveform package functions--------------------------------------------------------------------------        
    def UpdateWaveformerSignal(self, WaveformPackage):
        self.FreshWaveformPackage = WaveformPackage # Capture the newest generated waveform tuple signal from Waveformer.
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
    
    #--------------------------------------------------------------Round package functions------------------------------------------------------------------------        
    def AddFreshRound(self):
        CurrentRoundSequence = self.RoundOrderBox.value()
        
        WaveformQueueDict = copy.deepcopy(self.WaveformQueueDict) # Here we make the self.WaveformQueueDict private so that other rounds won't refer to the same variable.
        WaveformQueueDict_GalvoInfor = copy.deepcopy(self.WaveformQueueDict_GalvoInfor)
        self.RoundQueueDict['RoundPackage_{}'.format(CurrentRoundSequence)] = WaveformQueueDict
        self.RoundQueueDict['GalvoInforPackage_{}'.format(CurrentRoundSequence)] = WaveformQueueDict_GalvoInfor # Information we need to restore pmt scanning images.
        
        #Configure information for Z-stack
        ZstackNumber = self.FocusStackNumTextbox.value()
        ZstackStep = self.FocusStackStepTextbox.value()
        
        self.FocusStackInfoDict['RoundPackage_{}'.format(CurrentRoundSequence)] = 'NumberOfFocus{}WithIncrementBeing{}'.format(ZstackNumber, ZstackStep)
        
        self.normalOutputWritten('Round{} added.\n'.format(CurrentRoundSequence))
        print('Round added.')
        
    def GenerateScanCoords(self):
        self.CoordContainer = np.array([])
        # settings for scanning index
        position_index=[]
        row_start = int(self.ScanStartRowIndexTextbox.value()) #row position index start number
        row_end = int(self.ScanEndRowIndexTextbox.value())+1 #row position index end number
        
        column_start = int(self.ScanStartColumnIndexTextbox.value())
        column_end = int(self.ScanEndColumnIndexTextbox.value())+1  # With additional plus one, the range is fully covered by steps.
        
        step = int(self.ScanstepTextbox.value()) #length of each step, 1500 for -5~5V FOV
      
        for i in range(row_start, row_end, step):
            position_index.append(int(i))
            for j in range(column_start, column_end, step):
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
        self.RoundQueueDict = {}
        self.RoundCoordsDict = {}
        self.WaveformQueueDict_GalvoInfor = {}
        self.GeneralSettingDict = {}
        self.FocusStackInfoDict = {}
        
        self.normalOutputWritten('Rounds cleared.\n')
        print('Rounds cleared.')
    #--------------------------------------------------------------Selection functions------------------------------------------------------------------------         
    def ConfigGeneralSettings(self):
        selectnum = int(self.selec_num_box.value())
        if self.ComBoxSelectionFactor_1.currentText() == 'Mean intensity in contour weight':
            MeanIntensityContourWeight = self.WeightBoxSelectionFactor_1.value()
        elif self.ComBoxSelectionFactor_1.currentText() == 'Contour soma ratio weight':
            ContourSomaRatioWeight = self.WeightBoxSelectionFactor_1.value()
        elif self.ComBoxSelectionFactor_1.currentText() == 'Change weight':
            ChangeWeight = self.WeightBoxSelectionFactor_1.value()
            
        if self.ComBoxSelectionFactor_2.currentText() == 'Mean intensity in contour weight':
            MeanIntensityContourWeight = self.WeightBoxSelectionFactor_2.value()
        elif self.ComBoxSelectionFactor_2.currentText() == 'Contour soma ratio weight':
            ContourSomaRatioWeight = self.WeightBoxSelectionFactor_2.value()
        elif self.ComBoxSelectionFactor_2.currentText() == 'Change weight':
            ChangeWeight = self.WeightBoxSelectionFactor_2.value()
            
        if self.ComBoxSelectionFactor_3.currentText() == 'Mean intensity in contour weight':
            MeanIntensityContourWeight = self.WeightBoxSelectionFactor_3.value()
        elif self.ComBoxSelectionFactor_3.currentText() == 'Contour soma ratio weight':
            ContourSomaRatioWeight = self.WeightBoxSelectionFactor_3.value()
        elif self.ComBoxSelectionFactor_3.currentText() == 'Change weight':
            ChangeWeight = self.WeightBoxSelectionFactor_3.value()
        
        BefRoundNum = int(self.BefKCLRoundNumBox.value())        
        AftRoundNum = int(self.AftKCLRoundNumBox.value())        
        smallestsize = int(self.IPsizetextbox.currentText())            
        openingfactor = int(self.opening_factorBox.value())
        closingfactor = int(self.closing_factorBox.value())
        cellopeningfactor = int(self.cellopening_factorBox.value())
        cellclosingfactor = int(self.cellclosing_factorBox.value())
        binary_adaptive_block_size = int(self.binary_adaptive_block_sizeBox.value())
        self_findcontour_thres = float(self.find_contour_thres_box.value())
        contour_dilation = int(self.contour_dilation_box.value())
        savedirectory = self.savedirectory
        
        #--------------------------------------------------------Generate the focus correction matrix-----------------------------------------------------------
        if self.ApplyFocusSetCheckbox.isChecked():
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
                RawDuplicateRow = self.FocusDuplicateMethodInfor[0,:] # The row index from calibration step (Corresponding to column index in python array)
                RawDuplicateCol = self.FocusDuplicateMethodInfor[1,:]
                RawDuplicateFocus = self.FocusDuplicateMethodInfor[2,:]
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
                        self.FocusCorrectionMatrixDict['RoundPackage_{}'.format(CurrentRound+1)] = FocusCorrectionMatrixContainer               
                        print(self.FocusCorrectionMatrixDict['RoundPackage_{}'.format(CurrentRound+1)])
        else:
            self.FocusCorrectionMatrixDict = []
        
#        print(self.FocusCorrectionMatrixDict.keys())
        generalnamelist = ['selectnum', 'Mean intensity in contour weight','Contour soma ratio weight','Change weight', 'BefRoundNum', 'AftRoundNum', 'smallestsize', 'openingfactor', 'closingfactor', 'cellopeningfactor', 
                           'cellclosingfactor', 'binary_adaptive_block_size', 'self_findcontour_thres', 'contour_dilation', 'savedirectory', 'FocusCorrectionMatrixDict', 'FocusStackInfoDict']
        
        generallist = [selectnum, MeanIntensityContourWeight, ContourSomaRatioWeight, ChangeWeight, BefRoundNum, AftRoundNum, smallestsize, openingfactor, closingfactor, cellopeningfactor, 
                       cellclosingfactor, binary_adaptive_block_size, self_findcontour_thres, contour_dilation, savedirectory, self.FocusCorrectionMatrixDict, self.FocusStackInfoDict]
        
        for item in range(len(generallist)):
            self.GeneralSettingDict[generalnamelist[item]] = generallist[item]
#        print(self.GeneralSettingDict['FocusStackInfoDict'])
        self.normalOutputWritten('Rounds configured.\n')
        
        #---------------------------------------------------------------Show general info---------------------------------------------------------------------------------
        self.normalOutputWritten('--------Pipeline general info--------\n')
        for eachround in range(int(len(self.RoundQueueDict)/2)):

            for eachwaveform in self.RoundQueueDict['RoundPackage_'+str(eachround+1)]:
                try:
                    if len(self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][3]) != 0:
                        self.normalOutputWritten('Round {}, recording channels:{}.\n'.format(eachround+1, self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][3]))
                        print('Round {}, recording channels:{}.'.format(eachround+1, self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][3]))#[1]['Sepcification']
#                    else:
#                        self.normalOutputWritten('Round {} No recording channel.\n'.format(eachround+1))
                except:
                    self.normalOutputWritten('No recording channel.\n')
                    print('No recording channel.')
                try:
                    self.normalOutputWritten('Round {}, Analog signals:{}.\n'.format(eachround+1, self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][1]['Sepcification']))
                    print('Round {}, Analog signals:{}.'.format(eachround+1, self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][1]['Sepcification']))#
                except:
                    self.normalOutputWritten('No Analog signals.\n')
                    print('No Analog signals.')
                try:
                    if len(self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][2]['Sepcification']) != 0:
                        self.normalOutputWritten('Round {}, Digital signals:{}.\n'.format(eachround+1, self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][2]['Sepcification']))
                        print('Round {}, Digital signals:{}.'.format(eachround+1, self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][2]['Sepcification']))#
#                    else:
#                        self.normalOutputWritten('Round {} No Digital signals.\n'.format(eachround+1))
                except:
                    self.normalOutputWritten('No Digital signals.\n')
                    print('No Digital signals.')
                    
            self.normalOutputWritten('\n')
        self.normalOutputWritten('----------------------------------------\n')
        
        
    def _open_file_dialog(self):
        self.savedirectory = str(QtWidgets.QFileDialog.getExistingDirectory())
        self.savedirectorytextbox.setText(self.savedirectory)
        self.saving_prefix = str(self.prefixtextbox.text())
        
        
    #--------------------------------------------------------------------GenerateFocusCorrectionMatrix-----------------------------------------
    def CaptureFocusCorrectionMatrix(self, CorrectionFomula):
        self.CorrectionFomula = CorrectionFomula
        
    def CaptureFocusDuplicateMethodMatrix(self, FocusDuplicateMethodInfor):
        self.FocusDuplicateMethodInfor = FocusDuplicateMethodInfor
        
        #**************************************************************************************************************************************
        #-----------------------------------------------------------Functions for Execution----------------------------------------------------
        #**************************************************************************************************************************************   
    def ExecutePipeline(self):
        get_ipython().run_line_magic('matplotlib', 'inline') # before start, set spyder back to inline
        
        self.ExecuteThreadInstance = ScanningExecutionThread(self.RoundQueueDict, self.RoundCoordsDict, self.GeneralSettingDict)
        self.ExecuteThreadInstance.ScanningResult.connect(self.GetDataForShowingRank)
        self.ExecuteThreadInstance.start()
        
    def Savepipeline(self):
        SavepipelineInstance = []
        SavepipelineInstance.extend([self.RoundQueueDict, self.RoundCoordsDict, self.GeneralSettingDict])
        
        np.save(os.path.join(self.savedirectory, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_Pipeline'), SavepipelineInstance)
        
        
    def GetDataForShowingRank(self, RankedAllCellProperties, FinalMergedCoords, IndexLookUpCellPropertiesDict, PMTimageDict):
        
        self.RankedAllCellProperties = RankedAllCellProperties
        self.FinalMergedCoords = FinalMergedCoords # Stage coordinates of the top cells with same ones merged together.
        self.IndexLookUpCellPropertiesDict = IndexLookUpCellPropertiesDict
        self.PMTimageDict = PMTimageDict
        
        self.TotalCoordsNum = len(self.FinalMergedCoords)
        
        self.TopGeneralInforLabel.setText('Number of coords in total: {}'.format(self.TotalCoordsNum))

    def PopNextTopCells(self, direction):       
        if direction == 'next':
            if self.popnexttopimgcounter > (self.TotalCoordsNum-1):#Make sure it doesn't go beyond the last coords.
                self.popnexttopimgcounter -= 1
            CurrentPosIndex = self.FinalMergedCoords[self.popnexttopimgcounter,:].tolist() # self.popnexttopimgcounter is the order number of each Stage coordinates.
            
            self.TopCoordsLabel.setText("Row: {} Col: {}".format(CurrentPosIndex[0], CurrentPosIndex[1]))     
            self.CurrentImgShowTopCells = self.PMTimageDict['RoundPackage_{}'.format(self.GeneralSettingDict['BefRoundNum'])]['row_{}_column_{}'.format(CurrentPosIndex[0], CurrentPosIndex[1])]
            self.ShowTopCellsInstance = ShowTopCellsThread(self.GeneralSettingDict, self.RankedAllCellProperties, CurrentPosIndex, self.IndexLookUpCellPropertiesDict, self.CurrentImgShowTopCells, self.MatdisplayFigureTopGuys)
            self.ShowTopCellsInstance.run()
    #        self.ax = self.ShowTopCellsInstance.gg()
    #        self.ax = self.MatdisplayFigureTopGuys.add_subplot(111)
            self.MatdisplayCanvasTopGuys.draw()
#            if self.popnexttopimgcounter < (self.TotalCoordsNum-1):
            self.popnexttopimgcounter += 1 # Alwasy plus 1 to get it ready for next move.
            
        elif direction == 'previous':
            self.popnexttopimgcounter -= 2 
            if self.popnexttopimgcounter >= 0:
                CurrentPosIndex = self.FinalMergedCoords[self.popnexttopimgcounter,:].tolist() # self.popnexttopimgcounter is the order number of each Stage coordinates.
                
                self.TopCoordsLabel.setText("Row: {} Col: {}".format(CurrentPosIndex[0], CurrentPosIndex[1]))     
                self.CurrentImgShowTopCells = self.PMTimageDict['RoundPackage_{}'.format(self.GeneralSettingDict['BefRoundNum'])]['row_{}_column_{}'.format(CurrentPosIndex[0], CurrentPosIndex[1])]
                self.ShowTopCellsInstance = ShowTopCellsThread(self.GeneralSettingDict, self.RankedAllCellProperties, CurrentPosIndex, self.IndexLookUpCellPropertiesDict, self.CurrentImgShowTopCells, self.MatdisplayFigureTopGuys)
                self.ShowTopCellsInstance.run()
        #        self.ax = self.ShowTopCellsInstance.gg()
        #        self.ax = self.MatdisplayFigureTopGuys.add_subplot(111)
                self.MatdisplayCanvasTopGuys.draw()
                if self.popnexttopimgcounter < (self.TotalCoordsNum-1):
                    self.popnexttopimgcounter += 1
            else:
                self.popnexttopimgcounter = 0
        
    #--------------------------------------------------------Save and load file----------------------------------------------------------------
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
                RawDuplicateRow = self.FocusDuplicateMethodInfor[0,:] # The row index from calibration step (Corresponding to column index in python array)
                RawDuplicateCol = self.FocusDuplicateMethodInfor[1,:]
                RawDuplicateFocus = self.FocusDuplicateMethodInfor[2,:]
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
                        
                        self.FocusCorrectionMatrixDict['RoundPackage_{}'.format(CurrentRound+1)] = FocusCorrectionMatrixContainer               
                        print(self.FocusCorrectionMatrixDict['RoundPackage_{}'.format(CurrentRound+1)])
        else:
            self.FocusCorrectionMatrixDict = []
        
        self.GeneralSettingDict['FocusCorrectionMatrixDict'] = self.FocusCorrectionMatrixDict # Refresh the focus correction
        self.GeneralSettingDict['savedirectory'] = self.savedirectory
        
        self.normalOutputWritten('Pipeline loaded.\n')
        print('Pipeline loaded.')
        
        #---------------------------------------------------------------Show general info---------------------------------------------------------------------------------
        self.normalOutputWritten('--------Pipeline general info--------\n')
        for eachround in range(int(len(self.RoundQueueDict)/2)):

            for eachwaveform in self.RoundQueueDict['RoundPackage_'+str(eachround+1)]:
                try:
                    if len(self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][3]) != 0:
                        self.normalOutputWritten('Round {}, recording channels:{}.\n'.format(eachround+1, self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][3]))
                        print('Round {}, recording channels:{}.'.format(eachround+1, self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][3]))#[1]['Sepcification']
#                    else:
#                        self.normalOutputWritten('Round {} No recording channel.\n'.format(eachround+1))
                except:
                    self.normalOutputWritten('No recording channel.\n')
                    print('No recording channel.')
                try:
                    self.normalOutputWritten('Round {}, Analog signals:{}.\n'.format(eachround+1, self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][1]['Sepcification']))
                    print('Round {}, Analog signals:{}.'.format(eachround+1, self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][1]['Sepcification']))#
                except:
                    self.normalOutputWritten('No Analog signals.\n')
                    print('No Analog signals.')
                try:
                    if len(self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][2]['Sepcification']) != 0:
                        self.normalOutputWritten('Round {}, Digital signals:{}.\n'.format(eachround+1, self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][2]['Sepcification']))
                        self.normalOutputWritten('Lasting time:{} s.\n'.format(len(self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][2]['Waveform'][0])/self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][0]))
                        
                        print('Lasting time:{} s.\n'.format(len(self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][2]['Waveform'][0])/self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][0]))
                        print('Round {}, Digital signals:{}.'.format(eachround+1, self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][2]['Sepcification']))#
#                    else:
#                        self.normalOutputWritten('Round {} No Digital signals.\n'.format(eachround+1))
                except:
                    self.normalOutputWritten('No Digital signals.\n')
                    print('No Digital signals.')
                    
            self.normalOutputWritten('\n')
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
        
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        mainwin = Mainbody()
        mainwin.show()
        app.exec_()
    run_app()
