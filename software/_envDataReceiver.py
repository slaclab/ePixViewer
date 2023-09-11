#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Title      : Updated data receivers for PyDM live viewer
#-----------------------------------------------------------------------------
# File       : dataReceivers.py
# Author     : Jaeyoung (Daniel) Lee
# Created    : 2022-06-22
# Last update: 2022-08-26
#-----------------------------------------------------------------------------
# Description:
# Updated data receivers for processing image, environment, and pseudoscope
# data for the new PyDM live viewer
#-----------------------------------------------------------------------------
# This file is part of the ePix rogue. It is subject to
# the license terms in the LICENSE.txt file found in the top-level directory
# of this distribution and at:
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
# No part of the ePix rogue, including this file, may be
# copied, modified, propagated, or distributed except according to the terms
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------
# Catch the future warning bitwise and with bitmask
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

import subprocess
import os

class EnvDataReceiver(pr.DataReceiver):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        print(kwargs)


        @self.command()
        def OpenGUI():
            subprocess.Popen(["python", os.path.dirname(os.path.abspath(__file__))+"/runLiveDisplay.py", "--dataReceiver", "rogue://0/root.{}".format(kwargs['name']), "pseudoscope", "--title", "PseudoScope 0"], shell=False)

        '''
        self.add(pr.LocalVariable(
            name = "ShowChannelBData",
            description = "Enable channel B",
            value = True
        ))

        self.add(pr.LocalVariable(
            name = "ShowChannelAData",
            description = "Enable channel A",
            value = True
        ))

        self.add(pr.LocalVariable(
            name = "ChannelAData",
            description = "channel A",
            value = []
        ))

        self.add(pr.LocalVariable(
            name = "ChannelBData",
            description = "channel B",
            value = []
        ))

        self.add(pr.LocalVariable(
            name = "FFTYA",
            description = "channel A FFT (Y data)",
            value = []
        ))

        self.add(pr.LocalVariable(
            name = "FFTXA",
            description = "channel A FFT (X data)",
            value = []
        ))

        self.add(pr.LocalVariable(
            name = "FFTYB",
            description = "channel B FFT (Y data)",
            value = []
        ))

        self.add(pr.LocalVariable(
            name = "FFTXB",
            description = "channel B FFT (X data)",
            value = []
        ))
        '''

    def process(self, frame):
        
        payload = frame.getNumpy(0, frame.getPayload()).view(np.uint32)
        print('PAYLOAD LEN: {}'.format(len(payload)))
        '''
        datalen = int((len(payload)-26)/2)

        channelA = -1.0 + payload[16:16+datalen] * (2.0 / 2**14)
        channelB = -1.0 + payload[16+datalen:16+(2*datalen)] * (2.0 / 2**14)

        sr = 1

        X = fft(channelA)
        N = len(X)
        n = np.arange(N)
        T = N/sr
        freq = n/T


        self.ChannelAData.set(channelA)
        self.FFTXA.set(freq)
        self.FFTYA.set(np.abs(X))

        X = fft(channelB)
        N = len(X)
        n = np.arange(N)
        T = N/sr
        freq = n/T

        self.ChannelBData.set(channelB)
        self.FFTXB.set(freq)
        self.FFTYB.set(np.abs(X))
        '''

        return
