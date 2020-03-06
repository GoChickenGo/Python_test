# -*- coding: utf-8 -*-
"""
Created on Mon Mar 11 12:40:17 2019

@author: lhuismans

This class manages the configurations for all the devices. 
All the ports/serialnumbers/channels etc. are stored and managed via this class.

To make sure that every instance of this class has the same variables the class
makes use of a Singleton pattern. This allows only a single instance of the class
and thus ensures that independent of where it is initiated and changed the values 
of this class will stay the same. 
http://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html
https://stackoverflow.com/questions/44237186/what-is-the-best-way-to-share-data-between-widgets-with-pyqt

In addition to this the class makes use of properties which replace the setter/
getter functions in python. 
https://www.python-course.eu/python3_properties.php

Then there are two extra functions for saving variables to a file. When the variables are first opened 
we want the previous values to be loaded (using the load function), this happens when opening
the main window and is thus part of opening the program.

The save method allows to save changes so they can be used the next time the program is used.
This already happens when hitting "apply" in the configuration window.
"""
try:
   import cPickle as pickle
except:
   import pickle
import os

class Singleton:
    """Alex Martelli implementation of Singleton (Borg)
    http://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html
    
    Obtained from: 
    https://stackoverflow.com/questions/44237186/what-is-the-best-way-to-share-data-between-widgets-with-pyqt"""
    
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class Configuration(Singleton):
    def __init__(self):
        Singleton.__init__(self)
        self.loadVariables()
        
    #--------------------------Loading and saving------------------------------
    def loadVariables(self):
        """Derived from: https://stackoverflow.com/questions/2709800/how-to-pickle-yourself
        Used to load the previous configuration."""
        try:
            file = open("./NIDAQ/configurationvariables.pickle", "rb") #When loading from Python_test folder
        except:
            try:
                file = open(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\People\Xin Meng\Code\Python_test\NIDAQ\configurationvariables.pickle', "rb")
            except:
                file = open(r'C:\Lab_program\Python_test\NIDAQ\configurationvariables.pickle', "rb")
#        file = open(r"M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\People\Xin Meng\Code\Python_test\configurationvariables.pickle", "rb")
        tmp_dict = pickle.load(file)
        file.close()
        
        self.__dict__.update(tmp_dict)
        
    def saveVariables(self):
        file = open("./configurationvariables.pickle", "wb")
        pickle.dump(self.__dict__, file, 2)
        file.close()
        
    #--------------------------Python setter and getters (properites)----------
    """For the use of properties see:
        https://www.python-course.eu/python3_properties.php
        These replace the setters and getters. When variables have to be modified,
        e.g. you want to cast a variable in a desired format like a string, these
        can be used."""
    @property
    def filter1Port(self):
        return self.__filter1Port
    
    @filter1Port.setter
    def filter1Port(self, port):
        self.__filter1Port = str(port)
        
    @property
    def filter2Port(self):
        return self.__filter2Port
    
    @filter2Port.setter
    def filter2Port(self, port):
        self.__filter2Port = str(port)
        
    @property
    def filter3Port(self):
        return self.__filter2Port
    
    @filter3Port.setter
    def filter3Port(self, port):
        self.__filter3Port = str(port)
        
    @property
    def dmdPort(self):
        return self.__dmdPort
    
    @dmdPort.setter
    def dmdPort(self, port):
        self.__dmdPort = str(port)
        
    @property
    def dmdSerialNumber(self):
        return self.__dmdSerialNumber
    
    @dmdSerialNumber.setter
    def dmdSerialNumber(self, serialnumber):
        self.__dmdSerialNumber = int(serialnumber)
        
    @property
    def stagePort(self):
        return self.__stagePort
    
    @stagePort.setter
    def stagePort(self, port):
        self.__stagePort = str(port)
        
    @property
    def aotfChannel(self):
        return self.__aotfChannel
    
    @aotfChannel.setter
    def aotfChannel(self, channel):
        self.__aotfChannel = str(channel)
    
    @property
    def patchVoltInChannel(self):
        return self.__patchVoltInChannel
    
    @patchVoltInChannel.setter
    def patchVoltInChannel(self, channel):
        self.__patchVoltInChannel = str(channel)
        
    @property
    def patchVoltOutChannel(self):
        return self.__patchVoltOutChannel
    
    @patchVoltOutChannel.setter
    def patchVoltOutChannel(self, channel):
        self.__patchVoltOutChannel = str(channel)
        
    @property
    def patchCurOutChannel(self):
        return self.__patchCurOutChannel
    
    @patchCurOutChannel.setter
    def patchCurOutChannel(self, channel):
        self.__patchCurOutChannel = str(channel)
        
    @property
    def galvoXChannel(self):
        return self.__galvoXChannel
    
    @galvoXChannel.setter
    def galvoXChannel(self, channel):
        self.__galvoXChannel = str(channel)
        
    @property
    def galvoYChannel(self):
        return self.__galvoYChannel
    
    @galvoYChannel.setter
    def galvoYChannel(self, channel):
        self.__galvoYChannel = str(channel)
        
    @property
    def pmtChannel(self):
        return self.__pmtChannel
    
    @pmtChannel.setter
    def pmtChannel(self, channel):
        self.__pmtChannel = str(channel)
        
    @property
    def trigger1Channel(self):
        return self.__trigger1Channel
    
    @trigger1Channel.setter
    def trigger1Channel(self, channel):
        self.__trigger1Channel = str(channel)
    
    @property
    def trigger2Channel(self):
        return self.__trigger2Channel
    
    @trigger2Channel.setter
    def trigger2Channel(self, channel):
        self.__trigger2Channel = str(channel)
        
    @property
    def clock1Channel(self):
        return self.__clock1Channel
    
    @clock1Channel.setter
    def clock1Channel(self, channel):
        self.__clock1Channel = channel
        
    @property
    def clock2Channel(self):
        return self.__clock2Channel
    
    @clock2Channel.setter
    def clock2Channel(self, channel):
        self.__clock2Channel = channel
        