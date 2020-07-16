# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 11:31:53 2020

@author: xinmeng

# =============================================================================
# General control of Insight X3.
# =============================================================================
"""

import serial
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal
import time

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
                        print('Laser action failed, failnumber: {}'.format(failnumber))
                        time.sleep(0.2)
                else:
                    print('Fail for 8 times, give up - -')
                    success = False                    
                    
            return returnValue
        
        return wrapper
    
    @Try_until_Success
    def QueryLaserID(self):
        """
        Returns a system identification string that contains four fields separated by commas
        """
        command = '*IDN?' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii", errors='replace'))        
            LaserID_byte = Insight.readline() #Reads an '\n' terminated line
            LaserID = LaserID_byte.decode("utf-8", errors='replace')
            
            print(LaserID)
    
    @Try_until_Success
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
            Status_list.append('Tunable beam shutter open')
        elif Status_binary[29] == '0':
            Status_list.append('Tunable beam shutter closed')
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
    
    @Try_until_Success
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
    
    @Try_until_Success
    def QueryPower(self):
        """
        Returns the laser output power (in Watts).
        """
        command = 'READ:POWer?' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))        
            LaserPower = (Insight.readline()).decode("utf-8")
            
#            print('LaserPower is {} w.'.format(LaserPower))
#            print(LaserPower)
            return LaserPower
        
    @Try_until_Success
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

            return LaserWavelength
    
    @Try_until_Success
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
    
    @Try_until_Success
    def SetWatchdogTimer(self, timeout):
        """
        Sets the number of seconds for the software watchdog timer. A value of 0 disables the software watchdog timer. 
        If the laser does not receive a valid command (or query) every n seconds, the pump laser is turned off and shutters are closed. 
        A recommended value of 3 seconds should be used. Do not disable the timer except for programing support.
        """
        command = 'TIMer:WATChdog ' + str(timeout) + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))
            print('TIMer:WATChdog set to {} s.'.format(timeout))
    
    @Try_until_Success
    def SetOperatingMode(self, mode):
        """
        MODE RUN sets the laser to standard operating mode.
        MODE ALIGN sets the laser to low power so that it is easier and safer to align the optical beam through a microscope. 
        Note that the laser does not necessarily meet mode quality or divergence specifications at the low power.
        """
        if mode == 'MODE RUN':
            command = 'MODE RUN' + self.CRending
        elif mode == 'MODE ALIGN':
            command = 'MODE ALIGN' + self.CRending
            
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))        
            print('Setting: {}'.format(mode))
    
    @Try_until_Success
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
#            ONresponse = (Insight.readline()).decode("utf-8")
            
#            print('The response to ON is: {}'.format(ONresponse))
    
    @Try_until_Success
    def Turn_Off_PumpLaser(self):
        """
        Turns off the pump diode laser, but the oven temperatures are maintained for a quick warm-up time. 
        To turn off the laser system entirely, refer to the SHUTDOWN command.
        """
        command = 'OFF' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))        
            
            print('Pump diode laser turned down.')
    
    @Try_until_Success
    def Open_TunableBeamShutter(self):
        """
        Opens the tunable beam shutter.
        It is normal for *STB? to return an incorrect shutter status for approximately 1 second after issuing the SHUTter 1 command.
        """
        command = 'SHUTter 1' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))    
    
    @Try_until_Success
    def Close_TunableBeamShutter(self):
        """
        Closes the tunable beam shutter.
        """
        command = 'SHUTter 0' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii")) 
    
    @Try_until_Success
    def SaveVariables(self):
        """
        Saves the variables and continues laser operation, unlike the SHUTDOWN command, which saves these variables and turns off the system.
        """
        command = 'SAVe' + self.CRending
        
        with serial.Serial(self.address, self.baudrate) as Insight:
            Insight.write(command.encode("ascii"))        
            SAVeresponse = (Insight.readline()).decode("utf-8")
            
            print(SAVeresponse)
            

class QueryLaserStatusThread(QThread):
    """
    Thread to query laser status. 
    CAN NOT QUERY AND SEND COMMANDS AT THE SAME TIME!!!
    
    BEFORE SENDING COMMANDS, ONE CAN SET STOPFLAG TO FALSE AND START AGAIN AFTER EXECUTION,
    """
    Thread_Status_list = pyqtSignal(list)
    def __init__(self, Laserinstance, frequency, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Laserinstance = Laserinstance
        self.queryfreq = frequency
        self.stopflag = False
        
        self.Status_list = None
        self.Status_wavelength = None
        self.Status_power = None
        
    def run(self):
        while self.stopflag == False:
            # print('WatchDog started.')
            try:
                self.Status_list = self.Laserinstance.QueryStatus()
#                self.Status_wavelength = self.Laserinstance.QueryWavelength()
                self.Status_power = self.Laserinstance.QueryPower()
                self.Status_list.append(self.Status_power)
                self.Thread_Status_list.emit(self.Status_list)
            except:
                print('Query status failed.')
            time.sleep(((1/self.queryfreq)))
        if self.stopflag == True:
            self.quit()
            self.wait()
            print('WatchDog stopped.')
            
if __name__ == "__main__":
    import time
    
    if False:
        Laserinstance = InsightX3('COM11')
    
        Laserinstance.QueryLaserID()
        Laserinstance.SetWatchdogTimer(3)
        
        targetwavelength = 1280
        
    #    QueryWatchDog = QueryLaserStatusThread(Laserinstance, 1.1)
    #
    #    QueryWatchDog.start()
    #    time.sleep(1)
    #    print(QueryWatchDog.Status_wavelength)
    #
    #    time.sleep(1)
    #    QueryWatchDog.stopflag = True
    #    time.sleep(1)
    #    Laserinstance.SetWavelength(1280)
    #    time.sleep(1)
    #    #Restart query thread
    #    QueryWatchDog.stopflag = False
    #    QueryWatchDog.start()
    #    time.sleep(1)
    #    print(QueryWatchDog.Status_wavelength)
    #    time.sleep(1)
    #
    #    QueryWatchDog.stopflag = True
    #    time.sleep(2)
    #    print(QueryWatchDog.isRunning())
        
    #    #--------------------Wait for laser to initialize--------------------------
    #    if 'Laser state:Initializing' in QueryWatchDog.Status_list:
    #        while 'Laser state:Initializing' in QueryWatchDog.Status_list:
    #            time.sleep(0.5)   
    #         
    #    if 'Laser state:Ready' in QueryWatchDog.Status_list:
    #        
    #        """
    #        Begin issuing a series of READ:PCTWarmedup? queries and wait for the laser to return “100” to indicate the system is fully warmed up.
    #        """        
    #        warmupstatus = 0
    #        while int(warmupstatus) != 100:
    #            try:
    #                warmupstatus = Laserinstance.QueryWarmupTime()
    #                time.sleep(0.6)
    #            except:
    #                time.sleep(0.6)
                    
            
        
        Status_list = Laserinstance.QueryStatus()
        
        if 'Laser state:Initializing' in Status_list:
            while 'Laser state:Initializing' in Status_list:
                Status_list = Laserinstance.QueryStatus()
                time.sleep(0.5)
                
        if 'Laser state:Ready' in Status_list:
            warmupstatus = 0
            while int(warmupstatus) != 100:
                warmupstatus = Laserinstance.QueryWarmupTime()
                time.sleep(0.5)        
            #-Set the wavelength
            Laserinstance.SetWavelength(targetwavelength)
            LaserWavelength = Laserinstance.QueryWavelength()
            
            Status_list = Laserinstance.QueryStatus()
            if int(LaserWavelength) == targetwavelength and 'Laser state:Ready' in Status_list:
                while int(warmupstatus) != 100:
                    warmupstatus = Laserinstance.QueryWarmupTime()
                    time.sleep(0.5)
                if int(warmupstatus) == 100:
                    print('try to turn on pump laser...')
                    Laserinstance.Turn_On_PumpLaser()
                
                    # Wait for the laser to be in running state.
                    Status_list = Laserinstance.QueryStatus()
                    while 'Laser state:RUN' not in Status_list:
                        Status_list = Laserinstance.QueryStatus()
                        time.sleep(1)
                    print('Laser state:RUN')
                    
                    # Open the shutter.
                    Status_list = Laserinstance.QueryStatus()
                    if 'Tubable beam shutter closed' in Status_list:
                        Laserinstance.Open_TunableBeamShutter()
                    print('Laser shutter open.')
                    time.sleep(2)
                    
                    Status_list = Laserinstance.QueryStatus()
                    if 'Tubable beam shutter open' in Status_list:
                        Laserinstance.Close_TunableBeamShutter()
                    print('Laser shutter closed.')
                    
                    Status_list = Laserinstance.QueryStatus()
                    Laserinstance.SaveVariables()
                    
                    Status_list = Laserinstance.QueryStatus()
                    Laserinstance.Turn_Off_PumpLaser()
                    print('Turn_Off_PumpLaser.')