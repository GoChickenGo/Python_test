# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 13:32:17 2019

@author: xinmeng
"""

import nidaqmx
import numpy as np
from nidaqmx.constants import AcquisitionType, TaskMode

Daq_sample_rate = 50000

with nidaqmx.Task() as master_task:
    master_task.ao_channels.add_ao_voltage_chan("/Dev1/ao1")
    
    master_task.timing.cfg_samp_clk_timing(
        Daq_sample_rate, sample_mode=AcquisitionType.FINITE, samps_per_chan=100000) # set up clock
    
    samples=0*np.sin(np.arange(0, 30, 0.0001))
    
    master_task.write(samples)
    master_task.start()
    master_task.wait_until_done()
    