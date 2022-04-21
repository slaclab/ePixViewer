
import os
import rogue.utilities
import rogue.utilities.fileio
import rogue.interfaces.stream
import pyrogue
import time
import ePixViewer.imgProcessing as imgPr
import ePixViewer.Cameras as cameras
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import pdb

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
except ImportError:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *

################################################################################
################################################################################
#   Event reader class
#
################################################################################
class EventReader(rogue.interfaces.stream.Slave):
    """retrieves data from a file using rogue utilities services"""

    def __init__(self, parent):
        rogue.interfaces.stream.Slave.__init__(self)
        super(EventReader, self).__init__()
        self.enable = True
        self.numAcceptedFrames = 0
        self.numProcessFrames = 0
        self.numSkipFrames = 1  # 1 accpts all frames, 2 accepts every other frame, 3 every thrid frame and so on
        self.lastProcessedFrameTime = 0
        self.ProcessFramePeriod = 0
        self.lastFrame = rogue.interfaces.stream.Frame
        self.frameIndex = 1
        self.frameData = bytearray()
        self.frameDataArray = [bytearray(), bytearray(), bytearray(), bytearray()]  # bytearray()
        self.frameDataScope = bytearray()
        self.frameDataMonitoring = bytearray()
        self.readDataDone = False
        self.parent = parent
        #############################
        # define the data type IDs
        #############################
        self.VIEW_DATA_CHANNEL_ID = 0x1
        self.VIEW_PSEUDOSCOPE_ID = 0x2
        self.VIEW_MONITORING_DATA_ID = 0x3
        self.readFileDelay = 0.1
        self.busy = False
        self.busyTimeout = 0
        self.lastTime = time.clock_gettime(0)

    # Checks all frames in the file to look for the one that needs to be displayed
    # self.frameIndex defines which frame should be returned.
    # Once the frame is found, saves data and emits a signal do enable the class window
    # to dislplay it. The emit signal is needed because only that class' thread can
    # access the screen.

    def _acceptFrame(self, frame):
        # enter debug mode
        #print("\n---------------------------------\n-\n- Entering DEBUG mode _acceptFrame \n-\n-\n--------------------------------- ")
        # pdb.set_trace()

        self.lastFrame = frame
        # reads entire frame
        p = bytearray(self.lastFrame.getPayload())
        self.lastFrame.read(p, 0)
        if (PRINT_VERBOSE):
            print('_accepted p[', self.numAcceptedFrames, '] flags: ', self.lastFrame.getFlags(), ' len: ', len(p))
        if (PRINT_VERBOSE):
            print('_accepted p[', self.numAcceptedFrames, ']: ', p[0:40])
        ##if (PRINT_VERBOSE): print('_accepted type' , type(p))
        self.frameDataArray[self.numAcceptedFrames % 4][:] = p  # bytearray(self.lastFrame.getPayload())
        self.numAcceptedFrames += 1

        VcNum = p[0] & 0xF
        if (self.busy):
            self.busyTimeout = self.busyTimeout + 1
            if (PRINT_VERBOSE):
                print("Event Reader Busy: " + str(self.busyTimeout))
            if self.busyTimeout > 10:
                self.busy = False
        else:
            self.busyTimeout = 0

        if (time.clock_gettime(0) - self.lastTime) > 1 or self.parent.currentCam.cameraType == 'ePixM32Array':
            self.lastTime = time.clock_gettime(0)
            if ((VcNum == self.VIEW_PSEUDOSCOPE_ID) and (not self.busy)):
                self.lastProcessedFrameTime = time.time()
                self.parent.processPseudoScopeFrameTrigger.emit()
            elif (VcNum == self.VIEW_MONITORING_DATA_ID and (not self.busy)):
                self.lastProcessedFrameTime = time.time()
                self.parent.processMonitoringFrameTrigger.emit()
            elif (VcNum == 0):
                if (((self.numAcceptedFrames == self.frameIndex) or (self.frameIndex == 0))
                        and (self.numAcceptedFrames % self.numSkipFrames == 0)):
                    self.lastProcessedFrameTime = time.time()
                    if (self.parent.cbdisplayImageEn.isChecked()):
                        self.parent.processFrameTrigger.emit()

    def _processFrame(self):

        index = self.numProcessFrames % 4
        self.numProcessFrames += 1
        if ((self.enable) and (not self.busy)):
            self.busy = True

            # Get the channel number
            chNum = (self.lastFrame.getFlags() >> 24)
            # reads payload only
            p = self.frameDataArray[index]
            # reads entire frame
            VcNum = p[0] & 0xF
            if (PRINT_VERBOSE):
                print(
                    '-------- Frame ',
                    self.numAcceptedFrames,
                    'Channel flags',
                    self.lastFrame.getFlags(),
                    ' Channel Num:',
                    chNum,
                    ' Vc Num:',
                    VcNum)
            # Check if channel number is 0x1 (streaming data channel)
            if (chNum == self.VIEW_DATA_CHANNEL_ID or VcNum == 0):
                # Collect the data
                if (PRINT_VERBOSE):
                    print('Num. image data readout: ', len(p))
                self.frameData[:] = p
                cnt = 0
#                if ((self.numAcceptedFrames == self.frameIndex) or (self.frameIndex == 0)):
                self.readDataDone = True
                # Emit the signal.
                self.parent.imageTrigger.emit()
                # if displaying all images the sleep produces a frame rate that can be displayed without
                # freezing or crashing the program.
#                time.sleep(self.readFileDelay)

            # during stream chNumId is not assigned so these ifs cannot be used to distiguish the frames
            # during stream VIEW_PSEUDOSCOPE_ID is set to zero
            if (chNum == self.VIEW_PSEUDOSCOPE_ID or VcNum == self.VIEW_PSEUDOSCOPE_ID):
                # view Pseudo Scope Data
                if (PRINT_VERBOSE):
                    print('Num. pseudo scope data readout: ', len(p))
                self.frameDataScope[:] = p
                # Emit the signal.
                self.parent.pseudoScopeTrigger.emit()
                # if displaying all images the sleep produces a frame rate that can be displayed without
                # freezing or crashing the program.
#                time.sleep(self.readFileDelay)

            if (chNum == self.VIEW_MONITORING_DATA_ID or VcNum == self.VIEW_MONITORING_DATA_ID):
                # view Pseudo Scope Data
                if (PRINT_VERBOSE):
                    print('Num. slow monitoring data readout: ', len(p))
                self.frameDataMonitoring[:] = p
                # Emit the signal.
                self.parent.monitoringDataTrigger.emit()
                # if displaying all images the sleep produces a frame rate that can be displayed without
                # freezing or crashing the program.
#                time.sleep(self.readFileDelay)
            # sets busy flag at the end
            #self.busy = False