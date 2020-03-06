# -*- coding: utf-8 -*-
"""
Created on Thu Feb 13 12:10:35 2020

@author: xinmeng
"""

import serial

class KBD101Controller:
    """
    This class initializes a KBD101 controller, to be able to control the
    Thorlabs translation stage. 
    Baudrate: 9600
    Parity: None
    """
    def __init__(self, address):
        self.baudrate = 115200
        self.parity = None
        self.address = address
        
    def IdentifySelf(self):
        '''
        Instruct hardware unit to identify itself (by flashing its front panel  LEDs).  
        '''
        with serial.Serial(self.address, self.baudrate) as translationmotor:
            command = '230200005001'#command = '230200005001'
            translationmotor.write(command.encode()) 
            
    def MoveAbs50mm(self):
        '''
        Move to absolute position at 50mm.
        '''
        with serial.Serial(self.address, self.baudrate) as translationmotor:
            command = '53040600A2011000400D0300'
            translationmotor.write(command.encode())         
        
            
    def Disconnect(self):
        with serial.Serial(self.address, self.baudrate) as translationmotor:
            command = '020000005001' # TX 02, 00, 00, 00, 50, 01
            translationmotor.write(command.encode())         
        
#    def moveToPosition(self, position=0):
            
if (__name__ == "__main__"):
    
    import time
    translationmotor = KBD101Controller('COM10')
    translationmotor.IdentifySelf()
    translationmotor.MoveAbs50mm()
    time.sleep(1)
    translationmotor.Disconnect()