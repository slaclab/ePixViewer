import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from ePixViewer import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

class DataReceiverEpix100a(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(708, 768, **kwargs)
        
        self._superRowSize = 384
        self._NumAsicsPerSide = 2
        self._NumAdcChPerAsic = 4
        self._NumColPerAdcCh = 96
        self._superRowSizeInBytes = self._superRowSize * 4
        self.sensorWidth = self._calcImgWidth()
        self.sensorHeight = 708
        self.pixelDepth = 16
        self.cameraModule = "Standard ePix100a"
        self.bitMask = np.uint16(0xFFFF)
    
    def descramble(self, frame):
        imgDesc = bytearray(frame.getPayload())
        frame.read(imgDesc,0)
        imgDesc = self._descrambleEPix100aImage(imgDesc)
        
        return imgDesc

    def _calcImgWidth(self):
        return self._NumAsicsPerSide * self._NumAdcChPerAsic * self._NumColPerAdcCh

    def _descrambleEPix100aImageAsByteArray(self, rawData):
        """performs the ePix100a image descrambling (this is a place holder only)"""
        
        #removes header before displying the image
        for j in range(0,32):
            rawData.pop(0)
        
        #get the first superline
        imgBot = bytearray()
        imgTop = bytearray()
        for j in range(0,self.sensorHeight):
            if (j%2):
                imgTop.extend(rawData[((self.sensorHeight-j)*self._superRowSizeInBytes):((self.sensorHeight-j+1)*self._superRowSizeInBytes)])
            else:
                imgBot.extend(rawData[(j*self._superRowSizeInBytes):((j+1)*self._superRowSizeInBytes)]) 
        imgDesc = imgTop
        imgDesc.extend(imgBot)

        # returns final image
        return imgDesc

    def _descrambleEPix100aImage(self, rawData):
        """performs the ePix100a image descrambling """
        
        imgDescBA = self._descrambleEPix100aImageAsByteArray(rawData)

        imgDesc = np.frombuffer(imgDescBA,dtype='int16')
        if self.sensorHeight*self.sensorWidth != len(imgDesc):
           print("Got wrong pixel number ", len(imgDesc))
        else:
           imgDesc = imgDesc.reshape(self.sensorHeight, self.sensorWidth)
        # returns final image
        return imgDesc
