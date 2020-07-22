#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  1 11:58:33 2020

@author: Izak de Heer
"""

import pyqtgraph as pg
from PyQt5 import QtCore, QtGui

class DrawingImageView(pg.ImageView):
    def __init__(self, *args, **kwargs):
        """
        Class inheriting from pg.ImageView. This class provides on-screen
        mouse drawing by overwritten mouse event methods. 
        """
        
        super().__init__(*args, **kwargs)        
        self.flag_drawing_mode = False
        self.isDrawing = False
        self.new_roi = False
        
        self.vertices = []
        self.roilist = []
        self.pen = QtGui.QPen(QtCore.Qt.red)
        
#    def changeDrawingMode(self):
#        if self.flag_drawing_mode:
#            self.getImageItem().mousePressEvent.connect(self.mousePressEventDrawing)# = self.mousePressEvent
#            self.getImageItem().mouseMoveEvent.connect(self.mouseMoveEventDrawing)# = self.mouseMoveEvent
#            self.getImageItem().mouseReleaseEvent.connect(self.mouseReleaseEventDrawing)# = self.mouseReleaseEvent
#        else:
#            self.getImageItem().mousePressEvent.disconnect(self.mousePressEventDrawing)# = self.mousePressEvent
#            self.getImageItem().mouseMoveEvent.disconnect(self.mouseMoveEventDrawing)# = self.mouseMoveEvent
#            self.getImageItem().mouseReleaseEvent.disconnect(self.mouseReleaseEventDrawing)# = self.mouseReleaseEvent
        self.view = self.getView()
        self.getImageItem().mousePressEvent = self.mousePressEventDrawing
        self.getImageItem().mouseMoveEvent = self.mouseMoveEventDrawing
        self.getImageItem().mouseReleaseEvent = self.mouseReleaseEventDrawing
    
    def mousePressEvent(self, e):
        if self.flag_drawing_mode:
            self.mousePressEventDrawing(e)
        else:
            super(DrawingImageView, self).getImageItem().mousePressEvent(e)
            
    def mouseMoveEvent(self, e):
        print('Mouse move event')
        if self.flag_drawing_mode:
            self.mouseMoveEventDrawing(e)
        else:
            super(DrawingImageView, self).getImageItem().mouseMoveEvent(e)
        
    def mouseReleaseEvent(self, e):
        print('Mouse release event')
        if self.flag_drawing_mode:
            self.mouseReleaseEventDrawing(e)
        else:
            super(DrawingImageView, self).getImageItem().mouseReleaseEvent(e)
        
    def mousePressEventDrawing(self, e):
        print('Mouse pressed')
        self.new_roi = True
        self.isDrawing = True

        self.x_start = e.pos().x()
        self.y_start = e.pos().y()
        
        self.handle_id = 0
        
    def mouseMoveEventDrawing(self, e):
        print('Mouse moved')
        if not self.isDrawing:
            return
        
        x = e.pos().x()
        y = e.pos().y()
            
        if self.new_roi:
            self.roilist.append(pg.graphicsItems.ROI.PolyLineROI(positions=[(self.x_start,self.y_start), (x,y)]))    
            self.selectedroi = self.roilist[-1]
            self.selectedroi.setPen(self.pen)
            self.getView().addItem(self.selectedroi)
            self.new_roi = False
            
        else:            
            self.handle_id += 1            
            self.selectedroi.addFreeHandle(pos=(x,y))
            
            # Remove closing segment of previous mouse movement
            if self.selectedroi.segments['name' == 'closingSegment'] in self.selectedroi.segments:
                self.selectedroi.removeSegment(self.selectedroi.segments[-1])
                
            self.selectedroi.addSegment(self.selectedroi.handles[-1]['item'], self.selectedroi.handles[-2]['item'])
            
            # Add new closing segment
            self.selectedroi.addSegment(self.selectedroi.handles[0]['item'], self.selectedroi.handles[-1]['item'])
                
    def mouseReleaseEventDrawing(self, e):
        print('Mouse released')
        self.isDrawing = False
    