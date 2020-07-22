#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 11:07:21 2020

@author: Izak de Heer

This script is used to compare the precision and accuracy of both manual and 
automated recognition of registration grid points for cirlces and touching 
squares patterns.
"""

from CoordinatesManager.backend.readRegistrationImages import touchingCoordinateFinder, circleCoordinateFinder
from skimage.measure import block_reduce
import skimage
import numpy as np
import matplotlib.pyplot as plt
import os
import time
# -*- coding: utf-8 -*-
import sys
import numpy as np

import matplotlib.pyplot as plt
import os       

from skimage.measure import block_reduce

class Coordinates:
    def __init__(self, fig, axs, n, *args, **kwargs):
        self.coords = []
        self.counter = 0
        self.axs = axs
        self.fig = fig
        self.id = n
    
    def save_coord(self, event):
        if event.dblclick:    
            x, y = event.xdata, event.ydata
            self.coords.append([x,y])
            
            self.axs[self.counter].scatter(x, y, color='r')
            plt.draw()
            
            if self.counter == 5:
                self.print_coords()
                global man_coordinates
                man_coordinates[:,:,self.id] = np.asarray(self.coords)
                
            self.counter += 1
        
    def print_coords(self):
        print('--------------------------')
        print('Coordinates list:')
        print(np.asarray(self.coords))

def open_coordinate_files(method):
    global coordinates
    coordinates = np.reshape(np.loadtxt('CoordinatesManager/Results/10-7/'+method+'_positions_automatic.txt'), (6,2,6))
    global man_coordinates
    man_coordinates = np.reshape(np.loadtxt('CoordinatesManager/Results/10-7/'+method+'_positions_manual.txt'), (6,2,6))

if __name__ == "__main__":
    
    method = 'squares' # 'circle' or 'squares'
    
    # Use to open previously found coordinates from file
    if True:
        open_coordinate_files(method)
    
    fig, axs = plt.subplots(1,2, figsize=(10,4))
    
    if True:
        axs[0].scatter(coordinates[:,0,:], coordinates[:,1,:], color='r', label='Automated', marker = '*')
        axs[0].scatter(man_coordinates[:,0,:], man_coordinates[:,1,:], color='b', label='Manual', marker = '8')
        axs[0].legend()
        axs[0].set_ylim([0, 2048])
        axs[0].set_xlim([0, 2048])
        axs[0].set_title('Located registration grid points \n ('+method+', n=36 per sample)')
    
       
    if True:
        zero_mean_coordinates = np.zeros(coordinates.shape)
        zero_mean_man_coordinates = np.zeros(coordinates.shape)
        for i in range(coordinates.shape[0]):
            for j in range(coordinates.shape[1]):
                zero_mean_coordinates[i,j,:] = coordinates[i,j,:] - np.average(coordinates[i,j,:])
                zero_mean_man_coordinates[i,j,:] = man_coordinates[i,j,:] - np.average(man_coordinates[i,j,:])
                
    if True:
        axs[1].scatter(zero_mean_coordinates[:,0,:], zero_mean_coordinates[:,1,:], color='r', label='Automatic', marker='*')
        axs[1].scatter(zero_mean_man_coordinates[:,0,:], zero_mean_man_coordinates[:,1,:], color='b', label='Manual', marker='8')
        axs[1].legend(loc='upper left')
        axs[1].set_title('Located registration grid points after removing mean \n ('+method+', n=36 per sample)')
        
        
        variance = np.var(np.sqrt(zero_mean_coordinates[:,0,:]**2 + zero_mean_coordinates[:,1,:]**2 ) )
        variance_man = np.var(np.sqrt(zero_mean_man_coordinates[:,0,:]**2 + zero_mean_man_coordinates[:,1,:]**2 ) )
        
        if method == 'squares':
            axs[1].text(15, 75, 'Manual:')
            axs[1].text(15, 67, "Variance: {:.1f}".format(variance_man))
            
            axs[1].text(15, 52, 'Automatic:')
            axs[1].text(15, 45, "Variance: {:.1f}".format(variance))
        else:
            axs[1].text(5, 32, 'Manual:')
            axs[1].text(5, 29, "Variance: {:.1f}".format(variance_man))
            axs[1].text(5, 23, 'Automatic:')
            axs[1].text(5, 20, "Variance: {:.1f}".format(variance))
    
    if True:
        man_distance_to_origin = np.sqrt(zero_mean_man_coordinates[:,0,:]**2 + zero_mean_man_coordinates[:,1,:]**2).ravel()
        distance_to_origin = np.sqrt(zero_mean_coordinates[:,0,:]**2 + zero_mean_coordinates[:,1,:]**2).ravel()
        
        max_distance = max(np.max(man_distance_to_origin), np.max(distance_to_origin))
        fig, axs = plt.subplots(2,1)
        axs[0].hist(man_distance_to_origin, bins = 8)
        axs[0].set_title('Absolute distance from cluster mean for manual grid locating \n ('+method+', n=36 per sample)')
        axs[0].set_xlim([0, max_distance])
        if method == 'squares':
            axs[0].set_ylim([0, 21])
        else:
            axs[0].set_ylim([0, 13])
        axs[0].set_xlabel('Absolute distance from cluster mean')
        axs[0].set_ylabel('Frequency')
        
        axs[1].hist(distance_to_origin, bins = 8)
        axs[1].set_title('Absolute distance from cluster mean for automatic grid locating \n ('+method+', n=36 per sample)')
        axs[1].set_xlim([0, max_distance])
        if method == 'squares':
            axs[1].set_ylim([0, 21])
        else:
            axs[1].set_ylim([0, 13])
        axs[1].set_xlabel('Absolute distance from cluster mean')
        axs[1].set_ylabel('Frequency')
        
        plt.tight_layout()
    
    # Use for picking locations manually
    if False:
        grid_points_x = 2
        grid_points_y = 3
        num_points = grid_points_x * grid_points_y
        
        abs_x_coords = np.linspace(0, 768, grid_points_x+2)[1:-1]
        abs_y_coords = np.linspace(0, 1024, grid_points_y+2)[1:-1]
        
        coordinates = np.zeros((num_points, 2, 6))
        
        for n in range(5,6):
            
            fig, axs = plt.subplots(grid_points_x,grid_points_y)
            axs = axs.ravel()
            
            coords = Coordinates(fig, axs, n)
            fig.canvas.mpl_connect('button_press_event', coords.save_coord)
        
            print(n)
            for i in range(num_points):
                if method == 'squares':
                    image = plt.imread(os.getcwd()+'/CoordinatesManager/Registration_Images/TouchingSquares/TouchingSquaresWithCells'+str(n+1)+'/image_'+str(i)+'.png')
                else:
                    image = plt.imread(os.getcwd()+'/CoordinatesManager/Registration_Images/TouchingSquares/CircleWithCells'+str(n+1)+'/image_'+str(i)+'.png')
                image = np.average(image, axis=2)
                
                # Downsample image in order to speed up
                image = block_reduce(image, (2,2))
            
                axs[i].imshow(image)   
                
                plt.tight_layout()
                plt.show()
                
            man_coordinates *= 2
            
    # Use for picking locations automatic
    if False:
        grid_points_x = 2
        grid_points_y = 3
        num_points = grid_points_x * grid_points_y
        
        abs_x_coords = np.linspace(0, 768, grid_points_x+2)[1:-1]
        abs_y_coords = np.linspace(0, 1024, grid_points_y+2)[1:-1]
        
        coordinates = np.zeros((num_points, 2, 6))
        
        for n in range(6):
            fig, axs = plt.subplots(2,3)
            axs = axs.ravel()
            
            print(n)
            for i in range(num_points):
                if method == 'squares':
                    image = plt.imread(os.getcwd()+'/CoordinatesManager/Registration_Images/DMD Registration Data/TouchingSquaresWithCells'+str(n+1)+'/image_'+str(i)+'.png')
                else:
                    image = plt.imread(os.getcwd()+'/CoordinatesManager/Registration_Images/DMD Registration Data/CircleWithCells'+str(n+1)+'/image_'+str(i)+'.png')
                    
                image = np.average(image, axis=2)
                
                # Downsample image in order to speed up
                image = block_reduce(image, (2,2))
                
            
                coordinates[i,:,n] = touchingCoordinateFinder(image, method = 'curvefit')    
                # coordinates[i,:,n] = circleCoordinateFinder(image)
                axs[i].imshow(image)
                axs[i].scatter(coordinates[i,0,n], coordinates[i,1,n], color='r')
                axs[i].set_axis_off()
                
        # Compensate for downsampling by factor of 2 in each direction
        coordinates *= 2
    
    