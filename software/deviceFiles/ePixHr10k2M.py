import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from ePixViewer.software._dataReceiver import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

ASIC_NUM    = 4
ASIC_HEIGHT = 192
ASIC_WIDTH  = 144
# expecting for even number of pixels : (2 + x) x 48 / 2
class DataReceiverEpixHr10k2M(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(ASIC_WIDTH * ASIC_NUM, ASIC_HEIGHT, **kwargs)
    
    def descramble(self, frame):
        # Function to descramble raw frames into numpy arrays
        payload = frame.getNumpy(0, frame.getPayload()).view(np.uint16)
        #array1_hex = np.array([hex(y) for y in img])
        #print("{} got payload of size {} uint16 {}".format(self.name, img.shape[0], array1_hex))
        img = payload[6:ASIC_WIDTH * ASIC_NUM * ASIC_HEIGHT + 6]
        print("{} got payload of size {} (uint16). Extracted image of size {} (uint16) {}".format(self.name, payload.shape[0], img.shape[0], img))
        imgReshaped = img.reshape(ASIC_WIDTH * ASIC_NUM,ASIC_HEIGHT)
        return imgReshaped