# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 16:27:55 2020

@author: xinmeng
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from skimage.io import imread
import os
#from EvolutionAnalysis import ImageStackAnalysis
from EvolutionAnalysis_v2 import ProcessImage

class CurveAnalysis():
    
    def ReadinImgs(self, Nest_data_directory, rowIndex, colIndex):
        
        fileNameList = []
        ImgSequenceNum = 0
        for file in os.listdir(Nest_data_directory):
            if 'PMT_0Zmax' in file and 'R{}C{}'.format(rowIndex, colIndex) in file:
                fileNameList.append(file)
        
        fileNameList.sort(key=lambda x: int(x[x.index('Round')+5:x.index('_Coord')])) # Sort the list according to Round number
#        print(fileNameList)
        
        for eachfile in fileNameList:
            ImgSequenceNum += 1
            img_fileName = os.path.join(Nest_data_directory, eachfile)
            temp_loaded_image = imread(img_fileName, as_gray=True)
            temp_loaded_image = temp_loaded_image[np.newaxis, :, :]
            if ImgSequenceNum == 1:
                PMT_image_wholetrace_stack = temp_loaded_image
            else:
                PMT_image_wholetrace_stack = np.concatenate((PMT_image_wholetrace_stack, temp_loaded_image), axis=0)
                    
        return PMT_image_wholetrace_stack
    
    def Fit_WholeImg(self, function, imageStack, KCltrace):
        
        # KCl trace is np array made of 1(EC) and 0(KCl), also works as mask to delete KCl from the fitting data.
        
        self.imgsignalmean = np.zeros(len(KCltrace))
        for i in range(len(imageStack)):
            self.imgsignalmean[i] = np.mean(imageStack[i])
            
        xdata = np.linspace(1, len(KCltrace), len(KCltrace))
        
        xdata2fit = xdata[KCltrace, ...]
        imgsignalmean2fit = self.imgsignalmean[KCltrace, ...]
        
        plt.figure()
        plt.plot(xdata2fit, imgsignalmean2fit, label='Original')

        
        popt, pcov = curve_fit(function, xdata2fit, imgsignalmean2fit, maxfev=2000)
        
        plt.plot(xdata, func(xdata, *popt), 'r-', label='fit: a=%5.3f, b=%5.3f, c=%5.3f' % tuple(popt))
        plt.legend(loc='upper right')
        plt.show()
        
        return xdata2fit, imgsignalmean2fit, popt, pcov

if __name__ == "__main__":
    
    #Providing row and col index
    
    def func(x, a, b, c):
        return a * np.exp(-b * x) + c
    CurveAnalysis_instance = CurveAnalysis()
#    ImageStackAnalysis_instance = ProcessImage()
    
    PMT_image_wholetrace_stack = CurveAnalysis_instance.ReadinImgs('M:/tnw/ist/do/projects/Neurophotonics/Brinkslab/Data/Octoscope/2020-2-26 Archon control EC/trial_1', rowIndex = 1500, colIndex = 0)
    
    KCtrac = np.array([1,1,1,1,1,1,1,1,1,1,1,1], dtype=bool)
    
    RegionProposalMask, RegionProposalOriginalImage = ProcessImage.generate_mask(PMT_image_wholetrace_stack, openingfactor=2, closingfactor=3, binary_adaptive_block_size=335)#256(151) 500(335)
    
    CellPropDictEachRound = ProcessImage.get_cell_properties_Roundstack(PMT_image_wholetrace_stack, RegionProposalMask, smallest_size=300, contour_thres=0.001, 
                                                                                       contour_dilationparameter=15, cell_region_opening_factor=1, cell_region_closing_factor=3)

#    RegionProposalMask, RegionProposalOriginalImage = ImageStackAnalysis_instance.generate_mask(PMT_image_wholetrace_stack, openingfactor=2, 
#                                                                                                closingfactor=3, binary_adaptive_block_size=335)#256(151) 500(335)
#    
#    CellPropDictEachRound = ImageStackAnalysis_instance.get_cell_properties_Roundstack(PMT_image_wholetrace_stack, RegionProposalMask, smallest_size=300, contour_thres=0.001, 
#                                                                                       contour_dilationparameter=15, cell_region_opening_factor=1, cell_region_closing_factor=3)
    
    
    for EachCell in range(len(CellPropDictEachRound['RoundSequence1'])):
        cellproplist=[]
        for i in range(len(CellPropDictEachRound)):
    #        print((CellPropDictEachRound['RoundSequence{}'.format(i+1)][2]['Mean intensity in contour']))
            cellproplist.append(CellPropDictEachRound['RoundSequence{}'.format(i+1)][EachCell]['Mean intensity'])
            
        Xpltdata = np.linspace(1, len(KCtrac), len(KCtrac))
        
        XpltdatawithECmask = Xpltdata[KCtrac, ...]
        YpltdatawithECmask = np.asarray(cellproplist)[KCtrac, ...]
        
        XpltdatawithKCmask = Xpltdata[np.invert(KCtrac), ...]
        YpltdatawithKCmask = np.asarray(cellproplist)[np.invert(KCtrac), ...]
        
        plt.figure()
        # plot the EC scatters
        plt.scatter(XpltdatawithECmask, YpltdatawithECmask, c='b', marker='o', linewidths=4, label='EC')
#                 markersize=8, linewidth=0,
#                 markerfacecolor='blue',
#                 markeredgecolor='gray',
#                 markeredgewidth=2, label='Cell-{}'.format(EachCell+1))
        # plot the kc scatters
        plt.scatter(XpltdatawithKCmask, YpltdatawithKCmask, marker='o', linewidths=4, c='r', label='KC')
#                 markersize=8, linewidth=0,
#                 markerfacecolor='red',
#                 markeredgecolor='gray',
#                 markeredgewidth=2)
        plt.plot(Xpltdata, cellproplist, color='black', label='Cell-{}'.format(EachCell+1))
        
        plt.legend(loc='upper right')
        plt.show()
    xdata2fit, imgsignalmean2fit, popt, pcov = CurveAnalysis_instance.Fit_WholeImg(func, PMT_image_wholetrace_stack, KCtrac)
    
    
#    def func(x, a, b, c):
#        return a * np.exp(-b * x) + c
#    xdata = np.array([1,2,3,4,9,10,11,12])
#    ydata = np.array([0.59,0.57,0.49,0.46,0.43,0.41,0.41,0.39])
#    
#    plt.plot(xdata, ydata, 'b-', label='data')
#    
#    popt, pcov = curve_fit(func, xdata, ydata, maxfev=2000)
#    
#    plt.plot(xdata, func(xdata, *popt), 'r-', label='fit: a=%5.3f, b=%5.3f, c=%5.3f' % tuple(popt))
#    plt.legend(loc='upper right')
#    plt.show()
#    xActualdata = np.linspace(1, 12, num=12)
#    yActualdata = np.array([0.59,0.57,0.49,0.46,0.47,0.47,0.445,0.44,0.43,0.41,0.41,0.39])
    
#    yCorrected = yActualdata - func(xActualdata, *popt)
    
#    plt.plot(xActualdata, yCorrected, 'g-', label='corrected: a=%5.3f, b=%5.3f, c=%5.3f' % tuple(popt))