# -*- coding: utf-8 -*-
"""
Created on Sat Mar  7 16:46:47 2020

@author: xinmeng
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math
try:
    from findcontour import imageanalysistoolbox
except:
    from ImageAnalysis.findcontour import imageanalysistoolbox
from skimage import data
from skimage.filters import threshold_otsu, threshold_local
from skimage.filters.rank import entropy
from skimage.segmentation import clear_border
from skimage.measure import label, perimeter, find_contours
from skimage.morphology import closing, square, opening, reconstruction, skeletonize, convex_hull_image, dilation, thin, binary_erosion, disk
from skimage.measure import regionprops, moments, moments_central, moments_hu
from skimage.color import label2rgb
from skimage.restoration import denoise_tv_chambolle
from skimage.io import imread
from scipy.signal import convolve2d, medfilt
import scipy.interpolate as interpolate
from scipy.ndimage.filters import gaussian_filter1d
import numpy.lib.recfunctions as rfn
import copy
import os
import plotly.express as px

#================================================================ProcessImage============================================================
class ProcessImage():

    """
    # ==========================================================================================================================================================
    # ************************************  Retrive scanning scheme and read in images. ************************************ 
    # ==========================================================================================================================================================
    """

    def ReadinImgs_Roundstack(Nest_data_directory, rowIndex, colIndex):
        """
        # =============================================================================
        #         Read in images from nest directory.
        # =============================================================================
        """
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
    
    def retrive_scanning_scheme(Nest_data_directory):
        """
        # =============================================================================
        # Return lists that contain round sequence and coordinates strings, like ['Coords1_R0C0', 'Coords2_R0C1500']
        # =============================================================================
        """
        fileNameList = []
#        ImgSequenceNum = 0
        for file in os.listdir(Nest_data_directory):
            if 'PMT_0Zmax' in file:
                fileNameList.append(file)
        
        RoundNumberList = []
        CoordinatesList = []
        for eachfilename in fileNameList:
            # Get how many rounds are there
            RoundNumberList.append(eachfilename[eachfilename.index('Round'):eachfilename.index('_Coord')])
            RoundNumberList = list(dict.fromkeys(RoundNumberList)) # Remove Duplicates
            
            CoordinatesList.append(eachfilename[eachfilename.index('Coord'):eachfilename.index('_PMT')])
            CoordinatesList = list(dict.fromkeys(CoordinatesList))
            
#        print(CoordinatesList)
        return RoundNumberList, CoordinatesList, fileNameList


    """           
    # ==========================================================================================================================================================
    # ************************************    Individual image processing    ************************************    
    # ==========================================================================================================================================================
    """
    
    def generate_mask(imagestack, openingfactor, closingfactor, binary_adaptive_block_size):
        """
        Return a rough binary mask generated from single image or first image of the stack using adaptive thresholding.
        """
        if imagestack.ndim == 3:
            template_image = imagestack[0,:,:] # Get the first image of the stack to generate the mask for Region Proposal
        elif imagestack.ndim == 2:
            template_image = imagestack
        
        template_image = denoise_tv_chambolle(template_image, weight=0.01) # Denoise the image.
        # -----------------------------------------------Adaptive thresholding-----------------------------------------------
#        block_size = binary_adaptive_block_size#335
        AdaptiveThresholding = threshold_local(template_image, binary_adaptive_block_size, offset=0)
        BinaryMask = template_image >= AdaptiveThresholding
        OpeningBinaryMask = opening(BinaryMask, square(int(openingfactor)))
        RegionProposal_Mask = closing(OpeningBinaryMask, square(int(closingfactor)))
        
        RegionProposal_ImgInMask = RegionProposal_Mask*template_image
        
        return RegionProposal_Mask, RegionProposal_ImgInMask
    
    
    def Region_Proposal(image, RegionProposalMask, smallest_size, biggest_size, lowest_region_intensity, Roundness_thres, DeadPixelPercentageThreshold,
                        contour_thres, contour_dilationparameter, cell_region_opening_factor, cell_region_closing_factor):
        """
        # =============================================================================
        # Based on tag fluorescence image, generate region proposal bounding box.
        # ** RegionProposalMask: the binary mask for region iterative analysis.
        # ** smallest_size/biggest_size: cells size out of this range are ignored.
        # ** lowest_region_intensity: cells with mean region intensity below this are ignored.
        # ** contour_thres: threshold for contour recognizition.
        # ** Roundness_thres: Roundness above this are ignored.
        # ** DeadPixelPercentageThreshold: Percentage of saturated pixels.
        # ** contour_dilationparameter: the dilation degree applied when doing inward contour dilation for thicker menbrane area.
        # ** cell_region_opening_factor: degree of opening operation on individual cell mask.
        # ** cell_region_closing_factor: degree of closing operation on individual cell mask.
        # =============================================================================
        """
        cleared = RegionProposalMask.copy()
        clear_border(cleared)
        # label image regions, prepare for regionprops
        label_image = label(cleared)       
        dtype = [('BoundingBox', 'U32'), ('Mean intensity', float), ('Mean intensity in contour', float), ('Contour soma ratio', float), ('Roundness', float)]
        CellSequenceInRegion = 0
        dirforcellprp = {}
        show_img = False
        if show_img == True:
            plt.figure()
            fig_showlabel, ax_showlabel = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
            ax_showlabel.imshow(image)#Show the first image
        for region in regionprops(label_image,intensity_image = image): 
            
            # skip small images
            if region.area > smallest_size and region.mean_intensity > lowest_region_intensity and region.area < biggest_size:

                # draw rectangle around segmented coins
                minr, minc, maxr, maxc = region.bbox
                boundingbox_info = 'minr{}_minc{}_maxr{}_maxc{}'.format(minr, minc, maxr, maxc)
                bbox_area = (maxr-minr)*(maxc-minc)
                # Based on the boundingbox for each cell from first image in the stack, raw image of slightly larger region is extracted from each round.
                RawRegionImg = image[max(minr-4,0):min(maxr+4, image[0].shape[0]), max(minc-4,0):min(maxc+4, image[0].shape[0])] # Raw region image 
        
                RawRegionImg_for_contour = RawRegionImg.copy()
                
                #---------Get the cell filled mask-------------
                filled_mask_bef, MeanIntensity_Background = imageanalysistoolbox.get_cell_filled_mask(RawRegionImg = RawRegionImg, region_area = bbox_area*0.2, 
                                                                                                      cell_region_opening_factor = cell_region_opening_factor, 
                                                                                                      cell_region_closing_factor = cell_region_closing_factor)

                filled_mask_convolve2d = imageanalysistoolbox.smoothing_filled_mask(RawRegionImg, filled_mask_bef = filled_mask_bef, region_area = bbox_area*0.2, threshold_factor = 1.1)

                # Find contour along filled image
                contour_mask_thin_line = imageanalysistoolbox.contour(filled_mask_convolve2d, RawRegionImg_for_contour.copy(), contour_thres) 

                # after here intensityimage_intensity is changed from contour labeled with number 5 to binary image
                contour_mask_of_cell = imageanalysistoolbox.inwarddilationmask(contour_mask_thin_line.copy() ,filled_mask_convolve2d, contour_dilationparameter)
                
                #                    Calculate Roundness
                #--------------------------------------------------------------
                filled_mask_area = len(np.where(filled_mask_convolve2d == 1)[0])
                contour_mask_perimeter = len(np.where(contour_mask_thin_line == 1)[0])
                Roundness = 4*3.1415*filled_mask_area/contour_mask_perimeter**2
#                print('Roundness: {}'.format(4*3.1415*filled_mask_area/contour_mask_perimeter**2))
                
                #                    Calculate central moments
                #--------------------------------------------------------------
#                M = moments(filled_mask_convolve2d)
#                centroid = (M[1, 0] / M[0, 0], M[0, 1] / M[0, 0])
#                Img_moments_central = moments_central(filled_mask_convolve2d, centroid, order=4)
##                print(Img_moments_central)
#                Img_moments_hu = moments_hu(Img_moments_central/np.amax(Img_moments_central))
#                
#                # Log scale hu moments
#                for EachMoment in range(len(Img_moments_hu)):
#                    Img_moments_hu[EachMoment] = -1* np.copysign(1.0, Img_moments_hu[EachMoment]) * np.log10(abs(Img_moments_hu[EachMoment]))
                
#                print(sum(Img_moments_hu[0:4]))
#                print('Img_moments_hu is {}'.format(Img_moments_hu))
                
                #--------------------------------------------------------------
                # Roundness Threshold
                if Roundness < Roundness_thres:
                    MeanIntensity_FilledArea = np.mean(RawRegionImg[np.where(filled_mask_bef == 1)]) - MeanIntensity_Background # Mean pixel value of filled raw cell area
                                    
                    MeanIntensity_Contour = np.mean(RawRegionImg[np.where(contour_mask_of_cell == 1)]) - MeanIntensity_Background
                    
                    soma_mask_of_cell = filled_mask_convolve2d - contour_mask_of_cell
                    MeanIntensity_Soma = np.mean(RawRegionImg[np.where(soma_mask_of_cell == 1)]) - MeanIntensity_Background#Mean pixel value of soma area                
                    contour_soma_ratio = MeanIntensity_Contour/MeanIntensity_Soma
                    
                    Cell_Area_Img = filled_mask_convolve2d * RawRegionImg
                    # Calculate the entrophy of the image.
    #                entr_img = entropy(Cell_Area_Img/np.amax(Cell_Area_Img), disk(5))
    #                print(np.mean(entr_img))
    
                    #---------------------Calculate dead pixels----------------
                    DeadPixelNum = len(np.where(Cell_Area_Img >= 3.86)[0])
                    filled_mask_convolve2d_area = len(np.where(filled_mask_convolve2d >= 0)[0])
                    DeadPixelPercentage = round(DeadPixelNum / filled_mask_convolve2d_area, 3)
#                    print('Dead Pixel percentage: {}'.format(DeadPixelPercentage)) # b[np.where(aa==16)]=2
                    
                    if str(MeanIntensity_FilledArea) == 'nan':
                        MeanIntensity_FilledArea = 0
                    if str(MeanIntensity_Contour) == 'nan':
                        MeanIntensity_Contour = 0
                    if str(contour_soma_ratio) == 'nan':
                        contour_soma_ratio = 0
                        
                    if DeadPixelPercentage <= DeadPixelPercentageThreshold:
                    
                        dirforcellprp[CellSequenceInRegion] = (boundingbox_info, MeanIntensity_FilledArea, MeanIntensity_Contour, contour_soma_ratio, Roundness)    
                    
    #                    plt.figure()
    #                    plt.imshow(RawRegionImg)
    #                    plt.show()
    #    # #    
    #                    plt.figure()
    #                    plt.imshow(filled_mask_convolve2d)
    #                    plt.show()
                    
                        #--------------------------------------------------Add red boundingbox to axis----------------------------------------------
                        rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr, fill=False, edgecolor='red', linewidth=2)
                        contour_mean_bef_rounded = str(round(MeanIntensity_Contour, 3))[0:5]
                        
                        if show_img == True:
                            ax_showlabel.add_patch(rect)
                            ax_showlabel.text((maxc + minc)/2, (maxr + minr)/2, 'Cell-{}, {}: {}'.format(CellSequenceInRegion, 'c_m', contour_mean_bef_rounded),
                                              fontsize=8, color='yellow', style='italic')#,bbox={'facecolor':'red', 'alpha':0.3, 'pad':8})
        
                        CellSequenceInRegion += 1
        if show_img == True:
            ax_showlabel.set_axis_off()
            plt.show()
            
        TagFluorescenceLookupBook = np.zeros(CellSequenceInRegion, dtype = dtype)
        for p in range(CellSequenceInRegion):
            TagFluorescenceLookupBook[p] = dirforcellprp[p]
            
        return TagFluorescenceLookupBook
    
    def extract_information_from_bbox(image, bbox_list, DeadPixelPercentageThreshold, contour_thres, contour_dilationparameter, cell_region_opening_factor, cell_region_closing_factor):
        """
        # =============================================================================
        # Based on tag fluorescence image
        # =============================================================================
        """
        
        dtype = [('BoundingBox', 'U32'), ('Mean intensity', float), ('Mean intensity in contour', float), ('Contour soma ratio', float)]
        CellSequenceInRegion = 0
        dirforcellprp = {}
        
        show_img = False
        if show_img == True:
            plt.figure()
            fig_showlabel, ax_showlabel = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
            ax_showlabel.imshow(image)#Show the first image
            
        for Each_bounding_box in bbox_list:

            # Retrieve boundingbox information
            minr = int(Each_bounding_box[Each_bounding_box.index('minr')+4:Each_bounding_box.index('_minc')])
            maxr = int(Each_bounding_box[Each_bounding_box.index('maxr')+4:Each_bounding_box.index('_maxc')])        
            minc = int(Each_bounding_box[Each_bounding_box.index('minc')+4:Each_bounding_box.index('_maxr')])
            maxc = int(Each_bounding_box[Each_bounding_box.index('maxc')+4:len(Each_bounding_box)])
                
            # Based on the boundingbox for each cell from first image in the stack, raw image of slightly larger region is extracted from each round.
            RawRegionImg = image[max(minr-4,0):min(maxr+4, image[0].shape[0]), max(minc-4,0):min(maxc+4, image[0].shape[0])] # Raw region image 
            
            RawRegionImg_for_contour = RawRegionImg.copy()
            
            #---------Get the cell filled mask-------------
            bbox_area = (maxr-minr)*(maxc-minc)

            filled_mask_bef, MeanIntensity_Background = imageanalysistoolbox.get_cell_filled_mask(RawRegionImg = RawRegionImg, region_area = bbox_area*0.2, 
                                                                                                  cell_region_opening_factor = cell_region_opening_factor, 
                                                                                                  cell_region_closing_factor = cell_region_closing_factor)

            filled_mask_convolve2d = imageanalysistoolbox.smoothing_filled_mask(RawRegionImg, filled_mask_bef = filled_mask_bef, region_area = bbox_area*0.2, threshold_factor = 1.1)

            # Find contour along filled image
            contour_mask_thin_line = imageanalysistoolbox.contour(filled_mask_convolve2d, RawRegionImg_for_contour.copy(), contour_thres) 

            # after here intensityimage_intensity is changed from contour labeled with number 5 to binary image
            contour_mask_of_cell = imageanalysistoolbox.inwarddilationmask(contour_mask_thin_line.copy() ,filled_mask_convolve2d, contour_dilationparameter)
            
            # Calculate mean values.
            #--------------------------------------------------------------
            MeanIntensity_FilledArea = np.mean(RawRegionImg[np.where(filled_mask_bef == 1)]) - MeanIntensity_Background # Mean pixel value of filled raw cell area
                            
            MeanIntensity_Contour = np.mean(RawRegionImg[np.where(contour_mask_of_cell == 1)]) - MeanIntensity_Background
            
            soma_mask_of_cell = filled_mask_convolve2d - contour_mask_of_cell
            MeanIntensity_Soma = np.mean(RawRegionImg[np.where(soma_mask_of_cell == 1)]) - MeanIntensity_Background#Mean pixel value of soma area                
            contour_soma_ratio = MeanIntensity_Contour/MeanIntensity_Soma

            Cell_Area_Img = filled_mask_convolve2d * RawRegionImg
            
            #---------------------Calculate dead pixels----------------
            DeadPixelNum = len(np.where(Cell_Area_Img >= 3.86)[0])
            filled_mask_convolve2d_area = len(np.where(filled_mask_convolve2d >= 0)[0])
            DeadPixelPercentage = round(DeadPixelNum / filled_mask_convolve2d_area, 3)
            
            if str(MeanIntensity_FilledArea) == 'nan':
                MeanIntensity_FilledArea = 0
            if str(MeanIntensity_Contour) == 'nan':
                MeanIntensity_Contour = 0
            if str(contour_soma_ratio) == 'nan':
                contour_soma_ratio = 0
            
            if DeadPixelPercentage <= DeadPixelPercentageThreshold:
                dirforcellprp[CellSequenceInRegion] = (Each_bounding_box, MeanIntensity_FilledArea, MeanIntensity_Contour, contour_soma_ratio, )
                
                # plt.figure()
                # plt.imshow(RawRegionImg)
                # plt.show()
    
                # plt.figure()
                # plt.imshow(contour_mask_of_cell)
                # plt.show()
            
                #--------------------------------------------------Add red boundingbox to axis----------------------------------------------
                rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr, fill=False, edgecolor='red', linewidth=2)
                contour_mean_bef_rounded = str(round(MeanIntensity_Contour, 3))[0:5]
                
                if show_img == True:
                    ax_showlabel.add_patch(rect)
                    ax_showlabel.text((maxc + minc)/2, (maxr + minr)/2, 'Cell-{}, {}: {}'.format(CellSequenceInRegion, 'c_m', contour_mean_bef_rounded),fontsize=8, color='yellow', style='italic')
    
                CellSequenceInRegion += 1
                
        if show_img == True:
            ax_showlabel.set_axis_off()
            plt.show()
            
        LibFluorescenceLookupBook = np.zeros(CellSequenceInRegion, dtype = dtype)
        for p in range(CellSequenceInRegion):
            LibFluorescenceLookupBook[p] = dirforcellprp[p]
            
        return LibFluorescenceLookupBook        
        
    
    def get_Skeletonized_contour(image, RegionProposalMask, smallest_size, contour_thres, contour_dilationparameter, cell_region_opening_factor, 
                                 cell_region_closing_factor, scanning_voltage, points_per_contour, sampling_rate):
        """
        # =============================================================================
        #         Get the skeletonized contour of the cell for automated contour scanning.
        # ** RegionProposalMask: the binary mask for region iterative analysis.
        # ** smallest_size: cells size below this number are ignored.
        # ** lowest_region_intensity: cells with mean region intensity below this are ignored.
        # ** contour_thres: threshold for contour recognizition.
        # ** contour_dilationparameter: the dilation degree applied when doing inward contour dilation for thicker menbrane area.
        # ** cell_region_opening_factor: degree of opening operation on individual cell mask.
        # ** cell_region_closing_factor: degree of closing operation on individual cell mask.
        # ** scanning_voltage: The scanning voltage of input image.
        # ** points_per_contour: desired number of points in contour routine.
        # ** sampling_rate: sampling rate for contour scanning.
        # =============================================================================
        """
        cleared = RegionProposalMask.copy()
        clear_border(cleared)
        # label image regions, prepare for regionprops
        label_image = label(cleared)
        
        CellSequenceInRegion = 0
        CellSkeletonizedContourDict = {}
#        dtype = [('No.', int), ('Mean intensity', float), ('Mean intensity in contour', float), ('Contour soma ratio', float)]
        
        for region in regionprops(label_image,intensity_image = image): # USE first image in stack before perfusion as template 
            
            # skip small images
            if region.area > smallest_size:
         
                # draw rectangle around segmented coins
                minr, minc, maxr, maxc = region.bbox
                
                #region_mean_intensity = region.mean_intensity #mean intensity of the region, 0 pixels in label are omitted.
                
                # Based on the boundingbox for each cell from first image in the stack, raw image of slightly larger region is extracted from each round.
                RawRegionImg = image[max(minr-4,0):min(maxr+4, image[0].shape[0]), max(minc-4,0):min(maxc+4, image[0].shape[0])] # Raw region image 
                
                RawRegionImg_for_contour = RawRegionImg.copy()
                
                #---------Get the cell filled mask-------------
                filled_mask_bef, MeanIntensity_Background = imageanalysistoolbox.get_cell_filled_mask(RawRegionImg = RawRegionImg, region_area = region.area, 
                                                                            cell_region_opening_factor = cell_region_opening_factor, 
                                                                            cell_region_closing_factor = cell_region_closing_factor)
                
                filled_mask_convolve2d = imageanalysistoolbox.smoothing_filled_mask(RawRegionImg, filled_mask_bef = filled_mask_bef, region_area = region.area, threshold_factor = 2)
                
                # Set the edge lines to zero so that we don't have the risk of unclosed contour at the edge of image.
                if minr == 0 or minc == 0:
                    filled_mask_convolve2d[0,:] = False
                    filled_mask_convolve2d[:,0] = False
                if maxr == image[0].shape[0] or maxc == image[0].shape[0]:
                    filled_mask_convolve2d[filled_mask_convolve2d.shape[0]-1, :] = False
                    filled_mask_convolve2d[:, filled_mask_convolve2d.shape[1]-1] = False
                    
                # Find contour along filled image
                contour_mask_thin_line = imageanalysistoolbox.contour(filled_mask_convolve2d, RawRegionImg_for_contour.copy(), contour_thres) 
#                plt.figure()
#                plt.imshow(contour_mask_thin_line)
#                plt.show()
                # after here intensityimage_intensity is changed from contour labeled with number 5 to binary image
#                contour_mask_of_cell = imageanalysistoolbox.inwarddilationmask(contour_mask_thin_line.copy() ,filled_mask_convolve2d, contour_dilationparameter)
                #--------------------------------------------------------------
#                print(len(np.where(contour_mask_thin_line == 1)[0]))
                if len(np.where(contour_mask_thin_line == 1)[0]) > 0:
                    #-------------------Sorting and filtering----------------------
                    clockwise_sorted_raw_trace = ProcessImage.sort_index_clockwise(contour_mask_thin_line)
                    [X_routine, Y_routine], filtered_cellmap = ProcessImage.tune_contour_routine(contour_mask_thin_line, clockwise_sorted_raw_trace, filtering_kernel = 1.5)
                    #--------------------------------------------------------------
                    
                    #----------Put contour image back to original image.-----------
                    ContourFullFOV = np.zeros((image.shape[0], image.shape[1]))
                    ContourFullFOV[max(minr-4,0):min(maxr+4, image[0].shape[0]), max(minc-4,0):min(maxc+4, image[0].shape[0])] = filtered_cellmap.copy()
    
                    X_routine = X_routine + max(minr-4,0)
                    Y_routine = Y_routine + max(minc-4,0)
                    #--------------------------------------------------------------
                    
                    figure, (ax1, ax2) = plt.subplots(2, 1, figsize=(10,10))
                    ax1.imshow(ContourFullFOV, cmap = plt.cm.gray)
                    ax2.imshow(filtered_cellmap*2+RawRegionImg, cmap = plt.cm.gray)
    #                ax2.imshow(ContourFullFOV*2+image, cmap = plt.cm.gray)
    #                ax2.imshow(filled_mask_convolve2d, cmap = plt.cm.gray)           
    #                figure.tight_layout()
                    plt.show()
                    
                    #------------Organize for Ni-daq execution---------------------
                    voltage_contour_routine_X = (X_routine/ContourFullFOV.shape[0])*scanning_voltage*2-scanning_voltage
                    voltage_contour_routine_Y = (Y_routine/ContourFullFOV.shape[1])*scanning_voltage*2-scanning_voltage
                    
                    #--------------interpolate to get 500 points-------------------
                    x_axis = np.arange(0,len(voltage_contour_routine_X))
                    f_x = interpolate.interp1d(x_axis, voltage_contour_routine_X, kind='cubic')
                    newx = np.linspace(x_axis.min(), x_axis.max(), num=points_per_contour)
                    X_interpolated = f_x(newx)
                    
                    y_axis = np.arange(0,len(voltage_contour_routine_Y))
                    f_y = interpolate.interp1d(y_axis, voltage_contour_routine_Y, kind='cubic')
                    newy = np.linspace(y_axis.min(), y_axis.max(), num=points_per_contour)
                    Y_interpolated = f_y(newy)
                    
                    #-----------speed and accelation check-------------------------
    #                contour_x_speed = np.diff(X_interpolated)/time_gap
    #                contour_y_speed = np.diff(Y_interpolated)/time_gap
                    time_gap = 1/sampling_rate
                    contour_x_acceleration = np.diff(X_interpolated, n=2)/time_gap**2
                    contour_y_acceleration = np.diff(Y_interpolated, n=2)/time_gap**2
                    
                    if AccelerationGalvo < np.amax(abs(contour_x_acceleration)):
                        print(np.amax(abs(contour_x_acceleration)))
                    if AccelerationGalvo < np.amax(abs(contour_y_acceleration)):
                        print(np.amax(abs(contour_y_acceleration)))
                    
                    X_interpolated = np.around(X_interpolated, decimals=3)
                    Y_interpolated = np.around(Y_interpolated, decimals=3)
                    
                    ContourArray_forDaq = np.vstack((X_interpolated,Y_interpolated))
                    
                    CellSkeletonizedContourDict['DaqArray_cell{}'.format(CellSequenceInRegion)] = ContourArray_forDaq
                    CellSkeletonizedContourDict['ContourMap_cell{}'.format(CellSequenceInRegion)] = ContourFullFOV
                    CellSequenceInRegion += 1
                    #--------------------------------------------------------------
                                    
                
        return CellSkeletonizedContourDict
    
    def sort_index_clockwise(cellmap):
        """
        # =============================================================================
        #  Given the binary contour, sort the index so that they are in clockwise sequence for further contour scanning.
        # =============================================================================
        """

        rawindexlist = list(zip(np.where(cellmap == 1)[0], np.where(cellmap == 1)[1]))
        rawindexlist.sort()
        
        
        cclockwiselist = rawindexlist[0:1] # first point in clockwise direction
        clockwiselist = rawindexlist[1:2] # first point in counter clockwise direction
        # reverse the above assignment depending on how first 2 points relate
        if rawindexlist[1][1] > rawindexlist[0][1]: 
            clockwiselist = rawindexlist[1:2]
            cclockwiselist = rawindexlist[0:1]
        
        coordstorage = rawindexlist[2:]
#        print(len(rawindexlist))
        timeout = time.time()
        while len(clockwiselist+cclockwiselist) != len(rawindexlist):
            for p in coordstorage:#Try one by one from coords dump until find one that is right next to existing clockwise or counter clockwise liste.
                # append to the list to which the next point is closest
                x_last_clockwise = clockwiselist[-1][0]
                y_last_clockwise = clockwiselist[-1][1]
                x_last_cclockwise = cclockwiselist[-1][0]
                y_last_cclockwise = cclockwiselist[-1][1]
#                if (x_last_clockwise-p[0])**2+(y_last_clockwise-p[1])**2 == 1 and \
#                ((x_last_clockwise-p[0])**2+(y_last_clockwise-p[1])**2) < ((x_last_cclockwise-p[0])**2+(y_last_cclockwise-p[1])**2):
#                    clockwiselist.append(p)
#                    coordstorage.remove(p)                    
                if (x_last_clockwise-p[0])**2+(y_last_clockwise-p[1])**2 <= 2 and \
                ((x_last_clockwise-p[0])**2+(y_last_clockwise-p[1])**2) <= ((x_last_cclockwise-p[0])**2+(y_last_cclockwise-p[1])**2):
                    clockwiselist.append(p)
                    coordstorage.remove(p)
                    break
                elif (x_last_cclockwise-p[0])**2+(y_last_cclockwise-p[1])**2 <= 2 and \
                ((x_last_clockwise-p[0])**2+(y_last_clockwise-p[1])**2) > ((x_last_cclockwise-p[0])**2+(y_last_cclockwise-p[1])**2):
#                    print((cclockwiselist[-1][0]-p[0])**2+(cclockwiselist[-1][1]-p[1])**2)
#                    print('cc')
                    cclockwiselist.append(p)
                    coordstorage.remove(p)
                    break
            # If clockwise and counter clockwise meet each other
            if len(clockwiselist+cclockwiselist) > 10 and (x_last_clockwise-x_last_cclockwise)**2+(y_last_clockwise-y_last_cclockwise)**2 <= 2:
                break
            # If we have a situation like this at the end of enclosure:
            #  0  0  1
            #  0  1  1
            #  1  0  0
            if len(clockwiselist+cclockwiselist) > 10 and (x_last_clockwise-x_last_cclockwise)**2+(y_last_clockwise-y_last_cclockwise)**2 == 5:
                if (cclockwiselist[-2][0]-clockwiselist[-1][0])**2 + (cclockwiselist[-2][1]-clockwiselist[-1][1])**2 == 2:
                    cclockwiselist.remove(cclockwiselist[-1])
                    break
                
            if time.time() > timeout+2:
                print('timeout')
                break
#        print(clockwiselist[-1])
#        print(cclockwiselist[-1])
#        print(p)
        print(coordstorage)
        cclockwiselist.reverse()
        result = clockwiselist + cclockwiselist
        
        return result
    
    def tune_contour_routine(cellmap, clockwise_sorted_raw_trace, filtering_kernel):
        """
        # =============================================================================
        #  Given the clockwise sorted binary contour, interploate and filter for further contour scanning.
        # =============================================================================
        """
        Unfiltered_contour_routine_X = np.array([])
        Unfiltered_contour_routine_Y = np.array([])
        for rawcoord in clockwise_sorted_raw_trace:
            Unfiltered_contour_routine_X = np.append(Unfiltered_contour_routine_X, rawcoord[0])
            Unfiltered_contour_routine_Y = np.append(Unfiltered_contour_routine_Y, rawcoord[1])
        
        # filtering and show filtered contour
#        X_routine = medfilt(Unfiltered_contour_routine_X, kernel_size=filtering_kernel)
#        Y_routine = medfilt(Unfiltered_contour_routine_Y, kernel_size=filtering_kernel)
        X_routine = gaussian_filter1d(Unfiltered_contour_routine_X, sigma = filtering_kernel)
        Y_routine = gaussian_filter1d(Unfiltered_contour_routine_Y, sigma = filtering_kernel)
        
        filtered_cellmap = np.zeros((cellmap.shape[0], cellmap.shape[1]))
        for i in range(len(X_routine)):
            filtered_cellmap[int(X_routine[i]), int(Y_routine[i])] = 1

        
        return [X_routine, Y_routine], filtered_cellmap
        
    def get_cell_properties_Roundstack(imagestack, RegionProposalMask, smallest_size, contour_thres, contour_dilationparameter, cell_region_opening_factor, cell_region_closing_factor):
        
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
                fig_showlabel, ax_showlabel = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
                ax_showlabel.imshow(imagestack[0])#Show the first image
            
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
#                    intensityimage_intensity = region.intensity_image # need a copy of this cause region will be altered by s.contour
                    
                    # Based on the boundingbox for each cell from first image in the stack, raw image of slightly larger region is extracted from each round.
                    RawRegionImg = imagestack[EachRound][max(minr-4,0):min(maxr+4, imagestack[0].shape[0]), max(minc-4,0):min(maxc+4, imagestack[0].shape[0])] # Raw region image 
                    
                    RawRegionImg_for_contour = RawRegionImg.copy()

                    #---------Get the cell filled mask-------------
                    filled_mask_bef = imageanalysistoolbox.get_cell_filled_mask(RawRegionImg = RawRegionImg, region_area = region.area, 
                                                                                cell_region_opening_factor = cell_region_opening_factor, 
                                                                                cell_region_closing_factor = cell_region_closing_factor)

                    filled_origin_image_intensity = RawRegionImg*filled_mask_bef # Intensity image of cell with hole filled
                    filled_mean_bef = np.mean(RawRegionImg[np.where(filled_mask_bef == 1)]) # Mean pixel value of filled raw cell area
                    
                    filled_mask_convolve2d = imageanalysistoolbox.smoothing_filled_mask(RawRegionImg, filled_mask_bef = filled_mask_bef, region_area = region.area, threshold_factor = 1.1)
                    
                    # Find contour along filled image
#                    imageanalysistoolbox_instacne=imageanalysistoolbox()
                    contour_mask_bef = imageanalysistoolbox.contour(filled_mask_convolve2d, RawRegionImg_for_contour.copy(), contour_thres)
                    # after here intensityimage_intensity is changed from contour labeled with number 5 to binary image
                    contour_mask_of_cell = imageanalysistoolbox.inwarddilationmask(contour_mask_bef ,filled_mask_bef, contour_dilationparameter)   
                
#                    contourimage_intensity_aft = s.contour(filled_mask_aft, regionimage_after_for_contour.copy(), contour_thres) 
#                    after here intensityimage_intensity is changed with contour labeled with number 5
#                    contour_mask_of_intensity_aft = s.inwarddilationmask(contourimage_intensity_aft ,filled_mask_aft, contour_dilationparameter)
    
                    contour_mean_bef = np.mean(RawRegionImg[np.where(contour_mask_of_cell == 1)])
#                    contour_mean_aft = np.mean(regionimage_after[np.where(contour_mask_of_intensity_aft == 1)])  
                    
                    cell_soma_mask_bef = filled_mask_bef - contour_mask_of_cell
                    
                    contour_origin_image_intensity = RawRegionImg*contour_mask_of_cell # Intensity image of cell contour
                    soma_origin_image_intensity = RawRegionImg*cell_soma_mask_bef # Intensity image of cell soma part
    
                    soma_mean_bef = np.mean(RawRegionImg[np.where(cell_soma_mask_bef == 1)])#Mean pixel value of soma area
                    
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
                        ax_showlabel.add_patch(rect)
                        ax_showlabel.text((maxc + minc)/2, (maxr + minr)/2, 'Cell-{}, {}: {}'.format \
                                          (RegionLoopNumber, 'c_m', contour_mean_bef_rounded),fontsize=8, color='yellow', style='italic')
                                       
#            print('Total region number: {}'.format(RegionLoopNumber))
            cell_properties = np.zeros(len(region_mean_intensity_list), dtype = dtype)
            for p in range(RegionLoopNumber):
                cell_properties[p] = dirforcellprp[p]
            
            CellPropDictEachRound['RoundSequence{}'.format(EachRound+1)] = cell_properties
            
            if EachRound == 0:
                ax_showlabel.set_axis_off()
    #            if EachRound == 0:
                plt.show()
            
        return CellPropDictEachRound
    
    """
    # ==========================================================================================================================================================
    # ************************************   Organize cell properties dictionary  ************************************ 
    # ==========================================================================================================================================================
    """

    def TagFluorescenceAnalysis(tag_folder, tag_round, Roundness_threshold):
        """
        # =============================================================================
        # Given the folder and round number of tag fluorescence, return a dictionary 
        # that contains each scanning position as key and structured array of detailed 
        # information about each identified cell as content.
        # =============================================================================
        """
        tagprotein_cell_properties_dict = {}
        RoundNumberList, CoordinatesList, fileNameList = ProcessImage.retrive_scanning_scheme(tag_folder)

        for EachRound in RoundNumberList:
            
            if EachRound == tag_round:
                
                for EachCoord in CoordinatesList:
                    
                # =============================================================================
                #             For tag fluorescence:
                # =============================================================================    
                    print(EachCoord)
                    #-------------- readin image---------------
                    for Eachfilename in enumerate(fileNameList):
                        if EachCoord in Eachfilename[1] and EachRound in Eachfilename[1]:                        
                            tag_imagefilename = os.path.join(tag_folder, Eachfilename[1])
#                    print(tag_imagefilename)
                    loaded_tag_image = imread(tag_imagefilename, as_gray=True)
                    #------------------------------------------
    
                    RegionProposalMask, RegionProposalOriginalImage = ProcessImage.generate_mask(loaded_tag_image, openingfactor=2, 
                                                                                                                closingfactor=3, binary_adaptive_block_size=335)#256(151) 500(335)
                    
                    TagFluorescenceLookupBook = ProcessImage.Region_Proposal(loaded_tag_image, RegionProposalMask, smallest_size=800, biggest_size=3500, Roundness_thres = Roundness_threshold,
                                                                             DeadPixelPercentageThreshold = 0.14, lowest_region_intensity=0.16, contour_thres=0.001, contour_dilationparameter=11,
                                                                             cell_region_opening_factor=1, cell_region_closing_factor=2)
                    
                    tagprotein_cell_properties_dict['{}_{}'.format(EachRound, EachCoord)] = TagFluorescenceLookupBook
                    
    #            for Eachpos in tagprotein_cell_properties_dict:
    #                cellnum = len(tagprotein_cell_properties_dict[Eachpos])
    #                for eachcell in range(cellnum):
    #                    if str(tagprotein_cell_properties_dict[Eachpos][eachcell]['Mean intensity']) != 'nan':
    #                        tag_cell_mean_intensity.append(tagprotein_cell_properties_dict[Eachpos][eachcell]['Mean intensity'])
    #                        trace_back.append('{}_{}'.format(Eachpos, eachcell))
    
        return tagprotein_cell_properties_dict
    
    def LibFluorescenceAnalysis(lib_folder, tag_round, lib_round, tagprotein_cell_properties_dict):
        """
        # =============================================================================
        # Delivering cell properties from tag screening round, return a dictionary 
        # that contains each scanning position as key and structured array of detailed 
        # information about each identified cell as content.
        # =============================================================================
        """
        lib_cell_properties_dict = {}
        RoundNumberList, CoordinatesList, fileNameList = ProcessImage.retrive_scanning_scheme(lib_folder)

        for EachRound in RoundNumberList:
            
            if EachRound == lib_round:
                
                for EachCoord in CoordinatesList:
                # =============================================================================
                #             For library fluorescence:
                # =============================================================================
                    print(EachCoord)
                    bbox_list = []
                    #-------------- readin image---------------
                    for Eachfilename in enumerate(fileNameList):
                        if EachCoord in Eachfilename[1] and EachRound in Eachfilename[1]:            
                            lib_imagefilename = os.path.join(lib_folder, Eachfilename[1])
#                    print(lib_imagefilename)
                    loaded_lib_image = imread(lib_imagefilename, as_gray=True)
                    #------------------------------------------                    
                    
                    #------------unpack bbox infor----------------------
                    for eachcellregion in range(len(tagprotein_cell_properties_dict['{}_{}'.format(tag_round, EachCoord)])):
                        bbox_list.append(tagprotein_cell_properties_dict['{}_{}'.format(tag_round, EachCoord)][eachcellregion]['BoundingBox'])                    

                    LibFluorescenceLookupBook = ProcessImage.extract_information_from_bbox(image = loaded_lib_image, bbox_list = bbox_list, DeadPixelPercentageThreshold = 0.54, 
                                                                                           contour_thres=0.001, contour_dilationparameter=11, cell_region_opening_factor=1, cell_region_closing_factor=2)
                    
                    lib_cell_properties_dict['{}_{}'.format(EachRound, EachCoord)] = LibFluorescenceLookupBook
                    
        
        return lib_cell_properties_dict
    
    def CorrectForFusionProtein(tagprotein_cell_properties_dict, lib_cell_properties_dict, tagprotein_laserpower, lib_laserpower):
        """
        # =============================================================================
        # Assume that there's one tag protein scanning round, add 'Mean intensity devided by tag' field to the structured array in the dictionary.
        # =============================================================================
        """
        for coordinate_tag in tagprotein_cell_properties_dict:
            
            current_coord_string = coordinate_tag[coordinate_tag.index('Coord'):len(coordinate_tag)]
            cell_number = len(tagprotein_cell_properties_dict[coordinate_tag])
            
            for coordinate_lib in lib_cell_properties_dict:
                
                if current_coord_string in coordinate_lib: # No matter what the round number is, look for the same coorinate.
                    
                    divisionlist = []
                    for eachcell in range(cell_number):
                        tag_fluo = tagprotein_cell_properties_dict[coordinate_tag][eachcell]['Mean intensity']
                        lib_fluo = lib_cell_properties_dict[coordinate_lib][eachcell]['Mean intensity']
                        if tag_fluo == 0:
                            division =0
                        else:
                            division = (lib_fluo/lib_laserpower)/(tag_fluo/tagprotein_laserpower)

#                        print(coordinate_lib+', cell'+str(eachcell)+','+str(lib_fluo))
#                        print(division)
                        divisionlist.append(division)
                    
                    lib_cell_properties_dict[coordinate_lib] = rfn.append_fields(lib_cell_properties_dict[coordinate_lib], 'Mean intensity divided by tag', divisionlist, usemask=False)
                        
        return lib_cell_properties_dict
    
    def OrganizeOverview(lib_cell_properties_dict, CutOffThresList, EvaluatingPara_1, WeightPara_1, EvaluatingPara_2, WeightPara_2):
        """
        # =============================================================================
        # Add 'ID' field which indicates position, round information to the structured array in the dictionary.
        # Delete cells that are dimmer than threshold.
        # Add 'Normalized distance' field which indicates the distance to the scatter plots origin in EvaluatingPara_1 and EvaluatingPara_2 dimensions.
        # ** EvaluatingPara: Indicates the field along which calculation of distance takes place.
        # =============================================================================
        """        
        Overview_dtype = [('BoundingBox', 'U32'), ('Mean intensity', float), ('Mean intensity in contour', float), 
                          ('Contour soma ratio', float), ('Mean intensity divided by tag', float)]
        counting = 0
        
        totalcellnum = 0
        for EachCoord in lib_cell_properties_dict:
            totalcellnum += len(lib_cell_properties_dict[EachCoord])
            
        Overview_LookupBook = np.zeros(totalcellnum, dtype = Overview_dtype)
        IDlist = []
        for EachCoord in lib_cell_properties_dict:
            for EachCellArray in lib_cell_properties_dict[EachCoord]:
                Overview_LookupBook[counting] = EachCellArray
#                ID_infor = EachCoord + "_No" + str(counting)
                IDlist.append(EachCoord)
                counting += 1
        # Append the id field
        Overview_LookupBook = rfn.append_fields(Overview_LookupBook, 'ID', IDlist, usemask=False)  
        
        # Trimming according to thresholds
        DeleteIndexList = []
        # Delete cells that are dimmer than threshold.
        for EachCell in range(len(Overview_LookupBook)):
            if 'Mean intensity in contour' in CutOffThresList and 'Contour soma ratio' in CutOffThresList:
                if Overview_LookupBook[EachCell]['Mean intensity in contour'] < CutOffThresList[CutOffThresList.index('Mean intensity in contour') + 1]:
                    DeleteIndexList.append(EachCell)

                elif Overview_LookupBook[EachCell]['Contour soma ratio'] < CutOffThresList[CutOffThresList.index('Contour soma ratio') + 1]:
                    DeleteIndexList.append(EachCell)
        
        Overview_LookupBook = np.delete(Overview_LookupBook, DeleteIndexList, 0)
        
        # Append the number field.
        NoList = []
        for EachCell in range(len(Overview_LookupBook)):
            NoList.append(EachCell)
        Overview_LookupBook = rfn.append_fields(Overview_LookupBook, 'IDNumber', NoList, usemask=False)
            
        # Add 'Normalized distance' field
        NormalizedDistanceArray = np.array([])
        for EachCellIndex in range(len(Overview_LookupBook)):
            # Get the original values of two axes.
            value_Para_1 = Overview_LookupBook[EachCellIndex][EvaluatingPara_1]/np.amax(Overview_LookupBook[EvaluatingPara_1])
            value_Para_2 = Overview_LookupBook[EachCellIndex][EvaluatingPara_2]/np.amax(Overview_LookupBook[EvaluatingPara_2])
            
            Distance = ((value_Para_1 * WeightPara_1)**2 \
                        + (value_Para_2 * WeightPara_2)**2)**0.5

            NormalizedDistanceArray = np.append(NormalizedDistanceArray, Distance)
                
        Overview_LookupBook = rfn.append_fields(Overview_LookupBook, 'Normalized distance', NormalizedDistanceArray, usemask=False)
        
        return Overview_LookupBook
    
    def WeightedSorting(cell_properties, property_1, property_2, property_3, weight_1, weight_2, weight_3):
        """
        # Sorting using linear combination of weights.
        """
        max_p1 = np.amax(cell_properties[property_1])
        max_p2 = np.amax(cell_properties[property_2])
        max_p3 = np.amax(cell_properties[property_3])
        
        weights = cell_properties[property_1]/max_p1*weight_1 + \
                  cell_properties[property_2]/max_p2*weight_2 + \
                  cell_properties[property_3]/max_p3*weight_3
        
        if str(weights) == 'nan':
            weights = 0
            
        cell_properties = rfn.append_fields(cell_properties, 'Weighted ranking', weights, usemask=False)
        
        cell_properties = np.flip(np.sort(cell_properties, order='Weighted ranking'), 0)

        return cell_properties
    
    
    def DistanceSelecting(cell_properties, selectionRadiusPercent):
        """
        # Sorting using field 'Normalized distance'.
        # ** selectionRadiusPercent: Threshold for distance to be selected.
        """
        max_Normalized_distance = np.amax(cell_properties['Normalized distance'])
        min_Normalized_distance = np.amin(cell_properties['Normalized distance'])
        selectionRadiusThres = ((max_Normalized_distance - min_Normalized_distance) * selectionRadiusPercent/100) + min_Normalized_distance
        
        Selected_cell_number = 0
        
        if selectionRadiusPercent == 100:
            Selected_LookupBook = cell_properties
            Selected_cell_number = len(Selected_LookupBook)
        else:
            Selected_LookupBook = np.array([])
            for EachCellIndex in range(len(cell_properties)):
                if cell_properties[EachCellIndex]['Normalized distance'] > selectionRadiusThres:
                    if Selected_cell_number == 0:
                        Selected_LookupBook = np.array([cell_properties[EachCellIndex]])
                    else:
                        Selected_LookupBook = np.append(Selected_LookupBook, cell_properties[EachCellIndex])
                    Selected_cell_number += 1
        
        if Selected_cell_number == 1:
            Selected_LookupBook = Selected_LookupBook
        else:
            Selected_LookupBook = np.flip(np.sort(Selected_LookupBook, order='Normalized distance'), 0)

        return Selected_LookupBook        
        
if __name__ == "__main__":
    
    from skimage.io import imread
    import time
    from IPython import get_ipython

#    speedGalvo = 20000.0 #Volt/s
#    AccelerationGalvo = 1.54*10**8 #Acceleration galvo in volt/s^2
#    #--------------------------------------------------------------------------
#    PMT_image = imread(r'D:\XinMeng\imageCollection\Round2_Coord3_R1500C1500_PMT_2.tif', as_gray=True)
##    time_gap = 1/50000
#     
#    RegionProposalMask, RegionProposalOriginalImage = ProcessImage.generate_mask(PMT_image, openingfactor=2, 
#                                                                                                closingfactor=4, binary_adaptive_block_size=335)#256(151) 500(335)
#
#    CellSkeletonizedContourDict= ProcessImage.get_Skeletonized_contour(PMT_image, RegionProposalMask, smallest_size=400, contour_thres=0.001, 
#                                                                                       contour_dilationparameter=11, cell_region_opening_factor=1, cell_region_closing_factor=2,
#                                                                                       scanning_voltage=5, points_per_contour=500, sampling_rate = 50000)
            
        
# =============================================================================
    tag_folder = r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-05-12 Archon lib 400FOVs 4 grid\trial_1'
    lib_folder = r'D:\XinMeng\imageCollection\Fov3\New folder (3)'
  #   tag_folder = r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-3-6 Archon brightness screening\NovArch library'

    tag_round = 'Round1'
    lib_round = 'Round4'
    
    EvaluatingPara_1 = 'Mean intensity divided by tag'
    EvaluatingPara_2 = 'Contour soma ratio'
    
    MeanIntensityThreshold = 0.16
    
    starttime = time.time()
    
    tagprotein_cell_properties_dict = ProcessImage.TagFluorescenceAnalysis(tag_folder, tag_round, Roundness_threshold = 2.1)
    print('tag done.')
    
    tagprotein_cell_properties_dict_meanIntensity_list = []
    for eachpos in tagprotein_cell_properties_dict:
        for i in range(len(tagprotein_cell_properties_dict[eachpos])):
            tagprotein_cell_properties_dict_meanIntensity_list.append(tagprotein_cell_properties_dict[eachpos]['Mean intensity'][i])
            
        
#    lib_cell_properties_dict = ProcessImage.LibFluorescenceAnalysis(lib_folder, tag_round, lib_round, tagprotein_cell_properties_dict)
#    print('lib done.')
#    
#    # Devided by fusion protein brightness.
#    lib_cell_properties_dict = ProcessImage.CorrectForFusionProtein(tagprotein_cell_properties_dict, lib_cell_properties_dict, tagprotein_laserpower=1, lib_laserpower=30)
#    # Organize and add 'ranking' and 'boundingbox' fields to the structured array.
#    Overview_LookupBook = ProcessImage.OrganizeOverview(lib_cell_properties_dict, ['Mean intensity in contour', 0.16, 'Contour soma ratio', 0.8], EvaluatingPara_1, 1, EvaluatingPara_2, 0.5)
#    #--------------------------------------------------------------------------
##    Overview_LookupBook_sorted = ProcessImage.WeightedSorting(Overview_LookupBook, 'Mean intensity divided by tag', 'Mean intensity in contour', 'Contour soma ratio', 
##                                                              weight_1 = 0.4, weight_2 = 0.4, weight_3 = 0.2)
#    #--------------------------------------------------------------------------
#    selectionRadius = 'circle'
#    selectionPercent = 100
#    
#    Overview_LookupBook_filtered = ProcessImage.DistanceSelecting(Overview_LookupBook, selectionPercent)
#
#    totalselectnum = 5
    
    
#    fig = px.scatter(Overview_LookupBook, x=EvaluatingPara_1, y=EvaluatingPara_2, 
#               hover_name= 'ID', color= 'Normalized distance', 
#               hover_data= ['Sequence', 'Mean intensity'], width=1050, height=950)
#    fig.write_html('Screening scatters.html', auto_open=True)
    # Display scatters
#    get_ipython().run_line_magic('matplotlib', 'qt')
#    plt.scatter(Overview_LookupBook[EvaluatingPara_1], Overview_LookupBook[EvaluatingPara_2], s=np.pi*3, c='blue', alpha=0.5)
#    plt.scatter(Overview_LookupBook_filtered[EvaluatingPara_1], Overview_LookupBook_filtered[EvaluatingPara_2], s=np.pi*3, c='red', alpha=0.5)
#    plt.title('Screening scatter plot')
#    plt.xlabel(EvaluatingPara_1)
#    plt.ylabel(EvaluatingPara_2)
#    plt.show()
#    
##    get_ipython().run_line_magic('matplotlib', 'inline')
#
##    Top_from_Overview_LookupBook = Overview_LookupBook_sorted[0:20]
#    ranking = 1
#    for EachCell in range(len(Overview_LookupBook_filtered)):
#        spec = Overview_LookupBook_filtered[EachCell]['ID']
##        #-------------- readin image---------------
##        for file in os.walk(lib_folder):
##            if spec and 'Zmax' in file:
#        lib_imagefilename = os.path.join(lib_folder, spec+'_PMT_0Zmax.tif')
##                break
##            break
#        print(lib_imagefilename)
#        loaded_lib_image_display = imread(lib_imagefilename, as_gray=True)
#        # Retrieve boundingbox information
#        Each_bounding_box = Overview_LookupBook_filtered[EachCell]['BoundingBox']
#        minr = int(Each_bounding_box[Each_bounding_box.index('minr')+4:Each_bounding_box.index('_minc')])
#        maxr = int(Each_bounding_box[Each_bounding_box.index('maxr')+4:Each_bounding_box.index('_maxc')])        
#        minc = int(Each_bounding_box[Each_bounding_box.index('minc')+4:Each_bounding_box.index('_maxr')])
#        maxc = int(Each_bounding_box[Each_bounding_box.index('maxc')+4:len(Each_bounding_box)])
#        
##        plt.figure()
#        fig_showlabel, ax_showlabel = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
#        ax_showlabel.imshow(loaded_lib_image_display)#Show the first image
#        #--------------------------------------------------Add red boundingbox to axis----------------------------------------------
#        rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr, fill=False, edgecolor='cyan', linewidth=2)
##        contour_mean_bef_rounded = str(round(MeanIntensity_Contour, 3))[0:5]
#        ax_showlabel.add_patch(rect)
#        ax_showlabel.text(maxc, minr, 'NO_{}'.format(ranking),fontsize=8, color='orange', style='italic')
#        ranking += 1
#        # Based on the boundingbox for each cell from first image in the stack, raw image of slightly larger region is extracted from each round.
##        RankdisplayImg = loaded_lib_image_display[minr:maxr, minc:maxc] # Raw region image 
#        
#        ax_showlabel.set_axis_off()
#        plt.show()
# =============================================================================


                