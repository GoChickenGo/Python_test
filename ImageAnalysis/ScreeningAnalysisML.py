# -*- coding: utf-8 -*-
"""
Created on Thu May  7 15:50:10 2020

@author: xinmeng
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math
from skimage import data, exposure
from skimage.filters import threshold_otsu, threshold_local
from skimage.filters.rank import entropy
from skimage.segmentation import clear_border
from skimage.measure import label, perimeter, find_contours
from skimage.morphology import closing, square, opening, reconstruction, skeletonize, \
                                convex_hull_image, dilation, thin, binary_erosion, disk
from skimage.measure import regionprops, moments, moments_central, moments_hu
from skimage.color import label2rgb, gray2rgb
from skimage.restoration import denoise_tv_chambolle
from skimage.io import imread
from PIL import Image
from scipy.signal import convolve2d, medfilt
import scipy.interpolate as interpolate
from scipy.ndimage.filters import gaussian_filter1d
import numpy.lib.recfunctions as rfn
import pandas as pd
import copy
import os
import plotly.express as px
import sys
try:
    from findcontour import imageanalysistoolbox
except:
    from ImageAnalysis.findcontour import imageanalysistoolbox
#------------------------------------------------------------------------------
os.chdir(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\People\Xin Meng\Code\Python_test\ImageAnalysis') 
from mrcnn import visualize
sys.path.append(".\MaskRCNN")

from Config.ConfigFileDemo import cellConfig     
from DetectClass import Detect
#------------------------------------------------------------------------------


#================================================================ProcessImage===============================================
class ProcessImageML():
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        """
        # =============================================================================
        # Initialize the detector instance and load the model.
        # =============================================================================
        """
        # Load configuration file
        self.config = cellConfig()
        self.config.WeigthPath = r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\People\Xin Meng\Code\Data\Weights\WeightsMaskRCNNVal009.h5'
        self.Detector = Detect(self.config)        
        self.Detector.loadModel()
    #%%
    """
    # ======================================================================================================================
    # ************************************  Retrive scanning scheme and read in images. ************************************ 
    # ======================================================================================================================
    """

    def ReadinImgs_Roundstack(self, Nest_data_directory, rowIndex, colIndex):
        """
        Read in images from nest directory.
        
        Parameters
        ----------
        Nest_data_directory : string.
            The directory to folder where the screening data is stored.
        rowIndex, colIndex:
            Row and column index in stage coordinates.
    
        Returns
        -------
        PMT_image_wholetrace_stack : 2-D ndarray or stack of 2-D ndarray.
            Loaded images.
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
            temp_loaded_image = imread(img_fileName, as_gray=False)
            temp_loaded_image = temp_loaded_image[np.newaxis, :, :]
            if ImgSequenceNum == 1:
                PMT_image_wholetrace_stack = temp_loaded_image
            else:
                PMT_image_wholetrace_stack = np.concatenate((PMT_image_wholetrace_stack, temp_loaded_image), axis=0)
                    
        return PMT_image_wholetrace_stack
    
    def retrive_scanning_scheme(self, Nest_data_directory):
        """
        Return lists that contain round sequence and coordinates strings, like ['Coords1_R0C0', 'Coords2_R0C1500']

        Parameters
        ----------
        Nest_data_directory : string.
            The directory to folder where the screening data is stored.
    
        Returns
        -------
        RoundNumberList : List.
            List of all round numbers in screening.
        CoordinatesList : List.
            List of all stage coordinates in screening scheme.
        fileNameList: List.
            List of file names strings.
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
            
#        print(RoundNumberList, CoordinatesList, fileNameList)
        return RoundNumberList, CoordinatesList, fileNameList
    #%%
    """
    # ================================================================================================================
    # ************************************  Run detection on single image  ************************************* 
    # ================================================================================================================
    """
    def DetectionOnImage(self, Rawimage, axis = None, show_mask=True, show_bbox=True):
        """ 
        Convert image pixel values to unit8 to run on MaskRCNN, and then run MaskRCNN on it.
        """        
        image = Rawimage * (255.0/Rawimage.max())
        image=image.astype(int)+1
    
        if len(np.shape(image)) == 2:
            image = gray2rgb(image)
        
        # Run the detection on input image.
        results        = self.Detector.RunDetectionOnImage(image)
        
        MLresults      = results[0]
        
        if axis != None:
            # If axis is given, draw on axis.
            ax, fig        = visualize.display_instances(image, MLresults['rois'], MLresults['masks'], MLresults['class_ids'], 
                            ['BG'] + self.config.ValidLabels, scores=None, ax = axis, show_mask=show_mask, show_bbox=show_bbox, ReturnImageHandle=True) #MLresults['scores']
            
            return MLresults, ax, fig
        else:
            return MLresults
    """
    # ================================================================================================================
    # ************************************  Organize cell properties dictionary  ************************************* 
    # ================================================================================================================
    """

    def FluorescenceAnalysis(self, folder, round_num):
        """
        # =============================================================================
        # Given the folder and round number, return a dictionary for the round
        # that contains each scanning position as key and structured array of detailed 
        # information about each identified cell as content.
        #
        #   Returned structured array fields:
        #   - BoundingBox of cell ROI
        #   - Mean intensity of whole cell area
        #   - Mean intensity of cell membrane part
        #   - Contour soma ratio
        # =============================================================================
        
        Parameters
        ----------
        folder : string.
            The directory to folder where the screening data is stored.
        round_num : int.
            The target round number of analysis.
            
        Returns
        -------
        cell_Data : pd.DataFrame.
            Sum of return from func: retrieveDataFromML, for whole round.
        """
        RoundNumberList, CoordinatesList, fileNameList = self.retrive_scanning_scheme(folder)
        os.mkdir(os.path.join(folder, 'MLimages_{}'.format(round_num))) # Create the folder
        
        for EachRound in RoundNumberList:
            
            if EachRound == round_num:
                
                # Start numbering cells at each round
                self.cell_counted_inRound = 0  
                
                for EachCoord in CoordinatesList:
                    
                # =============================================================================
                #             For tag fluorescence:
                # =============================================================================    
                    print(EachCoord)
                    #-------------- readin image---------------
                    for Eachfilename in enumerate(fileNameList):
                        if EachCoord in Eachfilename[1] and EachRound in Eachfilename[1]:
                            ImgNameInfor = Eachfilename[1][0:len(Eachfilename[1])-14] # get rid of '_PMT_0Zmax.tif' in the name.
                            tag_imagefilename = os.path.join(folder, Eachfilename[1])
                    #------------------------------------------
    
                    # =========================================================================
                    #                     USING MASKRCNN...
                    # =========================================================================
                    Imagepath      = self.Detector._fixPathName(tag_imagefilename)
                    Rawimage     = imread(Imagepath)
                    
#                    if ClearImgBef == True:
#                        # Clear out junk parts to make it esaier for ML detection.
#                        RawimageCleared = self.preProcessMLimg(Rawimage, smallest_size=300, lowest_region_intensity=0.16)
#                    else:
#                        RawimageCleared = Rawimage.copy()
                                        
                    image = self.Convert2Unit8(Imagepath, Rawimage)
                    
                    # Run the detection on input image.
                    results        = self.Detector.RunDetectionOnImage(image)
                    
                    MLresults      = results[0]
                    ax, fig        = visualize.display_instances(image, MLresults['rois'], MLresults['masks'], MLresults['class_ids'], 
                                                    ['BG'] + self.config.ValidLabels, MLresults['scores'],ReturnImageHandle=True)
                    ax.imshow(fig)

                    # Save the detection image
                    segmentationImg = Image.fromarray(fig) #generate an image object
                    segmentationImg.save(os.path.join(folder, 'MLimages_{}\{}.tif'.format(round_num, ImgNameInfor)))#save as tif
                    
                    if self.cell_counted_inRound == 0:
                        cell_Data = self.retrieveDataFromML(Rawimage, MLresults, str(ImgNameInfor))
                    else:                       
                        Cell_Data_new = self.retrieveDataFromML(Rawimage, MLresults, str(ImgNameInfor))
                        if len(Cell_Data_new) > 0:
                            cell_Data = cell_Data.append(Cell_Data_new)
                    
        return cell_Data
    
    def Convert2Unit8(self, Imagepath, Rawimage):
        """ Convert image pixel values to unit8 to run on MaskRCNN.
        """
        if Imagepath[len(Imagepath)-3:len(Imagepath)] == 'tif':
            """ set image data type to unit8
            """
            image = Rawimage * (255.0/Rawimage.max())
            image=image.astype(int)+1
        
            if len(np.shape(image)) == 2:
                image = gray2rgb(image)
    
            return image
        
        else:
            return Rawimage
                
    def retrieveDataFromML(self, image, MLresults, ImgNameInfor):
        """ Given the raw image and ML returned result dictionary, calculate interested parameters from it.
        
        class_ids = 3: Flat cell
        class_ids = 2: Round cell
        class_ids = 1: Dead cell
        
        #   Returned structured array fields:
        #   - BoundingBox of cell ROI
        #   - Mean intensity of whole cell area
        #   - Mean intensity of cell membrane part
        #   - Contour soma ratio
        
        Parameters
        ----------
        image : 2-D ndarray.
            Input image.
        MLresults : Dictionary.
            The returned dictionary from MaskRCNN.
        ImgNameInfor : String.
            Information of input image.
            
        Returns
        -------
        Cell_DataFrame : pd.DataFrame.
            Detail information extracted from MaskRCNN mask from the image, in pandas dataframe format.
        """
        ROInumber = len(MLresults['scores']) 
        cell_counted_inImage = 0
        
        for eachROI in range(ROInumber):
            if MLresults['class_ids'][eachROI] == 3:
                ROIlist = MLresults['rois'][eachROI]
                CellMask = MLresults['masks'][:,:,eachROI]
                
                RawImg_roi = image[ROIlist[0]:ROIlist[2], ROIlist[1]:ROIlist[3]] # Raw image in each bounding box
                CellMask_roi = CellMask[ROIlist[0]:ROIlist[2], ROIlist[1]:ROIlist[3]] # Individual cell mask in each bounding box
    
                # =============================================================
                #             # Find contour along cell mask
                # =============================================================
                cell_contour_mask = self.findContour(CellMask_roi, RawImg_roi.copy(), 0.001) # Return the binary contour mask in bounding box.
                # after here intensityimage_intensity is changed from contour labeled with number 5 to binary image.
                cell_contour_mask_dilated = self.inwardDilationMask(cell_contour_mask, CellMask_roi, dilationparameter = 11)   
                
                #-------------Calculate intensity based on masks---------------
                cell_contour_meanIntensity = np.mean(RawImg_roi[np.where(cell_contour_mask_dilated == 1)]) # Mean pixel value of cell membrane.
                cell_area_meanIntensity = np.mean(RawImg_roi[np.where(CellMask_roi == 1)]) # Mean pixel value of whole cell area.
                
                cell_soma_mask = CellMask_roi - cell_contour_mask_dilated
                cell_soma_meanIntensity = np.mean(RawImg_roi[np.where(cell_soma_mask == 1)]) # Mean pixel value of soma area.         
                cell_contourSoma_ratio = round(cell_contour_meanIntensity/cell_soma_meanIntensity, 5) # Calculate the contour/soma intensity ratio.
                
                boundingbox_info = 'minr{}_maxr{}_minc{}_maxc{}'.format(ROIlist[0], ROIlist[2], ROIlist[1], ROIlist[3])

                if cell_counted_inImage == 0:
                    Cell_DataFrame = pd.DataFrame([[ImgNameInfor, boundingbox_info, cell_area_meanIntensity, cell_contour_meanIntensity, cell_contourSoma_ratio]], 
                                      columns = ['ImgNameInfor', 'BoundingBox', 'Mean_intensity', 'Mean_intensity_in_contour', 'Contour_soma_ratio'],
                                      index = ['Cell {}'.format(self.cell_counted_inRound)])
                else:
                    Cell_DataFrame_new = pd.DataFrame([[ImgNameInfor, boundingbox_info, cell_area_meanIntensity, cell_contour_meanIntensity, cell_contourSoma_ratio]], 
                                      columns = ['ImgNameInfor', 'BoundingBox', 'Mean_intensity', 'Mean_intensity_in_contour', 'Contour_soma_ratio'],
                                      index = ['Cell {}'.format(self.cell_counted_inRound)])                    
                    Cell_DataFrame = Cell_DataFrame.append(Cell_DataFrame_new)
                    
                self.cell_counted_inRound += 1
                cell_counted_inImage += 1
        
        if cell_counted_inImage == 0:
            return pd.DataFrame()
        else:
            return Cell_DataFrame 
    
    #%%
    def MergeDataFrames(self, cell_Data_1, cell_Data_2, method = 'TagLib'):
        """ Merge Data frames based on input methods.
        
        #   'TagLib': Merge tag protein screening round with library screening round.
        #   -In this mode, for each bounding box in the tag round, it will search through every bounding box in library round and find the best match with
        #   -with the most intersection, and then treat them as images from the same cell and merge the two input dataframes.
        
        Parameters
        ----------
        cell_Data_1, cell_Data_2 : pd.DataFrame.
            Input data from two rounds.
        method : String.
            Merge method. 
            'TagLib': for brightness screening.
            
        Returns
        -------
        Cell_DataFrame_Merged : pd.DataFrame.
            Detail information from merging two input dataframe, with bounding boxes from different rounds overlapping above 60% seen as same cell.
        """
        if method == 'TagLib':
            cell_Data_1 = cell_Data_1.add_suffix('_Tag')
            cell_Data_2 = cell_Data_2.add_suffix('_Lib')
            cell_merged_num = 0
            # Assume that cell_Data_1 is the tag protein dataframe, for each of the cell bounding box, find the one with the most intersection from library dataframe.
            for index_Data_1, row_Data_1 in cell_Data_1.iterrows():
                # For each flat cell in round
                bounding_box_str_Data_1 = row_Data_1['BoundingBox_Tag']
                ImgNameInforString_Data1 = row_Data_1['ImgNameInfor_Tag']
                # Retrieve boundingbox information
                minr_Data_1 = int(bounding_box_str_Data_1[bounding_box_str_Data_1.index('minr')+4:bounding_box_str_Data_1.index('_maxr')])
                maxr_Data_1 = int(bounding_box_str_Data_1[bounding_box_str_Data_1.index('maxr')+4:bounding_box_str_Data_1.index('_minc')])        
                minc_Data_1 = int(bounding_box_str_Data_1[bounding_box_str_Data_1.index('minc')+4:bounding_box_str_Data_1.index('_maxc')])
                maxc_Data_1 = int(bounding_box_str_Data_1[bounding_box_str_Data_1.index('maxc')+4:len(bounding_box_str_Data_1)])
                intersection_Area_percentage_list = []
                index_list_Data_2 = []
                # Iterate through DataFrame 2 calculating intersection area
                for index_2, row_Data_2 in cell_Data_2.iterrows():
                    ImgNameInforString_Data2 = row_Data_2['ImgNameInfor_Lib']
                    # Search in the same coordinates.
                    if ImgNameInforString_Data2[ImgNameInforString_Data2.index('_R')+1:len(ImgNameInforString_Data2)] == \
                    ImgNameInforString_Data1[ImgNameInforString_Data1.index('_R')+1:len(ImgNameInforString_Data1)]:
                        bounding_box_str_Data_2 = row_Data_2['BoundingBox_Lib']
                        # Retrieve boundingbox information
                        minr_Data_2 = int(bounding_box_str_Data_2[bounding_box_str_Data_2.index('minr')+4:bounding_box_str_Data_2.index('_maxr')])
                        maxr_Data_2 = int(bounding_box_str_Data_2[bounding_box_str_Data_2.index('maxr')+4:bounding_box_str_Data_2.index('_minc')])        
                        minc_Data_2 = int(bounding_box_str_Data_2[bounding_box_str_Data_2.index('minc')+4:bounding_box_str_Data_2.index('_maxc')])
                        maxc_Data_2 = int(bounding_box_str_Data_2[bounding_box_str_Data_2.index('maxc')+4:len(bounding_box_str_Data_2)])                
                        
                        # Overlapping row
                        if minr_Data_2 < maxr_Data_1 and maxr_Data_2 > minr_Data_1:
                            intersection_rowNumber = min((abs(minr_Data_2 - maxr_Data_1), maxr_Data_1 - minr_Data_1)) - max(maxr_Data_1 - maxr_Data_2, 0)
                        else:
                            intersection_rowNumber = 0
                        # Overlapping column
                        if minc_Data_2 < maxc_Data_1 and maxc_Data_2 > minc_Data_1:
                            intersection_colNumber = min((abs(minc_Data_2 - maxc_Data_1), maxc_Data_1 - minc_Data_1)) - max(maxc_Data_1 - maxc_Data_2, 0)
                        else:
                            intersection_colNumber = 0                
            
                        intersection_Area = intersection_rowNumber * intersection_colNumber
                        intersection_Area_percentage = intersection_Area / ((maxr_Data_1 - minr_Data_1) * (maxc_Data_1 - minc_Data_1))
                        intersection_Area_percentage_list.append(intersection_Area_percentage)
                        index_list_Data_2.append(index_2)
                
                if len(intersection_Area_percentage_list) > 0:
                    # Link back cells based on intersection area
                    if max(intersection_Area_percentage_list) > 0.6:
                        # If in DataFrame_2 there's a cell that has a overlapping bounding box, merge and generate a new dataframe.
                        Merge_data2_index = index_list_Data_2[intersection_Area_percentage_list.index(max(intersection_Area_percentage_list))]
      
                        Merged_identifiedCell = pd.concat((cell_Data_1.loc[index_Data_1], cell_Data_2.loc[Merge_data2_index]), axis = 0)
                        
                        # Add the lib/tag brightness ratio
                        Lib_Tag_ratio = pd.DataFrame([Merged_identifiedCell.loc['Mean_intensity_in_contour_Lib'] / Merged_identifiedCell.loc['Mean_intensity_in_contour_Tag']],
                                                     index = ['Lib_Tag_contour_ratio'])
                        
                        Merged_identifiedCell = pd.concat((Merged_identifiedCell, Lib_Tag_ratio), axis = 0)
                        Merged_identifiedCell.rename(columns={0:'Cell {}'.format(cell_merged_num)}, inplace=True) # Rename the column name, which is the index name after T.
                         
                        if cell_merged_num == 0:
                            Cell_DataFrame_Merged = Merged_identifiedCell
                        else:
                            Cell_DataFrame_Merged = pd.concat((Cell_DataFrame_Merged, Merged_identifiedCell), axis = 1)
                        cell_merged_num += 1
              
            Cell_DataFrame_Merged = Cell_DataFrame_Merged.T
            
        return Cell_DataFrame_Merged
    
    
    def FilterDataFrames(self, DataFrame, Mean_intensity_in_contour_thres, Contour_soma_ratio_thres, *args, **kwargs):
        """
        Filter the dataframe based on input numbers.
        
        Parameters
        ----------
        DataFrame : pd.DataFrame.
            Input data.
        Mean_intensity_in_contour_thres : Float.
            Threshold for eliminating dim cells.
        Contour_soma_ratio_thres : Float.
            Threshold for contour soma ratio.
            
        Returns
        -------
        DataFrames_filtered : pd.DataFrame.
            Filtered dataframe.
        """
        DataFrames_filtered = DataFrame[(DataFrame['Mean_intensity_in_contour_Lib'] > Mean_intensity_in_contour_thres) & 
                                        (DataFrame['Contour_soma_ratio_Lib'] > Contour_soma_ratio_thres)]
                
        return DataFrames_filtered
    
    def Sorting_onTwoaxes(self, DataFrame, axis_1, axis_2, weight_1, weight_2):
        """
        Sort the dataframe based on normalized distance calculated from two given axes.
        """
        if axis_1 == "Lib_Tag_contour_ratio" and axis_2 == "Contour_soma_ratio_Lib":
            # Get the min and max on two axes, prepare for next step.
            Contour_soma_ratio_min, Contour_soma_ratio_max = DataFrame.Contour_soma_ratio_Lib.min(), DataFrame.Contour_soma_ratio_Lib.max()
            Lib_Tag_contour_ratio_min, Lib_Tag_contour_ratio_max = DataFrame.Lib_Tag_contour_ratio.min(), DataFrame.Lib_Tag_contour_ratio.max()
            
            DataFrame_sorted = DataFrame.loc[(((DataFrame.Contour_soma_ratio_Lib - Contour_soma_ratio_min) / (Contour_soma_ratio_max - Contour_soma_ratio_min)) ** 2 * weight_2
            + ((DataFrame.Lib_Tag_contour_ratio - Lib_Tag_contour_ratio_min) / (Lib_Tag_contour_ratio_max - Lib_Tag_contour_ratio_min)) **2 * weight_1) \
            .sort_values(ascending=False).index]   
    
        return DataFrame_sorted
    
    def showPlotlyScatter(self, DataFrame, x_axis, y_axis):
        
        fig = px.scatter(DataFrame, x = x_axis, y=y_axis, hover_name= DataFrame.index, color= 'Lib_Tag_contour_ratio',
                         hover_data= ['Contour_soma_ratio_Lib', 'Lib_Tag_contour_ratio', 'ImgNameInfor_Lib'], width=1050, height=950)
#        fig.update_layout(hovermode="x")
        fig.write_html('Screening scatters.html', auto_open=True)
        
    #%%
    """
    # ======================================================================================================================
    # ****************************************  Traditional image analysis part. ******************************************* 
    # ======================================================================================================================
    """    
    def findContour(self, imagewithouthole, image, threshold):
        """
        Return contour mask by eroding inward from filled cell mask.
        
        Parameters
        ----------
        imagewithouthole : 2-D ndarray.
            Input filled image.
        image : 2-D ndarray.
            Raw image.
        threshold : Float.
            Threshold for finding contour.
            
        Returns
        -------
        binarycontour : 2-D ndarray.
            Binary contour mask.
        """      
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
    
    def inwardDilationMask(self, binarycontour, imagewithouthole, dilationparameter):
        
        dilationimg = dilation(binarycontour, square(dilationparameter))
        
        contour_mask = dilationimg*imagewithouthole
        
        return contour_mask
                    
    
    def preProcessMLimg(self, image, smallest_size, lowest_region_intensity):
        """
        # =======Some preprocessing to get rid of junk parts and make image clearer.=========
        #
        # --smallest_size/biggest_size: cells size out of this range are ignored.
        # --lowest_region_intensity: cells with mean region intensity below this are ignored.
        # --cell_region_opening_factor: degree of opening operation on individual cell mask.
        # --cell_region_closing_factor: degree of closing operation on individual cell mask.
        #====================================================================================
        """
        openingfactor=2
        closingfactor=3
        binary_adaptive_block_size=335
        cell_region_opening_factor=1
        cell_region_closing_factor=2
        
        image = denoise_tv_chambolle(image, weight=0.01) # Denoise the image.
      
        # -----------------------------------------------Set background to 0-----------------------------------------------
        AdaptiveThresholding = threshold_local(image, binary_adaptive_block_size, offset=0)
        BinaryMask = image >= AdaptiveThresholding
        OpeningBinaryMask = opening(BinaryMask, square(int(openingfactor)))
        RegionProposal_Mask = closing(OpeningBinaryMask, square(int(closingfactor)))
        
        clear_border(RegionProposal_Mask)
        # label image regions, prepare for regionprops
        label_image = label(RegionProposal_Mask)  
        FinalpreProcessROIMask = np.zeros((image.shape[0], image.shape[1]))
        
        for region in regionprops(label_image,intensity_image = image): 
            
            # skip small images
            if region.area > smallest_size and region.mean_intensity > lowest_region_intensity:
                
                # draw rectangle around segmented coins
                minr, minc, maxr, maxc = region.bbox

                bbox_area = (maxr-minr)*(maxc-minc)
                # Based on the boundingbox for each cell from first image in the stack, raw image of slightly larger region is extracted from each round.
                RawRegionImg = image[minr:maxr, minc:maxc] # Raw region image 

                #---------Get the cell filled mask-------------
                filled_mask_bef, MeanIntensity_Background = imageanalysistoolbox.get_cell_filled_mask(RawRegionImg = RawRegionImg, region_area = bbox_area*0.2, 
                                                                                                      cell_region_opening_factor = cell_region_opening_factor, 
                                                                                                      cell_region_closing_factor = cell_region_closing_factor)

                filled_mask_convolve2d = imageanalysistoolbox.smoothing_filled_mask(RawRegionImg, filled_mask_bef = filled_mask_bef, region_area = bbox_area*0.2, threshold_factor = 1.1)
                #----------Put region maks back to original image.-----------
                preProcessROIMask = np.zeros((image.shape[0], image.shape[1]))
                preProcessROIMask[minr:maxr, minc:maxc] = filled_mask_convolve2d
                
                FinalpreProcessROIMask += preProcessROIMask
                
        FinalpreProcessROIMask = np.where(FinalpreProcessROIMask > 1, 1, FinalpreProcessROIMask)
        ClearedImg = FinalpreProcessROIMask * image
        
        return ClearedImg
    #%%
    
if __name__ == "__main__":
    
    import time
    # =============================================================================
    tag_folder = r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-4-08 Archon citrine library 100FOVs\trial_3_library_cellspicked'
    lib_folder = r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-5-28 Stage stability test\crll1\New folder'
  #   tag_folder = r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-3-6 Archon brightness screening\NovArch library'

    tag_round = 'Round1'
    lib_round = 'Round2'
    
    starttime = time.time()
    
    ProcessML = ProcessImageML()

#    cell_Data_1 = ProcessML.FluorescenceAnalysis(lib_folder, tag_round)
    cell_Data_2 = ProcessML.FluorescenceAnalysis(lib_folder, tag_round)
#    Cell_DataFrame_Merged = ProcessML.MergeDataFrames(cell_Data_1, cell_Data_2, method = 'TagLib')
#    DataFrames_filtered = ProcessML.FilterDataFrames(Cell_DataFrame_Merged, Mean_intensity_in_contour_thres = 0.25, Contour_soma_ratio_thres = 1)
#    DataFrame_sorted = ProcessML.Sorting_onTwoaxes(DataFrames_filtered, axis_1 = "Lib_Tag_contour_ratio", axis_2 = "Contour_soma_ratio_Lib", weight_1 = 1, weight_2 = 0.5)
#    ProcessML.showPlotlyScatter(DataFrame_sorted, x_axis='Lib_Tag_contour_ratio', y_axis="Contour_soma_ratio_Lib")
    # =============================================================================
#    tif_image = imread(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\People\Xin Meng\Code\Data\Trial_tif\Round1_Coords3_R16500C19800_PMT_0Zmax.tif')
#    MLresults_dict = np.load \
#    (r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\People\Xin Meng\Code\Data\Trial_tif\tagprotein_cell_properties_dict.npy',allow_pickle='TRUE').item()
#    