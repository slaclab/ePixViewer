import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


import pyrogue as pr
import numpy as np


import collections
import time
from copy import copy
from ePixViewer import DataReceiverBase

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
