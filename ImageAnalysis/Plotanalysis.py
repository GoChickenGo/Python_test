# -*- coding: utf-8 -*-
"""
Created on Sun Nov 17 16:11:31 2019

@author: xinmeng
"""
from __future__ import division
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPoint
from PyQt5.QtGui import QColor, QPen, QPixmap, QIcon

from PyQt5.QtWidgets import QWidget, QButtonGroup, QLabel, QSlider, QSpinBox, QDoubleSpinBox, QGridLayout, QPushButton, QGroupBox, QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox, QTabWidget, QCheckBox, QRadioButton, QFileDialog
from IPython import get_ipython
import pyqtgraph as pg
import csv
import sys
import numpy as np
import matplotlib.pyplot as plt
import os

class PlotAnalysisGUI(QWidget):
    
    waveforms_generated = pyqtSignal(object, object, list, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        #------------------------Initiating patchclamp class-------------------
        #----------------------------------------------------------------------
        #----------------------------------GUI---------------------------------
        #----------------------------------------------------------------------
        self.setMinimumSize(200,200)
        self.setWindowTitle("Plot display")
        self.layout = QGridLayout(self)
        
        pmtimageContainer = QGroupBox("Read-in")
        self.pmtimageLayout = QGridLayout()
        
        self.checkboxWaveform = QCheckBox("Waveform")
        self.checkboxWaveform.setStyleSheet('color:CadetBlue;font:bold "Times New Roman"')
        self.checkboxWaveform.setChecked(True)
        self.layout.addWidget(self.checkboxWaveform, 0, 0)  
        
        self.checkboxTrace = QCheckBox("Recorded trace")
        self.checkboxTrace.setStyleSheet('color:CadetBlue;font:bold "Times New Roman"')
        self.layout.addWidget(self.checkboxTrace, 1, 0)  
        
        self.checkboxCam = QCheckBox("Cam trace")
        self.checkboxCam.setStyleSheet('color:CadetBlue;font:bold "Times New Roman"')
        
        self.Spincamsamplingrate = QSpinBox(self)
        self.Spincamsamplingrate.setMaximum(2000)
        self.Spincamsamplingrate.setValue(250)
        self.Spincamsamplingrate.setSingleStep(250)
        self.layout.addWidget(self.Spincamsamplingrate, 2, 2)
        self.layout.addWidget(QLabel("Camera FPS:"), 2, 1)
        
        self.layout.addWidget(self.checkboxCam, 2, 0)  
        
        self.savedirectorytextbox = QtWidgets.QLineEdit(self)
        self.pmtimageLayout.addWidget(self.savedirectorytextbox, 1, 0)
        
#        self.v_directorytextbox = QtWidgets.QLineEdit(self)
#        self.pmtimageLayout.addWidget(self.v_directorytextbox, 2, 0)
            
        self.toolButtonOpenDialog = QtWidgets.QPushButton('Select folder')
#        self.toolButtonOpenDialog.setStyleSheet("QPushButton {color:teal;background-color: pink; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
#                                                "QPushButton:pressed {color:yellow;background-color: pink; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")

        #self.toolButtonOpenDialog.setObjectName("toolButtonOpenDialog")
        self.toolButtonOpenDialog.clicked.connect(self._open_file_dialog)
        
        
#        self.toolButtonOpenDialog_v = QtWidgets.QPushButton('Recorded trace file')
#        #self.toolButtonOpenDialog_v.setObjectName("toolButtonOpenDialog")
#        self.toolButtonOpenDialog_v.clicked.connect(self.getfile_voltage)
        
#        self.cam_directorytextbox = QtWidgets.QLineEdit(self)
#        self.pmtimageLayout.addWidget(self.cam_directorytextbox, 3, 0)
#        self.toolButtonOpenDialog_cam = QtWidgets.QPushButton('Cam trace file')
        #self.toolButtonOpenDialog_cam.setObjectName("toolButtonOpenDialog")
#        self.toolButtonOpenDialog_cam.clicked.connect(self.getfile_cam)
        
        self.pmtimageLayout.addWidget(self.toolButtonOpenDialog, 1, 1)
#        self.pmtimageLayout.addWidget(self.toolButtonOpenDialog_v, 2, 1)
#        self.pmtimageLayout.addWidget(self.toolButtonOpenDialog_cam, 3, 1)
        
        self.toolButtonLoad = QtWidgets.QPushButton('Graph')
        self.toolButtonLoad.setStyleSheet("QPushButton {color:white;background-color: green; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}"
                                                "QPushButton:pressed {color:yellow;background-color: pink; border-style: outset;border-radius: 10px;border-width: 2px;font: bold 14px;padding: 6px}")
        self.toolButtonLoad.clicked.connect(self.show_graphy)        
        self.pmtimageLayout.addWidget(self.toolButtonLoad, 1, 2)

             
        pmtimageContainer.setLayout(self.pmtimageLayout)
        self.layout.addWidget(pmtimageContainer, 3, 0, 1, 3)
        
    def _open_file_dialog(self):
        self.Nest_data_directory = str(QtWidgets.QFileDialog.getExistingDirectory())
        self.savedirectorytextbox.setText(self.Nest_data_directory)
        
#    def getfile(self):
#        self.wave_fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Single File', r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2019-12-10 insert movement testing\Archon_KClassay_15s\2019-12-10_18-06-12__Wavefroms_sr_100.npy')
        
#    def getfile_voltage(self):
#        self.recorded_wave_fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Single File', r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2019-12-06 Perfusion fluorescence test\Novarch2\Vp2019-12-06_17-31-05.npy')
        
#    def getfile_cam(self):# For csv file

                
    def show_graphy(self):
        get_ipython().run_line_magic('matplotlib', 'qt')
        
        self.cam_trace_fluorescence_dictionary = {}
        self.cam_trace_fluorescence_filename_dictionary = {}
        self.region_file_name = []
        
        for file in os.listdir(self.Nest_data_directory):
            if 'Wavefroms_sr_' in file:
                self.wave_fileName = os.path.join(self.Nest_data_directory, file)
            elif file.endswith('csv'): # Quick dirty fix
                self.recorded_cam_fileName = os.path.join(self.Nest_data_directory, file)
                
                self.samplingrate_cam = self.Spincamsamplingrate.value()
                self.cam_trace_time_label = np.array([])
                self.cam_trace_fluorescence_value = np.array([])
                
                with open(self.recorded_cam_fileName, newline='') as csvfile:
                    spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
                    for column in spamreader:
                        coords = column[0].split(",")
                        if coords[0] != 'X': # First row and column is 'x, y'
                            self.cam_trace_time_label = np.append(self.cam_trace_time_label, int(coords[0]))
                            self.cam_trace_fluorescence_value = np.append(self.cam_trace_fluorescence_value, float(coords[1]))
                self.cam_trace_fluorescence_dictionary["region_{0}".format(len(self.region_file_name)+1)] = self.cam_trace_fluorescence_value
                self.cam_trace_fluorescence_filename_dictionary["region_{0}".format(len(self.region_file_name)+1)] = file
                self.region_file_name.append(file)
            elif 'Vp' in file:
                self.recorded_wave_fileName = os.path.join(self.Nest_data_directory, file)

        # Read in configured waveforms
        configwave_wavenpfileName = self.wave_fileName#r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Patch clamp\2019-11-29 patch-perfusion-Archon1\trial-1\perfusion2\2019-11-29_15-51-16__Wavefroms_sr_100.npy'
        temp_loaded_container = np.load(configwave_wavenpfileName, allow_pickle=True)

        Daq_sample_rate = int(float(configwave_wavenpfileName[configwave_wavenpfileName.find('sr_')+3:-4]))
        
        self.Checked_display_list = ['Waveform']
        if self.checkboxTrace.isChecked():
            self.Checked_display_list = np.append(self.Checked_display_list, 'Recorded_trace')
        if self.checkboxCam.isChecked():
            self.Checked_display_list = np.append(self.Checked_display_list, 'Cam_trace')
        
#            Vm_diff = round(np.mean(Vm[100:200]) - np.mean(Vm[-200:-100]), 2)

        reference_length=len(temp_loaded_container[0]['Waveform'])
        xlabel_all = np.arange(reference_length)/Daq_sample_rate
        
        #----------------------------------------------------For patch perfusion---------------------------------------------------------------
        if len(self.region_file_name) == 0:

            #plt.figure()
            if len(self.Checked_display_list) == 2:
                figure, (ax1, ax2) = plt.subplots(2, 1)

            elif len(self.Checked_display_list) == 3:
                figure, (ax1, ax2, ax3) = plt.subplots(3, 1)
                
            for i in range(len(temp_loaded_container)):
                if temp_loaded_container[i]['Sepcification'] == '640AO':
                    pass
#                    ax1.plot(xlabel_all, temp_loaded_container[i]['Waveform'], label='640AO', color='r')
                elif temp_loaded_container[i]['Sepcification'] == '488AO':
                    ax1.plot(xlabel_all, temp_loaded_container[i]['Waveform'], label='488AO', color='b')
                elif temp_loaded_container[i]['Sepcification'] == 'Perfusion_8':
                    ax1.plot(xlabel_all, temp_loaded_container[i]['Waveform'], label='KCL')
                elif temp_loaded_container[i]['Sepcification'] == 'Perfusion_7':
                    ax1.plot(xlabel_all, temp_loaded_container[i]['Waveform'], label='EC')
                elif temp_loaded_container[i]['Sepcification'] == 'Perfusion_2':
                    ax1.plot(xlabel_all, temp_loaded_container[i]['Waveform'], label='Suction')
            ax1.set_title('Output waveforms')        
            ax1.set_xlabel('time(s)')
            ax1.set_ylabel('Volt')
            ax1.legend()
    
            if 'Recorded_trace' in self.Checked_display_list:
        #        plt.yticks(np.round(np.arange(min(Vm), max(Vm), 0.05), 2))      
                # Read in recorded waves
                Readin_fileName = self.recorded_wave_fileName#r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Patch clamp\2019-11-29 patch-perfusion-Archon1\trial-2\Vp2019-11-29_17-31-18.npy'
                
                if 'Vp' in os.path.split(Readin_fileName)[1]: # See which channel is recorded
                    Vm = np.load(Readin_fileName, allow_pickle=True)
                    Vm = Vm[4:-1]# first 5 are sampling rate, Daq coffs
                    Vm[0]=Vm[1]
                
                ax2.set_xlabel('time(s)')        
                ax2.set_title('Recording')
                ax2.set_ylabel('V (Vm*10)')
                ax2.plot(xlabel_all, Vm, label = 'Vm')
                #ax2.annotate('Vm diff = '+str(Vm_diff*100)+'mV', xy=(0, max(Vm)-0.1))        
                ax2.legend()
            elif 'Recorded_trace' not in self.Checked_display_list and len(self.Checked_display_list) == 2:
                ax2.plot(self.cam_trace_time_label/self.samplingrate_cam, self.cam_trace_fluorescence_dictionary["region_{0}".format(region_number+1)], label = 'Fluorescence')
                ax2.set_xlabel('time(s)')        
                ax2.set_title('ROI Fluorescence'+' ('+str(self.cam_trace_fluorescence_filename_dictionary["region_{0}".format(region_number+1)])+')')
                ax2.set_ylabel('CamCounts')
                ax2.legend()
                
            if len(self.Checked_display_list) == 3:
                ax3.plot(self.cam_trace_time_label/self.samplingrate_cam, self.cam_trace_fluorescence_dictionary["region_{0}".format(region_number+1)], label = 'Fluorescence')
                ax3.set_xlabel('time(s)')        
                ax3.set_title('ROI Fluorescence'+' ('+str(self.cam_trace_fluorescence_filename_dictionary["region_{0}".format(region_number+1)])+')')
                ax3.set_ylabel('CamCounts')
                ax3.legend()
            #plt.autoscale(enable=True, axis="y", tight=False)
            figure.tight_layout()
            plt.show()
        #----------------------------------------------------For plots with camera regions-----------------------------------------------------
        if len(self.region_file_name) != 0:
            for region_number in range(len(self.region_file_name)):
                #plt.figure()
                if len(self.Checked_display_list) == 2:
                    figure, (ax1, ax2) = plt.subplots(2, 1)
                    print(1111)
                elif len(self.Checked_display_list) == 3:
                    figure, (ax1, ax2, ax3) = plt.subplots(3, 1)
                    
                for i in range(len(temp_loaded_container)):
                    if temp_loaded_container[i]['Sepcification'] == '640AO':
                        ax1.plot(xlabel_all, temp_loaded_container[i]['Waveform'], label='640AO', color='r')
                    elif temp_loaded_container[i]['Sepcification'] == '488AO':
                        ax1.plot(xlabel_all, temp_loaded_container[i]['Waveform'], label='488AO', color='b')
                    elif temp_loaded_container[i]['Sepcification'] == 'Perfusion_8':
                        ax1.plot(xlabel_all, temp_loaded_container[i]['Waveform'], label='KCL')
                    elif temp_loaded_container[i]['Sepcification'] == 'Perfusion_7':
                        ax1.plot(xlabel_all, temp_loaded_container[i]['Waveform'], label='EC')
                    elif temp_loaded_container[i]['Sepcification'] == 'Perfusion_2':
                        ax1.plot(xlabel_all, temp_loaded_container[i]['Waveform'], label='Suction')
                ax1.set_title('Output waveforms')        
                ax1.set_xlabel('time(s)')
                ax1.set_ylabel('Volt')
                ax1.legend()
        
                if 'Recorded_trace' in self.Checked_display_list:
            #        plt.yticks(np.round(np.arange(min(Vm), max(Vm), 0.05), 2))      
                    # Read in recorded waves
                    Readin_fileName = self.recorded_wave_fileName#r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Patch clamp\2019-11-29 patch-perfusion-Archon1\trial-2\Vp2019-11-29_17-31-18.npy'
                    
                    if 'Vp' in os.path.split(Readin_fileName)[1]: # See which channel is recorded
                        Vm = np.load(Readin_fileName, allow_pickle=True)
                        Vm = Vm[4:-1]# first 5 are sampling rate, Daq coffs
                        Vm[0]=Vm[1]
                    
                    ax2.set_xlabel('time(s)')        
                    ax2.set_title('Recording')
                    ax2.set_ylabel('V (Vm*10)')
                    ax2.plot(xlabel_all, Vm, label = 'Vm')
                    #ax2.annotate('Vm diff = '+str(Vm_diff*100)+'mV', xy=(0, max(Vm)-0.1))        
                    ax2.legend()
                elif 'Recorded_trace' not in self.Checked_display_list and len(self.Checked_display_list) == 2:
                    ax2.plot(self.cam_trace_time_label/self.samplingrate_cam, self.cam_trace_fluorescence_dictionary["region_{0}".format(region_number+1)], label = 'Fluorescence')
                    ax2.set_xlabel('time(s)')        
                    ax2.set_title('ROI Fluorescence'+' ('+str(self.cam_trace_fluorescence_filename_dictionary["region_{0}".format(region_number+1)])+')')
                    ax2.set_ylabel('CamCounts')
                    ax2.legend()
                    
                if len(self.Checked_display_list) == 3:
                    ax3.plot(self.cam_trace_time_label/self.samplingrate_cam, self.cam_trace_fluorescence_dictionary["region_{0}".format(region_number+1)], label = 'Fluorescence')
                    ax3.set_xlabel('time(s)')        
                    ax3.set_title('ROI Fluorescence'+' ('+str(self.cam_trace_fluorescence_filename_dictionary["region_{0}".format(region_number+1)])+')')
                    ax3.set_ylabel('CamCounts')
                    ax3.legend()
                #plt.autoscale(enable=True, axis="y", tight=False)
                figure.tight_layout()
                plt.show()
            #get_ipython().run_line_magic('matplotlib', 'inline')
    
    def closeEvent(self, event):
        get_ipython().run_line_magic('matplotlib', 'inline')

if __name__ == "__main__":
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        pg.setConfigOptions(imageAxisOrder='row-major')
        mainwin = Mainbody()
        mainwin.show()
        app.exec_()
    run_app()