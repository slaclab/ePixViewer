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
    def __init__(self, length, width, **kwargs):
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
                for i in range(self.x - 10, self.x + 10):
                    if i >= 0 and i < self.length and self.x > 0 and self.x < self.length and self.y - 1 > 0 and self.y + 1 < self.width:
                        imgView[i][self.y] = crossHairVal
                        imgView[i][self.y-1] = crossHairVal
                        imgView[i][self.y+1] = crossHairVal
                for i in range(self.y - 10, self.y + 10):
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
            low = np.int32(array.min())
            high = np.int32(array.max())
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

class DataReceiverEpixHrSingle10kT(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(146, 192, **kwargs)
    
    def descramble(self, frame):
        # Function to descramble raw frames into numpy arrays
        img = frame.getNumpy(0, frame.getPayload()).view(np.uint16)
        quadrant0 = img[6:28038]
        adcImg = quadrant0.reshape(-1,6)
        for i in range(0,6):
            if len(adcImg[0:adcImg.shape[0],i]) == 4672:
                adcImg2 = adcImg[0:adcImg.shape[0],i].reshape(-1,32)
                adcImg2[1:,30] = adcImg2[0:adcImg2.shape[0]-1,30]
                adcImg2[1:,31] = adcImg2[0:adcImg2.shape[0]-1,31]
                if i == 0:
                    quadrant0sq = adcImg2
                else:
                    quadrant0sq = np.concatenate((quadrant0sq,adcImg2),1)
            else:
                self.DescError.set(self.DescError.get() + 1, write = True)
                raise Exception("*****Descramble error*****")
        return quadrant0sq

class DataReceiverEpix100a(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(708, 768, **kwargs)
    
    def descramble(self, frame):
        imgDescBA = self._descrambleEPix100aImageAsByteArray(frame)
        imgDesc = np.frombuffer(imgDescBA,dtype='int16')
        imgDesc = imgDesc.reshape(self.sensorHeight, self.sensorWidth)
        return imgDesc

class DataReceiverEpix100p(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(706, 768, **kwargs)
    
    def descramble(self, frame):
        for j in range(0,32):
            frame.pop(0)
        imgBot = frame[(0*1536):(1*1536)] 
        imgTop = frame[(1*1536):(2*1536)] 
        for j in range(2,706):
            if (j%2):
                imgBot.extend(frame[(j*1536):((j+1)*1536)])
            else:
                imgTop.extend(frame[(j*1536):((j+1)*1536)]) 
        imgDesc = imgBot
        imgDesc.extend(imgTop)
        imgDesc = np.array(imgDesc,dtype='uint8')
        return imgDesc

class DataReceiverTixel48x48(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(96, 96, **kwargs)
    
    def descramble(self, frame):
        if (len(frame)==4):
            quadrant0 = np.frombuffer(frame[0,4:],dtype='uint16')
            quadrant0sq = quadrant0.reshape(48,48)
            quadrant1 = np.frombuffer(frame[1,4:],dtype='uint16')
            quadrant1sq = quadrant1.reshape(48,48)
            quadrant2 = np.frombuffer(frame[2,4:],dtype='uint16')
            quadrant2sq = quadrant2.reshape(48,48)
            quadrant3 = np.frombuffer(frame[3,4:],dtype='uint16')
            quadrant3sq = quadrant3.reshape(48,48)
            imgTop = np.concatenate((quadrant0sq, quadrant1sq),1)
            imgBot = np.concatenate((quadrant2sq, quadrant3sq),1)
            imgDesc = np.concatenate((imgTop, imgBot),0)
        else:
            imgDesc = np.zeros((48*2,48*2), dtype='uint16')
        imgDesc = np.where((imgDesc & 0x1) == 1 , imgDesc, 0)
        return imgDesc

class DataReceiverCpix2(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(96, 96, **kwargs)
    
    def descramble(self, frame):
        if (len(frame)==4):
            quadrant0 = np.frombuffer(frame[0,4:],dtype='uint16')
            quadrant0sq = quadrant0.reshape(48,48)
            quadrant1 = np.frombuffer(frame[1,4:],dtype='uint16')
            quadrant1sq = quadrant1.reshape(48,48)
            quadrant2 = np.frombuffer(frame[2,4:],dtype='uint16')
            quadrant2sq = quadrant2.reshape(48,48)
            quadrant3 = np.frombuffer(frame[3,4:],dtype='uint16')
            quadrant3sq = quadrant3.reshape(48,48)
            imgTop = np.concatenate((quadrant0sq, quadrant1sq),1)
            imgBot = np.concatenate((quadrant2sq, quadrant3sq),1)
            imgDesc = np.concatenate((imgTop, imgBot),0)
        else:
            imgDesc = np.zeros((48*2,48*2), dtype='uint16')
        return imgDesc

class DataReceiverEpixM32Array(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(64, 64, **kwargs)
    
    def descramble(self, frame):
        if (len(frame)==2):
            quadrant0 = np.frombuffer(frame[0,4:],dtype='uint16')
            quadrant0sq = quadrant0.reshape(64,32)
            quadrant1 = np.frombuffer(frame[1,4:],dtype='uint16')
            quadrant1sq = quadrant1.reshape(64,32)
            imgTop = quadrant0sq
            imgBot = quadrant1sq
            imgDesc = np.concatenate((imgTop, imgBot),1)
        else:
            imgDesc = np.zeros((64,64), dtype='uint16')
        return imgDesc

class DataReceiverAdc32x32(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(32, 64, **kwargs)
    
    def descramble(self, frame):
        if (len(frame)==2):
            quadrant0 = np.frombuffer(frame[0,4:],dtype='uint16')
            quadrant0sq = quadrant0.reshape(32,32)
            quadrant1 = np.frombuffer(frame[1,4:],dtype='uint16')
            quadrant1sq = quadrant1.reshape(32,32)
            imgTop = quadrant0sq
            imgBot = quadrant1sq
            imgDesc = np.concatenate((imgTop, imgBot),1)
        else:
            imgDesc = np.zeros((32,64), dtype='uint16')
        return imgDesc

class DataReceiverCryo64xN(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(64, 64, **kwargs)
    
    def descramble(self, frame):
        if (type(frame != 'numpy.ndarray')):
            img = np.frombuffer(frame,dtype='uint16')
        samples = int((img.shape[0]-6)/64)
        if (samples) != ((img.shape[0]-6)/64):
            imgDesc = np.zeros((64,64), dtype='uint16')
            return imgDesc
        img2 = img[6:].reshape(samples,64)
        imgDesc = np.append(img2[:,0:64:2].transpose(), img2[:,1:64:2].transpose()).reshape(64,samples)
        return imgDesc

class DataReceiverEpixHrEpixM(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(64, 64, **kwargs)
    
    def descramble(self, frame):
        if (type(frame != 'numpy.ndarray')):
            img = np.frombuffer(frame,dtype='uint16')
        samples = int((img.shape[0]-6)/64)

        if (samples) != ((img.shape[0]-6)/64):
            imgDesc = np.zeros((64,64), dtype='uint16')
            return imgDesc
        img2 = img[6:].reshape(samples,64)
        imgDesc = np.append(img2[:,0:64:2].transpose(), img2[:,1:64:2].transpose()).reshape(64,samples)
        return np.transpose(imgDesc)

class DataReceiverEpixHrMv2(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(384, 192, **kwargs)
        self.framePixelRow = 192
        self.framePixelColumn = 384
        pixelsPerLanesRows = 48
        pixelsPerLanesColumns = 64
        evenRow = np.transpose([np.array([*range(0, pixelsPerLanesRows, 2)])])
        oddRow = np.transpose([np.array([*range(1, pixelsPerLanesRows, 2)])])
        duopleRow = np.concatenate((evenRow, oddRow), 0)

        evenColumn = np.array([*range(0, pixelsPerLanesColumns, 2)])
        oddColumn = np.array([*range(1, pixelsPerLanesColumns, 2)])
        duopleColumn = np.concatenate((evenColumn, oddColumn), 0)

        quadColumnMatrix = np.ones((pixelsPerLanesRows, 1)) * duopleColumn
        quadRowMatrix =  duopleRow * np.ones((1, pixelsPerLanesColumns))
        row_list= [*range(0, self.framePixelRow, pixelsPerLanesRows)]
        column_list = [*range(0, self.framePixelColumn, pixelsPerLanesColumns)]
        self.imgDescCol = np.zeros((self.framePixelRow, self.framePixelColumn), dtype=int)
        self.imgDescRow = np.zeros((self.framePixelRow, self.framePixelColumn), dtype=int)
        # 

        def laneMap(colMatrix, rowMatrix, currLaneColumn, currLaneRow):
            colMatRet = colMatrix + (currLaneColumn * pixelsPerLanesColumns)
            rowMatRet = rowMatrix + (currLaneRow * pixelsPerLanesRows)
            return colMatRet.astype(int), rowMatRet.astype(int)

        for i in column_list:
            column0 = i
            columnF = pixelsPerLanesColumns + i
            for j in row_list:
                row0 = j
                rowF = pixelsPerLanesRows + j
                self.imgDescCol[row0: rowF, column0: columnF], self.imgDescRow[row0: rowF, column0: columnF] = laneMap(quadColumnMatrix, quadRowMatrix, column_list.index(i), row_list.index(j))
    
    def descramble(self, frame):
        rawData = frame.getNumpy(0, frame.getPayload()).view(np.uint16)
        current_frame_temp = np.zeros((self.framePixelRow, self.framePixelColumn), dtype=int)
        """performs the EpixMv2 image descrambling """
        if (len(rawData)==73752):
             if (type(rawData != 'numpy.ndarray')):
                img = np.frombuffer(rawData,dtype='uint16')
             quadrant0 = np.frombuffer(rawData[24:73752],dtype='uint16')
             adcImg = quadrant0.reshape(-1,24)
             quadrant = [bytearray(),bytearray(),bytearray(),bytearray()]

             for i in range(4):
                quadrant[i] = np.concatenate((adcImg[:,0+i].reshape(-1,64),
                                              adcImg[:,4+i].reshape(-1,64),
                                              adcImg[:,8+i].reshape(-1,64),
                                              adcImg[:,12+i].reshape(-1,64),
                                              adcImg[:,16+i].reshape(-1,64), 
                                              adcImg[:,20+i].reshape(-1,64)),1)

             imgDesc = np.concatenate((quadrant[0], quadrant[1]),0)
             imgDesc = np.concatenate((imgDesc, quadrant[2]),0)
             imgDesc = np.concatenate((imgDesc, quadrant[3]),0)
        else:
            print("descramble error")
            print('rawData length {}'.format(len(rawData)))
            imgDesc = np.zeros((192,384), dtype='uint16')

        
        current_frame_temp[self.imgDescRow, self.imgDescCol] = imgDesc
        # returns final image
        return np.bitwise_and(current_frame_temp, self.PixelBitMask.get())


class DataReceiverEpixUHR(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(168, 192, **kwargs)

        self.framePixelRow = 168
        self.framePixelColumn = 192
        self.counter = 0
        self.lane_map = self.lane_map()

    def read_uint12(self,data_chunk):
        #https://stackoverflow.com/questions/44735756/python-reading-12-bit-binary-files
        fst_uint8, mid_uint8, lst_uint8 = np.reshape(data_chunk, (data_chunk.shape[0] // 3, 3)).astype(np.uint16).T
        fst_uint12 = (fst_uint8 << 4) + (mid_uint8 >> 4)
        snd_uint12 = ((mid_uint8 % 16) << 8) + lst_uint8
        return np.reshape(np.concatenate((fst_uint12[:, None], snd_uint12[:, None]), axis=1), 2 * fst_uint12.shape[0])

    def lane_map(self):
        column_map = []
        cluster_map = np.empty(72)
        #create the sp map
        sp_map = np.array([0,3,6,1,4,7,2,5,8])

        #create the cluster map
        for index in range (8):
            cluster_map[sp_map+(index*9)] = range(index,65+index,8)

        #cast cluster_map to int
        cluster_map=cluster_map.astype(int)

        #split the cluster in the 2 sp columns
        cluster_map = np.concatenate([np.reshape(cluster_map [0:len(cluster_map)//2], (12,3)),np.reshape(cluster_map [len(cluster_map)//2:], (12,3))],axis =1 )

        #re-linearize the cluster_map
        cluster_map = np.reshape(cluster_map, 72)

        #create the column map
        for cluster_n in range (14):
            column_map = np.append(column_map , (14*cluster_map) + cluster_n)

        #cast column_map to int
        column_map=column_map.astype(int)

        #create the cluster_columns_map
        lane_map = np.concatenate([np.reshape(column_map*2,(168,6)),np.reshape((column_map*2)+1,(168,6))],axis =1 )

        #re-linearize the cluster_columns_map
        lane_map = np.reshape(lane_map, 2016)
        
        return lane_map

    def frame_reorder(self,input_frame,lane_map):
        frame= np.empty([168,1])
        frame.fill(np.nan)

        for lane_n in range (16):
            #taking one lane at the time
            frame_tmp = input_frame[lane_n,1:]
            #using the map
            lane_tmp = frame_tmp[lane_map]
            #reshape
            lane_tmp = np.reshape(lane_tmp, (168,12))
            frame = np.concatenate([frame,lane_tmp],axis =1)

        return frame[np.logical_not(np.isnan(frame))]    

    
    def descramble(self, frame):
        # print('Debug: Frame counter {}'.format(self.counter))
        # self.counter = self.counter + 1
        
        #create the frames
        current_frame_temp = np.zeros((self.framePixelRow, self.framePixelColumn), dtype=int)
        rawData_12bit = np.empty((16,2017), dtype=int)

        #get the frames from the stream
        rawData_8bit = frame.getNumpy(0, frame.getPayload()).view(np.uint8)
        rawData_8bit = np.reshape(rawData_8bit[16:48424],(2017,24))
        rawData_8bit = np.flip(rawData_8bit,1).T

        #parse the 8bit chunks into the 12bit
        for j in range (2017):
            rawData_12bit[:,j] = self.read_uint12(rawData_8bit[:,j])

        #use the map to filter the pixels
        frame = self.frame_reorder(rawData_12bit, self.lane_map)
        frame = np.reshape(frame, (168,192))
        frame = frame.astype(int)

        current_frame_temp = np.flip(frame,0)

        return np.bitwise_and(current_frame_temp, self.PixelBitMask.get())


class DataReceiverEpixUHRMHzMode(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(56, 64, **kwargs)

        self.framePixelRow = 56
        self.framePixelColumn = 64
        self.counter = 0
        self.lane_map_MHz = self.lane_map_MHz()

    def read_uint12(self,data_chunk):
        #https://stackoverflow.com/questions/44735756/python-reading-12-bit-binary-files
        fst_uint8, mid_uint8, lst_uint8 = np.reshape(data_chunk, (data_chunk.shape[0] // 3, 3)).astype(np.uint16).T
        fst_uint12 = (fst_uint8 << 4) + (mid_uint8 >> 4)
        snd_uint12 = ((mid_uint8 % 16) << 8) + lst_uint8
        return np.reshape(np.concatenate((fst_uint12[:, None], snd_uint12[:, None]), axis=1), 2 * fst_uint12.shape[0])

    def lane_map_MHz(self):
        column_map = []
        cluster_map = np.empty(8)
        
        #create the cluster map
        for index in range (8):
            cluster_map[index] = index
        #cast cluster_map to int
        cluster_map=cluster_map.astype(int)
        
        #split the cluster in the 2 sp columns
        cluster_map = np.concatenate([np.reshape(cluster_map [0:len(cluster_map)//2], (4,1)),np.reshape(cluster_map [len(cluster_map)//2:], (4,1))],axis =1 )
        
        #re-linearize the cluster_map
        cluster_map = np.reshape(cluster_map, 8)
        
        #create the column map
        for cluster_n in range (14):
            column_map = np.append(column_map , (14*cluster_map) + cluster_n)
        
        #cast column_map to int
        column_map=column_map.astype(int)
        
        #create the cluster_columns_map
        lane_map = np.concatenate([np.reshape(column_map*2,(56,2)),np.reshape((column_map*2)+1,(56,2))],axis =1 )
        
        #re-linearize the cluster_columns_map
        lane_map = np.reshape(lane_map, 224)
        
        return lane_map

    def frame_reorder_MHz(self,input_frame,lane_map):
        frame= np.empty([56,1])
        frame.fill(np.nan)
        for lane_n in range (16):
            #taking one lane at the time
            frame_tmp = input_frame[lane_n,1:]
            #using the map
            lane_tmp = frame_tmp[lane_map]
            #reshape
            lane_tmp = np.reshape(lane_tmp, (56,4))
            frame = np.concatenate([frame,lane_tmp],axis =1)
        return frame[np.logical_not(np.isnan(frame))] 

    
    def descramble(self, frame):
        #create the frames
        current_frame_temp = np.zeros((self.framePixelRow, self.framePixelColumn), dtype=int)
        rawData_12bit = np.empty((16,225), dtype=int)

        #get the frames from the stream
        rawData_8bit = frame.getNumpy(0, frame.getPayload()).view(np.uint8)
        rawData_8bit = np.reshape(rawData_8bit[16:5416],(225,24))
        rawData_8bit = np.flip(rawData_8bit,1).T

        #parse the 8bit chunks into the 12bit
        for j in range (225):
            rawData_12bit[:,j] = self.read_uint12(rawData_8bit[:,j])

        #use the map to filter the pixels
        frame = self.frame_reorder_MHz(rawData_12bit, self.lane_map_MHz)
        frame = np.reshape(frame, (56,64))
        frame = frame.astype(int)

        current_frame_temp = np.flip(frame,0)

        return np.bitwise_and(current_frame_temp, self.PixelBitMask.get())

class DataReceiverEnvMonitoring(pr.DataReceiver):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add(pr.LocalVariable(
            name = "StrongBackTemp",
            value = 0,
            description = "Strong back temperature"
        ))
        self.add(pr.LocalVariable(
            name = "AmbientTemp",
            value = 0,
            description = "Ambient temperature"
        ))
        self.add(pr.LocalVariable(
            name = "RelativeHum",
            value = 0,
            description = "Relative humidity"
        ))
        self.add(pr.LocalVariable(
            name = "ASICACurrent",
            value = 0,
            description = "ASIC (A.) current (mA)"
        ))
        self.add(pr.LocalVariable(
            name = "ASICDCurrent",
            value = 0,
            description = "ASIC (D.) current (mA)"
        ))
        self.add(pr.LocalVariable(
            name = "GuardRingCurrent",
            value = 0,
            description = "Guard ring current (uA)"
        ))
        self.add(pr.LocalVariable(
            name = "VccA",
            value = 0,
            description = "Vcc_a (mV)"
        ))
        self.add(pr.LocalVariable(
            name = "VccD",
            value = 0,
            description = "Vcc_d (mV)"
        ))

    def process(self, frame):
        with self.root.updateGroup():
            rawData = bytearray(frame.getPayload())
            frame.read(rawData, 0)
            envData = np.zeros((8,1), dtype='int32')
            for j in range(0,32):
                rawData.pop(0)
            for j in range(0,8):
                envData[j] = int.from_bytes(rawData[j*4:(j+1)*4], byteorder='little')
            envData[0] = envData[0] / 100
            envData[1] = envData[1] / 100
            envData[2] = envData[2] / 100
            self.StrongBackTemp.set(int(envData[0]), write = True)
            self.AmbientTemp.set(int(envData[1]), write = True)
            self.RelativeHum.set(int(envData[2]), write = True)
            self.ASICACurrent.set(int(envData[3]), write = True)
            self.ASICDCurrent.set(int(envData[4]), write = True)
            self.GuardRingCurrent.set(int(envData[5]), write = True)
            self.VccA.set(int(envData[6]), write = True)
            self.VccD.set(int(envData[7]), write = True)
            self.Updated.set(True, write = True)

class DataReceiverPseudoScope(pr.DataReceiver):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add(pr.LocalVariable(
            name = "ChannelAData",
            value = [],
            description = "Vector data for channel A"
        ))
        self.add(pr.LocalVariable(
            name = "ChannelBData",
            value = [],
            description = "Vector data for channel B"
        ))
        self.add(pr.LocalVariable(
            name = "ShowChannelAData",
            value = False,
            description = "Whether to show channel A data"
        ))
        self.add(pr.LocalVariable(
            name = "ShowChannelBData",
            value = False,
            description = "Whether to show chanel B data"
        ))
        self.add(pr.LocalVariable(
            name = "FFTXA",
            value = [],
            description = "Vector data for fourier transform x of channel A"
        ))
        self.add(pr.LocalVariable(
            name = "FFTYA",
            value = [],
            description = "Vector data for fourier transform y of channel A"
        ))
        self.add(pr.LocalVariable(
            name = "FFTXB",
            value = [],
            description = "Vector data for fourier transform x of channel B"
        ))
        self.add(pr.LocalVariable(
            name = "FFTYB",
            value = [],
            description = "Vector data for fourier transform y of channel B"
        ))

    def process(self, frame):
        rawData = bytearray(frame.getPayload())
        frame.read(rawData,0)
        data  = np.frombuffer(rawData,dtype='uint16')
        data  = data[16:-14]
        oscWords = len(data)
        chAdata = -0.0 + data[0:int(oscWords/2)] * (2.0/2**14)
        chBdata = -0.0 + data[int(oscWords/2): oscWords] * (2.0/2**14)
        chAdata = (2.0-0.053) + chAdata * (-1.04)
        chBdata = (2.0-0.053) + chBdata * (-1.04)
        N = len(chAdata)
        TA = 4E-8
        freqs = []
        yfA = []
        yfB = []
        zeros = np.zeros(1)
        if N > 0:
            freqs = np.fft.rfftfreq(N, TA)
            yfA = np.abs(np.fft.rfft(chAdata))
            yfB = np.abs(np.fft.rfft(chBdata))
            with self.root.updateGroup():
                if self.ShowChannelAData.get():
                    self.ChannelAData.set(chAdata, write = True)
                    self.FFTXA.set(freqs[2:], write = True)
                    self.FFTYA.set(yfA[2:], write = True)
                else:
                    self.ChannelAData.set(zeros, write = True)
                    self.FFTXA.set(zeros, write = True)
                    self.FFTYA.set(zeros, write = True)
                if self.ShowChannelBData.get():
                    self.ChannelBData.set(chBdata, write = True)
                    self.FFTXB.set(freqs[2:], write = True)
                    self.FFTYB.set(yfB[2:], write = True)
                else:
                    self.ChannelBData.set(zeros, write = True)
                    self.FFTXB.set(zeros, write = True)
                    self.FFTYB.set(zeros, write = True)
                self.Updated.set(True, write = True)