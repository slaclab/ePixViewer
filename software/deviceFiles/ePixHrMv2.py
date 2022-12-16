import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from epixViewer.software._dataReceiver import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy


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