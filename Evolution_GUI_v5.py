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
from EvolutionScanningThread import ScanningExecutionThread, ShowTopCellsThread # This is the thread file for execution.
from ImageAnalysis.EvolutionAnalysis_v2 import ProcessImage
from SampleStageControl.stage import LudlStage
from NIDAQ.generalDaqerThread import execute_tread_singlesample_digital

import FocusCalibrater
import GalvoWidget.PMTWidget
import NIDAQ.AOTFWidget
import ThorlabsFilterSlider.FilterSliderWidget
import InsightX3.TwoPhotonLaserUI

class Mainbody(QWidget):
    
    waveforms_generated = pyqtSignal(object, object, list, int)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        os.chdir('./')# Set directory to current folder.
        self.setFont(QFont("Arial"))
        
        self.setMinimumSize(1080, 1920)
        self.setWindowTitle("McDonnell")
        self.layout = QGridLayout(self)
        
        self.WaveformQueueDict = {}
        self.RoundQueueDict = {}
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
                                                "QPushButton:pressed {color:yellow;background-color: pink; border-style: outset;border-radius: 3px;border-width: 2px;font: bold 14px;padding: 1px}"
                                                "QPushButton:hover:!pressed {color:gray;background-color: pink; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")

        self.toolButtonOpenDialog.setObjectName("toolButtonOpenDialog")
        self.toolButtonOpenDialog.clicked.connect(self._open_file_dialog)
        
        GeneralSettingContainerLayout.addWidget(self.toolButtonOpenDialog, 0, 0)
        
        ButtonConfigurePipeline = QPushButton('Configure', self)
        ButtonConfigurePipeline.setStyleSheet("QPushButton {color:white;background-color: rgb(184,184,243); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:hover:!pressed {color:gray;background-color: rgb(184,184,243); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        ButtonConfigurePipeline.clicked.connect(self.ConfigGeneralSettings)
#        ButtonConfigurePipeline.clicked.connect(self.GenerateFocusCorrectionMatrix)
        
        ButtonExePipeline = QPushButton('Execute', self)
        ButtonExePipeline.setStyleSheet("QPushButton {color:white;background-color: rgb(184,184,243); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:hover:!pressed {color:gray;background-color: rgb(184,184,243); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
#        ButtonExePipeline.clicked.connect(self.ConfigGeneralSettings)      
        ButtonExePipeline.clicked.connect(self.ExecutePipeline)
        
        ButtonSavePipeline = QPushButton('Save pipeline', self)
        ButtonSavePipeline.setStyleSheet("QPushButton {color:white;background-color: rgb(82,153,211); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:hover:!pressed {color:gray;background-color: rgb(82,153,211); border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
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
        self.Matdisplay_Figure = Figure()
        self.Matdisplay_Canvas = FigureCanvas(self.Matdisplay_Figure)

        ImageDisplayContainerLayout.addWidget(self.Matdisplay_Canvas, 1, 1, 8, 5)
        
        self.Matdisplay_toolbar = NavigationToolbar(self.Matdisplay_Canvas, self)
        ImageDisplayContainerLayout.addWidget(self.Matdisplay_toolbar, 0, 1, 1, 5)
        
#        self.TopCoordsLabel = QLabel("Row:      Col:      ")
#        ImageDisplayContainerLayout.addWidget(self.TopCoordsLabel, 1, 6)
        
#        self.TopGeneralInforLabel = QLabel("  ")
#        ImageDisplayContainerLayout.addWidget(self.TopGeneralInforLabel, 2, 6)    
        
        ButtonRankResetCoordImg = QPushButton('Reset coord', self)
        ButtonRankResetCoordImg.clicked.connect(self.ResetRankCoord)
        ImageDisplayContainerLayout.addWidget(ButtonRankResetCoordImg, 0, 6)
        
        ButtonRankPreviousCoordImg = QPushButton('Previous', self)
        ButtonRankPreviousCoordImg.clicked.connect(lambda: self.GoThroughTopCells('previous'))
        ImageDisplayContainerLayout.addWidget(ButtonRankPreviousCoordImg, 1, 6)
        
        self.ButtonShowInScatter = QPushButton('Show in scatter', self)
        self.ButtonShowInScatter.setCheckable(True)
        self.ButtonShowInScatter.clicked.connect(self.ShowScatterPos)
        ImageDisplayContainerLayout.addWidget(self.ButtonShowInScatter, 2, 6)

        ButtonRankNextCoordImg = QPushButton('Next', self)
        ButtonRankNextCoordImg.clicked.connect(lambda: self.GoThroughTopCells('next'))
        ImageDisplayContainerLayout.addWidget(ButtonRankNextCoordImg, 1, 7)
        
        ButtonRankDeleteFromList = QPushButton('Delete', self)
        ButtonRankDeleteFromList.clicked.connect(self.DeleteFromTopCells)
        ImageDisplayContainerLayout.addWidget(ButtonRankDeleteFromList, 2, 7)
        
        ButtonRankSaveList = QPushButton('Save array', self)
        ButtonRankSaveList.clicked.connect(self.SaveCellsProArray)
        ImageDisplayContainerLayout.addWidget(ButtonRankSaveList, 3, 6)
        
#        ButtonRankNextCoordImg = QPushButton('Move here', self)
#        ButtonRankNextCoordImg.setObjectName('Startbutton')
##        ButtonRankNextCoordImg.clicked.connect(lambda: self.PopNextTopCells('next'))
#        ImageDisplayContainerLayout.addWidget(ButtonRankNextCoordImg, 3, 7)
        
        self.ConsoleTextDisplay = QTextEdit()
        self.ConsoleTextDisplay.setFontItalic(True)
        self.ConsoleTextDisplay.setPlaceholderText('Notice board from console.')
        self.ConsoleTextDisplay.setMaximumHeight(200)
        ImageDisplayContainerLayout.addWidget(self.ConsoleTextDisplay, 4, 6, 5, 2)
        
        
        ImageDisplayContainer.setLayout(ImageDisplayContainerLayout)
        ImageDisplayContainer.setMinimumHeight(400)
        ImageDisplayContainer.setMinimumWidth(550)

    #--------------------------------------------------------------------------------------------------------------------------------------------
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for tool widgets-------------------------------------------------------
        #**************************************************************************************************************************************
        ToolWidgetsContainer = QGroupBox('Tool widgets')
        ToolWidgetsLayout = QGridLayout()
        
        self.OpenPMTWidgetButton = QPushButton('PMT', self)
        ToolWidgetsLayout.addWidget(self.OpenPMTWidgetButton, 0, 0)
        self.OpenPMTWidgetButton.clicked.connect(self.openPMTWidget)   
        
        self.OpenAOTFWidgetButton = QPushButton('AOTF', self)
        ToolWidgetsLayout.addWidget(self.OpenAOTFWidgetButton, 0, 1)
        self.OpenAOTFWidgetButton.clicked.connect(self.openAOTFWidget)      
        
        self.OpenFilterSliderWidgetButton = QPushButton('FilterSlider', self)
        ToolWidgetsLayout.addWidget(self.OpenFilterSliderWidgetButton, 1, 0)
        self.OpenFilterSliderWidgetButton.clicked.connect(self.openFilterSliderWidget)
        
        self.OpenInsightWidgetButton = QPushButton('Insight X3', self)
        ToolWidgetsLayout.addWidget(self.OpenInsightWidgetButton, 1, 1)
        self.OpenInsightWidgetButton.clicked.connect(self.openInsightWidget)    
        
        self.switchbutton_LED = QPushButton('LED')
        self.switchbutton_LED.setCheckable(True)
        self.switchbutton_LED.clicked.connect(lambda: self.execute_tread_single_sample_digital('LED'))
        ToolWidgetsLayout.addWidget(self.switchbutton_LED, 0, 3)
        
        ToolWidgetsContainer.setLayout(ToolWidgetsLayout)

        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for Image processing settings------------------------------------------
        #**************************************************************************************************************************************
        self.PostProcessTab = QTabWidget()
        
        ImageProcessingContainer = QGroupBox()
        IPLayout = QGridLayout()
        
        self.IPsizetextbox = QSpinBox(self)
        self.IPsizetextbox.setMaximum(2000)
        self.IPsizetextbox.setValue(800)
        self.IPsizetextbox.setSingleStep(1)
        IPLayout.addWidget(self.IPsizetextbox, 1, 7)
        IPLayout.addWidget(QLabel("Cell smallest size:"), 1, 6)
        
        self.opening_factorBox = QSpinBox(self)
        self.opening_factorBox.setMaximum(2000)
        self.opening_factorBox.setValue(2)
        self.opening_factorBox.setSingleStep(1)
        IPLayout.addWidget(self.opening_factorBox, 2, 5)
        IPLayout.addWidget(QLabel("Mask opening factor:"), 2, 4)
        
        self.closing_factorBox = QSpinBox(self)
        self.closing_factorBox.setMaximum(2000)
        self.closing_factorBox.setValue(3)
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
        self.contour_dilation_box.setValue(11)
        self.contour_dilation_box.setSingleStep(1)
        IPLayout.addWidget(self.contour_dilation_box, 1, 3)
        IPLayout.addWidget(QLabel("Contour thickness:"), 1, 2)
        
        IPLayout.addWidget(QLabel("Threshold-contour:"), 1, 4)
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
        self.cellclosing_factorBox.setMaximum(20000)
        self.cellclosing_factorBox.setValue(2)
        self.cellclosing_factorBox.setSingleStep(1)
        IPLayout.addWidget(self.cellclosing_factorBox, 2, 3)
        IPLayout.addWidget(QLabel("Cell closing factor:"), 2, 2)
        
        ImageProcessingContainer.setLayout(IPLayout)
        
        LoadSettingContainer = QGroupBox()
        LoadSettingLayout = QGridLayout()
        
        self.FilepathSwitchBox = QComboBox()
        self.FilepathSwitchBox.addItems(['Tag', 'Lib','All'])
        LoadSettingLayout.addWidget(self.FilepathSwitchBox, 0, 0)
        
        self.AnalysisRoundBox = QSpinBox(self)
        self.AnalysisRoundBox.setMaximum(2000)
        self.AnalysisRoundBox.setValue(1)
        self.AnalysisRoundBox.setSingleStep(1)
        LoadSettingLayout.addWidget(self.AnalysisRoundBox, 0, 2)
        
        self.AddAnalysisRoundButton = QtWidgets.QPushButton('Add Round:')
        self.AddAnalysisRoundButton.clicked.connect(self.SetAnalysisRound)
        LoadSettingLayout.addWidget(self.AddAnalysisRoundButton, 0, 1)
        
        self.datasavedirectorytextbox = QLineEdit(self)
        self.datasavedirectorytextbox.setPlaceholderText('Data directory')
        LoadSettingLayout.addWidget(self.datasavedirectorytextbox, 0, 3, 1, 3)
        
        self.toolButtonOpenDialog = QtWidgets.QPushButton('Set path')
        self.toolButtonOpenDialog.clicked.connect(self.SetAnalysisPath)
        LoadSettingLayout.addWidget(self.toolButtonOpenDialog, 0, 6)
        
        self.ClearAnalysisInforButton = QtWidgets.QPushButton('Clear infor')
        self.ClearAnalysisInforButton.clicked.connect(self.ClearAnalysisInfor)
        LoadSettingLayout.addWidget(self.ClearAnalysisInforButton, 0, 7)        

        LoadSettingContainer.setLayout(LoadSettingLayout)
        
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for Selection settings Container---------------------------------------
        #**************************************************************************************************************************************
        SelectionsettingTab = QWidget()
        SelectionsettingTab.layout = QGridLayout()
        
        self.SeleParaBox = QComboBox()
        self.SeleParaBox.addItems(['Mean intensity divided by tag/Contour soma ratio'])
        SelectionsettingTab.layout.addWidget(self.SeleParaBox, 0, 2)
        SelectionsettingTab.layout.addWidget(QLabel('Scatter axes'), 0, 1)
        
        self.AnalysisTypeSwitchBox = QComboBox()
        self.AnalysisTypeSwitchBox.addItems(['Brightness screening', 'Lib'])
        SelectionsettingTab.layout.addWidget(self.AnalysisTypeSwitchBox, 0, 0)
        
        ExecuteAnalysisButton = QPushButton('Load images', self)
#        ExecuteAnalysisButton.setObjectName('Startbutton')
        ExecuteAnalysisButton.clicked.connect(lambda: self.StartScreeningAnalysisThread())
        SelectionsettingTab.layout.addWidget(ExecuteAnalysisButton, 1, 2)
        
        UpdateProcessTab = QTabWidget()
        UpdateProcessTab.layout = QGridLayout()
        
        UpdateProcessTab_1 = QWidget()
        UpdateProcessTab_1.layout = QGridLayout()
        
        UpdateProcessTab_1.layout.addWidget(QLabel("Selection boundary:"), 0, 0)
        
        self.Selection_boundaryBox = QComboBox()
        self.Selection_boundaryBox.addItems(['Circular radius', 'Rank'])
        UpdateProcessTab_1.layout.addWidget(self.Selection_boundaryBox, 0, 1)
        
#        self.AnalysisCirclePercentBox = QSpinBox(self)
#        self.AnalysisCirclePercentBox.setMaximum(100)
#        self.AnalysisCirclePercentBox.setValue(50)
#        self.AnalysisCirclePercentBox.setSingleStep(1)
#        UpdateProcessTab_1.layout.addWidget(self.AnalysisCirclePercentBox, 0, 3)
#        UpdateProcessTab_1.layout.addWidget(QLabel("Percentage(%):"), 0, 2)
        
        UpdateScattersButton = QtWidgets.QPushButton('Update scatters')
        UpdateScattersButton.clicked.connect(self.UpdateSelectionScatter)
        UpdateProcessTab_1.layout.addWidget(UpdateScattersButton, 0, 4)
        
        UpdateProcessTab_2 = QWidget()
        UpdateProcessTab_2.layout = QGridLayout()   
        
        self.WeightBoxSelectionFactor_1 = QDoubleSpinBox(self)
        self.WeightBoxSelectionFactor_1.setDecimals(2)
        self.WeightBoxSelectionFactor_1.setMinimum(0)
        self.WeightBoxSelectionFactor_1.setMaximum(1)
        self.WeightBoxSelectionFactor_1.setValue(1)
        self.WeightBoxSelectionFactor_1.setSingleStep(0.1)  
        UpdateProcessTab_2.layout.addWidget(self.WeightBoxSelectionFactor_1, 0, 1)
        UpdateProcessTab_2.layout.addWidget(QLabel("Weight for axis 1:"), 0, 0)
        
        self.WeightBoxSelectionFactor_2 = QDoubleSpinBox(self)
        self.WeightBoxSelectionFactor_2.setDecimals(2)
        self.WeightBoxSelectionFactor_2.setMinimum(0)
        self.WeightBoxSelectionFactor_2.setMaximum(1)
        self.WeightBoxSelectionFactor_2.setValue(0.5)
        self.WeightBoxSelectionFactor_2.setSingleStep(0.1)  
        UpdateProcessTab_2.layout.addWidget(self.WeightBoxSelectionFactor_2, 0, 3)  
        UpdateProcessTab_2.layout.addWidget(QLabel("Weight for axis 2:"), 0, 2)
        
        self.WeightBoxSelectionFactor_3 = QDoubleSpinBox(self)
        self.WeightBoxSelectionFactor_3.setDecimals(2)
        self.WeightBoxSelectionFactor_3.setMinimum(0)
        self.WeightBoxSelectionFactor_3.setMaximum(1)
        self.WeightBoxSelectionFactor_3.setValue(1)
        self.WeightBoxSelectionFactor_3.setSingleStep(0.1)  
        UpdateProcessTab_2.layout.addWidget(self.WeightBoxSelectionFactor_3, 0, 5)  
        UpdateProcessTab_2.layout.addWidget(QLabel("Weight for axis 3:"), 0, 4)
        
        UpdateProcessTab_1.setLayout(UpdateProcessTab_1.layout)
        UpdateProcessTab_2.setLayout(UpdateProcessTab_2.layout)
        UpdateProcessTab.addTab(UpdateProcessTab_1,"Normalized distance") 
        UpdateProcessTab.addTab(UpdateProcessTab_2,"Axes weights") 
        SelectionsettingTab.layout.addWidget(UpdateProcessTab, 0, 3, 2, 4)
        
        SelectionsettingTab.setLayout(SelectionsettingTab.layout)

        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for Selection threshold settings---------------------------------------
        #**************************************************************************************************************************************
        SelectionthresholdsettingTab = QWidget()
        SelectionthresholdsettingTab.layout = QGridLayout()
        
        SelectionthresholdsettingTab.layout.addWidget(QLabel("Intensity threshold:"), 0, 0)
        self.SelectionMeanInten_thres_box = QDoubleSpinBox(self)
        self.SelectionMeanInten_thres_box.setDecimals(4)
        self.SelectionMeanInten_thres_box.setMinimum(0)
        self.SelectionMeanInten_thres_box.setMaximum(10)
        self.SelectionMeanInten_thres_box.setValue(0.150)
        self.SelectionMeanInten_thres_box.setSingleStep(0.0001)  
        SelectionthresholdsettingTab.layout.addWidget(self.SelectionMeanInten_thres_box, 0, 1)
        
        SelectionthresholdsettingTab.layout.addWidget(QLabel("Contour/Soma threshold:"), 1, 0)
        self.SelectionCSratio_thres_box = QDoubleSpinBox(self)
        self.SelectionCSratio_thres_box.setDecimals(3)
        self.SelectionCSratio_thres_box.setMinimum(0)
        self.SelectionCSratio_thres_box.setMaximum(10)
        self.SelectionCSratio_thres_box.setValue(0.80)
        self.SelectionCSratio_thres_box.setSingleStep(0.0001)  
        SelectionthresholdsettingTab.layout.addWidget(self.SelectionCSratio_thres_box, 1, 1) 
        
        SelectionthresholdsettingTab.layout.addWidget(QLabel("Roundness threshold:"), 0, 2)
        self.SelectionRoundness_thres_box = QDoubleSpinBox(self)
        self.SelectionRoundness_thres_box.setDecimals(3)
        self.SelectionRoundness_thres_box.setMinimum(0)
        self.SelectionRoundness_thres_box.setMaximum(10)
        self.SelectionRoundness_thres_box.setValue(1.10)
        self.SelectionRoundness_thres_box.setSingleStep(0.0001)  
        SelectionthresholdsettingTab.layout.addWidget(self.SelectionRoundness_thres_box, 0, 3) 
        
        SelectionthresholdsettingTab.setLayout(SelectionthresholdsettingTab.layout)
        
        self.PostProcessTab.addTab(SelectionsettingTab,"Analysis selection")        
        self.PostProcessTab.addTab(LoadSettingContainer,"Loading settings")
        self.PostProcessTab.addTab(SelectionthresholdsettingTab,"Threshold settings")
        self.PostProcessTab.addTab(ImageProcessingContainer,"Image analysis settings")

        # ==========================================================================================================================================================
        #         #**************************************************************************************************************************************
        #         #-----------------------------------------------------------GUI for PiplineContainer---------------------------------------------------
        #         #**************************************************************************************************************************************
        # ==========================================================================================================================================================
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
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"    
                                        "QPushButton:hover:!pressed {color:gray;background-color: teal; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        ButtonDeleteRound = QPushButton('Delete Round', self)
        ButtonDeleteRound.setStyleSheet("QPushButton {color:white;background-color: crimson; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:hover:!pressed {color:gray;background-color: crimson; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        

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
        self.ScanRepeatTextbox.setMaximum(100000)
        self.ScanRepeatTextbox.setSingleStep(1)
        PipelineContainerLayout.addWidget(self.ScanRepeatTextbox, 0, 7)
        PipelineContainerLayout.addWidget(QLabel("Meshgrid:"), 0, 6)  
        
        self.OpenTwoPLaserShutterCheckbox = QCheckBox("Open shutter first")
        self.OpenTwoPLaserShutterCheckbox.setStyleSheet('color:blue;font:bold "Times New Roman"')
        self.OpenTwoPLaserShutterCheckbox.setChecked(True)
        PipelineContainerLayout.addWidget(self.OpenTwoPLaserShutterCheckbox, 0, 8)
        
#        self.BefKCLRoundNumBox = QSpinBox(self)
#        self.BefKCLRoundNumBox.setMinimum(1)
#        self.BefKCLRoundNumBox.setMaximum(1000)
#        self.BefKCLRoundNumBox.setValue(1)
#        self.BefKCLRoundNumBox.setSingleStep(1)
#        self.BefKCLRoundNumBox.setMaximumWidth(30)
#        PipelineContainerLayout.addWidget(self.BefKCLRoundNumBox, 0, 7)
#        PipelineContainerLayout.addWidget(QLabel("Bef-Round Num:"), 0, 6)
#
#        self.AftKCLRoundNumBox = QSpinBox(self)
#        self.AftKCLRoundNumBox.setMinimum(1)
#        self.AftKCLRoundNumBox.setMaximum(1000)
#        self.AftKCLRoundNumBox.setValue(3)
#        self.AftKCLRoundNumBox.setSingleStep(1)
#        self.AftKCLRoundNumBox.setMaximumWidth(30)
#        PipelineContainerLayout.addWidget(self.AftKCLRoundNumBox, 0, 9)
#        PipelineContainerLayout.addWidget(QLabel("Aft-Round Num:"), 0, 8)        
        
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
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:hover:!pressed {color:gray;background-color: teal; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        

        ButtonDeleteWaveform = QPushButton('Delete Waveform', self)
        ButtonDeleteWaveform.setStyleSheet("QPushButton {color:white;background-color: crimson; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:hover:!pressed {color:gray;background-color: crimson; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        
        ButtonClearWaveform = QPushButton('Clear Waveforms', self)
        ButtonClearWaveform.setStyleSheet("QPushButton {color:white;background-color: maroon; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                        "QPushButton:hover:!pressed {color:gray;background-color: maroon; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")        

        RoundContainerLayout.addWidget(ButtonAddWaveform, 0, 3)
        RoundContainerLayout.addWidget(ButtonDeleteWaveform, 0, 4)
        RoundContainerLayout.addWidget(ButtonClearWaveform, 0, 5)
        ButtonAddWaveform.clicked.connect(self.AddFreshWaveform)
        ButtonDeleteWaveform.clicked.connect(self.DeleteFreshWaveform)
        ButtonClearWaveform.clicked.connect(self.ClearWaveformQueue)
        
        self.Waveformer_widget_instance = NIDAQ.Waveformer_for_screening.WaveformGenerator()
        self.Waveformer_widget_instance.WaveformPackage.connect(self.UpdateWaveformerSignal)
        self.Waveformer_widget_instance.GalvoScanInfor.connect(self.UpdateWaveformerGalvoInfor)

        RoundContainerLayout.addWidget(self.Waveformer_widget_instance, 2, 0, 2, 9)
        RoundContainer.setLayout(RoundContainerLayout)
        
        PipelineContainerLayout.addWidget(RoundContainer, 3, 0, 4, 10)       
        #--------------------------------------------------------------------------------------------------------------------------------------     

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
        #--------------------------------------------------------------------------------------------------------------------------------------
        
        PipelineContainer.setLayout(PipelineContainerLayout)
        
        self.layout.addWidget(GeneralSettingContainer, 1, 0, 1, 4)
        self.layout.addWidget(FocusCorrectionContainer, 2, 0, 1, 2)
        self.layout.addWidget(ImageDisplayContainer, 2, 2, 1, 2)
        self.layout.addWidget(ToolWidgetsContainer, 4, 0, 1, 1)
        self.layout.addWidget(self.PostProcessTab, 4, 1, 1, 3)
        self.layout.addWidget(PipelineContainer, 5, 0, 1, 4)
        self.setLayout(self.layout)
        
    """
    # =============================================================================
    #     FUNCTIONS FOR EXECUTION
    # =============================================================================
    """
    # =============================================================================
    # ------------------------------------------------------------Waveform package functions--------------------------------------------------------------------------        
    # =============================================================================
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
    
    # =============================================================================
    #     #--------------------------------------------------------------Round package functions------------------------------------------------------------------------        
    # =============================================================================
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
        self.RoundQueueDict = {}
        self.RoundQueueDict['InsightEvents'] = []
        self.RoundQueueDict['FilterEvents'] = []
        self.RoundCoordsDict = {}
        self.WaveformQueueDict_GalvoInfor = {}
        self.GeneralSettingDict = {}
        self.FocusStackInfoDict = {}
        
        self.normalOutputWritten('Rounds cleared.\n')
        print('Rounds cleared.')
        
    """
    # =============================================================================
    #     Configure general settings, get ready for execution      
    # =============================================================================
    """
    def ConfigGeneralSettings(self):
#        selectnum = self.selec_num_box.value()
#        if self.ComBoxSelectionFactor_1.currentText() == 'Mean intensity in contour weight':
#            MeanIntensityContourWeight = self.WeightBoxSelectionFactor_1.value()
#        elif self.ComBoxSelectionFactor_1.currentText() == 'Contour soma ratio weight':
#            ContourSomaRatioWeight = self.WeightBoxSelectionFactor_1.value()
#        elif self.ComBoxSelectionFactor_1.currentText() == 'Change weight':
#            ChangeWeight = self.WeightBoxSelectionFactor_1.value()
#            
#        if self.ComBoxSelectionFactor_2.currentText() == 'Mean intensity in contour weight':
#            MeanIntensityContourWeight = self.WeightBoxSelectionFactor_2.value()
#        elif self.ComBoxSelectionFactor_2.currentText() == 'Contour soma ratio weight':
#            ContourSomaRatioWeight = self.WeightBoxSelectionFactor_2.value()
#        elif self.ComBoxSelectionFactor_2.currentText() == 'Change weight':
#            ChangeWeight = self.WeightBoxSelectionFactor_2.value()
#            
#        if self.ComBoxSelectionFactor_3.currentText() == 'Mean intensity in contour weight':
#            MeanIntensityContourWeight = self.WeightBoxSelectionFactor_3.value()
#        elif self.ComBoxSelectionFactor_3.currentText() == 'Contour soma ratio weight':
#            ContourSomaRatioWeight = self.WeightBoxSelectionFactor_3.value()
#        elif self.ComBoxSelectionFactor_3.currentText() == 'Change weight':
#            ChangeWeight = self.WeightBoxSelectionFactor_3.value()
#        
#        BefRoundNum = int(self.BefKCLRoundNumBox.value())        
#        AftRoundNum = int(self.AftKCLRoundNumBox.value())        
#        smallestsize = int(self.IPsizetextbox.value())            
#        openingfactor = int(self.opening_factorBox.value())
#        closingfactor = int(self.closing_factorBox.value())
#        cellopeningfactor = int(self.cellopening_factorBox.value())
#        cellclosingfactor = int(self.cellclosing_factorBox.value())
#        binary_adaptive_block_size = int(self.binary_adaptive_block_sizeBox.value())
#        self_findcontour_thres = float(self.find_contour_thres_box.value())
#        contour_dilation = int(self.contour_dilation_box.value())
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
        
#        print(self.FocusCorrectionMatrixDict.keys())
#        generalnamelist = ['selectnum', 'Mean intensity in contour weight','Contour soma ratio weight','Change weight', 'BefRoundNum', 
#                            'AftRoundNum', 'smallestsize', 'openingfactor', 'closingfactor', 'cellopeningfactor', 
#                           'cellclosingfactor', 'binary_adaptive_block_size', 'self_findcontour_thres', 'contour_dilation', 'savedirectory', 'FocusCorrectionMatrixDict', 'FocusStackInfoDict']
#        
#        generallist = [selectnum, MeanIntensityContourWeight, ContourSomaRatioWeight, ChangeWeight, BefRoundNum, AftRoundNum, smallestsize, openingfactor, closingfactor, cellopeningfactor, 
#                       cellclosingfactor, binary_adaptive_block_size, self_findcontour_thres, contour_dilation, savedirectory, self.FocusCorrectionMatrixDict, self.FocusStackInfoDict]
        generalnamelist = ['savedirectory', 'FocusCorrectionMatrixDict', 'FocusStackInfoDict', 'Meshgrid', 'Scanning step', 'StartUpEvents']
        
        generallist = [savedirectory, self.FocusCorrectionMatrixDict, self.FocusStackInfoDict, meshrepeat, self.step, StartUpEvents]
        
        for item in range(len(generallist)):
            self.GeneralSettingDict[generalnamelist[item]] = generallist[item]
#        print(self.GeneralSettingDict['FocusStackInfoDict'])
        self.normalOutputWritten('Rounds configured.\n')
        
        #---------------------------------------------------------------Show general info---------------------------------------------------------------------------------
        self.normalOutputWritten('--------Pipeline general info--------\n')
        for eachround in range(int(len(self.RoundQueueDict)/2-1)):

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
        self.savedirectory = str(QtWidgets.QFileDialog.getExistingDirectory(directory='M:/tnw/ist/do/projects/Neurophotonics/Brinkslab/Data'))
        self.savedirectorytextbox.setText(self.savedirectory)
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
            self.ShowTopCellsInstance = ShowTopCellsThread(self.GeneralSettingDict, self.RankedAllCellProperties, CurrentPosIndex, 
                                                           self.IndexLookUpCellPropertiesDict, self.CurrentImgShowTopCells, self.Matdisplay_Figure)
            self.ShowTopCellsInstance.run()
    #        self.ax = self.ShowTopCellsInstance.gg()
    #        self.ax = self.Matdisplay_Figure.add_subplot(111)
            self.Matdisplay_Canvas.draw()
#            if self.popnexttopimgcounter < (self.TotalCoordsNum-1):
            self.popnexttopimgcounter += 1 # Alwasy plus 1 to get it ready for next move.
            
        elif direction == 'previous':
            self.popnexttopimgcounter -= 2 
            if self.popnexttopimgcounter >= 0:
                CurrentPosIndex = self.FinalMergedCoords[self.popnexttopimgcounter,:].tolist() # self.popnexttopimgcounter is the order number of each Stage coordinates.
                
                self.TopCoordsLabel.setText("Row: {} Col: {}".format(CurrentPosIndex[0], CurrentPosIndex[1]))     
                self.CurrentImgShowTopCells = self.PMTimageDict['RoundPackage_{}'.format(self.GeneralSettingDict['BefRoundNum'])]['row_{}_column_{}'.format(CurrentPosIndex[0], CurrentPosIndex[1])]
                self.ShowTopCellsInstance = ShowTopCellsThread(self.GeneralSettingDict, self.RankedAllCellProperties, CurrentPosIndex, 
                                                               self.IndexLookUpCellPropertiesDict, self.CurrentImgShowTopCells, self.Matdisplay_Figure)
                self.ShowTopCellsInstance.run()
        #        self.ax = self.ShowTopCellsInstance.gg()
        #        self.ax = self.Matdisplay_Figure.add_subplot(111)
                self.Matdisplay_Canvas.draw()
                if self.popnexttopimgcounter < (self.TotalCoordsNum-1):
                    self.popnexttopimgcounter += 1
            else:
                self.popnexttopimgcounter = 0
        
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
                        self.normalOutputWritten('Lasting time:{} s.\n'.format(len(self.RoundQueueDict['RoundPackage_'+
                                                 str(eachround+1)][eachwaveform][2]['Waveform'][0])/self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][0]))
                        
                        print('Lasting time:{} s.\n'.format(len(self.RoundQueueDict['RoundPackage_'+
                              str(eachround+1)][eachwaveform][2]['Waveform'][0])/self.RoundQueueDict['RoundPackage_'+str(eachround+1)][eachwaveform][0]))
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
        
    """
    # =============================================================================
    #     FUNCTIONS FOR DATA ANALYSIS AND DISPLAY
    # =============================================================================
    """
    def SetAnalysisPath(self):
        self.Analysissavedirectory = str(QtWidgets.QFileDialog.getExistingDirectory())
        self.datasavedirectorytextbox.setText(self.Analysissavedirectory)
        
        if self.FilepathSwitchBox.currentText() == 'Tag':
            self.Tag_folder = self.Analysissavedirectory
        elif self.FilepathSwitchBox.currentText() == 'Lib':
            self.Lib_folder = self.Analysissavedirectory     
        elif self.FilepathSwitchBox.currentText() == 'All':
            self.Tag_folder = self.Analysissavedirectory
            self.Lib_folder = self.Analysissavedirectory    
        
    def SetAnalysisRound(self):

        if self.FilepathSwitchBox.currentText() == 'Tag':
            self.Tag_round_infor.append(self.AnalysisRoundBox.value())
        elif self.FilepathSwitchBox.currentText() == 'Lib':
            self.Lib_round_infor.append(self.AnalysisRoundBox.value())
        
        self.normalOutputWritten('Tag_round_infor: {}\nLib_round_infor: {}\n'.format(str(self.Tag_round_infor), str(self.Lib_round_infor)))
        
    def ClearAnalysisInfor(self):
        self.Tag_folder = None
        self.Lib_folder = None
        self.Tag_round_infor = []
        self.Lib_round_infor = []
    
    def StartScreeningAnalysisThread(self):
        
        self.ScreeningAnalysis_thread = threading.Thread(target = self.ScreeningAnalysis, daemon = True)
        self.ScreeningAnalysis_thread.start()  
    
    def ScreeningAnalysis(self):
        # For the brightness screening
        if self.AnalysisTypeSwitchBox.currentText() == 'Brightness screening':

            self.normalOutputWritten('Start loading images...\n')
            tag_folder = self.Tag_folder
            lib_folder = self.Lib_folder
        
            tag_round = 'Round{}'.format(self.Tag_round_infor[0])
            lib_round = 'Round{}'.format(self.Lib_round_infor[0])
            
            tagprotein_cell_properties_dict = ProcessImage.TagFluorescenceAnalysis(tag_folder, tag_round, Roundness_threshold = self.SelectionRoundness_thres_box.value())
            self.normalOutputWritten('tag done...\n')
            
            lib_cell_properties_dict = ProcessImage.LibFluorescenceAnalysis(lib_folder, tag_round, lib_round, tagprotein_cell_properties_dict)
            self.normalOutputWritten('lib done...\n')
            
            # Devided by fusion protein brightness.
            self.lib_cell_properties_dict = ProcessImage.CorrectForFusionProtein(tagprotein_cell_properties_dict, lib_cell_properties_dict, tagprotein_laserpower=1, lib_laserpower=30)
            
    def UpdateSelectionScatter(self):
        lib_cell_properties_dict = self.lib_cell_properties_dict
        IntensityThreshold = self.SelectionMeanInten_thres_box.value()
        CSratioThreshold = self.SelectionCSratio_thres_box.value()
        self.EvaluatingPara_list = str(self.SeleParaBox.currentText()).split("/")
        
        self.Matdisplay_Figure.clear()
        if self.Selection_boundaryBox.currentText() == 'Circular radius':
#            selectionRadiusPercent = 100 - self.AnalysisCirclePercentBox.value()
            selectionRadiusPercent = 100
            if len(self.EvaluatingPara_list) == 2:
                # Organize and add 'ranking' and 'boundingbox' fields to the structured array.
                axis_1_weight = self.WeightBoxSelectionFactor_1.value()
                axis_2_weight = self.WeightBoxSelectionFactor_2.value()
                self.Overview_LookupBook = ProcessImage.OrganizeOverview(lib_cell_properties_dict, ['Mean intensity in contour', IntensityThreshold, 'Contour soma ratio', CSratioThreshold], 
                                                                         self.EvaluatingPara_list[0], axis_1_weight, self.EvaluatingPara_list[1], axis_2_weight)
                self.Overview_LookupBook = ProcessImage.DistanceSelecting(self.Overview_LookupBook, 100) # Sort the original array according to distance from origin.
                
                self.Overview_LookupBook_filtered = ProcessImage.DistanceSelecting(self.Overview_LookupBook, selectionRadiusPercent)
                
                ax1 = self.Matdisplay_Figure.add_subplot(111)
                ax1.scatter(self.Overview_LookupBook[self.EvaluatingPara_list[0]], self.Overview_LookupBook[self.EvaluatingPara_list[1]], s=np.pi*3, c='blue', alpha=0.5)
                ax1.scatter(self.Overview_LookupBook_filtered[self.EvaluatingPara_list[0]], self.Overview_LookupBook_filtered[self.EvaluatingPara_list[1]], s=np.pi*3, c='red', alpha=0.5)
                ax1.set_xlabel(self.EvaluatingPara_list[0])
                ax1.set_ylabel(self.EvaluatingPara_list[1])
                self.Matdisplay_Figure.tight_layout()
                self.Matdisplay_Canvas.draw()
                
                # Some numbers ready for tracing back
                self.TotaNumofCellSelected = len(self.Overview_LookupBook_filtered)
                self.TotalCellNum = len(self.Overview_LookupBook)
                self.normalOutputWritten('---- Total cells selected: {}; Total cells: {}----\n'.format(self.TotaNumofCellSelected, self.TotalCellNum))
                
                fig = px.scatter(self.Overview_LookupBook, x=self.EvaluatingPara_list[0], y=self.EvaluatingPara_list[1], 
                hover_name= 'ID', color= 'Normalized distance', 
                hover_data= ['Sequence', 'Mean intensity'], width=1050, height=950)
                fig.write_html('Screening scatters.html', auto_open=True)
                
    def GoThroughTopCells(self, direction):
        
        if direction == 'next':
            if self.popnexttopimgcounter > (self.TotaNumofCellSelected-1):#Make sure it doesn't go beyond the last coords.
                self.popnexttopimgcounter -= 1
            
            self.CurrentRankCellpProperties = self.Overview_LookupBook_filtered[self.popnexttopimgcounter]
            
            #--------------------Show image with cell in box----------------------
            spec = self.CurrentRankCellpProperties['ID']
            print(spec)
    #        #-------------- readin image---------------
            tag_imagefilename = os.path.join(self.Tag_folder, spec+'_PMT_0Zmax.tif')
            print(tag_imagefilename)
            loaded_tag_image_display = imread(tag_imagefilename, as_gray=True)
            # Retrieve boundingbox information
            Each_bounding_box = self.CurrentRankCellpProperties['BoundingBox']
            minr = int(Each_bounding_box[Each_bounding_box.index('minr')+4:Each_bounding_box.index('_minc')])
            maxr = int(Each_bounding_box[Each_bounding_box.index('maxr')+4:Each_bounding_box.index('_maxc')])        
            minc = int(Each_bounding_box[Each_bounding_box.index('minc')+4:Each_bounding_box.index('_maxr')])
            maxc = int(Each_bounding_box[Each_bounding_box.index('maxc')+4:len(Each_bounding_box)])
            
            self.Matdisplay_Figure.clear()
            ax1 = self.Matdisplay_Figure.add_subplot(111)
            ax1.imshow(loaded_tag_image_display)#Show the first image
            #--------------------------------------------------Add red boundingbox to axis----------------------------------------------
            rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr, fill=False, edgecolor='cyan', linewidth=2)
            ax1.add_patch(rect)
            ax1.text(maxc, minr, 'NO_{}'.format(self.popnexttopimgcounter),fontsize=10, color='orange', style='italic')
            self.Matdisplay_Figure.tight_layout()
            self.Matdisplay_Canvas.draw()
            
            #-------------------Print details of cell of interest----------------
            self.normalOutputWritten('------------------No.{} out of {}----------------\n'.format(self.popnexttopimgcounter+1, self.TotaNumofCellSelected))
            self.normalOutputWritten('ID: {}\n{}: {}\n{}: {}\n'.format(spec, self.EvaluatingPara_list[0], round(self.CurrentRankCellpProperties[self.EvaluatingPara_list[0]], 4), \
                                                                     self.EvaluatingPara_list[1], round(self.CurrentRankCellpProperties[self.EvaluatingPara_list[1]], 4)))
            #------------------Stage move----------------------------------------
#            self.CurrentPos = spec[spec.index('_R')+2:len(spec)].split('C')
#            self.ludlStage.moveAbs(int(self.CurrentPos[0]),int(self.CurrentPos[1]))
            
            self.popnexttopimgcounter += 1 # Alwasy plus 1 to get it ready for next move.
            
        elif direction == 'previous':
            self.popnexttopimgcounter -= 2 
            if self.popnexttopimgcounter >= 0:
                
                self.CurrentRankCellpProperties = self.Overview_LookupBook_filtered[self.popnexttopimgcounter]
                
                #--------------------Show image with cell in box----------------------
                spec = self.CurrentRankCellpProperties['ID']
        #        #-------------- readin image---------------
                tag_imagefilename = os.path.join(self.Tag_folder, spec+'_PMT_0Zmax.tif')
    
                loaded_tag_image_display = imread(tag_imagefilename, as_gray=True)
                # Retrieve boundingbox information
                Each_bounding_box = self.CurrentRankCellpProperties['BoundingBox']
                minr = int(Each_bounding_box[Each_bounding_box.index('minr')+4:Each_bounding_box.index('_minc')])
                maxr = int(Each_bounding_box[Each_bounding_box.index('maxr')+4:Each_bounding_box.index('_maxc')])        
                minc = int(Each_bounding_box[Each_bounding_box.index('minc')+4:Each_bounding_box.index('_maxr')])
                maxc = int(Each_bounding_box[Each_bounding_box.index('maxc')+4:len(Each_bounding_box)])
                
                self.Matdisplay_Figure.clear()
                ax1 = self.Matdisplay_Figure.add_subplot(111)
                ax1.imshow(loaded_tag_image_display)#Show the first image
                #--------------------------------------------------Add red boundingbox to axis----------------------------------------------
                rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr, fill=False, edgecolor='cyan', linewidth=2)
                ax1.add_patch(rect)
                ax1.text(maxc, minr, 'NO_{}'.format(self.popnexttopimgcounter),fontsize=10, color='orange', style='italic')
                self.Matdisplay_Figure.tight_layout()
                self.Matdisplay_Canvas.draw()
                
                #-------------------Print details of cell of interest----------------
                self.normalOutputWritten('------------------No.{} out of {}----------------\n'.format(self.popnexttopimgcounter+1, self.TotaNumofCellSelected))
                self.normalOutputWritten('ID: {}\n{}: {}\n{}: {}\n'.format(spec, self.EvaluatingPara_list[0], round(self.CurrentRankCellpProperties[self.EvaluatingPara_list[0]], 4), \
                                                                     self.EvaluatingPara_list[1], round(self.CurrentRankCellpProperties[self.EvaluatingPara_list[1]], 4)))
                
                #------------------Stage move----------------------------------------
#                self.CurrentPos = spec[spec.index('_R')+2:len(spec)].split('C')
#                self.ludlStage.moveAbs(int(self.CurrentPos[0]),int(self.CurrentPos[1]))
                
                if self.popnexttopimgcounter < (self.TotaNumofCellSelected-1):
                    self.popnexttopimgcounter += 1
            else:
                self.popnexttopimgcounter = 0
                
        elif direction == 'null':
            self.popnexttopimgcounter -= 1
            
            self.CurrentRankCellpProperties = self.Overview_LookupBook_filtered[self.popnexttopimgcounter]
            
            #--------------------Show image with cell in box----------------------
            spec = self.CurrentRankCellpProperties['ID']
    #        #-------------- readin image---------------
            tag_imagefilename = os.path.join(self.Tag_folder, spec+'_PMT_0Zmax.tif')

            loaded_tag_image_display = imread(tag_imagefilename, as_gray=True)
            # Retrieve boundingbox information
            Each_bounding_box = self.CurrentRankCellpProperties['BoundingBox']
            minr = int(Each_bounding_box[Each_bounding_box.index('minr')+4:Each_bounding_box.index('_minc')])
            maxr = int(Each_bounding_box[Each_bounding_box.index('maxr')+4:Each_bounding_box.index('_maxc')])        
            minc = int(Each_bounding_box[Each_bounding_box.index('minc')+4:Each_bounding_box.index('_maxr')])
            maxc = int(Each_bounding_box[Each_bounding_box.index('maxc')+4:len(Each_bounding_box)])
            
            self.Matdisplay_Figure.clear()
            ax1 = self.Matdisplay_Figure.add_subplot(111)
            ax1.imshow(loaded_tag_image_display)#Show the first image
            #--------------------------------------------------Add red boundingbox to axis----------------------------------------------
            rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr, fill=False, edgecolor='cyan', linewidth=2)
            ax1.add_patch(rect)
            ax1.text(maxc, minr, 'NO_{}'.format(self.popnexttopimgcounter),fontsize=10, color='orange', style='italic')
            self.Matdisplay_Figure.tight_layout()
            self.Matdisplay_Canvas.draw()
            
            self.popnexttopimgcounter += 1
            
    def ShowScatterPos(self):
        if self.ButtonShowInScatter.isChecked():
            self.Matdisplay_Figure.clear()
            ax1 = self.Matdisplay_Figure.add_subplot(111)
            ax1.scatter(self.Overview_LookupBook[self.EvaluatingPara_list[0]], self.Overview_LookupBook[self.EvaluatingPara_list[1]], s=np.pi*3, c='blue', alpha=0.5)
            ax1.scatter(self.Overview_LookupBook_filtered[self.EvaluatingPara_list[0]], self.Overview_LookupBook_filtered[self.EvaluatingPara_list[1]], s=np.pi*3, c='blue', alpha=0.5)
            ax1.scatter(self.Overview_LookupBook_filtered[self.popnexttopimgcounter-1][self.EvaluatingPara_list[0]], self.Overview_LookupBook_filtered[self.popnexttopimgcounter-1][self.EvaluatingPara_list[1]], 
                        s=np.pi*6, c='yellow', alpha=0.5)
            ax1.set_xlabel(self.EvaluatingPara_list[0])
            ax1.set_ylabel(self.EvaluatingPara_list[1])
            self.Matdisplay_Figure.tight_layout()
            self.Matdisplay_Canvas.draw()            
        else:
            self.GoThroughTopCells('null')
            
    def DeleteFromTopCells(self):
        self.popnexttopimgcounter -= 1
        self.Overview_LookupBook_filtered = np.delete(self.Overview_LookupBook_filtered, self.popnexttopimgcounter, 0)
#        self.Overview_LookupBook = np.delete(self.Overview_LookupBook, self.popnexttopimgcounter, 0) # Overview_LookupBook is also sorted according to distance, 
#                                                                                                     # that's why delete the same index as above.
        self.TotaNumofCellSelected -= 1
    
    def SaveCellsProArray(self):
        np.save(os.path.join(self.savedirectory, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_CellsProperties'), self.Overview_LookupBook)
        
    def ResetRankCoord(self):
        self.popnexttopimgcounter = 0
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
