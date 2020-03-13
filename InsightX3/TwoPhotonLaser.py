# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 11:31:53 2020

@author: xinmeng

# =============================================================================
# General control of Insight X3.
# =============================================================================
"""

import serial

class InsightX3:
    """
    8 data bits
    no parity
    one stop bit
    baud rate 9600
    
    The control flow of an InSight X3 program might look like this:
    1.Turn on the system, then wait approximately 120 seconds for the computers to initialize.
    2.Begin issuing a series of READ:PCTWarmedup? queries and wait for the laser to return “100” to indicate the system is fully warmed up.
    3.Set the output wavelength to 800 nm by issuing the WAVelength 800 command.
    4.Check the operational readiness by issuing *STB? and then interpret the state bits of the numerical response to determine if the state is ready (State 25).
    5.Turn on the laser by issuing the ON command.
    6.Issue *STB? every 1 second until the response state indicates RUN (State 50).
    7.Open the shutter by issuing the SHUTTER 1 command.
    
    Hibernate — This is the default day-to-day operating mode. Shuts off the laser diode, 
    closes the shutters, and saves the wavelength and motor positions. It also closes the GUI. 
    Using Hibernate DOES NOT shut down the laser internal computer operations, so the laser can be restarted without the delay of the internal 
    computers rebooting. Because Hibernate does not shut down the internal computers, the power 
    supply MUST BE LEFT ON when using the Hibernate mode. DO NOT TURN OFF THE POWER!
    """
    def __init__(self, address):
        self.baudrate = 9600
        self.parity = None
        self.address = address
        self.CRending = '\r'
        self.LFending = '\n'
        
    def QueryLaserID(self):
        """
        Returns a system identification string that contains four fields separated by commas
        """
        command = '*IDN?' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))        
            LaserID_byte = Insight.readline() #Reads an '\n' terminated line
            LaserID = LaserID_byte.decode("utf-8")
            
            print(LaserID)
            
    def QueryStatus(self):
        """
        Returns an integer value that corresponds to a 32-bit binary number. 
        Some binary bit locations correspond to the status of individual components, 
        while others give general status information. This allows immediate analysis of the laser status.
        """
        command = '*STB?' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))
            status_byte = Insight.readline() #Reads an '\n' terminated line

            Status_binary = '{:032b}'.format(int(status_byte.decode("utf-8")))# It's now a 32 bit string.
        
        # =============================================================================
        #         Interpretation from bit numbers. Referring Insight Programming A-8 for details.
        # =============================================================================
        Status_list = []
        if Status_binary[31] == '1':
            Status_list.append('Emission')
        if Status_binary[30] == '1':
            Status_list.append('Pulsing')
        if Status_binary[29] == '1':
            Status_list.append('Tubalbe beam shutter open')
        elif Status_binary[29] == '0':
            Status_list.append('Tubalbe beam shutter closed')
        # if Status_binary[28] == '1':
        #     Status_list.append('Fixed IP beam shutter open')# always 1 for our laser.
        if Status_binary[26] == '1':
            Status_list.append('Servo on')
        if Status_binary[22] == '1':
            Status_list.append('User interlock open')
        if Status_binary[21] == '1':
            Status_list.append('Keyswitch open')
        if Status_binary[20] == '1':
            Status_list.append('Power supply interlock open')
        if Status_binary[19] == '1':
            Status_list.append('Internal interlock open')
        if Status_binary[17] == '1':
            Status_list.append('Warning! ERROR detected')# Use READ:AHIStory? (page A-4) to see what is causing the warning.
        if Status_binary[16] == '1':
            Status_list.append('Fault! Laser truned off')
            
        Laser_state = int(Status_binary[9:16], 2)
        if Laser_state <= 24:
            Status_list.append('Laser state:Initializing')
        if Laser_state == 25:
            Status_list.append('Laser state:Ready')
        if 26 <= Laser_state <= 49:
            Status_list.append('Laser state:Turning on/Optimizing')
        if Laser_state == 50:
            Status_list.append('Laser state:RUN')
        if 51 <= Laser_state <= 59:
            Status_list.append('Laser state:Moving to Align mode')
        if Laser_state == 60:
            Status_list.append('Laser state:Align mode')
        if 61 <= Laser_state <= 69:
            Status_list.append('Laser state:Exiting Align mode')
            
        print(Status_list)
        return Status_list
            
    def QueryWarmupTime(self):
        """
        Returns the status of system warm-up as a percent of the predicted total time. The system responds with a value similar to 050<LF>. 
        When the response is 100<LF>, the laser can be turned on.
        """
        command = 'READ:PCTWarmedup?' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))
            warmupstatus_byte = Insight.readline() #Reads an '\n' terminated line
            warmupstatus = warmupstatus_byte.decode("utf-8")
            
            print('Warming up: {}%'.format(warmupstatus[0:len(warmupstatus)-1]))
            return warmupstatus
        
    def QueryPower(self):
        """
        Returns the laser output power (in Watts).
        """
        command = 'READ:POWer?' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))        
            LaserPower = (Insight.readline()).decode("utf-8")
            
            print('LaserPower is {} w.'.format(LaserPower))
            print(LaserPower)
            
    def QueryWavelength(self):
        """
        The query returns the most recent value of the WAVelength command. 
        Use it to verify that the command was properly received. A typical response might be 900<LF>.
        """
        command = 'WAVelength?' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))        
            LaserWavelength = (Insight.readline()).decode("utf-8")
            
            print('LaserWavelength is {} nm.'.format(LaserWavelength[0:len(LaserWavelength)-1]))
            # print(LaserWavelength)
            return LaserWavelength
            
    def SetWavelength(self, Wavelength):
        """
        Sets the wavelength to between 680 and 1300 nm. Values out of this range are ignored.
        The query returns the most recent value of the WAVelength command. 
        Use it to verify that the command was properly received. A typical response might be 900<LF>.
        """
        command = 'WAVelength ' + str(Wavelength) + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))
            print('LaserWavelength going to {} nm...'.format(Wavelength))
            
    def Turn_On_PumpLaser(self):
        """
        Turns on the pump laser.
        NOTE:The shutter is not automatically opened when the ON command is issued.
        
        The response to this command depends on whether or not the system is warmed up. 
        Use the READ:PCTWarmedup? query to determine the progress of the warm-up cycle. 
        When the response to this query reaches 100, the laser can be started. While the response is 0 to 99, the ON command is simply ignored.
        """
        command = 'ON' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))        
            ONresponse = (Insight.readline()).decode("utf-8")
            
            print('The response to ON is: {}'.format(ONresponse))
            
    def Turn_Off_PumpLaser(self):
        """
        Turns off the pump diode laser, but the oven temperatures are maintained for a quick warm-up time. 
        To turn off the laser system entirely, refer to the SHUTDOWN command.
        """
        command = 'OFF' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))        
            
            print('Pump diode laser turned down.')
            
    def Open_TunableBeamShutter(self):
        """
        Opens the tunable beam shutter.
        It is normal for *STB? to return an incorrect shutter status for approximately 1 second after issuing the SHUTter 1 command.
        """
        command = 'SHUTter 1' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))    
            
    def Close_TunableBeamShutter(self):
        """
        Closes the tunable beam shutter.
        """
        command = 'SHUTter 0' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii")) 
            
    def SaveVariables(self):
        """
        Saves the variables and continues laser operation, unlike the SHUTDOWN command, which saves these variables and turns off the system.
        """
        command = 'SAVe' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))        
            SAVeresponse = (Insight.readline()).decode("utf-8")
            
            print(SAVeresponse)
            
        
if __name__ == "__main__":
    
    Laserinstance = InsightX3('COM11')
    Laserinstance.QueryLaserID()
    Laserinstance.QueryStatus()
    warmupstatus = Laserinstance.QueryWarmupTime()
    Laserinstance.QueryWavelength()
    
    # Laserinstance.SetWavelength(1280)