#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 09:21:44 2020

@author: Izak de Heer
"""


from scipy import optimize
import numpy as np
import matplotlib.pyplot as plt
    
def _transform_x(p, *kwargs):
    order = int(np.sqrt(len(kwargs)))
    c = np.reshape(np.asarray(kwargs), (order,order))
    return np.polynomial.polynomial.polyval2d(p[:,0], p[:,1], c)

def _transform_y(p, *kwargs):
    order = int(np.sqrt(len(kwargs)))
    c = np.reshape(np.asarray(kwargs), (order,order))
    return np.polynomial.polynomial.polyval2d(p[:,0], p[:,1], c)

def polynomial2DFit(p, q, order = 1):
    """
    Input an array of coordinates p and q in frame P and Q. The function returns
    a function matrix that transforms P into Q using polynomial transform. 
    
    param p, q = np.array([p1_x, p1_y], 
                          [p2_x, p2_y, 
                            .., ..])
    
    param order = order of polynomial transform, order should be smaller than 
                  the number of input points
                  
    return = stacked polynomial coefficients matrices, rounded to 4 decimals
    
    """
    
    init_param = np.ones((order+1,order+1))
    params_x, _ = optimize.curve_fit(_transform_x, p, q[:,0], init_param)
    params_y, _ = optimize.curve_fit(_transform_y, p, q[:,1], init_param)
    
    return np.stack((np.reshape(params_x, (order+1, order+1)), np.reshape(params_y, (order+1, order+1))), axis = 2)

def transform(coord, c):
    """
    param coord: np.ndarray of shape nx2 containing x and y coordinates. 
    param c: matrix containing the transformation coefficients.
    
    """
    if coord.ndim == 1:
        new_coord_x = np.polynomial.polynomial.polyval2d(coord[0], coord[1], c[:,:,0])
        new_coord_y = np.polynomial.polynomial.polyval2d(coord[0], coord[1], c[:,:,1])
    else:
        new_coord_x = np.polynomial.polynomial.polyval2d(coord[:,0], coord[:,1], c[:,:,0])
        new_coord_y = np.polynomial.polynomial.polyval2d(coord[:,0], coord[:,1], c[:,:,1])
    return np.transpose(np.stack((new_coord_x, new_coord_y)))

if __name__ == '__main__':
    grid_points_x = 2
    grid_points_y = 3
    
    x_coords = np.linspace(0, 768, grid_points_x+2)[1:-1].astype(int)
    y_coords = np.linspace(0, 1024, grid_points_y+2)[1:-1].astype(int)
    
    px = np.linspace(0, 768, 4)[1:-1].astype(int)
    py = np.linspace(0, 1024, 5)[1:-1].astype(int)
    
    qx = np.array((571, 1121, 1730, 648, 1120, 1648))
    qy = np.array((807, 797, 861, 1411, 1348, 1340))
    
    coord_out = np.reshape((np.meshgrid(x_coords, y_coords)), (2, -1), order='F').transpose()
    coord_in = np.stack((qy,qx), axis=1)
    
    soln1 = np.round(polynomial2DFit(coord_in, coord_out), 3)
    
    print('in x:')
    print(soln1[:,:,0])
    print('in y:')
    print(soln1[:,:,1])