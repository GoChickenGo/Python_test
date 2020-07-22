# -*- coding: utf-8 -*-
"""
Created on Wed May 20 18:32:50 2020

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

try:
    from ScreeningAnalysisML import ProcessImageML
except:
    from ImageAnalysis.ScreeningAnalysisML import ProcessImageML

class MainGUI(QWidget):
    
    waveforms_generated = pyqtSignal(object, object, list, int)
    #%%
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
        
        GoSeqButton = QPushButton('Go to Cell_: ', self)
        GoSeqButton.clicked.connect(self.GotoSequence)
        ImageButtonContainerLayout.addWidget(GoSeqButton, 3, 6)
        
        self.ShowSequenceScatterButton = QPushButton('Show this cell in scatter', self)
        self.ShowSequenceScatterButton.setCheckable(True)
        self.ShowSequenceScatterButton.clicked.connect(self.ShowSequenceScatter)
        ImageButtonContainerLayout.addWidget(self.ShowSequenceScatterButton, 4, 6)
        
        self.CellSequenceBox = QSpinBox(self)
        self.CellSequenceBox.setMaximum(9000)
        self.CellSequenceBox.setMinimum(1)
        self.CellSequenceBox.setValue(1)
        self.CellSequenceBox.setSingleStep(1)
        ImageButtonContainerLayout.addWidget(self.CellSequenceBox, 3, 7)
        
#        ButtonRankDeleteFromList = QPushButton('Delete', self)
#        ButtonRankDeleteFromList.clicked.connect(self.DeleteFromTopCells)
#        ImageButtonContainerLayout.addWidget(ButtonRankDeleteFromList, 2, 7)
        
        ButtonRankSaveList = QPushButton('Save Excel', self)
        ButtonRankSaveList.clicked.connect(self.SaveCellsDataframetoExcel)
        ImageButtonContainerLayout.addWidget(ButtonRankSaveList, 2, 7)
        
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
        
        IPLayout.addWidget(QLabel("Contour/soma ratio threshold:"), 0, 0)
        self.Contour_soma_ratio_thres_box = QDoubleSpinBox(self)
        self.Contour_soma_ratio_thres_box.setDecimals(4)
        self.Contour_soma_ratio_thres_box.setMinimum(-10)
        self.Contour_soma_ratio_thres_box.setMaximum(10)
        self.Contour_soma_ratio_thres_box.setValue(1.000)
        self.Contour_soma_ratio_thres_box.setSingleStep(0.0001)  
        IPLayout.addWidget(self.Contour_soma_ratio_thres_box, 0, 1)
        
        IPLayout.addWidget(QLabel("Mean intensity in contour threshold:"), 0, 2)
        self.Mean_intensity_in_contour_thres_box = QDoubleSpinBox(self)
        self.Mean_intensity_in_contour_thres_box.setDecimals(4)
        self.Mean_intensity_in_contour_thres_box.setMinimum(-10)
        self.Mean_intensity_in_contour_thres_box.setMaximum(10)
        self.Mean_intensity_in_contour_thres_box.setValue(0.250)
        self.Mean_intensity_in_contour_thres_box.setSingleStep(0.0001)  
        IPLayout.addWidget(self.Mean_intensity_in_contour_thres_box, 0, 3)
        
        ImageProcessingContainer.setLayout(IPLayout)
        
        #---------------------------Loading------------------------------------
        LoadSettingContainer = QGroupBox()
        LoadSettingLayout = QGridLayout()
        
        self.FilepathSwitchBox = QComboBox()
        self.FilepathSwitchBox.addItems(['All', 'Tag', 'Lib'])
        LoadSettingLayout.addWidget(self.FilepathSwitchBox, 1, 0)
        
        self.AnalysisRoundBox = QSpinBox(self)
        self.AnalysisRoundBox.setMaximum(2000)
        self.AnalysisRoundBox.setValue(1)
        self.AnalysisRoundBox.setSingleStep(1)
        LoadSettingLayout.addWidget(self.AnalysisRoundBox, 1, 2)
        
        self.AddAnalysisRoundButton = QtWidgets.QPushButton('Add Round:')
        self.AddAnalysisRoundButton.clicked.connect(self.SetAnalysisRound)
        LoadSettingLayout.addWidget(self.AddAnalysisRoundButton, 1, 1)
        
        self.datasavedirectorytextbox = QLineEdit(self)
        self.datasavedirectorytextbox.setPlaceholderText('Data directory')
        LoadSettingLayout.addWidget(self.datasavedirectorytextbox, 0, 0, 1, 4)
        
        self.toolButtonOpenDialog = QtWidgets.QPushButton('Set path')
        self.toolButtonOpenDialog.clicked.connect(self.SetAnalysisPath)
        LoadSettingLayout.addWidget(self.toolButtonOpenDialog, 0, 4)
        
        ExecuteAnalysisButton = QPushButton('Load images', self)
#        ExecuteAnalysisButton.setObjectName('Startbutton')
        ExecuteAnalysisButton.clicked.connect(lambda: self.ScreeningAnalysis())
        LoadSettingLayout.addWidget(ExecuteAnalysisButton, 1, 3)
        
        self.ClearAnalysisInforButton = QtWidgets.QPushButton('Clear infor')
        self.ClearAnalysisInforButton.clicked.connect(self.ClearAnalysisInfor)
        LoadSettingLayout.addWidget(self.ClearAnalysisInforButton, 1, 4)
        
        self.X_axisBox = QComboBox()
        self.X_axisBox.addItems(['Lib_Tag_contour_ratio'])
        LoadSettingLayout.addWidget(self.X_axisBox, 2, 1)
        LoadSettingLayout.addWidget(QLabel('X axis: '), 2, 0)
        
        self.WeightBoxSelectionFactor_1 = QDoubleSpinBox(self)
        self.WeightBoxSelectionFactor_1.setDecimals(2)
        self.WeightBoxSelectionFactor_1.setMinimum(0)
        self.WeightBoxSelectionFactor_1.setMaximum(1)
        self.WeightBoxSelectionFactor_1.setValue(1)
        self.WeightBoxSelectionFactor_1.setSingleStep(0.1)  
        LoadSettingLayout.addWidget(self.WeightBoxSelectionFactor_1, 2, 3)
        LoadSettingLayout.addWidget(QLabel("Weight:"), 2, 2)
        
        self.Y_axisBox = QComboBox()
        self.Y_axisBox.addItems(['Contour_soma_ratio_Lib'])
        LoadSettingLayout.addWidget(self.Y_axisBox, 3, 1)
        LoadSettingLayout.addWidget(QLabel('Y axis: '), 3, 0)
        
        self.WeightBoxSelectionFactor_2 = QDoubleSpinBox(self)
        self.WeightBoxSelectionFactor_2.setDecimals(2)
        self.WeightBoxSelectionFactor_2.setMinimum(0)
        self.WeightBoxSelectionFactor_2.setMaximum(1)
        self.WeightBoxSelectionFactor_2.setValue(0.5)
        self.WeightBoxSelectionFactor_2.setSingleStep(0.1)  
        LoadSettingLayout.addWidget(self.WeightBoxSelectionFactor_2, 3, 3)
        LoadSettingLayout.addWidget(QLabel("Weight:"), 3, 2)

        LoadSettingContainer.setLayout(LoadSettingLayout)
        

        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for Selection threshold settings---------------------------------------
        #**************************************************************************************************************************************

        
        self.PostProcessTab.addTab(LoadSettingContainer,"Loading settings")    
        self.PostProcessTab.addTab(ImageProcessingContainer,"Image analysis thresholds")
        
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
    #%%
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
        Mean_intensity_in_contour_thres = self.Mean_intensity_in_contour_thres_box.value()
        Contour_soma_ratio_thres = self.Contour_soma_ratio_thres_box.value()
        # For the brightness screening
        self.ProcessML = ProcessImageML()
        
        self.normalOutputWritten('Start loading images...\n')
        tag_folder = self.Tag_folder
        lib_folder = self.Lib_folder
    
        tag_round = 'Round{}'.format(self.Tag_round_infor[0])
        lib_round = 'Round{}'.format(self.Lib_round_infor[0])
        
        cell_Data_1 = self.ProcessML.FluorescenceAnalysis(tag_folder, tag_round)
        cell_Data_2 = self.ProcessML.FluorescenceAnalysis(lib_folder, lib_round)
        Cell_DataFrame_Merged = self.ProcessML.MergeDataFrames(cell_Data_1, cell_Data_2, method = 'TagLib')
        DataFrames_filtered = self.ProcessML.FilterDataFrames(Cell_DataFrame_Merged, Mean_intensity_in_contour_thres, Contour_soma_ratio_thres)
        self.DataFrame_sorted = self.ProcessML.Sorting_onTwoaxes(DataFrames_filtered, axis_1 = self.X_axisBox.currentText(), axis_2 = self.Y_axisBox.currentText(), 
                                                                 weight_1 = self.WeightBoxSelectionFactor_1.value(), weight_2 = self.WeightBoxSelectionFactor_2.value())
        
        self.SaveCellsDataframetoExcel()
        self.UpdateSelectionScatter()
    #%%
    def UpdateSelectionScatter(self):

        self.EvaluatingPara_list = [self.X_axisBox.currentText(), self.Y_axisBox.currentText()]
        
        self.Matdisplay_Figure.clear()

        if len(self.EvaluatingPara_list) == 2:
            
            ax1 = self.Matdisplay_Figure.add_subplot(111)
            ax1.scatter(self.DataFrame_sorted.loc[:,self.EvaluatingPara_list[0]], self.DataFrame_sorted.loc[:,self.EvaluatingPara_list[1]], s=np.pi*3, c='blue', alpha=0.5)
            ax1.set_xlabel(self.EvaluatingPara_list[0])
            ax1.set_ylabel(self.EvaluatingPara_list[1])
            self.Matdisplay_Figure.tight_layout()
            self.Matdisplay_Canvas.draw()
            
            # Some numbers ready for tracing back
            self.TotaNumofCellSelected = len(self.DataFrame_sorted)
            self.TotalCellNum = len(self.DataFrame_sorted)
            self.normalOutputWritten('---- Total cells selected: {}; Total cells: {}----\n'.format(self.TotaNumofCellSelected, self.TotalCellNum))
            
            saving_directory = os.path.join(self.Tag_folder, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_Screening scatters.html')
            self.ProcessML.showPlotlyScatter(self.DataFrame_sorted, x_axis=self.EvaluatingPara_list[0], y_axis=self.EvaluatingPara_list[1], saving_directory = saving_directory)
                
    def GoThroughTopCells(self, direction):
        """
        ! Cell dataframe index starts from Cell 1, which corresponds to popnexttopimgcounter = 0.
        """
        if direction == 'next':
            if self.popnexttopimgcounter > (self.TotaNumofCellSelected-1):#Make sure it doesn't go beyond the last coords.
                self.popnexttopimgcounter -= 1
            
            self.CurrentRankCellpProperties = self.DataFrame_sorted.iloc[self.popnexttopimgcounter]
            
            #--------------------Show image with cell in box----------------------
            spec = self.CurrentRankCellpProperties.loc['ImgNameInfor_Tag']
            print(spec)
    #        #-------------- readin image---------------
            tag_imagefilename = os.path.join(self.Tag_folder, spec+'_PMT_0Zmax.tif')
            print(tag_imagefilename)
            loaded_tag_image_display = imread(tag_imagefilename, as_gray=True)
            # Retrieve boundingbox information
            Each_bounding_box = self.CurrentRankCellpProperties.loc['BoundingBox_Tag']
            minr = int(Each_bounding_box[Each_bounding_box.index('minr')+4:Each_bounding_box.index('_maxr')])
            maxr = int(Each_bounding_box[Each_bounding_box.index('maxr')+4:Each_bounding_box.index('_minc')]) -1    
            minc = int(Each_bounding_box[Each_bounding_box.index('minc')+4:Each_bounding_box.index('_maxc')])
            maxc = int(Each_bounding_box[Each_bounding_box.index('maxc')+4:len(Each_bounding_box)]) -1
            
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
            self.normalOutputWritten('ID: {}\n{}: {}\n{}: {}\n{}: {}\n'.format(spec, self.EvaluatingPara_list[0], round(self.CurrentRankCellpProperties.loc[self.EvaluatingPara_list[0]], 4), \
                                                                     self.EvaluatingPara_list[1], round(self.CurrentRankCellpProperties.loc[self.EvaluatingPara_list[1]], 4), 
                                                                     'IDNumber', self.CurrentRankCellpProperties.name))
            #------------------Stage move----------------------------------------
#            self.CurrentPos = spec[spec.index('_R')+2:len(spec)].split('C')
#            self.ludlStage.moveAbs(int(self.CurrentPos[0]),int(self.CurrentPos[1]))
            
            self.popnexttopimgcounter += 1 # Alwasy plus 1 to get it ready for next move.
            
        elif direction == 'previous':
            self.popnexttopimgcounter -= 2 
            if self.popnexttopimgcounter >= 0:
                
                self.CurrentRankCellpProperties = self.DataFrame_sorted.iloc[self.popnexttopimgcounter]
                
                #--------------------Show image with cell in box----------------------
                spec = self.CurrentRankCellpProperties.loc['ImgNameInfor_Tag']
                print(spec)
        #        #-------------- readin image---------------
                tag_imagefilename = os.path.join(self.Tag_folder, spec+'_PMT_0Zmax.tif')
                print(tag_imagefilename)
                loaded_tag_image_display = imread(tag_imagefilename, as_gray=True)
                # Retrieve boundingbox information
                Each_bounding_box = self.CurrentRankCellpProperties.loc['BoundingBox_Tag']
                minr = int(Each_bounding_box[Each_bounding_box.index('minr')+4:Each_bounding_box.index('_maxr')])
                maxr = int(Each_bounding_box[Each_bounding_box.index('maxr')+4:Each_bounding_box.index('_minc')]) -1    
                minc = int(Each_bounding_box[Each_bounding_box.index('minc')+4:Each_bounding_box.index('_maxc')])
                maxc = int(Each_bounding_box[Each_bounding_box.index('maxc')+4:len(Each_bounding_box)]) -1
                
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
                self.normalOutputWritten('ID: {}\n{}: {}\n{}: {}\n{}: {}\n'.format(spec, self.EvaluatingPara_list[0], round(self.CurrentRankCellpProperties.loc[self.EvaluatingPara_list[0]], 4), \
                                                                         self.EvaluatingPara_list[1], round(self.CurrentRankCellpProperties.loc[self.EvaluatingPara_list[1]], 4), 
                                                                         'IDNumber', self.CurrentRankCellpProperties.name))
                
                #------------------Stage move----------------------------------------
#                self.CurrentPos = spec[spec.index('_R')+2:len(spec)].split('C')
#                self.ludlStage.moveAbs(int(self.CurrentPos[0]),int(self.CurrentPos[1]))
                
                if self.popnexttopimgcounter < (self.TotaNumofCellSelected-1):
                    self.popnexttopimgcounter += 1
            else:
                self.popnexttopimgcounter = 0
                
        elif direction == 'null':
            self.popnexttopimgcounter -= 1
            
            self.CurrentRankCellpProperties = self.DataFrame_sorted.iloc[self.popnexttopimgcounter]
            
            #--------------------Show image with cell in box----------------------
            spec = self.CurrentRankCellpProperties.loc['ImgNameInfor_Tag']
            print(spec)
    #        #-------------- readin image---------------
            tag_imagefilename = os.path.join(self.Tag_folder, spec+'_PMT_0Zmax.tif')
            print(tag_imagefilename)
            loaded_tag_image_display = imread(tag_imagefilename, as_gray=True)
            # Retrieve boundingbox information
            Each_bounding_box = self.CurrentRankCellpProperties.loc['BoundingBox_Tag']
            minr = int(Each_bounding_box[Each_bounding_box.index('minr')+4:Each_bounding_box.index('_maxr')])
            maxr = int(Each_bounding_box[Each_bounding_box.index('maxr')+4:Each_bounding_box.index('_minc')]) -1    
            minc = int(Each_bounding_box[Each_bounding_box.index('minc')+4:Each_bounding_box.index('_maxc')])
            maxc = int(Each_bounding_box[Each_bounding_box.index('maxc')+4:len(Each_bounding_box)]) -1
            
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
        self.SpecificIndexInArray = 'Cell ' + str(self.CellSequenceBox.value())
        self.CurrentRankCellpProperties = self.DataFrame_sorted.loc[self.SpecificIndexInArray,:]
        
        #--------------------Show image with cell in box----------------------
        spec = self.CurrentRankCellpProperties.loc['ImgNameInfor_Tag']
        print(spec)
#        #-------------- readin image---------------
        tag_imagefilename = os.path.join(self.Tag_folder, spec+'_PMT_0Zmax.tif')
        print(tag_imagefilename)
        loaded_tag_image_display = imread(tag_imagefilename, as_gray=True)
        # Retrieve boundingbox information
        Each_bounding_box = self.CurrentRankCellpProperties.loc['BoundingBox_Tag']
        minr = int(Each_bounding_box[Each_bounding_box.index('minr')+4:Each_bounding_box.index('_maxr')])
        maxr = int(Each_bounding_box[Each_bounding_box.index('maxr')+4:Each_bounding_box.index('_minc')]) -1    
        minc = int(Each_bounding_box[Each_bounding_box.index('minc')+4:Each_bounding_box.index('_maxc')])
        maxc = int(Each_bounding_box[Each_bounding_box.index('maxc')+4:len(Each_bounding_box)]) -1
        
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
        ax1.text(maxc, minr, 'NO_{}'.format(self.CurrentRankCellpProperties.name),fontsize=10, color='orange', style='italic')
        self.Matdisplay_Figure.tight_layout()
        self.Matdisplay_Canvas.draw()
        
        #-------------------Print details of cell of interest----------------
        self.normalOutputWritten('------------------IDNumber {}----------------\n'.format(self.CurrentRankCellpProperties.name))
        self.normalOutputWritten('ID: {}\n{}: {}\n{}: {}\n'.format(spec, self.EvaluatingPara_list[0], round(self.CurrentRankCellpProperties.loc[self.EvaluatingPara_list[0]], 4), \
                                                                 self.EvaluatingPara_list[1], round(self.CurrentRankCellpProperties.loc[self.EvaluatingPara_list[1]], 4)))
            
    def ShowScatterPos(self):
        if self.ButtonShowInScatter.isChecked():
            self.Matdisplay_Figure.clear()
            ax1 = self.Matdisplay_Figure.add_subplot(111)
            ax1.scatter(self.DataFrame_sorted.loc[:,self.EvaluatingPara_list[0]], self.DataFrame_sorted.loc[:,self.EvaluatingPara_list[1]], s=np.pi*3, c='blue', alpha=0.5)
            ax1.scatter(self.DataFrame_sorted.iloc[self.popnexttopimgcounter-1, :].loc[self.EvaluatingPara_list[0]], self.DataFrame_sorted.iloc[self.popnexttopimgcounter-1, :].loc[self.EvaluatingPara_list[1]], 
                        s=np.pi*6, c='red', alpha=0.5)
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
            
            ax1.scatter(self.DataFrame_sorted.loc[:,self.EvaluatingPara_list[0]], self.DataFrame_sorted.loc[:,self.EvaluatingPara_list[1]], s=np.pi*3, c='blue', alpha=0.5)
            ax1.scatter(self.DataFrame_sorted.loc[self.SpecificIndexInArray, :].loc[self.EvaluatingPara_list[0]], self.DataFrame_sorted.loc[self.SpecificIndexInArray, :].loc[self.EvaluatingPara_list[1]], 
                        s=np.pi*6, c='red', alpha=0.5)

            ax1.set_xlabel(self.EvaluatingPara_list[0])
            ax1.set_ylabel(self.EvaluatingPara_list[1])
            self.Matdisplay_Figure.tight_layout()
            self.Matdisplay_Canvas.draw()            
        else:
            self.GoThroughTopCells('sequence')
    
    def SaveCellsDataframetoExcel(self):
        os.path.join(self.Tag_folder, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_CellsProperties.xlsx')
        self.DataFrame_sorted.to_excel(os.path.join(self.Tag_folder, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_CellsProperties.xlsx'))
#        np.save(os.path.join(self.Tag_folder, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_CellsProperties'), self.Overview_LookupBook)
        
    def ResetRankCoord(self):
        self.popnexttopimgcounter = 0
    #%%
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        pg.setConfigOptions(imageAxisOrder='row-major')
        mainwin = MainGUI()
        mainwin.show()
        app.exec_()
    run_app() 