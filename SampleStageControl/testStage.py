                         # -*- coding: utf-8 -*-
"""
Created on Mon Feb 18 11:42:50 2019

@author: lhuismans
"""
import time
from stage import LudlStage
#import visa
#First initialize the stage, the correct COM-port has to be specified. I think you can find the COM# under device manager.

ludlStage = LudlStage("COM6")

#ludlStage.send_end='True'
#ludlStage.delay = 0.2
#ludlStage.baud_rate=9600
#ludlStage.read_termination = '\r'
#ludlStage.write_termination='\r'


#Now the stage is initialized functions can be past to it. In the stage.py file each function is explained and it is specified what parameters it takes.
#ludlStage.Joystick(True)
#ludlStage.timeout = 0.1
#ludlStage.delay = 0.1

i= 0
j= 0
ludlStage.moveAbs(i,j)
#ludlStage.moveRel(i,j)
#time.sleep(1)
ii, jj =ludlStage.getPos() #j increase = fov in labview shifts down

row_start = 0
row_end = 3200
column_start = 0
column_end = 3200

step = 1500
position_index=[]
good_position_index = []

for i in range(row_start, row_end, step):
    position_index.append(i)
    for j in range(column_start, column_end, step):
        position_index.append(j)
        print ('-----------------------------------')
        print (position_index)
        
        #stage movement
        ludlStage.moveAbs(i,j)
        time.sleep(1)
        
        k=[i,j]
        x = input('蔷ʅ（´◔౪◔）ʃ薇:')
        if x == 'y':
            good_position_index.append(k)
        
        #input("Press Enter to continue...")
        
        time.sleep(1)
       
        ludlStage.getPos()
        
        
        del position_index[-1]
        print ('---------------^^^^---------------')
    position_index=[]
    
for i in range(len(good_position_index)):
    ludlStage.moveAbs(good_position_index[i][0],good_position_index[i][1])
    input("Press Enter to continue...")
"""
adress = "COM7"
rm = visa.ResourceManager()
time.sleep(5)
ludlStageConnection = rm.open_resource(adress)
command = 'Move X = %d Y = %d' % (0, 0)
print(ludlStageConnection.query(command))
time.sleep(5)
command = 'Move X = %d Y = %d' % (-10000, -10000)
print(ludlStageConnection.query(command))
ludlStageConnection.clear()
"""
#If more functions are needed the programming manual from Ludl has an extensive list of functions that can be provided.
