# -*- coding: utf-8 -*-
"""
Created on Thu Oct 31 10:20:54 2019

@author: xinmeng
"""

# -*- coding: utf-8 -*-
"""
Created on Wed May  1 20:20:32 2019

@author: Meng
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math
try:
    from ImageAnalysis.findcontour import imageanalysistoolbox
except:
    from findcontour import imageanalysistoolbox
from skimage import data
from skimage.filters import threshold_otsu, threshold_local
from skimage.segmentation import clear_border
from skimage.measure import label, perimeter, find_contours
from skimage.morphology import closing, square, opening, reconstruction
from skimage.measure import regionprops
from skimage.color import label2rgb
from skimage.restoration import denoise_tv_chambolle
import numpy.lib.recfunctions as rfn

class ImageAnalysis():
    def __init__(self, value1, value2, ):
        self.img_before_tem = value1
        self.img_after_tem = value2
        self.Img_before = self.img_before_tem.copy()
        self.Img_after = self.img_after_tem.copy()

        
    def applyMask(self, openingfactor, closingfactor, binary_adaptive_block_size):
        self.openingfactor=int(openingfactor)#2
        self.closingfactor=int(closingfactor) #3       
        self.Img_before = denoise_tv_chambolle(self.Img_before, weight=0.01)
        self.Img_after = denoise_tv_chambolle(self.Img_after, weight=0.01)
        
        thresh = threshold_otsu(self.Img_before)#-0.7#-55
        # -----------------------------------------------Adaptive thresholding-----------------------------------------------
        block_size = binary_adaptive_block_size#335
        binary_adaptive = threshold_local(self.Img_before, block_size, offset=0)
        binary_adaptive1 = self.Img_before >= binary_adaptive
        binarymask = opening(binary_adaptive1, square(self.openingfactor))
        self.mask_bef = closing(binarymask, square(self.closingfactor))
        
        Segimg_bef = self.mask_bef*self.Img_before.copy()

        binary_adaptive = threshold_local(self.Img_after, block_size, offset=0)
        binary_adaptive2 = self.Img_after >= binary_adaptive
        binarymask = opening(binary_adaptive2, square(self.openingfactor))
        self.mask_aft = closing(binarymask, square(self.closingfactor))
       
        Segimg_aft = self.mask_aft*self.Img_after.copy()
              
        #fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
        #ax.imshow(Segimg_aft) #fig 3
        
        return Segimg_bef, Segimg_aft, self.mask_bef, self.mask_aft, thresh
    
    '''    
    def ratio(self, value1, value2):
        self.Segimg_bef_ratio = np.where(value1 == 0, 1, value1)
        Ratio = value2/self.Segimg_bef_ratio
        
        #fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
        #ax.imshow(Ratio) #fig 3 
        return Ratio
    '''
    def get_intensity_properties(self, smallest_size, theMask, threshold, intensity_bef, intensty_aft, i, j, contour_thres, contour_dilationparameter, cell_region_opening, cell_region_closing):
        # remove artifacts connected to image border
        self.Labelmask = theMask # mask for general cell localization, so dosen't matter too much whose it is
        self.Imagbef = intensity_bef # Thresholded whole image
        self.Imageaft = intensty_aft        
        self.row_num = i
        self.column_num = j
        self.threshold = threshold
        self.contour_thres = contour_thres
        self.contour_dilationparameter = contour_dilationparameter
        self.cell_openingfactor = cell_region_opening#1
        self.cell_closingfactor = cell_region_closing#5
        
        cleared = self.Labelmask.copy()
        clear_border(cleared)
                # label image regions
        label_image = label(cleared)
        dtype = [('Row index', 'i4'), ('Column index', 'i4'), ('Mean intensity', float), ('Mean intensity in contour', float), ('Circularity', float), ('Contour soma ratio', float), ('Change', float)]
        
        region_mean_intensity_list = []
        region_circularit_list = []
        region_meanintensity_contour_list = []
        
        self.individual_cell_dic_bef = {}
        self.individual_cell_dic_aft = {}
        
        #Get 2 more pixels out of boundary box in case of cell movements
        #We need to add 2 rows and columns of 0 to the whole FOV in case cells detected at the edge
        expanded_image_container_bef = np.zeros((self.Imagbef.shape[0]+4, self.Imagbef.shape[1]+4))
        expanded_image_container_bef[2:self.Imagbef.shape[0]+2, 2:self.Imagbef.shape[1]+2] = self.Imagbef
        
        expanded_image_container_aft = np.zeros((self.Imageaft.shape[0]+4, self.Imageaft.shape[1]+4))
        expanded_image_container_aft[2:self.Imageaft.shape[0]+2, 2:self.Imageaft.shape[1]+2] = self.Imageaft
        
        loopmun = 0
        dirforcellprp={}
        for region in regionprops(label_image,intensity_image=self.Imagbef): # USE image before perfusion as template
            
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
                self.intensityimage_intensity = region.intensity_image # need a copy of this cause region will be altered by s.contour
                
                self.regionimage_before = expanded_image_container_bef[minr:maxr+4, minc:maxc+4] # Raw region image 
                self.regionimage_after = expanded_image_container_aft[minr:maxr+4, minc:maxc+4]
                
                self.regionimage_before_for_contour = self.regionimage_before.copy()
                self.regionimage_after_for_contour = self.regionimage_after.copy()
                
                self.individual_cell_dic_bef[str(loopmun)] = self.regionimage_before_for_contour # put each cell region into a dictionary
                self.individual_cell_dic_aft[str(loopmun)] = self.regionimage_after_for_contour
                '''
                plt.figure()
                plt.imshow(self.regionimage_before, cmap = plt.cm.gray) 
                plt.show() 
                '''
                #print(np.max(self.regionimage_before))
                # Get binary cell image baseed on expanded current region image
                thresh_regionbef = threshold_otsu(self.regionimage_before)
                self.expanded_binary_region_bef = np.where(self.regionimage_before >= thresh_regionbef, 1, 0)
                
                binarymask_bef = opening(self.expanded_binary_region_bef, square(self.cell_openingfactor))
                self.expanded_binary_region_bef = closing(binarymask_bef, square(self.cell_closingfactor))
        
                thresh_regionaft = threshold_otsu(self.regionimage_after)
                self.expanded_binary_region_aft = np.where(self.regionimage_after >= thresh_regionaft, 1, 0)
                
                binarymask_aft = opening(self.expanded_binary_region_aft, square(self.cell_openingfactor))
                self.expanded_binary_region_aft = closing(binarymask_aft, square(self.cell_closingfactor))
                '''
                print('Original raw image:')
                plt.figure()
                plt.imshow(self.regionimage_before, cmap = plt.cm.gray) 
                plt.show()  
                '''
                # fill in the holes
                seed_bef = np.copy(self.expanded_binary_region_bef)
                seed_bef[1:-1, 1:-1] = self.expanded_binary_region_bef.max()
                mask_bef = self.expanded_binary_region_bef
        
                self.filled_mask_bef = reconstruction(seed_bef, mask_bef, method='erosion')# The binary mask with filling holes
                
                seed_aft = np.copy(self.expanded_binary_region_aft)
                seed_aft[1:-1, 1:-1] = self.expanded_binary_region_aft.max()
                mask_aft = self.expanded_binary_region_aft
        
                self.filled_mask_aft = reconstruction(seed_aft, mask_aft, method='erosion')# fill in the holes
                
                filled_origin_image_intensity = self.regionimage_before*self.filled_mask_bef # Intensity image of cell with hole filled
                filled_mean_bef = np.mean(self.regionimage_before[np.where(self.filled_mask_bef == 1)]) # Mean pixel value of filled raw cell area
                
                # Find contour along filled image
                s=imageanalysistoolbox()
                contour_mask_bef = s.contour(self.filled_mask_bef, self.regionimage_before_for_contour.copy(), self.contour_thres) # after here self.intensityimage_intensity is changed from contour labeled with number 5 to binary image
                self.contour_mask_of_intensity_bef = s.inwarddilationmask(contour_mask_bef ,self.filled_mask_bef, self.contour_dilationparameter)   
            
                contourimage_intensity_aft = s.contour(self.filled_mask_aft, self.regionimage_after_for_contour.copy(), self.contour_thres) # after here self.intensityimage_intensity is changed with contour labeled with number 5
                self.contour_mask_of_intensity_aft = s.inwarddilationmask(contourimage_intensity_aft ,self.filled_mask_aft, self.contour_dilationparameter)

                contour_mean_bef = np.mean(self.regionimage_before[np.where(self.contour_mask_of_intensity_bef == 1)])
                contour_mean_aft = np.mean(self.regionimage_after[np.where(self.contour_mask_of_intensity_aft == 1)])  
                
                self.cell_soma_mask_bef = self.filled_mask_bef - self.contour_mask_of_intensity_bef
                
                contour_origin_image_intensity = self.regionimage_before*self.contour_mask_of_intensity_bef # Intensity image of cell contour
                soma_origin_image_intensity = self.regionimage_before*self.cell_soma_mask_bef # Intensity image of cell soma part

                soma_mean_bef = np.mean(self.regionimage_before[np.where(self.cell_soma_mask_bef == 1)])#Mean pixel value of soma area
                
                contour_soma_ratio = contour_mean_bef/soma_mean_bef
                contour_change_ratio = contour_mean_aft/contour_mean_bef

                plt.figure()
                plt.imshow(self.contour_mask_of_intensity_bef, cmap = plt.cm.gray)       
                plt.show()
                
                plt.figure()
                plt.imshow(self.contour_mask_of_intensity_aft, cmap = plt.cm.gray)       
                plt.show()
                '''
                '''
                print('Contour soma ratio: '+str(round(contour_soma_ratio, 3)))
                print('Contour image:')                                
                plt.figure()
                plt.imshow(contour_origin_image_intensity, cmap = plt.cm.gray)       
                plt.show()
                
                print('Soma image:')                                
                plt.figure()
                plt.imshow(soma_origin_image_intensity, cmap = plt.cm.gray)       
                plt.show()                

                #print(region_mean_intensity)
                region_mean_intensity_list.append(filled_mean_bef)# Mean intensity of filled image
                
                region_circularit_list.append(regioncircularity)
                region_meanintensity_contour_list.append(contour_mean_bef)                
                dirforcellprp[loopmun] = (self.row_num, self.column_num, filled_mean_bef, contour_mean_bef, regioncircularity, contour_soma_ratio, contour_change_ratio)
                
                loopmun = loopmun+1
        print('Total region number: {}'.format(loopmun))
        cell_properties = np.zeros(len(region_mean_intensity_list), dtype = dtype)
        for p in range(loopmun):
            cell_properties[p] = dirforcellprp[p]
            
        return cell_properties, self.expanded_binary_region_bef, contour_origin_image_intensity, self.intensityimage_intensity, contour_change_ratio                
        #return self.individual_cell_dic_bef, self.individual_cell_dic_aft
    
    def cell_processing(self, individual_cell_bef, individual_cell_aft):# for each single cell
        self.regionimage_before_individualcell = individual_cell_bef
        self.regionimage_after_individualcell = individual_cell_aft
        self.cell_openingfactor = 1
        self.cell_closingfactor = 5
        
        # Get binary cell image baseed on expanded current region image
        thresh_regionbef = threshold_otsu(self.regionimage_before_individualcell)
        self.expanded_binary_region_bef = np.where(self.regionimage_before_individualcell >= thresh_regionbef, 1, 0)
        
        binarymask_bef = opening(self.expanded_binary_region_bef, square(self.cell_openingfactor))
        self.expanded_binary_region_bef = closing(binarymask_bef, square(self.cell_closingfactor))

        thresh_regionaft = threshold_otsu(self.regionimage_after_individualcell)
        self.expanded_binary_region_aft = np.where(self.regionimage_after_individualcell >= thresh_regionaft, 1, 0)
        
        binarymask_aft = opening(self.expanded_binary_region_aft, square(self.cell_openingfactor))
        self.expanded_binary_region_aft = closing(binarymask_aft, square(self.cell_closingfactor))
        
        plt.figure()
        plt.imshow(self.expanded_binary_region_bef, cmap = plt.cm.gray)       
        plt.show()        
        
        seed = np.copy(self.expanded_binary_region_bef)
        seed[1:-1, 1:-1] = self.expanded_binary_region_bef.max()
        mask = self.expanded_binary_region_bef

        filled = reconstruction(seed, mask, method='erosion')
        plt.figure()
        plt.imshow(filled, cmap = plt.cm.gray)       
        plt.show()   
        
        s=imageanalysistoolbox()
        contour_mask_bef = s.contour(self.expanded_binary_region_bef, self.regionimage_before_individualcell.copy(), self.contour_thres) # after here self.intensityimage_intensity is changed from contour labeled with number 5 to binary image
        contour_mask_of_intensity_bef = s.inwarddilationmask(contour_mask_bef ,self.expanded_binary_region_bef, self.contour_dilationparameter)   

        contourimage_intensity_aft = s.contour(self.expanded_binary_region_aft, self.regionimage_after_individualcell.copy(), self.contour_thres) # after here self.intensityimage_intensity is changed with contour labeled with number 5
        contour_mask_of_intensity_aft = s.inwarddilationmask(contourimage_intensity_aft ,self.expanded_binary_region_aft, self.contour_dilationparameter) 

        plt.figure()
        #plt.imshow(contour_mask_of_intensity_bef, cmap = plt.cm.gray)
        plt.imshow(self.regionimage_before_individualcell, cmap = plt.cm.gray)       
        plt.show()
        
        cleared = self.expanded_binary_region_bef.copy() # Necessary for region iteration
        clear_border(cleared)
        label_image = label(cleared)

        for sub_region in regionprops(label_image, self.regionimage_before_individualcell):
            
            if sub_region.area < 3:#int(np.size(self.regionimage_before_individualcell)*0.1):
                for i in range(len(sub_region.coords)):
                    #print(sub_region.coords[i])
                    contour_mask_of_intensity_bef[sub_region.coords[i][0], sub_region.coords[i][1]] = 0
                    
        cleared_1 = self.expanded_binary_region_aft.copy()
        clear_border(cleared_1)
        label_image_aft = label(cleared_1)
        
        for sub_region_aft in regionprops(label_image_aft, self.regionimage_after_individualcell):
      
            if sub_region_aft.area < 3:#int(np.size(self.regionimage_after_individualcell)*0.1):
                for j in range(len(sub_region_aft.coords)):
                    #print(sub_region_aft.coords[j])
                    contour_mask_of_intensity_aft[sub_region_aft.coords[j][0], sub_region_aft.coords[j][1]] = 0
            
        plt.figure()
        plt.imshow(contour_mask_of_intensity_bef, cmap = plt.cm.gray)
        plt.show()
        
    def showlabel(self, smallest_size, theMask, original_intensity, threshold, i, j, cell_properties):
        # remove artifacts connected to image border
        self.Labelmask = theMask
        self.OriginImag = original_intensity
        self.row_num = i
        self.column_num = j
        self.threshold = threshold
        
        cleared = self.Labelmask.copy()
        clear_border(cleared)
                # label image regions
        label_image = label(cleared)
        #image_label_overlay = label2rgb(label_image, image=image)
        
        plt.figure()
        self.fig_showlabel, self.ax_showlabel = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
        #plt.figure(self.row_num+self.column_num)
        self.ax_showlabel.imshow(label_image)
        
        loopmun1 = 0
        for region in regionprops(label_image,intensity_image=self.OriginImag):
            # skip small images
            if region.area > smallest_size:
                               
                # draw rectangle around segmented coins
                minr, minc, maxr, maxc = region.bbox
                rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr, fill=False, edgecolor='red', linewidth=2)
                self.ax_showlabel.add_patch(rect)
                filledimg = region.filled_image #Binary region image with filled holes which has the same size as bounding box.
                '''
                contours = find_contours(filledimg, 0.8) # Find iso-valued contours in a 2D array for a given level value.
                
                for n, contour in enumerate(contours):
                    self.ax_showlabel.plot(contour[:, 1]+minc, contour[:, 0]+minr, linewidth=1, color='yellow')
                '''
                x1 = cell_properties['Change'][loopmun1]
                x2 = cell_properties['Mean intensity in contour'][loopmun1]
                x3 = cell_properties['Circularity'][loopmun1]                
                #circularity = (4 * math.pi * region.filled_area) / (filledperimeter * filledperimeter) # region.perimeter will count in perimeters from the holes inside
                self.ax_showlabel.text((maxc + minc)/2, (maxr + minr)/2, str(round(x1, 3))+',  '+str(round(x2, 3)),fontsize=8, color='yellow', style='italic')#,bbox={'facecolor':'red', 'alpha':0.3, 'pad':8})
                
                loopmun1 = loopmun1+1
        #plt.show()       
        self.ax_showlabel.set_axis_off()
        plt.show()
        #plt.tight_layout()
        #self.ax_showlabel.show()
        
        #return filledimg, Sliced_binary_region_image, intensityimage
    def showlabel_with_rank(self, smallest_size, theMask, original_intensity, cpstart, cpend, cell_properties, thekey_attri, num_hits):
        self.Labelmask = theMask
        self.OriginImag = original_intensity
        self.cp_start = cpstart
        self.cp_end = cpend
        #self.threshold = threshold
        self.thekey_attri= thekey_attri
        
        #cell_properties = cell_properties[:num_hits]
        cell_properties = cell_properties[self.cp_start:self.cp_end+1] # trace back to i,j corresponding locations in cell properties list.
        cleared = self.Labelmask.copy()
        clear_border(cleared)
                # label image regions
        label_image = label(cleared)
        #image_label_overlay = label2rgb(label_image, image=image)
        
        
        fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
        ax.imshow(label_image)
        
        loopmun1 = 0
        for region in regionprops(label_image,intensity_image=self.OriginImag):
            # skip small images
            if region.area > smallest_size:         
                # draw rectangle around segmented coins

                #filledimg = region.filled_image
                x2 = cell_properties['Mean intensity in contour'][loopmun1]
                x3 = cell_properties['Ranking'][loopmun1]
                if x3 < num_hits:
                    minr, minc, maxr, maxc = region.bbox
                    rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr, fill=False, edgecolor='red', linewidth=2)
                    ax.add_patch(rect)                    
                    #circularity = (4 * math.pi * region.filled_area) / (filledperimeter * filledperimeter) # region.perimeter will count in perimeters from the holes inside
                    ax.text((maxc + minc)/2, (maxr + minr)/2, str(round(x2, 3))+ ',  '+str(x3), fontsize=8, color='yellow', style='italic')#,bbox={'facecolor':'red', 'alpha':0.3, 'pad':8})
                    
                    
                    #ax.plot(contours[:, 1], contours[:, 0], linewidth=2)
                loopmun1 = loopmun1+1
        print(loopmun1)       
        ax.set_axis_off()
        #plt.tight_layout()
        plt.show()
        
    def showlabel_with_rank_givenAx(self, smallest_size, theMask, original_intensity, cpstart, cpend, cell_properties, thekey_attri, num_hits, ax):
        self.Labelmask = theMask
        self.OriginImag = original_intensity
        self.cp_start = cpstart
        self.cp_end = cpend
        #self.threshold = threshold
        self.thekey_attri= thekey_attri
        
        #cell_properties = cell_properties[:num_hits]
        cell_properties = cell_properties[self.cp_start:self.cp_end+1] # trace back to i,j corresponding locations in cell properties list.
        cleared = self.Labelmask.copy()
        clear_border(cleared)
                # label image regions
        label_image = label(cleared)
        #image_label_overlay = label2rgb(label_image, image=image)
        
        
#        fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
        ax.imshow(label_image)
        
        loopmun1 = 0
        for region in regionprops(label_image,intensity_image=self.OriginImag):
            # skip small images
            if region.area > smallest_size:         
                # draw rectangle around segmented coins

                #filledimg = region.filled_image
                x2 = cell_properties['Mean intensity in contour'][loopmun1]
                x3 = cell_properties['Ranking'][loopmun1]
                if x3 < num_hits:
                    minr, minc, maxr, maxc = region.bbox
                    rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr, fill=False, edgecolor='red', linewidth=2)
                    ax.add_patch(rect)                    
                    #circularity = (4 * math.pi * region.filled_area) / (filledperimeter * filledperimeter) # region.perimeter will count in perimeters from the holes inside
                    ax.text((maxc + minc)/2, (maxr + minr)/2, str(round(x2, 3))+ ',  '+str(x3), fontsize=8, color='yellow', style='italic')#,bbox={'facecolor':'red', 'alpha':0.3, 'pad':8})
                    
                    
                    #ax.plot(contours[:, 1], contours[:, 0], linewidth=2)
                loopmun1 = loopmun1+1
        print(loopmun1)       
        ax.set_axis_off()
        #plt.tight_layout()
#        plt.show()
        
    def sort_using_weight(self, cell_properties, property_1, property_2, property_3, weight_1, weight_2, weight_3):
        
        max_p1 = np.amax(cell_properties[property_1])
        max_p2 = np.amax(cell_properties[property_2])
        max_p3 = np.amax(cell_properties[property_3])
        
        #cell_properties = np.flip(np.sort(cell_properties, order=property_1), 0)
        cell_properties = rfn.append_fields(cell_properties, 'Nomalization according to '+property_1, cell_properties[property_1]/max_p1, usemask=False)

        #cell_properties = np.flip(np.sort(cell_properties, order=property_2), 0)
        cell_properties = rfn.append_fields(cell_properties, 'Nomalization according to '+property_2, cell_properties[property_2]/max_p2, usemask=False)
        
        cell_properties = rfn.append_fields(cell_properties, 'Nomalization according to '+property_3, cell_properties[property_3]/max_p3, usemask=False)
        
        weights = cell_properties['Nomalization according to '+property_1]*weight_1 + cell_properties['Nomalization according to '+property_2]*weight_2 + cell_properties['Nomalization according to '+property_3]*weight_3
        
        cell_properties = rfn.append_fields(cell_properties, 'evalution', weights, usemask=False)
        
        cell_properties = np.flip(np.sort(cell_properties, order='evalution'), 0)

        return cell_properties