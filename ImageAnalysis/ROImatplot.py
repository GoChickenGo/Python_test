# -*- coding: utf-8 -*-
"""
Created on Tue Aug  6 11:19:37 2019

@author: xinmeng
"""

"""
compute the mean and stddev of 100 data sets and plot mean vs stddev.
When you click on one of the mu, sigma points, plot the raw data from
the dataset that generated the mean and stddev
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.widgets import LassoSelector
#from IPython import get_ipython

class mouse_select_points():
    def __init__(self, value1, value2):
        self.axis1 = value1
        self.axis2 = value2
        
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_title('click on points')
        
        line, = ax.plot(self.axis1, self.axis2, 'o', picker=5)  # 5 points tolerance
        
        def onpick(event):
            thisline = event.artist
            xdata = thisline.get_xdata()
            ydata = thisline.get_ydata()
            ind = event.ind
            points = [xdata[ind][0], ydata[ind][0]]
            #points = tuple(zip(xdata[ind], ydata[ind]))
            print('onpick points:', points)
        
        fig.canvas.mpl_connect('pick_event', onpick)
        
        plt.show()


'''
Highlight point selected with picker
'''       
class highlightpoints(object):
    def __init__(self, value1, value2):
        self.axis1 = value1
        self.axis2 = value2
    def makePlot(self):
        self.fig = plt.figure('Test', figsize=(10, 8))
        ax = plt.subplot(111)
        ax.plot(self.axis1, self.axis2, 'o', color='red', picker=5)
        #ax.plot(self.axis1, self.axis2, 'o', color='blue', picker=5)
        self.highlight, = ax.plot([], [], 'o', color='yellow')
        self.cid = plt.connect('pick_event', self.onPick)
        plt.show()

    def onPick(self, event=None):
        this_point = event.artist
        x_value = this_point.get_xdata()
        y_value = this_point.get_ydata()
        ind = event.ind
        self.highlight.set_data(x_value[ind][0],y_value[ind][0])
        self.fig.canvas.draw_idle()
        
class SelectFromCollection(object):
    """Select indices from a matplotlib collection using `LassoSelector`.

    Selected indices are saved in the `ind` attribute. This tool fades out the
    points that are not part of the selection (i.e., reduces their alpha
    values). If your collection has alpha < 1, this tool will permanently
    alter the alpha values.

    Note that this tool selects collection objects based on their *origins*
    (i.e., `offsets`).

    Parameters
    ----------
    ax : :class:`~matplotlib.axes.Axes`
        Axes to interact with.

    collection : :class:`matplotlib.collections.Collection` subclass
        Collection you want to select from.

    alpha_other : 0 <= float <= 1
        To highlight a selection, this tool sets all selected points to an
        alpha value of 1 and non-selected points to `alpha_other`.
    """

    def __init__(self, value1, value2, alpha_other=0.3):
        #get_ipython().run_line_magic('matplotlib', 'qt')
        self.collection_of_point = []
        plt.figure()
        self.axis1 = value1
        self.axis2 = value2        
        ax_SelectFromCollection = plt.subplot(111)
        collection = ax_SelectFromCollection.scatter(self.axis1, self.axis2, s=50)
                
        self.canvas = ax_SelectFromCollection.figure.canvas
        self.collection = collection
        self.alpha_other = alpha_other

        self.xys = collection.get_offsets()
        self.Npts = len(self.xys)

        # Ensure that we have separate colors for each object
        self.fc = collection.get_facecolors()
        if len(self.fc) == 0:
            raise ValueError('Collection must have a facecolor')
        elif len(self.fc) == 1:
            self.fc = np.tile(self.fc, (self.Npts, 1))

        self.lasso = LassoSelector(ax_SelectFromCollection, onselect=self.onselect)
        self.ind = []
        
        #fig = plt.figure()
        #ax_SelectFromCollection = plt.subplot(111)
        #while len(self.collection_of_point) == 0:
        def accept(event):
            if event.key == "enter":
                print("Selected points:")
                print(self.xys[self.ind])
                self.collection_of_point.append(self.xys[self.ind])
                self.disconnect()
                ax_SelectFromCollection.set_title("")
                self.canvas.draw()
        self.canvas.mpl_connect("key_press_event", accept)
        ax_SelectFromCollection.set_title("Press enter to accept selected points.")
        
        #plt.show()
        
    def onselect(self, verts):
        path = Path(verts)
        self.ind = np.nonzero(path.contains_points(self.xys))[0]
        self.fc[:, -1] = self.alpha_other
        self.fc[self.ind, -1] = 1
        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()

    def disconnect(self):
        self.lasso.disconnect_events()
        self.fc[:, -1] = 1
        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()
        
        
'''
if __name__ == '__main__':
    import matplotlib.pyplot as plt

    # Fixing random state for reproducibility
    np.random.seed(19680801)

    data = np.random.rand(100, 2)

    subplot_kw = dict(xlim=(0, 1), ylim=(0, 1), autoscale_on=False)
    fig, ax = plt.subplots(subplot_kw=subplot_kw)

    pts = ax.scatter(data[:, 0], data[:, 1], s=80)
    selector = SelectFromCollection(ax, pts)

    def accept(event):
        if event.key == "enter":
            print("Selected points:")
            print(selector.xys[selector.ind])
            selector.disconnect()
            ax.set_title("")
            fig.canvas.draw()

    fig.canvas.mpl_connect("key_press_event", accept)
    ax.set_title("Press enter to accept selected points.")

    plt.show()
'''