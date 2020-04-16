# -*- coding: utf-8 -*-
"""
Created on Mon Dec 23 15:10:53 2019

@author: xinmeng
-----------------------------------------------------------Threading class for evolution screening--------------------------------------------------------------------------------
"""
from PyQt5.QtCore import pyqtSignal, QThread
import numpy as np
from SampleStageControl.stage import LudlStage
import time
from PIL import Image
from matplotlib import pyplot as plt
import os
from datetime import datetime
from NIDAQ.generalDaqerThread import (execute_analog_readin_optional_digital_thread, execute_tread_singlesample_analog,
                                execute_tread_singlesample_digital, execute_analog_and_readin_digital_optional_camtrig_thread, DaqProgressBar)
from ImageAnalysis.trymageAnalysis_v3 import ImageAnalysis
import numpy.lib.recfunctions as rfn
from PI_ObjectiveMotor.focuser import PIMotor
from ThorlabsFilterSlider.filterpyserial import ELL9Filter
from InsightX3.TwoPhotonLaser_backend import InsightX3
import math
import threading
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class ScanningExecutionThread(QThread):
    
    ScanningResult = pyqtSignal(np.ndarray, np.ndarray, object, object) #The signal for the measurement, we can connect to this signal
    
    def __init__(self, RoundQueueDict, RoundCoordsDict, GeneralSettingDict, *args, **kwargs):        
        super().__init__(*args, **kwargs)
        self.RoundQueueDict = RoundQueueDict
        self.RoundCoordsDict = RoundCoordsDict
        self.GeneralSettingDict = GeneralSettingDict
        self.Status_list = None
        self.ludlStage = LudlStage("COM12")
        self.watchdog_flag = True
        
        self.PMTimageDict = {}
        for i in range(int(len(self.RoundQueueDict)/2-1)): # initial the nested PMTimageDict dictionary. -2 because default keys for insight and filter.
            self.PMTimageDict['RoundPackage_{}'.format(i+1)] = {}
        self.clock_source = 'Dev1 as clock source' # Should be set by GUI.
        
        self.scansavedirectory = self.GeneralSettingDict['savedirectory']
        self.meshgridnumber = int(self.GeneralSettingDict['Meshgrid'])
        
    def run(self):
        """
        # ==========================================================================================================================================================
        #                                                                       Initialization
        # ==========================================================================================================================================================
        """
#        if len(self.GeneralSettingDict['FocusCorrectionMatrixDict']) > 0:# if focus correction matrix was generated.
        """
        # =============================================================================
        #         connect the Objective motor
        # =============================================================================
        """
        print('----------------------Starting to connect the Objective motor-------------------------')
        self.pi_device_instance = PIMotor()
        print('Objective motor connected.')
        self.errornum = 0
        self.ObjCurrentPos = self.pi_device_instance.pidevice.qPOS(self.pi_device_instance.pidevice.axes)
        
        """
        # =============================================================================
        #         connect the Insight X3
        # =============================================================================
        """        
        if len(self.RoundQueueDict['InsightEvents']) != 0:
            self.Laserinstance = InsightX3('COM11')
            try:
                querygap = 1.1
                # self.Laserinstance.SetWatchdogTimer(0) # Disable the laser watchdog!
#                Status_watchdog_thread = threading.Thread(target = self.Status_watchdog, args=[querygap], daemon=True)
#                Status_watchdog_thread.start() 
                time.sleep(1)
                #-------------Initialize laser--------------
                self.watchdog_flag = False
                time.sleep(0.5)
        
                warmupstatus = 0
                while int(warmupstatus) != 100:
                    try:
                        warmupstatus = self.Laserinstance.QueryWarmupTime()
                        time.sleep(0.6)
                    except:
                        time.sleep(0.6)
                        
                # if int(warmupstatus) == 100:
                #     self.warmupstatus = True
                #     print('Laser fully warmed up.')
                #     if 'Laser state:Ready' in self.Status_list:
                #         self.Laserinstance.Turn_On_PumpLaser()
                #         self.laserRun = True
                #     elif 'Laser state:RUN' in self.Status_list:
                #         self.laserRun = True
                        
                self.watchdog_flag = True
                time.sleep(0.5)
            except:
                print('Laser not connected.')
                
            # If turn on the laser shutter in the beginning
            if 'Shutter_Open' in self.GeneralSettingDict['StartUpEvents']:
                time.sleep(0.5)
                while True:
                    try:
                        self.Laserinstance.Open_TunableBeamShutter()
                        break
                    except:
                        time.sleep(1)
                time.sleep(0.5)                
        
        """
        # ==========================================================================================================================================================
        #                                                                       Execution
        # ==========================================================================================================================================================
        """
   
        GridSequence = 0
        TotalGridNumber = self.meshgridnumber**2
        ScanningMaxCoord = int(np.amax(self.RoundCoordsDict['CoordsPackage_1'])) # Get the largest coordinate
        for EachGrid in range(TotalGridNumber):
            """
            # =============================================================================
            #         For each small repeat unit in the scanning meshgrid
            # =============================================================================
            """
            ScanningGridOffset_Row = int(GridSequence % self.meshgridnumber) * (ScanningMaxCoord + self.GeneralSettingDict['Scanning step']) # Offset coordinate row value for each well.
            ScanningGridOffset_Col = int(GridSequence/self.meshgridnumber) * (ScanningMaxCoord + self.GeneralSettingDict['Scanning step']) # Offset coordinate colunm value for each well.
            GridSequence += 1
            time.sleep(0.5)
            
            for EachRound in range(int(len(self.RoundQueueDict)/2-1)): # EachRound is the round sequence number starting from 0, while the actual number used in dictionary is 1.
                print ('----------------------------------------------------------------------------')            
                print('Below is Grid {}, Round {}.'.format(EachGrid, EachRound+1)) # EachRound+1 is the corresponding round number when setting the dictionary starting from round 1.
                
                """
                # =============================================================================
                #         Unpack the settings for each round
                # =============================================================================
                """
                # Initialize variables
                CoordOrder = 0      # Counter for n th coordinates, for appending cell properties array.      
                CellPropertiesDict = {}
                ND_filter1_Pos = None
                ND_filter2_Pos = None
                EM_filter_Pos = None
                cp_end_index = -1
                self.IndexLookUpCellPropertiesDict = {} #look up dictionary for each cell properties
                
                #-------------Unpack the focus stack information.
                ZStackinfor = self.GeneralSettingDict['FocusStackInfoDict']['RoundPackage_{}'.format(EachRound+1)]
                self.ZStackNum = int(ZStackinfor[ZStackinfor.index('Focus')+5])
                self.ZStackStep = float(ZStackinfor[ZStackinfor.index('Being')+5:len(ZStackinfor)])
                
                #-------------Unpack infor for stage move.
                CoordsNum = int(len(self.RoundCoordsDict['CoordsPackage_{}'.format(EachRound+1)])/2) #Each pos has 2 coords
                
                #-------------Unpack infor for filter event. In the list, the first one is for ND filter and the second one is for emission filter.
                FilterEventIndexList = [i for i,x in enumerate(self.RoundQueueDict['FilterEvents']) if 'Round_{}'.format(EachRound+1) in x]
                
                if len(FilterEventIndexList) > 0:
                    NDposText = self.RoundQueueDict['FilterEvents'][FilterEventIndexList[0]]
                    NDnumber = NDposText[NDposText.index('ToPos_')+6:len(NDposText)]
                    
                    EMposText = self.RoundQueueDict['FilterEvents'][FilterEventIndexList[1]]
                    EMprotein = EMposText[EMposText.index('ToPos_')+6:len(EMposText)]
                    
                    # "COM9" for filter 1 port, which has ND values from 0 to 3.
                    # "COM7" for filter 2 port, which has ND values from 0 to 0.5.
                    if NDnumber == '0':
                        ND_filter1_Pos = 0
                        ND_filter2_Pos = 0
                    elif NDnumber == '1':
                        ND_filter1_Pos = 1
                        ND_filter2_Pos = 0
                    elif NDnumber == '2':
                        ND_filter1_Pos = 2
                        ND_filter2_Pos = 0
                    elif NDnumber == '2.3':
                        ND_filter1_Pos = 2
                        ND_filter2_Pos = 2
                    elif NDnumber == '2.5':
                        ND_filter1_Pos = 2
                        ND_filter2_Pos = 3
                    elif NDnumber == '0.5':
                        ND_filter1_Pos = 0
                        ND_filter2_Pos = 3        
                    elif NDnumber == '0.3':
                        ND_filter1_Pos = 0
                        ND_filter2_Pos = 2
                    
                    if EMprotein == 'Arch':
                        EM_filter_Pos = 0
                    elif EMprotein == 'eGFP':
                        EM_filter_Pos = 1
                    
                #-------------Unpack infor for Insight X3. In the list, the first one is for shutter event and the second one is for wavelength event. 
                InsightX3EventIndexList = [i for i,x in enumerate(self.RoundQueueDict['InsightEvents']) if 'Round_{}'.format(EachRound+1) in x]
                
                """
                # =============================================================================
                #         Execute Insight event at the beginning of each round
                # =============================================================================
                """            
                if len(InsightX3EventIndexList) == 1:
                    print(InsightX3EventIndexList)
                    InsightText = self.RoundQueueDict['InsightEvents'][InsightX3EventIndexList[0]]
                    if 'Shutter_Open' in InsightText:
                        self.watchdog_flag = False
                        time.sleep(0.5)
                        while True:
                            try:
                                self.Laserinstance.Open_TunableBeamShutter()
                                break
                            except:
                                time.sleep(1)
                        time.sleep(0.5)
                        print('Laser shutter open.')
                        self.watchdog_flag = True
                        time.sleep(0.5)
    
                    elif 'Shutter_Close' in InsightText:
                        self.watchdog_flag = False
                        time.sleep(0.5)
                        while True:
                            try:
                                self.Laserinstance.Close_TunableBeamShutter()
                                break
                            except:
                                time.sleep(1)
                        time.sleep(0.5)
                        print('Laser shutter closed.')
                        self.watchdog_flag = True
                        time.sleep(0.5)
                    elif 'WavelengthTo' in InsightText:
                        self.watchdog_flag = False
                        time.sleep(0.5)
                        TargetWavelen = int(InsightText[InsightText.index('To_')+3:len(InsightText)])
                        print(TargetWavelen)
                        while True:
                            try:
                                self.Laserinstance.SetWavelength(TargetWavelen)
                                break
                            except:
                                time.sleep(1)
                        time.sleep(5)
                        self.watchdog_flag = True
                        time.sleep(0.5)
                        
                elif len(InsightX3EventIndexList) == 2:
                    
                    InsightText_wl = self.RoundQueueDict['InsightEvents'][InsightX3EventIndexList[1]]
                    InsightText_st = self.RoundQueueDict['InsightEvents'][InsightX3EventIndexList[0]]
                    
                    if 'WavelengthTo' in InsightText_wl and 'Shutter_Open' in InsightText_st:
                        self.watchdog_flag = False
                        time.sleep(0.5)
                        TargetWavelen = int(InsightText_wl[InsightText_wl.index('To_')+3:len(InsightText_wl)])
                        while True:
                            try:
                                self.Laserinstance.SetWavelength(TargetWavelen)
                                break
                            except:
                                time.sleep(1)
                        time.sleep(5)
                        while True:
                            try:
                                self.Laserinstance.Open_TunableBeamShutter()
                                break
                            except:
                                time.sleep(1)
                        print('Laser shutter open.')
                        self.watchdog_flag = True
                        time.sleep(0.5)
                        
                    elif 'WavelengthTo' in InsightText_wl and 'Shutter_Close' in InsightText_st:
                        self.watchdog_flag = False
                        time.sleep(0.5)
                        TargetWavelen = int(InsightText_wl[InsightText_wl.index('To_')+3:len(InsightText_wl)])
                        while True:
                            try:                        
                                self.Laserinstance.SetWavelength(TargetWavelen)
                                break
                            except:
                                time.sleep(1)
                        time.sleep(5)
                        while True:
                            try:
                                self.Laserinstance.Close_TunableBeamShutter()
                                break
                            except:
                                time.sleep(1)
                        time.sleep(1)
                        print('Laser shutter closed.')
                        self.watchdog_flag = True
                        time.sleep(0.5)
                        
                    time.sleep(2)
                    
                """
                # =============================================================================
                #         Execute filter event at the beginning of each round
                # =============================================================================
                """            
                if ND_filter1_Pos != None and ND_filter2_Pos != None:
                    #Move filter 1
                    self.filter1 = ELL9Filter("COM9")
                    self.filter1.moveToPosition(ND_filter1_Pos)
                    time.sleep(1)
                    #Move filter 2
                    self.filter2 = ELL9Filter("COM7")
                    self.filter2.moveToPosition(ND_filter2_Pos)
                    time.sleep(1)
                if EM_filter_Pos != None:
                    self.filter3 = ELL9Filter("COM15")
                    self.filter3.moveToPosition(EM_filter_Pos)
                    time.sleep(1)
    
                    
                self.currentCoordsSeq = 0
                for EachCoord in range(CoordsNum):
                    """
                    #------------------------------------------At each stage position:-------------------------------------------
                    """
                    self.error_massage = None
                    
                    self.currentCoordsSeq += 1
                    
                    """
                    # =============================================================================
                    #         Stage movement
                    # =============================================================================
                    """
                    RowIndex = int(self.RoundCoordsDict['CoordsPackage_{}'.format(EachRound+1)][EachCoord*2:EachCoord*2+2][0]) + ScanningGridOffset_Row
                    ColumnIndex = int(self.RoundCoordsDict['CoordsPackage_{}'.format(EachRound+1)][EachCoord*2:EachCoord*2+2][1]) + ScanningGridOffset_Col
    
                    try:
                        self.ludlStage.moveAbs(RowIndex,ColumnIndex) # Row/Column indexs of np.array are opposite of stage row-col indexs.
                    except:
                        self.error_massage = 'Fail_MoveStage'
                        self.errornum += 1
                        print('Stage move failed! Error number: {}'.format(int(self.errornum)))
                    
                    print ('Round {}. Current index: {}.'.format(EachRound+1, [RowIndex,ColumnIndex]))

                    time.sleep(1)
                    
                    """
                    # =============================================================================
                    #         Get the z stack objective positions ready
                    # =============================================================================
                    """
                    #-------------------------------------------If focus correction applies----------------------------------------
                    if len(self.GeneralSettingDict['FocusCorrectionMatrixDict']) > 0:
                        FocusPosArray = self.GeneralSettingDict['FocusCorrectionMatrixDict']['RoundPackage_{}_Grid_{}'.format(EachRound+1, EachGrid)]
    #                    print(FocusPosArray)
                        FocusPosArray = FocusPosArray.flatten('F')
                        FocusPos_fromCorrection = FocusPosArray[EachCoord]
                        print('Target focus pos: '.format(FocusPos_fromCorrection))
                    
                    # Without focus correction
                    if len(self.GeneralSettingDict['FocusCorrectionMatrixDict']) == 0:
                        ZStacklinspaceStart = self.ObjCurrentPos['1'] - (math.floor(self.ZStackNum/2)-1)*self.ZStackStep
                        ZStacklinspaceEnd = self.ObjCurrentPos['1'] + (self.ZStackNum - math.floor(self.ZStackNum/2))*self.ZStackStep
                    # With focus correction
                    elif len(self.GeneralSettingDict['FocusCorrectionMatrixDict']) > 0:
                        ZStacklinspaceStart = FocusPos_fromCorrection - (math.floor(self.ZStackNum/2)-1)*self.ZStackStep
                        ZStacklinspaceEnd = FocusPos_fromCorrection + (self.ZStackNum - math.floor(self.ZStackNum/2))*self.ZStackStep                    
                        
                    ZStackPosList = np.linspace(ZStacklinspaceStart, ZStacklinspaceEnd, num = self.ZStackNum)       
                    print(ZStackPosList)
                    
                    """
                    # =============================================================================
                    #         Execute waveform packages
                    # =============================================================================
                    """
                    self.WaveforpackageNum = int(len(self.RoundQueueDict['RoundPackage_{}'.format(EachRound+1)]))
                    #Execute each individual waveform package
                    print('*******************************************Round {}. Current index: {}.**************************************************'.format(EachRound+1, [RowIndex,ColumnIndex]))
                    for EachZStackPos in range(self.ZStackNum): # Move to Z stack focus 
                        print('--------------------------------------------Stack {}--------------------------------------------------'.format(EachZStackPos+1))
                        if self.ZStackNum > 1:
                            self.ZStackOrder = int(EachZStackPos +1) # Here the first one is 1, not starting from 0.
                            FocusPos = ZStackPosList[EachZStackPos]
                            print('Target focus pos: {}'.format(FocusPos))
    
                            pos = PIMotor.move(self.pi_device_instance.pidevice, FocusPos)
                            self.ObjCurrentPosInStack = self.pi_device_instance.pidevice.qPOS(self.pi_device_instance.pidevice.axes)
                            print("Current position: {:.4f}".format(self.ObjCurrentPosInStack['1']))
                            
                            time.sleep(0.3)
                        else:
                            self.ZStackOrder = 1
                        
                        for EachWaveform in range(self.WaveforpackageNum):
                            WaveformPackageToBeExecute = self.RoundQueueDict['RoundPackage_{}'.format(EachRound+1)]['WaveformPackage_{}'.format(EachWaveform+1)]
                            WaveformPackageGalvoInfor = self.RoundQueueDict['GalvoInforPackage_{}'.format(EachRound+1)]['GalvoInfor_{}'.format(EachWaveform+1)]  
                            self.readinchan = WaveformPackageToBeExecute[3]
                            self.RoundWaveformIndex = [EachRound+1, EachWaveform+1] # first is current round number, second is current waveform package number.
                            self.CurrentPosIndex = [RowIndex, ColumnIndex]
    #                        self.ProcessData_executed = False
                            
                            if WaveformPackageGalvoInfor != 'NoGalvo': # Unpack the information of galvo scanning.
                                self.readinchan = WaveformPackageGalvoInfor[0]
                                self.repeatnum = WaveformPackageGalvoInfor[1]
                                self.PMT_data_index_array = WaveformPackageGalvoInfor[2]
                                self.averagenum = WaveformPackageGalvoInfor[3]
                                self.lenSample_1 = WaveformPackageGalvoInfor[4]
                                self.ScanArrayXnum = WaveformPackageGalvoInfor[5]
        
                            if self.clock_source == 'Dev1 as clock source':
                                self.adcollector = execute_analog_readin_optional_digital_thread()
                                self.adcollector.set_waves(WaveformPackageToBeExecute[0], WaveformPackageToBeExecute[1], WaveformPackageToBeExecute[2], WaveformPackageToBeExecute[3]) #[0] = sampling rate, [1] = analogcontainer_array, [2] = digitalcontainer_array, [3] = readinchan
                                self.adcollector.collected_data.connect(self.ProcessData)
                                self.adcollector.run()
                                #self.ai_dev_scaling_coeff = self.adcollector.get_ai_dev_scaling_coeff()
                            elif self.clock_source == 'Cam as clock source' :
                                self.adcollector = execute_analog_and_readin_digital_optional_camtrig_thread()
                                self.adcollector.set_waves(WaveformPackageToBeExecute[0], WaveformPackageToBeExecute[1], WaveformPackageToBeExecute[2], WaveformPackageToBeExecute[3])
                                self.adcollector.collected_data.connect(self.ProcessData)
                                self.adcollector.run()
                                
                            
                        time.sleep(0.6) # Wait for receiving data to be done.
                    time.sleep(0.3)
                    print('*************************************************************************************************************************')

        """
        # ==========================================================================================================================================================
        #                                                                       Finalizing
        # ==========================================================================================================================================================
        """                
        
        # Switch off laser
        if len(self.RoundQueueDict['InsightEvents']) != 0:
            self.watchdog_flag = False
            time.sleep(0.5)
            
            self.Laserinstance.Close_TunableBeamShutter()
            time.sleep(0.5)
            self.Laserinstance.SaveVariables()
            while True:
                try:                        
                    self.Laserinstance.Turn_Off_PumpLaser()
                    break
                except:
                    time.sleep(1)
        
        # Disconnect focus motor
        try:
            PIMotor.CloseMotorConnection(self.pi_device_instance.pidevice)
            print('Objective motor disconnected.')
        except:
            pass
    #--------------------------------------------------------------Reconstruct and save images from 1D recorded array.--------------------------------------------------------------------------------       
    def ProcessData(self, data_waveformreceived):    
        print('ZStackOrder is:'+str(self.ZStackOrder)+'numis_'+str(self.ZStackNum))
        self.adcollector.save_as_binary(self.scansavedirectory)
        
        self.channel_number = len(data_waveformreceived)
        if self.channel_number == 1:            
            if 'Vp' in self.readinchan:
                pass
            elif 'Ip' in self.readinchan:
                pass
            elif 'PMT' in self.readinchan:  # repeatnum, PMT_data_index_array, averagenum, ScanArrayXnum

                self.data_collected_0 = data_waveformreceived[0]*-1
                self.data_collected_0 = self.data_collected_0[0:len(self.data_collected_0)-1]
                print(len(self.data_collected_0))                
                for imageSequence in range(self.repeatnum):
                    
                    try:
                        self.PMT_image_reconstructed_array = self.data_collected_0[np.where(self.PMT_data_index_array == imageSequence+1)]
#                        if imageSequence == int(self.repeatnum)-1:
#                            self.PMT_image_reconstructed_array = self.PMT_image_reconstructed_array[0:len(self.PMT_image_reconstructed_array)-1] # Extra one sample at the end.
#                        print(self.PMT_image_reconstructed_array.shape)
                        Dataholder_average = np.mean(self.PMT_image_reconstructed_array.reshape(self.averagenum, -1), axis=0)
#                        print(Dataholder_average.shape)
                        Value_yPixels = int(self.lenSample_1/self.ScanArrayXnum)
                        self.PMT_image_reconstructed = np.reshape(Dataholder_average, (Value_yPixels, self.ScanArrayXnum))
                        
                        self.PMT_image_reconstructed = self.PMT_image_reconstructed[:, 50:550] # Crop size based on: M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Xin\2019-12-30 2p beads area test 4um
#                        self.PMT_image_reconstructed = self.PMT_image_reconstructed[:, 70:326] # for 256*256 images
                        #---------------------------------------------For multiple images in one z pos, Stack the arrays into a 3d array--------------------------------------------------------------------------
                        if imageSequence == 0:
                            self.PMT_image_reconstructed_stack = self.PMT_image_reconstructed[np.newaxis, :, :] # Turns into 3d array
                        else:
                            self.PMT_image_reconstructed_stack = np.concatenate((self.PMT_image_reconstructed_stack, self.PMT_image_reconstructed[np.newaxis, :, :]), axis=0)
                            print(self.PMT_image_reconstructed_stack.shape)
                        #---------------------------------------------Calculate the z max projection-----------------------------------------------------------------------
                        if self.repeatnum == 1: # Consider one repeat image situlation 
                            if self.ZStackNum > 1:
                                if self.ZStackOrder == 1:
                                    self.PMT_image_maxprojection_stack = self.PMT_image_reconstructed[np.newaxis, :, :]

                                else:

                                    self.PMT_image_maxprojection_stack = np.concatenate((self.PMT_image_maxprojection_stack, self.PMT_image_reconstructed[np.newaxis, :, :]), axis=0)

                            else:
                                self.PMT_image_maxprojection_stack = self.PMT_image_reconstructed[np.newaxis, :, :]
                        # Save the max projection image
                        if self.ZStackOrder == self.ZStackNum:
                            self.PMT_image_maxprojection = np.max(self.PMT_image_maxprojection_stack, axis=0)
                            
                            LocalimgZprojection = Image.fromarray(self.PMT_image_maxprojection) #generate an image object
                            LocalimgZprojection.save(os.path.join(self.scansavedirectory, 'Round'+str(self.RoundWaveformIndex[0])+'_Coords'+str(self.currentCoordsSeq)+'_R'+str(self.CurrentPosIndex[0])+'C'+str(self.CurrentPosIndex[1])+'_PMT_'+str(imageSequence)+'Zmax'+'.tif')) #save as tif                            
#                            
                        Localimg = Image.fromarray(self.PMT_image_reconstructed) #generate an image object
                        Localimg.save(os.path.join(self.scansavedirectory, 'Round'+str(self.RoundWaveformIndex[0])+'_Coords'+str(self.currentCoordsSeq)+'_R'+str(self.CurrentPosIndex[0])+'C'+str(self.CurrentPosIndex[1])+'_PMT_'+str(imageSequence)+'Zpos'+str(self.ZStackOrder)+'.tif')) #save as tif
                        
                        plt.figure()
                        plt.imshow(self.PMT_image_reconstructed, cmap = plt.cm.gray) # For reconstructed image we pull out the first layer, getting 2d img.
                        plt.show()
                    except:
                        print('No.{} image failed to generate.'.format(imageSequence))
                    
        elif self.channel_number == 2: 
            if 'PMT' not in self.readinchan:
                pass
            elif 'PMT' in self.readinchan:

                self.data_collected_0 = data_waveformreceived[0]*-1
                self.data_collected_0 = self.data_collected_0[0:len(self.data_collected_0)-1]
                print(len(self.data_collected_0)) 
                for imageSequence in range(self.repeatnum):
                    try:
                        self.PMT_image_reconstructed_array = self.data_collected_0[np.where(self.PMT_data_index_array == imageSequence+1)]
                        if imageSequence == int(self.repeatnum)-1:
                            self.PMT_image_reconstructed_array = self.PMT_image_reconstructed_array[0:len(self.PMT_image_reconstructed_array)-1] # Extra one sample at the end.

                        Dataholder_average = np.mean(self.PMT_image_reconstructed_array.reshape(self.averagenum, -1), axis=0)
                        Value_yPixels = int(self.lenSample_1/self.ScanArrayXnum)
                        self.PMT_image_reconstructed = np.reshape(Dataholder_average, (Value_yPixels, self.ScanArrayXnum))
                        
                        self.PMT_image_reconstructed = self.PMT_image_reconstructed[:, 50:550]
                        
                        # Stack the arrays into a 3d array
                        if imageSequence == 0:
                            self.PMT_image_reconstructed_stack = self.PMT_image_reconstructed[np.newaxis, :, :]
                        else:
                            self.PMT_image_reconstructed_stack = np.concatenate((self.PMT_image_reconstructed_stack, self.PMT_image_reconstructed[np.newaxis, :, :]), axis=0)
                        
                        #---------------------------------------------Calculate the z max projection-----------------------------------------------------------------------
                        if self.repeatnum == 1: # Consider one repeat image situlation 
                            if self.ZStackNum > 1:
                                if self.ZStackOrder == 1:
                                    self.PMT_image_maxprojection_stack = self.PMT_image_reconstructed[np.newaxis, :, :]
                                else:
                                    self.PMT_image_maxprojection_stack = np.concatenate((self.PMT_image_maxprojection_stack, self.PMT_image_reconstructed[np.newaxis, :, :]), axis=0)
                            else:
                                self.PMT_image_maxprojection_stack = self.PMT_image_reconstructed[np.newaxis, :, :]
                        # Save the max projection image
                        if self.ZStackOrder == self.ZStackNum:
                            self.PMT_image_maxprojection = np.max(self.PMT_image_maxprojection_stack, axis=0)
                            
                            LocalimgZprojection = Image.fromarray(self.PMT_image_maxprojection) #generate an image object
                            LocalimgZprojection.save(os.path.join(self.scansavedirectory, 'Round'+str(self.RoundWaveformIndex[0])+'_Coords'+str(self.currentCoordsSeq)+'_R'+str(self.CurrentPosIndex[0])+'C'+str(self.CurrentPosIndex[1])+'_PMT_'+str(imageSequence)+'Zmax'+'.tif')) #save as tif                            
                        
                        Localimg = Image.fromarray(self.PMT_image_reconstructed) #generate an image object
                        Localimg.save(os.path.join(self.scansavedirectory, 'Round'+str(self.RoundWaveformIndex[0])+'_Coords'+str(self.currentCoordsSeq)+'_R'+str(self.CurrentPosIndex[0])+'C'+str(self.CurrentPosIndex[1])+'_PMT_'+str(imageSequence)+'Zpos'+str(self.ZStackOrder)+'.tif')) #save as tif
                        
                        plt.figure()
                        plt.imshow(self.PMT_image_reconstructed, cmap = plt.cm.gray)
                        plt.show()
                    except:
                        print('No.{} image failed to generate.'.format(imageSequence))

#        self.PMTimageDict['RoundPackage_{}'.format(self.RoundWaveformIndex[0])]['row_{}_column_{}'.format(self.CurrentPosIndex[0], self.CurrentPosIndex[1])] = self.PMT_image_maxprojection
                 
#        self.PMTimageDict['RoundPackage_{}'.format(self.RoundWaveformIndex[0])]['row_{}_column_{}_stack{}'.format(self.CurrentPosIndex[0], self.CurrentPosIndex[1], self.ZStackOrder)] = self.PMT_image_reconstructed_stack
#        self.ProcessData_executed = True
        print('ProcessData executed.')
        
    #-----------------------------------------------------------------Sorting the cells------------------------------------------------------------------------------------------------------------
#    def SortingPropertiesArray(self, All_cell_properties):  
#        #------------------------------------------CAN use 'import numpy.lib.recfunctions as rfn' to append field--------------
#        original_cp = rfn.append_fields(All_cell_properties, 'Original_sequence', list(range(0, len(All_cell_properties))), usemask=False)
#        #print('*********************sorted************************')        
#        sortedcp = self.ImageAnalysisInstance.sort_using_weight(original_cp, 'Mean intensity in contour','Contour soma ratio','Change', self.GeneralSettingDict['Mean intensity in contour weight'], self.GeneralSettingDict['Contour soma ratio weight'], self.GeneralSettingDict['Change weight'])
#        #******************************Add ranking to it*********************************
#        ranked_cp = rfn.append_fields(sortedcp, 'Ranking', list(range(0, len(All_cell_properties))), usemask=False)
#        #print('***********************Original sequence with ranking**************************')        
#        withranking_cp = np.sort(ranked_cp, order='Original_sequence')
#       
#        # All the cells are ranked, now we find the desired group and their position indexs, call the images and show labels of
#        # these who meet the requirements, omitting bad ones.
#        
#        #get the index
#        cell_properties_selected_hits = ranked_cp[0:self.GeneralSettingDict['selectnum']]
#        cell_properties_selected_hits_index_sorted = np.sort(cell_properties_selected_hits, order=['Row index', 'Column index'])
#        index_samples = np.vstack((cell_properties_selected_hits_index_sorted['Row index'],cell_properties_selected_hits_index_sorted['Column index']))
#        
#        merged_index_samples = index_samples[:,0] # Merge coordinates which are the same.
#
#        #consider these after 1st one
#        for i in range(1, len(index_samples[0])):
#            #print(index_samples[:,i][0] - index_samples[:,i-1][0])    
#            if index_samples[:,i][0] != index_samples[:,i-1][0] or index_samples[:,i][1] != index_samples[:,i-1][1]: 
#                merged_index_samples = np.append(merged_index_samples, index_samples[:,i], axis=0)
#        merged_index_samples = merged_index_samples.reshape(-1, 2) # 1st column=i, 2nd column=j
#        
#        return withranking_cp, merged_index_samples
    
#    def GetDataForShowingRank(self):
#        return self.RankedAllCellProperties, self.FinalMergedCoords, self.IndexLookUpCellPropertiesDict, self.PMTimageDict
    #----------------------------------------------------------------WatchDog for laser----------------------------------------------------------------------------------
    def Status_watchdog(self, querygap):
        
        while True:
            if self.watchdog_flag == True:
                self.Status_list = self.Laserinstance.QueryStatus()
                time.sleep(querygap)
            else:
                print('Watchdog stopped')
                time.sleep(querygap)
            
    
class ShowTopCellsThread(QThread):
    
    PMTimageDictMeasurement = pyqtSignal(object) #The signal for the measurement, we can connect to this signal
    
    def __init__(self, GeneralSettingDict, RankedAllCellProperties, FinalMergedCoords, IndexLookUpCellPropertiesDict, PMTimage, MatdisplayFigureTopGuys, *args, **kwargs):        
        super().__init__(*args, **kwargs)
        self.GeneralSettingDict = GeneralSettingDict
        self.RankedAllCellProperties = RankedAllCellProperties
        self.CurrentPos = FinalMergedCoords
        self.IndexLookUpCellPropertiesDict = IndexLookUpCellPropertiesDict
        self.ShowTopCellImg = PMTimage
        self.MatdisplayFigureTopGuys = MatdisplayFigureTopGuys
        
        self.IndexLookUpCellPropertiesDictRow = self.IndexLookUpCellPropertiesDict['row_{}_column_{}'.format(self.CurrentPos[0], self.CurrentPos[1])][0]
        self.IndexLookUpCellPropertiesDictCol = self.IndexLookUpCellPropertiesDict['row_{}_column_{}'.format(self.CurrentPos[0], self.CurrentPos[1])][1]
        
        self.ludlStage = LudlStage("COM6")
    def run(self):
        self.TopCellAx = self.MatdisplayFigureTopGuys.add_subplot(111)

        print ('-----------------------------------')
        
        #stage movement
        self.ludlStage.moveAbs(self.CurrentPos[0],self.CurrentPos[1])
        time.sleep(1)
                        
        S = ImageAnalysis(self.ShowTopCellImg, self.ShowTopCellImg) #The same as ImageAnalysis(Data_dict_0[Pic_name], Data_dict_1[Pic_name]), call the same image with same dictionary index.
        v1, v2, mask_1, mask_2, thres = S.applyMask(self.GeneralSettingDict['openingfactor'], 
                                                    self.GeneralSettingDict['closingfactor'], 
                                                    self.GeneralSettingDict['binary_adaptive_block_size'])
        S.showlabel_with_rank_givenAx(self.GeneralSettingDict['smallestsize'], mask_1, v1, self.IndexLookUpCellPropertiesDictRow, self.IndexLookUpCellPropertiesDictCol, self.RankedAllCellProperties, 'Mean intensity in contour', self.GeneralSettingDict['selectnum'], self.TopCellAx)

        print ('-----------------------------------')

        

        