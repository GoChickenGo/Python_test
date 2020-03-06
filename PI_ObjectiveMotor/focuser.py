# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 14:41:41 2019

@author: xinmeng
"""
import sys
sys.path.append(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\People\Xin Meng\Code\PIPython\PIPython\PIPython-1.3.4.17')
sys.path.append(r'.\Linearstage')

try:
    from pipython import GCSDevice
    from pipython import pitools
except:
    from pipython.pipython import GCSDevice
    from pipython.pipython import pitools 

class PIMotor:

    def __init__(self):
        CONTROLLERNAME = 'C-863.11'
        #STAGES = None
        STAGES = ('M-110.1DG')
        REFMODE = ('FNL')
        
        self.pidevice = GCSDevice()
        print(self.pidevice.EnumerateUSB())
        # InterfaceSetupDlg() is an interactive dialog. There are other methods to
        # connect to an interface without user interaction.
        serialstring = self.pidevice.EnumerateUSB()
    
        #pidevice.InterfaceSetupDlg(key='sample')
        # pidevice.ConnectRS232(comport=1, baudrate=115200)
        self.pidevice.ConnectUSB(serialnum=serialstring[0])
        # pidevice.ConnectTCPIP(ipaddress='192.168.178.42')
    
        # Each PI controller supports the qIDN() command which returns an
        # identification string with a trailing line feed character which
        # we "strip" away.
    
        print('connected: {}'.format(self.pidevice.qIDN().strip()))
    
        # Show the version info which is helpful for PI support when there
        # are any issues.
    
        if self.pidevice.HasqVER():
            print('version info: {}'.format(self.pidevice.qVER().strip()))
    #    allaxes = self.pidevice.qSAI_ALL()
#        return self.pidevice
        
    
    def move(pidevice, target_pos):  
        #pidevice.StopAll()
        #pidevice.SVO(pidevice.axes, [True] * len(pidevice.axes))
        #pitools.waitontarget(pidevice, axes=pidevice.axes)
        
    #            pitools.startup(pidevice, stages=STAGES, refmode=REFMODE)
    
        # Now we query the allowed motion range of all connected stages.
        # GCS commands often return an (ordered) dictionary with axes/channels
        # as "keys" and the according values as "values".
    
        rangemin = list(pidevice.qTMN().values())
        rangemax = list(pidevice.qTMX().values())
        ranges = zip(rangemin, rangemax)
        
        targets = [target_pos]
        pidevice.MOV(pidevice.axes, targets)
        pitools.waitontarget(pidevice)
        positions = pidevice.qPOS(pidevice.axes)
        for axis in pidevice.axes:
            print('position of axis {} = {:.4f}'.format(axis, positions[axis]))
            
        print('Obj movement done')
    #            pidevice.CloseConnection()
    
    def GetCurrentPos(pidevice):
        positions = pidevice.qPOS(pidevice.axes)
        return positions
        
    def CloseMotorConnection(pidevice):
        pidevice.CloseConnection()
    
if __name__ == '__main__':
    # To see what is going on in the background you can remove the following
    # two hashtags. Then debug messages are shown. This can be helpful if
    # there are any issues.

    # import logging
    # logging.basicConfig(level=logging.DEBUG)
    pi = PIMotor()
#    pi_device = pi.ConnectPIMotor
    
    PIMotor.move(pi.pidevice, 3.455)
    PIMotor.CloseMotorConnection(pi.pidevice)

