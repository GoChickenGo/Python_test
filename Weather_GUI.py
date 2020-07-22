#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 18:28:40 2020

@author: xinmeng
"""

from __future__ import division
import sys
sys.path.append('../')
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPoint, QRect, QObject, QSize
from PyQt5.QtGui import QImage, QPalette, QBrush, QFont, QPainter, QColor, QPen

from PyQt5.QtWidgets import (QWidget, QButtonGroup, QLabel, QSlider, QSpinBox, QDoubleSpinBox, QGridLayout, QPushButton, QGroupBox, 
                             QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox, QTabWidget, QCheckBox, QRadioButton, 
                             QFileDialog, QProgressBar, QTextEdit, QDial, QStyleFactory)

import sys
try:
    from pyowm import OWM
except:
    pass

class WeatherUI(QWidget):
    """
    https://github.com/csparpa/pyowm
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFont(QFont("Arial"))
        self.setWindowTitle("Weather")
        self.layout = QGridLayout(self)
        
        BasicEventContainer = QGroupBox('Delft now')
        self.BasicEventLayout = QGridLayout()
        BasicEventContainer.setStyleSheet("QGroupBox {\
                                        font: bold;\
                                        border: 1px solid silver;\
                                        border-radius: 6px;\
                                        margin-top: 10px;\
                                        color:#7B68EE;\
                                        background-color : azure}\
                                        font-size: 14px;\
                                        QGroupBox::title{subcontrol-origin: margin;\
                                                         left: 7px;\
                                                         padding: 5px 5px 5px 5px;}")
        
        self.weather_status_label = QLabel()
        self.weather_status_label.setStyleSheet("QLabel { background-color : azure; color : teal; font: bold;}")
        self.weather_temperature_label = QLabel()
        self.weather_temperature_label.setStyleSheet("QLabel { background-color : azure; color : purple; }")
        
        try:
            owm = OWM('23c7e4896cc56fccab427f4a227097d4')# You MUST provide a valid API key, this is mine!
            
            # Search for current weather in Delft (NL)
            mgr = owm.weather_manager()
            observation = mgr.weather_at_place('Delft,NL')
            self.weather_obj = observation.weather
            self.weather_status_label.setText(self.weather_obj.detailed_status)
            self.weather_temperature_label.setText(str(self.weather_obj.temperature('celsius')['temp'])+ '°C')
        except:
            self.weather_status_label.setText('')
            self.weather_temperature_label.setText('')
        
        self.BasicEventLayout.addWidget(self.weather_status_label, 0, 0)
        self.BasicEventLayout.addWidget(self.weather_temperature_label, 0, 1)
        
        BasicEventContainer.setLayout(self.BasicEventLayout)
        self.layout.addWidget(BasicEventContainer, 0, 0)
        
    def closeEvent(self, event):
        QtWidgets.QApplication.quit()
        event.accept()
        
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        QtWidgets.QApplication.setStyle(QStyleFactory.create('Fusion'))
        mainwin = WeatherUI()
        mainwin.show()
        app.exec_()
    run_app()