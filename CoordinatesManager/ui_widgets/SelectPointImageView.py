#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  6 11:26:55 2020

@author: Izak de Heer
"""

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (QWidget, QPushButton, QRadioButton, QVBoxLayout, 
                             QCheckBox, QGridLayout, QGroupBox, QTabWidget, 
                             QGraphicsView, QGraphicsScene, QListWidget, QLabel)
from PyQt5.QtCore import QThread, pyqtSignal, QSize, Qt

import pyqtgraph as pg
from pyqtgraph import QtGui

import sys

import numpy as np
        
        
class SelectPointImageView(pg.ImageView):
    
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        self.pen = QtGui.QPen(QtCore.Qt.red)
        
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide() 
        self.ui.normGroup.hide()
        self.ui.roiPlot.hide()
        
        self.parent = parent
        
        self.scene.sigMouseClicked.connect(self.mousePressEvent)
        self.new_roi = True
        
    def mousePressEvent(self, e):
        pos = self.getView().mapToView(e.pos())
        
        if self.new_roi:
            self.roi1 = pg.graphicsItems.ROI.CrosshairROI(pos = pos, size = 100)
            self.getView().addItem(self.roi1)
            self.new_roi = False
        else:
            self.roi1.setPos(pos)
    
    def resizeEvent(self, event):
        """
        Forces the widget to be square upon resize event
        """
        # Create a square base size of 10x10 and scale it to the new size
        # maintaining aspect ratio.
        new_size = QSize(10, 10)
        new_size.scale(event.size(), Qt.KeepAspectRatio)
        self.resize(new_size)