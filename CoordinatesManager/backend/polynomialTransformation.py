#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 09:54:25 2020

@author: Izak de Heer

"""

import matplotlib.pyplot as plt
import numpy as np

class polynomialRegression:
    def addPoints(self, q, p):
        """
        Add coordinates in both coordinate systems to the object. Q is the initial
        coordinate system, P is the coordinate system to which Q has to be mapped
        by the transformation.
        """
        self.q = q
        self.p = p
    
    def setOrder(self, order):
        """
        Set the order of the polynomial transformation.
        """
        self.order = order

    def transform(self, r):
        """
        This function takes points as input and returns the 
        transformed points. 
            
        q = np.array([[1,1], [1, 2], [1,3]])
        
        """
        
        if r.ndim == 1:
            Q = self._createTransformationMatrix(r)
            
            if Q is None:
                return
            
            return np.squeeze(np.reshape(np.dot(Q, self.A), (-1,2), order='F'))
            
        else:
            num_points = r.shape[0]
        
        transformed_points = np.zeros([num_points, 2])
        
        for i in range(num_points):
            
            Q = self._createTransformationMatrix(r[i,:])
            
            if Q is None:
                return
            
            transformed_points[i,:] = np.squeeze(np.dot(Q, self.A))
        return np.reshape(transformed_points, (-1,2), order='F')
        
    
    def _createTransformationMatrix(self,q): 
        if len(q.shape) == 1:
            Qx = np.array([1, 0, q[0], q[1]])
            Qy = np.hstack((0, 1, np.zeros(2*self.order), q[0], q[1]))
    
            for i in range(2,self.order+1):
                Qx = np.hstack((Qx, q[0]**i, q[1]**i))
                Qy = np.hstack((Qy, q[0]**i, q[1]**i))
            
            Qx = np.hstack((Qx, np.zeros(2*self.order)))
        else:
            print("Function takes only one point at a time")
            return 
            
        Q = np.vstack((Qx, Qy))
        
        return Q
    
    def _createRegressionMatrix(self, q):
        self.size = 2+4*self.order
        self.hsize = 1+2*self.order ## Define half size, just for convenience
    
        if len(self.q.shape) != 1 and self.order == 0:
            num_input_points = self.q.shape[0]
            print("Number of input points is "+str(num_input_points))
            print("For zeroth order input one point only")
            self.Q = None
            return
        
        if self.q.shape[0] != self.hsize and self.order != 0:
            num_input_points = self.q.shape[0]
            print("Number of input points is "+str(num_input_points))
            print("For N'th order input 1+2N points")
            self.Q = None
            return
        
        col1 = np.hstack((np.ones(self.hsize), np.zeros(self.hsize)))
        col2 = np.flip(col1)
        
        if self.order == 0:
            return np.vstack((col1, col2)).transpose()
        else:
            col3 = np.hstack((q[:,0], np.zeros(self.hsize)))
            col4 = np.hstack((q[:,1], np.zeros(self.hsize)))
            col5 = np.hstack((np.zeros(self.hsize), q[:,0]))
            col6 = np.hstack((np.zeros(self.hsize), q[:,1]))
            
            Qx = np.vstack((col1, col2, col3, col4))
            Qy = np.vstack((col5, col6))
    
        for i in range(2,self.order+1):
            Qx = np.vstack((Qx, col3**i, col4**i))
            Qy = np.vstack((Qy, col5**i, col6**i))
            
        self.Q = np.vstack((Qx, Qy)).transpose()
    
    def findTransform(self):
        """
        
        This function performs multilinear regression between two sets of points 
        Q and P in different coordinate frames. The function returns the transformation
        matrix T and the translation vector t according to P = t + sum_{n=1}^N (T Q)^n. 
        
        """
            
        self._createRegressionMatrix(self.q)
        if self.Q is None:
            return None, None
        
        self.P = np.reshape(self.p, (-1, 1), order='F')
        
        # Standard regression formula
        try:
            self.A = np.dot(np.dot(np.linalg.inv(np.dot(self.Q.transpose(), self.Q)),self.Q.transpose()), self.P)
        except np.linalg.LinAlgError:
            print("Matrix is singular. Try different set of input points. " \
                  + "Points should not be colinear")
            return
    
        self.t = self.A[0:2]
        print("Translation vector =")
        print(np.around(self.t, 5))
        print()
        
        # Because of the order in the A vector, the a_n, b_n, c_n and d_n are not 
        # in consequetive order in A. Therefore, a moveaxis() is performed.
        Areduced = self.A[2:]
        num = int(Areduced.shape[0]/2)
        tmp = np.hstack((Areduced[0:num], Areduced[num:]))
        
        self.T = np.zeros((int(tmp.shape[0]/2), 2, 2))
        for i in range(self.T.shape[0]):
            self.T[i, :, :] = tmp[2*i:2*i+2, 0:2]
        
        
        # self.T = np.moveaxis(np.reshape(self.A[2:], (2,2,-1)), 0, -2)
    
        for i in range(self.order):
            print(str(i+1) + "'th order transformation matrix =")
            print(np.around(self.T[i,:,:], 5))
            print()
                
        self.flag_transformation_found = True            
        return self.T, self.t
        
    def plotPoints(self):
        p = self.p
        q = self.q
        xmin = min(q[:,0].min(), p[:,0].min())
        xmax = max(q[:,0].max(), p[:,0].max())
        ymin = min(q[:,1].min(), p[:,1].min())
        ymax = max(q[:,1].max(), p[:,1].max())
        xrange = xmax - xmin
        yrange = ymax - ymin
        xmin -= 0.1*xrange
        xmax += 0.1*xrange
        ymin -= 0.1*yrange
        ymax += 0.1*yrange
        
        fig, axs = plt.subplots(1,2)
        axs[0].scatter(q[:,0], q[:,1])
        axs[0].set_xlim([xmin,xmax])
        axs[0].set_ylim([ymin, ymax])
        axs[0].set_title("Points in coordinate system Q")
        axs[0].set_xlabel("x")
        axs[0].set_xlabel("y")
        axs[1].scatter(p[:,0], p[:,1])
        axs[1].set_xlim([xmin,xmax])
        axs[1].set_ylim([ymin, ymax])
        axs[1].set_title("Points in coordinate system P")
        axs[1].set_xlabel("x")
        axs[1].set_xlabel("y")
        
if __name__=="__main__":
    p1 = np.array([272, 200])
    p2 = np.array([272, 202])
    p3 = np.array([274, 210])
    
    q1 = np.array([1, 0])
    q2 = np.array([1, 1])
    q3 = np.array([2, 5])
    
    p = np.vstack((p1, p2, p3))
    q = np.vstack((q1, q2, q3))
    
    registrator = polynomialRegression()
    registrator.addPoints(p, q)
    registrator.setOrder(1)
    
    registrator.findTransform()
    
    r1 = np.array([614, 614])
    r2 = np.array([5, 6])
    r3 = np.array([5, 7])
    
    r = np.vstack((r1, r2, r3))
    
    R1 = registrator.transform(r)
    