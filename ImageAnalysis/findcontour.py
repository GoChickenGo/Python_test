# -*- coding: utf-8 -*-
"""
Created on Mon May 20 17:51:19 2019

@author: xinmeng
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math
from skimage import data
from skimage.filters import threshold_otsu
from skimage.segmentation import clear_border
from skimage.measure import label, perimeter, find_contours
from skimage.morphology import opening, closing, square, dilation, reconstruction
from skimage.measure import regionprops
from skimage.restoration import denoise_tv_chambolle

class imageanalysistoolbox():
    '''
    Given intensity image, return cell filled mask.
    '''
    def get_cell_filled_mask(RawRegionImg, region_area, cell_region_opening_factor, cell_region_closing_factor):
        '''
        RawRegionImg: Original region image.
        region_area: Area of binary whole cell mask.
        cell_region_opening_factor: Number used for opening.
        cell_region_closing_factor: Number used for closing.
        '''
        #---------------------------------------------------Get binary cell image baseed on expanded current region image-------------------------------------------------
        RawRegionImg = denoise_tv_chambolle(RawRegionImg, weight=0.01)
        
        thresh_regionbef = threshold_otsu(RawRegionImg)
        expanded_binary_region_bef = np.where(RawRegionImg >= thresh_regionbef, 1, 0)
        
        binarymask_bef = opening(expanded_binary_region_bef, square(int(cell_region_opening_factor)))
        expanded_binary_region_bef = closing(binarymask_bef, square(int(cell_region_closing_factor)))

        #---------------------------------------------------fill in the holes, prepare for contour recognition-----------------------------------------------------------
        seed_bef = np.copy(expanded_binary_region_bef)
        seed_bef[1:-1, 1:-1] = expanded_binary_region_bef.max()
        mask_bef = expanded_binary_region_bef

        filled_mask_bef = reconstruction(seed_bef, mask_bef, method='erosion')# The binary mask with filling holes
        
        #----------------------------------------------------Clean up parts that don't belong to cell of interest---------------------------------------
        SubCellClearUpSize = int(region_area*0.35) # Assume that trash parts won't take up 35% of the whole cell boundbox area
#        print(region_area)
        IndividualCellCleared = filled_mask_bef.copy()

        clear_border(IndividualCellCleared)
        # label image regions, prepare for regionprops
        IndividualCell_label_image = label(IndividualCellCleared)
        
        for subcellregion in regionprops(IndividualCell_label_image,intensity_image = RawRegionImg.copy()):
            
            if subcellregion.area < SubCellClearUpSize:

                for EachsubcellregionCoords in subcellregion.coords:
#                                print(EachsubcellregionCoords.shape)
                    filled_mask_bef[EachsubcellregionCoords[0], EachsubcellregionCoords[1]] = 0
                    
        return filled_mask_bef
    
    '''
    Return contour mask by eroding inward from filled cell mask.
    '''
    def contour(self, imagewithouthole, image, threshold):
        
        contours = find_contours(imagewithouthole, threshold) # Find iso-valued contours in a 2D array for a given level value.
                
        for n, contour in enumerate(contours):
            #print(contour[1,0])
            col = contour[:, 1]
            row = contour[:, 0]
            col1 = [int(round(i)) for i in col]
            row1 = [int(round(i)) for i in row]
                    
            for m in range(len(col1)):
                image[row1[m], col1[m]] = 5
                #filledimg[contour[:, 0], contour[:, 1]] = 2
            #ax.plot(contour[:, 1]+minc, contour[:, 0]+minr, linewidth=3, color='yellow')
        binarycontour = np.where(image == 5, 1, 0)
        return binarycontour
    
    def inwarddilationmask(self, binarycontour, imagewithouthole, dilationparameter):
        
        dilationimg = dilation(binarycontour, square(dilationparameter))
        
        contour_mask = dilationimg*imagewithouthole
        
        return contour_mask
