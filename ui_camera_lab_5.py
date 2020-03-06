# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 10:26:16 2019

Camera ROI and UI class. The idea was to program this completely seperately
from every data acquisition function but in the end this did not completely 
work out.

TO DO:
    - ROI can still be set outside of the maxbounds with the spinboxes. Should
    be an easy fix but since it's already functioning quite slow I don't know
    how to keep this optimised
    
    
    -When in external triggering mode, the program functions very slow/crashes
    when the camera stops receiving triggers (ergo does not gather any more 
    images). This is an important point to fix. Might has to do with the UI,
    not the backend..
    
    -When in external triggering mode, while the roi gets opened it tries to get
    a picture. With no triggers incoming, it will keep waiting and crash.
    
    -update the circ buffer widget in the main ui when updating the circular 
    buffer size within the timed window popup. 
    
    -possibly create a popup settings menu that gets all available settings
    instead of hardcoding some! Take this as inspiration maybe 
    https://github.com/Jhsmit/micromanager-samples/blob/master/mm_print_properties.py
    
    

@author: dvanderheijden
"""

#['ThorCam','ThorlabsUSBCamera','ThorCam']

from __future__ import division
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialogButtonBox, QWidget, QLabel, QGridLayout, \
QPushButton, QLineEdit, QGroupBox, QVBoxLayout, QHBoxLayout, QSpinBox, QComboBox
from PyQt5.QtCore import QTimer, QRect, QRectF
from PyQt5.QtGui  import QIntValidator,  QDoubleValidator

import pyqtgraph as pg
import numpy as np
import sys

from camera_backend_lab_5 import Camera

'''
Some general settings for pyqtgraph, these only have to do with appearance 
except for row-major, which inverts the image and puts mirrors some axes.
'''

pg.setConfigOptions(imageAxisOrder='row-major')
pg.setConfigOption('background', 'k')
pg.setConfigOption('foreground', 'w')
pg.setConfigOption('useOpenGL', True)
pg.setConfigOption('leftButtonPan', False)


class TimedPopup(QWidget):
    def __init__(self, camdev, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Timed Video")
        self.resize(500, 300)
        self.camdev = camdev #for accesing the camera device (camera backend)
        
        #-----------------Creating line inputs---------------------------------
        durationContainer = QGroupBox()
        durationLayout = QGridLayout()
        
        durationLayout.addWidget(QLabel\
        ("How many frames/seconds would you like to record?"),0,0,1,3)
        
        self.framesnumber = QLineEdit()
        self.framesnumber.setValidator(QIntValidator(0,99999))
        self.framesnumber.setFixedWidth(100)
        self.framesnumber.returnPressed.connect(self.framesnumber_changed)
        durationLayout.addWidget(QLabel("Recording frames:"),1,0)
        durationLayout.addWidget(self.framesnumber,1,1)
        
        self.secondsnumber = QLineEdit()
        self.dblval = QDoubleValidator()
        self.dblval.setRange(0,9999)
        self.dblval.setDecimals(1)
        self.secondsnumber.setValidator(self.dblval)
        self.secondsnumber.setFixedWidth(100)
        self.secondsnumber.returnPressed.connect(self.secondsnumber_changed)
        durationLayout.addWidget(QLabel("Recording time (s):"),1,2)
        durationLayout.addWidget(self.secondsnumber,1,3)
        
        self.bufsize = QLineEdit()
        self.bufsize.setValidator(self.dblval)
        self.bufsize.setFixedWidth(100)
        self.bufsize.returnPressed.connect(self.framesnumber_changed)
        durationLayout.addWidget(QLabel("Buffer size (gb):"),2,0)
        durationLayout.addWidget(self.bufsize,2,1)
        
        self.buffercalculator = QPushButton("Calculate buffer size")
        self.buffercalculator.pressed.connect(self.calculate_buffer_size)
        durationLayout.addWidget(self.buffercalculator,2,2)
        
        durationContainer.setMaximumHeight(100)
        durationContainer.setMaximumWidth(500)

        durationContainer.setLayout(durationLayout)
        #----------------------------------------------------------------------
        self.dialog= QDialogButtonBox()
        self.dialog.addButton(QDialogButtonBox.Ok)
        self.dialog.accepted.connect(self.Ok)
        
        self.dialog.addButton(QDialogButtonBox.Cancel)
        self.dialog.rejected.connect(self.Cancel)
               
        #------------------------Master----------------------------------------
        master = QGridLayout()
        master.addWidget(durationContainer,0,0)
        master.addWidget(self.dialog,1,0)
        self.setLayout(master)


    def framesnumber_changed(self):
        framerate = self.camdev.get_framerate()
        secs = str(float(self.framesnumber.text())/framerate)
        self.secondsnumber.setText(secs)

    def secondsnumber_changed(self):        
        framerate = self.camdev.get_framerate()
        frames = str(int(float(self.secondsnumber.text())*framerate))
        self.framesnumber.setText(frames)
    
    def calculate_buffer_size(self):
        imsize = self.camdev.imsize()/(1000)
        frames = float(self.framesnumber.text())
        bufsize = round((imsize*frames),2) #buffersize in gb
        self.bufsize.setText(str(bufsize))
        
    
    def Ok(self):
        bufsize = int(float(self.bufsize.text())*1000)
        self.camdev.set_buf_size(bufsize)
        self.camdev.timed_recording(int(self.framesnumber.text()))
        self.close()

    def Cancel(self):
        self.close()
        
class CameraROI(QWidget):
    def __init__(self, camdev, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        #----------------------------General settings--------------------------  
        
        self.setMinimumSize(300,120)
        self.setWindowTitle("Camera ROI")
        self.resize(686, 545)
        
        self.camdev = camdev #for accesing the camera device (camera backend)
        
        #----------------------------Adding Imageview--------------------------
        
        self.roiWidget = pg.ImageView()
        self.roiWidget.ui.roiBtn.hide()
        self.roiWidget.ui.menuBtn.hide() 
        self.roiWidget.ui.histogram.hide() 
        self.roiWidget.ui.normGroup.hide()
        self.roiWidget.ui.roiPlot.hide()
        self.roiWidget.autoLevels()
        
        #------------------------------Adding ROI item-------------------------
        
        current_roi = self.camdev.mmc.getROI()
        '''
        By implementing the current ROI variable I make sure everytime the ROI 
        window is opened, the current ROI is shown.
        '''
        x = int(current_roi[0])
        y = int(current_roi[1])
        x_size = int(current_roi[2])
        y_size = int(current_roi[3])
        
        self.roi = pg.RectROI([x,y],[x_size,y_size], pen=(0,9))
        self.roiview = self.roiWidget.getView()
        self.roiview.addItem(self.roi)# add ROIs to main image    
        self.roi.maxBounds= QRectF(0,0,self.camdev.width,self.camdev.height) 
        #setting the max ROI bounds to be within the camera resolution
        
        self.roi.sigRegionChanged.connect(self.update_roi_coordinates) 
        #This function ensures the spinboxes show the actual roi coordinates

        #------------------------------Buttons---------------------------------

        self.center_roiButton = QPushButton()
        self.center_roiButton.setText("Center ROI")        
        self.center_roiButton.clicked.connect(lambda: self.set_roi_flag())
        '''
        set_roi_flag checks whether the centering button is pushed and 
        acts accordingly.
        '''
        self.center_roiButton.setCheckable(True)
        '''
        The ROI needs to be centered to maximise the framerate of the hamamatsu
        CMOS. When not centered it will count the outermost vertical pixel and
        treats it as the size of the ROI. See the camera manual for a more 
        detailed explanation.
        '''
        
        self.set_roiButton = QPushButton()
        self.set_roiButton.setText("Set ROI")
        self.set_roiButton.clicked.connect(self.set_roi)
        
        
        self.clear_roiButton = QPushButton()
        self.clear_roiButton.setText("Clear ROI")
        self.clear_roiButton.clicked.connect(self.clear_roi)
        
        

        self.get_frameButton = QPushButton()
        self.get_frameButton.setText("Get last frame")
        self.get_frameButton.clicked.connect(self.get_frame)
        
        cameraroiContainer = QGroupBox()
        cameraroiLayout = QGridLayout()
        cameraroiLayout.addWidget(self.roiWidget,0,0,0,4)
        cameraroiLayout.addWidget(self.set_roiButton,1,0)
        cameraroiLayout.addWidget(self.clear_roiButton,1,1)
        cameraroiLayout.addWidget(self.get_frameButton,1,2)
        cameraroiLayout.addWidget(self.center_roiButton,1,3)
        cameraroiContainer.setLayout(cameraroiLayout)

        #------------------------------Spinboxes-------------------------------
        '''
        On request of Xin some spinboxes for better monitoring and setting the 
        ROI. Upon changing the values of the spinboxes the ROI gets updated and 
        vice-versa.
        '''
        coordinateBox = QGroupBox("ROI coordinates")
        coordinatesLayout = QHBoxLayout()
        
        self.x_position = QSpinBox()
        self.x_position.setFixedWidth(60)
        self.x_position.setMaximum(self.camdev.width)
        self.x_position.valueChanged.connect(self.spin_value_changed)
        
        xBox = QGroupBox()
        xboxLayout = QHBoxLayout()
        xboxLayout.addWidget(QLabel("x position:"),0)
        xboxLayout.addWidget(self.x_position,1)
        xBox.setMaximumWidth(200)
        xBox.setLayout(xboxLayout)


        self.y_position = QSpinBox()
        self.y_position.setFixedWidth(60)
        self.y_position.setMaximum(self.camdev.height)
        self.y_position.valueChanged.connect(self.spin_value_changed)
        
        yBox = QGroupBox()
        yboxLayout = QHBoxLayout()
        yboxLayout.addWidget(QLabel("y position:"),0)
        yboxLayout.addWidget(self.y_position,1)
        yBox.setMaximumWidth(200)
        yBox.setLayout(yboxLayout)

        self.x_size = QSpinBox()
        self.x_size.setFixedWidth(60)
        self.x_size.setMaximum(self.camdev.width)
        self.x_size.valueChanged.connect(self.spin_value_changed)
        
        x_sizeBox = QGroupBox()
        x_sizeboxLayout = QHBoxLayout()
        x_sizeboxLayout.addWidget(QLabel("x size:"),0)
        x_sizeboxLayout.addWidget(self.x_size,1)
        x_sizeBox.setMaximumWidth(200)
        x_sizeBox.setLayout(x_sizeboxLayout)

        
        self.y_size = QSpinBox()
        self.y_size.setFixedWidth(60)
        self.y_size.setMaximum(self.camdev.height)
        self.y_size.setValue(y_size)
        self.y_size.valueChanged.connect(self.spin_value_changed)
        
        y_sizeBox = QGroupBox()
        y_sizeboxLayout = QHBoxLayout()
        y_sizeboxLayout.addWidget(QLabel("y size:"),0)
        y_sizeboxLayout.addWidget(self.y_size,1)
        y_sizeBox.setMaximumWidth(200)
        y_sizeBox.setLayout(y_sizeboxLayout)

        
        coordinatesLayout.addWidget(xBox,0)
        coordinatesLayout.addWidget(yBox,1)
        coordinatesLayout.addWidget(x_sizeBox,2)
        coordinatesLayout.addWidget(y_sizeBox,3)
        
        coordinateBox.setLayout(coordinatesLayout)
        
        coordinateBox.setMaximumHeight(100)

        #------------------------------Master----------------------------------
        master = QGridLayout()
        master.addWidget(coordinateBox,0,0)
        master.addWidget(cameraroiContainer,1,0)
        self.setLayout(master)
        
        #-------------------------Initial Settings-----------------------------
        self.center_roiButton.click() #Best if the ROI is centered
        self.get_frame() #Saves the press of a button when opening the ROI
        
        #######################################################################
        #---------------------------Functions----------------------------------
        #######################################################################
        
    def set_roi(self):     
        self.roi_x = int(self.roi.pos()[0])
        self.roi_y = int(self.roi.pos()[1])
        self.roi_x_size = int(self.roi.size()[0])
        self.roi_y_size = int(self.roi.size()[1])       
        self.camdev.set_cam_roi(self.roi_x,self.roi_y,self.roi_x_size,self.roi_y_size)
    
    def clear_roi(self):
        self.camdev.clear_roi()
        
        
    def get_frame(self):
        self.camdev.snap_roi()
        self.roiWidget.setImage(self.camdev.image_roi)
        self.set_roi()
        
        #---------------------Spinbox Functions--------------------------------
        
    def update_roi_coordinates(self):
        self.roi_x = int(self.roi.pos()[0])
        self.roi_y = int(self.roi.pos()[1])
        self.roi_height = int(self.roi.size()[1])
        self.roi_width = int(self.roi.size()[0])
        
        self.x_position.setValue(self.roi_x)
        self.y_position.setValue(self.roi_y)
        self.x_size.setValue(self.roi_width)
        self.y_size.setValue(self.roi_height)
      
    def spin_value_changed(self):
        
        if self.x_size.value() != self.roi_x_size or self.y_size.value() != self.roi_y_size:

            self.roi.setSize([self.x_size.value(),self.y_size.value()])
        
        
        if self.center_roiButton.isChecked():
            if self.x_position.value() != self.roi_x:
                self.roi.setPos(self.x_position.value())
        else:
            if self.x_position.value() != self.roi_x or self.y_position.value() != self.roi_y:
                self.roi.setPos(self.x_position.value(),self.y_position.value())

    #----------------------------ROI centering functions----------------------

    def center_roi(self):
        
        self.y_center = int(self.center_frame-0.5*self.roi_height)
        
        if  self.roi_y != self.y_center:
           self.roi.setPos(self.roi_x, self.y_center)
           self.update_roi_coordinates()
           
           
    def set_roi_flag(self):
        if self.center_roiButton.isChecked():
            self.y_position.setReadOnly(True)
            self.clear_roi()
            self.center_frame = 0.5*self.camdev.mmc.getImageHeight()
            """
            I've put the center frame in the set_roi_flag so it automatically
            adjusts to the number of pixels (which is dependent on the binning
            settings for example.)
            """
            self.set_roi()
            self.roi.sigRegionChanged.connect(lambda: self.center_roi()) 
            #setting the ROI to the center every move
            """
            If the ROI centering performs poorly it is also possible to use the 
            sigRegionChangeFinished() function. I like this better for now.
            """
        
        else:
            self.y_position.setReadOnly(False)
            self.roi.sigRegionChanged.disconnect() 
            '''
            I do not know how to disconnect one specific function, so I 
            disconnect both and then reconnect the update_roi_coordinates 
            function.
            '''
            self.roi.sigRegionChanged.connect(self.update_roi_coordinates) 
            

class CameraUI(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        #----------------------------------------------------------------------
        #----------------------------------GUI---------------------------------
        #----------------------------------------------------------------------
        self.setWindowTitle("Camera")

        #------------------------------Camera ui-------------------------------                           
        cameraimageContainer = QGroupBox("Camera View")
        cameraimageLayout = QGridLayout()
                
        #-------------------------Camera Operation Buttons---------------------        
        self.pictureButton = QPushButton("Snap picture") 
        #This is the button for taking a single picture and saving it
        self.pictureButton.clicked.connect(lambda: self.takepicture())
        
        self.singleframeButton = QPushButton("Single Frame") 
        #This is the button for displaying a single frame for ROI selection
        self.singleframeButton.clicked.connect(lambda: self.singleframe())
        
        self.recordButton = QPushButton()
        #Button for recording for undefined number of frames!
        self.recordButton.setText("Record")
        self.recordButton.setCheckable(True)
        self.recordButton.clicked.connect(lambda: self.record_enable())
      
        self.timedButton = QPushButton("Timed video") 
        #This is the option of recording for a preset time period/number of frames
        self.timedButton.clicked.connect(lambda: self.timedvideo())
        self.duration = QLineEdit()
        
        self.liveButton = QPushButton() 
        #Button for showing a live feed
        self.liveButton.setCheckable(True)
        self.liveButton.setText("Live")
        self.liveButton.clicked.connect(self.live_enabled) 
        self.liveButton.clicked.connect(self.live_feed_enable)
        
        self.roi_selectionButton = QPushButton()
        self.roi_selectionButton.setText("ROI selection")
        self.roi_selectionButton.setCheckable(True)
        self.roi_selectionButton.clicked.connect(self.roi_selection_pressed)

        #------------------------------Settings---------------------------
        camerasettingsContainer = QGroupBox("Settings")
        camerasettingsLayout  = QGridLayout()
        
        '''
        Adding comboboxes for all camera settings. Most are specific for 
        the hamamatsu orca flash 4 and will not work when used with other 
        cameras (such as the democam). In the future maybe better to
        generate these settings based on available micromanager setting instead
        of hardcoding!
        '''

        self.camBox = QComboBox()
        '''
        For connecting to a camera! 
        '''
        self.camBox.setGeometry(QRect(40, 40, 491, 31))
        self.camBox.setObjectName(("Camera"))
        self.camBox.addItem("Hamamatsu")
        self.camBox.addItem("Democam")
        self.camBox.activated[str].connect(self.set_cam)        
        camerasettingsLayout.addWidget(self.camBox,0,0)

        self.disconnectButton = QPushButton()
        '''
        Disconnect from the camera using the close_cam function in the backend 
        '''
        self.disconnectButton.setText("Disconnect")
        self.disconnectButton.clicked.connect(lambda: self.disconnect())
        camerasettingsLayout.addWidget(self.disconnectButton,1,0)

        
        self.trigBox = QComboBox()
        '''
        Internal is the camera free running mode,
        external is external triggering mode. I do not know what software means
        exactly, it might be a start trigger mode (trigger into free running)
        but I'll have to see
        '''
        self.trigBox.setGeometry(QRect(40, 40, 491, 31))
        self.trigBox.setObjectName(("Trigger Source"))
        self.trigBox.addItem("INTERNAL")
        self.trigBox.addItem("EXTERNAL")
        self.trigBox.addItem("SOFTWARE")
        self.trigBox.activated[str].connect(self.set_trigger_method)
        camerasettingsLayout.addWidget(self.trigBox,0,1)

        self.trig_activeBox =  QComboBox()            
        '''
        This is for selecting what type of triggering method to use.
        '''
        self.trig_activeBox.setGeometry(QRect(40, 40, 491, 31))
        self.trig_activeBox.setObjectName(("Trigger Active Edge"))
        self.trig_activeBox.addItem("SYNCREADOUT")
        self.trig_activeBox.addItem("EDGE")
        self.trig_activeBox.addItem("LEVEL")   
        self.trig_activeBox.activated[str].connect(self.set_trigger_active)
        camerasettingsLayout.addWidget(self.trig_activeBox,1,1)

        self.binBox = QComboBox()
        '''
        Binning effectively lowers the resolution while keeping sensitity high.
        Could be usefull in some scenarios.
        '''
        self.binBox.setGeometry(QRect(40, 40, 491, 31))
        self.binBox.setObjectName(("Binning"))
        self.binBox.addItem("1x1")
        self.binBox.addItem("2x2")
        self.binBox.addItem("4x4")
        self.binBox.activated[str].connect(self.set_binning)
        camerasettingsLayout.addWidget(self.binBox,0,2)

        self.circBufferSize = QLineEdit()
        '''
        Small widget for setting the circular buffer size! Sets size in GB. 
        Data stream size depends on the ROI size. 
        '''
        self.dblval = QDoubleValidator()
        self.dblval.setRange(0,80)
        self.dblval.setDecimals(1)
        self.circBufferSize.setValidator(self.dblval)
        self.circBufferSize.setFixedWidth(30)
        self.circBufferSize.returnPressed.connect(lambda: \
            self.set_circ_buffersize(float(self.circBufferSize.text())))
        camerasettingsLayout.addWidget(self.circBufferSize,1,2)

        self.exposureBox = QGroupBox ("Exposure Time")
        '''
        Small widget for setting the exposure time in miliseconds.
        '''
        self.exposureLayout = QGridLayout()    
        self.exposure_line = QLineEdit(self)
        self.exposure_line.setFixedWidth(60)      
        self.exposure_line.returnPressed.connect(lambda:self.exposure_changed())
        self.exposureLayout.addWidget(QLabel("Exposure time (ms)"),0,0)
        self.exposureLayout.addWidget(self.exposure_line,0,1)
        self.exposureBox.setMaximumWidth(300)
        self.exposureBox.setLayout(self.exposureLayout)
        
        camerasettingsLayout.addWidget(self.exposureBox,0,3,0,2)            
        camerasettingsContainer.setMaximumHeight(100)
        camerasettingsContainer.setLayout(camerasettingsLayout)
        
        #------------------------------Monitoring------------------------------
        monitorContainer = QGroupBox()
        monitorLayout = QGridLayout()
        
        self.framerate_monitor = QLabel()
        monitorLayout.addWidget(self.framerate_monitor,0,1)
        monitorLayout.addWidget(QLabel("Framerate (Hz):"),0,0)
                
        self.buffer_free_capacity_monitor = QLabel()
        monitorLayout.addWidget(self.buffer_free_capacity_monitor,1,1)
        monitorLayout.addWidget(QLabel("Buffer Capacity (ims):"),1,0)

        monitorContainer.setLayout(monitorLayout)
        monitorContainer.setMaximumWidth(200)
        
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(lambda: self.update_monitor())
        '''
        I don't start the monitor_timer during initialisation, because this will
        create an error. I start it when connecting to a camera!
        '''

        #------------------------------Videoscreen-----------------------------
        '''
        Initiating an imageview object for the main videoscreen. Hiding the pre
        existing ROI and menubuttons.
        '''

        self.videoWidget = pg.ImageView()
        self.video_item = self.videoWidget.getImageItem()
        self.video_item.setAutoDownsample(True)
        self.videoWidget.ui.roiBtn.hide()
        self.videoWidget.ui.menuBtn.hide() 
        self.videoWidget.ui.normGroup.hide()
        self.videoWidget.ui.roiPlot.hide()
        self.videoWidget.autoLevels()
        
        '''
        The update timer is build for setting the framerate of the imageviewer 
        for the main screen! The .start function determines the framerate 
        (30 ms = 33 Hz).
        '''

        self.update_timer_live = QTimer()
        self.update_timer_live.timeout.connect(lambda: self.update_view())
        '''
        I toggle the live feed on and off by starting/stopping the 
        update_timer_live!
        '''
        #--------------------------setting the camera viewer layout------------
        
        cameraimageLayout.addWidget(self.videoWidget)
        cameraimageContainer.setLayout(cameraimageLayout)    
        
        #--------------------------master for the camera operations----------
        
        camopContainer = QGroupBox("Operations")
        
        camopLayout = QVBoxLayout() 
        camopContainer.setMaximumWidth(200)
        
        camopLayout.addWidget(self.pictureButton,0)
        camopLayout.addWidget(self.recordButton,1)
        camopLayout.addWidget(self.timedButton,2)
        camopLayout.addWidget(self.liveButton,3)
        camopLayout.addWidget(self.singleframeButton,4)
        camopLayout.addWidget(self.roi_selectionButton,5)
        camopContainer.setLayout(camopLayout)
           
        #------------------------------Master----------------------------------
           
        master = QGridLayout()
        master.addWidget(camerasettingsContainer,0,0)
        master.addWidget(cameraimageContainer,1,0)
        master.addWidget(monitorContainer,0,1)
        master.addWidget(camopContainer,1,1)
        
        self.setLayout(master)

        #-----------------------------Startup----------------------------------
        
        self.no_cam_initiated()

#------------------------------------------------------------------------------
#-----------------------------FUNCTIONS----------------------------------------
#------------------------------------------------------------------------------
              

    #-----------------------Button disabling-----------------------------------                          
    """
    Here I disable the buttons and functions that are not to be used simultanuously  
    """       
    
    def live_enabled(self):
        if self.liveButton.isChecked():
            self.singleframeButton.setEnabled(False)
            self.roi_selectionButton.setEnabled(False)
            self.disconnectButton.setEnabled(False)              
            ''' 
            and now for the roi selection buttons. I put in the try so it 
            doesn't give an error when no ROI window is yet created. 
            '''
            try:
                '''
                Make sure the ROI window is closed to optimise performance
                '''
            
                self.roi_selectionButton.setChecked(False)
                self.close_roi_selection()
            except: 
                pass       
            '''
            Also making sure the settings are not changed during live acquisition
            '''
            self.camBox.setEnabled(False)   
            self.trigBox.setEnabled(False)
            self.trig_activeBox.setEnabled(False)
            self.binBox.setEnabled(False)
            self.circBufferSize.setEnabled(False)

            self.exposure_line.setEnabled(False)
            
        else:          
            self.singleframeButton.setEnabled(True)
            self.disconnectButton.setEnabled(True)
            self.roi_selectionButton.setEnabled(True)
            self.camBox.setEnabled(True)   
            self.trigBox.setEnabled(True)
            self.trig_activeBox.setEnabled(True)
            self.binBox.setEnabled(True)
            self.circBufferSize.setEnabled(True)

            self.exposure_line.setEnabled(True)   
            
    def no_cam_initiated(self):            
            self.timedButton.setEnabled(False)
            self.liveButton.setEnabled(False)
            self.singleframeButton.setEnabled(False)
            self.roi_selectionButton.setEnabled(False)
            self.pictureButton.setEnabled(False)
            self.recordButton.setEnabled(False)
            self.disconnectButton.setEnabled(False)
        
            self.trigBox.setEnabled(False)
            self.trig_activeBox.setEnabled(False)
            self.binBox.setEnabled(False)
            self.circBufferSize.setEnabled(False)

            self.exposure_line.setEnabled(False)
            
            self.monitor_timer.stop()
            self.framerate_flag = False
            
            self.cam_in = False
            
    def cam_initiated(self):
            self.timedButton.setEnabled(True)
            self.liveButton.setEnabled(True)
            self.singleframeButton.setEnabled(True)
            self.roi_selectionButton.setEnabled(True)
            self.pictureButton.setEnabled(True)
            self.recordButton.setEnabled(True)
            self.disconnectButton.setEnabled(True)
        
            self.trigBox.setEnabled(True)
            self.trig_activeBox.setEnabled(True)
            self.binBox.setEnabled(True)
            self.circBufferSize.setEnabled(True)

            self.exposure_line.setEnabled(True)   

            self.monitor_timer.start(100) 
            self.exposure_line.setText(str(int(self.cam.mmc.getExposure())))
            self.circBufferSize.setText(str(self.cam.mmc.getCircularBufferMemoryFootprint()/1000))
            self.framerate_flag = False    
            
            self.cam.timed_filming_done.connect(self.writing_done)
            
            self.cam_in = True
            
    def record_enabled(self):
            self.liveButton.setChecked(False)
            self.roi_selectionButton.setChecked(False)
            
            self.timedButton.setEnabled(False)
            self.liveButton.setEnabled(False)
            self.singleframeButton.setEnabled(False)
            self.roi_selectionButton.setEnabled(False)
            self.pictureButton.setEnabled(False)
            
            self.camBox.setEnabled(False)   
            self.trigBox.setEnabled(False)
            self.trig_activeBox.setEnabled(False)
            self.binBox.setEnabled(False)
            self.circBufferSize.setEnabled(False)
            self.disconnectButton.setEnabled(False)
            
            self.exposure_line.setEnabled(False)
            
            self.recordButton.setChecked(True)
        
    def record_disabled(self):
            self.timedButton.setEnabled(True)
            self.liveButton.setEnabled(True)
            self.singleframeButton.setEnabled(True)
            self.roi_selectionButton.setEnabled(True)
            self.pictureButton.setEnabled(True)
            self.disconnectButton.setEnabled(True)
            
            self.binBox.setEnabled(True)    
            self.camBox.setEnabled(True)   
            self.trigBox.setEnabled(True)
            self.trig_activeBox.setEnabled(True)
            self.circBufferSize.setEnabled(True)

            self.exposure_line.setEnabled(True)
    
            self.recordButton.setChecked(False)
            
    def writing_done(self, done):
        if done:
            self.record_disabled()
        else:
            self.record_enabled()
            
    #------------------------------Setting Camera Properties-------------------
    def set_cam(self,cam):
        if cam == "Democam":
            try:
                self.cam = Camera(['Camera', 'DemoCamera', 'DCam'])               
                print("{}".format(cam)+" camera loaded.")  
                self.cam_initiated()                
            except:
                print("{}".format(cam)+" camera not found.")
                self.no_cam_initiated()
        elif cam == "Thorcam":
            try:
                self.cam = Camera(['ThorCam','ThorlabsUSBCamera','ThorCam'])
                self.cam_initiated()
                print("{}".format(cam)+" camera loaded.")
                

            except:
                print("{}".format(cam)+" camera not found.")
                self.no_cam_initiated()
        elif cam == "Hamamatsu":
            try:
                self.cam = Camera(['Camera', 'HamamatsuHam', 'HamamatsuHam_DCAM'])
                self.cam_initiated()
                print("{}".format(cam)+" camera loaded.")
                
                #specifically for the Hamcam, not necesarry for the DCAM
                self.set_trigger_active("SYNCREADOUT")
                
            except:
                print("{}".format(cam)+" camera not found.")               
                self.no_cam_initiated()
        
    def set_trigger_method(self,method):
        self.cam.mmc.setProperty(self.cam.name, 'TRIGGER SOURCE', method)
    
    def set_trigger_active(self,edge):
        self.cam.mmc.setProperty(self.cam.name, 'TRIGGER ACTIVE', edge)
    
    def set_binning(self,binning):
        self.cam.mmc.setProperty(self.cam.name, 'Binning', binning)        
    
    def set_circ_buffersize(self,size):
        mbsize = 1000*size
        self.cam.set_buf_size(int(mbsize)) #size in GB
    
    def exposure_changed(self):
        set_time = float(self.exposure_line.text())
        self.cam.set_exposure_time(set_time)
        actual_exp_time = self.cam.get_exposure_time()
        if not set_time == round(actual_exp_time,1):
            self.exposure_line.setText(str(round(actual_exp_time,1)))
    
    def update_monitor(self):
        if self.cam_in:
            FPS = self.cam.get_framerate() 
            self.framerate_monitor.setText(str(FPS))
            
        if self.recordButton.isChecked():
            ims_in_buffer = self.cam.mmc.getRemainingImageCount()
            buffercap = self.cam.mmc.getBufferTotalCapacity()
            self.buffer_free_capacity_monitor.setText(str(ims_in_buffer)+"/"+ str(buffercap))
     
    #-----------------------Data Acquisition Functions-------------------------     
            
    def takepicture(self):
        self.cam.snap()

    def update_view(self):
        self.cam.get_frame()
        self.set_view()

    def set_view(self):
        self.videoWidget.setImage(self.cam.image)

    def timedvideo(self):
        self.timedWindow = TimedPopup(self.cam)
        self.timedWindow.setGeometry(QRect(500, 500, 200, 90))
        self.timedWindow.show()
        
              
    def live_feed_enable(self):
        if self.liveButton.isChecked():
            self.cam.startseqacq()
            self.update_timer_live.start(30) #ms timeout period
        else:         
            self.update_timer_live.stop()
            self.cam.stopseqacq()
    
    def timed_record(self):
        self.cam.start_recording()
        self.recordButton.setChecked(True) #so a manual stop can be implemented
        self.record_enabled()
         
    def record_enable(self):
        if self.recordButton.isChecked():  
            if self.update_timer_live.isActive():
                self.update_timer_live.clicked()
            self.cam.start_recording()
            
        else:
            self.cam.stop_recording()

    
    def check_recording(self):
        if self.recordButton.isChecked():
            self.recordButton.click()
        
    def singleframe(self):
        self.cam.get_single_frame()
        self.set_view()
               
    #----------------------ROI Selection---------------------------------------
    def roi_selection_pressed(self):
        
        if self.roi_selectionButton.isChecked():
            self.open_roi_selection()
        else:
            self.close_roi_selection()

    def close_roi_selection(self):
        self.roiWindow.close()
        self.roiWindow.roiWidget.close()


    def open_roi_selection(self):
        self.roiWindow = CameraROI(self.cam)        
        self.roiWindow.setGeometry(QRect(100, 100, 600, 600))
        self.roiWindow.show()

    #---------------------Closing the camera app-------------------------------
    def disconnect(self):
        self.cam.close_camera()
        self.no_cam_initiated()
        self.update_timer_live.stop()
        self.monitor_timer.stop()   
        self.stopRecording()

    def stopRecording(self):
        """close the camera."""
        try:  #Try so it doesn't give an error when no cam is initiated. 
            self.cam.stop_recording()
        except:
            pass
        
    def closeEvent(self, event):
        """Making sure the camera closes upon closing the application."""
        self.no_cam_initiated()
        self.update_timer_live.stop()
        self.monitor_timer.stop()   
        self.stopRecording()
        
        try:
            self.cam.close_camera()  
            self.roiWindow.close()
        except:
            pass
         
        
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        mainwin = CameraUI()
        mainwin.show()
        app.exec_()
        
    def check_qinput():
        DEVICE = ['Camera', 'DemoCamera', 'DCam']
        cam = Camera(DEVICE)
        
        qinput = QtWidgets.QApplication(sys.argv)
        mainwin = TimedPopup(cam)
        mainwin.show()
        qinput.exec_()
    
    run_app()
#    check_qinput()