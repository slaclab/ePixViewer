import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from ePixViewer import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

class DataReceiverEpixHrDuo10kT(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(384, 144, **kwargs)
    
    def descramble(self, frame):

        img = frame.getNumpy(0, frame.getPayload()).view(np.uint16)
        quadrant0 = img[6:144*384+6]
        quadrant0sq = quadrant0.reshape(-1,384)
        
        return quadrant0sq
        
