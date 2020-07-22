# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 23:23:58 2020

@author: ideheer
"""

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (QWidget, QPushButton, QRadioButton, QVBoxLayout, 
                             QCheckBox, QGridLayout, QHBoxLayout, QVBoxLayout, 
                             QGroupBox, QTabWidget, QGraphicsView, QGraphicsScene, 
                             QListWidget, QSizePolicy, QLabel, QComboBox, QLayout,
                             QStackedWidget, QSpinBox, QLineEdit)

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5 import QtGui

from StylishQT import MySwitch, roundQGroupBox, SquareImageView

from SampleStageControl.Stagemovement_Thread import StagemovementAbsoluteThread
from HamamatsuCam.HamamatsuActuator import CamActuator

import sys
import os

import matplotlib.pyplot as plt
import numpy as np
import time

"""
The goal of this widget is to snap a lot of images that can be used for stage 
registration. Analysis of the images should be done manually, because it appears
to be hard to do this in an automated fashion. 
"""

class StageWidget(QWidget):
    
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.main_application = parent
        
        self.set_image_saving_location(os.getcwd()+'/CoordinatesManager/Registration_Images/StageRegistration/')
        
        self.init_gui()
        
        
    def init_gui(self):
        layout = QGridLayout()
        
        self.setFixedSize(320,100)
        
        self.box = roundQGroupBox()
        self.box.setTitle("Stage")
        box_layout = QGridLayout()
        self.box.setLayout(box_layout)
        
        self.setLayout(layout)
        
        self.collect_data_button = QPushButton('Collect data')
        self.collect_data_button.clicked.connect(self.start_aqcuisition)
        
        box_layout.addWidget(self.collect_data_button)
        
        layout.addWidget(self.box)
    
    def set_image_saving_location(self, filepath):
        self.image_file_path = filepath
        
    def start_aqcuisition(self):
        global_pos = np.array(((-5000,-5000), (-5000, 5000), (5000, -5000), (5000, 5000)))
        global_pos_name = ['A', 'B', 'C', 'D']
        
        delta = 200
        local_pos = np.transpose(np.reshape(np.meshgrid(np.array((-delta, 0, delta)), np.array((-delta, 0, delta))), (2, -1)))
        local_pos_name = [str(i) for i in range(9)]
        
        self.cam = CamActuator()
        self.cam.initializeCamera()
        
        # Offset variables are used to generate replicates for good statistics
        offset_y = offset_x = delta
        
        cnt = 0
        for i in range(global_pos.shape[0]):
            for j in range(local_pos.shape[0]):
                x = global_pos[i,0] + local_pos[j,0] + offset_x
                y = global_pos[i,1] + local_pos[j,1] + offset_y
                
                stage_movement_thread = StagemovementAbsoluteThread(x, y)
                stage_movement_thread.start()
                time.sleep(2)
                stage_movement_thread.quit()
                stage_movement_thread.wait()
                
                image = self.cam.SnapImage(0.04)
                filename = global_pos_name[i]+local_pos_name[j]
                
                self.save_image(filename, image)
                
                cnt += 1
                print(str(cnt)+'/'+str(len(local_pos_name)*len(global_pos_name)))
        
        self.cam.Exit()
        
    def save_image(self, filename, image):
        plt.imsave(self.image_file_path+filename+'.png', image)
            
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        mainwin = StageWidget()
        mainwin.show()
        app.exec_()
    run_app()