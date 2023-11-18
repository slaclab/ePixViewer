import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from ePixViewer import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

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