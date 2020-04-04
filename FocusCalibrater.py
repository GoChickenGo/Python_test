# -*- coding: utf-8 -*-
"""
Created on Thu Jan  2 17:37:09 2020

@author: xinmeng

# Row/Column indexs of coordinates np.array are opposite of stage row-col indexs.
"""

from __future__ import division
import sys
import numpy as np
from matplotlib import pyplot as plt
from IPython import get_ipython
from matplotlib.ticker import FormatStrFormatter
from NIDAQ.configuration import Configuration
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import (QWidget,QLineEdit, QLabel, QGridLayout, QPushButton, QVBoxLayout, QProgressBar, QHBoxLayout, QComboBox, QMessageBox, 
                             QPlainTextEdit, QGroupBox, QTabWidget, QCheckBox, QDoubleSpinBox, QSpinBox)
import pyqtgraph as pg
from pyqtgraph import PlotDataItem, TextItem
import os
import math
import time
from datetime import datetime
from PI_ObjectiveMotor.focuser import PIMotor
from SampleStageControl.Stagemovement_Thread import StagemovementAbsoluteThread
from scipy import interpolate

class FocusMatrixFeeder(QWidget):
    FocusCorrectionFomula = pyqtSignal(object)
    FocusCorrectionForDuplicateMethod = pyqtSignal(object)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QGridLayout(self)
#        self.setMaximumSize(400,400)
        self.CurrentCoordsSequence = 0 # start from 0, pos1, pos2, pos3...
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for StageScanContainer-------------------------------------------------
        #**************************************************************************************************************************************        
        ScanContainer = QGroupBox("Scanning settings")        
        ScanSettingLayout = QGridLayout() #Layout manager
        
        self.FeederScanStartRowIndexTextbox = QSpinBox(self)
        self.FeederScanStartRowIndexTextbox.setMinimum(-20000)
        self.FeederScanStartRowIndexTextbox.setMaximum(10000000)
        self.FeederScanStartRowIndexTextbox.setSingleStep(500)
        ScanSettingLayout.addWidget(self.FeederScanStartRowIndexTextbox, 0, 1)
        ScanSettingLayout.addWidget(QLabel("Start index-row:"), 0, 0)
      
        self.FeederScanEndRowIndexTextbox = QSpinBox(self)
        self.FeederScanEndRowIndexTextbox.setMinimum(-20000)
        self.FeederScanEndRowIndexTextbox.setMaximum(10000000)
        self.FeederScanEndRowIndexTextbox.setSingleStep(500)
        ScanSettingLayout.addWidget(self.FeederScanEndRowIndexTextbox, 0, 3)
        ScanSettingLayout.addWidget(QLabel("End index-row:"), 0, 2)
        
        self.FeederScanStartColumnIndexTextbox = QSpinBox(self)
        self.FeederScanStartColumnIndexTextbox.setMinimum(-20000)
        self.FeederScanStartColumnIndexTextbox.setMaximum(10000000)
        self.FeederScanStartColumnIndexTextbox.setSingleStep(500)
        ScanSettingLayout.addWidget(self.FeederScanStartColumnIndexTextbox, 1, 1)
        ScanSettingLayout.addWidget(QLabel("Start index-column:"), 1, 0)   
        
        self.FeederScanEndColumnIndexTextbox = QSpinBox(self)
        self.FeederScanEndColumnIndexTextbox.setMinimum(-20000)
        self.FeederScanEndColumnIndexTextbox.setMaximum(10000000)
        self.FeederScanEndColumnIndexTextbox.setSingleStep(500)
        ScanSettingLayout.addWidget(self.FeederScanEndColumnIndexTextbox, 1, 3)
        ScanSettingLayout.addWidget(QLabel("End index-column:"), 1, 2)      

        self.FeederScanstepTextbox = QSpinBox(self)
        self.FeederScanstepTextbox.setMaximum(20000)
        self.FeederScanstepTextbox.setValue(1650)
        self.FeederScanstepTextbox.setSingleStep(1650)
        ScanSettingLayout.addWidget(self.FeederScanstepTextbox, 0, 5)
        ScanSettingLayout.addWidget(QLabel("Step size:"), 0, 4)
        
        self.SetStageScanCoordsButton = QPushButton('Set', self)
        self.SetStageScanCoordsButton.setCheckable(True)
        ScanSettingLayout.addWidget(self.SetStageScanCoordsButton, 1, 5)
        self.SetStageScanCoordsButton.clicked.connect(self.GenerateScanCoords)        
        self.SetStageScanCoordsButton.clicked.connect(self.disableCoords)
        
        ScanContainer.setLayout(ScanSettingLayout)
        
        self.layout.addWidget(ScanContainer, 1, 0, 1, 7)
        
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for StageMoveContainer-------------------------------------------------
        #**************************************************************************************************************************************        
        StageMoveContainer = QGroupBox("Stage Movement")        
        StageMoveContainerLayout = QGridLayout() #Layout manager
        
        self.StageMoveRowIndexSpinbox = QSpinBox(self)
        self.StageMoveRowIndexSpinbox.setMinimum(-20000)
        self.StageMoveRowIndexSpinbox.setMaximum(20000)
        self.StageMoveRowIndexSpinbox.setSingleStep(500)
        StageMoveContainerLayout.addWidget(self.StageMoveRowIndexSpinbox, 0, 1)
        StageMoveContainerLayout.addWidget(QLabel("Row index:"), 0, 0)
      
        self.StageMoveColumnIndexSpinbox = QSpinBox(self)
        self.StageMoveColumnIndexSpinbox.setMinimum(-20000)
        self.StageMoveColumnIndexSpinbox.setMaximum(20000)
        self.StageMoveColumnIndexSpinbox.setSingleStep(500)
        StageMoveContainerLayout.addWidget(self.StageMoveColumnIndexSpinbox, 0, 3)
        StageMoveContainerLayout.addWidget(QLabel("Column index:"), 0, 2)
        
        self.StageMoveCoordsButton = QPushButton('Move here', self)
        StageMoveContainerLayout.addWidget(self.StageMoveCoordsButton, 0, 4)
        self.StageMoveCoordsButton.clicked.connect(self.MoveToDefinedCoords)
        
        self.StageMovePreviousCoordsButton = QPushButton('Previous pos.', self)
        StageMoveContainerLayout.addWidget(self.StageMovePreviousCoordsButton, 1, 0, 1, 2)
        self.StageMovePreviousCoordsButton.clicked.connect(lambda: self.MoveToNextPos('previous'))
        
        self.StageMoveNextCoordsButton = QPushButton('Next pos.', self)
        StageMoveContainerLayout.addWidget(self.StageMoveNextCoordsButton, 1, 2, 1, 2)
        self.StageMoveNextCoordsButton.clicked.connect(lambda: self.MoveToNextPos('next'))
        
        StageMoveContainer.setLayout(StageMoveContainerLayout)
#        StageMoveContainer.setMaximumWidth(200)
        self.layout.addWidget(StageMoveContainer, 2, 0, 2, 4)   
        
        #**************************************************************************************************************************************
        #-----------------------------------------------------------GUI for MotorMoveContainer-------------------------------------------------
        #**************************************************************************************************************************************        
        MotorMoveContainer = QGroupBox("Obj. motor")        
        MotorMoveContainerLayout = QGridLayout() #Layout manager
        
        self.ObjMotor_connect = QPushButton("Connect")
        MotorMoveContainerLayout.addWidget(self.ObjMotor_connect, 0, 0)
        self.ObjMotor_connect.clicked.connect(lambda: self.ConnectMotor())       
        
        self.ObjMotor_disconnect = QPushButton("Disconnect")
        MotorMoveContainerLayout.addWidget(self.ObjMotor_disconnect, 0, 1)
        self.ObjMotor_disconnect.clicked.connect(lambda: self.DisconnectMotor()) 
        
        self.ObjMotor_current_pos_Label = QLabel("Pos now: ")
        MotorMoveContainerLayout.addWidget(self.ObjMotor_current_pos_Label, 3, 0, 1, 2)
        
        self.ObjMotor_upwards = QPushButton("↑")
        MotorMoveContainerLayout.addWidget(self.ObjMotor_upwards, 3, 2)
        self.ObjMotor_upwards.clicked.connect(lambda: self.Motor_move_upwards())
#        self.ObjMotor_upwards.setShortcut('w')
        
        self.ObjMotor_down = QPushButton("↓")
        MotorMoveContainerLayout.addWidget(self.ObjMotor_down, 4, 2)
        self.ObjMotor_down.clicked.connect(lambda: self.Motor_move_downwards())
#        self.stage_down.setShortcut('s')
        
        self.ObjMotor_target = QDoubleSpinBox(self)
        self.ObjMotor_target.setMinimum(-10000)
        self.ObjMotor_target.setMaximum(10000)
        self.ObjMotor_target.setDecimals(6)
#        self.ObjMotor_target.setValue(3.45)
        self.ObjMotor_target.setSingleStep(0.001)        
        MotorMoveContainerLayout.addWidget(self.ObjMotor_target, 2, 1, 1, 2)

        self.ObjMotor_goto = QPushButton("Move to")
        MotorMoveContainerLayout.addWidget(self.ObjMotor_goto, 2, 0)
        self.ObjMotor_goto.clicked.connect(self.MoveMotor)
        
        self.ObjMotor_step = QDoubleSpinBox(self)
        self.ObjMotor_step.setMinimum(-10000)
        self.ObjMotor_step.setMaximum(10000)
        self.ObjMotor_step.setDecimals(6)
        self.ObjMotor_step.setValue(0.001)
        self.ObjMotor_step.setSingleStep(0.001)        
        MotorMoveContainerLayout.addWidget(self.ObjMotor_step, 1, 1, 1, 2)
        MotorMoveContainerLayout.addWidget(QLabel("Step: "), 1, 0)        
        
        MotorMoveContainer.setLayout(MotorMoveContainerLayout)
        
        self.layout.addWidget(MotorMoveContainer, 2, 4, 4, 3)
    
        self.SetFocusPos4CurrentCoordsButton = QPushButton('Set Focus', self)
        self.SetFocusPos4CurrentCoordsButton.setStyleSheet("QPushButton {color:white;background-color: LimeGreen; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                   "QPushButton:pressed {color:OrangeRed;background-color: LimeGreen; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")

        self.layout.addWidget(self.SetFocusPos4CurrentCoordsButton, 4, 0, 1, 2)
        self.SetFocusPos4CurrentCoordsButton.clicked.connect(self.SetFocusPos)
        
#        self.SetAndMoveNextCoordsButton = QPushButton('Set and Next pos.', self)
#        self.layout.addWidget(self.SetAndMoveNextCoordsButton, 4, 1)
#        self.SetAndMoveNextCoordsButton.clicked.connect(self.MoveToNextPos)
#        self.SetAndMoveNextCoordsButton.clicked.connect(self.SetFocusPos)        

        self.EmitCoordsButton = QPushButton('Finish', self)
        self.EmitCoordsButton.setStyleSheet("QPushButton {color:white;background-color: BlueViolet; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                          "QPushButton:pressed {color:black;background-color: BlueViolet; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")

        self.layout.addWidget(self.EmitCoordsButton, 4, 3)
        self.EmitCoordsButton.clicked.connect(self.EmitCorrectionMatrix) 
    
    #---------------------------------------------------------------Functions for StageScan------------------------------------------------------
    def disableCoords(self):
        if self.SetStageScanCoordsButton.isChecked():
            self.FeederScanStartRowIndexTextbox.setEnabled(False)
            self.FeederScanEndRowIndexTextbox.setEnabled(False)
            self.FeederScanStartColumnIndexTextbox.setEnabled(False)
            self.FeederScanEndColumnIndexTextbox.setEnabled(False)
            self.FeederScanstepTextbox.setEnabled(False)
        else:
            self.FeederScanStartRowIndexTextbox.setEnabled(True)
            self.FeederScanEndRowIndexTextbox.setEnabled(True)
            self.FeederScanStartColumnIndexTextbox.setEnabled(True)
            self.FeederScanEndColumnIndexTextbox.setEnabled(True)
            self.FeederScanstepTextbox.setEnabled(True)           
        
    def GenerateScanCoords(self):
        if self.SetStageScanCoordsButton.isChecked():

            try:
                self.stage_movement_thread = StagemovementAbsoluteThread()
            except:
                print('Stage not initialized.')
            
            self.FeederCoordContainer = np.array([])
            # settings for scanning index
            position_index=[]
            row_start = int(self.FeederScanStartRowIndexTextbox.value()) #row position index start number
            row_end = int(self.FeederScanEndRowIndexTextbox.value())+1 #row position index end number
            
            column_start = int(self.FeederScanStartColumnIndexTextbox.value())
            column_end = int(self.FeederScanEndColumnIndexTextbox.value())+1  # With additional plus one, the range is fully covered by steps.
            
            step = int(self.FeederScanstepTextbox.value()) #length of each step, 1650 for -5~5V FOV
          
            for i in range(row_start, row_end, step):
                position_index.append(int(i))
                for j in range(column_start, column_end, step):
                    position_index.append(int(j))
                    
                    self.FeederCoordContainer = np.append(self.FeederCoordContainer, (position_index))
    #                print('the coords now: '+ str(self.CoordContainer))
                    del position_index[-1]
                    
                position_index=[]
            
            self.CoordsNum = int(len(self.FeederCoordContainer)/2)
            print(self.FeederCoordContainer)
            
            #---------------numpy.meshgrid method------------------------
            linspace_num_x = math.floor((row_end-row_start)/step)+1
            linspace_num_y = math.floor((column_end-column_start)/step)+1
            
            X = np.linspace(row_start,int(row_start+step*(linspace_num_x-1)),linspace_num_x)
            Y = np.linspace(column_start,int(column_start+step*(linspace_num_y-1)),linspace_num_y)
            RowIndex, ColumnIndex = np.meshgrid(X,Y)
            
            self.ColumnIndexMeshgrid = ColumnIndex.astype(int)
            self.RowIndexMeshgrid = RowIndex.astype(int)
            
            self.FocusCalibrationContainer = 3.278*np.ones((len(Y), len(X)))
            self.FocusCalibrationContainer[0,1] = 3.3
            
            print('Row index matrix: {}'.format(self.RowIndexMeshgrid))
            print('Column index matrix: {}'.format(self.ColumnIndexMeshgrid))
            print(self.FocusCalibrationContainer)
    #---------------------------------------------------------------Functions for StageMove------------------------------------------------------    
    def MoveToDefinedCoords(self):
        self.DefinedTargetRowIndex = int(self.StageMoveRowIndexSpinbox.value())
        self.DefinedTargetColIndex = int(self.StageMoveColumnIndexSpinbox.value())
        
        self.stage_movement_thread.SetTargetPos(self.DefinedTargetRowIndex, self.DefinedTargetColIndex)
#        stage_movement_thread.current_position.connect(self.update_stage_current_pos)
        self.stage_movement_thread.start()
        time.sleep(0.5)
        self.stage_movement_thread.quit()
        self.stage_movement_thread.wait()
        
    def MoveToNextPos(self, direction):
        if direction == 'next':
            if self.CurrentCoordsSequence > (self.CoordsNum-1):
                self.CurrentCoordsSequence -= 1
            print(self.CurrentCoordsSequence)
#            self.CurrentCoordsSequence = self.CurrentCoordsSequence
            self.TargetRowIndex = self.FeederCoordContainer[self.CurrentCoordsSequence*2:self.CurrentCoordsSequence*2+2][0]
            self.TargetColIndex = self.FeederCoordContainer[self.CurrentCoordsSequence*2:self.CurrentCoordsSequence*2+2][1]
            
            self.stage_movement_thread.SetTargetPos(self.TargetRowIndex, self.TargetColIndex)
            self.stage_movement_thread.current_position.connect(self.update_stage_current_pos)
            self.stage_movement_thread.start()
#            time.sleep(0.5)
            self.stage_movement_thread.quit()
            self.stage_movement_thread.wait()        
            
#            if self.CurrentCoordsSequence < (self.CoordsNum-1): # Get ready for next pos.CurrentCoordsSequence stands for next one.
            self.CurrentCoordsSequence += 1     
        elif direction == 'previous':

            self.CurrentCoordsSequence -= 2
            if self.CurrentCoordsSequence >= 0:
                print(self.CurrentCoordsSequence)
                self.TargetRowIndex = self.FeederCoordContainer[self.CurrentCoordsSequence*2:self.CurrentCoordsSequence*2+2][0]
                self.TargetColIndex = self.FeederCoordContainer[self.CurrentCoordsSequence*2:self.CurrentCoordsSequence*2+2][1]
                
                self.stage_movement_thread.SetTargetPos(self.TargetRowIndex, self.TargetColIndex)
                self.stage_movement_thread.current_position.connect(self.update_stage_current_pos)
                self.stage_movement_thread.start()
#                time.sleep(0.5)
                self.stage_movement_thread.quit()
                self.stage_movement_thread.wait()        
                
                if self.CurrentCoordsSequence < (self.CoordsNum-1): # Get ready for next pos.CurrentCoordsSequence stands for next one.
                    self.CurrentCoordsSequence += 1 
            else:
                self.CurrentCoordsSequence = 0
                
        print(self.TargetRowIndex, self.TargetColIndex)
        
    def update_stage_current_pos(self, current_pos):
        self.StageMoveRowIndexSpinbox.setValue(int(current_pos[0]))
        self.StageMoveColumnIndexSpinbox.setValue(int(current_pos[1]))
    
        
    #---------------------------------------------------------------Functions for MotorMoveContainer------------------------------------------------
    def ConnectMotor(self):
        self.ObjMotor_connect.setEnabled(False)
        self.ObjMotor_disconnect.setEnabled(True)
        
        self.device_instance = ConnectObj_Thread()
        self.device_instance.start()
        self.device_instance.finished.connect(self.getmotorhandle)

    def getmotorhandle(self):
        self.pi_device_instance = self.device_instance.getInstance()
        print('Objective motor connected.')
#        self.normalOutputWritten('Objective motor connected.'+'\n')
        
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
        print('Objective motor disconnected.')
#        self.normalOutputWritten('Objective motor disconnected.'+'\n')
        
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

    #-------------------------------------------------------------Set motor pos as part of focus calibration----------------------------------------------------
    def SetFocusPos(self): 
        self.CalibrationContainerRowIndex = np.where(self.RowIndexMeshgrid[0,:] == self.TargetRowIndex)[0][0]
        self.CalibrationContainerColIndex = np.where(self.ColumnIndexMeshgrid[:,0] == self.TargetColIndex)[0][0]        
        # Row index is actually the column index in python.
        self.FocusCalibrationContainer[self.CalibrationContainerColIndex, self.CalibrationContainerRowIndex] = self.ObjCurrentPos['1']
        
        print(self.FocusCalibrationContainer)
        
    def EmitCorrectionMatrix(self):
        try:
            self.CorrectionMatrixFomula = interpolate.interp2d(self.ColumnIndexMeshgrid,self.RowIndexMeshgrid,self.FocusCalibrationContainer,kind='cubic') #https://stackoverflow.com/questions/33259896/python-interpolation-2d-array-for-huge-arrays
            self.FocusCorrectionFomula.emit(self.CorrectionMatrixFomula)
        except:
            print('Interpolate failed.')
    
        self.CorrectionForDuplicateMethod = np.vstack((self.FeederCoordContainer[::2],self.FeederCoordContainer[1::2], self.FocusCalibrationContainer.flatten('F')))#‘F’ means to flatten in column-major (Fortran- style) order.
        self.FocusCorrectionForDuplicateMethod.emit(self.CorrectionForDuplicateMethod)
        print('Duplicate correction emitted.')
#        print(self.CorrectionForDuplicateMethod[2,:])
               
        
class ConnectObj_Thread(QThread):
#    videostack_signal = pyqtSignal(np.ndarray)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
#        self.fileName = fileName
#        self.xRel = xRel
#        self.yRel = yRel
        
    def run(self):
        self.pi_device_instance = PIMotor()
        
    def getInstance(self):
        return self.pi_device_instance

if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        mainwin = FocusMatrixFeeder()
        mainwin.show()
        app.exec_()
    run_app()