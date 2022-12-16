import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from epixViewer.software._dataReceiver import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

class DataReceiverEpix100p(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(706, 768, **kwargs)
    
    def descramble(self, frame):
        for j in range(0,32):
            frame.pop(0)
        imgBot = frame[(0*1536):(1*1536)] 
        imgTop = frame[(1*1536):(2*1536)] 
        for j in range(2,706):
            if (j%2):
                imgBot.extend(frame[(j*1536):((j+1)*1536)])
            else:
                imgTop.extend(frame[(j*1536):((j+1)*1536)]) 
        imgDesc = imgBot
        imgDesc.extend(imgTop)
        imgDesc = np.array(imgDesc,dtype='uint8')
        return imgDesc