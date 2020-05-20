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
from skimage.filters import threshold_otsu, threshold_local
from skimage.segmentation import clear_border
from skimage.measure import label, perimeter, find_contours
from skimage.morphology import opening, closing, square, dilation, reconstruction, binary_erosion
from skimage.measure import regionprops
from skimage.restoration import denoise_tv_chambolle
from scipy.signal import convolve2d

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
        binary_adaptive_block_size = region_area*0.3
        if (binary_adaptive_block_size % 2) == 0:
            binary_adaptive_block_size += 1
#        thresh_regionbef = threshold_otsu(RawRegionImg)
        thresh_regionbef = threshold_local(RawRegionImg, binary_adaptive_block_size, offset=0)
        expanded_binary_region_bef = np.where(RawRegionImg >= thresh_regionbef, 1, 0)
        
        binarymask_bef = opening(expanded_binary_region_bef, square(int(cell_region_opening_factor)))
        expanded_binary_region_bef = closing(binarymask_bef, square(int(cell_region_closing_factor)))

        #---------------------------------------------------fill in the holes, prepare for contour recognition-----------------------------------------------------------
        seed_bef = np.copy(expanded_binary_region_bef)
        seed_bef[1:-1, 1:-1] = expanded_binary_region_bef.max()
        mask_bef = expanded_binary_region_bef

        filled_mask_bef = reconstruction(seed_bef, mask_bef, method='erosion')# The binary mask with filling holes
        
        # Calculate the background
        MeanIntensity_Background = np.mean(RawRegionImg[np.where(filled_mask_bef == 0)])
        """ MeanIntensity_Background is not accurate!!!
        """
        MeanIntensity_Background = 0 
        #----------------------------------------------------Clean up parts that don't belong to cell of interest---------------------------------------
        SubCellClearUpSize = int(region_area*0.35) # Assume that trash parts won't take up 35% of the whole cell boundbox area
#        print(region_area)
        IndividualCellCleared = filled_mask_bef.copy()

        clear_border(IndividualCellCleared)
        # label image regions, prepare for regionprops
        IndividualCell_label_image = label(IndividualCellCleared)
        
        for subcellregion in regionprops(IndividualCell_label_image,intensity_image = RawRegionImg.copy()):
            
            if subcellregion.area < SubCellClearUpSize: # Clean parts that are smaller than SubCellClearUpSize, which should result in only one main part left.

                for EachsubcellregionCoords in subcellregion.coords:
#                                print(EachsubcellregionCoords.shape)
                    filled_mask_bef[EachsubcellregionCoords[0], EachsubcellregionCoords[1]] = 0
        #------------------------------------------------------------------------------------------------------------------------------------------------         
     
        return filled_mask_bef, MeanIntensity_Background
    
    
    def smoothing_filled_mask(RawRegionImg, filled_mask_bef, region_area, threshold_factor):
        '''
        Given the cell filled mask, smooth the egde by convolution.
        '''
        
        # Shrink the image a bit.
#        filled_mask_bef = binary_erosion(filled_mask_bef, square(1))
        # Try to smooth the boundary.
        kernel = np.ones((5,5))
        filled_mask_convolve2d = convolve2d(filled_mask_bef, kernel, mode='same')                
        try:
            filled_mask_convolve2d = np.where(filled_mask_convolve2d >= threshold_otsu(filled_mask_convolve2d)*threshold_factor, 1, 0) # Here higher the threshold a bit to shrink the mask, make sure generated contour doesn't exceed.
        except:
            pass
        # Get rid of little patches.
#                self.filled_mask_convolve2d = opening(self.filled_mask_convolve2d, square(int(1)))
        
        #---------------------------------------------------fill in the holes, prepare for contour recognition-----------------------------------------------------------
        seed_bef = np.copy(filled_mask_convolve2d)
        seed_bef[1:-1, 1:-1] = filled_mask_convolve2d.max()
        mask_bef = filled_mask_convolve2d

        filled_mask_reconstructed = reconstruction(seed_bef, mask_bef, method='erosion')# The binary mask with filling holes        
        #----------------------------------------------------Clean up parts that don't belong to cell of interest---------------------------------------
        SubCellClearUpSize = int(region_area*0.30) # Assume that trash parts won't take up 35% of the whole cell boundbox area
#                    print('minsize: '+str(SubCellClearUpSize))
        IndividualCellCleared = filled_mask_reconstructed.copy()

        clear_border(IndividualCellCleared)
        # label image regions, prepare for regionprops
        IndividualCell_label_image = label(IndividualCellCleared)
        
        for subcellregion_convolve2d in regionprops(IndividualCell_label_image,intensity_image = RawRegionImg.copy()):
            
            if subcellregion_convolve2d.area < SubCellClearUpSize:

                for EachsubcellregionCoords in subcellregion_convolve2d.coords:
#                                print(EachsubcellregionCoords.shape)
                    filled_mask_reconstructed[EachsubcellregionCoords[0], EachsubcellregionCoords[1]] = 0
        #------------------------------------------------------------------------------------------------------------------------------------------------
        return filled_mask_reconstructed

    def contour(imagewithouthole, image, threshold):
        '''
        Return contour mask by eroding inward from filled cell mask.
        '''        
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
    
    def inwarddilationmask(binarycontour, imagewithouthole, dilationparameter):
        
        dilationimg = dilation(binarycontour, square(dilationparameter))
        
        contour_mask = dilationimg*imagewithouthole
        
        return contour_mask
