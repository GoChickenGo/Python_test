# -*- coding: utf-8 -*-
"""
Created on Fri Apr 24 11:05:50 2020

@author: xinmeng
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

from datetime import datetime
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.express as px

from ImageAnalysis.EvolutionAnalysis_v2 import ProcessImage


class MainGUI(QWidget):
    
    waveforms_generated = pyqtSignal(object, object, list, int)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        os.chdir('./')# Set directory to current folder.
        self.setFont(QFont("Arial"))
        
#        self.setMinimumSize(900, 1020)
        self.setWindowTitle("Screening Analysis")
        self.layout = QGridLayout(self)
        
        self.popnexttopimgcounter = 0
        self.Tag_round_infor = []
        self.Lib_round_infor = []
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for Billboard display------------------------------------------------------
        #**************************************************************************************************************************************
        ImageDisplayContainer = QGroupBox("Billboard")
        ImageDisplayContainerLayout = QGridLayout()
        
        self.GraphyDisplayTab = QTabWidget()
        
        #----------------------------------------------------------------------
        MatDsiplayPart = QWidget()
        MatDsiplayPart.layout = QGridLayout()        
        
        # a figure instance to plot on
        self.Matdisplay_Figure = Figure()
        self.Matdisplay_Canvas = FigureCanvas(self.Matdisplay_Figure)
        
        self.Matdisplay_toolbar = NavigationToolbar(self.Matdisplay_Canvas, self)
        MatDsiplayPart.layout.addWidget(self.Matdisplay_toolbar, 0, 0)  
        MatDsiplayPart.layout.addWidget(self.Matdisplay_Canvas, 1, 0)
        MatDsiplayPart.setLayout(MatDsiplayPart.layout)
        
        self.OriginalImgWidget = pg.ImageView()
        self.OriginalImg_item = self.OriginalImgWidget.getImageItem() #setLevels
        self.OriginalImg_view = self.OriginalImgWidget.getView()
        self.OriginalImg_item.setAutoDownsample(True)
        
        self.OriginalImgWidget.ui.roiBtn.hide()
        self.OriginalImgWidget.ui.menuBtn.hide() 
        self.OriginalImgWidget.ui.normGroup.hide()
        self.OriginalImgWidget.ui.roiPlot.hide()
        
        self.GraphyDisplayTab.addTab(self.OriginalImgWidget, "Image loaded")
        self.GraphyDisplayTab.addTab(MatDsiplayPart,"Scatter")
        
        ImageDisplayContainerLayout.addWidget(self.GraphyDisplayTab, 1, 1)
        
        #----------------------------------------------------------------------
        ImageButtonContainer = QGroupBox()
        ImageButtonContainerLayout = QGridLayout()
        
        ButtonRankResetCoordImg = QPushButton('Reset coord', self)
        ButtonRankResetCoordImg.clicked.connect(self.ResetRankCoord)
        ImageButtonContainerLayout.addWidget(ButtonRankResetCoordImg, 0, 6)
        
        ButtonRankPreviousCoordImg = QPushButton('Previous', self)
        ButtonRankPreviousCoordImg.setShortcut('a')
        ButtonRankPreviousCoordImg.clicked.connect(lambda: self.GoThroughTopCells('previous'))
        ImageButtonContainerLayout.addWidget(ButtonRankPreviousCoordImg, 1, 6)
        
        self.ButtonShowInScatter = QPushButton('Show in scatter', self)
        self.ButtonShowInScatter.setShortcut('s')
        self.ButtonShowInScatter.setCheckable(True)
        self.ButtonShowInScatter.clicked.connect(self.ShowScatterPos)
        ImageButtonContainerLayout.addWidget(self.ButtonShowInScatter, 2, 6)

        ButtonRankNextCoordImg = QPushButton('Next', self)
        ButtonRankNextCoordImg.setShortcut('d')
        ButtonRankNextCoordImg.clicked.connect(lambda: self.GoThroughTopCells('next'))
        ImageButtonContainerLayout.addWidget(ButtonRankNextCoordImg, 1, 7)
        
        GoSeqButton = QPushButton('Go to IDNumber: ', self)
        GoSeqButton.clicked.connect(self.GotoSequence)
        ImageButtonContainerLayout.addWidget(GoSeqButton, 3, 6)
        
        self.ShowSequenceScatterButton = QPushButton('Show this in scatter', self)
        self.ShowSequenceScatterButton.setCheckable(True)
        self.ShowSequenceScatterButton.clicked.connect(self.ShowSequenceScatter)
        ImageButtonContainerLayout.addWidget(self.ShowSequenceScatterButton, 3, 8)
        
        self.CellSequenceBox = QSpinBox(self)
        self.CellSequenceBox.setMaximum(9000)
        self.CellSequenceBox.setValue(0)
        self.CellSequenceBox.setSingleStep(1)
        ImageButtonContainerLayout.addWidget(self.CellSequenceBox, 3, 7)
        
        ButtonRankDeleteFromList = QPushButton('Delete', self)
        ButtonRankDeleteFromList.clicked.connect(self.DeleteFromTopCells)
        ImageButtonContainerLayout.addWidget(ButtonRankDeleteFromList, 2, 7)
        
        ButtonRankSaveList = QPushButton('Save array', self)
        ButtonRankSaveList.clicked.connect(self.SaveCellsProArray)
        ImageButtonContainerLayout.addWidget(ButtonRankSaveList, 4, 6)
        
        self.ConsoleTextDisplay = QTextEdit()
        self.ConsoleTextDisplay.setFontItalic(True)
        self.ConsoleTextDisplay.setPlaceholderText('Notice board from console.')
        self.ConsoleTextDisplay.setMaximumHeight(300)
        ImageButtonContainerLayout.addWidget(self.ConsoleTextDisplay, 5, 6, 3, 2)
        
        ImageButtonContainer.setLayout(ImageButtonContainerLayout)
        
        ImageDisplayContainer.setLayout(ImageDisplayContainerLayout)
        ImageDisplayContainer.setMinimumHeight(700)
        ImageDisplayContainer.setMinimumWidth(700)
        
        self.layout.addWidget(ImageDisplayContainer, 0, 0, 2, 2)
        self.layout.addWidget(ImageButtonContainer, 0, 2)
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for Image processing settings------------------------------------------
        #**************************************************************************************************************************************
        self.PostProcessTab = QTabWidget()
        self.PostProcessTab.setMaximumWidth(400)
        self.PostProcessTab.setFixedHeight(250)
        
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
        
        #---------------------------Loading------------------------------------
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
        LoadSettingLayout.addWidget(self.datasavedirectorytextbox, 1, 0, 1, 2)
        
        self.toolButtonOpenDialog = QtWidgets.QPushButton('Set path')
        self.toolButtonOpenDialog.clicked.connect(self.SetAnalysisPath)
        LoadSettingLayout.addWidget(self.toolButtonOpenDialog, 1, 2)
        
        ExecuteAnalysisButton = QPushButton('Load images', self)
#        ExecuteAnalysisButton.setObjectName('Startbutton')
        ExecuteAnalysisButton.clicked.connect(lambda: self.StartScreeningAnalysisThread())
        LoadSettingLayout.addWidget(ExecuteAnalysisButton, 2, 1)
        
        self.ClearAnalysisInforButton = QtWidgets.QPushButton('Clear infor')
        self.ClearAnalysisInforButton.clicked.connect(self.ClearAnalysisInfor)
        LoadSettingLayout.addWidget(self.ClearAnalysisInforButton, 2, 2)        

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
        
        UpdateProcessTab = QTabWidget()
        UpdateProcessTab.layout = QGridLayout()
        
        UpdateProcessTab_1 = QWidget()
        UpdateProcessTab_1.layout = QGridLayout()
        
        UpdateProcessTab_1.layout.addWidget(QLabel("Selection boundary:"), 0, 0)
        
        self.Selection_boundaryBox = QComboBox()
        self.Selection_boundaryBox.addItems(['Circular radius', 'Rank'])
        UpdateProcessTab_1.layout.addWidget(self.Selection_boundaryBox, 0, 1)
        
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
        UpdateProcessTab_2.layout.addWidget(QLabel("Axis 1:"), 0, 0)
        
        self.WeightBoxSelectionFactor_2 = QDoubleSpinBox(self)
        self.WeightBoxSelectionFactor_2.setDecimals(2)
        self.WeightBoxSelectionFactor_2.setMinimum(0)
        self.WeightBoxSelectionFactor_2.setMaximum(1)
        self.WeightBoxSelectionFactor_2.setValue(0.5)
        self.WeightBoxSelectionFactor_2.setSingleStep(0.1)  
        UpdateProcessTab_2.layout.addWidget(self.WeightBoxSelectionFactor_2, 0, 3)  
        UpdateProcessTab_2.layout.addWidget(QLabel("Axis 2:"), 0, 2)
        
        self.WeightBoxSelectionFactor_3 = QDoubleSpinBox(self)
        self.WeightBoxSelectionFactor_3.setDecimals(2)
        self.WeightBoxSelectionFactor_3.setMinimum(0)
        self.WeightBoxSelectionFactor_3.setMaximum(1)
        self.WeightBoxSelectionFactor_3.setValue(1)
        self.WeightBoxSelectionFactor_3.setSingleStep(0.1)  
        UpdateProcessTab_2.layout.addWidget(self.WeightBoxSelectionFactor_3, 0, 5)  
        UpdateProcessTab_2.layout.addWidget(QLabel("Axis 3:"), 0, 4)
        
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
        
        UpdateProcessTab_2.layout.addWidget(SelectionthresholdsettingTab, 1, 0, 1, 6)
        
        UpdateProcessTab_1.setLayout(UpdateProcessTab_1.layout)
        UpdateProcessTab_2.setLayout(UpdateProcessTab_2.layout)
        UpdateProcessTab.addTab(UpdateProcessTab_1,"Normalized distance") 
        UpdateProcessTab.addTab(UpdateProcessTab_2,"Axes weights") 
        SelectionsettingTab.layout.addWidget(UpdateProcessTab, 1, 0, 4, 3)
        
        SelectionsettingTab.setLayout(SelectionsettingTab.layout)

        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for Selection threshold settings---------------------------------------
        #**************************************************************************************************************************************

        
        self.PostProcessTab.addTab(LoadSettingContainer,"Loading settings")        
        self.PostProcessTab.addTab(SelectionsettingTab,"Analysis selection")        
        self.PostProcessTab.addTab(ImageProcessingContainer,"Image analysis settings")
        
        self.layout.addWidget(self.PostProcessTab, 1, 2)
        
        self.setLayout(self.layout)
        
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
            
            self.UpdateSelectionScatter()
            
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
                # Sort the original array according to distance from origin.
                self.Overview_LookupBook = ProcessImage.DistanceSelecting(self.Overview_LookupBook, 100) 
                
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
                hover_data= ['IDNumber', 'Mean intensity'], width=1050, height=950)
                fig.write_html('Screening scatters.html', auto_open=True)
                
    def GoThroughTopCells(self, direction):
        
        if direction == 'next':
            if self.popnexttopimgcounter > (self.TotaNumofCellSelected-1):#Make sure it doesn't go beyond the last coords.
                self.popnexttopimgcounter -= 1
            
            self.CurrentRankCellpProperties = self.Overview_LookupBook[self.popnexttopimgcounter]
            
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
            maxr = int(Each_bounding_box[Each_bounding_box.index('maxr')+4:Each_bounding_box.index('_maxc')]) - 1        
            minc = int(Each_bounding_box[Each_bounding_box.index('minc')+4:Each_bounding_box.index('_maxr')])
            maxc = int(Each_bounding_box[Each_bounding_box.index('maxc')+4:len(Each_bounding_box)]) - 1
            
            loaded_tag_image_display[minr, minc:maxc] = 4
            loaded_tag_image_display[maxr, minc:maxc] = 4
            loaded_tag_image_display[minr:maxr, minc] = 4
            loaded_tag_image_display[minr:maxr, maxc] = 4
            
            # -------Show image in imageview-------------
            self.OriginalImg_item.setImage(np.fliplr(np.rot90(loaded_tag_image_display)), autoLevels=True)
            self.OriginalImg_item.setLevels((0, 1))
            
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
            self.normalOutputWritten('ID: {}\n{}: {}\n{}: {}\n{}: {}\n'.format(spec, self.EvaluatingPara_list[0], round(self.CurrentRankCellpProperties[self.EvaluatingPara_list[0]], 4), \
                                                                     self.EvaluatingPara_list[1], round(self.CurrentRankCellpProperties[self.EvaluatingPara_list[1]], 4), 
                                                                     'IDNumber', self.CurrentRankCellpProperties['IDNumber']))
            #------------------Stage move----------------------------------------
#            self.CurrentPos = spec[spec.index('_R')+2:len(spec)].split('C')
#            self.ludlStage.moveAbs(int(self.CurrentPos[0]),int(self.CurrentPos[1]))
            
            self.popnexttopimgcounter += 1 # Alwasy plus 1 to get it ready for next move.
            
        elif direction == 'previous':
            self.popnexttopimgcounter -= 2 
            if self.popnexttopimgcounter >= 0:
                
                self.CurrentRankCellpProperties = self.Overview_LookupBook[self.popnexttopimgcounter]
                
                #--------------------Show image with cell in box----------------------
                spec = self.CurrentRankCellpProperties['ID']
        #        #-------------- readin image---------------
                tag_imagefilename = os.path.join(self.Tag_folder, spec+'_PMT_0Zmax.tif')
    
                loaded_tag_image_display = imread(tag_imagefilename, as_gray=True)
                # Retrieve boundingbox information
                Each_bounding_box = self.CurrentRankCellpProperties['BoundingBox']
                minr = int(Each_bounding_box[Each_bounding_box.index('minr')+4:Each_bounding_box.index('_minc')])
                maxr = int(Each_bounding_box[Each_bounding_box.index('maxr')+4:Each_bounding_box.index('_maxc')])-1      
                minc = int(Each_bounding_box[Each_bounding_box.index('minc')+4:Each_bounding_box.index('_maxr')])
                maxc = int(Each_bounding_box[Each_bounding_box.index('maxc')+4:len(Each_bounding_box)])-1
                
                loaded_tag_image_display[minr, minc:maxc] = 4
                loaded_tag_image_display[maxr, minc:maxc] = 4
                loaded_tag_image_display[minr:maxr, minc] = 4
                loaded_tag_image_display[minr:maxr, maxc] = 4
                
                # -------Show image in imageview-------------
                self.OriginalImg_item.setImage(np.fliplr(np.rot90(loaded_tag_image_display)), autoLevels=True)
                self.OriginalImg_item.setLevels((0, 1))
                
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
                self.normalOutputWritten('ID: {}\n{}: {}\n{}: {}\n{}: {}\n'.format(spec, self.EvaluatingPara_list[0], round(self.CurrentRankCellpProperties[self.EvaluatingPara_list[0]], 4), \
                                                                     self.EvaluatingPara_list[1], round(self.CurrentRankCellpProperties[self.EvaluatingPara_list[1]], 4), 
                                                                     'IDNumber', self.CurrentRankCellpProperties['IDNumber']))
                
                #------------------Stage move----------------------------------------
#                self.CurrentPos = spec[spec.index('_R')+2:len(spec)].split('C')
#                self.ludlStage.moveAbs(int(self.CurrentPos[0]),int(self.CurrentPos[1]))
                
                if self.popnexttopimgcounter < (self.TotaNumofCellSelected-1):
                    self.popnexttopimgcounter += 1
            else:
                self.popnexttopimgcounter = 0
                
        elif direction == 'null':
            self.popnexttopimgcounter -= 1
            
            self.CurrentRankCellpProperties = self.Overview_LookupBook[self.popnexttopimgcounter]
            
            #--------------------Show image with cell in box----------------------
            spec = self.CurrentRankCellpProperties['ID']
    #        #-------------- readin image---------------
            tag_imagefilename = os.path.join(self.Tag_folder, spec+'_PMT_0Zmax.tif')

            loaded_tag_image_display = imread(tag_imagefilename, as_gray=True)
            # Retrieve boundingbox information
            Each_bounding_box = self.CurrentRankCellpProperties['BoundingBox']
            minr = int(Each_bounding_box[Each_bounding_box.index('minr')+4:Each_bounding_box.index('_minc')])
            maxr = int(Each_bounding_box[Each_bounding_box.index('maxr')+4:Each_bounding_box.index('_maxc')])-1
            minc = int(Each_bounding_box[Each_bounding_box.index('minc')+4:Each_bounding_box.index('_maxr')])
            maxc = int(Each_bounding_box[Each_bounding_box.index('maxc')+4:len(Each_bounding_box)])-1
            
            loaded_tag_image_display[minr, minc:maxc] = 4
            loaded_tag_image_display[maxr, minc:maxc] = 4
            loaded_tag_image_display[minr:maxr, minc] = 4
            loaded_tag_image_display[minr:maxr, maxc] = 4
            
            # -------Show image in imageview-------------
            self.OriginalImg_item.setImage(np.fliplr(np.rot90(loaded_tag_image_display)), autoLevels=True)
            self.OriginalImg_item.setLevels((0, 1))
            
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
            
        elif direction == 'IDNumber':
            self.GotoSequence()
            
    def GotoSequence(self):
        """
        Go to a specific cell
        """
        self.SpecificIndexInArray = np.where(self.Overview_LookupBook['IDNumber']==self.CellSequenceBox.value())[0][0]
        self.CurrentRankCellpProperties = self.Overview_LookupBook[self.SpecificIndexInArray]
        
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
        maxr = int(Each_bounding_box[Each_bounding_box.index('maxr')+4:Each_bounding_box.index('_maxc')]) - 1        
        minc = int(Each_bounding_box[Each_bounding_box.index('minc')+4:Each_bounding_box.index('_maxr')])
        maxc = int(Each_bounding_box[Each_bounding_box.index('maxc')+4:len(Each_bounding_box)]) - 1
        
        loaded_tag_image_display[minr, minc:maxc] = 4
        loaded_tag_image_display[maxr, minc:maxc] = 4
        loaded_tag_image_display[minr:maxr, minc] = 4
        loaded_tag_image_display[minr:maxr, maxc] = 4
        
        # -------Show image in imageview-------------
        self.OriginalImg_item.setImage(np.fliplr(np.rot90(loaded_tag_image_display)), autoLevels=True)
        self.OriginalImg_item.setLevels((0, 1))
        
        self.Matdisplay_Figure.clear()
        ax1 = self.Matdisplay_Figure.add_subplot(111)
        ax1.imshow(loaded_tag_image_display)#Show the first image
        #--------------------------------------------------Add red boundingbox to axis----------------------------------------------
        rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr, fill=False, edgecolor='cyan', linewidth=2)
        ax1.add_patch(rect)
        ax1.text(maxc, minr, 'Seq_{}'.format(self.CurrentRankCellpProperties['IDNumber']),fontsize=10, color='orange', style='italic')
        self.Matdisplay_Figure.tight_layout()
        self.Matdisplay_Canvas.draw()
        
        #-------------------Print details of cell of interest----------------
        self.normalOutputWritten('------------------IDNumber {}----------------\n'.format(self.CurrentRankCellpProperties['IDNumber']))
        self.normalOutputWritten('ID: {}\n{}: {}\n{}: {}\n'.format(spec, self.EvaluatingPara_list[0], round(self.CurrentRankCellpProperties[self.EvaluatingPara_list[0]], 4), \
                                                                 self.EvaluatingPara_list[1], round(self.CurrentRankCellpProperties[self.EvaluatingPara_list[1]], 4)))
            
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
            
    def ShowSequenceScatter(self):
        if self.ShowSequenceScatterButton.isChecked():
            self.Matdisplay_Figure.clear()
            ax1 = self.Matdisplay_Figure.add_subplot(111)
            ax1.scatter(self.Overview_LookupBook[self.EvaluatingPara_list[0]], self.Overview_LookupBook[self.EvaluatingPara_list[1]], s=np.pi*3, c='blue', alpha=0.5)
            ax1.scatter(self.Overview_LookupBook_filtered[self.EvaluatingPara_list[0]], self.Overview_LookupBook_filtered[self.EvaluatingPara_list[1]], s=np.pi*3, c='blue', alpha=0.5)
            ax1.scatter(self.Overview_LookupBook_filtered[self.SpecificIndexInArray][self.EvaluatingPara_list[0]], self.Overview_LookupBook_filtered[self.SpecificIndexInArray][self.EvaluatingPara_list[1]], 
                        s=np.pi*6, c='yellow', alpha=0.5)
            ax1.set_xlabel(self.EvaluatingPara_list[0])
            ax1.set_ylabel(self.EvaluatingPara_list[1])
            self.Matdisplay_Figure.tight_layout()
            self.Matdisplay_Canvas.draw()            
        else:
            self.GoThroughTopCells('sequence')
            
    def DeleteFromTopCells(self):
        self.popnexttopimgcounter -= 1
        self.Overview_LookupBook_filtered = np.delete(self.Overview_LookupBook_filtered, self.popnexttopimgcounter, 0)
#        self.Overview_LookupBook = np.delete(self.Overview_LookupBook, self.popnexttopimgcounter, 0) # Overview_LookupBook is also sorted according to distance, 
#                                                                                                     # that's why delete the same index as above.
        self.TotaNumofCellSelected -= 1
    
    def SaveCellsProArray(self):
        np.save(os.path.join(self.Tag_folder, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_CellsProperties'), self.Overview_LookupBook)
        
    def ResetRankCoord(self):
        self.popnexttopimgcounter = 0
        
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        pg.setConfigOptions(imageAxisOrder='row-major')
        mainwin = MainGUI()
        mainwin.show()
        app.exec_()
    run_app() 