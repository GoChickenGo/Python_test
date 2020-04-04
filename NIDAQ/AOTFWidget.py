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
from PyQt5.QtGui import QColor, QPen, QPixmap, QIcon, QTextCursor, QFont, QPainter, QBrush

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
        
        self.switchbutton_640 = MySwitch('ON', 'red', 'OFF', 'maroon', width = 32)
        self.switchbutton_640.clicked.connect(lambda: self.execute_tread_single_sample_digital('640blanking'))
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
        
        self.switchbutton_532 = MySwitch('ON', 'green', 'OFF', 'dark olive green', width = 32)
        self.switchbutton_532.clicked.connect(lambda: self.execute_tread_single_sample_digital('532blanking'))
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
        
        self.switchbutton_488 = MySwitch('ON', 'blue', 'OFF', 'teal', width = 32)
        self.switchbutton_488.clicked.connect(lambda: self.execute_tread_single_sample_digital('488blanking'))
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
                
class MySwitch(QtWidgets.QPushButton):
    def __init__(self, label_1, color_1, label_2, color_2, width, parent = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setMinimumWidth(66)
        self.setMinimumHeight(22)
        self.switch_label_1 = label_1
        self.switch_label_2 = label_2
        self.switch_color_1 = color_1
        self.switch_color_2 = color_2
        self.width = width
        
    def paintEvent(self, event):
        label = self.switch_label_1 if self.isChecked() else self.switch_label_2
        
        if self.isChecked():
            bg_color = QColor(self.switch_color_1)
        else:
            bg_color = QColor(self.switch_color_2)
                
        radius = 10
        width = self.width
        center = self.rect().center()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(center)
        painter.setBrush(QColor(0,0,0))

        pen = QPen(Qt.black)
        pen.setWidth(2)
        painter.setPen(pen)

        painter.drawRoundedRect(QRect(-width, -radius, 2*width, 2*radius), radius, radius)
        painter.setBrush(QBrush(bg_color))
        sw_rect = QRect(-radius, -radius, width + radius, 2*radius)
        if not self.isChecked():
            sw_rect.moveLeft(-width)
        painter.drawRoundedRect(sw_rect, radius, radius)
        painter.drawText(sw_rect, Qt.AlignCenter, label)
        
        
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