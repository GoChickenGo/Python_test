# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 12:21:01 2019

@author: lhuismans

Notes:
    
"""
import nidaqmx
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx.stream_writers import AnalogSingleChannelWriter
from nidaqmx.constants import AcquisitionType, TaskMode
from nidaqmx.stream_writers import AnalogMultiChannelWriter, DigitalMultiChannelWriter
from nidaqmx.stream_readers import AnalogSingleChannelReader
from PyQt5.QtCore import pyqtSignal, QThread

import sys
sys.path.append('../')

import numpy as np
import NIDAQ.wavegenerator
from NIDAQ.configuration import Configuration
from NIDAQ.wavegenerator import blockWave
from NIDAQ.constants import MeasurementConstants

class pmtimaging_continuous_Thread(QThread):
    measurement = pyqtSignal(np.ndarray) #The signal for the measurement, we can connect to this signal
    def __init__(self, wave, sampleRate, readNumber, averagenumber, ScanArrayXnum, *args, **kwargs):
        """
        wave is the output data
        sampleRate is the sampleRate of the DAQ
        readNumber is the 
        """
        super().__init__(*args, **kwargs)
        
        self.sampleRate = sampleRate
        self.readNumber = readNumber
        self.averagenumber = averagenumber
        self.ScanArrayXnum = int(ScanArrayXnum)
        self.ypixelnumber = int((self.readNumber/self.averagenumber)/self.ScanArrayXnum)
        
        self.wave = wave
        
        self.configs = Configuration()
            
    def run(self):
        """
        Starts writing a waveform continuously while reading 
        the buffer periodically
        """
        
        #DAQ
        with nidaqmx.Task() as slave_Task3, nidaqmx.Task() as master_Task:
            #slave_Task3 = nidaqmx.Task()
            slave_Task3.ao_channels.add_ao_voltage_chan("/Dev1/ao0:1")
            master_Task.ai_channels.add_ai_voltage_chan("/Dev1/ai0")
            
            slave_Task3.timing.cfg_samp_clk_timing(rate = self.sampleRate, source='ai/SampleClock',
                                                   sample_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS)
                                                 
            
            # Analoginput
            master_Task.timing.cfg_samp_clk_timing(rate = self.sampleRate,
                                                   sample_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                                   samps_per_chan = self.readNumber)
            
            reader = AnalogSingleChannelReader(master_Task.in_stream)
            writer = AnalogMultiChannelWriter(slave_Task3.out_stream)
            
            reader.auto_start = False
            writer.auto_start = False
            
            writer.write_many_sample(self.wave)
            
            """Reading data from the buffer in a loop. 
            The idea is to let the task read more than could be loaded in the buffer for each iteration.
            This way the task will have to wait slightly longer for incoming samples. And leaves the buffer
            entirely clean. This way we always know the correct numpy size and are always left with an empty
            buffer (and the buffer will not slowly fill up)."""
            output = np.zeros(self.readNumber)
            slave_Task3.start() #Will wait for the readtask to start so it can use its clock
            master_Task.start()
            while not self.isInterruptionRequested():
                reader.read_many_sample(data = output, 
                                        number_of_samples_per_channel = self.readNumber)
                
                #Emiting the data just received as a signal

                Dataholder_average = np.mean(output.reshape(self.averagenumber, -1), axis=0)
                
                self.data_PMT = np.reshape(Dataholder_average, (self.ypixelnumber, self.ScanArrayXnum))
                
                if self.ypixelnumber == 500:
                    self.data_PMT= self.data_PMT[:, 50:550]*-1
                elif self.ypixelnumber == 256:
                    self.data_PMT= self.data_PMT[:, 70:326]*-1
                    
                self.measurement.emit(self.data_PMT)    
          
class pmtimagingTest:

    def __init__(self):
        """Initiate all the values."""
    
    def setWave(self, Daq_sample_rate, Value_voltXMin, Value_voltXMax, Value_voltYMin, Value_voltYMax, Value_xPixels, Value_yPixels, averagenum):
        
        
        self.Daq_sample_rate = Daq_sample_rate
        self.averagenum = averagenum
        
        self.Galvo_samples_offset = 0
        self.offsetsamples_galvo = []
    
        #Generate galvo samples            
        self.samples_1, self.samples_2= NIDAQ.wavegenerator.waveRecPic(sampleRate = self.Daq_sample_rate, imAngle = 0, voltXMin = Value_voltXMin, voltXMax = Value_voltXMax, 
                         voltYMin = Value_voltYMin, voltYMax = Value_voltYMax, xPixels = Value_xPixels, yPixels = Value_yPixels, 
                         sawtooth = True)
        #ScanArrayX = wavegenerator.xValuesSingleSawtooth(sampleRate = Daq_sample_rate, voltXMin = Value_voltXMin, voltXMax = Value_voltXMax, xPixels = Value_xPixels, sawtooth = True)
        self.Totalscansamples = len(self.samples_1)*self.averagenum # Calculate number of samples to feed to scanner, by default it's one frame 
        self.ScanArrayXnum = int (len(self.samples_1)/Value_yPixels) # number of samples of each individual line of x scanning
        #print(self.ScanArrayXnum)
        #print(self.Digital_container_feeder[:, 0])
        
        self.repeated_samples_1 = np.tile(self.samples_1, self.averagenum)
        self.repeated_samples_2_yaxis = np.tile(self.samples_2, self.averagenum)
        
        self.Galvo_samples = np.vstack((self.repeated_samples_1,self.repeated_samples_2_yaxis))

        self.pmtimagingThread = pmtimaging_continuous_Thread(self.Galvo_samples, self.Daq_sample_rate, self.Totalscansamples, self.averagenum, self.ScanArrayXnum)
        #self.pmtimagingThread.wave = self.Galvo_samples
        return self.Totalscansamples
    
    def setWave_contourscan(self, Daq_sample_rate, contour_samples, contour_point_number):
                
        self.Daq_sample_rate = Daq_sample_rate
        contour_point_number = contour_point_number
        self.pmtimagingThread = pmtimaging_continuous_Thread_contour(contour_samples, self.Daq_sample_rate, contour_point_number, 1, 1)
        #self.pmtimagingThread.wave = self.Galvo_samples
        
    def start(self):
        self.pmtimagingThread.start() #Start executing what is inside run()
    
    def aboutToQuitHandler(self):
        self.pmtimagingThread.requestInterruption()
        self.pmtimagingThread.wait()
        
class pmtimaging_continuous_Thread_contour(QThread):
    measurement = pyqtSignal(np.ndarray) #The signal for the measurement, we can connect to this signal
    def __init__(self, wave, sampleRate, readNumber, averagenumber, ScanArrayXnum, *args, **kwargs):
        """
        wave is the output data
        sampleRate is the sampleRate of the DAQ
        readNumber is the 
        """
        super().__init__(*args, **kwargs)
        
        self.sampleRate = sampleRate
        self.readNumber = readNumber
        self.averagenumber = averagenumber
        self.ScanArrayXnum = int(ScanArrayXnum)
        self.ypixelnumber = int((self.readNumber/self.averagenumber)/self.ScanArrayXnum)
        
        self.wave = wave
        
        self.configs = Configuration()
            
    def run(self):
        """
        Starts writing a waveform continuously while reading 
        the buffer periodically
        """
        
        #DAQ
        with nidaqmx.Task() as slave_Task3, nidaqmx.Task() as master_Task:
            #slave_Task3 = nidaqmx.Task()
            slave_Task3.ao_channels.add_ao_voltage_chan("/Dev1/ao0:1")
            master_Task.ai_channels.add_ai_voltage_chan("/Dev1/ai0")
            
            slave_Task3.timing.cfg_samp_clk_timing(rate = self.sampleRate, source='ai/SampleClock',
                                                   sample_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS)
                                                 
            
            # Analoginput
            master_Task.timing.cfg_samp_clk_timing(rate = self.sampleRate,
                                                   sample_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                                   samps_per_chan = self.readNumber)
            
            reader = AnalogSingleChannelReader(master_Task.in_stream)
            writer = AnalogMultiChannelWriter(slave_Task3.out_stream)
            
            reader.auto_start = False
            writer.auto_start = False
            
            writer.write_many_sample(self.wave)
            
            """Reading data from the buffer in a loop. 
            The idea is to let the task read more than could be loaded in the buffer for each iteration.
            This way the task will have to wait slightly longer for incoming samples. And leaves the buffer
            entirely clean. This way we always know the correct numpy size and are always left with an empty
            buffer (and the buffer will not slowly fill up)."""
            output = np.zeros(self.readNumber)
            slave_Task3.start() #Will wait for the readtask to start so it can use its clock
            master_Task.start()
            print('Contour scanning!!')
            while not self.isInterruptionRequested():
                reader.read_many_sample(data = output, 
                                        number_of_samples_per_channel = self.readNumber)
                
                #Emiting the data just received as a signal

                Dataholder_average = np.mean(output.reshape(self.averagenumber, -1), axis=0)
                
                self.data_PMT = np.reshape(Dataholder_average, (self.ypixelnumber, self.ScanArrayXnum))
                        
                self.data_PMT= self.data_PMT*-1
                #self.measurement.emit(self.data_PMT)  
                
class pmtimagingTest_contour:

    def __init__(self):
        """Initiate all the values."""
    
    def setWave_contourscan(self, Daq_sample_rate, contour_samples, contour_point_number):
                
        self.Daq_sample_rate = Daq_sample_rate
        contour_point_number = contour_point_number
        self.pmtimagingThread_contour = pmtimaging_continuous_Thread_contour(contour_samples, self.Daq_sample_rate, contour_point_number, 1, 1)
        #self.pmtimagingThread.wave = self.Galvo_samples
        
    def start(self):
        self.pmtimagingThread_contour.start() #Start executing what is inside run()
    
    def aboutToQuitHandler(self):
        self.pmtimagingThread_contour.requestInterruption()
        self.pmtimagingThread_contour.wait()
        print('Contour scan stopped!!')