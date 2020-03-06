#c -*- coding: utf-8 -*-
"""
Created on Sat Aug 10 20:54:40 2019

@author: xinmeng
    ============================== ==============================================
    
    For general experiments in Dr. Daan's lab ゴゴゴ ゴ ゴ ゴ  ゴ  ゴ
    ============================== ==============================================
    == Widget descriptions ==
    
    - PatchClamp.ui_patchclamp_sealtest: The GUI for patch clamp.
    - NIDAQ.Waveformer_for_screening: The GUI for configuring and executing waveforms in National Instrument Data Acquisition (DAQ) device.
    - GalvoWidget.PMTWidget: For PMT scanning imaging.
    - ImageAnalysis.AnalysisWidget: Data Analysis widget.
    - SampleStageControl.StageMoveWidget: The GUI for sample stage movement control.
    - NIDAQ.AOTFWidget: To control AOTF, which is controlled by NI-daq.
    - ThorlabsFilterSlider.FilterSliderWidget: Controller for Thorlabs filter slider.
    - PI_ObjectiveMotor.ObjMotorWidget: Widget for objective motor control.
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
import sys

#from GalvoWidget.pmt_thread import pmtimagingTest, pmtimagingTest_contour

#import NIDAQ.wavegenerator

from NIDAQ.generalDaqerThread import (execute_analog_readin_optional_digital_thread, execute_tread_singlesample_analog,
                                execute_tread_singlesample_digital, execute_analog_and_readin_digital_optional_camtrig_thread, DaqProgressBar)

import os
import PatchClamp.ui_patchclamp_sealtest
import NIDAQ.Waveformer_for_screening
import GalvoWidget.PMTWidget
import ImageAnalysis.AnalysisWidget
import SampleStageControl.StageMoveWidget
import NIDAQ.AOTFWidget
import ThorlabsFilterSlider.FilterSliderWidget
import PI_ObjectiveMotor.ObjMotorWidget

import time
import pyqtgraph.console
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
        self.OC = 0.1
        #----------------------------------------------------------------------
        #----------------------------------GUI---------------------------------
        #----------------------------------------------------------------------
        self.setMinimumSize(1710,1200)
        self.setWindowTitle("Tupolev v1.0")
        self.layout = QGridLayout(self)
        # Setting tabs
        self.tabs = QTabWidget()
        self.Galvo_WidgetInstance = GalvoWidget.PMTWidget.PMTWidgetUI()
        self.Waveformer_WidgetInstance = NIDAQ.Waveformer_for_screening.WaveformGenerator()
        self.PatchClamp_WidgetInstance = PatchClamp.ui_patchclamp_sealtest.PatchclampSealTestUI()
        #self.tab4 = ui_camera_lab_5.CameraUI()
        self.Analysis_WidgetInstance = ImageAnalysis.AnalysisWidget.AnalysisWidgetUI()
        
        #--------------Add tab widgets-------------------
        self.tabs.addTab(self.Galvo_WidgetInstance,"PMT imaging")
        self.tabs.addTab(self.Waveformer_WidgetInstance,"Waveform")
        self.tabs.addTab(self.PatchClamp_WidgetInstance,"Patch clamp")
        #self.tabs.addTab(self.tab4,"Camera")        
        self.tabs.addTab(self.Analysis_WidgetInstance,"Image analysis")
        
        self.savedirectory = os.path.join(os.path.expanduser("~"), "Desktop") #'M:/tnw/ist/do/projects/Neurophotonics/Brinkslab/Data'
        
        # Establishing communication betweeb widgets.
        self.Galvo_WidgetInstance.SignalForContourScanning.connect(self.PassVariable_GalvoWidget2Waveformer)
        self.Galvo_WidgetInstance.MessageBack.connect(self.normalOutputWritten)
        self.Analysis_WidgetInstance.MessageBack.connect(self.normalOutputWritten)
        
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
        
        #======================================================================================================================================
        StageMoveWidgetInstance = SampleStageControl.StageMoveWidget.StageWidgetUI()
        self.layout.addWidget(StageMoveWidgetInstance, 2, 0)
             
        AOTFWidgetInstance = NIDAQ.AOTFWidget.AOTFWidgetUI()
        self.layout.addWidget(AOTFWidgetInstance, 1, 0)
        
        FilterSliderWidgetInstance = ThorlabsFilterSlider.FilterSliderWidget.FilterSliderWidgetUI()
        self.layout.addWidget(FilterSliderWidgetInstance, 3, 0)    
        
        ObjMotorInstance = PI_ObjectiveMotor.ObjMotorWidget.ObjMotorWidgetUI()
        self.layout.addWidget(ObjMotorInstance, 4, 0)         

        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for camera button------------------------------------------------------
       
        self.open_cam = QPushButton('Open Camera')
        self.open_cam.clicked.connect(self.open_camera)
        self.layout.addWidget(self.open_cam,5,0)
        
        self.console_text_edit = QTextEdit()
        self.console_text_edit.setFontItalic(True)
        self.console_text_edit.setPlaceholderText('Notice board from console.')
        self.console_text_edit.setMaximumHeight(200)
        self.layout.addWidget(self.console_text_edit, 6, 0)
        
        #**************************************************************************************************************************************        
        #self.setLayout(pmtmaster)
        self.layout.addWidget(self.tabs, 0, 1, 8, 4)
        self.setLayout(self.layout)
        '''
        ***************************************************************************************************************************************
        ************************************************************END of GUI*****************************************************************
        '''
        
    def __del__(self):
        # Restore sys.stdout
        sys.stdout = sys.__stdout__
        
        '''
        ***************************************************************************************************************************************
        ************************************************************ Functions to pass variables across widges ********************************
        '''        
    def PassVariable_GalvoWidget2Waveformer(self, contour_point_number, Daq_sample_rate_pmt, time_per_contour, handle_viewbox_coordinate_x, handle_viewbox_coordinate_y):
        
        self.Waveformer_WidgetInstance.galvo_contour_label_1.setText("Points in contour: %.d" % contour_point_number)
        self.Waveformer_WidgetInstance.galvo_contour_label_2.setText("Sampling rate: %.d" % Daq_sample_rate_pmt)
        self.Waveformer_WidgetInstance.Daq_sample_rate_pmt = Daq_sample_rate_pmt
        self.Waveformer_WidgetInstance.handle_viewbox_coordinate_position_array_expanded_x = handle_viewbox_coordinate_x
        self.Waveformer_WidgetInstance.handle_viewbox_coordinate_position_array_expanded_y = handle_viewbox_coordinate_y
        self.Waveformer_WidgetInstance.time_per_contour = time_per_contour
        
                
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
        self.Galvo_WidgetInstance.savedirectory = self.savedirectory
        self.Galvo_WidgetInstance.prefixtextboxtext = self.saving_prefix
        
        self.Waveformer_WidgetInstance.savedirectory = self.savedirectory
        self.Waveformer_WidgetInstance.saving_prefix = self.saving_prefix

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

        
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        pg.setConfigOptions(imageAxisOrder='row-major')
        mainwin = Mainbody()
        mainwin.show()
        app.exec_()
    run_app()