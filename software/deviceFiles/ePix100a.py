import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from ePixViewer.software._dataReceiver import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

class DataReceiverEpix100a(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(708, 768, **kwargs)
    
    def descramble(self, frame):
        imgDescBA = self._descrambleEPix100aImageAsByteArray(frame)
        imgDesc = np.frombuffer(imgDescBA,dtype='int16')
        imgDesc = imgDesc.reshape(self.sensorHeight, self.sensorWidth)
        return imgDesc