# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 22:44:20 2019

@author: Meng
"""
import numpy as np
import time
from SampleStageControl.stage import LudlStage
from PyQt5.QtCore import pyqtSignal, QThread

class StagemovementRelativeThread(QThread):
    current_position = pyqtSignal(np.ndarray)
    def __init__(self, xRel, yRel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ludlStage = LudlStage("COM12")
        self.xRel = xRel
        self.yRel = yRel
        
    def run(self):
        self.ludlStage.moveRel(self.xRel,self.yRel)
        time.sleep(0.5)
        self.xPosition, self.yPosition = self.ludlStage.getPos()
        self.current_position_array = np.array([self.xPosition, self.yPosition])
        #print(self.current_position_array)
        self.current_position.emit(self.current_position_array)
        
class StagemovementAbsoluteThread(QThread):
    current_position = pyqtSignal(np.ndarray)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ludlStage = LudlStage("COM12")
        
    def SetTargetPos(self, xAbs, yAbs):
        self.xAbs = xAbs
        self.yAbs = yAbs
        
    def run(self):
        self.ludlStage.moveAbs(self.xAbs,self.yAbs)
        time.sleep(0.5)
        self.xPosition, self.yPosition = self.ludlStage.getPos()
        self.current_position_array = np.array([self.xPosition, self.yPosition])
        #print(self.current_position_array)
        self.current_position.emit(self.current_position_array)