import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from ePixViewer.software._dataReceiver import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

ASIC_NUM    = 5
ASIC_HEIGHT = 192
ASIC_WIDTH  = 144

class DataReceiverEpixHr10k2M(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(ASIC_WIDTH * ASIC_NUM, ASIC_HEIGHT, **kwargs)
    
    def descramble(self, frame):
        # Function to descramble raw frames into numpy arrays
        img = frame.getNumpy(0, frame.getPayload()).view(np.uint16)
        imgReshaped = img.reshape(ASIC_WIDTH * ASIC_NUM,ASIC_HEIGHT)
        return imgReshaped