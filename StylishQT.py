# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 18:33:21 2020

@author: xinmeng

                For stylish looking
"""
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPoint, QRect, QObject, QSize, QAbstractAnimation, QVariantAnimation
from PyQt5.QtGui import QImage, QPalette, QBrush, QFont, QPainter, QColor, QPen, QIcon

from PyQt5.QtWidgets import (QWidget, QButtonGroup, QLabel, QSlider, QSpinBox, QDoubleSpinBox, QGridLayout, QPushButton, QGroupBox, 
                             QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox, QTabWidget, QCheckBox, QRadioButton, 
                             QFileDialog, QProgressBar, QTextEdit, QStyleFactory, QMainWindow, QMenu, QAction)

import pyqtgraph as pg

class roundQGroupBox(QGroupBox):
    def __init__(self, background_color = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """
        Round corner group box. Background color can be set e.g. background_color = 'blue'
        """
        if background_color != None:
            self.background_color = background_color
        else:
            self.background_color = "None"
        
        StyleSheet = "QGroupBox {\
                        font: bold;\
                        border: 1px solid silver;\
                        border-radius: 6px;\
                        margin-top: 12px;\
                        color:Navy; \
                        background-color: " + self.background_color + \
                        "}QGroupBox::title{subcontrol-origin: margin;\
                                         left: 7px;\
                                         padding: 5px 5px 5px 5px;}"
        self.setStyleSheet(StyleSheet)

class FancyPushButton(QtWidgets.QPushButton):
    clicked = pyqtSignal()
    """
    Button with animation effect. color1 is the color on the right, color2 on the left.
    """
    def __init__(self, width, height, parent=None, *args, **kwargs):
        super().__init__(parent)

        self.setMinimumSize(width, height)
        
        if len(kwargs) == 0:
            self.color1 = QColor(240, 53, 218)
            self.color2 = QColor(61, 217, 245)
        else:
            self.color1 = QColor(kwargs.get('color1', None)[0], kwargs.get('color1', None)[1], kwargs.get('color1', None)[2])
            self.color2 = QColor(kwargs.get('color2', None)[0], kwargs.get('color2', None)[1], kwargs.get('color2', None)[2])
        
        self._animation = QVariantAnimation(
            self,
            valueChanged=self._animate,
            startValue=0.00001,
            endValue=0.9999,
            duration=250
        )
        
#        self.setStyleSheet("QPushButton:disabled {color:white;background-color: grey; border-style: outset;border-radius: 8px;border-width: 2px;font: bold 12px;padding: 6px}")

    def _animate(self, value):
        qss = """
            font: 75 8pt "Microsoft YaHei UI";
            font-weight: bold;
            color: rgb(255, 255, 255);
            border-style: solid;
            border-radius:8px;
        """
        grad = "background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 {color1}, stop:{value} {color2}, stop: 1.0 {color1});".format(
            color1=self.color1.name(), color2=self.color2.name(), value=value
        )
        qss += grad
        self.setStyleSheet(qss)

    def enterEvent(self, event):
        self._animation.setDirection(QAbstractAnimation.Forward)
        self._animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animation.setDirection(QAbstractAnimation.Backward)
        self._animation.start()
        super().enterEvent(event)
        
    def mousePressEvent(self, event):
        self._animation.setDirection(QAbstractAnimation.Forward)
        self._animation.start()
        self.clicked.emit()
        super().enterEvent(event)       
        
class MySwitch(QtWidgets.QPushButton):
    """
    General switch button widget.
    """
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

class runButton(QtWidgets.QPushButton):
    """
    Button style for 'Run'
    """
    def __init__(self, label, parent = None):
        super().__init__(parent)
        self.setIcon(QIcon('./Icons/Run.png'))
        StyleSheet = ("QPushButton {color:#0000CC;font: bold;background-color: qlineargradient( x1:0 y1:0, x2:1 y2:0, stop:0 #FF99FF, stop:1 #9ED8FF);border-radius: 8px;}" 
                      "QPushButton:hover:!pressed {color:white;background-color: #9999FF;border-radius: 8px;}"
                      "QPushButton:disabled {color:white;background-color: grey;border-radius: 8px;}")
        self.setStyleSheet(StyleSheet)
        self.setText(label)
        self.setFixedHeight(32)
        self.setIconSize(QSize(30, 30))
        
class stop_deleteButton(QtWidgets.QPushButton):
    """
    Button style for 'STOP' or 'Delete'
    """
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setIcon(QIcon('./Icons/cross.png'))
        StyleSheet = ("QPushButton {color:#0000CC;font: bold;background-color: qlineargradient( x1:0 y1:0, x2:1 y2:0, stop:0 #CC0000, stop:1 #FF8000);border-radius: 8px;}" 
                      "QPushButton:hover:!pressed {color:white;background-color: #660000;border-radius: 8px;}"
                      "QPushButton:disabled {color:white;background-color: grey;border-radius: 8px;}")
        self.setStyleSheet(StyleSheet)
        
class saveButton(QtWidgets.QPushButton):
    """
    Button style for 'save'
    """
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setIcon(QIcon('./Icons/save.png'))
        StyleSheet = ("QPushButton {color:#0000CC;font: bold;background-color: qlineargradient( x1:0 y1:0, x2:1 y2:0, stop:0 #56F6C6, stop:1 #00CC00);border-radius: 8px;}" 
                      "QPushButton:hover:!pressed {color:white;background-color: #9999FF;border-radius: 8px;}"
                      "QPushButton:disabled {color:white;background-color: grey;border-radius: 8px;}")
        self.setStyleSheet(StyleSheet)               
        self.setFixedHeight(32)
        
class addButton(QtWidgets.QPushButton):
    """
    Button style for 'save'
    """
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setIcon(QIcon('./Icons/add.png'))
        StyleSheet = ("QPushButton {color:#0000CC;font: bold;background-color: qlineargradient( x1:0 y1:0, x2:1 y2:0, stop:0 #66FFFF, stop:1 #66FFB2);border-radius: 8px;}" 
                      "QPushButton:hover:!pressed {color:white;background-color: #9999FF;border-radius: 8px;}"
                      "QPushButton:disabled {color:white;background-color: grey;border-radius: 8px;}")
        self.setStyleSheet(StyleSheet)               
        self.setFixedHeight(32)
        
class generateButton(QtWidgets.QPushButton):
    """
    Button style for 'generate'
    """
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setIcon(QIcon('./Icons/generate.png'))
        StyleSheet = ("QPushButton {color:#0000CC;font: bold;background-color: qlineargradient( x1:0 y1:0, x2:1 y2:0, stop:0 #39C0F0, stop:1 #CBF0FD);border-radius: 8px;}" 
                      "QPushButton:hover:!pressed {color:white;background-color: #9999FF;border-radius: 8px;}"
                      "QPushButton:disabled {color:white;background-color: grey;border-radius: 8px;}")
        self.setStyleSheet(StyleSheet)               
        self.setFixedHeight(32)
        
class connectButton(QtWidgets.QPushButton):
    """
    Button style for 'generate'
    """
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setIcon(QIcon('./Icons/connect.png')) 
        self.setStyleSheet("QPushButton {color:black;background-color: qlineargradient( x1:0 y1:0, x2:1 y2:0, stop:0 #FFFF00, stop:1 #E5CCFF);border-radius: 8px;}" 
                                          "QPushButton:hover:!pressed {color:white;background-color: #9999FF;border-radius: 8px;}"
                                          "QPushButton:disabled {color:white;background-color: grey;border-radius: 8px;}") 
          
        self.setFixedHeight(30)
        
class disconnectButton(QtWidgets.QPushButton):
    """
    Button style for 'generate'
    """
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setIcon(QIcon('./Icons/disconnect.png')) 
        self.setStyleSheet("QPushButton {color:black;background-color: qlineargradient( x1:0 y1:0, x2:1 y2:0, stop:0 #FF9999, stop:1 #FFCC99);border-radius: 8px;}"
                                          "QPushButton:hover:!pressed {color:white;background-color: #9999FF;border-radius: 8px;}"
                                          "QPushButton:disabled {color:white;background-color: grey;border-radius: 8px;}") 
          
        self.setFixedHeight(30)

class SquareImageView(pg.ImageView):
    """
    ImageView widget that stays square when resized
    """
    
    def __init__(self, parent = None):
        super().__init__(parent)
    
    def resizeEvent(self, event):
        # Create a square base size of 10x10 and scale it to the new size
        # maintaining aspect ratio.
        new_size = QSize(10, 10)
        new_size.scale(event.size(), Qt.KeepAspectRatio)
        self.resize(new_size)
    

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    w = QtWidgets.QWidget()
    lay = QtWidgets.QVBoxLayout(w)
    
    container = roundQGroupBox(title = 'HaHA', background_color = 'azure')
    lay2 = QtWidgets.QVBoxLayout(container)
    lay.addWidget(container)
    
    for i in range(2):
        button = connectButton()
        button.setText("Kinase")
        lay2.addWidget(button)
        
    def closeEvent(self, event):
        QtWidgets.QApplication.quit()
        event.accept()

    w.resize(640, 480)
    w.show()
    app.exec_()