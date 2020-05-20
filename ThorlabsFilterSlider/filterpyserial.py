# -*- coding: utf-8 -*-
"""
Created on Thu Nov  8 12:55:22 2018

@author: lhuismans
"""
import serial
import time

class ELL9Filter:
    """
    This class initializes a ELL9K filter stage, to be able to control the
    device. 
    Baudrate: 9600
    Parity: None
    """
    def __init__(self, address):
        self.baudrate = 9600
        self.parity = None
        self.address = address
        
    def Try_until_Success(func):
        """ This is the decorator to try to execute the function until succeed.
        """
        def wrapper(*args, **kwargs):
            
            success = None
            failnumber = 0
            
            while success is None:
                if failnumber <8:
                    try:
                        returnValue = func(*args, **kwargs)
                        success = True

                    except:
    
                        failnumber += 1                    
                        print('filter move failed, failnumber: {}'.format(failnumber))
                        time.sleep(0.2)
                else:
                    print('Fail for 8 times, give up - -')
                    success = False                    
                    
            return returnValue
        
        return wrapper
    
    @Try_until_Success
    def home(self):
        """
        Moves the stage to its home position.
        """
        with serial.Serial(self.address, self.baudrate) as motor: #You can find the COM# using ELLO
            command = '0ho0'
            motor.write(command.encode()) #Moves the stage of channel 0 to home
          
    @Try_until_Success
    def forward(self):
        """
        Moves the stage one position forward.
        """
        with serial.Serial(self.address, self.baudrate) as motor:
            command = '0fw'
            motor.write(command.encode()) #Moves the stage of channel 0 one position forward
    
    @Try_until_Success     
    def backward(self):
        """
        Moves the stage one position backward.
        """
        with serial.Serial(self.address, self.baudrate) as motor:
            command = '0bw'
            motor.write(command.encode()) #Moves the stage of channel 0 one position backward
    
    @Try_until_Success
    def moveToPosition(self, position=0):
        """
        Moves the stage to an absolute position.
        The positions are labeled 0, 1, 2 and 3, each linked to a filter.
        """
        assert position < 4, "Choose a position 0, 1, 2 or 3"

        with serial.Serial(self.address, self.baudrate, timeout = 1) as motor:
            if position == 0:
                command = '0ma00000000'
            elif position == 1:
                command = "0ma0000001F"
            elif position == 2:
                command = "0ma0000003E"
            elif position == 3:
                command = "0ma0000005D"
            motor.write(command.encode())

    @Try_until_Success
    def getPosition(self):
        """
        Retrieves the current position of the filter and prints the value.
        """
        with serial.Serial(self.address, self.baudrate, timeout = 1) as motor:
            command = '0gp'
            motor.write(command.encode())
            position = motor.read(size=11)

            if position == b'0PO00000000':
                return 0
            elif position == b'0PO0000001F':
                return 1
            elif position == b'0PO0000003E':
                return 2
            elif position == b'0PO0000005D':
                return 3       