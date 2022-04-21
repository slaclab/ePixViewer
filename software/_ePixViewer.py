#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Title      : local image viewer for the ePix camera images
# -----------------------------------------------------------------------------
# File       : ePixViewer.py
# Author     : Dionisio Doering
# Created    : 2017-02-08
# Last update: 2017-02-08
# -----------------------------------------------------------------------------
# Description:
# Simple image viewer that enble a local feedback from data collected using
# ePix cameras. The initial intent is to use it with stand alone systems
#
# -----------------------------------------------------------------------------
# This file is part of the ePix rogue. It is subject to
# the license terms in the LICENSE.txt file found in the top-level directory
# of this distribution and at:
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
# No part of the ePix rogue, including this file, may be
# copied, modified, propagated, or distributed except according to the terms
# contained in the LICENSE.txt file.
# -----------------------------------------------------------------------------

import sys
import os
import rogue.utilities
import rogue.utilities.fileio
import rogue.interfaces.stream
import pyrogue
import time
import ePixViewer.imgProcessing as imgPr
import ePixViewer.Cameras as cameras
import ePixViewer.MplCanvas as mp
import ePixViewer.TabbedCtrlCanvas as tbcc
import ePixViewer.EventReader as er

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

PRINT_VERBOSE = 0

################################################################################
################################################################################
#   Window class
#   Implements the screen that display all images.
#   Calls other classes defined in this file to properly read and process
#   the images in a givel file
################################################################################


class Window(QMainWindow, QObject):
    """Class that defines the main window for the viewer."""

    # Define a new signal called 'trigger' that has no arguments.
    imageTrigger = pyqtSignal(object)
    pseudoScopeTrigger = pyqtSignal(object)
    monitoringDataTrigger = pyqtSignal(object)
    processFrameTrigger = pyqtSignal(object)
    processPseudoScopeFrameTrigger = pyqtSignal(object)
    processMonitoringFrameTrigger = pyqtSignal(object)

    def __init__(self, cameraType='ePix100a'):
        super(Window, self).__init__()
        # window init
        self.mainWdGeom = [50, 50, 1100, 600]  # x, y, width, height
        self.setGeometry(self.mainWdGeom[0], self.mainWdGeom[1], self.mainWdGeom[2], self.mainWdGeom[3])
        self.setWindowTitle("ePix Image Viewer")

        # creates a camera object
        self.currentCam = cameras.Camera(cameraType=cameraType)

        # add actions for menu item
        extractAction = QAction("&Quit", self)
        extractAction.setShortcut("Ctrl+Q")
        extractAction.setStatusTip('Leave The App')
        extractAction.triggered.connect(self.close_viewer)
        openFile = QAction("&Open File", self)
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip('Open a new set of images')
        openFile.setStatusTip('Open file')
        openFile.triggered.connect(self.file_open)

        # display status tips for all menu items (or actions)
        # pdb.set_trace()
        self.statusBar()

        # Creates the main menu,
        mainMenu = self.menuBar()
        # adds items and subitems
        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(openFile)
        fileMenu.addAction(extractAction)

        print('101')
        # Create widget
        self.prepairWindow()

        # add all buttons to the screen
        self.def_bttns()

        # rogue interconection  #
        # Create the objects
        self.fileReader = rogue.utilities.fileio.StreamReader()
        self.eventReader = er.EventReader(self)
        self.eventReaderScope = er.EventReader(self)
        self.eventReaderMonitoring = er.EventReader(self)

        # Connect the fileReader to our event processor
        pyrogue.streamConnect(self.fileReader, self.eventReader)

        # Connect the trigger signal to a slot.
        # the different threads send messages to synchronize their tasks
        self.imageTrigger.connect(self.buildImageFrame)
        self.pseudoScopeTrigger.connect(self.displayPseudoScopeFromReader)
        self.monitoringDataTrigger.connect(self.displayMonitoringDataFromReader)
        self.processFrameTrigger.connect(self.eventReader._processFrame)
        self.processPseudoScopeFrameTrigger.connect(self.eventReaderScope._processFrame)
        self.processMonitoringFrameTrigger.connect(self.eventReaderMonitoring._processFrame)

        # weak way to sync frame reader and display
        self.readFileDelay = 0.1
        self.displayBusy = False
        self.displayBysyCounter = 0
        print('131')
        # limits the rate of data to 1/ProcessFramePeriod
        # only single frame images work with this option
        if ((cameraType == 'ePix100a') or (cameraType == 'ePix10ka')):
            self.eventReader.ProcessFramePeriod = 0.5
        # Scompe and monitoring update rates are limited to 1 Hz
        self.eventReaderScope.ProcessFramePeriod = 1
        self.eventReaderMonitoring.ProcessFramePeriod = 1

        # initialize image processing objects
        self.rawImgFrame = []
        self.imgDesc = []
        self.imgTool = imgPr.ImageProcessing(self)

        # init mouse variables
        self.mouseX = 0
        self.mouseY = 0
        self.image = QImage()
        self.pixelTimeSeries = np.array([])
        self.chAdata = np.array([])
        self.chBdata = np.array([])
        print('152')
        # initialize data monitoring
        self.monitoringDataTraces = np.zeros((8, 1), dtype='int32')
        self.monitoringDataIndex = 0
        self.monitoringDataLength = 100

        # init bit mask
        self.pixelBitMask.setText(str(hex(np.uint16(self.currentCam.bitMask))))

        # display the window on the screen after all items have been added
        self.show()
        print('163')

    def prepairWindow(self):
        # Center UI
        self.imageScaleMax = int(10000)
        self.imageScaleMin = int(-10000)
        screen = QDesktopWidget().screenGeometry(self)
        size = self.geometry()
        self.buildUi()

    # creates the main display element of the user interface

    def buildUi(self):
        # label used to display image
        self.mainImageDisp = mp.MplCanvas(MyTitle="Image Display")
        #self.label = QLabel()
        #self.label.mousePressEvent = self.mouseClickedOnImage
        self.cid_mousePressEvent = self.mainImageDisp.mpl_connect('button_press_event', self.mouseClickedOnImage)
        # self.label.setAlignment(Qt.AlignTop)
        # self.label.setFixedSize(800,800)
        # self.label.setScaledContents(True)

        # left hand side layout
        self.mainWidget = QWidget(self)
        vbox1 = QVBoxLayout()
        vbox1.setAlignment(Qt.AlignTop)
        #vbox1.addWidget(self.label,  Qt.AlignTop)
        vbox1.addWidget(self.mainImageDisp, Qt.AlignTop)

        self.toolbar = NavigationToolbar(self.mainImageDisp, self)
        vbox1.addWidget(self.toolbar, Qt.AlignTop)

        # tabbed control box
        self.gridVbox2 = tbcc.TabbedCtrlCanvas(self)
        hSubbox1 = QHBoxLayout()
        hSubbox1.addWidget(self.gridVbox2)

        # line plot 1
        self.lineDisplay1 = mp.MplCanvas(MyTitle="Line Display 1")
        hSubbox2 = QHBoxLayout()
        hSubbox2.addWidget(self.lineDisplay1)

        # line plot 2
        self.lineDisplay2 = mp.MplCanvas(MyTitle="Line Display 2")
        hSubbox3 = QHBoxLayout()
        hSubbox3.addWidget(self.lineDisplay2)

        # right hand side layout
        vbox2 = QVBoxLayout()
        vbox2.addLayout(hSubbox1)
        vbox2.addLayout(hSubbox2)
        vbox2.addLayout(hSubbox3)

        hbox = QHBoxLayout(self.mainWidget)
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox2)

        self.mainWidget.setFocus()
        self.setCentralWidget(self.mainWidget)

    def setReadDelay(self, delay):
        self.eventReader.readFileDelay = delay
        self.eventReaderScope.readFileDelay = delay
        self.eventReaderMonitoring.readFileDelay = delay
        self.readFileDelay = delay

    def file_open(self):
        self.eventReader.frameIndex = 1
        self.eventReader.VIEW_DATA_CHANNEL_ID = 1
        self.setReadDelay(0.1)
        self.filename = QFileDialog.getOpenFileName(
            self, 'Open File', '', 'Rogue Images (*.dat);; GenDAQ Images (*.bin);;Any (*.*)')
        if (os.path.splitext(self.filename)[1] == '.dat'):
            self.displayImagDat(self.filename)
        else:
            self.displayImag(self.filename)

    def def_bttns(self):
        return self

    def setPixelBitMask(self):
        # updates the number of images used to calculate the dark image
        try:
            textInput = self.pixelBitMask.text()
            pixelBitMask = int(textInput, 16)
            if (pixelBitMask > 0):
                self.currentCam.bitMask = pixelBitMask
                print("Pixel Bit Mask Set.")
        except ValueError:
            pixelBitMask = self.currentCam.bitMask
            print("Error: Pixel Bit Mask Not Set. Got: ", self.pixelBitMask.text())

    def setDark(self):
        # updates the number of images used to calculate the dark image
        try:
            numDarkImg = int(self.numDarkImg.text())
        except ValueError:
            numDarkImg = self.imgTool.numDarkImages
        if (numDarkImg > 0):
            self.imgTool.numDarkImages = numDarkImg
        # starts capturing the images for the dark image generation
        self.imgTool.setDarkImg(self.imgDesc)
        print("Dark image requested.")

    def unsetDark(self):
        self.imgTool.unsetDarkImg()
        print("Dark image unset.")

    # display the previous frame from the current file

    def prevFrame(self):
        self.eventReader.frameIndex = int(self.frameNumberLine.text()) - 1
        if (self.eventReader.frameIndex < 1):
            self.eventReader.frameIndex = 1
        self.frameNumberLine.setText(str(self.eventReader.frameIndex))
        print('Selected frame ', self.eventReader.frameIndex)
        self.displayImagDat(self.filename)

    # display the next frame from the current file

    def nextFrame(self):
        self.eventReader.frameIndex = int(self.frameNumberLine.text()) + 1
        self.frameNumberLine.setText(str(self.eventReader.frameIndex))
        print('Selected frame ', self.eventReader.frameIndex)
        self.displayImagDat(self.filename)

    # checks if the user really wants to exit

    def close_viewer(self):
        choice = QMessageBox.question(self, 'Quit!',
                                            "Do you want to quit viewer?",
                                            QMessageBox.Yes | QMessageBox.No)
        if choice == QMessageBox.Yes:
            print("Exiting now...")
            sys.exit()
        else:
            pass

    # if the image is png or other standard extension it uses this function to display it.

    def displayImag(self, path):
        print('File name: ', path)
        if path:
            image = QImage(path)
            self.mainImageDisp.update_figure(image)
#            pp = QPixmap.fromImage(image)
#            self.label.setPixmap(pp.scaled(
#                    self.label.size(),
#                    KeepAspectRatio,
#                    SmoothTransformation))

    # if the image is a rogue type, calls the file reader object to read all frames

    def displayImagDat(self, filename):

        print('File name: ', filename)
        self.eventReader.readDataDone = False
        self.eventReader.numAcceptedFrames = 0
        self.fileReader.open(filename)

        # waits until data is found
        timeoutCnt = 0
        while ((self.eventReader.readDataDone == False) and (timeoutCnt < 10)):
            timeoutCnt += 1
            print('Loading image...', self.eventReader.frameIndex, 'atempt', timeoutCnt)
            time.sleep(0.1)

    # build image frame.
    # If image frame is completed calls displayImageFromReader
    # If image is incomplete stores the partial image
    def buildImageFrame(self):
        print('334')
        newRawData = self.eventReader.frameData.copy()
        #print('newRawData', len(newRawData))
        # print('self.rawImageFrame',len(self.rawImgFrame))
        # print('self.currentCam',self.currentCam)
        [frameComplete, readyForDisplay, self.rawImgFrame] = self.currentCam.buildImageFrame(
            currentRawData=self.rawImgFrame, newRawData=newRawData)
        #print('@ bulidImageFrame: frameComplete: ', frameComplete, 'readyForDisplay: ', readyForDisplay, 'returned raw data len', len(self.rawImgFrame))

        if (readyForDisplay):
            if (not self.displayBusy):
                self.displayImageFromReader(imageData=self.rawImgFrame)
            else:
                print("Display busy (%d)" % (self.displayBysyCounter))
                self.displayBysyCounter = self.displayBysyCounter + 1
                if (self.displayBysyCounter > 10):
                    self.displayBysyCounter = 0
                    self.displayBusy = False
                    # frees the memory since it has been used already enabling a new frame logic to start fresh
                    self.rawImgFrame = []
                    self.eventReader.frameData = bytearray()
                    self.frameDataArray = [bytearray(), bytearray(), bytearray(), bytearray()]
                    newRawData = bytearray()
                    frameComplete = 0
                    readyForDisplay = 0

        if (frameComplete == 0 and readyForDisplay == 1):
            # in this condition we have data about two different images
            # since a new image has been sent and the old one is incomplete
            # the next line preserves the new data to be used with the next frame
            print("Incomplete frame")
            self.rawImgFrame = newRawData
        if (frameComplete == 1):
            # frees the memory since it has been used alreay enabling a new frame logic to start fresh
            self.rawImgFrame = []
        self.eventReader.busy = False

    # core code for displaying the image
    def displayImageFromReader(self, imageData):
        print('372')
        # init variables
        self.displayBusy = True
        self.imgTool.imgWidth = self.currentCam.sensorWidth
        self.imgTool.imgHeight = self.currentCam.sensorHeight
        # get descrambled image com camera
        self.imgDesc = self.currentCam.descrambleImage(imageData)

        arrayLen = len(self.imgDesc)

        self._updateImageScales()

        if (self.imgTool.imgDark_isSet):
            self.ImgDarkSub = self.imgTool.getDarkSubtractedImg(self.imgDesc)
            # self.imgTool.reScaleImgTo8bit(self.ImgDarkSub, self.imageScaleMax, self.imageScaleMin)
            _8bitImg = self.ImgDarkSub
        else:
            # get the data into the image object
            # self.imgTool.reScaleImgTo8bit(self.imgDesc, self.imageScaleMax, self.imageScaleMin)
            _8bitImg = self.imgDesc

        #self.image = QImage(_8bitImg.repeat(4), self.imgTool.imgWidth, self.imgTool.imgHeight, QImage.Format_RGB32)

        #pp = QPixmap.fromImage(self.image)
        self.mainImageDisp.update_figure(_8bitImg, contrast=[self.imageScaleMax, self.imageScaleMin], autoScale=False)
        # self.label.setPixmap(pp.scaled(self.label.size(),KeepAspectRatio,SmoothTransformation))
        # self.label.adjustSize()
        # updates the frame number
        # this sleep is a weak way of waiting for the file to be readout completely... needs improvement
        time.sleep(self.readFileDelay)
        thisString = 'Frame {} of {}'.format(self.eventReader.frameIndex, self.eventReader.numAcceptedFrames)

        self.displayBusy = False

        self.postImageDisplayProcessing()

    """Checks the value on the user interface, if valid update them"""

    def _updateImageScales(self):
        # saves current values locally
        imageScaleMax = self.imageScaleMax
        print(imageScaleMax)
        imageScaleMin = self.imageScaleMin
        try:
            self.imageScaleMax = int(self.imageScaleMaxLine.text())
            self.imageScaleMin = int(self.imageScaleMinLine.text())
        except ValueError:
            self.imageScaleMax = imageScaleMax
            self.imageScaleMin = imageScaleMin

    def displayPseudoScopeFromReader(self):
        # saves data locally
        rawData = self.eventReaderScope.frameDataScope
        # converts bytes to array of dwords
        data = np.frombuffer(rawData, dtype='uint16')
        # limits trace length for fast display (may be removed in the future)

        # header are 8 32 bit words
        # footer are 5 32 bit words
        data = data[16:-10]
        oscWords = len(data)

        self.chAdata = -1.0 + data[0:int(oscWords / 2)] * (2.0 / 2**14)
        self.chBdata = -1.0 + data[int(oscWords / 2): oscWords] * (2.0 / 2**14)

        if (self.LinePlot2_RB1.isChecked()):
            self.lineDisplay2.update_plot(self.cbScopeCh0.isChecked(), "Scope Trace A", 'r', self.chAdata,
                                          self.cbScopeCh1.isChecked(), "Scope Trace B", 'b', self.chBdata)
        self.eventReaderScope.busy = False

    def displayMonitoringDataFromReader(self):
        rawData = self.eventReaderMonitoring.frameDataMonitoring
        envData = np.zeros((8, 1), dtype='int32')

        # exits if there is no
        if (len(rawData) == 0):
            return false
        # removes header before displying the image
        for j in range(0, 32):
            rawData.pop(0)
        for j in range(0, 8):
            envData[j] = int.from_bytes(rawData[j * 4:(j + 1) * 4], byteorder='little')
        # convert temperature and humidity by spliting for 100
        envData[0] = envData[0] / 100
        envData[1] = envData[1] / 100
        envData[2] = envData[2] / 100

        if (self.monitoringDataIndex == 0):
            self.monitoringDataTraces = envData
        else:
            self.monitoringDataTraces = np.append(self.monitoringDataTraces, envData, 1)

        if (self.LinePlot2_RB2.isChecked()):
            self.lineDisplay2.update_plot(self.cbEnvMonCh0.isChecked(), "Env. Data 0", 'r', self.monitoringDataTraces[0, :],
                                          self.cbEnvMonCh1.isChecked(
            ), "Env. Data 1", 'b', self.monitoringDataTraces[1, :],
                self.cbEnvMonCh2.isChecked(
            ), "Env. Data 2", 'g', self.monitoringDataTraces[2, :],
                self.cbEnvMonCh3.isChecked(
            ), "Env. Data 3", 'y', self.monitoringDataTraces[3, :],
                self.cbEnvMonCh4.isChecked(
            ), "Env. Data 4", 'r+-', self.monitoringDataTraces[4, :],
                self.cbEnvMonCh5.isChecked(
            ), "Env. Data 5", 'b+-', self.monitoringDataTraces[5, :],
                self.cbEnvMonCh6.isChecked(
            ), "Env. Data 6", 'g+-', self.monitoringDataTraces[6, :],
                self.cbEnvMonCh7.isChecked(), "Env. Data 7", 'y+-', self.monitoringDataTraces[7, :])

        # increments position
        self.monitoringDataIndex = self.monitoringDataIndex + 1
        if (self.monitoringDataIndex > self.monitoringDataLength):
            self.monitoringDataTraces = np.delete(self.monitoringDataTraces, 0, 1)

        self.eventReaderMonitoring.busy = False

    # Evaluates which post display algorithms are needed if any
    def postImageDisplayProcessing(self):
        # saves dark image set, if requested
        if (self.imgTool.imgDark_isRequested):
            self.imgTool.setDarkImg(self.imgDesc)
        # if the image gets done, saves it for other processes
        if (self.imgTool.imgDark_isSet):
            self.ImgDarkSub = self.imgTool.getDarkSubtractedImg(self.imgDesc)

        # check horizontal line display
        if ((self.cbHorizontalLineEnabled.isChecked()) or (self.cbVerticalLineEnabled.isChecked())
                or (self.cbpixelTimeSeriesEnabled.isChecked())):
            self.updatePixelTimeSeriesLinePlot()
            self.updateLinePlots()

    def updateLinePlots(self):
        ##if (PRINT_VERBOSE): print('Horizontal plot processing')

        # full line plot
        if (self.imgTool.imgDark_isSet):
            # self.ImgDarkSub
            self.lineDisplay1.update_plot(self.cbHorizontalLineEnabled.isChecked(), "Horizontal", 'r', self.ImgDarkSub[self.mouseY, :],
                                          self.cbVerticalLineEnabled.isChecked(
            ), "Vertical", 'b', self.ImgDarkSub[:, self.mouseX],
                self.cbpixelTimeSeriesEnabled.isChecked(), "Pixel TS", 'k', self.pixelTimeSeries)
        else:
            # self.imgDesc
            self.lineDisplay1.update_plot(self.cbHorizontalLineEnabled.isChecked(), "Horizontal", 'r', self.imgDesc[self.mouseY, :],
                                          self.cbVerticalLineEnabled.isChecked(
            ), "Vertical", 'b', self.imgDesc[:, self.mouseX],
                self.cbpixelTimeSeriesEnabled.isChecked(), "Pixel TS", 'k', self.pixelTimeSeries)

    """ Plot pixel values for multiple images """

    def clearPixelTimeSeriesLinePlot(self):
        self.pixelTimeSeries = np.array([])

    def updatePixelTimeSeriesLinePlot(self):
        ##if (PRINT_VERBOSE): print('Horizontal plot processing')

        # full line plot
        if (self.imgTool.imgDark_isSet):
            self.pixelTimeSeries = np.append(self.pixelTimeSeries, self.ImgDarkSub[self.mouseY, self.mouseX])
        else:
            self.pixelTimeSeries = np.append(self.pixelTimeSeries, self.imgDesc[self.mouseY, self.mouseX])

        if(not self.cbpixelTimeSeriesEnabled.isChecked()):
            self. clearPixelTimeSeriesLinePlot()

    """Save the enabled series to file, plot 1"""

    def SaveSeriesToFile(self):
        # open a pop up menu to set the filename
        self.filename = QFileDialog.getOpenFileName(self, 'Save File', '', 'csv file (*.csv);; Any (*.*)')
        if (self.cbHorizontalLineEnabled.isChecked()):
            if (self.imgTool.imgDark_isSet):
                np.savetxt(os.path.splitext(self.filename)[0] + "_horizontal" + os.path.splitext(self.filename)[
                           1], self.ImgDarkSub[self.mouseY, :], fmt='%d', delimiter=',', newline='\n')
            else:
                np.savetxt(os.path.splitext(self.filename)[0] + "_horizontal" + os.path.splitext(
                    self.filename)[1], self.imgDesc[self.mouseY, :], fmt='%d', delimiter=',', newline='\n')

        if (self.cbVerticalLineEnabled.isChecked()):
            if (self.imgTool.imgDark_isSet):
                np.savetxt(os.path.splitext(self.filename)[0] + "_vertical" + os.path.splitext(self.filename)[
                           1], self.ImgDarkSub[:, self.mouseX], fmt='%d', delimiter=',', newline='\n')
            else:
                np.savetxt(os.path.splitext(self.filename)[
                           0] + "_vertical" + os.path.splitext(self.filename)[1], self.imgDesc[:, self.mouseX], fmt='%d', delimiter=',', newline='\n')

        if (self.cbpixelTimeSeriesEnabled.isChecked()):
            np.savetxt(
                os.path.splitext(
                    self.filename)[0] +
                "_pixel" +
                os.path.splitext(
                    self.filename)[1],
                self.pixelTimeSeries,
                fmt='%d',
                delimiter=',',
                newline='\n')

    """Save the enabled monitoring series to file, plot 2"""

    def SaveMonitoringSeriesToFile(self):
        # open a pop up menu to set the filename
        self.filename = QFileDialog.getOpenFileName(self, 'Save File', '', 'csv file (*.csv);; Any (*.*)')
        print("saveMonitoring")
        if (self.LinePlot2_RB1.isChecked()):
            if (self.cbScopeCh0.isChecked()):
                print("channel0")
                np.savetxt(
                    os.path.splitext(
                        self.filename)[0] +
                    "_scope0" +
                    os.path.splitext(
                        self.filename)[1],
                    self.chAdata,
                    fmt='%f',
                    delimiter=',',
                    newline='\n')
            if (self.cbScopeCh1.isChecked()):
                print("channel1")
                np.savetxt(
                    os.path.splitext(
                        self.filename)[0] +
                    "_scope1" +
                    os.path.splitext(
                        self.filename)[1],
                    self.chBdata,
                    fmt='%f',
                    delimiter=',',
                    newline='\n')

    def _paintEvent(self, e):
        qp = QPainter()
        qp.begin(self.image)
        self.drawCross(qp)
        qp.end()

    def drawPoint(self, qp):
        qp.setPen(Qt.red)
        size = self.label.size()
        imageH = self.image.height()
        imageW = self.image.width()
        pixmapH = self.label.height()
        pixmapW = self.label.width()

        if ((self.mouseX > 0) and (self.mouseX < imageW)):
            if ((self.mouseY > 0) and (self.mouseY < imageH)):
                x = int(self.mouseX * pixmapW / imageW)
                y = int(self.mouseY * pixmapH / imageH)
                qp.drawPoint(x, y)

    def drawCross(self, qp):
        qp.setPen(Qt.red)
        size = self.label.size()
        imageH = self.image.height()
        imageW = self.image.width()
        pixmapH = self.label.height()
        pixmapW = self.label.width()

        if ((self.mouseX > 0) and (self.mouseX < imageW)):
            if ((self.mouseY > 0) and (self.mouseY < imageH)):
                x = int(self.mouseX * pixmapW / imageW)
                y = int(self.mouseY * pixmapH / imageH)
                qp.drawLine(x - 2, y - 2, x + 2, y + 2)
                qp.drawLine(x - 2, y + 2, x + 2, y - 2)

    def mouseClickedOnImage(self, event):
        if (self.imgDesc != []):
            #mouseX = event.pos().x()
            #mouseY = event.pos().y()
            self.mouseX, self.mouseY = int(event.xdata), int(event.ydata)
            #pixmapH = self.label.height()
            #pixmapW = self.label.width()
            #imageH = self.image.height()
            #imageW = self.image.width()

            #self.mouseX = int(imageW*mouseX/pixmapW)
            #self.mouseY = int(imageH*mouseY/pixmapH)

            if (self.imgTool.imgDark_isSet):
                self.mousePixelValue = self.ImgDarkSub[self.mouseY, self.mouseX]
            elif (self.imgDesc != []):
                self.mousePixelValue = self.imgDesc[self.mouseY, self.mouseX]

            # clear the pixel time sereis every time the pixel of interest is changed
            self.clearPixelTimeSeriesLinePlot()

            #print('Raw mouse coordinates: {},{}'.format(mouseX, mouseY))
            #print('Pixel map dimensions: {},{}'.format(pixmapW, pixmapH))
            #print('Image dimensions: {},{}'.format(imageW, imageH))
            print('Pixel[{},{}] = {}'.format(self.mouseX, self.mouseY, self.mousePixelValue))
            self.mouseXLine.setText(str(self.mouseX))
            self.mouseYLine.setText(str(self.mouseY))
            self.mouseValueLine.setText(str(self.mousePixelValue))
            # test on update_figure
            self.updateLinePlots()
            if (self.cbImageZoomEnabled.isChecked()):
                if (self.imgTool.imgDark_isSet):
                    self.lineDisplay1.update_figure(self.ImgDarkSub[self.mouseY -
                                                                    10:self.mouseY +
                                                                    10, self.mouseX -
                                                                    10:self.mouseX +
                                                                    10], contrast=[self.imageScaleMax, self.imageScaleMin], autoScale=False)
                elif (self.imgDesc != []):
                    self.lineDisplay1.update_figure(self.imgDesc[self.mouseY -
                                                                 10:self.mouseY +
                                                                 10, self.mouseX -
                                                                 10:self.mouseX +
                                                                 10], contrast=[self.imageScaleMax, self.imageScaleMin], autoScale=False)
