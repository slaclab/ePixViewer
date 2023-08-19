import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from ePixViewer.software._dataReceiver import DataReceiverBase
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
        numOfBanks = 24
        bankHeight = pixelsPerLanesRows
        bankWidth = pixelsPerLanesColumns

        imageSize = self.framePixelColumn * self.framePixelRow

        self.lookupTableCol = np.zeros(imageSize, dtype=int)
        self.lookupTableRow = np.zeros(imageSize, dtype=int)

        # based on descrambling pattern described here figure out the location of the pixel based on its index in raw data
        # https://confluence.slac.stanford.edu/download/attachments/392826236/image-2023-8-9_16-6-42.png?version=1&modificationDate=1691622403000&api=v2
        descarambledImg = np.zeros((numOfBanks, bankHeight,bankWidth), dtype=int)
        for row in range(bankHeight) :
            for col in range (bankWidth) : 
                for bank in range (numOfBanks) :
                    #                                  (even cols w/ offset       +  row offset       + increment every two cols)   * fill one pixel / bank + bank increment
                    descarambledImg[bank, row, col] = (((col+1) % 2) * 1536       +   32 * row        + int(col / 2))               * numOfBanks            + bank
        

        # reorder banks from
        # 18    19    20    21    22    23
        # 12    13    14    15    16    17
        #  6     7     8     9    10    11
        #  0     1     2     3     4     5
        #
        #                To
        #  3     7    11    15    19    23         <= Quadrant[3] 48 x 64 x 6
        #  2     6    10    14    18    22         <= Quadrant[2] 48 x 64 x 6
        #  1     5     9    13    17    21         <= Quadrant[1] 48 x 64 x 6
        #  0     4     8    12    16    20         <= Quadrant[0] 48 x 64 x 6

        quadrant = [bytearray(),bytearray(),bytearray(),bytearray()]
        for i in range(4):
            quadrant[i] = np.concatenate((descarambledImg[0+i],
                                        descarambledImg[4+i],
                                        descarambledImg[8+i],
                                        descarambledImg[12+i],
                                        descarambledImg[16+i],
                                        descarambledImg[20+i]),1)
            
        descarambledImg = np.concatenate((quadrant[0], quadrant[1]),0)
        descarambledImg = np.concatenate((descarambledImg, quadrant[2]),0)
        descarambledImg = np.concatenate((descarambledImg, quadrant[3]),0)  

        # Work around ASIC/firmware bug: first and last row of each bank are exchanged
        # Create lookup table where each row points to itself
        hardwareBugWorkAroundRowLUT = np.zeros((192))
        for index in range (self.framePixelRow) :
            hardwareBugWorkAroundRowLUT[index] = index
        # Then we need to exchange row 0 with 47, 48 with 95, 96 with 143, 144 with 191
        hardwareBugWorkAroundRowLUT[0] = 47
        hardwareBugWorkAroundRowLUT[47] = 0
        hardwareBugWorkAroundRowLUT[48] = 95
        hardwareBugWorkAroundRowLUT[95] = 48
        hardwareBugWorkAroundRowLUT[96] = 143
        hardwareBugWorkAroundRowLUT[143] = 96
        hardwareBugWorkAroundRowLUT[144] = 191
        hardwareBugWorkAroundRowLUT[191] = 144


        # reverse pixel original index to new row and column to generate lookup tables
        for row in range (self.framePixelRow) :
            for col in range (self.framePixelColumn):  
                index = descarambledImg[row,col]
                self.lookupTableRow[index] = hardwareBugWorkAroundRowLUT[row]
                self.lookupTableCol[index] = col

        # reshape column and row lookup table
        self.lookupTableCol = np.reshape(self.lookupTableCol, (self.framePixelRow, self.framePixelColumn))
        self.lookupTableRow = np.reshape(self.lookupTableRow, (self.framePixelRow, self.framePixelColumn))

    def descramble(self, frame):
        rawData = frame.getNumpy(0, frame.getPayload()).view(np.uint16)
        current_frame_temp = np.zeros((self.framePixelRow, self.framePixelColumn), dtype=int)
        """performs the EpixMv2 image descrambling (simply applying lookup table) """
        if (len(rawData)==73752):
            imgDesc = np.frombuffer(rawData[24:73752],dtype='uint16').reshape(192, 384)
        else:
            print("descramble error")
            print('rawData length {}'.format(len(rawData)))
            imgDesc = np.zeros((192,384), dtype='uint16')

        
        current_frame_temp[self.lookupTableRow, self.lookupTableCol] = imgDesc
        # returns final image
        return np.bitwise_and(current_frame_temp, self.PixelBitMask.get())