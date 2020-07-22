#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  4 12:29:32 2020

@author: Izak de Heer

This code is used to create two binary images for image registration without 
any hardware connected. One image is the theoretical DMD pattern, the other the
theoretical image captured by the camera. The image captured by the camera
should be diffraction-limited, however for the sake of simplicity this is 
ignored initially. The purpose of this simplification is implementing the code
to find the transformation from camera to DMD coordinates without dealing with
diffraction-limited spots. 

"""

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import skimage.draw as skd

def writePositionsToFile(file, *args):
    
    for i in range(len(args)):
        file.write(str(args[i][0])+','+str(args[i][1])+'\n')


def circlePatterns(*args):
    c = np.array((args))
    for i in range(3):
        array = np.zeros([1024,768])
    
        array[skd.draw.circle(c[i,0],c[i,1],40)] = 255
        
        pattern = Image.fromarray(array)
        pattern = pattern.convert("L")
        
        pattern.save("./../Registration_Images/registration_mask_"+str(i)+".png","PNG")
        
        file = open('./../Registration_Images/positions.txt', 'w')
        writePositionsToFile(file, p1, p2, p3)
        file.close()

def touchingSquarePatterns(sigma, *args):
    """
    Function for easy plotting of points to get sense of the distribution of 
    points. Input argument can be any number of two-value arrays, representing
    x and y coordinate pairs. 
    """
    c = np.array((args))
    for i in range(3):
        array = np.zeros([1024,768])    
        array[skd.draw.rectangle((c[i,0]-sigma, c[i,1]-sigma), (c[i,0],c[i,1]))] = 255
        array[skd.draw.rectangle((c[i,0]+sigma, c[i,1]+sigma), (c[i,0],c[i,1]))] = 255
        
        pattern = Image.fromarray(array)
        pattern = pattern.convert("L")
        
        pattern.save("./../Registration_Images/TouchingSquares/registration_mask_"+str(i)+".png","PNG")
        
        file = open('./../Registration_Images/TouchingSquares/positions.txt', 'w')
        writePositionsToFile(file, p1, p2, p3)
        file.close()
        
def plotPoints(*args):
    c = np.array((args))
    fig = plt.figure()
    plt.scatter(c[:,0], c[:,1])
    plt.xlim(0, 1024)
    plt.ylim(0, 768)
    plt.show()

if __name__ == "__main__":
#    p1 = np.array([300,300])
#    p2 = np.array([600,300])
#    p3 = np.array([450,450])
#    p4 = np.array([300,600])
    
    p1 = np.array([300,200])
    p2 = np.array([500,600])
    p3 = np.array([700,200])
    sigma = 75
    
    # circlePatterns(p1,p2,p3, p4)
    touchingSquarePatterns(sigma, p1, p2, p3)
    
#    plotPoints(p1, p2, p3)