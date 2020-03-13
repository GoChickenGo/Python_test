# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 14:03:52 2020

@author: xinmeng
"""

from __future__ import division
import sys
sys.path.append('../')
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPoint, QRect, QObject
from PyQt5.QtGui import QColor, QPen, QPixmap, QIcon, QTextCursor, QFont

from PyQt5.QtWidgets import (QWidget, QButtonGroup, QLabel, QSlider, QSpinBox, QDoubleSpinBox, QGridLayout, QPushButton, QGroupBox, 
                             QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox, QTabWidget, QCheckBox, QRadioButton, 
                             QFileDialog, QProgressBar, QTextEdit, QScrollBar)
from PyQt5.QtCore import QThread
import pyqtgraph as pg
import numpy as np
import sys

from PI_ObjectiveMotor.focuser import PIMotor

class ObjMotorWidgetUI(QWidget):
    
#    waveforms_generated = pyqtSignal(object, object, list, int)
#    SignalForContourScanning = pyqtSignal(int, int, int, np.ndarray, np.ndarray)
#    MessageBack = pyqtSignal(str)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
#        os.chdir('./')# Set directory to current folder.
        self.setFont(QFont("Arial"))
        
#        self.setMinimumSize(1350,900)
        self.setWindowTitle("ObjMotorWidget")
        self.layout = QGridLayout(self)
        
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
        
        self.FocusSlider = QScrollBar(Qt.Horizontal)
        self.FocusSlider.setMinimum(0)
        self.FocusSlider.setMaximum(5000000)
#        self.FocusSlider.setTickPosition(QSlider.TicksBothSides)
#        self.FocusSlider.setTickInterval(1000000)
        self.FocusSlider.setStyleSheet('color:white; background: lightblue')
        self.FocusSlider.setSingleStep(10000)
#        self.line640 = QLineEdit(self)
#        self.line640.setFixedWidth(60)
#        self.FocusSlider.sliderReleased.connect(lambda:self.updatelinevalue(640))
        self.FocusSlider.sliderReleased.connect(lambda:self.move_through_slider())
#        self.line640.returnPressed.connect(lambda:self.updatesider(640))
        self.ObjMotorcontrolLayout.addWidget(self.FocusSlider, 4, 0, 1, 3)
        
        ObjMotorcontrolContainer.setLayout(self.ObjMotorcontrolLayout)
        ObjMotorcontrolContainer.setMaximumHeight(300)
        self.layout.addWidget(ObjMotorcontrolContainer, 4, 0)          
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------Fucs for Motor movement----------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************         
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
        
        decimal_places = len(str(self.ObjCurrentPos['1']).split('.')[1])
        self.FocusSlider.setValue(int(self.ObjCurrentPos['1']*(10**decimal_places)))
        
    def MoveMotor(self):
        
        pos = PIMotor.move(self.pi_device_instance.pidevice, self.ObjMotor_target.value())
        self.ObjCurrentPos = self.pi_device_instance.pidevice.qPOS(self.pi_device_instance.pidevice.axes)
        self.ObjMotor_current_pos_Label.setText("Current position: {:.4f}".format(self.ObjCurrentPos['1'])) # Axis here is a string.
        self.ObjMotor_target.setValue(self.ObjCurrentPos['1'])  
        
        decimal_places = len(str(self.ObjCurrentPos['1']).split('.')[1])
        self.FocusSlider.setValue(int(self.ObjCurrentPos['1']*(10**decimal_places)))
      
    def DisconnectMotor(self):
        self.ObjMotor_connect.setEnabled(True)
        self.ObjMotor_disconnect.setEnabled(False)
        
        PIMotor.CloseMotorConnection(self.pi_device_instance.pidevice)
#        self.normalOutputWritten('Objective motor disconnected.'+'\n')
        
    def Motor_move_upwards(self):
        self.MotorStep = self.ObjMotor_step.value()
        pos = PIMotor.move(self.pi_device_instance.pidevice, (self.ObjCurrentPos['1'] + self.MotorStep))
        self.ObjCurrentPos = self.pi_device_instance.pidevice.qPOS(self.pi_device_instance.pidevice.axes)
        self.ObjMotor_current_pos_Label.setText("Current position: {:.4f}".format(self.ObjCurrentPos['1'])) # Axis here is a string.
        
        decimal_places = len(str(self.ObjCurrentPos['1']).split('.')[1])
        self.FocusSlider.setValue(int(self.ObjCurrentPos['1']*(10**decimal_places)))
        
    def Motor_move_downwards(self):
        self.MotorStep = self.ObjMotor_step.value()
        pos = PIMotor.move(self.pi_device_instance.pidevice, (self.ObjCurrentPos['1'] - self.MotorStep))
        self.ObjCurrentPos = self.pi_device_instance.pidevice.qPOS(self.pi_device_instance.pidevice.axes)
        self.ObjMotor_current_pos_Label.setText("Current position: {:.4f}".format(self.ObjCurrentPos['1'])) # Axis here is a string.
        
        decimal_places = len(str(self.ObjCurrentPos['1']).split('.')[1])
        self.FocusSlider.setValue(int(self.ObjCurrentPos['1']*(10**decimal_places)))
        
    def move_through_slider(self):
        pos = PIMotor.move(self.pi_device_instance.pidevice, self.FocusSlider.value()/1000000)
        self.ObjCurrentPos = self.pi_device_instance.pidevice.qPOS(self.pi_device_instance.pidevice.axes)
        self.ObjMotor_current_pos_Label.setText("Current position: {:.4f}".format(self.ObjCurrentPos['1'])) # Axis here is a string.
        
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
        pg.setConfigOptions(imageAxisOrder='row-major')
        mainwin = ObjMotorWidgetUI()
        mainwin.show()
        app.exec_()
    run_app()