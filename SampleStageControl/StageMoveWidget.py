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
                                color:Navy; }\
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
        self.stagecontrolLayout.addWidget(self.stage_upwards, 1, 2)
        self.stage_upwards.clicked.connect(lambda: self.sample_stage_move_upwards())
        self.stage_upwards.setShortcut('w')
        
        self.stage_left = QPushButton()
        self.stage_left.setToolTip("Click arrow to enable WASD keyboard control")
        self.stage_left.setFixedWidth(40)
        self.stage_left.setFixedHeight(40)
        self.stage_left.setIcon(QIcon('./Icons/LeftArrow.png'))
#        self.stage_left.setStyleSheet("QPushButton {padding: 10px;}");
        self.stage_left.setIconSize(QSize(35,35))
        self.stagecontrolLayout.addWidget(self.stage_left, 2, 1)
        self.stage_left.clicked.connect(lambda: self.sample_stage_move_leftwards())
        self.stage_left.setShortcut('a')
        
        self.stage_right = QPushButton()
        self.stage_right.setToolTip("Click arrow to enable WASD keyboard control")
        self.stage_right.setFixedWidth(40)
        self.stage_right.setFixedHeight(40)
        self.stage_right.setIcon(QIcon('./Icons/RightArrow.png')) 
        self.stage_right.setIconSize(QSize(35,35))
        self.stagecontrolLayout.addWidget(self.stage_right, 2, 3)
        self.stage_right.clicked.connect(lambda: self.sample_stage_move_rightwards())
        self.stage_right.setShortcut('d')
        
        self.stage_down = QPushButton()
        self.stage_down.setToolTip("Click arrow to enable WASD keyboard control")
        self.stage_down.setFixedWidth(40)
        self.stage_down.setFixedHeight(40)
        self.stage_down.setIcon(QIcon('./Icons/DownArrow.png'))
        self.stage_down.setIconSize(QSize(35,35))
        self.stagecontrolLayout.addWidget(self.stage_down, 2, 2)
        self.stage_down.clicked.connect(lambda: self.sample_stage_move_downwards())
        self.stage_down.setShortcut('s')
        
        self.stage_speed = QSpinBox(self)
        self.stage_speed.setFixedWidth(47)
        self.stage_speed.setMinimum(0)
        self.stage_speed.setMaximum(100000)
        self.stage_speed.setValue(300)
        self.stage_speed.setSingleStep(1650)        
        self.stagecontrolLayout.addWidget(self.stage_speed, 0, 1)
        self.stagecontrolLayout.addWidget(QLabel("Moving step:"), 0, 0)
        
        self.led_Label = QLabel("LED: ")
        self.stagecontrolLayout.addWidget(self.led_Label, 0, 2)
        
        self.switchbutton_LED = QPushButton()
        #self.switchbutton_LED.setStyleSheet("QPushButton {color:white;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                            #"QPushButton:pressed {color:black;background-color: blue; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.switchbutton_LED.setCheckable(True)
        self.switchbutton_LED.setIcon(QIcon('./Icons/AOTF_off.png'))
        #self.holdingbutton.toggle()
        
        self.switchbutton_LED.clicked.connect(lambda: self.execute_tread_single_sample_digital('LED'))
        self.switchbutton_LED.clicked.connect(lambda: self.change_AOTF_icon('LED'))
        self.stagecontrolLayout.addWidget(self.switchbutton_LED, 0, 3)
        
        self.stage_current_pos_Label = QLabel("Current position: ")
        self.stagecontrolLayout.addWidget(self.stage_current_pos_Label, 1, 0)
        
        self.stage_goto = QPushButton("Move to:")
        self.stage_goto.setStyleSheet("QPushButton {color:white;background-color: blue; border-style: outset;border-radius: 8px;border-width: 2px;font: bold 12px;padding: 6px}"
                                            "QPushButton:pressed {color:red;background-color: white; border-style: outset;border-radius: 8px;border-width: 2px;font: bold 12px;padding: 6px}"
                                            "QPushButton:hover:!pressed {color:green;background-color: blue; border-style: outset;border-radius: 8px;border-width: 2px;font: bold 12px;padding: 6px}")        
        self.stagecontrolLayout.addWidget(self.stage_goto, 3, 0)
        self.stage_goto.clicked.connect(lambda: self.sample_stage_move_towards())
        
        self.stage_goto_x = QLineEdit(self)
        self.stage_goto_x.setFixedWidth(47)
        self.stagecontrolLayout.addWidget(self.stage_goto_x, 3, 1)
        
        self.stage_goto_y = QLineEdit(self)
        self.stage_goto_y.setFixedWidth(47)
        self.stagecontrolLayout.addWidget(self.stage_goto_y, 3, 2)
        
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
        self.stage_current_pos_Label.setText('X:'+str(self.stage_current_pos[0])+' Y: '+str(self.stage_current_pos[1]))
        
    def execute_tread_single_sample_digital(self, channel):
        if channel == '640blanking':
            if self.switchbutton_640.isChecked():
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 1)
                execute_tread_singlesample_AOTF_digital.start()
            else:
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 0)
                execute_tread_singlesample_AOTF_digital.start()
        elif channel == '532blanking':
            if self.switchbutton_532.isChecked():
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 1)
                execute_tread_singlesample_AOTF_digital.start()
            else:
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 0)
                execute_tread_singlesample_AOTF_digital.start()        
        elif channel == '488blanking':
            if self.switchbutton_488.isChecked():
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 1)
                execute_tread_singlesample_AOTF_digital.start()
            else:
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 0)
                execute_tread_singlesample_AOTF_digital.start()  
                
        elif channel == 'LED':
            if self.switchbutton_LED.isChecked():
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 1)
                execute_tread_singlesample_AOTF_digital.start()
            else:
                execute_tread_singlesample_AOTF_digital = execute_tread_singlesample_digital()
                execute_tread_singlesample_AOTF_digital.set_waves(channel, 0)
                execute_tread_singlesample_AOTF_digital.start() 
                
    def change_AOTF_icon(self, channel):
        if channel == '640blanking':
            if self.switchbutton_640.isChecked():
                self.AOTF_red_iconlabel.setPixmap(QPixmap('./Icons/AOTF_red_on.png'))
            else:
                self.AOTF_red_iconlabel.setPixmap(QPixmap(self.ICON_off_AOTF))
        elif channel == '532blanking':
            if self.switchbutton_532.isChecked():
                self.AOTF_green_iconlabel.setPixmap(QPixmap('./Icons/AOTF_green_on.png'))
            else:
                self.AOTF_green_iconlabel.setPixmap(QPixmap(self.ICON_off_AOTF))        
        elif channel == '488blanking':
            if self.switchbutton_488.isChecked():
                self.AOTF_blue_iconlabel.setPixmap(QPixmap('./Icons/AOTF_blue_on.png'))
            else:
                self.AOTF_blue_iconlabel.setPixmap(QPixmap(self.ICON_off_AOTF)) 
        elif channel == 'LED':
            if self.switchbutton_LED.isChecked():
                self.switchbutton_LED.setIcon(QIcon('./Icons/LED_on.png'))
            else:
                self.switchbutton_LED.setIcon(QIcon('./Icons/AOTF_off.png'))
        
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        pg.setConfigOptions(imageAxisOrder='row-major')
        mainwin = StageWidgetUI()
        mainwin.show()
        app.exec_()
    run_app()