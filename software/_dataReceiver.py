#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Title      : Updated data receivers for PyDM live viewer
#-----------------------------------------------------------------------------
# File       : dataReceivers.py
# Author     : Jaeyoung (Daniel) Lee
# Created    : 2022-06-22
# Last update: 2022-08-26
#-----------------------------------------------------------------------------
# Description:
# Updated data receivers for processing image, environment, and pseudoscope
# data for the new PyDM live viewer
#-----------------------------------------------------------------------------
# This file is part of the ePix rogue. It is subject to
# the license terms in the LICENSE.txt file found in the top-level directory
# of this distribution and at:
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the ePix rogue, including this file, may be
# copied, modified, propagated, or distributed except according to the terms
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------
# Catch the future warning bitwise and with bitmask
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

class DataReceiverBase(pr.DataReceiver):
    def __init__(self, length, width, numClusters, **kwargs):
        super().__init__(**kwargs)
        self.length = length
        self.width = width
        self.Queue = collections.deque(maxlen = 50000)
        # Queue for histogram
        self.ImageQueue = collections.deque(maxlen = 30)
        # Queue for automatic contrast
        self.NoiseQueue = collections.deque(maxlen = 1000)
        # Queue for noise color map
        self.TimePlotQueue = collections.deque(maxlen = 1000)
        # Queue for pixel timeplot y
        self.TimePlotIndexQueue = collections.deque(maxlen = 1000)
        # Queue for pixel timeplot x
        self.nextIndex = 0
        # Next index for timeplot
        self.maxlen = 1000
        # Maxlen for timeplot
        self.numDarkCol = 0
        self.DarkImg = []
        self.oldApplyDark = False
        self.x = 0
        self.y = 0
        self.start = time.time()
        self.colormap = []
        #self.pixelBitMask = 0x0000 
        self.add(pr.LocalVariable(
            name = "PixelBitMask",
            disp = '0x{:04x}',
            description = "Masking off pixel bits",
            value = 0x7fff,
        ))
        
        self.add(pr.LocalVariable(
            name = "PixelData",
            value = [],
            description = "Vector pixel value for pixel data slot"
        ))
        self.add(pr.LocalVariable(
            name = "IndexData",
            value = [],
            description = "Vector index value for pixel data slot"
        ))
        self.add(pr.LocalVariable(
            name = "PixelDataScalar",
            value = 0,
            description = "Scalar pixel value for pixel data slot"
        ))
        self.add(pr.LocalVariable(
            name = "X",
            value = 0,
            description = "Cursor coordinate"
        ))
        self.add(pr.LocalVariable(
            name = "Y",
            value = 0,
            description = "Cursor coordinate"
        ))
        self.add(pr.LocalVariable(
            name = "NumDarkReq",
            value = 0,
            description = "Number of dark requested"
        ))
        self.add(pr.LocalVariable(
            name = "NumDarkCol",
            value = 0,
            description = "Number of dark collected"
        ))
        self.add(pr.LocalVariable(
            name = "ApplyDark",
            value = False,
            description = "Whether to apply dark or not"
        ))
        self.add(pr.LocalVariable(
            name = "DarkReady",
            value = False,
            description = "Whether dark is ready or not"
        ))
        self.add(pr.LocalVariable(
            name = "CollectDark",
            value = False,
            description = "Whether user wants to collect dark or not"
        ))
        self.add(pr.LocalVariable(
            name = "AvgDark",
            value = np.empty([1,1]),
            description = "Average of darks collected,"
        ))
        self.add(pr.LocalVariable(
            name = "ShowDark",
            value = False,
            description = "Whether to show dark or not"
        ))
        self.add(pr.LocalVariable(
            name = "MaxPixVal",
            value = 12000,
            description = "Maximum contrast"
        ))
        self.add(pr.LocalVariable(
            name = "MinPixVal",
            value = 10000,
            description = "Minimum contrast"
        ))
        self.add(pr.LocalVariable(
            name = "Histogram",
            value = [],
            description = "Vector data for histogram's y-axis"
        ))
        self.add(pr.LocalVariable(
            name = "Bins",
            value = [],
            description = "Vector data for histogram's bins"
        ))
        self.add(pr.LocalVariable(
            name = "PlotHorizontal",
            value = False,
            description = "Whether to plot horizontal rows or not"
        ))
        self.add(pr.LocalVariable(
            name = "PlotVertical",
            value = False,
            description = "Whether to plot vertical columns or not"
        ))
        self.add(pr.LocalVariable(
            name = "Horizontal",
            value = [],
            description = "Vector data for horizontal row pixel values"
        ))
        self.add(pr.LocalVariable(
            name = "Vertical",
            value = [],
            description = "Vector data for vertical column pixel values"
        ))
        self.add(pr.LocalVariable(
            name = "AutoCon",
            value = False,
            description = "Whether to have auto contrast or not"
        ))
        self.add(pr.LocalVariable(
            name = "DescError",
            value = 0,
            mode = "RO",
            description = "Count of descramble errors to be displayed"
        ))
        self.add(pr.LocalVariable(
            name = "NoiseColormap",
            value = False,
            description = "Whether to show noise colormap or not"
        ))
        self.add(pr.LocalVariable(
            name = "NoiseColormapReady",
            value = False,
            description = "Whether NoiseColormap is ready or not"
        ))
        self.add(pr.LocalVariable(
            name = "TimePlotMaxLen",
            value = 1000,
            description = "Max frame length for timeplot"
        ))
        self.add(pr.LocalVariable(
            name = "ResetTimePlot",
            value = False,
            description = "Whether to reset timeplot or not"
        ))
        self.add(pr.LocalVariable(
            name = "GainMSB",
            value = True,
            description = "If true shift the LSB as MSB"
        ))
        maxlen = 1000
        index = -maxlen
        for i in range(maxlen):
            self.TimePlotQueue.append(0)
            self.TimePlotIndexQueue.append(index + i)
    
    def resetTimePlot(self):
        maxlen = self.TimePlotMaxLen.get()
        index = -maxlen
        for i in range(maxlen):
            self.TimePlotQueue.append(0)
            self.TimePlotIndexQueue.append(index + i)
        self.nextIndex = 0
        self.Queue = []
        self.NoiseQueue = []
    
    def resetTimePlotMaxLen(self):
        self.TimePlotQueue = collections.deque(self.TimePlotQueue.copy(), maxlen = self.TimePlotMaxLen.get())
        self.TimePlotIndexQueue = collections.deque(self.TimePlotIndexQueue.copy(), maxlen = self.TimePlotMaxLen.get())

    def descramble(self, frame):
        return frame

    def process(self, frame):
        if time.time() - self.start > 1 and self.NoiseQueue:
            self.start = time.time()
            self.colormap = np.std(np.array(self.NoiseQueue), 0)
        with self.root.updateGroup():
            if len(self.colormap):
                self.NoiseColormapReady.set(True, write = True)
            imgDesc = self.descramble(frame)
            imgView = copy(imgDesc)
            imgRaw = copy(imgDesc)

            if self.ResetTimePlot.get():
                self.resetTimePlot()
                self.ResetTimePlot.set(False, write = True)

            if self.TimePlotMaxLen.get() is not self.maxlen:
                self.resetTimePlotMaxLen()
                self.maxlen = self.TimePlotMaxLen.get()

            # Dark collecting process:
            if self.CollectDark.get():
                if self.DarkReady.get():
                    self.AvgDark.set(np.empty([1,1]), write = True)
                    self.DarkImg = []
                    self.DarkReady.set(False, write = True)
                    self.numDarkCol = 0
                if self.NumDarkReq.get() is not self.numDarkCol:
                    self.DarkImg.append(imgRaw)
                    self.numDarkCol += 1
                else:
                    self.AvgDark.set(np.mean(np.array(np.intc(self.DarkImg)),axis=0), write = True)
                    self.DarkReady.set(True, write = True)
                    print("\n*****Dark ready*****\n")
                    self.CollectDark.set(False, write = True)
            if self.ApplyDark.get() is not self.oldApplyDark:
                self.Queue = []
                self.ImageQueue = []
                self.NoiseQueue = []
                self.oldApplyDark = self.ApplyDark.get()
            if self.ApplyDark.get():
                imgView = np.intc(imgView) - self.AvgDark.get()
                imgRaw = np.intc(imgRaw) - self.AvgDark.get()
            if self.ShowDark.get():
                self.Data.set(self.AvgDark.get(), write = True)
            else:
                if int(self.X.get()) is not self.y or int(self.Y.get()) is not self.x:
                    self.Queue = []

                # Switch x and y due to PyDMImageViewer row-coloumn switching:
                self.y = int(self.X.get())
                self.x = int(self.Y.get())

                if self.NoiseColormap.get():
                    imgView = copy(self.colormap)
                # Showing crosshair:
                crossHairVal = -sys.maxsize - 1
                for i in range(self.x - 4, self.x + 5):
                    if i >= 0 and i < self.length and self.x > 0 and self.x < self.length and self.y - 1 > 0 and self.y + 1 < self.width:
                        imgView[i][self.y] = crossHairVal
                        imgView[i][self.y-1] = crossHairVal
                        imgView[i][self.y+1] = crossHairVal
                for i in range(self.y - 4, self.y + 5):
                    if i >= 0 and i < self.width and self.y > 0 and self.y < self.width and self.x - 1 > 0 and self.x + 1 < self.length:
                        imgView[self.x][i] = crossHairVal
                        imgView[self.x-1][i] = crossHairVal
                        imgView[self.x+1][i] = crossHairVal
                self.Data.set(imgView, write = True)
            
            self.NoiseQueue.append(imgRaw)
            # Setting data for timeplot and horizontal/vertical plots:
            if self.x >= 0 and self.x < self.length and self.y >= 0 and self.y < self.width:
                # Timeplot processing
                self.PixelDataScalar.set(int(imgRaw[self.x][self.y]), write = True)
                self.TimePlotQueue.append(int(imgRaw[self.x][self.y]))
                self.TimePlotIndexQueue.append(self.nextIndex)
                self.nextIndex += 1
                self.PixelData.set(np.array(self.TimePlotQueue), write = True)
                self.IndexData.set(np.array(self.TimePlotIndexQueue), write = True)

                temp = imgRaw
                if self.NoiseColormap.get():
                    temp = self.colormap
                if self.PlotHorizontal.get():
                    self.Horizontal.set(temp[self.x], write = True)
                else:
                    self.Horizontal.set(np.zeros(1), write = True)
                if self.PlotVertical.get():
                    self.Vertical.set(temp[:,self.y], write = True)
                else:
                    self.Vertical.set(np.zeros(1), write = True)
                self.Queue.append(imgRaw[self.x][self.y])
                self.ImageQueue.append(imgRaw)

            

            # Histogram generation & automatic contrast processing:
            array = np.array(self.Queue)
            imgArray = np.array(self.ImageQueue)
            mean = imgArray.mean()
            rms = imgArray.std()
            low = np.int32(np.min(array,initial=0))
            high = np.int32(np.max(array,initial=0))
            binsA = np.arange(low - 10, high + 10, 1)
            histogram, bins = np.histogram(array, bins=binsA)
            bins = np.delete(bins, len(bins) - 1, 0)
            self.Histogram.set(histogram, write = True)
            self.Bins.set(bins, write = True)
            if self.AutoCon.get():
                multiplier = 2
                if self.ApplyDark.get():
                    multiplier = 10
                if self.ShowDark.get():
                    self.MaxPixVal.set(int(self.AvgDark.get().mean() + multiplier * self.AvgDark.get().std()), write = True)
                    self.MinPixVal.set(int(self.AvgDark.get().mean() - multiplier * self.AvgDark.get().std()), write = True)
                else:
                    self.MaxPixVal.set(int(mean + multiplier * rms), write = True)
                    self.MinPixVal.set(int(mean - multiplier * rms), write = True)
                if self.NoiseColormap.get():
                    self.MaxPixVal.set(50, write = True)
                    self.MinPixVal.set(0, write = True)
            self.Updated.set(True, write = True)