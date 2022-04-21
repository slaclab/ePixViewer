
import os
import rogue.utilities
import rogue.utilities.fileio
import rogue.interfaces.stream
import pyrogue
import time
import ePixViewer.imgProcessing as imgPr
import ePixViewer.Cameras as cameras
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import pdb

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
except ImportError:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *



################################################################################
################################################################################
#   Matplotlib class
#
################################################################################
class MplCanvas(FigureCanvas):
    """This is a QWidget derived from FigureCanvasAgg."""

    def __init__(self, parent=None, width=5, height=4, dpi=100, MyTitle=""):

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.MyTitle = MyTitle
        self.axes.set_title(self.MyTitle)
        self.fig.cbar = None

    def compute_initial_figure(self):
        # if one wants to plot something at the begining of the application fill this function.
        #self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'b')
        self.axes.plot([], [], 'b')

    def update_plot(self):
        # Build a list of 4 random integers between 0 and 10 (both inclusive)
        l = [-1, -2, 10, 14]  # [random.randint(0, 10) for i in range(4)]
        # self.axes.cla()
        self.axes.plot([0, 1, 2, 3], l, 'r')
        self.draw()

    # the arguments are expected in the following sequence
    # (display enabled, line name, line color, data array)
    def update_plot(self, *args):
        argIndex = 0
        lineName = ""
#        if (self.fig.cbar!=None):
#            self.fig.cbar.remove()

        self.axes.cla()
        for arg in args:
            if (argIndex == 0):
                lineEnabled = arg
            if (argIndex == 1):
                lineName = arg
            if (argIndex == 2):
                lineColor = arg
            if (argIndex == 3):
                ##if (PRINT_VERBOSE): print(lineName)
                if (lineEnabled):
                    l = arg  # [random.randint(0, 10) for i in range(4)]
                    self.axes.plot(l, lineColor)
                argIndex = -1
            argIndex = argIndex + 1
        self.axes.set_title(self.MyTitle)
        self.draw()

    def update_plot_with_marker(self, *args):
        argIndex = 0
        lineName = ""
#        if (self.fig.cbar!=None):
#            self.fig.cbar.remove()

        self.axes.cla()
        for arg in args:
            if (argIndex == 0):
                lineEnabled = arg
            if (argIndex == 1):
                lineName = arg
            if (argIndex == 2):
                lineColor = arg
            if (argIndex == 3):
                ##if (PRINT_VERBOSE): print(lineName)
                if (lineEnabled):
                    l = np.bitwise_and(arg, np.uint16(0x3FFF))  # [random.randint(0, 10) for i in range(4)]
                    x_markers = np.where((np.bitwise_and(arg, np.uint16(0x4000)) >> 14) > 0)
                    self.axes.plot(l, lineColor)
                    self.axes.scatter(x_markers, l[x_markers], color='black')
                argIndex = -1
            argIndex = argIndex + 1
        self.axes.set_title(self.MyTitle)
        self.draw()

    def update_figure(self, image=None, contrast=None, autoScale=True):
        self.axes.cla()
        self.axes.autoscale = autoScale

        if (len(image) > 0):
            # self.axes.gray()
            if (contrast is not None):
                self.cax = self.axes.imshow(
                    image, interpolation='nearest', cmap='gray', vmin=np.minimum(
                        contrast[0], contrast[1]), vmax=np.maximum(
                        contrast[0], contrast[1]))
            else:
                self.cax = self.axes.imshow(image, interpolation='nearest', cmap='gray')

#            if (self.fig.cbar==None):
#                self.fig.cbar = self.fig.colorbar(self.cax)
#            else:
#                self.fig.cbar.remove()
#                self.fig.cbar = self.fig.colorbar(self.cax)
        self.draw()