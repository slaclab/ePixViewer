import sys
import random
import numpy as np
import matplotlib
import signal
from matplotlib.patches import Rectangle
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class Matrix(FigureCanvas):
    def __init__(self, numOfCols=24, numOfRows=24, adcWidth=10, colormap=cm.gist_heat,
                       markEvery=1, name="Demo Matrix", **kwargs):

        # arguments
        self.numOfCols = numOfCols
        self.numOfRows = numOfRows
        self.adcWidth  = adcWidth
        self.colormap  = colormap
        self.markEvery = markEvery
        self.name      = name

        # internals
        self._adcMax = pow(2, self.adcWidth)
        self._norm = matplotlib.colors.Normalize(vmin=0, vmax=self._adcMax)
        self._m = cm.ScalarMappable(norm=self._norm, cmap=self.colormap)

        print(f"Initializing {self.name} online viewer. Please wait...")

        # init
        fig = plt.figure()
        self.pixelMatrix = [[0 for col in range(numOfCols)] for row in range(numOfRows)]
        self.axes = fig.add_subplot(111)
        fig.colorbar(cm.ScalarMappable(norm=self._norm, cmap=self.colormap), ax=self.axes)

        self._parametrizeMatrix()
        self._initializeMatrix()
        self._populateMatrix()

        super(Matrix, self).__init__(fig)

    def _clearMatrix(self):
        self.axes.cla()

    def _initializeMatrix(self):
        for row in range(self.numOfRows):
            for col in range(self.numOfCols):
                self.pixelMatrix[row][col] = 0

    def _populateMatrix(self):
        for row in range(self.numOfRows):
            for col in range(self.numOfCols):
                self.axes.add_patch(self._pixelAlloc(adc=self.pixelMatrix[row][col], col=col, row=row))

    def setPixels(self, cols, rows, adcVals):
        for pixel in range(len(cols)):
            self.axes.add_patch(self._pixelAlloc(adc=adcVals[pixel], col=cols[pixel], row=rows[pixel]))

    def resetPixels(self, cols, rows):
        for pixel in range(len(cols)):
            self.axes.add_patch(self._pixelAlloc(adc=0, col=cols[pixel], row=rows[pixel]))

    def _parametrizeMatrix(self):
        plt.title(self.name)
        plt.xlabel("Column")
        plt.ylabel("Row")
        self.axes.set_facecolor(self._m.to_rgba(0))
        self.axes.set_xlim([-2,self.numOfCols+1])
        self.axes.set_ylim([-2,self.numOfRows+1])
        plt.xticks(np.arange(0, self.numOfCols+1, self.markEvery))
        plt.yticks(np.arange(0, self.numOfRows+1, self.markEvery))
        plt.grid(True, color = "white", linewidth = "0.2", linestyle = "-")

    def _pixelAlloc(self, adc, col, row):
        pixel = matplotlib.patches.Rectangle((int(col), int(row)), 1, 1, color=self._m.to_rgba(adc))
        return pixel
