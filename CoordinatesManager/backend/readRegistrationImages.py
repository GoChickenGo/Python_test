#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 11:29:16 2020

@author: Izak de Heer
"""

import numpy as np
import matplotlib.pyplot as plt
import skimage.feature
import skimage.filters
import skimage.restoration
import skimage.exposure
import scipy.optimize
import scipy.ndimage as ndi
import scipy.signal
import time
import math as m
import os

from CoordinatesManager import Registrator

def gaussian(x, y, x0, y0, sigma, amp):
    """
    Function that returns a raveled binary array containing a circle.
    
    x and y: width and height of array 
    x0, y0: coordinates of the circle center
    sigma: size of the circle
    """
    
    X, Y = np.meshgrid(x,y)
    
    mask = amp*np.exp( ( -(X-x0)**2 - (Y-y0)**2 ) / (2*sigma**2) )
    
    mask = mask.ravel()
    return mask

def _gaussian(M, *args):
    """
    Callback function used by the scipy.optimize.curve_fit() function.
    """
    
    x = y = int(np.sqrt(M.shape[1]))
    arr = gaussian(x,y, *args)
    return arr

def gaussian_fitting(image):
    x_max = np.where(image == image.max())[0][0]
    y_max = np.where(image == image.max())[1][0]
    
    bbox_size = 50
    
    X, Y = np.meshgrid(np.linspace(-bbox_size, bbox_size, 2*bbox_size), np.linspace(-bbox_size, bbox_size, 2*bbox_size))
    
    x = np.vstack((X.ravel(), Y.ravel()))
    p0 = np.array([x_max, y_max, 1, 1])
    
    popt, pcov = scipy.optimize.curve_fit(_gaussian, x, image[x_max-bbox_size:x_max+bbox_size, y_max-bbox_size:y_max+bbox_size].ravel(), p0, maxfev=10)
    
    return np.array((popt[0], popt[1]))

def touchingCoordinateFinder(image, method = 'curvefit'):
    image = skimage.filters.gaussian(image,10)
    
    if method == 'curvefit':
        coordinate = findTouchingSquaresCenterCoordinate_curvefit(image)        
    elif method == 'correlation':
        coordinate = findTouchingSquaresCenterCoordinate_correlationt(image)        
    elif method == 'centroid':
        coordinate = findTouchingSquaresCenterCoordinate_centroid(image)        
    else:
        print('Invalid method: choose curvefit, correlation or centroid')
        return 

    return coordinate

def circleCoordinateFinder(image):
    image = skimage.filters.gaussian(image, 10)
    
    coordinate = findCircleCenterCoordinate_curvefit(image)
    return coordinate
    
def touching_squares(x, y, x0, y0, sigmax, sigmay):
    """
    Function that returns a raveled binary array containing two touching squares.
    
    x and y: width and height of array 
    x0, y0: coordinates of the point where the squares touch
    sigma: size of the squares
    """
    x1 = int(x0 - sigmax)
    x2 = int(x0 - 1)
    x3 = int(x0 + sigmax - 1)
    y1 = int(y0 - sigmay)
    y2 = int(y0 - 1)
    y3 = int(y0 + sigmay - 1)
    
    x = int(2.5*sigmax)
    y = int(2.5*sigmay)
    
    
    mask = np.zeros((x,y))
    mask[skimage.draw.rectangle((x1, y1), (x2, y2))] = 1
    mask[skimage.draw.rectangle((x2+1, y2+1), (x3, y3))] = 1
    
    mask = mask.ravel()
    return mask

def circle(x, y, x0, y0, sigma):
    """
    Function that returns a raveled binary array containing a circle.
    
    x and y: width and height of array 
    x0, y0: coordinates of the circle center
    sigma: size of the circle
    """
    
    x = int(2.5*sigma)
    y = int(2.5*sigma)
    
    
    mask = np.zeros((x,y))
    mask[skimage.draw.circle(x0, y0, sigma)] = 1
    
    mask = mask.ravel()
    return mask

def _circle(M, *args):
    """
    Callback function used by the scipy.optimize.curve_fit() function.
    """
    
    x = y = int(np.sqrt(M.shape[1]))
    arr = circle(x,y, *args)
    return arr

def _touching_squares(M, *args):
    """
    Callback function used by the scipy.optimize.curve_fit() function.
    """
    
    x = y = int(np.sqrt(M.shape[1]))
    arr = touching_squares(x, y, *args)
    return arr


def selectROI(image):
    """
    Function that searches for the section of the image that contains the 
    touching squares. Using only this section speeds up further computations. 
    In case thresholding results in multiple segments, it is assumed that the 
    segment with the largest area is the desired segment. Function returns the 
    a subsection of the input image, the coordinates of the bounding box in the
    coordinates of the input image and the threshold used to segment the input
    image.
    """
    ## Normalize image
    img = (image-image.min())/(image.max()-image.min())
    
    ## Clip image 
    img_clipped = np.clip(img,0, 0.3)
    img_clipped = img
    
    ## Normalize clipped image
    img_clipped = (img_clipped-img_clipped.min())/(img_clipped.max()-img_clipped.min())
    
    ## Find and apply Otsu threshold
    threshold = skimage.filters.threshold_minimum(img_clipped.ravel())
    
    img_thresholded = img_clipped > threshold
    
    img_thresholded = 1-skimage.morphology.area_closing(1-img_thresholded, area_threshold=2000)
    contour = skimage.measure.find_contours(img_thresholded, 0.9)
    
    if len(contour) != 1:
        bbox = np.array((np.amin(contour[0][:,0]), np.amax(contour[0][:,0]), np.amin(contour[0][:,1]), np.amax(contour[0][:,1])))
        bbox_area = (bbox[1]-bbox[0])*(bbox[3]-bbox[2])
        old_bbox_area = bbox_area
        
        for i in range(1, len(contour)):
            tmp_bbox = np.array((np.amin(contour[i][:,0]), np.amax(contour[i][:,0]), np.amin(contour[i][:,1]), np.amax(contour[i][:,1])))
            tmp_bbox_area = (tmp_bbox[1]-tmp_bbox[0])*(tmp_bbox[3]-tmp_bbox[2])
            
            if tmp_bbox_area > old_bbox_area:
                bbox = tmp_bbox
                
            old_bbox_area = tmp_bbox_area
                
    else:
        contour = contour[0]
        try:
            np.amin(contour[:,0])
        except:
            print('np.amin failed')
                
        bbox = np.array([np.amin(contour[:,0])-50, np.amax(contour[:,0])+50, np.amin(contour[:,1])-50, np.amax(contour[:,1])+50])
    
    bbox = bbox.astype(int)
    img_selection = img_clipped[bbox[0]:bbox[1], bbox[2]:bbox[3]]
    return bbox, img_selection, threshold

def findCircleCenterCoordinate_curvefit(image):
    """
    Function that takes an image, fits a template and returns the center of 
    the template. In order to speed the fitting up, a template is 
    fitted to a smaller section of the image around the maximum position. 
    """
    
    bbox, img_selection, threshold = selectROI(image)
    
    mask_width = bbox[1]-bbox[0]
    mask_height = bbox[3]-bbox[2]
    h_mask_width = m.floor(mask_width/2)
    h_mask_height = m.floor(mask_height/2)
    
    X,Y = np.mgrid[0:mask_width, 0:mask_height]
    x = np.vstack((X.ravel(), Y.ravel()))
    
    p0 = np.array([h_mask_width, h_mask_height, 0.4*mask_width, 0.4*mask_height])
    popt, pcov = scipy.optimize.curve_fit(_touching_squares, x, img_selection.ravel(), p0)
    
    coordinates = np.flip(np.array((bbox[0]+popt[0], bbox[2]+popt[1])).astype(int).astype(int))
    
    return coordinates

def findTouchingSquaresCenterCoordinate_curvefit(image):
    """
    Function that takes an image, fits a template and returns the center of 
    the template. In order to speed the fitting up, a template is 
    fitted to a smaller section of the image around the maximum position. 
    """
    
    bbox, img_selection, threshold = selectROI(image)
    
    mask_width = bbox[1]-bbox[0]
    mask_height = bbox[3]-bbox[2]
    h_mask_width = m.floor(mask_width/2)
    h_mask_height = m.floor(mask_height/2)
    
    X,Y = np.mgrid[0:mask_width, 0:mask_height]
    x = np.vstack((X.ravel(), Y.ravel()))
    
    p0 = np.array([h_mask_width, h_mask_height, 0.4*mask_width, 0.4*mask_height])
    popt, pcov = scipy.optimize.curve_fit(_touching_squares, x, img_selection.ravel(), p0)
    
    coordinates = np.flip(np.array((bbox[0]+popt[0], bbox[2]+popt[1])).astype(int).astype(int))
    
    return coordinates

def findTouchingSquaresCenterCoordinate_correlation(image):
    
    """
    Function that finds the center coordinates of two touching squares using
    a curve fit function, applied on a binary, thresholded image and a 
    template of the touching squares. Returns the center coordinates.
    
    """
    
    self._selectROI()
    mask_width = self.bbox[1]-self.bbox[0]
    mask_height = self.bbox[3]-self.bbox[2]
    h_mask_width = m.floor(mask_width/2)
    h_mask_height = m.floor(mask_height/2)

    mask = self.touching_squares(mask_width, mask_height, h_mask_width, h_mask_height, h_mask_width, h_mask_height)
    mask = np.reshape(mask, (mask_width, mask_height))
    
    result = scipy.signal.correlate(self.img_selection > self.threshold, mask)
    coordinate = np.squeeze(np.asarray(np.where(result == np.amax(result))))
    self.coordinates = np.array((coordinate[0] - h_mask_width + self.bbox[0], coordinate[1] - h_mask_height +self.bbox[2])).astype(int)

def findTouchingSquaresCenterCoordinate_centroid(image):
    """
    Function that finds the center coordinates of two touching squares using
    the centroid method. Returns the center coordinates.
    """
    
    self._selectROI()
    
    M = skimage.measure.moments(self.img_selection > self.threshold, order=1)
    centroid = (M[1, 0] / M[0, 0], M[0, 1] / M[0, 0])
    self.coordinates = np.array((centroid[0] + self.bbox[0], centroid[1]+self.bbox[2])).astype(int)

if __name__ == "__main__":
    
    if True:
        coordinates = np.loadtxt('CoordinatesManager/Results/galvo_registration_coords.txt').astype(int)
        
        # coordinates = np.zeros((9,2))
        
        x_coords = np.linspace(-10, 10, 5)[1:-1]
        y_coords = np.linspace(-10, 10, 5)[1:-1]
        xy_mesh = np.reshape(np.meshgrid(x_coords, y_coords), (2, -1), order='F').transpose()
        galvo_coordinates = xy_mesh
        
        fig1, axs1 =plt.subplots(3,3)
        axs1=  axs1.ravel()
        
        fig2, axs2 = plt.subplots(3,3)
        axs2 = axs2.ravel()
        
        for i in range(9):
            image = plt.imread('CoordinatesManager/Registration_Images/2P/Set1/image_'+str(i)+'.png')
            image = skimage.filters.gaussian(np.average(image, axis=2), 1)
            axs1[i].imshow(image.transpose())
            
            # print(np.mean(image))
            # print(np.where(image == np.max(image)))
            # print(np.min(image))
            # coordinates[i,:] = gaussian_fitting(image)
            axs1[i].add_artist(plt.Circle((coordinates[i,0], coordinates[i,1]), 75, color='r', fill = False))
            axs1[i].set_axis_off()
            axs1[i].set_title('('+str(coordinates[i,0])+','+str(coordinates[i,1])+')')
            # axs[i].scatter(coordinates[i,1], coordinates[i,0])
            # print(coordinates)
            
            axs2[i].scatter(galvo_coordinates[i,0], galvo_coordinates[i,1])
            axs2[i].set_ylim([-10, 10])
            axs2[i].set_xlim([-10, 10])
            axs2[i].plot((-10, -10, 10, 10, -10), (-10, 10, 10, -10, -10), color='black')
            axs2[i].set_title('('+str(galvo_coordinates[i,0])+','+str(galvo_coordinates[i,1])+')')
            axs2[i].set_axis_off()
        plt.tight_layout()
    
    if False:
        fig, axs = plt.subplots(2,6)
        
        grid_points_x = 2
        grid_points_y = 3
        
        x_coords = np.linspace(0, 768, grid_points_x+2)[1:-1].astype(int)
        y_coords = np.linspace(0, 1024, grid_points_y+2)[1:-1].astype(int)
        
        xy_coords = np.reshape((np.meshgrid(x_coords, y_coords)), (2, -1), order='F').transpose()
        
        for i in range(6):
            image = plt.imread(os.getcwd()+'/CoordinatesManager/Registration_Images/DMD Registration Data/TouchingSquaresWithCells1/image_'+str(i)+'.png')
            image = np.average(image, axis=2)
            
            mask = Registrator.DMDRegistator.create_registration_image_touching_squares(xy_coords[i,0], xy_coords[i,1])
            axs[0,i].imshow(mask, origin='lower')
            axs[0,i].set_axis_off()
            axs[0,i].set_title('('+str(xy_coords[i,1])+','+str( xy_coords[i,0])+')')
            # coordinates = touchingCoordinateFinder(image, method = 'curvefit')    
            coordinates = touchingCoordinateFinder(image)    
            axs[1,i].imshow(image, origin='lower')   
            axs[1,i].scatter(coordinates[0], coordinates[1], color='r')
            axs[1,i].set_title('('+str(coordinates[0])+','+str(coordinates[1])+')')
            axs[1,i].set_axis_off()
        
            print(coordinates)
            
            plt.tight_layout()
            plt.show()
    
    if False:
        image = plt.imread(os.getcwd()+'/CoordinatesManager/Registration_Images/DMD Registration Data/TouchingSquaresWithCells1/image_'+str(0)+'.png')
        image = np.average(image, axis=2)
        print(findTouchingSquaresCenterCoordinate_curvefit(image))
        
        
    if False:
        fig, axs = plt.subplots(1,4)
        
        image_org = plt.imread(os.getcwd()+'/CoordinatesManager/Registration_Images/DMD Registration Data/TouchingSquaresWithCells1/image_'+str(1)+'.png')
        image = np.average(image_org, axis=2)
        image = skimage.filters.gaussian(image,10)
        
        axs[0].imshow(image_org)
        axs[0].set_axis_off()
        
        bbox, img_selection, threshold, img_thresholded = selectROI(image)
        axs[1].imshow(1-img_thresholded, cmap='binary')
        axs[1].set_axis_off()
        
        coordinate = findTouchingSquaresCenterCoordinate_curvefit(image)
        axs[2].imshow(1 - (img_selection > threshold), cmap='binary')
        axs[2].scatter(coordinate[0]-bbox[2], coordinate[1]-bbox[0], color='r', linewidths = 5)
        axs[2].set_axis_off()
        
        axs[3].imshow(image_org)
        axs[3].scatter(coordinate[0], coordinate[1], color='r', linewidths = 5)
        axs[3].set_axis_off()