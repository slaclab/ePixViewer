#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Title      : Updated data receivers for PyDM live viewer
#-----------------------------------------------------------------------------
# File       : _envDataReceiver.py
# Author     : Julian Mendez
# Created    : 2023-08-24
# Last update: 2023-09-25
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
import json

class EnvDataReceiver(pr.DataReceiver):
    def __init__(self, config, rawToData, clockT, payloadElementSize=4, **kwargs):
        super().__init__(**kwargs)
        
        self.configChannels = config
        self.channelSel = 0
        self.clockT = clockT
        self.tickCount = 0
        self.rawToData = rawToData
        self.payloadElementSize = payloadElementSize
        enum = {}
        
        for i in range(len(config)):
            enum[i] = {
                'name': config[i]['name'],
                'color': config[i]['color']
            }
            
            self.add(pr.LocalVariable(
                name = 'selCh{}'.format(i),
                description = 'selectChannel',
                value = True,
                hidden=True
            ))

            self.add(pr.LocalVariable(
                name = "data[{}]".format(i),
                description = "Data Y",
                value = [],
                hidden=True
            ))

            self.add(pr.LocalVariable(
                name = "dataX[{}]".format(i),
                description = "Data X",
                value = [],
                hidden=True
            ))

            self.configChannels[i]['ptr'] = config[i]['name']
            self.configChannels[i]['ptr'] = self.configChannels[i]['ptr'].replace(' ','_').replace('(','_')
            self.configChannels[i]['ptr'] = self.configChannels[i]['ptr'].replace(')','').replace('[','_')
            self.configChannels[i]['ptr'] = self.configChannels[i]['ptr'].replace(']','').replace('.','')
            self.configChannels[i]['ptr'] = self.configChannels[i]['ptr'].replace('-','').replace('%','percent')
            config[i].setdefault('units', '')
            
            self.add(pr.LocalVariable(
                name = self.configChannels[i]['ptr'],
                description = "{} value".format(config[i]['name']),
                value = 0.0,
                units = config[i]['units'],
                mode         = 'RO'
            ))
        
        self.add(pr.LocalVariable(
            name = 'Ellapsed',
            description = "Duration in seconds since measurement starts",
            value = 0.0,
        ))

        @self.command()
        def OpenGUI():
            subprocess.Popen(["python", os.path.dirname(os.path.abspath(__file__))+"/runLiveDisplay.py", "--dataReceiver", "rogue://0/root.{}".format(kwargs['name']), "env", "--title", "Environmental"], shell=False)

        @self.command()
        def Clear():
            for i in range(len(self.configChannels)):
                self.tickCount = 0
                self.data[i].set(np.array([]))
                self.dataX[i].set(np.array([]))
                self._nodes[self.configChannels[i]['ptr']].set(0)
        
        self.add(pr.LocalVariable(
            name = 'channelList',
            description = 'channel list for GUI configuration',
            value = json.dumps(enum),
            hidden=True
        ))
        
    def process(self, frame):
        if (self.payloadElementSize == 8) :
            payload = frame.getNumpy(0, frame.getPayload()).view(np.uint64)
            if self.clockT is not None:
                self.tickCount = self.tickCount + int(payload[0] & np.uint64(0x0fffffff))
            else:
                self.tickCount += 1
        else :    
            payload = frame.getNumpy(0, frame.getPayload()).view(np.uint32)
            if self.clockT is not None:
                self.tickCount = self.tickCount + int(payload[0] & 0x0fffffff)
            else:
                self.tickCount += 1

        
        for i in range(len(self.configChannels)):
            newData = self.configChannels[i]['conv'](self.rawToData(int(payload[self.configChannels[i]['id']+1])))
            
            arr = self.data[i].get()
            arr = np.append(arr, newData)
            
            xarr = self.dataX[i].get()
            if len(xarr) == 0:
                xarr = np.append(xarr, 0)
            else:
                if self.clockT is not None:
                    xarr = np.append(xarr, round((float(self.tickCount)*self.clockT*16), 2))
                else:
                    xarr = np.append(xarr, self.tickCount)
                
            self.data[i].set(arr)
            self.dataX[i].set(xarr)
            
            self._nodes[self.configChannels[i]['ptr']].set(round(newData,5))
            
        if self.clockT is not None:
            self.Ellapsed.set(round((float(self.tickCount)*self.clockT*16), 2))
        else:
            self.Ellapsed += 1
        
        '''
        print('PAYLOAD LEN: {}'.format(len(payload)))
        print('{:x} - tick count : {:x} \'h'.format((payload[0] & 0xf0000000) >> 28, int(payload[0] & 0x0fffffff)))
        print('Ch {:d}: {:f}'.format((payload[1] & 0xff000000) >> 24, (5* float(payload[1] & 0xffffff) / 16777216)))
        print('Ch {:d}: {:f}'.format((payload[2] & 0xff000000) >> 24, (5* float(payload[2] & 0xffffff) / 16777216)))
        print('Ch {:d}: {:f}'.format((payload[3] & 0xff000000) >> 24, (5* float(payload[3] & 0xffffff) / 16777216)))
        print('Ch {:d}: {:f}'.format((payload[4] & 0xff000000) >> 24, (5* float(payload[4] & 0xffffff) / 16777216)))
        print('Ch {:d}: {:f}'.format((payload[5] & 0xff000000) >> 24, (5* float(payload[5] & 0xffffff) / 16777216)))
        print('Ch {:d}: {:f}'.format((payload[6] & 0xff000000) >> 24, (5* float(payload[6] & 0xffffff) / 16777216)))
        print('Ch {:d}: {:f}'.format((payload[7] & 0xff000000) >> 24, (5* float(payload[7] & 0xffffff) / 16777216)))
        print('Ch {:d}: {:f}'.format((payload[8] & 0xff000000) >> 24, (5* float(payload[8] & 0xffffff) / 16777216)))
        '''

        return
