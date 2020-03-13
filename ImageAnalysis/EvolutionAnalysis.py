# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 11:55:59 2020

@author: xinmeng
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math
from findcontour import imageanalysistoolbox
from skimage import data
from skimage.filters import threshold_otsu, threshold_local
from skimage.segmentation import clear_border
from skimage.measure import label, perimeter, find_contours
from skimage.morphology import closing, square, opening, reconstruction, skeletonize, convex_hull_image, dilation, thin, binary_erosion
from skimage.measure import regionprops
from skimage.color import label2rgb
from skimage.restoration import denoise_tv_chambolle

from scipy.signal import convolve2d
import numpy.lib.recfunctions as rfn
import copy

#================================================================ImageStackAnalysis============================================================
class ImageStackAnalysis():
    '''
    Given the time lapse image stack, return individual cell properties.
    '''
    def generate_mask(self, imagestack, openingfactor, closingfactor, binary_adaptive_block_size):
#        self.openingfactor=int(openingfactor)#2
#        self.closingfactor=int(closingfactor) #3     
        
        template_image = imagestack[0,:,:] # Get the first image of the stack to generate the mask for Region Proposal
        
        template_image = denoise_tv_chambolle(template_image, weight=0.01) # Denoise the image.
        
#        thresh = threshold_otsu(template_image)#-0.7#-55
        # -----------------------------------------------Adaptive thresholding-----------------------------------------------
#        block_size = binary_adaptive_block_size#335
        AdaptiveThresholding = threshold_local(template_image, binary_adaptive_block_size, offset=0)
        BinaryMask = template_image >= AdaptiveThresholding
        OpeningBinaryMask = opening(BinaryMask, square(int(openingfactor)))
        RegionProposalMask = closing(OpeningBinaryMask, square(int(closingfactor)))
        
        RegionProposalOriginalImage = RegionProposalMask*template_image
        
        return RegionProposalMask, RegionProposalOriginalImage#Segimg_bef, Segimg_aft, self.mask_bef, self.mask_aft, thresh
    
    def get_cell_properties_Roundstack(self, imagestack, RegionProposalMask, smallest_size, contour_thres, contour_dilationparameter, cell_region_opening_factor, cell_region_closing_factor):
    
        cleared = RegionProposalMask.copy()
        clear_border(cleared)
        # label image regions, prepare for regionprops
        label_image = label(cleared)
        
        dtype = [('Mean intensity', float), ('Mean intensity in contour', float), ('Circularity', float), ('Contour soma ratio', float)]
        
        CellPropDictEachRound = {}
        
        for EachRound in range(len(imagestack)):
            
            region_mean_intensity_list = []
            region_circularit_list = []
            region_meanintensity_contour_list = []        
            RegionLoopNumber = 0
            dirforcellprp={}
            
            if EachRound == 0: # Plot the label figure in the first round. 

                plt.figure()
                self.fig_showlabel, self.ax_showlabel = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
                self.ax_showlabel.imshow(imagestack[0])#Show the first image
            
            for region in regionprops(label_image,intensity_image = imagestack[0]): # USE first image in stack before perfusion as template 
                
                # skip small images
                if region.area > smallest_size:
             
                    # draw rectangle around segmented coins
                    minr, minc, maxr, maxc = region.bbox
                    
                    #region_mean_intensity = region.mean_intensity #mean intensity of the region, 0 pixels in label are omitted.
                    #allpixelnum = region.bbox_area
                    #labeledpixelnum = region.area #number of pixels in region omitting 0.
                    filledimg = region.filled_image 
                    filledperimeter = perimeter(filledimg)
                    regioncircularity = (4 * math.pi * region.filled_area) / (filledperimeter * filledperimeter) # region.perimeter will count in perimeters from the holes inside
                    #Sliced_binary_region_image = region.image
#                    self.intensityimage_intensity = region.intensity_image # need a copy of this cause region will be altered by s.contour
                    
                    # Based on the boundingbox for each cell from first image in the stack, raw image of slightly larger region is extracted from each round.
                    self.RawRegionImg = imagestack[EachRound][max(minr-4,0):min(maxr+4, imagestack[0].shape[0]), max(minc-4,0):min(maxc+4, imagestack[0].shape[0])] # Raw region image 
                    
                    self.RawRegionImg_for_contour = self.RawRegionImg.copy()

                    #---------Get the cell filled mask-------------
                    self.filled_mask_bef = imageanalysistoolbox.get_cell_filled_mask(RawRegionImg = self.RawRegionImg, region_area = region.area, cell_region_opening_factor = cell_region_opening_factor, cell_region_closing_factor = cell_region_closing_factor)

                    filled_origin_image_intensity = self.RawRegionImg*self.filled_mask_bef # Intensity image of cell with hole filled
                    filled_mean_bef = np.mean(self.RawRegionImg[np.where(self.filled_mask_bef == 1)]) # Mean pixel value of filled raw cell area
                    
                    self.filled_mask_convolve2d = imageanalysistoolbox.smoothing_filled_mask(self.RawRegionImg, filled_mask_bef = self.filled_mask_bef, region_area = region.area)
                    
                    # Find contour along filled image
                    imageanalysistoolbox_instacne=imageanalysistoolbox()
                    contour_mask_bef = imageanalysistoolbox_instacne.contour(self.filled_mask_convolve2d, self.RawRegionImg_for_contour.copy(), contour_thres)
                    # after here self.intensityimage_intensity is changed from contour labeled with number 5 to binary image
                    self.contour_mask_of_cell = imageanalysistoolbox_instacne.inwarddilationmask(contour_mask_bef ,self.filled_mask_bef, contour_dilationparameter)   
                
#                    contourimage_intensity_aft = s.contour(self.filled_mask_aft, self.regionimage_after_for_contour.copy(), self.contour_thres) # after here self.intensityimage_intensity is changed with contour labeled with number 5
#                    self.contour_mask_of_intensity_aft = s.inwarddilationmask(contourimage_intensity_aft ,self.filled_mask_aft, self.contour_dilationparameter)
    
                    contour_mean_bef = np.mean(self.RawRegionImg[np.where(self.contour_mask_of_cell == 1)])
#                    contour_mean_aft = np.mean(self.regionimage_after[np.where(self.contour_mask_of_intensity_aft == 1)])  
                    
                    self.cell_soma_mask_bef = self.filled_mask_bef - self.contour_mask_of_cell
                    
                    contour_origin_image_intensity = self.RawRegionImg*self.contour_mask_of_cell # Intensity image of cell contour
                    soma_origin_image_intensity = self.RawRegionImg*self.cell_soma_mask_bef # Intensity image of cell soma part
    
                    soma_mean_bef = np.mean(self.RawRegionImg[np.where(self.cell_soma_mask_bef == 1)])#Mean pixel value of soma area
                    
                    contour_soma_ratio = contour_mean_bef/soma_mean_bef

                    region_mean_intensity_list.append(filled_mean_bef)# Mean intensity of filled image
                    
                    region_circularit_list.append(regioncircularity)
                    region_meanintensity_contour_list.append(contour_mean_bef)                
                    dirforcellprp[RegionLoopNumber] = (filled_mean_bef, contour_mean_bef, regioncircularity, contour_soma_ratio)
                    
                    RegionLoopNumber = RegionLoopNumber+1
                    
                    #--------------------------------------------------Add red boundingbox to axis----------------------------------------------
                    rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr, fill=False, edgecolor='red', linewidth=2)

                    contour_mean_bef_rounded = str(round(contour_mean_bef, 3))[0:5]
                    if EachRound == 0:
                        self.ax_showlabel.add_patch(rect)
                        self.ax_showlabel.text((maxc + minc)/2, (maxr + minr)/2, 'Cell-{}, {}: {}'.format(RegionLoopNumber, 'c_m', contour_mean_bef_rounded),fontsize=8, color='yellow', style='italic')#,bbox={'facecolor':'red', 'alpha':0.3, 'pad':8})
                                       
#            print('Total region number: {}'.format(RegionLoopNumber))
            cell_properties = np.zeros(len(region_mean_intensity_list), dtype = dtype)
            for p in range(RegionLoopNumber):
                cell_properties[p] = dirforcellprp[p]
            
            CellPropDictEachRound['RoundSequence{}'.format(EachRound+1)] = cell_properties
            
            if EachRound == 0:
                self.ax_showlabel.set_axis_off()
    #            if EachRound == 0:
                plt.show()
            
        return CellPropDictEachRound


#================================================================CellContourScanGenerator============================================================
class CellContourScanGenerator():
    '''
    Given the image, return smoothed cell contour coordinates for contour scanning.
    '''
    def generate_mask(self, image, openingfactor, closingfactor, binary_adaptive_block_size):

        template_image = image # Get the first image of the stack to generate the mask for Region Proposal
        
        template_image = denoise_tv_chambolle(template_image, weight=0.01) # Denoise the image.
        
#        thresh = threshold_otsu(template_image)#-0.7#-55
        # -----------------------------------------------Adaptive thresholding-----------------------------------------------
#        block_size = binary_adaptive_block_size#335
        AdaptiveThresholding = threshold_local(template_image, binary_adaptive_block_size, offset=0)
        BinaryMask = template_image >= AdaptiveThresholding
        OpeningBinaryMask = opening(BinaryMask, square(int(openingfactor)))
        RegionProposalMask = closing(OpeningBinaryMask, square(int(closingfactor)))
        
        RegionProposalOriginalImage = RegionProposalMask*template_image
        
        return RegionProposalMask, RegionProposalOriginalImage#Segimg_bef, Segimg_aft, self.mask_bef, self.mask_aft, thresh
    
    def get_Skeletonized_contour(self, image, RegionProposalMask, smallest_size, contour_thres, contour_dilationparameter, cell_region_opening_factor, cell_region_closing_factor):
    
        cleared = RegionProposalMask.copy()
        clear_border(cleared)
        # label image regions, prepare for regionprops
        label_image = label(cleared)
                
        CellSkeletonizedContourDict = {}
            
        for region in regionprops(label_image,intensity_image = image): # USE first image in stack before perfusion as template 
            
            # skip small images
            if region.area > smallest_size:
         
                # draw rectangle around segmented coins
                minr, minc, maxr, maxc = region.bbox
                
                #region_mean_intensity = region.mean_intensity #mean intensity of the region, 0 pixels in label are omitted.
                
                # Based on the boundingbox for each cell from first image in the stack, raw image of slightly larger region is extracted from each round.
                self.RawRegionImg = image[max(minr-4,0):min(maxr+4, image[0].shape[0]), max(minc-4,0):min(maxc+4, image[0].shape[0])] # Raw region image 
                
                self.RawRegionImg_for_contour = self.RawRegionImg.copy()
                
                #---------Get the cell filled mask-------------
                self.filled_mask_bef = imageanalysistoolbox.get_cell_filled_mask(RawRegionImg = self.RawRegionImg, region_area = region.area, cell_region_opening_factor = cell_region_opening_factor, cell_region_closing_factor = cell_region_closing_factor)
# =============================================================================
#                 #---------------------------------------------------Get binary cell image baseed on expanded current region image-------------------------------------------------
# #                self.RawRegionImg = denoise_tv_chambolle(self.RawRegionImg, weight=0.01)
# #                
# #                thresh_regionbef = threshold_otsu(self.RawRegionImg)
# #                self.expanded_binary_region_bef = np.where(self.RawRegionImg >= thresh_regionbef, 1, 0)
# #                
# #                binarymask_bef = opening(self.expanded_binary_region_bef, square(int(cell_region_opening_factor)))
# #                self.expanded_binary_region_bef = closing(binarymask_bef, square(int(cell_region_closing_factor)))
# #
# #                #---------------------------------------------------fill in the holes, prepare for contour recognition-----------------------------------------------------------
# #                seed_bef = np.copy(self.expanded_binary_region_bef)
# #                seed_bef[1:-1, 1:-1] = self.expanded_binary_region_bef.max()
# #                mask_bef = self.expanded_binary_region_bef
# #        
# #                self.filled_mask_bef = reconstruction(seed_bef, mask_bef, method='erosion')# The binary mask with filling holes
# #                
# #                #----------------------------------------------------Clean up parts that don't belong to cell of interest---------------------------------------
# #                SubCellClearUpSize = int(region.area*0.35) # Assume that trash parts won't take up 35% of the whole cell boundbox area
# #                print(region.area)
# #                IndividualCellCleared = self.filled_mask_bef.copy()
# #
# #                clear_border(IndividualCellCleared)
# #                # label image regions, prepare for regionprops
# #                IndividualCell_label_image = label(IndividualCellCleared)
# #                
# #                for subcellregion in regionprops(IndividualCell_label_image,intensity_image = self.RawRegionImg.copy()):
# #                    
# #                    if subcellregion.area < SubCellClearUpSize:
# #
# #                        for EachsubcellregionCoords in subcellregion.coords:
# ##                                print(EachsubcellregionCoords.shape)
# #                            self.filled_mask_bef[EachsubcellregionCoords[0], EachsubcellregionCoords[1]] = 0
#                 #------------------------------------------------------------------------------------------------------------------------------------------------
# =============================================================================
                
                self.filled_mask_convolve2d = imageanalysistoolbox.smoothing_filled_mask(self.RawRegionImg, filled_mask_bef = self.filled_mask_bef, region_area = region.area)
# =============================================================================
#                 # Shrink the image a bit.
#                 self.filled_mask_bef = binary_erosion(self.filled_mask_bef, square(2))
#                 # Try to smooth the boundary.
#                 kernel = np.ones((5,5))
#                 self.filled_mask_convolve2d = convolve2d(self.filled_mask_bef, kernel, mode='same')                
#                 try:
#                     self.filled_mask_convolve2d = np.where(self.filled_mask_convolve2d >= threshold_otsu(self.filled_mask_convolve2d)*1.2, 1, 0) # Here higher the threshold a bit to shrink the mask, make sure generated contour doesn't exceed.
#                 except:
#                     pass
#                 # Get rid of little patches.
# #                self.filled_mask_convolve2d = opening(self.filled_mask_convolve2d, square(int(1)))
#                 #----------------------------------------------------Clean up parts that don't belong to cell of interest---------------------------------------
#                 SubCellClearUpSize = int(region.area*0.30) # Assume that trash parts won't take up 35% of the whole cell boundbox area
# #                    print('minsize: '+str(SubCellClearUpSize))
#                 IndividualCellCleared = self.filled_mask_convolve2d.copy()
# 
#                 clear_border(IndividualCellCleared)
#                 # label image regions, prepare for regionprops
#                 IndividualCell_label_image = label(IndividualCellCleared)
#                 
#                 for subcellregion_convolve2d in regionprops(IndividualCell_label_image,intensity_image = self.RawRegionImg.copy()):
#                     
#                     if subcellregion_convolve2d.area < SubCellClearUpSize:
# 
#                         for EachsubcellregionCoords in subcellregion_convolve2d.coords:
# #                                print(EachsubcellregionCoords.shape)
#                             self.filled_mask_convolve2d[EachsubcellregionCoords[0], EachsubcellregionCoords[1]] = 0
#                 #------------------------------------------------------------------------------------------------------------------------------------------------
# =============================================================================
                # Find contour along filled image
                imageanalysistoolbox_instacne=imageanalysistoolbox()
                contour_mask_bef = imageanalysistoolbox_instacne.contour(self.filled_mask_convolve2d, self.RawRegionImg_for_contour.copy(), contour_thres) 

                # after here self.intensityimage_intensity is changed from contour labeled with number 5 to binary image
                contour_mask_of_cell = imageanalysistoolbox_instacne.inwarddilationmask(contour_mask_bef.copy() ,self.filled_mask_convolve2d, contour_dilationparameter)

                contour_origin_image_intensity = self.RawRegionImg*contour_mask_of_cell # Intensity image of cell contour

# =============================================================================
#                 # Get the skeleton of the contour, same as contour_mask_bef
# #                contour_skeleton = skeletonize(contour_mask_of_cell)#, method='lee'                
#                 thinned_partial = thin(contour_mask_bef.copy(), max_iter=25)
# =============================================================================
                # -----------------------if cell appears on the border, complete the circle by connecting the two ends.----------------------------------
#                print(len(np.where(thinned_partial[:, 0]==True)[0]))
                if len(np.where(thinned_partial[:, 0]==True)[0]) > 1:#return the column index of edge pixels.
                    print('False on edge.')
#                thinned_partial[self.RawRegionImg.shape[0], :]==True
#                #---------------------------------------------------fill in the holes of the skeleton-----------------------------------------------------------
#                seed_bef_2 = np.copy(contour_skeleton)
#                seed_bef_2[1:-1, 1:-1] = contour_skeleton.max()
#                mask_bef_2 = contour_skeleton
#        
#                filled_mask_contour_skeleton = reconstruction(seed_bef_2, mask_bef_2, method='erosion')# The binary mask with filling holes
                
#                contour_skeleton_pruned = opening(contour_skeleton, square(int(cell_prune_opening_factor)))

                figure, (ax1, ax2) = plt.subplots(2, 1, figsize=(10,10))
        
                ax1.imshow(self.RawRegionImg, cmap = plt.cm.gray)
                ax2.imshow(contour_mask_bef, cmap = plt.cm.gray)
#                ax2.imshow(contour_mask_of_cell, cmap = plt.cm.gray)
#                ax2.imshow(thinned_partial, cmap = plt.cm.gray)           
#                figure.tight_layout()
                plt.show()
                
                #--------------------------------------------------Add red boundingbox to axis----------------------------------------------
#                rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr, fill=False, edgecolor='red', linewidth=2)
#
#                contour_mean_bef_rounded = str(round(contour_mean_bef, 3))[0:5]

#                self.ax_showlabel.add_patch(rect)
#                self.ax_showlabel.text((maxc + minc)/2, (maxr + minr)/2, 'Cell-{}, {}: {}'.format(RegionLoopNumber, 'c_m', contour_mean_bef_rounded),fontsize=8, color='yellow', style='italic')#,bbox={'facecolor':'red', 'alpha':0.3, 'pad':8})
                                   
            
        return CellSkeletonizedContourDict
    
if __name__ == "__main__":
    
    from skimage.io import imread
    #Providing row and col index
    PMT_image = imread(r'D:\XinMeng\imageCollection\Round2_Coord3_R1500C1500_PMT_2.tif', as_gray=True)[:, 50:550]
    
    CellContour_instance = CellContourScanGenerator()
    
    RegionProposalMask, RegionProposalOriginalImage = CellContour_instance.generate_mask(PMT_image, openingfactor=2, 
                                                                                                closingfactor=3, binary_adaptive_block_size=335)#256(151) 500(335)
    
    CellPropDictEachRound = CellContour_instance.get_Skeletonized_contour(PMT_image, RegionProposalMask, smallest_size=300, contour_thres=0.001, 
                                                                                       contour_dilationparameter=11, cell_region_opening_factor=1, cell_region_closing_factor=2)

