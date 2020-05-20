# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 11:23:13 2020

@author: xinmeng

Widely Tunable, Ultra-Fast, Solid-State Laser System.
"""

from __future__ import division
import sys
sys.path.append('../')
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPoint, QRect, QObject, QSize
from PyQt5.QtGui import QImage, QPalette, QBrush, QFont, QPainter, QColor, QPen

from PyQt5.QtWidgets import (QWidget, QButtonGroup, QLabel, QSlider, QSpinBox, QDoubleSpinBox, QGridLayout, QPushButton, QGroupBox, 
                             QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox, QTabWidget, QCheckBox, QRadioButton, 
                             QFileDialog, QProgressBar, QTextEdit, QDial, QStyleFactory)

import time
import sys
import threading, queue
from InsightX3.TwoPhotonLaser import TwoPhotonExecutor
from InsightX3.TwoPhotonLaser_backend import InsightX3
import StylishQT

class InsightWidgetUI(QWidget):
    """
    Refer to InSight X3 User Manual/APPENDIX A: Programming Guide
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
#        os.chdir('./')# Set directory to current folder.
        self.setFont(QFont("Arial"))
#        self.Laserinstance = TwoPhotonExecutor(address = 'COM11', WatchdogTimer = 3, WatchdogFreq = 1.1)
        self.Laserinstance = InsightX3('COM11')
        self.resize(265,150)
        self.setWindowTitle("Insight UI")
        self.layout = QGridLayout(self)
        self.watchdog_flag = True
        self.warmupstatus = False
        self.laserReady = False
        self.laserRun = False
        ini_watchdogtimeout = 0
        # =============================================================================
        #        Operation panel
        # =============================================================================
        BasicLaserEventContainer = QGroupBox()
        self.BasicLaserEventLayout = QGridLayout()
        
        PumpLabel = QLabel('Pump diode:')
        self.BasicLaserEventLayout.addWidget(PumpLabel, 1, 0)
#        PumpLabel.setAlignment(Qt.AlignRight)
        
        self.LaserSwitch = StylishQT.MySwitch('ON', 'green', 'OFF', 'red', width = 32)
        self.LaserSwitch.clicked.connect(self.LaserSwitchEvent)
        self.BasicLaserEventLayout.addWidget(self.LaserSwitch, 1, 1)
        
        ShutterLabel = QLabel('Shutter:')
        self.BasicLaserEventLayout.addWidget(ShutterLabel, 0, 0)
#        ShutterLabel.setAlignment(Qt.AlignRight)
        
        self.ShutterSwitchButton = StylishQT.MySwitch('ON', 'green', 'OFF', 'red', width = 32)
        self.ShutterSwitchButton.clicked.connect(self.ShutterSwitchEvent)
        self.BasicLaserEventLayout.addWidget(self.ShutterSwitchButton, 0, 1)
        
        self.ModeSwitchButton = StylishQT.MySwitch('ALIGN MODE', 'yellow', 'RUNNING MODE', 'cyan', width = 76)
        self.ModeSwitchButton.clicked.connect(self.ModeSwitchEvent)
        self.BasicLaserEventLayout.addWidget(self.ModeSwitchButton, 2, 0, 1, 2)
        
        WavelengthLabel = QLabel('Wavelength(nm):')
        self.BasicLaserEventLayout.addWidget(WavelengthLabel, 0, 2)
        
        self.SWavelengthTextbox = QSpinBox(self)
        self.SWavelengthTextbox.setMinimum(680)
        self.SWavelengthTextbox.setMaximum(1300)
        self.SWavelengthTextbox.setSingleStep(1)
        self.SWavelengthTextbox.setKeyboardTracking(False)
        self.BasicLaserEventLayout.addWidget(self.SWavelengthTextbox, 0, 3)
        self.SWavelengthTextbox.valueChanged.connect(self.setwavelegth)
        
        self.WatchdogTimerTextbox = QSpinBox(self)
        self.WatchdogTimerTextbox.setMinimum(0)
        self.WatchdogTimerTextbox.setMaximum(100000)
        self.WatchdogTimerTextbox.setSingleStep(1)
        self.WatchdogTimerTextbox.setKeyboardTracking(False)
        self.WatchdogTimerTextbox.setValue(ini_watchdogtimeout)
        self.BasicLaserEventLayout.addWidget(self.WatchdogTimerTextbox, 3, 1)
        self.BasicLaserEventLayout.addWidget(QLabel('Watch dog timer:'), 3, 0)
        self.WatchdogTimerTextbox.valueChanged.connect(self.setWatchdogTimer)
        
        BasicLaserEventContainer.setLayout(self.BasicLaserEventLayout)
        self.layout.addWidget(BasicLaserEventContainer, 1, 0)        
        # =============================================================================
        #         Status panel
        # =============================================================================
        LaserStatusContainer = QGroupBox('Laser status')
        self.LaserStatusLayout = QGridLayout()
        
        self.LaserStatuslabel = QLabel()
        self.LaserStatusLayout.addWidget(self.LaserStatuslabel, 0, 0)
        
        LaserStatusContainer.setLayout(self.LaserStatusLayout)
        self.layout.addWidget(LaserStatusContainer, 0, 0)

        # =============================================================================
        #         Quit event panel
        # =============================================================================
#        LaserQuitContainer = QGroupBox('Exit')
#        self.LaserQuitLayout = QGridLayout()
#        
#        QuitButtonStandby = QPushButton('Stand by', self)
#        QuitButtonStandby.clicked.connect(self.QuitStandby)
#        self.LaserQuitLayout.addWidget(QuitButtonStandby, 0, 0)
#        
#        QuitButtonStandby = QPushButton('Hibernate', self)
#        QuitButtonStandby.clicked.connect(self.QuitHibernate)
#        self.LaserQuitLayout.addWidget(QuitButtonStandby, 0, 1)
#        
#        LaserQuitContainer.setLayout(self.LaserQuitLayout)
#        self.layout.addWidget(LaserQuitContainer, 2, 0)        
        
        # =============================================================================
        #         Initialization
        # =============================================================================        
        try:
            querygap = 1.1
            self.Laserinstance.SetWatchdogTimer(0)
            time.sleep(0.3)
            self.Status_queue = queue.Queue()
            self.current_wavelength = self.Laserinstance.QueryWavelength()
            self.SWavelengthTextbox.setValue(int(self.current_wavelength))
            time.sleep(0.3)
            self.pill2kill = threading.Event()
            # self.Status_watchdog_thread = threading.Thread(target = self.Status_watchdog, args=(self.Status_queue, querygap), daemon = True)
            # self.Status_watchdog_thread.start()    
        except:
            self.LaserStatuslabel.setText('Laser not connected.')
            
            
    """
    # =============================================================================
    #     Laser events
    # =============================================================================
    """
    def Status_watchdog(self, Status_queue, querygap):
        
        while True:
            if self.watchdog_flag == True:
                self.Status_list = self.Laserinstance.QueryStatus()
                Status_queue.put(self.Status_list)
                self.LaserStatuslabel.setText(str(self.Status_list))
                time.sleep(querygap)
            else:
                print('Watchdog stopped')
                time.sleep(querygap)
        
    def LaserSwitchEvent(self):
        if self.LaserSwitch.isChecked():
            turnONThread = threading.Thread(target = self.TurnOnLaser)
            turnONThread.start()
#            self.TurnOnLaser()
        else:
            turnOFFThread = threading.Thread(target = self.TurnOffLaser)
            turnOFFThread.start()
        
    def TurnOnLaser(self):
        self.watchdog_flag = False
        time.sleep(0.5)
        self.Status_list = self.Laserinstance.QueryStatus()
        #-------------Initialize laser--------------
        if self.warmupstatus == False:
            
            warmupstatus = 0
            while int(warmupstatus) != 100:
                try:
                    warmupstatus = self.Laserinstance.QueryWarmupTime()
                    time.sleep(0.6)
                except:
                    time.sleep(0.6)
                    
            if int(warmupstatus) == 100:
                self.warmupstatus = True
                print('Laser fully warmed up.')

                if 'Laser state:Ready' in self.Status_list:
                    self.Laserinstance.Turn_On_PumpLaser()
                    
                    Status_list = []
        
                    while 'Laser state:RUN' not in Status_list:
                        time.sleep(1)
                        
                        try:
                            Status_list = self.Laserinstance.QueryStatus()
                        except:
                            pass
                        
                        if 'Laser state:RUN'  in Status_list:
                            self.laserRun = True
                            print('Laser state:RUN')
                            break
                    
        time.sleep(0.5)
        self.watchdog_flag = True
#        self.Status_watchdog_thread.event.set()
#        
#        while True:
#            if self.Status_watchdog_thread.event.is_set():
#                #-------------Initialize laser--------------
#                if self.warmupstatus == False:
#                    
#                    warmupstatus = 0
#                    while int(warmupstatus) != 100:
#                        try:
#                            warmupstatus = self.Laserinstance.QueryWarmupTime()
#                            time.sleep(0.6)
#                        except:
#                            time.sleep(0.6)
#                            
#                    if int(warmupstatus) == 100:
#                        self.warmupstatus = True
#                        print('Laser fully warmed up.')
#                        Current_status = Status_queue.get()
#                        if 'Laser state:Ready' in Current_status:
#                            self.Laserinstance.TurnLaserON()
#                        break
#            else:
#                time.sleep(0.5)
#            
#        self.Status_watchdog_thread.event.clear()
        
    def TurnOffLaser(self):
        self.watchdog_flag = False
        time.sleep(0.5)
        try:
            self.Laserinstance.Close_TunableBeamShutter()
            time.sleep(0.5)
        except:
            pass
        self.Laserinstance.SaveVariables()
        self.Laserinstance.Turn_Off_PumpLaser()

        
    def ShutterSwitchEvent(self):
        if self.ShutterSwitchButton.isChecked():
            turnONShuThread = threading.Thread(target = self.TurnOnLaserShutter)
            turnONShuThread.start()
        else:
            turnOFFShuThread = threading.Thread(target = self.TurnOffLaserShutter)
            turnOFFShuThread.start()
    
    def TurnOnLaserShutter(self):
        self.Status_list = self.Laserinstance.QueryStatus()
        if 'Tunable beam shutter closed' in self.Status_list:        
            self.watchdog_flag = False
            time.sleep(0.5)
            self.Laserinstance.Open_TunableBeamShutter()
            time.sleep(0.5)
            self.watchdog_flag = True     
        
    def TurnOffLaserShutter(self):
        self.Status_list = self.Laserinstance.QueryStatus()
        if 'Tunable beam shutter open' in self.Status_list:
            self.watchdog_flag = False
            time.sleep(0.5)
            self.Laserinstance.Close_TunableBeamShutter()
            time.sleep(0.5)
            self.watchdog_flag = True  
    
    def ModeSwitchEvent(self):
        if self.ModeSwitchButton.isChecked():        
            self.watchdog_flag = False
            time.sleep(0.5)

            self.Laserinstance.SetOperatingMode('MODE ALIGN')
            
            time.sleep(0.5)
            self.watchdog_flag = True
        else:
            self.watchdog_flag = False
            time.sleep(0.5)

            self.Laserinstance.SetOperatingMode('MODE RUN')
            
            time.sleep(0.5)
            self.watchdog_flag = True            
            
            
    def setwavelegth(self):
        self.watchdog_flag = False
        time.sleep(0.5)
        
        self.targetWavelength = int(self.SWavelengthTextbox.value())
        self.current_wavelength = self.Laserinstance.SetWavelength(self.targetWavelength)
        
        time.sleep(0.5)
        self.watchdog_flag = True
        
    def setWatchdogTimer(self):
        self.watchdog_flag = False
        time.sleep(0.5)
        
        WatchdogTimer = int(self.WatchdogTimerTextbox.value())
        self.Laserinstance.SetWatchdogTimer(WatchdogTimer)
        
        time.sleep(0.5)
        self.watchdog_flag = True
        
    def update_laser_status(self, status_list):
        self.LaserStatuslabel.setText(str(status_list))
        
    def QuitStandby(self):
        """
        It closes the shutters and disables the watchdog timer so that the laser does not stop when the GUI is closed. 
        It also saves the last set wavelength and motor positions, and it leaves all other components powered up and operating.
        """
        self.TurnOffLaserShutter()
        
        # Set timeout to a large value that is enough for next operation
        self.watchdog_flag = False
        time.sleep(0.5)
        
        self.Laserinstance.SetWatchdogTimer(0) # A value of 0 disables the software watchdog timer.

        time.sleep(0.5)
        self.Laserinstance.SaveVariables()
        
#        self.close()
        
    def QuitHibernate(self):
        """
        This is the default day-to-day operating mode. Shuts off the laser diode, closes the shutters, 
        and saves the wavelength and motor positions. It also closes the GUI.
        """
        self.TurnOffLaserShutter()
        self.watchdog_flag = False
        time.sleep(0.5)
        self.Laserinstance.SaveVariables()
        self.Laserinstance.Turn_Off_PumpLaser()  
        
#        self.close()
        
    def closeEvent(self, event):
        """
        https://stackoverflow.com/questions/37219153/how-to-change-the-buttons-order-in-qmessagebox
        """
        message = "<font size = 4 color = blue > LASER CLOSE</font> <br/><br/><font color = red > Standby</font> — Does not shut off the laser diode. It closes the shutters and disables the watchdog timer so that the laser does not stop when the GUI is closed.<br/><br/><font color = blue > Hibernate</font> — Shuts off the laser diode, closes the shutters, and saves the wavelength and motor positions."
        closeEventmsg = QMessageBox()
        closeEventmsg.setIcon(QMessageBox.Warning)
        closeEventmsg.setWindowTitle("Exiting...")
        closeEventmsg.setText(message)
        
        QuitStandbyButton = closeEventmsg.addButton("Stand by", QMessageBox.ActionRole)
        QuitHibernateButton = closeEventmsg.addButton("Hibernate", QMessageBox.ActionRole)
        QuitCancelButton = closeEventmsg.addButton("Back", QMessageBox.RejectRole)
        closeEventmsg.setDefaultButton(QuitCancelButton)
        
        QuitStandbyButton.clicked.connect(self.QuitStandby)
        QuitHibernateButton.clicked.connect(self.QuitHibernate)
        
        QuitCancelButton.clicked.connect(lambda:event.ignore())

        closeEventmsg.exec()
        
        
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        QtWidgets.QApplication.setStyle(QStyleFactory.create('Fusion'))
        mainwin = InsightWidgetUI()
        mainwin.show()
        app.exec_()
    run_app()