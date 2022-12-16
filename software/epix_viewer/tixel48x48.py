import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from software.epix_viewer._dataReceiver import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

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