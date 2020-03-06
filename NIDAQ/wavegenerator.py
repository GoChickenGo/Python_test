from __future__ import division
import numpy as np
import matplotlib.pyplot as plt
import math

from NIDAQ.constants import HardwareConstants

def xValuesSingleSawtooth(sampleRate = 1000, voltXMin = 0, voltXMax = 5, xPixels = 1024, sawtooth = True):
    """
    This function generates the xValues for !!!ONE PERIOD!!! of the sawtooth/triangle wave.
    
    First part: linearly moving up
    Second part: accelerating to the rampdown speed (maximum galvo speed for sawtooth)
    Third part: linearly moving down
    Fourth part: accelerating to rampup speed
    """
    #---------Defining standard variables------------
    constants = HardwareConstants()
    speedGalvo = constants.maxGalvoSpeed #Volt/s
    aGalvo = constants.maxGalvoAccel #Acceleration galvo in volt/s^2
    aGalvoPix = aGalvo/(sampleRate**2) #Acceleration galvo in volt/pixel^2
    xArray = np.array([]) #Array for x voltages
    rampUpSpeed = (voltXMax-voltXMin)/xPixels #Ramp up speed in volt/pixel
    rampDownSpeed = -speedGalvo/sampleRate #Ramp down speed in volt/pixel (Default sawtooth)
    
    #-----------Checking for triangle wave-----------
    if sawtooth == False:
        rampDownSpeed = -rampUpSpeed 
    
    #---------------------------------------------------------------------------
    #---------------------------x pixel wave function---------------------------
    #---------------------------------------------------------------------------
    
    #-----------Defining the ramp up (x)------------
    rampUp = np.linspace(voltXMin, voltXMax, xPixels)
    xArray = np.append(xArray, rampUp) #Adding the voltage values for the ramp up
    
    #-----------Defining the inertial part-------------
    inertialPart = np.array([]) #Making a temporary array for storing the voltage values of the inertial part
    vIn = rampUpSpeed #Speed of "incoming" ramp (volt/pixel)
    vOut = rampDownSpeed #Speed of "outgoing" ramp (volt/pixel)
    a = -aGalvoPix #Acceleration in volt/pixel^2
    timespanInertial = abs(math.floor((vOut-vIn)/a)) #Calculating the timespan needed
    t = np.arange(timespanInertial)
    inertialPart = 0.5*a*t[1::]**2+vIn*t[1::]+xArray[-1] #Making the array with the voltage values, we are not taking into acount the first value as this is the value of the previous sample
    xArray = np.append(xArray, inertialPart) #Adding the array to the total path
    
    if sawtooth == False:
        lineSizeStepFunction = xArray.size #Defining the linesize for the yArray in case of a triangle wave
    
    #----------Defining the ramp down----------------
    a = aGalvoPix
    startVoltage = xArray[-1]+rampDownSpeed
    #We calculate the endvoltage by using the timespan for the intertial part and 
    #the starting voltage
    endVoltage = 0.5*a*timespanInertial**2-rampUpSpeed*timespanInertial+voltXMin
    
    if sawtooth == True:
        timespanRampDown = abs(math.ceil((endVoltage-startVoltage)/rampDownSpeed))
        rampDownSpeed = (endVoltage-startVoltage)/timespanRampDown #Above line changed the rampDownSpeed so we have to recalculate
    else:
        timespanRampDown = rampUp.size #If it is a triangle wave the ramp down part should be as big as the ramp up part
        
    rampDown = np.linspace(startVoltage, endVoltage, timespanRampDown) #Specifying the linear path
    xArray = np.append(xArray, rampDown) #Adding the array to the total path
    
    #----------Defining the second inertial part-------------
    inertialPart2 = np.array([])
    vIn = rampDownSpeed #Speed of "incoming" ramp (volt/pixel)
    a = aGalvoPix #Acceleration in volt/pixel^2
    inertialPart2 = 0.5*a*t[1::]**2+vIn*t[1::]+xArray[-1] #We can use the same time units as the first inertial part but not including the last value, as this is part of the next iteration
    xArray = np.append(xArray, inertialPart2)
    
    if sawtooth == True:
        lineSizeStepFunction = xArray.size
    
    return xArray, lineSizeStepFunction

def yValuesFullSawtooth(sampleRate, voltYMin, voltYMax, xPixels, yPixels, lineSize):
    """
    This functiong generates the !!!FULL!!! yArray (stepfunction) for the sawtooth or triangle wave.
    
    lineSize defines the length of each step.
    For the trianglewave this is ~half the wavelength and for the sawtooth it is 
    the full wavelength. 
    """
    stepSize = (voltYMax-voltYMin)/yPixels
    
    #Creating the 'stairs'
    extendedYArray = np.ones(xPixels)*voltYMin #The first line is created manually as this is shorter
                                            #The step is starting at the beginning of the intertial part
    for i in np.arange(yPixels-1)+1:
        extendedYArray = np.append(extendedYArray, np.ones(lineSize)*i*stepSize+voltYMin)
    
    extraPixels = (lineSize*yPixels-extendedYArray.size) #Some extra pixels are needed to make x and y the same size
    extendedYArray = np.append(extendedYArray, np.ones(extraPixels)*voltYMin)
    
    return extendedYArray
    """
    #Creating the swing back (for multiple frames)
    inertialPart = np.array([]) #Making a temporary array for storing the voltage values of the inertial part
    vIn = 0 #Speed of "incoming" ramp (volt/pixel)
    vOut = -speedGalvo/sRate #Speed of "outgoing" ramp (volt/pixel)
    a = -aGalvoPix #Acceleration in volt/pixel^2
    timespanInertial = abs(math.floor((vOut-vIn)/a)) #Calculating the timespan needed
    t = np.arange(timespanInertial)
    inertialPart = 0.5*a*t[1::]**2+vIn*t[1::]+xArray[-1] #Making the array with the voltage values, we are not taking into acount the first value as this is the value of the previous sample
    xArray = np.append(xArray, inertialPart) #Adding the array to the total path
    """

def rotateXandY(xArray, yArray, voltXMin, voltXMax, voltYMin, voltYMax, imAngle):
    """
    Rotates x and corresponding y array for galvos around its center point.
    """
    radAngle = math.pi/180*imAngle #Converting degrees to radians
    
    #Shifting to the center
    xArray = xArray-((voltXMax-voltXMin)/2+voltXMin)
    yArray = yArray-((voltYMax-voltYMin)/2+voltYMin)
    
    #Converting the x and y arrays
    rotatedXArray = xArray*math.cos(radAngle)-yArray*math.sin(radAngle)
    rotatedYArray = xArray*math.sin(radAngle)+yArray*math.cos(radAngle)
    
    #Shifting it back
    finalXArray = rotatedXArray+((voltXMax-voltXMin)/2+voltXMin)
    finalYArray = rotatedYArray+((voltYMax-voltYMin)/2+voltYMin)
    
    return finalXArray, finalYArray

def repeatWave(wave, repeats):
    """
    Repeats the wave a set number of times and returns a new repeated wave.
    """
    extendedWave = np.array([])
    for i in range(repeats):
        extendedWave = np.append(extendedWave, wave)
    return extendedWave

def waveRecPic(sampleRate = 4000, imAngle = 0, voltXMin = 0, voltXMax = 5, 
                 voltYMin = 0, voltYMax = 5, xPixels = 1024, yPixels = 512, 
                 sawtooth = True):
    """
    Generates a the x and y values for making rectangular picture with a scanning laser.
    """
    xArray, lineSize = xValuesSingleSawtooth(sampleRate, voltXMin, voltXMax, xPixels, sawtooth)
    yArray = yValuesFullSawtooth(sampleRate, voltYMin, voltYMax, xPixels, yPixels, lineSize)
    
    #Looping it to get the desired amount of periods for x
    if sawtooth == True:
        extendedXArray = repeatWave(xArray, yPixels)
    else:
        repeats = int(math.ceil(yPixels/2))
        extendedXArray = repeatWave(xArray, repeats)
        
        #Checking if we should remove the last ramp down    
        if yPixels%2 == 1: 
            extendedXArray = extendedXArray[0:-lineSize]
    
    #Rotatin
    finalX, finalY = rotateXandY(extendedXArray, yArray, voltXMin, voltXMax, voltYMin,
                                 voltYMax, imAngle)
    return finalX, finalY

def blockWave(sampleRate, frequency, voltMin, voltMax, dutycycle):
    """
    Generates a one period blockwave. 
    sampleRate      samplerate set on the DAQ (int)
    frequency       frequency you want for the block wave (int)
    voltMin         minimum value of the blockwave (float)
    voltMax         maximum value of the blockwave (float)
    dutycycle       duty cycle of the wave (wavelength at voltMax) (float)
    """
    wavelength = int(sampleRate/frequency) #Wavelength in number of samples
    #The high values 
    high = np.ones(math.ceil(wavelength*dutycycle))*voltMax
    #Low values
    low = np.ones(math.floor(wavelength*(1-dutycycle)))*voltMin
    #Adding them
    return np.append(high, low)
    
def testSawtooth():
    sRate = 2000000
    imAngle = 0
    VxMax = 4
    VxMin = 0.
    VyMax = 10
    VyMin = 2
    xPixels = 1024
    yPixels = 1
    sawtooth = True
    
    xValues, yValues = waveRecPic(sRate, imAngle, VxMin, VxMax, VyMin, VyMax, 
                                                    xPixels, yPixels, sawtooth)
                                                    
    plt.plot(np.arange(xValues.size), xValues)
    plt.plot(np.arange(yValues.size), yValues)
    plt.show()