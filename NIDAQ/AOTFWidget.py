# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 12:18:12 2020

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
                             QFileDialog, QProgressBar, QTextEdit)

import pyqtgraph as pg
import time
import sys

from NIDAQ.generalDaqerThread import (execute_analog_readin_optional_digital_thread, execute_tread_singlesample_analog,
                                execute_tread_singlesample_digital, execute_analog_and_readin_digital_optional_camtrig_thread, DaqProgressBar)

class AOTFWidgetUI(QWidget):
    
#    waveforms_generated = pyqtSignal(object, object, list, int)
#    SignalForContourScanning = pyqtSignal(int, int, int, np.ndarray, np.ndarray)
#    MessageBack = pyqtSignal(str)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
#        os.chdir('./')# Set directory to current folder.
        self.setFont(QFont("Arial"))
        
#        self.setMinimumSize(1350,900)
        self.setWindowTitle("StageWidget")
        self.layout = QGridLayout(self)
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------GUI for AOTF---------------------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************
        AOTFcontrolContainer = QGroupBox("AOTF control")
        self.AOTFcontrolLayout = QGridLayout()
        
        self.slider640 = QSlider(Qt.Horizontal)
        self.slider640.setMinimum(0)
        self.slider640.setMaximum(500)
        self.slider640.setTickPosition(QSlider.TicksBothSides)
        self.slider640.setTickInterval(100)
        self.slider640.setSingleStep(1)
        self.line640 = QLineEdit(self)
        self.line640.setFixedWidth(60)
        self.slider640.sliderReleased.connect(lambda:self.updatelinevalue(640))
        self.slider640.sliderReleased.connect(lambda:self.execute_tread_single_sample_analog('640AO'))
        self.line640.returnPressed.connect(lambda:self.updatesider(640))
        
        self.ICON_off_AOTF = "./Icons/AOTF_off.png"
        self.AOTF_red_iconlabel = QLabel(self)
        self.AOTF_red_iconlabel.setPixmap(QPixmap(self.ICON_off_AOTF))
        self.AOTFcontrolLayout.addWidget(self.AOTF_red_iconlabel, 0, 0)
        
        self.switchbutton_640 = QPushButton("640")
        self.switchbutton_640.setStyleSheet("QPushButton {color:white;background-color: red; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:black;background-color: red; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.switchbutton_640.setCheckable(True)
        #self.holdingbutton.toggle()
        
        self.switchbutton_640.clicked.connect(lambda: self.execute_tread_single_sample_digital('640blanking'))
        self.switchbutton_640.clicked.connect(lambda: self.change_AOTF_icon('640blanking'))
        self.AOTFcontrolLayout.addWidget(self.switchbutton_640, 0, 1)
                
        self.slider532 = QSlider(Qt.Horizontal)
        self.slider532.setMinimum(0)
        self.slider532.setMaximum(500)
        self.slider532.setTickPosition(QSlider.TicksBothSides)
        self.slider532.setTickInterval(100)
        self.slider532.setSingleStep(1)
        self.line532 = QLineEdit(self)
        self.line532.setFixedWidth(60)
        self.slider532.sliderReleased.connect(lambda:self.updatelinevalue(532))
        self.slider532.sliderReleased.connect(lambda:self.execute_tread_single_sample_analog('532AO'))
        self.line532.returnPressed.connect(lambda:self.updatesider(532))
        
        self.AOTF_green_iconlabel = QLabel(self)
        self.AOTF_green_iconlabel.setPixmap(QPixmap(self.ICON_off_AOTF))
        self.AOTFcontrolLayout.addWidget(self.AOTF_green_iconlabel, 1, 0)
        
        self.switchbutton_532 = QPushButton("532")
        self.switchbutton_532.setStyleSheet("QPushButton {color:white;background-color: green; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:black;background-color: green; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.switchbutton_532.setCheckable(True)
        #self.holdingbutton.toggle()
        
        self.switchbutton_532.clicked.connect(lambda: self.execute_tread_single_sample_digital('532blanking'))
        self.switchbutton_532.clicked.connect(lambda: self.change_AOTF_icon('532blanking'))
        self.AOTFcontrolLayout.addWidget(self.switchbutton_532, 1, 1)
        
        self.slider488 = QSlider(Qt.Horizontal)
        self.slider488.setMinimum(0)
        self.slider488.setMaximum(500)
        self.slider488.setTickPosition(QSlider.TicksBothSides)
        self.slider488.setTickInterval(100)
        self.slider488.setSingleStep(1)
        self.line488 = QLineEdit(self)
        self.line488.setFixedWidth(60)
        self.slider488.sliderReleased.connect(lambda:self.updatelinevalue(488))
        self.slider488.sliderReleased.connect(lambda:self.execute_tread_single_sample_analog('488AO'))
        self.line488.returnPressed.connect(lambda:self.updatesider(488))
        
        self.AOTF_blue_iconlabel = QLabel(self)
        self.AOTF_blue_iconlabel.setPixmap(QPixmap(self.ICON_off_AOTF))
        self.AOTFcontrolLayout.addWidget(self.AOTF_blue_iconlabel, 2, 0)
        
        self.switchbutton_488 = QPushButton("488")
        self.switchbutton_488.setStyleSheet("QPushButton {color:white;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            "QPushButton:pressed {color:black;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.switchbutton_488.setCheckable(True)
        #self.holdingbutton.toggle()
        
        self.switchbutton_488.clicked.connect(lambda: self.execute_tread_single_sample_digital('488blanking'))
        self.switchbutton_488.clicked.connect(lambda: self.change_AOTF_icon('488blanking'))
        self.AOTFcontrolLayout.addWidget(self.switchbutton_488, 2, 1)        
        
        self.AOTFcontrolLayout.addWidget(self.slider640, 0, 2)
        self.AOTFcontrolLayout.addWidget(self.line640, 0, 3)
        self.AOTFcontrolLayout.addWidget(self.slider532, 1, 2)
        self.AOTFcontrolLayout.addWidget(self.line532, 1, 3)
        self.AOTFcontrolLayout.addWidget(self.slider488, 2, 2)
        self.AOTFcontrolLayout.addWidget(self.line488, 2, 3)
        
        AOTFcontrolContainer.setLayout(self.AOTFcontrolLayout)
        AOTFcontrolContainer.setMaximumHeight(300)
        self.layout.addWidget(AOTFcontrolContainer, 1, 0)
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------Fuc for AOTF---------------------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************
    def updatelinevalue(self, wavelength):
        if wavelength == 640:
            self.line640.setText(str(self.slider640.value()/100))
        if wavelength == 532:
            self.line532.setText(str(self.slider532.value()/100))
        if wavelength == 488:
            self.line488.setText(str(self.slider488.value()/100))
        
    def updateslider(self, wavelength):
        #self.slider640.setSliderPosition(int(float((self.line640.text())*100)))
        if wavelength == 640:
            self.slider640.setValue(int(float(self.line640.text())*100))
        if wavelength == 532:
            self.slider532.setValue(int(float(self.line532.text())*100))
        if wavelength == 488:
            self.slider488.setValue(int(float(self.line488.text())*100))
            
    def execute_tread_single_sample_analog(self, channel):
        if channel == '640AO':
            execute_tread_singlesample_AOTF_analog = execute_tread_singlesample_analog()
            execute_tread_singlesample_AOTF_analog.set_waves(channel, self.slider640.value())
            execute_tread_singlesample_AOTF_analog.start()
        elif channel == '532AO':
            execute_tread_singlesample_AOTF_analog = execute_tread_singlesample_analog()
            execute_tread_singlesample_AOTF_analog.set_waves(channel, self.slider532.value())
            execute_tread_singlesample_AOTF_analog.start()
        elif channel == '488AO':
            execute_tread_singlesample_AOTF_analog = execute_tread_singlesample_analog()
            execute_tread_singlesample_AOTF_analog.set_waves(channel, self.slider488.value())
            execute_tread_singlesample_AOTF_analog.start()            
            
    def execute_tread_single_sample_digital(self, channel):
        if channel == '640blanking':
            if self.switchbutton_640.isChecked():
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 1)
                execute_tread_singlesample_AOTF_digital.start()
            else:
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 0)
                execute_tread_singlesample_AOTF_digital.start()
        elif channel == '532blanking':
            if self.switchbutton_532.isChecked():
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 1)
                execute_tread_singlesample_AOTF_digital.start()
            else:
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 0)
                execute_tread_singlesample_AOTF_digital.start()        
        elif channel == '488blanking':
            if self.switchbutton_488.isChecked():
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 1)
                execute_tread_singlesample_AOTF_digital.start()
            else:
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 0)
                execute_tread_singlesample_AOTF_digital.start()  
                
        elif channel == 'LED':
            if self.switchbutton_LED.isChecked():
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 1)
                execute_tread_singlesample_AOTF_digital.start()
            else:
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 0)
                execute_tread_singlesample_AOTF_digital.start() 
                
    def change_AOTF_icon(self, channel):
        if channel == '640blanking':
            if self.switchbutton_640.isChecked():
                self.AOTF_red_iconlabel.setPixmap(QPixmap('./Icons/AOTF_red_on.png'))
            else:
                self.AOTF_red_iconlabel.setPixmap(QPixmap(self.ICON_off_AOTF))
        elif channel == '532blanking':
            if self.switchbutton_532.isChecked():
                self.AOTF_green_iconlabel.setPixmap(QPixmap('./Icons/AOTF_green_on.png'))
            else:
                self.AOTF_green_iconlabel.setPixmap(QPixmap(self.ICON_off_AOTF))        
        elif channel == '488blanking':
            if self.switchbutton_488.isChecked():
                self.AOTF_blue_iconlabel.setPixmap(QPixmap('./Icons/AOTF_blue_on.png'))
            else:
                self.AOTF_blue_iconlabel.setPixmap(QPixmap(self.ICON_off_AOTF)) 
        elif channel == 'LED':
            if self.switchbutton_LED.isChecked():
                self.switchbutton_LED.setIcon(QIcon('./Icons/LED_on.png'))
            else:
                self.switchbutton_LED.setIcon(QIcon('./Icons/AOTF_off.png'))
        
        
if __name__ == "__main__":
    
#    import sys
    sys.path.append('../')
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        pg.setConfigOptions(imageAxisOrder='row-major')
        mainwin = AOTFWidgetUI()
        mainwin.show()
        app.exec_()
    run_app()