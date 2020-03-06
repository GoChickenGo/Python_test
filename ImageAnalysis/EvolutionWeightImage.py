# -*- coding: utf-8 -*-
"""
Created on Sun Jan 19 18:23:02 2020

@author: xinmeng
"""

import numpy as np
from trymageAnalysis_v3 import ImageAnalysis
from skimage.io import imread
from PIL import Image
import matplotlib.pyplot as plt
from IPython import get_ipython
from matplot import SelectFromCollection
from matlabAnalysis import readbinaryfile, extractV

RawimgKC_1 = imread(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-1-22 Archon 2P KCl new scheme\scanning_3\analysis FOV1 Zmax\R7.tif', as_gray=True)#(r"O:\Delft\data\PMT__2019-11-08_14-55-56.tif", as_gray=True)
RawimgKC_2 = imread(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-1-22 Archon 2P KCl new scheme\scanning_3\analysis FOV1 Zmax\R8.tif', as_gray=True)#(r"O:\Delft\data\PMT__2019-11-08_14-55-56.tif", as_gray=True)
RawimgKC_3 = imread(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-1-22 Archon 2P KCl new scheme\scanning_3\analysis FOV1 Zmax\R9.tif', as_gray=True)#(r"O:\Delft\data\PMT__2019-11-08_14-55-56.tif", as_gray=True)
RawimgKC_4 = imread(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-1-22 Archon 2P KCl new scheme\scanning_3\analysis FOV1 Zmax\R10.tif', as_gray=True)#(r"O:\Delft\data\PMT__2019-11-08_14-55-56.tif", as_gray=True)

#RawimgKC_1 = RawimgKC_1[:,50:550]
#RawimgKC_2 = RawimgKC_2[:,50:550]
#RawimgKC_3 = RawimgKC_3[:,50:550]
#RawimgKC_4 = RawimgKC_4[:,50:550]

RawimgEC_1 = imread(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-1-22 Archon 2P KCl new scheme\scanning_3\analysis FOV1 Zmax\R2.tif', as_gray=True)#(r"O:\Delft\data\PMT__2019-11-08_14-55-56.tif", as_gray=True)
RawimgEC_2 = imread(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-1-22 Archon 2P KCl new scheme\scanning_3\analysis FOV1 Zmax\R3.tif', as_gray=True)#(r"O:\Delft\data\PMT__2019-11-08_14-55-56.tif", as_gray=True)
RawimgEC_3 = imread(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-1-22 Archon 2P KCl new scheme\scanning_3\analysis FOV1 Zmax\R4.tif', as_gray=True)#(r"O:\Delft\data\PMT__2019-11-08_14-55-56.tif", as_gray=True)
RawimgEC_4 = imread(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-1-22 Archon 2P KCl new scheme\scanning_3\analysis FOV1 Zmax\R5.tif', as_gray=True)

#RawimgEC_1 = RawimgEC_1[:,50:550]
#RawimgEC_2 = RawimgEC_2[:,50:550]
#RawimgEC_3 = RawimgEC_3[:,50:550]
#RawimgEC_4 = RawimgEC_4[:,50:550]

RawimgEC_5 = imread(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-1-22 Archon 2P KCl new scheme\scanning_3\analysis FOV1 Zmax\R12.tif', as_gray=True)#(r"O:\Delft\data\PMT__2019-11-08_14-55-56.tif", as_gray=True)
RawimgEC_6 = imread(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-1-22 Archon 2P KCl new scheme\scanning_3\analysis FOV1 Zmax\R13.tif', as_gray=True)#(r"O:\Delft\data\PMT__2019-11-08_14-55-56.tif", as_gray=True)
RawimgEC_7 = imread(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-1-22 Archon 2P KCl new scheme\scanning_3\analysis FOV1 Zmax\R14.tif', as_gray=True)#(r"O:\Delft\data\PMT__2019-11-08_14-55-56.tif", as_gray=True)
RawimgEC_8 = imread(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Octoscope\2020-1-22 Archon 2P KCl new scheme\scanning_3\analysis FOV1 Zmax\R15.tif', as_gray=True)


videostack = np.stack((RawimgEC_1, RawimgEC_2, RawimgEC_3, RawimgEC_4, RawimgKC_1, RawimgKC_2, RawimgKC_3, RawimgKC_4, RawimgEC_5, RawimgEC_6, RawimgEC_7, RawimgEC_8))
SolutionWaveform = np.append(np.zeros(4), np.ones(4))
SolutionWaveform = np.append(SolutionWaveform, np.zeros(4))
#
weight_ins = extractV(videostack, SolutionWaveform)
corrimage, weightimage, sigmaimage= weight_ins.cal()

#weightimage = videostack[6,:,:]-videostack[2,:,:]

plt.figure()
plt.imshow(corrimage, cmap = plt.cm.gray)
plt.show()