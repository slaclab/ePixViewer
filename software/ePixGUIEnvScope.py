#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Title      : Configuration file for live pseudoscope monitoring
#-----------------------------------------------------------------------------
# File       : ePixGUIPseudoScope.py
# Author     : Jaeyoung (Daniel) Lee
# Created    : 2022-06-22
# Last update: 2022-07-27
#-----------------------------------------------------------------------------
# Description:
# Configuration file for building the live pseudoscope monitoring GUI using
# PyDM
#-----------------------------------------------------------------------------
# This file is part of the ePix rogue. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the ePix rogue, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------

import os
import pydm
import json

from pydm.widgets import PyDMEnumComboBox, PyDMLabel, PyDMCheckbox
from pydm.widgets.channel import PyDMChannel

def runEnvScopeDisplay(dataReceiver, serverList='localhost:9090', root=None,
                   title=None,sizeX=800,sizeY=1000,maxListExpand=5,maxListSize=100):

    if root is not None:

        if not root.running:
            raise Exception("Attempt to use pydm with root that has not started")

        os.environ['ROGUE_SERVERS'] = 'localhost:{}'.format(root.serverPort)
    else:
        os.environ['ROGUE_SERVERS'] = serverList

    ui = os.path.abspath(__file__)

    if title is None:
        title = "Epix Live Display: {}".format(os.getenv('ROGUE_SERVERS'))

    args = []
    args.append(f"sizeX={sizeX}")
    args.append(f"sizeY={sizeY}")
    args.append(f"title='{title}'")
    args.append(f"maxListExpand={maxListExpand}")
    args.append(f"maxListSize={maxListSize}")

    app = pydm.PyDMApplication(ui_file=ui,
                               command_line_args=args,
                               macros={'dataReceiver': dataReceiver},
                               hide_nav_bar=True,
                               hide_menu_bar=True,
                               hide_status_bar=True)
    app.exec()

class ePixGUIEnvScope(pydm.Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(ePixGUIEnvScope, self).__init__(parent=parent, args=args, macros=macros)
        
        self._dataReceiver = macros['dataReceiver']
        self._channelboxes = []
        self.colors = ['black','red','blue','green','purple','orange','yellow','pink']
        
        channel = PyDMChannel(address='{}.channelList'.format(macros['dataReceiver']),
                              value_slot=self.channel_list_changed)
                              
        # Connect write channels if we have them
        channel.connect()
        
        #self.ui.PyDMWaveformPlot.setGraphXLabel('time (s)')
        
        #for i in range(5):
        #  device_label = PyDMLabel(parent=self, init_channel='{}.ChannelName'.format(macros['dataReceiver']))
        #  self.ui.deviceListLayout.addWidget(device_label)
  
    def ui_filename(self):
        # Point to the UI file
        return 'ui/ePixViewerEnvDataPyDM.ui'

    def ui_filepath(self):
        # Return the full path to the UI file
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), self.ui_filename())
        
    def channel_list_changed(self, value):
        self._channels = json.loads(value)
        for channel in self._channels:
            self._channelboxes.append(PyDMCheckbox(self._channels[channel]['name'], init_channel='{}.selCh{}'.format(self._dataReceiver, channel)))
            self.ui.channelList.addWidget(self._channelboxes[-1])
            self._channelboxes[-1].stateChanged.connect(self.updatePlotCurves)
            self._channelboxes[-1].chId = channel
            self._channelboxes[-1].verbose = self._channels[channel]['name']
            self._channelboxes[-1].lineColor = self._channels[channel]['color']
            
    def updatePlotCurves(self):
        #Look at all of the boxes
        for box in self._channelboxes:
        
            tmp = -1
            found = -1
            
            #search if channel is already ON
            for c in self.ui.PyDMWaveformPlot.getCurves():
                curve = json.loads(c)
                tmp += 1
                
                if curve['y_channel'] == self._dataReceiver + ".data[{}]".format(int(box.chId)):
                    found = tmp
                    break
                                
            #If box is checked: add channel if not ON or keep it
            if box.isChecked():
                if found == -1:
                    self.ui.PyDMWaveformPlot.addChannel(
                        y_channel=self._dataReceiver + ".data[{}]".format(box.chId),
                        x_channel=self._dataReceiver + ".dataX[{}]".format(box.chId), 
                        name=box.verbose, 
                        color=box.lineColor, 
                        lineStyle=1, 
                        lineWidth=2, 
                        symbol=None, 
                        symbolSize=10, 
                        redraw_mode=2,
                        yAxisName="Axis 1"
                    )
                    
            #Otherwise, remove the curve when it is ON
            elif found > -1:
                self.ui.PyDMWaveformPlot.removeChannelAtIndex(found)
                
        #Redraw the legend
        legend = self.ui.PyDMWaveformPlot._legend
        legend.clear()
        for curve in self.ui.PyDMWaveformPlot._curves:
            legend.addItem(curve, curve.name())
        
