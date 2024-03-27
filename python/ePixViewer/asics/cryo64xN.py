import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from ePixViewer import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

class DataReceiverCryo64xN(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(64, 64, **kwargs)
    
    def descramble(self, frame):
        img = frame.getNumpy(0, frame.getPayload()).view(np.uint16)
        samples = int((img.shape[0]-6)/64)
        if (samples) != ((img.shape[0]-6)/64):
            imgDesc = np.zeros((64,64), dtype='uint16')
            return imgDesc
        img2 = img[6:].reshape(samples,64)
        imgDesc = np.append(img2[:,0:64:2].transpose(), img2[:,1:64:2].transpose()).reshape(64,samples)
        return imgDesc
