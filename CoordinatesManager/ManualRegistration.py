#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  3 17:03:45 2020

@author: Izak de Heer
"""

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (QWidget, QPushButton, QRadioButton, QVBoxLayout, 
                             QCheckBox, QGridLayout, QHBoxLayout, QVBoxLayout, 
                             QGroupBox, QTabWidget, QGraphicsView, QGraphicsScene, 
                             QListWidget, QSizePolicy, QLabel, QComboBox, QLayout,
                             QStackedWidget, QSpinBox)

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from StylishQT import MySwitch, roundQGroupBox, SquareImageView

import pyqtgraph as pg
from pyqtgraph import QtGui

from CoordinatesManager.ui_widgets.SelectPointImageView import SelectPointImageView
from CoordinatesManager import CoordinateTransformations

import os
import sys
import matplotlib.pyplot as plt
import numpy as np

# from CoordinatesManager.Scratch.findTransformationCurvefit import find_transform

# Ensure that the Widget can be run either independently or as part of Tupolev.
if __name__ == "__main__":
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname+'/../')

class ManualRegistrationWindow(QWidget):
    
    sig_request_camera_image = pyqtSignal()
    sig_cast_transformation_to_DMD = pyqtSignal(np.ndarray, str)
    sig_cast_transformation_to_galvos = pyqtSignal(np.ndarray)
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        
        # self.setFixedSize(100,500)
        
        layout = QGridLayout()
        self.setLayout(layout)
        
        self.image_viewer = SelectPointImageView()
        layout.addWidget(self.image_viewer, 0, 0, 1, 3)
        
        open_image_button = QPushButton('Open image from file')
        retreive_image_from_camera_button = QPushButton('Load camera image')
        open_image_button.clicked.connect(self.open_image_file)
        retreive_image_from_camera_button.clicked.connect(lambda: self.sig_request_camera_image.emit())
        layout.addWidget(open_image_button, 1, 0, 1, 1)
        layout.addWidget(retreive_image_from_camera_button, 1, 1, 1, 1)
        
        self.coordinate_counter = QLabel('Saved coordinates: 0')
        layout.addWidget(self.coordinate_counter, 2, 0)
        self.filename_textbox = QLabel('File: ')
        layout.addWidget(self.filename_textbox, 2, 1)
        
        transformation_box = roundQGroupBox()
        transformation_box.setTitle('Transformation')
        transformation_box_layout = QGridLayout()
        transformation_box.setLayout(transformation_box_layout)
        
        self.transformation_order_spinbox = QSpinBox()
        transformation_box_layout.addWidget(QLabel('Polynomial order:'), 0, 0)
        transformation_box_layout.addWidget(self.transformation_order_spinbox, 0, 1)
        
        find_transform_button = QPushButton('Find transform')
        find_transform_button.clicked.connect(self.get_transformation)
        transformation_box_layout.addWidget(find_transform_button, 2, 0, 1, 2)
        
        layout.addWidget(transformation_box, 1, 2, 3, 1)
        
        coords_container = roundQGroupBox()
        coords_container.setTitle('Coordinates')
        coords_container_layout = QGridLayout()
        coords_container.setLayout(coords_container_layout)
        
        abs_coordinate_label_x = QLabel('x: ')
        self.abs_coordinate_textbox_x = QtWidgets.QLineEdit() 
        self.abs_coordinate_textbox_x.setValidator(QtGui.QDoubleValidator())
        
        abs_coordinate_label_y = QLabel('y: ')
        self.abs_coordinate_textbox_y = QtWidgets.QLineEdit() 
        self.abs_coordinate_textbox_y.setValidator(QtGui.QDoubleValidator())
        
        img_coordinate_label_x = QLabel('x: ')
        self.img_coordinate_textbox_x = QtWidgets.QLineEdit() 
        self.img_coordinate_textbox_x.setValidator(QtGui.QDoubleValidator())
        
        img_coordinate_label_y = QLabel('y: ')
        self.img_coordinate_textbox_y = QtWidgets.QLineEdit() 
        self.img_coordinate_textbox_y.setValidator(QtGui.QDoubleValidator())
        
        get_crosshair_coords_button = QPushButton('Pick coordinate')
        get_crosshair_coords_button.clicked.connect(self.get_crosshair_coordinates)
        
        save_coords_button = QPushButton('Save coordinates')
        save_coords_button.clicked.connect(self.save_coords)
        
        coords_container_layout.addWidget(QLabel('Absolute coordinates'), 0, 1, 1, 2)
        coords_container_layout.addWidget(abs_coordinate_label_x, 1, 0)
        coords_container_layout.addWidget(self.abs_coordinate_textbox_x, 1, 1)
        coords_container_layout.addWidget(abs_coordinate_label_y, 2, 0)
        coords_container_layout.addWidget(self.abs_coordinate_textbox_y, 2, 1)
        
        coords_container_layout.addWidget(QLabel('Image coordinates'), 0, 4, 1, 1)
        coords_container_layout.addWidget(img_coordinate_label_x, 1, 3)
        coords_container_layout.addWidget(self.img_coordinate_textbox_x, 1, 4)
        coords_container_layout.addWidget(img_coordinate_label_y, 2, 3)
        coords_container_layout.addWidget(self.img_coordinate_textbox_y, 2, 4)
        coords_container_layout.addWidget(get_crosshair_coords_button, 3, 4, 1, 1)
        coords_container_layout.addWidget(save_coords_button, 4, 0, 1, 5)
        
        layout.addWidget(coords_container, 3, 0, 3, 2)
        
        self.found_transformation_container = roundQGroupBox()
        self.found_transformation_container.setTitle('Result')
        found_transformation_container_layout = QGridLayout()
        self.found_transformation_container.setLayout(found_transformation_container_layout)
        self.found_transformation_text = QLabel('No transformation')
        found_transformation_container_layout.addWidget(self.found_transformation_text, 0, 0)
        
        self.devices_dropdown = QComboBox()
        devices = ['DMD: 640', 'DMD: 532', 'DMD: 488', 'Galvos']
        self.devices_dropdown.addItems(devices)
        self.cast_transformation_button = QPushButton('Cast')
        self.cast_transformation_button.clicked.connect(self.cast_transformation)
        
        found_transformation_container_layout.addWidget(QLabel('Cast to:'), 1, 0)
        found_transformation_container_layout.addWidget(self.devices_dropdown, 1, 1)
        found_transformation_container_layout.addWidget(self.cast_transformation_button, 2, 0, 1, 2)
        
        layout.addWidget(self.found_transformation_container, 4, 2, 2, 1)
        self.setMinimumSize(800,1000)
        self.show()
        
    def cast_transformation(self):
        if self.devices_dropdown.currentText() == 'DMD: 640':
            self.sig_cast_transformation_to_DMD.emit(self.transformation, '640')
        elif self.devices_dropdown.currentText() == 'DMD: 532':
            self.sig_cast_transformation_to_DMD.emit(self.transformation, '532')
        elif self.devices_dropdown.currentText() == 'DMD: 488':
            self.sig_cast_transformation_to_DMD.emit(self.transformation, '488')
        elif self.devices_dropdown.currentText() == 'Galvos':
            self.sig_cast_transformation_to_galvos.emit(self.transformation)
        
    def get_crosshair_coordinates(self):
        try:
            self.image_viewer.roi1
        except:
            print('Press in image to set crosshair')
            return
        
        coords = [self.image_viewer.roi1.pos().x(), self.image_viewer.roi1.pos().y()]
        self.img_coordinate_textbox_x.setText("{:.1f}".format(coords[0]))
        self.img_coordinate_textbox_y.setText("{:.1f}".format(coords[1]))
        
    def save_coords(self):
        try:
            self.abs_coords
        except:
            self.abs_coords = []
            self.img_coords = []
            
        coord = self.abs_coordinate_textbox_x.text()
        if coord == '':
            print('No absolute x coordinate')
            return
        else:    
            abscoordx = float(coord)
            self.abs_coordinate_textbox_x.setText('')
            
        coord = self.abs_coordinate_textbox_y.text()
        if coord == '':
                print('No absolute y coordinate')
                return
        else:
            abscoordy = float(coord)
            self.abs_coordinate_textbox_y.setText('')
        
        coord = self.img_coordinate_textbox_x.text()
        if coord == '':
            print('Invalid image x coordinate')
            return
        else:
            imgcoordx = float(coord)
            self.img_coordinate_textbox_x.setText('')
            
        coord = self.img_coordinate_textbox_y.text()
        if coord == '':
            print('Invalid image y coordinate')
            return
        else:
            imgcoordy = float(coord)
            self.img_coordinate_textbox_y.setText('')
        
        self.abs_coords.append([abscoordx, abscoordy])
        self.img_coords.append([imgcoordx, imgcoordy])
        print('Coordinates saved')
        
        try: 
            self.coordinate_counter_int 
        except: 
            self.coordinate_counter_int = 1
        else: 
            self.coordinate_counter_int += 1
            
        self.coordinate_counter.setText('Saved coordinates: '+str(self.coordinate_counter_int))
    
    def create_string_to_print(self, x):
        """

        Parameters
        ----------
        x : Matrix to be transformed to string

        Returns
        -------
        string : String to be printed

        """
        string = '          '
        
        for i in range(x.shape[0]):
            string += '  x^'+str(i) + '        '
        string += '\n'
        
        for i in range(x.shape[0]):    
            for j in range(x.shape[1]):
                if j == 0:
                    string += 'y^'+str(i)+'   '
                string += '|'+"{:.5f}".format(x[i,j])
            string += '| \n'
        return string
    
    def get_transformation(self):
        order = self.transformation_order_spinbox.value()
        self.transformation = CoordinateTransformations.polynomial2DFit(np.asarray(self.img_coords), np.asarray(self.abs_coords), order)
        string_x = self.create_string_to_print(self.transformation[:,:,0])
        string_y = self.create_string_to_print(self.transformation[:,:,1])
        self.found_transformation_text.setText('for x:\n'+string_x+'\n for y:\n'+string_y)
        
    def open_image_file(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select file', './CoordinateManager/',"(*.png *.tiff)")
        self.filename_textbox.setText('File: '+filename.split('/')[-1])
        image = plt.imread(filename)
        self.image_viewer.setImage(image)

class ManualRegistrationWidget(QWidget):
    
    sig_request_camera_image = pyqtSignal()
    
    def __init__(self, parent = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.init_gui()
        
    def init_gui(self):
        self.setFixedSize(325,100)
        
        layout = QGridLayout()
        self.setLayout(layout)
        
        self.box = roundQGroupBox()
        self.box.setTitle('Manual registration')
        box_layout = QGridLayout()
        self.box.setLayout(box_layout)
        
        layout.addWidget(self.box)
        
        self.open_button = QPushButton('Open')
        self.open_button.clicked.connect(self.open_window)
        box_layout.addWidget(self.open_button)
        
        self.show()
        
    def open_window(self):
        self.window = ManualRegistrationWindow()
        self.window.sig_request_camera_image.connect(lambda: self.sig_request_camera_image.emit())
        self.window.sig_cast_transformation_to_DMD.connect(self.parent.cast_transformation_to_DMD)
        self.window.sig_cast_transformation_to_galvos.connect(self.parent.cast_transformation_to_galvos)
    
    def receive_camera_image(self, image):
        self.window.image_viewer.setImage(image)
        print('Image received')
    
if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        mainwin = ManualRegistrationWidget()
        mainwin.show()
        app.exec_()
    run_app()