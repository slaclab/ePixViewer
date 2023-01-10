import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from ePixViewer.software._dataReceiver import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

class DataReceiverPseudoScope(pr.DataReceiver):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add(pr.LocalVariable(
            name = "ChannelAData",
            value = [],
            description = "Vector data for channel A"
        ))
        self.add(pr.LocalVariable(
            name = "ChannelBData",
            value = [],
            description = "Vector data for channel B"
        ))
        self.add(pr.LocalVariable(
            name = "ShowChannelAData",
            value = False,
            description = "Whether to show channel A data"
        ))
        self.add(pr.LocalVariable(
            name = "ShowChannelBData",
            value = False,
            description = "Whether to show chanel B data"
        ))
        self.add(pr.LocalVariable(
            name = "FFTXA",
            value = [],
            description = "Vector data for fourier transform x of channel A"
        ))
        self.add(pr.LocalVariable(
            name = "FFTYA",
            value = [],
            description = "Vector data for fourier transform y of channel A"
        ))
        self.add(pr.LocalVariable(
            name = "FFTXB",
            value = [],
            description = "Vector data for fourier transform x of channel B"
        ))
        self.add(pr.LocalVariable(
            name = "FFTYB",
            value = [],
            description = "Vector data for fourier transform y of channel B"
        ))

    def process(self, frame):
        rawData = bytearray(frame.getPayload())
        frame.read(rawData,0)
        data  = np.frombuffer(rawData,dtype='uint16')
        data  = data[16:-14]
        oscWords = len(data)
        chAdata = -0.0 + data[0:int(oscWords/2)] * (2.0/2**14)
        chBdata = -0.0 + data[int(oscWords/2): oscWords] * (2.0/2**14)
        chAdata = (2.0-0.053) + chAdata * (-1.04)
        chBdata = (2.0-0.053) + chBdata * (-1.04)
        N = len(chAdata)
        TA = 4E-8
        freqs = []
        yfA = []
        yfB = []
        zeros = np.zeros(1)
        if N > 0:
            freqs = np.fft.rfftfreq(N, TA)
            yfA = np.abs(np.fft.rfft(chAdata))
            yfB = np.abs(np.fft.rfft(chBdata))
            with self.root.updateGroup():
                if self.ShowChannelAData.get():
                    self.ChannelAData.set(chAdata, write = True)
                    self.FFTXA.set(freqs[2:], write = True)
                    self.FFTYA.set(yfA[2:], write = True)
                else:
                    self.ChannelAData.set(zeros, write = True)
                    self.FFTXA.set(zeros, write = True)
                    self.FFTYA.set(zeros, write = True)
                if self.ShowChannelBData.get():
                    self.ChannelBData.set(chBdata, write = True)
                    self.FFTXB.set(freqs[2:], write = True)
                    self.FFTYB.set(yfB[2:], write = True)
                else:
                    self.ChannelBData.set(zeros, write = True)
                    self.FFTXB.set(zeros, write = True)
                    self.FFTYB.set(zeros, write = True)
                self.Updated.set(True, write = True)