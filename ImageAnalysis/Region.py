# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 17:58:53 2019

@author: xinmeng
"""

import numpy as np
from trymageAnalysis_v2 import ImageAnalysis
from skimage.io import imread
from PIL import Image
import matplotlib.pyplot as plt
from IPython import get_ipython
from matplot import SelectFromCollection
import numpy.lib.recfunctions as rfn



Rawimgbef = imread("D:/work/Phd work/avg5_1_sameview.tif", as_gray=True)
Rawimgaft = imread("D:/work/Phd work/avg5_2_sameview.tif", as_gray=True)
#Rawimgbef = imread("D:/TUD/015001500out_1st.tif", as_gray=True)
#Rawimgaft = imread("D:/TUD/015001500out_1st.tif", as_gray=True)
#Rawimgbef = cv2.imread('D:\\regiontest1.png',0)
#Rawimgaft = cv2.imread('D:\\regiontest1.png',0)

Data_dict_0 = {}
Data_dict_0[str(-1500)+str(-1500)] = Rawimgbef[:, 53:553]#[134:360, 450:600]#[180:290, 220:330]###[40:100,300:350]
imagrarray = Rawimgbef#[40:100,300:350]


Data_dict_1 = {}
Data_dict_1[str(-1500)+str(-1500)] = Rawimgaft[:, 53:553]#[134:360, 450:600]#[180:290, 220:330]##[:, 53:553]#[40:100,300:350]

#img_before = Rawimgbef#[0:190, 0:250]#[0:22, 0:400]#[140:190, 155:205]#[200:400,300:500]#[483:483+600,690:690+600]  #crop image
#img_after = Rawimgaft#[0:190, 0:250]#[0:22, 0:400]#[140:190, 155:205]#[200:400,300:500]#[483:483+600,690:690+600]

S = ImageAnalysis(Data_dict_0[str(-1500)+str(-1500)], Data_dict_1[str(-1500)+str(-1500)])
v1, v2, bw, thres = S.applyMask(2,2,335)
#R = S.ratio(v1, v2)
L, cp, coutourmask, coutourimg, intensityimage_intensity, r = S.get_intensity_properties(200, bw, thres, v1, v2, -1500, -1500, 0.001,8)
#get_ipython().run_line_magic('matplotlib', 'qt')
S.showlabel(200, bw, v1, thres, -1500, -1500, cp)
#Fill, sliced, inten= S.showlabel(1000, bw, v2, thres, -1500, -1500, cp)
#print (L)
#Localimg = Image.fromarray(v2) #generate an image object
#Localimg.save('out_1st.tif') #save as tif

cp = rfn.append_fields(cp, 'Original_sequence', list(range(0, len(cp))), usemask=False)
print (cp)
#get_ipython().run_line_magic('matplotlib', 'qt')
#plt.plot(cp['Circularity'], cp['Mean intensity in contour'], 'ro')
#plt.axis([0, 6, 0, 20])
#plt.show()

sorted_cp = S.sort_using_weight(cp, 'Circularity', 'Mean intensity in contour', 0.5, 0.5)
#mouse_select_points(cp['Circularity'], cp['Mean intensity in contour'])
#app = highlightpoints(cp['Circularity'], cp['Mean intensity in contour'])
#app.makePlot()
####selection = SelectFromCollection(cp['Circularity'], cp['Mean intensity in contour'])
#input("Press Enter to continue...")
#wait for space input

####points = selection.collection_of_point
####print(points)
#ppp=assd.get_container()
'''
fig1 = plt.figure(1)
ax1 = fig1.add_subplot(111)

def accept(event):
    if event.key == "enter":
        print("Selected points:")
        print(selector.xys[selector.ind])
        selector.disconnect()
        ax1.set_title("")
        fig1.canvas.draw()

fig1.canvas.mpl_connect("key_press_event", accept)
ax1.set_title("Press enter to accept selected points.")

plt.show()
'''

'''
Rawimgbef1 = imread("D:/TUD/015001500out_1st.tif", as_gray=True)
Rawimgaft1 = imread("D:/TUD/015001500out_1st.tif", as_gray=True)
#Rawimgbef = cv2.imread('D:\\regiontest1.png',0)
#Rawimgaft = cv2.imread('D:\\regiontest1.png',0)

Data_dict_0[str(-1500)+str(-500)] = Rawimgbef1

Data_dict_1[str(-1500)+str(-500)] = Rawimgaft1

S = ImageAnalysis(Data_dict_0[str(-1500)+str(-500)], Data_dict_1[str(-1500)+str(-500)])
v1, v2, bw, thres = S.applyMask()
R = S.ratio(v1, v2)
L1, cp1, coutourmask, coutourimg, sing = S.get_intensity_properties(100, bw, v2, thres, v2, -1500, -500, 7)
S.showlabel(100, bw, v2, thres, -1500, -500, cp1)
#Fill, sliced, inten= S.showlabel(1000, bw, v2, thres, -1500, -1500, cp)
#print (L1)
print (cp1)

input("Press Enter to continue...")

print('...........Original ..........')

loopnum = 1
All_cell_properties_dict = {}
All_cell_properties_dict[0] = []
All_cell_properties = []

All_cell_properties_dict[1] = cp
All_cell_properties_dict[2] = cp1
if loopnum != 0:
    All_cell_properties = np.append(All_cell_properties_dict[1], All_cell_properties_dict[2], axis=0)
else:
    pass
#All_cell_properties = cp1
# Put all results in one

# Label the original order
original_dtype = np.dtype(All_cell_properties.dtype.descr + [('Original_sequence', '<i4')])
original_cp = np.zeros(All_cell_properties.shape, dtype=original_dtype)
original_cp['Row index'] = All_cell_properties['Row index']
original_cp['Column index'] = All_cell_properties['Column index']
original_cp['Mean intensity'] = All_cell_properties['Mean intensity']
original_cp['Circularity'] = All_cell_properties['Circularity']
original_cp['Mean intensity in contour'] = All_cell_properties['Mean intensity in contour']
original_cp['Original_sequence'] = list(range(0, len(All_cell_properties)))

print (original_cp['Mean intensity in contour'])
print('*********************sorted************************')
#sort
sortedcp = np.flip(np.sort(original_cp, order='Mean intensity in contour'), 0)
selected_num = 10 #determine how many we want
#unsorted_cp = All_cell_properties[:selected_num]
#targetcp = sortedcp[:selected_num]

rank_dtype = np.dtype(sortedcp.dtype.descr + [('Ranking', '<i4')])
ranked_cp = np.zeros(sortedcp.shape, dtype=rank_dtype)
ranked_cp['Row index'] = sortedcp['Row index']
ranked_cp['Column index'] = sortedcp['Column index']
ranked_cp['Mean intensity'] = sortedcp['Mean intensity']
ranked_cp['Circularity'] = sortedcp['Circularity']
ranked_cp['Mean intensity in contour'] = sortedcp['Mean intensity in contour']
ranked_cp['Original_sequence'] = sortedcp['Original_sequence']
ranked_cp['Ranking'] = list(range(0, len(All_cell_properties)))

print (ranked_cp)
print('***********************Original sequence with ranking**************************')

#back to original sequence with ranking
withranking_cp = np.sort(ranked_cp, order='Original_sequence')
print (withranking_cp['Mean intensity in contour'])

cp_index_dict = {}
Pic_name = str(-1500)+str(-1500)
Pic_name1 = str(-1500)+str(-500)

cp_index_dict[Pic_name] = [0, 12]
cp_index_dict[Pic_name1] = [13, 35]

target = Pic_name
target1 = Pic_name1

S = ImageAnalysis(Data_dict_0[target], Data_dict_1[target]) #S = ImageAnalysis(Data_dict_0[Pic_name], Data_dict_1[Pic_name])
v1, v2, bw, thres = S.applyMask()
S.showlabel_with_rank(100, bw, v2, cp_index_dict[target][0], cp_index_dict[target][1], withranking_cp, 'Mean intensity in contour', 10)

S = ImageAnalysis(Data_dict_0[target1], Data_dict_1[target1]) #S = ImageAnalysis(Data_dict_0[Pic_name], Data_dict_1[Pic_name])
v1, v2, bw, thres = S.applyMask()
S.showlabel_with_rank(100, bw, v2, cp_index_dict[target1][0], cp_index_dict[target1][1], withranking_cp, 'Mean intensity in contour', 10)

cell_properties_selected_hits = ranked_cp[0:7]
cell_properties_selected_hits_index_sorted = np.sort(cell_properties_selected_hits, order=['Row index', 'Column index'])

# for test
index_samples1 = np.array([[-1500, -1500,-1500, -1500, -1500, -500, -500, -500],   # i
                           [-1500, -1500, -500,  -500,  -500, -500,  500,  500]])  # j

# merge repeated index
# i in 1st row, j in 2nd row
index_samples = np.vstack((cell_properties_selected_hits_index_sorted['Row index'],cell_properties_selected_hits_index_sorted['Column index']))

merged_index_samples = index_samples[:,0]

#consider these after 1st one
for i in range(1, len(index_samples[0])):
    #print(index_samples[:,i][0] - index_samples[:,i-1][0])    
    if index_samples[:,i][0] != index_samples[:,i-1][0] or index_samples[:,i][1] != index_samples[:,i-1][1]: 
        merged_index_samples = np.append(merged_index_samples, index_samples[:,i], axis=0)
merged_index_samples = merged_index_samples.reshape(-1, 2) # 1st column=i, 2nd column=j
'''