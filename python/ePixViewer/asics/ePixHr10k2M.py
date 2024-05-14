import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from ePixViewer import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy


class DataReceiverEpixHr10k2M(DataReceiverBase):
    def __init__(self, **kwargs):
        self.ASIC_NUM    = 4
        self.ASIC_WIDTH = 192
        self.ASIC_HEIGHT  = 144
        self.header = 24
        super().__init__(self.ASIC_WIDTH * self.ASIC_NUM, self.ASIC_HEIGHT, **kwargs)

    def descramble(self, frame):
        # Function to descramble raw frames into numpy arrays
        payload = frame.getNumpy(0, frame.getPayload()).view(np.uint16)
        #array1_hex = np.array([hex(y) for y in payload])
        #print("{} got payload of size {} uint16 {}".format(self.name, payload.shape[0], array1_hex[tailIndex:]))
        #print("{} got payload of size {} (uint16)".format(self.name, 
        #                                payload.shape[0]))
        if (len(payload)==110640):
            tailIndex = self.ASIC_WIDTH * self.ASIC_NUM * self.ASIC_HEIGHT + self.header
            autoFillMask = payload[tailIndex+1] << 16 | payload[tailIndex] 
            fixedMask    = payload[tailIndex+3] << 16 | payload[tailIndex+2] 
            print("MODULE:{} F#:{} Mask:{}".format(payload[4] & 0x7, payload[3]<< 16 | payload[2], hex(autoFillMask | fixedMask) ))            

            img = payload[self.header:self.ASIC_HEIGHT * self.ASIC_WIDTH * self.ASIC_NUM + self.header]
    
            quadrant0 = img
            #descramble image
            #get data for each bank
            adcImg = quadrant0.reshape(-1,24)
            for i in range(0,24):
                #reshape data into 2D array per bank
                adcImg2 = adcImg[0:adcImg.shape[0],i].reshape(-1,32)
                #apply row-shift patch
                adcImg2[1:,30] = adcImg2[0:adcImg2.shape[0]-1,30]
                adcImg2[1:,31] = adcImg2[0:adcImg2.shape[0]-1,31]
                #concatenate bank data into a single image per asic
                if i == 0:
                    quadrant0sq = adcImg2
                else:
                    quadrant0sq = np.concatenate((quadrant0sq,adcImg2),1)
            imgDesc = quadrant0sq
        else:
            print("descramble error")
            imgDesc = np.zeros((self.ASIC_HEIGHT,self.ASIC_WIDTH * self.ASIC_NUM), dtype='uint16')
            
        # returns final image
        return imgDesc