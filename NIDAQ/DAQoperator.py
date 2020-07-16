# -*- coding: utf-8 -*-
"""
Created on Fri May 29 15:29:22 2020

@author: xinmeng
"""
"""
READIN TASK HAS TO START AHEAD OF READ MANY SAMPLES, OTHERWISE ITS NOT in SYN!!!
"""
# The adaptive NI DAQ tool

#import time
import nidaqmx
import numpy as np
from nidaqmx.constants import AcquisitionType, TaskMode, LineGrouping, Signal
from nidaqmx.stream_writers import AnalogMultiChannelWriter, DigitalMultiChannelWriter, DigitalSingleChannelWriter
from nidaqmx.stream_readers import AnalogSingleChannelReader, AnalogMultiChannelReader
from datetime import datetime
import os
from PyQt5.QtCore import pyqtSignal
from NIDAQ.configuration import Configuration

class DAQmission: # For all-purpose Nidaq tasks, use "Dev1/ai22" as reference channel.
    """
    # For all-purpose Nidaq tasks. Use "Dev1/ai22" as reference channel.
    # 'Sepcification' is the wrong spelling of 'Specification'. 
    """
    collected_data = pyqtSignal(np.ndarray)
    finishSignal = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configs = Configuration()
        self.configdictionary = {'galvosx':'Dev1/ao0',#self.configs.galvoXChannel,
                                 'galvosy':'Dev1/ao1',#self.configs.galvoYChannel, 
                                 '640AO':'Dev1/ao3',
                                 '488AO':'Dev2/ao1',
                                 '532AO':'Dev2/ao0',
                                 'patchAO':'Dev2/ao2',
                                 'cameratrigger':"Dev1/port0/line25",
                                 'galvotrigger':"Dev1/port0/line25",
                                 'blankingall':"Dev1/port0/line4",
                                 '640blanking':"Dev1/port0/line4",
                                 '532blanking':"Dev1/port0/line6",
                                 '488blanking':"Dev1/port0/line3",
                                 'PMT':"Dev1/ai0",
                                 'Vp':"Dev1/ai22",
                                 'Ip':"Dev1/ai20",
                                 #'Perfusion_8':"Dev1/port0/line19",#line21 is perfusion_8, set to 19-LED for test
                                 'LED':"Dev1/port0/line19",
                                 'Perfusion_7':"Dev1/port0/line22",
                                 'Perfusion_6':"Dev1/port0/line23",
                                 'Perfusion_2':"Dev1/port0/line24",
                                 '2Pshutter':"Dev1/port0/line18",
                                 'servo_power':"Dev1/port0/line15",
                                 'servo_modulation':"Dev1/port0/line14"
                                }
        
    def sendSingleAnalog(self, channel, value):
        """
        Write one single digital signal 
        """
        self.channelname = self.configdictionary[channel]
        self.writting_value = value

        # Assume that dev1 is always employed
        with nidaqmx.Task() as writingtask:
            writingtask.ao_channels.add_ao_voltage_chan(self.channelname)
            writingtask.write(self.writting_value)
            
    def sendSingleDigital(self, channel, value):
        """
        Write one single analog signal 
        """
        self.channelname = self.configdictionary[channel]
        if value == True:
            writting_value = np.array([1], dtype = bool)
        else:
            writting_value = np.array([0], dtype = bool)
        
        with nidaqmx.Task() as writingtask:
            writingtask.do_channels.add_do_chan(self.channelname)
            writingtask.write(writting_value)

            
    def runWaveforms(self, clock_source, sampling_rate, analog_signals, digital_signals, readin_channels):
        """
        Input:
          - samplingrate:
              Sampling rate of the waveforms.
              
          - analogsignals:
              Signals for the analog channels.
              It's a structured array with two fields: 
              1) 'Waveform': Raw 1-D np.array of actual float voltage signals.
              2) 'Sepcification': string telling which device to control that help to specify the NI-daq port, check self.configdictionary.
              
              Multiple waveforms should be stack on top of each other using np.stack.
              
              if empty, input can be a blank {}.
              
           -digitalsignals:
              Signals for the digital channels.
              It's a structured array with two fields: 1) 'Waveform': Raw 1-D np.array of type bool.
                                                       2) 'Sepcification': string that specifies the NI-daq port.
                                                          for example: dtype = np.dtype([('Waveform', float, (self.reference_length,)), ('Sepcification', 'U20')])
           -readinchannels:
              A list that contains the readin channels wanted. 
        """
        self.analogsignals = analog_signals
        self.digitalsignals = digital_signals
        self.readinchannels=readin_channels
        self.Daq_sample_rate = sampling_rate
        
        # =============================================================================
        #         Setting up waveforms
        # =============================================================================
        
        #----------------------------------------------------------------------
        # galvosx and galvosy as specification key words are already enough.        
        
        # Get the average number and y pixel number information from data
        self.averagenumber = 0
        self.ypixelnumber = 0
        self.galvosx_originalkey = 'galvosx'
        self.galvosy_originalkey = 'galvosy'
        
        for i in range(len(self.analogsignals['Sepcification'])):
            if 'galvosxavgnum' in self.analogsignals['Sepcification'][i]:
                self.averagenumber = int(self.analogsignals['Sepcification'][i][self.analogsignals['Sepcification'][i].index('_')+1:len(self.analogsignals['Sepcification'][i])])
                self.galvosx_originalkey = self.analogsignals['Sepcification'][i]
                self.analogsignals['Sepcification'][i] = 'galvosx'
            elif 'galvosyypixels' in self.analogsignals['Sepcification'][i]:
                self.ypixelnumber = int(self.analogsignals['Sepcification'][i][self.analogsignals['Sepcification'][i].index('_')+1:len(self.analogsignals['Sepcification'][i])])
                self.galvosy_originalkey = self.analogsignals['Sepcification'][i]
                self.analogsignals['Sepcification'][i] = 'galvosy'
            elif 'galvos_X_contour' in self.analogsignals['Sepcification'][i]:
                self.galvosx_originalkey = self.analogsignals['Sepcification'][i]
                self.analogsignals['Sepcification'][i] = 'galvosx'
            elif 'galvos_Y_contour' in self.analogsignals['Sepcification'][i]:
                self.galvosy_originalkey = self.analogsignals['Sepcification'][i]
                self.analogsignals['Sepcification'][i] = 'galvosy'
        #----------------------------------------------------------------------
        
        # Devide samples from Dev1 or 2
        self.analogwritesamplesdev1_Sepcification = []
        self.analogwritesamplesdev2_Sepcification = []
        
        self.analogwritesamplesdev1 = []
        self.analogwritesamplesdev2 = []
        
        if len(self.analogsignals['Waveform']) != 0:
            num_rows, num_cols = self.analogsignals['Waveform'].shape
            for i in range(int(num_rows)):
                if 'Dev1' in self.configdictionary[self.analogsignals['Sepcification'][i]]:
                    self.analogwritesamplesdev1_Sepcification.append(self.configdictionary[self.analogsignals['Sepcification'][i]])
                    self.analogwritesamplesdev1.append(self.analogsignals['Waveform'][i])
                else:
                    self.analogwritesamplesdev2_Sepcification.append(self.configdictionary[self.analogsignals['Sepcification'][i]])
                    self.analogwritesamplesdev2.append(self.analogsignals['Waveform'][i])
                
        self.analogsignal_dev1_number = len(self.analogwritesamplesdev1_Sepcification)
        self.analogsignal_dev2_number = len(self.analogwritesamplesdev2_Sepcification)
        
        self.analogsignalslinenumber = len(self.analogsignals)
        self.digitalsignalslinenumber = len(self.digitalsignals)
        
        # See if only digital signal is involved.
        if self.analogsignalslinenumber == 0 and self.digitalsignalslinenumber != 0:
            self.OnlyDigitalSignal = True
        else:
            self.OnlyDigitalSignal = False
            
        # See if Dev1 is involved.
        if self.analogsignal_dev1_number != 0:
            self.Dev1AnalogInvolved = True
        elif self.analogsignal_dev1_number == 0:
            self.Dev1AnalogInvolved = False
            
        if self.OnlyDigitalSignal == True:
            self.OnlyDigitalInvolved = True
        elif self.OnlyDigitalSignal == False:
            self.OnlyDigitalInvolved = False
            
        if self.analogsignal_dev2_number != 0:
            self.OnlyDev2AnalogInvolved = True
        elif self.analogsignal_dev2_number == 0:
            self.OnlyDev2AnalogInvolved = False
            
        # some preparations for analog lines
        if self.OnlyDigitalSignal == False:
            self.Totalscansamplesnumber = len(self.analogsignals['Waveform'][0])
            num_rows, num_cols = self.analogsignals['Waveform'].shape
            print("row number of analog signals:  "+str(num_rows))
        elif self.OnlyDigitalSignal == True:
            self.Totalscansamplesnumber = len(self.digitalsignals['Waveform'][0])  
        # Stack the Analog samples of dev1 and dev2 individually
        # IN CASE OF ONLY ONE ARRAY, WE NEED TO CONVERT THE SHAPE TO (1,N) BY USING np.array([]) OUTSIDE THE ARRAY!!
        #------------------------------------------!!_________________________
        if self.analogsignal_dev1_number == 1:            
            self.writesamples_dev1 = np.array([self.analogwritesamplesdev1[0]])

        elif self.analogsignal_dev1_number == 0:
            self.writesamples_dev1 = []
        else:
            self.writesamples_dev1 = self.analogwritesamplesdev1[0]    
            for i in range(1, self.analogsignal_dev1_number):
                self.writesamples_dev1 = np.vstack((self.writesamples_dev1, self.analogwritesamplesdev1[i]))
                
        if self.analogsignal_dev2_number == 1:
            self.writesamples_dev2 = np.array([self.analogwritesamplesdev2[0]])
        elif self.analogsignal_dev2_number == 0:
            self.writesamples_dev2 = []    
        else:
            self.writesamples_dev2 = self.analogwritesamplesdev2[0]
            for i in range(1, self.analogsignal_dev2_number):
                self.writesamples_dev2 = np.vstack((self.writesamples_dev2, self.analogwritesamplesdev2[i]))
        
        # Stack the digital samples        
        if self.digitalsignalslinenumber == 1:
            self.writesamples_digital = np.array([self.digitalsignals['Waveform'][0]])

        elif self.digitalsignalslinenumber == 0:
            self.writesamples_digital = []
        else:
            self.writesamples_digital = self.digitalsignals['Waveform'][0]
            for i in range(1, self.digitalsignalslinenumber):
                self.writesamples_digital = np.vstack((self.writesamples_digital, self.digitalsignals['Waveform'][i]))
        

        # Set the dtype of digital signals
        # The same as (0b1 << n)
        self.writesamples_digital = np.array(self.writesamples_digital, dtype = 'uint32')        
        for i in range(self.digitalsignalslinenumber):
            convernum = int(self.configdictionary[self.digitalsignals['Sepcification'][i]]
                            [self.configdictionary[self.digitalsignals['Sepcification'][i]].index('line')+
                             4:len(self.configdictionary[self.digitalsignals['Sepcification'][i]])])
            self.writesamples_digital[i] = self.writesamples_digital[i]*(2**(convernum))
            
        # For example, to send commands to line 0 and line 3, you hava to write 1001 to digital port, convert to uint32 that is 9.
        if self.digitalsignalslinenumber > 1:
           self.writesamples_digital = np.sum(self.writesamples_digital, axis = 0) # sum along the columns, for multiple lines
           self.writesamples_digital = np.array([self.writesamples_digital]) # here convert the shape from (n,) to (1,n)
           
                 
        if len(self.readinchannels) != 0:
            self.if_theres_readin_channel = True
        else:
            self.if_theres_readin_channel = False
            
        if self.if_theres_readin_channel == True:
            self.Dataholder = np.zeros((len(self.readinchannels), self.Totalscansamplesnumber))
        else:
            self.Dataholder = np.zeros((1, self.Totalscansamplesnumber))
        #-------------------------------------------------------------------------------------------------------------
        
        # =============================================================================
        #         Configure DAQ channels and execute waveforms
        # =============================================================================
        if clock_source == "DAQ": # If NI-DAQ is set as master clock source
            
            """
            # =============================================================================
            #         Analog signal in Dev 1 is involved
            # =============================================================================
            """
            if self.Dev1AnalogInvolved == True:
                with nidaqmx.Task() as slave_Task_1_analog_dev1, nidaqmx.Task() as slave_Task_1_analog_dev2, nidaqmx.Task() as master_Task_readin, nidaqmx.Task() as slave_Task_2_digitallines:
                    # adding channels      
                    # Set tasks from different devices apart
                    for i in range(self.analogsignal_dev1_number):
                        slave_Task_1_analog_dev1.ao_channels.add_ao_voltage_chan(self.analogwritesamplesdev1_Sepcification[i])
        
                    slave_Task_2_digitallines.do_channels.add_do_chan("/Dev1/port0", line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        
                    if self.if_theres_readin_channel == True:
                        self.Dataholder = np.zeros((len(self.readinchannels), self.Totalscansamplesnumber))
                    else:
                        self.Dataholder = np.zeros((1, self.Totalscansamplesnumber))
                        master_Task_readin.ai_channels.add_ai_voltage_chan(self.configdictionary['Vp']) # If no read-in channel is added, vp channel is added to keep code alive.
                        
        #            print(self.Dataholder.shape)
                    if 'PMT' in self.readinchannels:
                        master_Task_readin.ai_channels.add_ai_voltage_chan(self.configdictionary['PMT'])
                    if 'Vp' in self.readinchannels:
                        master_Task_readin.ai_channels.add_ai_voltage_chan(self.configdictionary['Vp'])
                    if 'Ip' in self.readinchannels:
                        master_Task_readin.ai_channels.add_ai_current_chan(self.configdictionary['Ip'])
                    
                    #get scaling coefficients
                    self.aichannelnames=master_Task_readin.ai_channels.channel_names
        
                    self.ai_dev_scaling_coeff_vp = []
                    self.ai_dev_scaling_coeff_ip = []
                    if "Vp" in self.readinchannels:
                        self.ai_dev_scaling_coeff_vp = nidaqmx._task_modules.channels.ai_channel.AIChannel(master_Task_readin._handle, self.configdictionary['Vp'])
                        #https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z0000019TuoSAE&l=nl-NL
                        #self.ai_dev_scaling_coeff.ai_dev_scaling_coeff
                        self.ai_dev_scaling_coeff_vp = np.array(self.ai_dev_scaling_coeff_vp.ai_dev_scaling_coeff)
                        
                    if "Ip" in self.readinchannels:
                        self.ai_dev_scaling_coeff_ip = nidaqmx._task_modules.channels.ai_channel.AIChannel(master_Task_readin._handle, self.configdictionary['Ip'])
                        #https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z0000019TuoSAE&l=nl-NL
                        #self.ai_dev_scaling_coeff.ai_dev_scaling_coeff
                        self.ai_dev_scaling_coeff_ip = np.array(self.ai_dev_scaling_coeff_ip.ai_dev_scaling_coeff)           
                    
                    self.ai_dev_scaling_coeff_list = np.append(self.ai_dev_scaling_coeff_vp, self.ai_dev_scaling_coeff_ip)
                    
                    # setting clock
                    # Analog clock  USE clock on Dev1 as center clock
                    slave_Task_1_analog_dev1.timing.cfg_samp_clk_timing(self.Daq_sample_rate, source='ai/SampleClock', sample_mode= AcquisitionType.FINITE, samps_per_chan=self.Totalscansamplesnumber)
                    master_Task_readin.timing.cfg_samp_clk_timing(self.Daq_sample_rate, sample_mode= AcquisitionType.FINITE, samps_per_chan=self.Totalscansamplesnumber)

                    master_Task_readin.export_signals.samp_clk_output_term = self.configs.clock1Channel#'/Dev1/PFI1'#
                    master_Task_readin.export_signals.start_trig_output_term = self.configs.trigger1Channel#'/Dev1/PFI2'
                    
                    if self.analogsignal_dev2_number != 0:
                        # By default assume that read master task is in dev1
                        
                        for i in range(self.analogsignal_dev2_number):
                            slave_Task_1_analog_dev2.ao_channels.add_ao_voltage_chan(self.analogwritesamplesdev2_Sepcification[i])
                        
                        dev2Clock = self.configs.clock2Channel#/Dev2/PFI1
                        slave_Task_1_analog_dev2.timing.cfg_samp_clk_timing(self.Daq_sample_rate, source=dev2Clock, sample_mode= AcquisitionType.FINITE, samps_per_chan=self.Totalscansamplesnumber)
                        
                        AnalogWriter = nidaqmx.stream_writers.AnalogMultiChannelWriter(slave_Task_1_analog_dev1.out_stream, auto_start= False)
                        AnalogWriter.auto_start = False
                        
                        AnalogWriter_dev2 = nidaqmx.stream_writers.AnalogMultiChannelWriter(slave_Task_1_analog_dev2.out_stream, auto_start= False)
                        AnalogWriter_dev2.auto_start = False
                    
                    # Digital clock
                    if len(self.digitalsignals['Sepcification']) != 0:
                        slave_Task_2_digitallines.timing.cfg_samp_clk_timing(self.Daq_sample_rate, source='ai/SampleClock', sample_mode= AcquisitionType.FINITE, samps_per_chan=self.Totalscansamplesnumber)
                        #slave_Task_2_digitallines.triggers.sync_type.SLAVE = True
                    
        
                	# Configure the writer and reader
                    AnalogWriter = nidaqmx.stream_writers.AnalogMultiChannelWriter(slave_Task_1_analog_dev1.out_stream, auto_start= False)
                    AnalogWriter.auto_start = False
                    if len(self.digitalsignals['Sepcification']) != 0:
                        DigitalWriter = nidaqmx.stream_writers.DigitalMultiChannelWriter(slave_Task_2_digitallines.out_stream, auto_start= False)
                        DigitalWriter.auto_start = False
                    reader = AnalogMultiChannelReader(master_Task_readin.in_stream)        
                    reader.auto_start = False
                    # ---------------------------------------------------------------------------------------------------------------------
                    #-----------------------------------------------------Begin to execute in DAQ------------------------------------------
                    AnalogWriter.write_many_sample(self.writesamples_dev1, timeout = 605.0)
                    
                    if self.analogsignal_dev2_number != 0:
                        AnalogWriter_dev2.write_many_sample(self.writesamples_dev2, timeout = 605.0)
                        
                    if self.digitalsignalslinenumber != 0:     
                        DigitalWriter.write_many_sample_port_uint32(self.writesamples_digital, timeout = 605.0)
                                   
                    print('^^^^^^^^^^^^^^^^^^Daq tasks start^^^^^^^^^^^^^^^^^^')
                    if self.analogsignal_dev2_number != 0:
                        slave_Task_1_analog_dev2.start()            
                    slave_Task_1_analog_dev1.start()
                    
                    if self.digitalsignalslinenumber != 0:
                        slave_Task_2_digitallines.start()
                        
                    master_Task_readin.start() #!!!!!!!!!!!!!!!!!!!! READIN TASK HAS TO START AHEAD OF READ MANY SAMPLES, OTHERWISE ITS NOT SYN!!!
                    
                    reader.read_many_sample(data = self.Dataholder, number_of_samples_per_channel =  self.Totalscansamplesnumber, timeout=605.0)            
                    #self.data_PMT = []
                    
                    slave_Task_1_analog_dev1.wait_until_done()
                    if self.analogsignal_dev2_number != 0:
                        slave_Task_1_analog_dev2.wait_until_done()
                    if self.digitalsignalslinenumber != 0:
                        slave_Task_2_digitallines.wait_until_done()                
                    master_Task_readin.wait_until_done()
                    
        #            if 'PMT' in self.readinchannels:
        #                Dataholder_average = np.mean(self.Dataholder[0,:].reshape(self.averagenumber, -1), axis=0)
        #                
        #                self.ScanArrayXnum = int ((self.Totalscansamplesnumber/self.averagenumber)/self.ypixelnumber)
        #                self.data_PMT = np.reshape(Dataholder_average, (self.ypixelnumber, self.ScanArrayXnum))
        #                
        #                self.data_PMT= self.data_PMT*-1
        
                    slave_Task_1_analog_dev1.stop()
                    if self.analogsignal_dev2_number != 0:
                        slave_Task_1_analog_dev2.stop()
                    if self.digitalsignalslinenumber != 0:
                        slave_Task_2_digitallines.stop()
                    master_Task_readin.stop()
                    
                    if self.if_theres_readin_channel == True:
                        self.collected_data.emit(self.Dataholder)
                    self.finishSignal.emit()
                    print('^^^^^^^^^^^^^^^^^^Daq tasks finish^^^^^^^^^^^^^^^^^^')
                    
                    
                # set the keys of galvos back for next round
                for i in range(len(self.analogsignals['Sepcification'])):
                    if 'galvosx' in self.analogsignals['Sepcification'][i]:
                        self.analogsignals['Sepcification'][i] = self.galvosx_originalkey
                    elif 'galvosy' in self.analogsignals['Sepcification'][i]:
                        self.analogsignals['Sepcification'][i] = self.galvosy_originalkey
            
                """
                # =============================================================================
                #         Only Dev 2 is involved  in sending analog signals
                # =============================================================================
                """
            elif self.OnlyDev2AnalogInvolved == True:
                
                with nidaqmx.Task() as slave_Task_1_analog_dev2, nidaqmx.Task() as master_Task_readin, nidaqmx.Task() as slave_Task_2_digitallines:
                    # adding channels      
                    # Set tasks from different devices apart
                    slave_Task_2_digitallines.do_channels.add_do_chan("/Dev1/port0", line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        
                    if self.if_theres_readin_channel == True:
                        self.Dataholder = np.zeros((len(self.readinchannels), self.Totalscansamplesnumber))
                    else:
                        self.Dataholder = np.zeros((1, self.Totalscansamplesnumber))
                        master_Task_readin.ai_channels.add_ai_voltage_chan(self.configdictionary['Vp']) # If no read-in channel is added, vp channel is added to keep code alive.
                        
        #            print(self.Dataholder.shape)
                    if 'PMT' in self.readinchannels:
                        master_Task_readin.ai_channels.add_ai_voltage_chan(self.configdictionary['PMT'])
                    if 'Vp' in self.readinchannels:
                        master_Task_readin.ai_channels.add_ai_voltage_chan(self.configdictionary['Vp'])
                    if 'Ip' in self.readinchannels:
                        master_Task_readin.ai_channels.add_ai_current_chan(self.configdictionary['Ip'])
                    
                    #get scaling coefficients
                    self.aichannelnames=master_Task_readin.ai_channels.channel_names
        
                    self.ai_dev_scaling_coeff_vp = []
                    self.ai_dev_scaling_coeff_ip = []
                    if "Vp" in self.readinchannels:
                        self.ai_dev_scaling_coeff_vp = nidaqmx._task_modules.channels.ai_channel.AIChannel(master_Task_readin._handle, self.configdictionary['Vp'])
                        #self.ai_dev_scaling_coeff.ai_dev_scaling_coeff
                        self.ai_dev_scaling_coeff_vp = np.array(self.ai_dev_scaling_coeff_vp.ai_dev_scaling_coeff)
                        
                    if "Ip" in self.readinchannels:
                        self.ai_dev_scaling_coeff_ip = nidaqmx._task_modules.channels.ai_channel.AIChannel(master_Task_readin._handle, self.configdictionary['Ip'])
                        #self.ai_dev_scaling_coeff.ai_dev_scaling_coeff
                        self.ai_dev_scaling_coeff_ip = np.array(self.ai_dev_scaling_coeff_ip.ai_dev_scaling_coeff)           
                    
                    self.ai_dev_scaling_coeff_list = np.append(self.ai_dev_scaling_coeff_vp, self.ai_dev_scaling_coeff_ip)
                    
                    # setting clock
                    master_Task_readin.timing.cfg_samp_clk_timing(self.Daq_sample_rate, sample_mode= AcquisitionType.FINITE, samps_per_chan=self.Totalscansamplesnumber)
    
                    master_Task_readin.export_signals.samp_clk_output_term = self.configs.clock1Channel#'/Dev1/PFI1'#
                    master_Task_readin.export_signals.start_trig_output_term = self.configs.trigger1Channel#'/Dev1/PFI2'
                    
                    if self.analogsignal_dev2_number != 0:
                        # By default assume that read master task is in dev1
                        
                        for i in range(self.analogsignal_dev2_number):
                            slave_Task_1_analog_dev2.ao_channels.add_ao_voltage_chan(self.analogwritesamplesdev2_Sepcification[i])
                        
                        dev2Clock = self.configs.clock2Channel#/Dev2/PFI1
                        slave_Task_1_analog_dev2.timing.cfg_samp_clk_timing(self.Daq_sample_rate, source=dev2Clock, sample_mode= AcquisitionType.FINITE, samps_per_chan=self.Totalscansamplesnumber)
                        
                        AnalogWriter_dev2 = nidaqmx.stream_writers.AnalogMultiChannelWriter(slave_Task_1_analog_dev2.out_stream, auto_start= False)
                        AnalogWriter_dev2.auto_start = False
                    
                    # Digital clock
                    if len(self.digitalsignals['Sepcification']) != 0: 
                        slave_Task_2_digitallines.timing.cfg_samp_clk_timing(self.Daq_sample_rate, source='ai/SampleClock', sample_mode= AcquisitionType.FINITE, samps_per_chan=self.Totalscansamplesnumber)
                    
                	# Configure the writer and reader
    
                    if len(self.digitalsignals['Sepcification']) != 0:
                        DigitalWriter = nidaqmx.stream_writers.DigitalMultiChannelWriter(slave_Task_2_digitallines.out_stream, auto_start= False)
                        DigitalWriter.auto_start = False
                    reader = AnalogMultiChannelReader(master_Task_readin.in_stream)        
                    reader.auto_start = False
                    # ---------------------------------------------------------------------------------------------------------------------
                    #-----------------------------------------------------Begin to execute in DAQ------------------------------------------
                    
                    if self.analogsignal_dev2_number != 0:
                        AnalogWriter_dev2.write_many_sample(self.writesamples_dev2, timeout = 605.0)
                        
                    if self.digitalsignalslinenumber != 0:     
                        DigitalWriter.write_many_sample_port_uint32(self.writesamples_digital, timeout = 605.0)
                                   
                    print('^^^^^^^^^^^^^^^^^^Daq tasks start^^^^^^^^^^^^^^^^^^')
                    if self.analogsignal_dev2_number != 0:
                        slave_Task_1_analog_dev2.start()            
                    
                    if self.digitalsignalslinenumber != 0:
                        slave_Task_2_digitallines.start()
                        
                    master_Task_readin.start() #!!!!!!!!!!!!!!!!!!!! READIN TASK HAS TO START AHEAD OF READ MANY SAMPLES, OTHERWISE ITS NOT SYN!!!
                    
                    reader.read_many_sample(data = self.Dataholder, number_of_samples_per_channel =  self.Totalscansamplesnumber, timeout=605.0)            
                    #self.data_PMT = []
                    
                    if self.analogsignal_dev2_number != 0:
                        slave_Task_1_analog_dev2.wait_until_done()
                    if self.digitalsignalslinenumber != 0:
                        slave_Task_2_digitallines.wait_until_done()                
                    master_Task_readin.wait_until_done()
                    
                    if self.analogsignal_dev2_number != 0:
                        slave_Task_1_analog_dev2.stop()
                    if self.digitalsignalslinenumber != 0:
                        slave_Task_2_digitallines.stop()
                    master_Task_readin.stop()
                    
                    if self.if_theres_readin_channel == True:
                        self.collected_data.emit(self.Dataholder)
                    self.finishSignal.emit()
                    print('^^^^^^^^^^^^^^^^^^Daq tasks finish^^^^^^^^^^^^^^^^^^')
                    
                    
                # set the keys of galvos back for next round
                for i in range(len(self.analogsignals['Sepcification'])):
                    if 'galvosx' in self.analogsignals['Sepcification'][i]:
                        self.analogsignals['Sepcification'][i] = self.galvosx_originalkey
                    elif 'galvosy' in self.analogsignals['Sepcification'][i]:
                        self.analogsignals['Sepcification'][i] = self.galvosy_originalkey
                        
                """
                # =============================================================================
                #         Only digital signals
                # =============================================================================
                """                    
            elif self.OnlyDigitalInvolved == True:
                
                # some preparations for digital lines
                Totalscansamplesnumber = len(self.digitalsignals['Waveform'][0])
                
                digitalsignalslinenumber = len(self.digitalsignals['Waveform'])
                        
                # Stack the digital samples        
                if digitalsignalslinenumber == 1:
                    holder2 = np.array([self.digitalsignals['Waveform'][0]])
        
                elif digitalsignalslinenumber == 0:
                    holder2 = []
                else:
                    holder2 = self.digitalsignals['Waveform'][0]
                    for i in range(1, digitalsignalslinenumber):
                        holder2 = np.vstack((holder2, self.digitalsignals['Waveform'][i]))
                
                # Set the dtype of digital signals
                #
                holder2 = np.array(holder2, dtype = 'uint32')        
                for i in range(digitalsignalslinenumber):
                    convernum = int(self.configdictionary[self.digitalsignals['Sepcification'][i]][self.configdictionary[self.digitalsignals['Sepcification'][i]].index('line')+
                                                          4:len(self.configdictionary[self.digitalsignals['Sepcification'][i]])])
                    print(convernum)
                    holder2[i] = holder2[i]*(2**(convernum))
                # For example, to send commands to line 0 and line 3, you hava to write 1001 to digital port, convert to uint32 that is 9.
                if digitalsignalslinenumber > 1:
                   holder2 = np.sum(holder2, axis = 0) # sum along the columns, for multiple lines        
                   holder2 = np.array([holder2]) # here convert the shape from (n,) to (1,n)
                #print(holder2.shape)
                #holder2 = holder2*16 
        
                #print(type(holder2[0][1]))
                #print(holder2[0][1])
        
                # Assume that dev1 is always employed
                with nidaqmx.Task() as slave_Task_2_digitallines:
                    # adding channels      
                    # Set tasks from different devices apart
                    slave_Task_2_digitallines.do_channels.add_do_chan("/Dev1/port0", line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
                    # Digital clock
                    slave_Task_2_digitallines.timing.cfg_samp_clk_timing(self.Daq_sample_rate, sample_mode= AcquisitionType.FINITE, samps_per_chan=Totalscansamplesnumber)
        
                	# Configure the writer and reader
                    DigitalWriter = nidaqmx.stream_writers.DigitalMultiChannelWriter(slave_Task_2_digitallines.out_stream, auto_start= False)
                    DigitalWriter.auto_start = False
                          
                    # ---------------------------------------------------------------------------------------------------------------------
                    #-----------------------------------------------------Begin to execute in DAQ------------------------------------------
                        
                    DigitalWriter.write_many_sample_port_uint32(holder2, timeout = 605.0)
                    
                    slave_Task_2_digitallines.start()
        
                    slave_Task_2_digitallines.wait_until_done(timeout = 605.0)                
        
                    slave_Task_2_digitallines.stop()        
        #----------------------------------------------------------------------------------------------------------------------------------
        
        # if the camera is the master clock source
        elif clock_source == "Camera":

            """
            # =============================================================================
            #         Analog signal in Dev 1 is involved
            # =============================================================================
            """
            if self.Dev1AnalogInvolved == True:
                with nidaqmx.Task() as slave_Task_1_analog_dev1, nidaqmx.Task() as slave_Task_1_analog_dev2, nidaqmx.Task() as master_Task_readin, nidaqmx.Task() as slave_Task_2_digitallines:
                    # adding channels      
                    # Set tasks from different devices apart
                    for i in range(self.analogsignal_dev1_number):
                        slave_Task_1_analog_dev1.ao_channels.add_ao_voltage_chan(self.analogwritesamplesdev1_Sepcification[i])
        
                    slave_Task_2_digitallines.do_channels.add_do_chan("/Dev1/port0", line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
                    
                    if self.if_theres_readin_channel == True:
                        self.Dataholder = np.zeros((len(self.readinchannels), self.Totalscansamplesnumber))
                    else:
                        self.Dataholder = np.zeros((1, self.Totalscansamplesnumber))
                        master_Task_readin.ai_channels.add_ai_voltage_chan(self.configdictionary['Vp']) # If no read-in channel is added, vp channel is added to keep code alive.
    
                    print(self.Dataholder.shape)
                    if 'PMT' in self.readinchannels:
                        master_Task_readin.ai_channels.add_ai_voltage_chan(self.configdictionary['PMT'])
                    if 'Vp' in self.readinchannels:
                        master_Task_readin.ai_channels.add_ai_voltage_chan(self.configdictionary['Vp'])
                    if 'Ip' in self.readinchannels:
                        master_Task_readin.ai_channels.add_ai_current_chan(self.configdictionary['Ip'])
                    
                    #get scaling coefficients
                    self.aichannelnames=master_Task_readin.ai_channels.channel_names
        
                    self.ai_dev_scaling_coeff_vp = []
                    self.ai_dev_scaling_coeff_ip = []
                    if "Vp" in self.readinchannels:
                        self.ai_dev_scaling_coeff_vp = nidaqmx._task_modules.channels.ai_channel.AIChannel(master_Task_readin._handle, self.configdictionary['Vp'])
                        #self.ai_dev_scaling_coeff.ai_dev_scaling_coeff
                        self.ai_dev_scaling_coeff_vp = np.array(self.ai_dev_scaling_coeff_vp.ai_dev_scaling_coeff)
                        
                    if "Ip" in self.readinchannels:
                        self.ai_dev_scaling_coeff_ip = nidaqmx._task_modules.channels.ai_channel.AIChannel(master_Task_readin._handle, self.configdictionary['Ip'])
                        #self.ai_dev_scaling_coeff.ai_dev_scaling_coeff
                        self.ai_dev_scaling_coeff_ip = np.array(self.ai_dev_scaling_coeff_ip.ai_dev_scaling_coeff)           
                    
                    self.ai_dev_scaling_coeff_list = np.append(self.ai_dev_scaling_coeff_vp, self.ai_dev_scaling_coeff_ip)
                    
                    # setting clock
                    # All the clock should refer to camera output trigger
                    self.cam_trigger_receiving_port = '/Dev1/PFI0'
                    
                    slave_Task_1_analog_dev1.timing.cfg_samp_clk_timing(self.Daq_sample_rate, source=self.cam_trigger_receiving_port, sample_mode= AcquisitionType.FINITE, samps_per_chan=self.Totalscansamplesnumber)
                    slave_Task_1_analog_dev1.triggers.start_trigger.cfg_dig_edge_start_trig(self.cam_trigger_receiving_port)
        
                    #slave_Task_1_analog_dev1.triggers.sync_type.SLAVE = True            
                    # Readin clock as master clock
                    master_Task_readin.timing.cfg_samp_clk_timing(self.Daq_sample_rate, source=self.cam_trigger_receiving_port, sample_mode= AcquisitionType.FINITE, samps_per_chan=self.Totalscansamplesnumber)
                    #master_Task_readin.triggers.sync_type.MASTER = True 
                    #master_Task_readin.export_signals(Signal.SAMPLE_CLOCK, '/Dev1/PFI1')
                    #master_Task_readin.export_signals(Signal.START_TRIGGER, '')
                    master_Task_readin.export_signals.samp_clk_output_term = self.configs.clock1Channel#'/Dev1/PFI1'#
                    master_Task_readin.export_signals.start_trig_output_term = self.configs.trigger1Channel#'/Dev1/PFI2'
                    master_Task_readin.triggers.start_trigger.cfg_dig_edge_start_trig(self.cam_trigger_receiving_port)
                    #slave_Task_1_analog_dev1.samp_clk_output_term
                    #slave_Task_1_analog_dev1.samp_trig_output_term
                    
                    if self.analogsignal_dev2_number != 0:
                        # By default assume that read master task is in dev1
                        
                        for i in range(self.analogsignal_dev2_number):
                            slave_Task_1_analog_dev2.ao_channels.add_ao_voltage_chan(self.analogwritesamplesdev2_Sepcification[i])
                        
                        dev2Clock = self.configs.clock2Channel#/Dev2/PFI1
                        slave_Task_1_analog_dev2.timing.cfg_samp_clk_timing(self.Daq_sample_rate, source=dev2Clock, sample_mode= AcquisitionType.FINITE, samps_per_chan=self.Totalscansamplesnumber)
                        #slave_Task_1_analog_dev2.triggers.sync_type.SLAVE = True
                        
                        #slave_Task_1_analog_dev2.triggers.start_trigger.cfg_dig_edge_start_trig(self.configs.trigger2Channel)#'/Dev2/PFI7'
                        
                        AnalogWriter = nidaqmx.stream_writers.AnalogMultiChannelWriter(slave_Task_1_analog_dev1.out_stream, auto_start= False)
                        AnalogWriter.auto_start = False
                        
                        AnalogWriter_dev2 = nidaqmx.stream_writers.AnalogMultiChannelWriter(slave_Task_1_analog_dev2.out_stream, auto_start= False)
                        AnalogWriter_dev2.auto_start = False
                    
                    # Digital clock
                    if len(self.digitalsignals['Sepcification']) != 0: 
                        slave_Task_2_digitallines.timing.cfg_samp_clk_timing(self.Daq_sample_rate, source=self.cam_trigger_receiving_port, sample_mode= AcquisitionType.FINITE, samps_per_chan=self.Totalscansamplesnumber)
                        slave_Task_2_digitallines.triggers.start_trigger.cfg_dig_edge_start_trig(self.cam_trigger_receiving_port)
                        #slave_Task_2_digitallines.triggers.sync_type.SLAVE = True
                    
        
                	# Configure the writer and reader
                    AnalogWriter = nidaqmx.stream_writers.AnalogMultiChannelWriter(slave_Task_1_analog_dev1.out_stream, auto_start= False)
                    AnalogWriter.auto_start = False
                    if len(self.digitalsignals['Sepcification']) != 0:
                        DigitalWriter = nidaqmx.stream_writers.DigitalMultiChannelWriter(slave_Task_2_digitallines.out_stream, auto_start= False)
                        DigitalWriter.auto_start = False
                    reader = AnalogMultiChannelReader(master_Task_readin.in_stream)        
                    reader.auto_start = False
        
                    # =============================================================================
                    # Begin to execute in DAQ
                    # =============================================================================
                    AnalogWriter.write_many_sample(self.writesamples_dev1, timeout = 605.0)
                    
                    if self.analogsignal_dev2_number != 0:
                        AnalogWriter_dev2.write_many_sample(self.writesamples_dev2, timeout = 605.0)
                        
                    if self.digitalsignalslinenumber != 0:     
                        DigitalWriter.write_many_sample_port_uint32(self.writesamples_digital, timeout = 605.0)
                                   
                    print('^^^^^^^^^^^^^^^^^^Daq tasks start^^^^^^^^^^^^^^^^^^')
                    if self.analogsignal_dev2_number != 0:
                        slave_Task_1_analog_dev2.start()            
                    slave_Task_1_analog_dev1.start()
                    
                    if self.digitalsignalslinenumber != 0:
                        slave_Task_2_digitallines.start()
                        
                    master_Task_readin.start() #!!!!!!!!!!!!!!!!!!!! READIN TASK HAS TO START AHEAD OF READ MANY SAMPLES, OTHERWISE ITS NOT SYN!!!
                    
                    reader.read_many_sample(data = self.Dataholder, number_of_samples_per_channel =  self.Totalscansamplesnumber, timeout=60.0)            
                    
                    
                    # wait_until_done will cause error here.
                    # slave_Task_1_analog_dev1.wait_until_done()
                    # if self.analogsignal_dev2_number != 0:
                    #     slave_Task_1_analog_dev2.wait_until_done()
                    # if self.digitalsignalslinenumber != 0:
                    #     slave_Task_2_digitallines.wait_until_done()                
                    # master_Task_readin.wait_until_done()
                    
                    # slave_Task_1_analog_dev1.stop()
                    # if self.analogsignal_dev2_number != 0:
                    #     slave_Task_1_analog_dev2.stop()
                    # if self.digitalsignalslinenumber != 0:
                    #     slave_Task_2_digitallines.stop()
                    # master_Task_readin.stop()
                    
    
                    print('^^^^^^^^^^^^^^^^^^Daq tasks finish^^^^^^^^^^^^^^^^^^')
                    if self.if_theres_readin_channel == True:
                        self.collected_data.emit(self.Dataholder)               
                    
                # set the keys of galvos back for next round
                for i in range(len(self.analogsignals['Sepcification'])):
                    if 'galvosx' in self.analogsignals['Sepcification'][i]:
                        self.analogsignals['Sepcification'][i] = self.galvosx_originalkey
                    elif 'galvosy' in self.analogsignals['Sepcification'][i]:
                        self.analogsignals['Sepcification'][i] = self.galvosy_originalkey
                        
                """
                # =============================================================================
                #         Only Dev 2 is involved in sending analog signals
                # =============================================================================
                """
            elif self.OnlyDev2AnalogInvolved == True:
                
                with nidaqmx.Task() as slave_Task_1_analog_dev2, nidaqmx.Task() as master_Task_readin, nidaqmx.Task() as slave_Task_2_digitallines:
                    # adding channels      
                    # Set tasks from different devices apart
                    slave_Task_2_digitallines.do_channels.add_do_chan("/Dev1/port0", line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        
                    if self.if_theres_readin_channel == True:
                        self.Dataholder = np.zeros((len(self.readinchannels), self.Totalscansamplesnumber))
                    else:
                        self.Dataholder = np.zeros((1, self.Totalscansamplesnumber))
                        master_Task_readin.ai_channels.add_ai_voltage_chan(self.configdictionary['Vp']) # If no read-in channel is added, vp channel is added to keep code alive.
                        
        #            print(self.Dataholder.shape)
                    if 'PMT' in self.readinchannels:
                        master_Task_readin.ai_channels.add_ai_voltage_chan(self.configdictionary['PMT'])
                    if 'Vp' in self.readinchannels:
                        master_Task_readin.ai_channels.add_ai_voltage_chan(self.configdictionary['Vp'])
                    if 'Ip' in self.readinchannels:
                        master_Task_readin.ai_channels.add_ai_current_chan(self.configdictionary['Ip'])
                    
                    #get scaling coefficients
                    self.aichannelnames=master_Task_readin.ai_channels.channel_names
        
                    self.ai_dev_scaling_coeff_vp = []
                    self.ai_dev_scaling_coeff_ip = []
                    if "Vp" in self.readinchannels:
                        self.ai_dev_scaling_coeff_vp = nidaqmx._task_modules.channels.ai_channel.AIChannel(master_Task_readin._handle, self.configdictionary['Vp'])
                        #self.ai_dev_scaling_coeff.ai_dev_scaling_coeff
                        self.ai_dev_scaling_coeff_vp = np.array(self.ai_dev_scaling_coeff_vp.ai_dev_scaling_coeff)
                        
                    if "Ip" in self.readinchannels:
                        self.ai_dev_scaling_coeff_ip = nidaqmx._task_modules.channels.ai_channel.AIChannel(master_Task_readin._handle, self.configdictionary['Ip'])
                        #self.ai_dev_scaling_coeff.ai_dev_scaling_coeff
                        self.ai_dev_scaling_coeff_ip = np.array(self.ai_dev_scaling_coeff_ip.ai_dev_scaling_coeff)           
                    
                    self.ai_dev_scaling_coeff_list = np.append(self.ai_dev_scaling_coeff_vp, self.ai_dev_scaling_coeff_ip)
                    
                    # setting clock
                    # All the clock should refer to camera output trigger
                    self.cam_trigger_receiving_port = '/Dev1/PFI0'
                    
                    master_Task_readin.timing.cfg_samp_clk_timing(self.Daq_sample_rate, source=self.cam_trigger_receiving_port, sample_mode= AcquisitionType.FINITE, samps_per_chan=self.Totalscansamplesnumber)
                    master_Task_readin.triggers.start_trigger.cfg_dig_edge_start_trig(self.cam_trigger_receiving_port)
                    master_Task_readin.export_signals.samp_clk_output_term = self.configs.clock1Channel#'/Dev1/PFI1'#
                    master_Task_readin.export_signals.start_trig_output_term = self.configs.trigger1Channel#'/Dev1/PFI2'
                    
                    if self.analogsignal_dev2_number != 0:
                        # By default assume that read master task is in dev1
                        
                        for i in range(self.analogsignal_dev2_number):
                            slave_Task_1_analog_dev2.ao_channels.add_ao_voltage_chan(self.analogwritesamplesdev2_Sepcification[i])
                        
                        dev2Clock = self.configs.clock2Channel#/Dev2/PFI1
                        slave_Task_1_analog_dev2.timing.cfg_samp_clk_timing(self.Daq_sample_rate, source=dev2Clock, sample_mode= AcquisitionType.FINITE, samps_per_chan=self.Totalscansamplesnumber)
                        slave_Task_1_analog_dev2.triggers.start_trigger.cfg_dig_edge_start_trig(self.cam_trigger_receiving_port)
                        AnalogWriter_dev2 = nidaqmx.stream_writers.AnalogMultiChannelWriter(slave_Task_1_analog_dev2.out_stream, auto_start= False)
                        AnalogWriter_dev2.auto_start = False
                    
                    # Digital clock
                    if len(self.digitalsignals['Sepcification']) != 0: 
                        slave_Task_2_digitallines.timing.cfg_samp_clk_timing(self.Daq_sample_rate, source=self.cam_trigger_receiving_port, sample_mode= AcquisitionType.FINITE, samps_per_chan=self.Totalscansamplesnumber)
                        slave_Task_2_digitallines.triggers.start_trigger.cfg_dig_edge_start_trig(self.cam_trigger_receiving_port)
                	# Configure the writer and reader
    
                    if len(self.digitalsignals['Sepcification']) != 0:
                        DigitalWriter = nidaqmx.stream_writers.DigitalMultiChannelWriter(slave_Task_2_digitallines.out_stream, auto_start= False)
                        DigitalWriter.auto_start = False
                    reader = AnalogMultiChannelReader(master_Task_readin.in_stream)        
                    reader.auto_start = False
                    # ---------------------------------------------------------------------------------------------------------------------
                    #-----------------------------------------------------Begin to execute in DAQ------------------------------------------
                    
                    if self.analogsignal_dev2_number != 0:
                        AnalogWriter_dev2.write_many_sample(self.writesamples_dev2, timeout = 605.0)
                        
                    if self.digitalsignalslinenumber != 0:     
                        DigitalWriter.write_many_sample_port_uint32(self.writesamples_digital, timeout = 605.0)
                                   
                    print('^^^^^^^^^^^^^^^^^^Daq tasks start^^^^^^^^^^^^^^^^^^')
                    if self.analogsignal_dev2_number != 0:
                        slave_Task_1_analog_dev2.start()            
                    
                    if self.digitalsignalslinenumber != 0:
                        slave_Task_2_digitallines.start()
                        
                    master_Task_readin.start() #!!!!!!!!!!!!!!!!!!!! READIN TASK HAS TO START AHEAD OF READ MANY SAMPLES, OTHERWISE ITS NOT SYN!!!
                    
                    reader.read_many_sample(data = self.Dataholder, number_of_samples_per_channel =  self.Totalscansamplesnumber, timeout=605.0)            
                    #self.data_PMT = []
                    
                    # if self.analogsignal_dev2_number != 0:
                    #     slave_Task_1_analog_dev2.wait_until_done()
                    # if self.digitalsignalslinenumber != 0:
                    #     slave_Task_2_digitallines.wait_until_done()                
                    # master_Task_readin.wait_until_done()
                    
                    # if self.analogsignal_dev2_number != 0:
                    #     slave_Task_1_analog_dev2.stop()
                    # if self.digitalsignalslinenumber != 0:
                    #     slave_Task_2_digitallines.stop()
                    # master_Task_readin.stop()
                    
    
                    print('^^^^^^^^^^^^^^^^^^Daq tasks finish^^^^^^^^^^^^^^^^^^')
                    if self.if_theres_readin_channel == True:
                        self.collected_data.emit(self.Dataholder)
                    self.finishSignal.emit()                
                    
                # set the keys of galvos back for next round
                for i in range(len(self.analogsignals['Sepcification'])):
                    if 'galvosx' in self.analogsignals['Sepcification'][i]:
                        self.analogsignals['Sepcification'][i] = self.galvosx_originalkey
                    elif 'galvosy' in self.analogsignals['Sepcification'][i]:
                        self.analogsignals['Sepcification'][i] = self.galvosy_originalkey
                        
                """
                # =============================================================================
                #         Only digital signals
                # =============================================================================
                """                    
            elif self.OnlyDigitalInvolved == True:
                
                self.cam_trigger_receiving_port = '/Dev1/PFI0'
                # some preparations for digital lines
                Totalscansamplesnumber = len(self.digitalsignals['Waveform'][0])
                
                digitalsignalslinenumber = len(self.digitalsignals['Waveform'])
                        
                # Stack the digital samples        
                if digitalsignalslinenumber == 1:
                    holder2 = np.array([self.digitalsignals['Waveform'][0]])
        
                elif digitalsignalslinenumber == 0:
                    holder2 = []
                else:
                    holder2 = self.digitalsignals['Waveform'][0]
                    for i in range(1, digitalsignalslinenumber):
                        holder2 = np.vstack((holder2, self.digitalsignals['Waveform'][i]))
                
                # Set the dtype of digital signals
                #
                holder2 = np.array(holder2, dtype = 'uint32')        
                for i in range(digitalsignalslinenumber):
                    convernum = int(self.configdictionary[self.digitalsignals['Sepcification'][i]][self.configdictionary[self.digitalsignals['Sepcification'][i]].index('line')+
                                                          4:len(self.configdictionary[self.digitalsignals['Sepcification'][i]])])
                    print(convernum)
                    holder2[i] = holder2[i]*(2**(convernum))
                # For example, to send commands to line 0 and line 3, you hava to write 1001 to digital port, convert to uint32 that is 9.
                if digitalsignalslinenumber > 1:
                   holder2 = np.sum(holder2, axis = 0) # sum along the columns, for multiple lines        
                   holder2 = np.array([holder2]) # here convert the shape from (n,) to (1,n)
                #print(holder2.shape)
                #holder2 = holder2*16 
        
                #print(type(holder2[0][1]))
                #print(holder2[0][1])
        
                # Assume that dev1 is always employed
                with nidaqmx.Task() as slave_Task_2_digitallines:
                    # adding channels      
                    # Set tasks from different devices apart
                    #for i in range(len(digitalsignals['Sepcification'])):
                        #slave_Task_2_digitallines.do_channels.add_do_chan(configdictionary[digitalsignals['Sepcification'][i]], line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)#line_grouping??????????????One Channel For Each Line
                    slave_Task_2_digitallines.do_channels.add_do_chan("/Dev1/port0", line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
                    # Digital clock
                    slave_Task_2_digitallines.timing.cfg_samp_clk_timing(self.Daq_sample_rate, source=self.cam_trigger_receiving_port, sample_mode= AcquisitionType.FINITE, samps_per_chan=Totalscansamplesnumber)
                    slave_Task_2_digitallines.triggers.start_trigger.cfg_dig_edge_start_trig(self.cam_trigger_receiving_port)
                	# Configure the writer and reader
                    DigitalWriter = nidaqmx.stream_writers.DigitalMultiChannelWriter(slave_Task_2_digitallines.out_stream, auto_start= False)
                    DigitalWriter.auto_start = False
                          
                    # ---------------------------------------------------------------------------------------------------------------------
                    #-----------------------------------------------------Begin to execute in DAQ------------------------------------------
                        
                    DigitalWriter.write_many_sample_port_uint32(holder2, timeout = 605.0)
                    
                    slave_Task_2_digitallines.start()
        
                    slave_Task_2_digitallines.wait_until_done(timeout = 605.0)                
        
                    slave_Task_2_digitallines.stop()   
                    
        
    def save_as_binary(self, directory):
        #print(self.ai_dev_scaling_coeff_vp)
        if self.if_theres_readin_channel == True:
            if 'Vp' in self.readinchannels:
                
                if 'PMT' not in self.readinchannels:
                    self.binaryfile_vp_data = np.concatenate((np.array([self.Daq_sample_rate]), np.array(self.ai_dev_scaling_coeff_vp), self.Dataholder[0,:]))
                    np.save(os.path.join(directory, 'Vp'+datetime.now().strftime('%Y-%m-%d_%H-%M-%S')), self.binaryfile_vp_data)
                   
                    if 'Ip' in self.readinchannels:
                        self.binaryfile_Ip_data = np.concatenate((np.array([self.Daq_sample_rate]), np.array(self.ai_dev_scaling_coeff_ip), self.Dataholder[1,:]))
                        np.save(os.path.join(directory, 'Ip'+datetime.now().strftime('%Y-%m-%d_%H-%M-%S')), self.binaryfile_Ip_data)                    
                else:
                    self.binaryfile_vp_data = np.concatenate((np.array([self.Daq_sample_rate]), np.array(self.ai_dev_scaling_coeff_vp), self.Dataholder[1,:]))
                    np.save(os.path.join(directory, 'Vp'+datetime.now().strftime('%Y-%m-%d_%H-%M-%S')), self.binaryfile_vp_data)
                    
                    if 'Ip' in self.readinchannels:
                        self.binaryfile_Ip_data = np.concatenate((np.array([self.Daq_sample_rate]), np.array(self.ai_dev_scaling_coeff_ip), self.Dataholder[2,:]))
                        np.save(os.path.join(directory, 'Ip'+datetime.now().strftime('%Y-%m-%d_%H-%M-%S')), self.binaryfile_Ip_data) 
            if 'PMT' in self.readinchannels: 
                self.data_PMT = self.Dataholder[0,:]*-1
                np.save(os.path.join(directory, 'PMT_array_'+datetime.now().strftime('%Y-%m-%d_%H-%M-%S')), self.data_PMT) 
#                self.pmtimage = Image.fromarray(self.data_PMT) #generate an image object
#                self.pmtimage.save(os.path.join(directory, 'PMT'+datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'.tif')) #save as tif
                

if __name__ == "__main__":
     daq= DAQmission()
     # daq.sendSingleDigital('blankingall', 0)
     daq.sendSingleAnalog('galvosx', 0)
     daq.sendSingleAnalog('galvosy', 0)