#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 10:44:31 2020

@author: Izak de Heer
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

from CoordinatesManager import DMDActuator, Registrator, CoordinateTransformations
from ImageAnalysis.ImageProcessing import ProcessImage

import sys
import os

import matplotlib.pyplot as plt
import numpy as np

class DMDWidget(QWidget):
    
    sig_request_mask_coordinates = pyqtSignal()
    sig_start_registration = pyqtSignal()
    sig_finished_registration = pyqtSignal()
    
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.main_application = parent
        
        self.set_transformation_saving_location(os.getcwd()+'/CoordinatesManager/Registration/dmd_transformation')
        
        self.init_gui()
        
        
    def init_gui(self):
        layout = QGridLayout()
        
        self.setFixedSize(320,300)
        
        self.box = roundQGroupBox()
        self.box.setTitle("DMD control")
        box_layout = QGridLayout()
        self.box.setLayout(box_layout)
        
        self.setLayout(layout)
        
        self.connect_button = QPushButton('Connect')
        self.register_button = QPushButton('Register')
        
        lasers = ['640', '532', '488']
        self.transform_for_laser_menu = QListWidget()
        self.transform_for_laser_menu.addItems(lasers)
        self.transform_for_laser_menu.setFixedHeight(55)
        self.transform_for_laser_menu.setCurrentRow(0)
        self.project_button = QPushButton('Start projecting')
        self.clear_button = QPushButton('Clear memory')
        self.white_project_button = QPushButton('Full illum.')
        self.load_mask_container_stack = QStackedWidget()
        
        self.connect_button.clicked.connect(self.connect)
        self.register_button.clicked.connect(lambda: self.register(self.transform_for_laser_menu.selectedItems()[0].text()))
        self.project_button.clicked.connect(self.project)
        self.clear_button.clicked.connect(self.clear)
        self.white_project_button.clicked.connect(self.project_full_white)
        
        # Stack page 1
        self.load_mask_container_1 = roundQGroupBox()
        self.load_mask_container_1.setTitle('Load mask')
        load_mask_container_layout_1 = QGridLayout()
        self.load_mask_container_1.setLayout(load_mask_container_layout_1)
        self.load_mask_from_widget_button = QPushButton('From mask generator')
        self.load_mask_from_file_button = QPushButton('From file')
        self.load_mask_from_widget_button.clicked.connect(self.load_mask_from_widget)
        self.load_mask_from_file_button.clicked.connect(self.load_mask_from_memory)
        load_mask_container_layout_1.addWidget(self.load_mask_from_widget_button, 0, 0)
        load_mask_container_layout_1.addWidget(self.load_mask_from_file_button, 1, 0)
        
        # Stack page 2
        self.load_mask_container_2 = roundQGroupBox()
        self.load_mask_container_2.setTitle('Load mask')
        load_mask_container_layout_2 = QGridLayout()
        self.load_mask_container_2.setLayout(load_mask_container_layout_2)
        self.load_image = QPushButton('Image')
        self.load_folder = QPushButton('Folder')
        self.load_video = QPushButton('Video')
        
        self.load_image.clicked.connect(self.load_mask_from_file)
        self.load_folder.clicked.connect(self.load_mask_from_folder)
        
        load_mask_container_layout_2.addWidget(self.load_image, 0, 0)
        load_mask_container_layout_2.addWidget(self.load_folder, 1, 0)
        load_mask_container_layout_2.addWidget(self.load_video, 2, 0)
        
        # Stack page 3
        self.load_mask_container_3 = roundQGroupBox()
        self.load_mask_container_3.setTitle('Load mask')
        load_mask_container_layout_3 = QGridLayout()
        self.load_mask_container_3.setLayout(load_mask_container_layout_3)
        self.frame_rate_textbox = QLineEdit()
        self.frame_rate_textbox.setValidator(QtGui.QIntValidator())
        self.frame_rate_textbox.setText('1000000')
        
        self.repeat_imgseq_button = QCheckBox()
        
        self.confirm_button = QPushButton('Set')
        self.confirm_button.clicked.connect(self.set_movie_settings_on_DMD)
        
        load_mask_container_layout_3.addWidget(QLabel(u"Frame duration (µs):"), 0, 0)
        load_mask_container_layout_3.addWidget(self.frame_rate_textbox, 0, 1)
        load_mask_container_layout_3.addWidget(QLabel('Repeat sequence:'), 1, 0)
        load_mask_container_layout_3.addWidget(self.repeat_imgseq_button, 1, 1)
        load_mask_container_layout_3.addWidget(self.confirm_button, 2, 1)
        
        ## Add layers to stack        
        self.load_mask_container_stack.addWidget(self.load_mask_container_1)
        self.load_mask_container_stack.addWidget(self.load_mask_container_2)
        self.load_mask_container_stack.addWidget(self.load_mask_container_3)
        
        box_layout.addWidget(self.connect_button, 0, 0)
        box_layout.addWidget(self.register_button, 1, 0)
        box_layout.addWidget(QLabel('To be used with laser:'), 0, 1)
        box_layout.addWidget(self.transform_for_laser_menu, 1, 1, 2, 1)
        box_layout.addWidget(self.project_button, 2, 0)
        box_layout.addWidget(self.clear_button, 3, 0)
        box_layout.addWidget(self.white_project_button, 3, 1)
        
        box_layout.addWidget(self.load_mask_container_stack, 4, 0, 1, 2)
        
        layout.addWidget(self.box)
        
        self.open_latest_transformation()
    
    def connect(self):
        if self.connect_button.text() == 'Connect':
            self.DMD = DMDActuator.DMDActuator()
            self.connect_button.setText('Disconnect')
            
        else:
            self.DMD.disconnect_DMD()
            del self.DMD
            self.connect_button.setText('Connect')
    
    def register(self, laser):
        self.sig_start_registration.emit()
        ## Add control for lasers, signal slot should be there in AOTF widget
        registrator = Registrator.DMDRegistator(self.DMD)
        self.transform[laser] = registrator.registration(registration_pattern = 'circle')
        self.save_transformation()
        self.sig_finished_registration.emit()
    
    def check_mask_format_valid(self, mask):
        if len(mask.shape) == 3:
            print('Image is stack; using max projection')
            mask = np.max(mask, axis=2)
        
        if mask.shape[0] == 1024 and mask.shape[1] == 768:
            mask = mask.transpose()
        
        elif mask.shape[0] != 768 or mask.shape[1] != 1024:
            print('Image has wrong resolution; should be 1024x768')
            return False, None
        
        return True, mask
    
    def load_mask_from_memory(self):
        """
        Open a file manager to browse through files, load image file
        """
        self.load_mask_container_stack.setCurrentIndex(1)
    
    def load_mask_from_file(self):
        self.loadFileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select file', './CoordinateManager/Images/',"(*.jpg *.png)")
        image = 255-plt.imread(self.loadFileName)    
        check, image = self.check_mask_format_valid(image)
        if check:
            self.DMD.send_data_to_DMD(image)
            print('Image loaded')
            self.load_mask_container_stack.setCurrentIndex(0)
    
    def load_mask_from_folder(self):
        """
        Load files from folder using path and save frames in multidimensional array. 
        """
        foldername = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select folder', './CoordinateManager/Images/')
        list_dir_raw = sorted(os.listdir(foldername))
        
        list_dir = [file for file in list_dir_raw if file[-3:] in ['png', 'jpg']]
        list_nr = len(list_dir)
        image_sequence = np.zeros([768, 1024, list_nr])
        for i in range(list_nr):
            single_mask =255- plt.imread(foldername + '/' + list_dir[i])
            check, valid_single_mask = self.check_mask_format_valid(single_mask)
            if check:
                image_sequence[:,:,i] = valid_single_mask
            else: 
                return
            
        self.DMD.send_data_to_DMD(image_sequence)
        
        self.load_mask_container_stack.setCurrentIndex(2)
    
    def set_movie_settings_on_DMD(self):
        repeat = self.repeat_imgseq_button.isChecked()
        frame_time = int(self.frame_rate_textbox.text())
        self.DMD.set_repeat(repeat)
        self.DMD.set_timing(frame_time)
        
        self.load_mask_container_stack.setCurrentIndex(0)
    
    def load_mask_from_widget(self):
        self.sig_request_mask_coordinates.emit()
        
    def receive_mask_coordinates(self, sig):
        ## Receive untransformed mask coordinates, transform them, create mask, 
        ## send mask to DMD. 

        [list_of_rois, flag_fill_contour, contour_thickness, flag_invert_mode] = sig
        
        list_of_rois = self.transform_coordinates(list_of_rois)
        
        self.mask = ProcessImage.CreateBinaryMaskFromRoiCoordinates(list_of_rois, \
                                                       fill_contour = flag_fill_contour, \
                                                       contour_thickness = contour_thickness, \
                                                       invert_mask = flag_invert_mode, 
                                                       mask_resolution = (768,1024))
        fig, axs = plt.subplots(1,1)
        axs.imshow(self.mask)
        self.DMD.send_data_to_DMD(self.mask)
    
    def project_full_white(self):
        self.DMD.send_data_to_DMD(np.ones((1024,768)))
        self.DMD.start_projection()
        self.project_button.setText('Stop projecting')
        
    def interupt_projection(self):
        if self.project_button.text() == 'Stop projecting':
            self.DMD.stop_projection()
            self.DMD.free_memory()
            self.project_button.setText('Start projecting')
    
    def continue_projection(self):
        self.DMD.stop_projection()
        self.DMD.free_memory()
        
        if self.project_button.text() == 'Stop projecting':
            self.DMD.send_data_to_DMD(self.mask)
            self.DMD.start_projection()
    
    def transform_coordinates(self, list_of_rois):
        laser = self.transform_for_laser_menu.selectedItems()[0].text()
        new_list_of_rois = []
        for roi in list_of_rois:
            new_list_of_rois.append(CoordinateTransformations.transform(roi, self.transform[laser]))
        
        return new_list_of_rois
            
    def project(self):
        if self.project_button.text() == 'Start projecting':
            print('Projecting')
            self.DMD.start_projection()
            self.project_button.setText('Stop projecting')
        else:
            self.DMD.stop_projection()
            self.project_button.setText('Start projecting')
            
    def clear(self):
        self.DMD.free_memory()
        
    def set_transformation_saving_location(self, filename):
        self.transformation_file_name = filename
    
    def save_transformation(self):
        for laser, transform in self.transform.items():
            size = transform.shape[0]
            np.savetxt(self.transformation_file_name+laser, np.reshape(transform, (-1, size)))
            
    def open_latest_transformation(self):
        self.transform = {}
        lasers = ['640', '532', '488']
        for laser in lasers:
            try:
                transform = np.loadtxt(self.transformation_file_name+laser)
            except:
                pass
            else: 
                print('Transform for '+laser+' loaded.')
                self.transform[laser] = np.reshape(transform, (transform.shape[1], -1, 2))
                print(self.transform[laser][:,:,0])
                print(self.transform[laser][:,:,1])
        
            
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        mainwin = DMDWidget()
        mainwin.show()
        app.exec_()
    run_app()