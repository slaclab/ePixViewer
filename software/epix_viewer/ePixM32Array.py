import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from software.epix_viewer._dataReceiver import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

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