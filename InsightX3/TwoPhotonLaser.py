# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 11:42:33 2020

@author: xinmeng

Caution:
--Need some gap between Setting wavelength and open shutter operations.
--IT IS VERY IMPORTANT TO KILL THE WATCHDOG AND THEN EXECUTE OPERATION! OTHERWISE ONCE THEY HAPPEN AT THE SAME TIME, LASER WILL TURN OFF!
"""

import time
try:
    from TwoPhotonLaser_backend import InsightX3, QueryLaserStatusThread
except:
    from InsightX3.TwoPhotonLaser_backend import InsightX3, QueryLaserStatusThread

class TwoPhotonExecutor:
    
    def __init__(self, address, WatchdogFreq, WatchdogTimer):
        self.address = address
        self.WatchdogFreq = WatchdogFreq
        self.warmupstatus = False
        self.laserReady = False
        self.laserRun = False
        self.WatchdogTimer = WatchdogTimer
        
    def InitLaser(self):
        self.Laserinstance = InsightX3(self.address)
    
        # self.Laserinstance.QueryLaserID()
        self.Laserinstance.SetWatchdogTimer(self.WatchdogTimer)
        
        # Start the status query thread
        self.QueryWatchDog = QueryLaserStatusThread(self.Laserinstance, self.WatchdogFreq)
        self.QueryWatchDog.start()
        time.sleep(1)
        
        #--------------------Wait for laser to initialize--------------------------
        if 'Laser state:Initializing' in self.QueryWatchDog.Status_list:
            print('Laser state:Initializing')
            while 'Laser state:Initializing' in self.QueryWatchDog.Status_list:
                time.sleep(0.5)
                
        if 'Laser state:Ready' in self.QueryWatchDog.Status_list:
            self.laserReady = True
            print('Laser state:Ready')
    
    def CheckWarmup(self):
        """
        Begin issuing a series of READ:PCTWarmedup? queries and wait for the laser to return “100” to indicate the system is fully warmed up.
        """        
        warmupstatus = 0
        while int(warmupstatus) != 100:
            try:
                warmupstatus = self.Laserinstance.QueryWarmupTime()
                time.sleep(0.6)
            except:
                time.sleep(0.6)
                
        if int(warmupstatus) == 100:
            self.warmupstatus = True
            print('Laser fully warmed up.')
                
    def SetWavelength(self, wavelength):
        """
        To avoid conflict of querying and sending commands at the same time, pause the watchdog in between.
        """
        self.QueryWatchDog.stopflag = True
        time.sleep(2)
        stop = False
        
        while self.QueryWatchDog.isRunning():
            time.sleep(0.2)
            
        while stop == False:
            try:
                self.Laserinstance.SetWavelength(wavelength)
                time.sleep(2)
                stop = True
            except:
                time.sleep(0.5)
                
        #Restart query thread
        self.QueryWatchDog.stopflag = False
        self.QueryWatchDog.start()
        time.sleep(1)
        return self.QueryWatchDog.Status_wavelength
        
    def TurnLaserON(self):
        self.QueryWatchDog.stopflag = True
        time.sleep(2)    
        
        while self.QueryWatchDog.isRunning():
            time.sleep(0.2)
            
        if self.warmupstatus == True:
            print('try to turn on pump laser...')
            self.Laserinstance.Turn_On_PumpLaser()
            
            Status_list = []

            while 'Laser state:RUN' not in Status_list:
                time.sleep(1)
                
                try:
                    Status_list = self.Laserinstance.QueryStatus()
                except:
                    pass
                
                if 'Laser state:RUN'  in Status_list:
                    self.laserRun = True
                    print('Laser state:RUN')
                    break
                
        #Restart query thread
        self.QueryWatchDog.stopflag = False
        self.QueryWatchDog.start()
        time.sleep(1)
            
    def OpenShutter(self):
        self.QueryWatchDog.stopflag = True
        time.sleep(2)
        
        while self.QueryWatchDog.isRunning():
            time.sleep(0.2)
        
        Status_list = []
        Status_list = self.Laserinstance.QueryStatus()
        if 'Tunable beam shutter closed' in Status_list:
            self.Laserinstance.Open_TunableBeamShutter()
            time.sleep(1)
            print('Laser shutter open.')
            
        #Restart query thread
        self.QueryWatchDog.stopflag = False
        self.QueryWatchDog.start()
        time.sleep(1)
        
        # if 'Laser state:RUN'  in self.QueryWatchDog.Status_list:
        #     self.laserRun = True
        
    def CloseShutter(self):
        self.QueryWatchDog.stopflag = True
        time.sleep(2)
        
        while self.QueryWatchDog.isRunning():
            time.sleep(0.2)
        
        Status_list = []
        Status_list = self.Laserinstance.QueryStatus()        
        # Close the shutter.
        if 'Tunable beam shutter open' in Status_list:
            self.Laserinstance.Close_TunableBeamShutter()
            time.sleep(2)
            print('Laser shutter closed.')
        #Restart query thread
        self.QueryWatchDog.stopflag = False
        self.QueryWatchDog.start()
        time.sleep(1)
        
        # if 'Laser state:RUN'  in self.QueryWatchDog.Status_list:
        #     self.laserRun = True
    
    def SetWatchdogTimer(self, WatchdogTimer):
        self.Laserinstance.SetWatchdogTimer(WatchdogTimer)
        
    def StopQueryWatchDog(self):
        self.QueryWatchDog.stopflag = True
        time.sleep(2)
        
        while self.QueryWatchDog.isRunning():
            time.sleep(0.2)
        print('Watchdog running: {}'.format(self.QueryWatchDog.isRunning()))
        
    def TurnLaserOFF(self):
        if self.laserRun == True:
            self.QueryWatchDog.stopflag = True
            time.sleep(2)
            
            while self.QueryWatchDog.isRunning():
                time.sleep(0.2)
            
            if self.QueryWatchDog.isRunning() == False:
                self.Laserinstance.SaveVariables()
                self.Laserinstance.Turn_Off_PumpLaser()
                self.laserRun = False
                
                print('Turn_Off_PumpLaser.')
            
if __name__ == "__main__":
        
    Laserinstance = TwoPhotonExecutor(address = 'COM11', WatchdogFreq = 0.8)
    Laserinstance.InitLaser()
    Laserinstance.CheckWarmup()
    Laserinstance.TurnLaserON()
    
    current_wavelength = Laserinstance.SetWavelength(1280)
    time.sleep(5)
    Laserinstance.OpenShutter()
    time.sleep(5)
    Laserinstance.CloseShutter()
    time.sleep(5)
    current_wavelength = Laserinstance.SetWavelength(900)
    time.sleep(5)
    Laserinstance.OpenShutter()
    time.sleep(5)
    Laserinstance.CloseShutter()
    Laserinstance.TurnLaserOFF()

