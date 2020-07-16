# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 12:04:41 2020

@author: xinmeng
"""
from __future__ import division
import sys
sys.path.append('../')
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPoint, QRect, QObject, QSize
from PyQt5.QtGui import QColor, QPen, QPixmap, QIcon, QTextCursor, QFont

from PyQt5.QtWidgets import (QWidget, QButtonGroup, QLabel, QSlider, QSpinBox, QDoubleSpinBox, QGridLayout, QPushButton, QGroupBox, 
                             QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox, QTabWidget, QCheckBox, QRadioButton, 
                             QFileDialog, QProgressBar, QTextEdit)
from NIDAQ.generalDaqerThread import execute_tread_singlesample_digital
import pyqtgraph as pg
import time
import sys

from SampleStageControl.Stagemovement_Thread import StagemovementRelativeThread, StagemovementAbsoluteThread

class StageWidgetUI(QWidget):
    
#    waveforms_generated = pyqtSignal(object, object, list, int)
#    SignalForContourScanning = pyqtSignal(int, int, int, np.ndarray, np.ndarray)
#    MessageBack = pyqtSignal(str)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
#        os.chdir('./')# Set directory to current folder.
        self.setFont(QFont("Arial"))
        
#        self.setMinimumSize(1350,900)
        self.setWindowTitle("StageWidget")
        self.layout = QGridLayout(self)
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------GUI for Stage--------------------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************
        stagecontrolContainer = QGroupBox("Stage control")
        stagecontrolContainer.setStyleSheet("QGroupBox {\
                                font: bold;\
                                border: 1px solid silver;\
                                border-radius: 6px;\
                                margin-top: 12px;\
                                color:Navy; \
                                background-color: #F8F8FF;}\
                                QGroupBox::title{subcontrol-origin: margin;\
                                                 left: 7px;\
                                                 padding: 5px 5px 5px 5px;}")
        self.stagecontrolLayout = QGridLayout()
        
        self.stage_upwards = QPushButton()
        self.stage_upwards.setToolTip("Click arrow to enable WASD keyboard control")
        self.stage_upwards.setFixedWidth(40)
        self.stage_upwards.setFixedHeight(40)
        self.stage_upwards.setIcon(QIcon('./Icons/UpArrow.png')) 
        self.stage_upwards.setIconSize(QSize(35,35))
        self.stagecontrolLayout.addWidget(self.stage_upwards, 1, 4)
        self.stage_upwards.clicked.connect(lambda: self.sample_stage_move_upwards())
        self.stage_upwards.setShortcut('w')
        
        self.stage_left = QPushButton()
        self.stage_left.setToolTip("Click arrow to enable WASD keyboard control")
        self.stage_left.setFixedWidth(40)
        self.stage_left.setFixedHeight(40)
        self.stage_left.setIcon(QIcon('./Icons/LeftArrow.png'))
#        self.stage_left.setStyleSheet("QPushButton {padding: 10px;}");
        self.stage_left.setIconSize(QSize(35,35))
        self.stagecontrolLayout.addWidget(self.stage_left, 2, 3)
        self.stage_left.clicked.connect(lambda: self.sample_stage_move_leftwards())
        self.stage_left.setShortcut('a')
        
        self.stage_right = QPushButton()
        self.stage_right.setToolTip("Click arrow to enable WASD keyboard control")
        self.stage_right.setFixedWidth(40)
        self.stage_right.setFixedHeight(40)
        self.stage_right.setIcon(QIcon('./Icons/RightArrow.png')) 
        self.stage_right.setIconSize(QSize(35,35))
        self.stagecontrolLayout.addWidget(self.stage_right, 2, 5)
        self.stage_right.clicked.connect(lambda: self.sample_stage_move_rightwards())
        self.stage_right.setShortcut('d')
        
        self.stage_down = QPushButton()
        self.stage_down.setToolTip("Click arrow to enable WASD keyboard control")
        self.stage_down.setFixedWidth(40)
        self.stage_down.setFixedHeight(40)
        self.stage_down.setIcon(QIcon('./Icons/DownArrow.png'))
        self.stage_down.setIconSize(QSize(35,35))
        self.stagecontrolLayout.addWidget(self.stage_down, 2, 4)
        self.stage_down.clicked.connect(lambda: self.sample_stage_move_downwards())
        self.stage_down.setShortcut('s')
        
        self.stage_speed = QSpinBox(self)
        self.stage_speed.setFixedWidth(47)
        self.stage_speed.setMinimum(0)
        self.stage_speed.setMaximum(100000)
        self.stage_speed.setValue(300)
        self.stage_speed.setSingleStep(1650)        
        self.stagecontrolLayout.addWidget(self.stage_speed, 2, 1)
        self.stagecontrolLayout.addWidget(QLabel("Step:"), 2, 0)
        
#        self.stage_current_pos_Label = QLabel("Current position: ")
#        self.stagecontrolLayout.addWidget(self.stage_current_pos_Label, 1, 0)
        
        self.stage_goto = QPushButton()
        self.stage_goto.setIcon(QIcon('./Icons/move_coord.png')) 
        self.stage_goto.setToolTip("Move to absolute position")
        self.stage_goto.setStyleSheet("QPushButton {color:white;background-color: #CCFFFF;}"
                                      "QPushButton:hover:!pressed {color:white;background-color: #FFE5CC;}")
        self.stage_goto.setFixedWidth(35)
        self.stage_goto.setFixedHeight(35)
        self.stagecontrolLayout.setAlignment(Qt.AlignVCenter)
#        self.stage_goto.setStyleSheet("QPushButton {color:white;background-color: #6495ED; border-style: outset;border-radius: 8px;border-width: 2px;font: bold 12px;padding: 6px}"
#                                            "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 8px;border-width: 2px;font: bold 12px;padding: 6px}"
#                                            "QPushButton:hover:!pressed {color:green;background-color: #6495ED; border-style: outset;border-radius: 8px;border-width: 2px;font: bold 12px;padding: 6px}")        
        self.stagecontrolLayout.addWidget(self.stage_goto, 1, 0)
        self.stage_goto.clicked.connect(lambda: self.sample_stage_move_towards())
        
        self.stage_goto_x = QLineEdit(self)
        self.stage_goto_x.setFixedWidth(47)
        self.stagecontrolLayout.addWidget(self.stage_goto_x, 1, 1)
        
        self.stage_goto_y = QLineEdit(self)
        self.stage_goto_y.setFixedWidth(47)
        self.stagecontrolLayout.addWidget(self.stage_goto_y, 1, 2)
        
#        self.stagecontrolLayout.addWidget(QLabel('Click arrow to enable WASD keyboard control'), 4, 0, 1, 3)
        
        stagecontrolContainer.setLayout(self.stagecontrolLayout)
#        stagecontrolContainer.setMinimumHeight(206)
        self.layout.addWidget(stagecontrolContainer, 2, 0)   
        
        #**************************************************************************************************************************************
        #--------------------------------------------------------------------------------------------------------------------------------------
        #-----------------------------------------------------------Fucs for stage movement----------------------------------------------------
        #--------------------------------------------------------------------------------------------------------------------------------------          
        #**************************************************************************************************************************************        
    def sample_stage_move_upwards(self):
        self.sample_move_distance_yRel = int(self.stage_speed.value())
        stage_movement_thread = StagemovementRelativeThread(0, self.sample_move_distance_yRel)
        stage_movement_thread.current_position.connect(self.update_stage_current_pos)
        stage_movement_thread.start()
        time.sleep(0.5)
        stage_movement_thread.quit()
        stage_movement_thread.wait()
        
    def sample_stage_move_downwards(self):
        self.sample_move_distance_yRel = int(self.stage_speed.value())
        stage_movement_thread = StagemovementRelativeThread(0, -1*self.sample_move_distance_yRel)
        stage_movement_thread.current_position.connect(self.update_stage_current_pos)
        stage_movement_thread.start()
        time.sleep(0.5)
        stage_movement_thread.quit()
        stage_movement_thread.wait()

    def sample_stage_move_leftwards(self):
        self.sample_move_distance_xRel = int(self.stage_speed.value())
        stage_movement_thread = StagemovementRelativeThread(self.sample_move_distance_xRel, 0)
        stage_movement_thread.current_position.connect(self.update_stage_current_pos)
        stage_movement_thread.start()
        time.sleep(0.5)
        stage_movement_thread.quit()
        stage_movement_thread.wait()
        
    def sample_stage_move_rightwards(self):
        self.sample_move_distance_xRel = int(self.stage_speed.value())
        stage_movement_thread = StagemovementRelativeThread(-1*self.sample_move_distance_xRel, 0)
        stage_movement_thread.current_position.connect(self.update_stage_current_pos)
        stage_movement_thread.start()
        time.sleep(0.5)
        stage_movement_thread.quit()
        stage_movement_thread.wait()
        
    def sample_stage_move_towards(self):
        self.sample_move_x = int(float(self.stage_goto_x.text()))
        self.sample_move_y = int(float(self.stage_goto_y.text()))
        stage_movement_thread = StagemovementAbsoluteThread(self.sample_move_x, self.sample_move_y)
        
        stage_movement_thread.current_position.connect(self.update_stage_current_pos)
        stage_movement_thread.start()
        time.sleep(2)
        stage_movement_thread.quit()
        stage_movement_thread.wait()
        
    def update_stage_current_pos(self, current_pos):
        self.stage_current_pos = current_pos
        self.stage_goto_x.setText(str(self.stage_current_pos[0]))
        self.stage_goto_y.setText(str(self.stage_current_pos[1]))
#        self.stage_current_pos_Label.setText('X:'+str(self.stage_current_pos[0])+' Y: '+str(self.stage_current_pos[1]))
        
        
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        pg.setConfigOptions(imageAxisOrder='row-major')
        mainwin = StageWidgetUI()
        mainwin.show()
        app.exec_()
    run_app()