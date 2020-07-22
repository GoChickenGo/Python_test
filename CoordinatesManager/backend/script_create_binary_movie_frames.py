#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 20 15:46:40 2020

@author: Izak de Heer
"""

import skimage.filters
import skimage.io
import numpy as np
import matplotlib.pyplot as plt
import os
import cv2

# Convert video in single frames .jpg
vidcap = cv2.VideoCapture('Videos/eagle.mp4')
success,image = vidcap.read()
count = 0
# while success:
#   cv2.imwrite("/Videos/eagle_frames/frame%d.jpg" % count, image)     # save frame as JPEG file
#   success,image = vidcap.read()
#   print ('Read a new frame: ', success)
#   count += 1

path = os.getcwd()+'/Images/eagle_frames_raw/'
for file in os.listdir(path):
    img = plt.imread(path+file)
    
    # Choose one RBG plane
    img_original = img[:,:,1]   
    
    # Filter image from background
    img = img_original > skimage.filters.threshold_isodata(img_original)
    
    # Resize to DMD resolution
    image_resized = skimage.transform.resize(img, (768, 1024),
                    anti_aliasing=True)
    
    skimage.io.imsave("Images/movie_frames_eagle/"+file[:-4]+"_resized_1.jpg", image_resized.astype(int))
    