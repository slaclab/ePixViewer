import random
import sys
import numpy as np
import matplotlib.cm as cm

from PyQt5 import QtCore, QtWidgets

from sparsifiedViewer._Matrix import Matrix

class MainPixelViewer(QtWidgets.QMainWindow):
    def __init__(self, name="Demo Matrix", demo=False, numOfCols=24,
                 numOfRows=24, adcWidth=10, markEvery=1,
                 colormap=cm.gist_heat, **kwargs):

        super(MainPixelViewer, self).__init__(**kwargs)

        # params
        self.name      = name
        self.numOfCols = numOfCols
        self.numOfRows = numOfRows
        self.adcWidth  = adcWidth
        self.markEvery = markEvery
        self.demo      = demo
        self.colormap  = colormap

        # internal
        self._colHits = []
        self._rowHits = []
        self._adcVals = []
        self._numOfRandomHits = 10

        self._adcMax = pow(2, self.adcWidth)

        self.canvas = Matrix(numOfCols=self.numOfCols, numOfRows=self.numOfRows,
                             adcWidth=self.adcWidth, colormap=self.colormap,
                             markEvery=self.markEvery, name=self.name)
        self.setCentralWidget(self.canvas)
        self.show()

        if self.demo:
            print("Running in demo (random hits) mode...")
            # Setup a timer to trigger the redraw by calling randomHits.
            self.timer = QtCore.QTimer()
            self.timer.setInterval(100)
            self.timer.timeout.connect(self._randomHits)
            self.timer.start()

    # interface function
    def handleHits(self, colArray, rowArray, adcArray):
        self._resetAll()
        self._setArrays(colArray=colArray, rowArray=rowArray, adcArray=adcArray)
        self._setMatrix()
        self.canvas.draw()

    def _randomHits(self):
        self._resetAll()
        hits = np.random.randint(0,self._numOfRandomHits)
        _randColArray = []
        _randRowArray = []
        _randAdcArray = []

        for col in range(hits):
            _randColArray.append(np.random.randint(0,self.numOfCols-1))
            _randRowArray.append(np.random.randint(0,self.numOfRows-1))
            _randAdcArray.append(np.random.randint(0,self._adcMax))

        self._setArrays(colArray=_randColArray, rowArray=_randRowArray, adcArray=_randAdcArray)

        self._setMatrix()
        self.canvas.draw()

    def _setArrays(self, colArray, rowArray, adcArray):
        self._colHits = colArray
        self._rowHits = rowArray
        self._adcVals = adcArray

    def _clearArrays(self):
        self._colHits.clear()
        self._rowHits.clear()
        self._adcVals.clear()

    def _setMatrix(self):
        self.canvas.setPixels(cols=self._colHits, rows=self._rowHits, adcVals=self._adcVals)

    def _resetMatrix(self):
        self.canvas.resetPixels(cols=self._colHits, rows=self._rowHits)

    def _resetAll(self):
        self._resetMatrix()
        self._clearArrays()
