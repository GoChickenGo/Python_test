# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 18:33:21 2020

@author: xinmeng
"""
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPoint, QRect, QObject, QSize, QAbstractAnimation, QVariantAnimation
from PyQt5.QtGui import QImage, QPalette, QBrush, QFont, QPainter, QColor, QPen, QIcon

from PyQt5.QtWidgets import (QWidget, QButtonGroup, QLabel, QSlider, QSpinBox, QDoubleSpinBox, QGridLayout, QPushButton, QGroupBox, 
                             QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox, QTabWidget, QCheckBox, QRadioButton, 
                             QFileDialog, QProgressBar, QTextEdit, QStyleFactory, QMainWindow, QMenu, QAction)

class FancyPushButton(QtWidgets.QPushButton):
    clicked = pyqtSignal()
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
        
        
if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    w = QtWidgets.QWidget()
    lay = QtWidgets.QVBoxLayout(w)

    for i in range(5):
        button = FancyPushButton(60,60, color1=(10,100,50), color2=(204,204,255))
        button.setText("Kinase")
        lay.addWidget(button)
    lay.addStretch()
    w.resize(640, 480)
    w.show()
    sys.exit(app.exec_())