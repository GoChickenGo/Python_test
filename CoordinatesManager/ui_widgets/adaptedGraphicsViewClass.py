#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 17:08:09 2020

@author: Izak de Heer
"""

import pyqtgraph as pg
from PyQt5 import QtCore, QtGui

class adaptedGraphicsView(pg.GraphicsView):
    def __init__(self, *args, **kwargs):
        """
        Class inheriting from pg.GraphicsView. This class provides on-screen
        mouse drawing by overwritten mouse event methods. 
        """
        
        super().__init__(*args, **kwargs)        
        self.last_x, self.last_y = None, None
        self.isDrawing = False
        self.vertices = []
        
    def mousePressEvent(self, e):
        self.isDrawing = True
        
    def mouseMoveEvent(self, e):
        if self.isDrawing:
            x = e.pos().x()
            y = e.pos().y()
            
            if self.last_x == None: # First event.
                self.last_x = x
                self.last_y = y
                self.vertices.append([x,y])
                 # Ignore the first time.
            
            else:
                pen = QtGui.QPen(QtCore.Qt.red)
                self.scene().addLine(QtCore.QLineF(x,y,self.last_x, self.last_y), pen)
                
                # Update the origin for next time.
                self.last_x = x
                self.last_y = y
                self.vertices.append([x,y])

    def mouseReleaseEvent(self, e):
        self.last_x = None
        self.last_y = None
        self.isDrawing = False
        ## In order to be able to draw multiple lines in one mask, 
        ## it should be known when the mouse was released, because that
        ## meaans a line segment is finished. This information is stored in the
        ## form of [-1, -1]. In order to prevent problems, the range of the 
        ## image should always be > 0. 
        self.vertices.append([-1,-1])