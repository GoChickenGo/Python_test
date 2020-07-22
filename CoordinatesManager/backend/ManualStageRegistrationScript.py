# -*- coding: utf-8 -*-
import sys
import numpy as np

import matplotlib.pyplot as plt
from skimage import measure
import skimage.draw
import os       

old_cwd = os.getcwd()
os.chdir(os.getcwd()+'/../../')
import CoordinateTransformations 
os.chdir(old_cwd)

from skimage.measure import block_reduce

class Coordinates:
    def __init__(self, fig, axs, global_pos_name, global_coords = None, *args, **kwargs):
        self.coords = []
        self.pos = []
        self.counter = 0
        self.axs = axs
        self.fig = fig
        self.global_pos_name = global_pos_name
        self.global_coords = global_coords
    
    def save_coord(self, event):
        if event.dblclick:    
            x, y = event.xdata, event.ydata
            self.coords.append([x,y])
            
            self.axs[self.counter].scatter(x, y, color='r')
            plt.draw()
            
            if self.counter == 8:
                self.print_coords()
                
            self.counter += 1
        
    def print_coords(self):
        print('Global pos '+str(self.global_pos_name)+' :')
        print('--------------------------')
        print('Coordinates list:')
        print(np.asarray(self.coords))
        
        self.relative_coords = np.zeros(np.asarray(self.coords).shape)
        self.relative_coords[:,0] = 2 * (  np.asarray(self.coords)[:,0] - self.coords[4][0] )
        self.relative_coords[:,1] = 2 * ( np.asarray(self.coords)[:,1] - self.coords[4][1] )
        
        print(self.relative_coords)
        
        self.transformation = CoordinateTransformations.polynomial2DFit(self.relative_coords, np.asarray(self.pos), order = 1)
        self.transformation = np.round(self.transformation, 3)
        print('Polynomial coefficients for x:')
        print(self.transformation[:,:,0])
        print('Polynomial coefficients for y:')
        print(self.transformation[:,:,1])
        print('--------------------------')
        print('--------------------------')
        print('')
        
def read_transformation_from_file():
    global transformation_A 
    global coords_A
    # transformation_A = np.reshape(np.loadtxt('Distance200_Offset200/A_transform.txt'), (2,2,2))
    coords_A = np.loadtxt('Distance200_Offset0/A_coords.txt')
    global transformation_B
    global coords_B
    # transformation_B = np.reshape(np.loadtxt('Distance200_Offset200/B_transform.txt'), (2,2,2))
    coords_B = np.loadtxt('Distance200_Offset0/B_coords.txt')
    global transformation_C 
    global coords_C
    # transformation_C = np.reshape(np.loadtxt('Distance200_Offset200/C_transform.txt'), (2,2,2))
    coords_C = np.loadtxt('Distance200_Offset0/C_coords.txt')
    global transformation_D
    global coords_D
    # transformation_D = np.reshape(np.loadtxt('Distance200_Offset200/D_transform.txt'), (2,2,2))
    coords_D = np.loadtxt('Distance200_Offset0/D_coords.txt')

if __name__ == "__main__":
    
    if True:
        read_transformation_from_file()
    
    global_pos = np.array(((-5000,-5000), (-5000, 5000), (5000, -5000), (5000, 5000)))
    global_pos_name = ['A', 'B', 'C', 'D']
        
    delta = 200
    offset = 0
    local_pos = np.transpose(np.reshape(np.meshgrid(np.array((-delta, 0, delta)), np.array((-delta, 0, delta))), (2, -1)))
    local_pos_name = [str(i) for i in range(9)]
    
    if True:
        relative_coords = np.zeros(np.asarray(coords_B).shape)
        relative_coords[:,0] = coords_C[:,0] - coords_C[4,0]
        relative_coords[:,1] = coords_C[:,1] - coords_C[4,1]
        
        transformation = CoordinateTransformations.polynomial2DFit(relative_coords, local_pos, order = 1)
        print('Transformation x')
        print(np.round(transformation[:,:,0], 3))
        print('Transformation y')
        print(np.round(transformation[:,:,1], 3))
    
    # Visualize 
    if True:
        fig, axs = plt.subplots(2,len(local_pos_name))
        
        for i in range(len(local_pos_name)):
            image = plt.imread('Distance200_Offset200/A'+str(i)+'.png')
            image = np.average(image, axis = 2)
            image = block_reduce(image, (2,2), np.mean)
        
            ## Add factor 1/2 becaue of downsampling
            x = int(coords_A[i,0]/2+100)
            y = int(coords_A[i,1]/2-100)
            delta = 100
            
            fig.suptitle('Images at different relative stage positions around the position (-5000 mV, -5000 mV) with one marked target cell', y = 0.8)
            axs[0,i].imshow(image)
            axs[0,i].scatter(x,y, color='r')
            axs[0,i].set_axis_off()
            axs[0,i].set_title(str(local_pos[i,0])+', ' +str(local_pos[i,1]))
            axs[0,i].plot((x-delta, x-delta, x+delta, x+delta, x-delta), (y-delta, y+delta, y+delta, y-delta, y-delta), color='r')
            axs[1,i].imshow(image[y-delta:y+delta, x-delta:x+delta])
            axs[1,i].scatter(delta, delta, color='r')
            axs[1,i].set_axis_off()
            # axs[1,i].plot((1, 1, 2*delta, 2*delta, 1), (1, 2*delta, 2*delta, 1, 1), color='r')
   
   
    # if True:
    #    coords = []
    #    for i in range(4):
           
    #        if i == 0:
    #            global_coords = coords_A
    #        elif i == 1:
    #            global_coords = coords_B
    #        elif i == 2:
    #            global_coords = coords_C
    #        else:
    #            global_coords = coords_D
           
    #        fig, axs = plt.subplots(3,3)
    #        axs = axs.ravel()
           
    #        coords.append( Coordinates(fig, axs, global_pos_name[i], global_coords = global_coords))
    #        fig.canvas.mpl_connect('button_press_event', coords[i].save_coord)
            
    #        for j in range(len(local_pos_name)):
    #             image = plt.imread('Distance200_Offset0/'+global_pos_name[i]+local_pos_name[j]+'.png')
    #             image = np.average(image, axis = 2)
    #             image = block_reduce(image, (2,2), np.mean)
                
    #             coords[i].pos.append([local_pos[j,0],local_pos[j,1]])
            
    #             x = int(coords_A[j,0]/2)
    #             y = int(coords_A[j,1]/2)
                
    #             delta = 100
                
    #             axs[j].imshow(image[y-delta:y+delta, x-delta:x+delta])
    #             axs[j].set_axis_off()
   
    # Use this to pick coordinates in camera image
    if False:
        coords = []
        for i in range(4):#len(global_pos_name)):
            num_locals = int(np.sqrt(len(local_pos)))
            fig, axs = plt.subplots(num_locals, num_locals)
            axs = axs.ravel()
            
            coords.append( Coordinates(fig, axs, global_pos_name[i]) )
            fig.canvas.mpl_connect('button_press_event', coords[i].save_coord)
            
            for j in range(len(local_pos_name)):
                
                x = local_pos[j,0]
                y = local_pos[j,1]
                
                coords[i].pos.append([x,y])
                
                image = plt.imread('Distance200_Offset200/'+global_pos_name[i]+local_pos_name[j]+'.png')
                image = np.average(image, axis = 2)
                image = block_reduce(image, (2,2), np.mean)
                axs[j].imshow(image)
            
            plt.show()
    
    # Use this to plot the transformation contour lines
    if False:
        transformations = [transformation_A, transformation_B, transformation_C, transformation_D]
        if False:
            fig, axs = plt.subplots(2,2)
            axs = axs.ravel()
            
            origin_x = global_pos[:,0]
            for i in range(len(transformations)):
                
                x = np.arange(origin_x[i] - delta + offset, origin_x[i] + delta + offset, 1)
                y = np.arange(origin_x[i] - delta + offset, origin_x[i] + delta + offset, 1)
                
                X, Y = np.meshgrid(x,y)
                
                # x = X.ravel()
                # y = Y.ravel()
                # c_x = np.ones((3,3))
                Z_x = np.polynomial.polynomial.polyval2d(X, Y, transformations[i][:,0,:])
                # Z_y = np.polynomial.polynomial.polyval2d(X, Y, c_y)
                axs[i].imshow(Z_x)#, extent = (x.min(), x.max(), y.min(), y.max())
                
                # Find contours at a constant value of 0.8
                contours = measure.find_contours(Z_x, np.average(Z_x))
            
                for n, contour in enumerate(contours):
                    axs[i].plot(contour[:, 1], contour[:, 0], linewidth=2)
                    
                plt.tight_layout()
                    
    if False:
        
        coord_1 = np.array((338, 738))
        coord_2 = np.array((337, 648))
        
        cam_image = np.zeros((2048,2048))
        cam_image[skimage.draw.rectangle(coord_1, coord_2)] = 255
        
        fig, axs = plt.subplots(1,2)
        
        axs[0].imshow(cam_image)
        
        coord_1_x_transformed = int(np.polynomial.polynomial.polyval2d(coord_1[0], coord_1[1], transformations[2][:,0,:]))
        coord_1_y_transformed = int(np.polynomial.polynomial.polyval2d(coord_1[0], coord_1[1], transformations[2][:,1,:]))
        coord_1_transformed = np.array((coord_1_x_transformed, coord_1_y_transformed))
        
        coord_2_x_transformed = int(np.polynomial.polynomial.polyval2d(coord_2[0], coord_2[1], transformations[2][:,0,:]))
        coord_2_y_transformed = int(np.polynomial.polynomial.polyval2d(coord_2[0], coord_2[1], transformations[2][:,1,:]))
        coord_2_transformed = np.array((coord_2_x_transformed, coord_2_y_transformed))
        
        voltage_image = np.zeros((10000, 10000))
        voltage_image[skimage.draw.rectangle((coord_1_transformed[0], coord_1_transformed[1]),\
                                             (coord_2_transformed[0], coord_2_transformed[1]))] = 255
        
        axs[1].imshow(voltage_image)
        