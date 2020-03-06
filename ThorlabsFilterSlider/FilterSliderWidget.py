# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 13:54:35 2020

@author: xinmeng
"""

from __future__ import division
import sys
sys.path.append('../')
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPoint, QRect, QObject
from PyQt5.QtGui import QColor, QPen, QPixmap, QIcon, QTextCursor, QFont

from PyQt5.QtWidgets import (QWidget, QButtonGroup, QLabel, QSlider, QSpinBox, QDoubleSpinBox, QGridLayout, QPushButton, QGroupBox, 
                             QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox, QTabWidget, QCheckBox, QRadioButton, 
                             QFileDialog, QProgressBar, QTextEdit)

import pyqtgraph as pg
import time
import sys

from ThorlabsFilterSlider.Filtermovement_Thread import FiltermovementThread

class FilterSliderWidgetUI(QWidget):
    
#    waveforms_generated = pyqtSignal(object, object, list, int)
#    SignalForContourScanning = pyqtSignal(int, int, int, np.ndarray, np.ndarray)
#    MessageBack = pyqtSignal(str)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
#        os.chdir('./')# Set directory to current folder.
        self.setFont(QFont("Arial"))
        
#        self.setMinimumSize(1350,900)
        self.setWindowTitle("FilterSliderWidget")
        self.layout = QGridLayout(self)
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------GUI for Filter movement----------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************
        ND_filtercontrolContainer = QGroupBox("ND filter control")
        self.NDfiltercontrolLayout = QGridLayout()
        
        bGBackupFromIntExt = QButtonGroup(self)

        self.filter1_pos0 = QPushButton('0')
        self.filter1_pos0.setCheckable(True)
        bGBackupFromIntExt.addButton(self.filter1_pos0)
        self.NDfiltercontrolLayout.addWidget(self.filter1_pos0, 0, 1)
        self.filter1_pos0.clicked.connect(lambda: self.filter_move_towards("COM9", 0))

        self.filter1_pos1 = QPushButton('1')
        self.filter1_pos1.setCheckable(True)
        bGBackupFromIntExt.addButton(self.filter1_pos1)
        self.NDfiltercontrolLayout.addWidget(self.filter1_pos1, 0, 2)    
        self.filter1_pos1.clicked.connect(lambda: self.filter_move_towards("COM9", 1))
        
        self.filter1_pos2 = QPushButton('2')
        self.filter1_pos2.setCheckable(True)
        bGBackupFromIntExt.addButton(self.filter1_pos2)
        self.NDfiltercontrolLayout.addWidget(self.filter1_pos2, 0, 3)
        self.filter1_pos2.clicked.connect(lambda: self.filter_move_towards("COM9", 2))
        
        self.filter1_pos3 = QPushButton('3')
        self.filter1_pos3.setCheckable(True)
        bGBackupFromIntExt.addButton(self.filter1_pos3)
        self.NDfiltercontrolLayout.addWidget(self.filter1_pos3, 0, 4)
        self.filter1_pos3.clicked.connect(lambda: self.filter_move_towards("COM9", 3)) 
        
        self.NDfiltercontrolLayout.addWidget(QLabel('Filter-1 pos: '), 0, 0)

        self.NDfiltercontrolLayout.addWidget(QLabel('Filter-2 pos: '), 1, 0)        
        bGBackupFromIntExt_1 = QButtonGroup(self)

        self.filter2_pos0 = QPushButton('0')
        self.filter2_pos0.setCheckable(True)
        bGBackupFromIntExt_1.addButton(self.filter2_pos0)
        self.NDfiltercontrolLayout.addWidget(self.filter2_pos0, 1, 1)
        self.filter2_pos0.clicked.connect(lambda: self.filter_move_towards("COM7", 0))

        self.filter2_pos1 = QPushButton('0.1')
        self.filter2_pos1.setCheckable(True)
        bGBackupFromIntExt_1.addButton(self.filter2_pos1)
        self.NDfiltercontrolLayout.addWidget(self.filter2_pos1, 1, 2)    
        self.filter2_pos1.clicked.connect(lambda: self.filter_move_towards("COM7", 1))
        
        self.filter2_pos2 = QPushButton('0.3')
        self.filter2_pos2.setCheckable(True)
        bGBackupFromIntExt_1.addButton(self.filter2_pos2)
        self.NDfiltercontrolLayout.addWidget(self.filter2_pos2, 1, 3)
        self.filter2_pos2.clicked.connect(lambda: self.filter_move_towards("COM7", 2))
        
        self.filter2_pos3 = QPushButton('0.5')
        self.filter2_pos3.setCheckable(True)
        bGBackupFromIntExt_1.addButton(self.filter2_pos3)
        self.NDfiltercontrolLayout.addWidget(self.filter2_pos3, 1, 4)
        self.filter2_pos3.clicked.connect(lambda: self.filter_move_towards("COM7", 3)) 
       
        ND_filtercontrolContainer.setLayout(self.NDfiltercontrolLayout)
        ND_filtercontrolContainer.setMaximumHeight(200)
        self.layout.addWidget(ND_filtercontrolContainer, 3, 0) 
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------Fucs for filter movement---------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #************************************************************************************************************************************** 
    def filter_move_towards(self, COMport, pos):
        filter_movement_thread = FiltermovementThread(COMport, pos)
        #filter_movement_thread.filtercurrent_position.connect(self.update_stage_current_pos)
        filter_movement_thread.start()
        time.sleep(1.5)
        filter_movement_thread.quit()
        filter_movement_thread.wait()
        
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        pg.setConfigOptions(imageAxisOrder='row-major')
        mainwin = FilterSliderWidgetUI()
        mainwin.show()
        app.exec_()
    run_app()