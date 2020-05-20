# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 17:27:08 2019

@author: xinmeng
"""

from PyQt5.QtCore import pyqtSignal, QThread
from ThorlabsFilterSlider.filterpyserial import ELL9Filter

class FiltermovementThread(QThread):
    filtercurrent_position = pyqtSignal(int)
    def __init__(self, Filter_COM, position, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_COM_num = Filter_COM
        self.filter1 = ELL9Filter(self.filter_COM_num)
        self.filter_target_pos = position
        
    def run(self):
        self.filter1.moveToPosition(self.filter_target_pos)
        self.filter_current_position = self.filter1.getPosition()        
        
        self.filtercurrent_position.emit(self.filter_current_position)