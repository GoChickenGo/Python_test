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
        
        
class DrawingWidget(pg.ImageView):
    
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        self.flag_is_drawing = False
        self.new_roi = False
        
        self.vertices = []
        self.roilist = []
        self.pen = QtGui.QPen(QtCore.Qt.yellow)
        self.ui_widget = parent
        
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide() 
        self.ui.normGroup.hide()
        self.ui.roiPlot.hide()
        
        self.parent = parent
        
    def append_to_roilist(self, roi):
        self.roilist.append(roi)
        
    def clear_rois(self):
        for roi in self.roilist:
            self.scene.removeItem(roi)
        
        self.roilist = []
        
    def enable_drawing(self, val):
        if val:
            self.scene.sigMouseMoved.connect(self.mouseMoveEventDrawing)
            # self.scene.sigMouseClicked.connect(self.mousePressEventDrawing)
        else:
            try:                
                self.scene.sigMouseMoved.disconnect(self.mouseMoveEventDrawing)
                # self.scene.sigMouseClicked.disconnect(self.mousePressEventDrawing)    
            except TypeError:
                pass
        
    # def mousePressEventDrawing(self, e):
    #     if self.flag_is_drawing:
    #         self.flag_is_drawing = False
    #     else:
    #         self.new_roi = True
    #         self.flag_is_drawing = True
    #         self.start_point = self.getView().mapToView(e.pos())

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            if self.flag_is_drawing:
                self.flag_is_drawing = False
            else:
                self.flag_is_drawing = True
                self.new_roi = True            
    
    def mouseMoveEventDrawing(self, pos):
        if not self.flag_is_drawing:
            return
        
        point = self.getView().mapToView(pos)
        
        if self.new_roi:
            self.start_point = self.getView().mapToView(pos)
            
            self.selectedroi = pg.graphicsItems.ROI.PolyLineROI(positions=[self.start_point, point])
            self.roilist.append(self.selectedroi)
            
            self.selectedroi.setPen(self.pen)
            self.getView().addItem(self.selectedroi)
            self.new_roi = False
            
        else:            
            self.selectedroi.addFreeHandle(point)
            
            # Remove closing segment of previous mouse movement
            if len(self.selectedroi.segments) > 1:
                self.selectedroi.removeSegment(self.selectedroi.segments[-1])
                
            self.selectedroi.addSegment(self.selectedroi.handles[-1]['item'], self.selectedroi.handles[-2]['item'])
            
            # Add new closing segment
            self.selectedroi.addSegment(self.selectedroi.handles[0]['item'], self.selectedroi.handles[-1]['item'])
    
    def resizeEvent(self, event):
        """
        Forces the widget to be square upon resize event
        """
        # Create a square base size of 10x10 and scale it to the new size
        # maintaining aspect ratio.
        new_size = QSize(10, 10)
        new_size.scale(event.size(), Qt.KeepAspectRatio)
        self.resize(new_size)