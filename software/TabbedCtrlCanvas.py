

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
#   Tabbed control class
#
################################################################################
class TabbedCtrlCanvas(QTabWidget):
    # https://pythonspot.com/qt4-tabs/ tips on tabs
    def __init__(self, parent):
        super(TabbedCtrlCanvas, self).__init__()

        # pointer to the parent class
        myParent = parent

        # Create tabs
        tab1 = QWidget()
        tab2 = QWidget()
        tab3 = QWidget()
        tab4 = QWidget()

        ######################################################
        # create widgets for tab 1 (Main)
        ######################################################
        # label used to display frame number
        self.labelFrameNum = QLabel('')
        # button set dark
        btnSetDark = QPushButton("Set Dark")
        btnSetDark.setMaximumWidth(150)
        btnSetDark.clicked.connect(myParent.setDark)
        btnSetDark.resize(btnSetDark.minimumSizeHint())
        # button unset dark
        btnUnSetDark = QPushButton("Unset Dark")
        btnUnSetDark.setMaximumWidth(150)
        btnUnSetDark.clicked.connect(myParent.unsetDark)
        btnUnSetDark.resize(btnUnSetDark.minimumSizeHint())
        numDarkImgLabel = QLabel("Number of Dark images")
        myParent.numDarkImg = QLineEdit()
        myParent.numDarkImg.setMaximumWidth(150)
        myParent.numDarkImg.setMinimumWidth(100)
        myParent.numDarkImg.setText(str(10))
        # button quit
        btnQuit = QPushButton("Quit")
        btnQuit.setMaximumWidth(150)
        btnQuit.clicked.connect(myParent.close_viewer)
        btnQuit.resize(btnQuit.minimumSizeHint())
        # mouse buttons
        mouseLabel = QLabel("Pixel Information")
        myParent.mouseXLine = QLineEdit()
        myParent.mouseXLine.setMaximumWidth(150)
        myParent.mouseXLine.setMinimumWidth(100)
        myParent.mouseYLine = QLineEdit()
        myParent.mouseYLine.setMaximumWidth(150)
        myParent.mouseYLine.setMinimumWidth(100)
        myParent.mouseValueLine = QLineEdit()
        myParent.mouseValueLine.setMaximumWidth(150)
        myParent.mouseValueLine.setMinimumWidth(100)
        # set bitmask
        btnSetPixelBitMask = QPushButton("Set")
        btnSetPixelBitMask.setMaximumWidth(150)
        btnSetPixelBitMask.clicked.connect(myParent.setPixelBitMask)
        btnSetPixelBitMask.resize(btnSetPixelBitMask.minimumSizeHint())
        pixelBitMaskLabel = QLabel("Pixel Bit Mask")
        myParent.pixelBitMask = QLineEdit()
        myParent.pixelBitMask.setMaximumWidth(150)
        myParent.pixelBitMask.setMinimumWidth(100)
        myParent.pixelBitMask.setInputMask("0xHHHH")
        # label contrast
        imageScaleLabel = QLabel("Contrast (max, min)")
        myParent.imageScaleMaxLine = QLineEdit()
        myParent.imageScaleMaxLine.setMaximumWidth(100)
        myParent.imageScaleMaxLine.setMinimumWidth(50)
        myParent.imageScaleMaxLine.setText(str(myParent.imageScaleMax))
        myParent.imageScaleMinLine = QLineEdit()
        myParent.imageScaleMinLine.setMaximumWidth(100)
        myParent.imageScaleMinLine.setMinimumWidth(50)
        myParent.imageScaleMinLine.setText(str(myParent.imageScaleMin))
        # check boxes
        myParent.cbdisplayImageEn = QCheckBox('Display Image Enable')

        # set layout to tab 1
        tab1Frame = QFrame()
        tab1Frame.setFrameStyle(QFrame.Panel)
        tab1Frame.setGeometry(100, 200, 0, 0)
        tab1Frame.setLineWidth(1)
        grid = QGridLayout()
        grid.setSpacing(5)
        grid.addWidget(tab1Frame, 0, 0, 7, 7)

        # add widgets to tab1
        grid.addWidget(numDarkImgLabel, 1, 1)
        grid.addWidget(myParent.numDarkImg, 1, 2)
        grid.addWidget(btnSetDark, 1, 3)
        grid.addWidget(btnUnSetDark, 1, 4)
        grid.addWidget(mouseLabel, 2, 1)
        grid.addWidget(myParent.mouseXLine, 2, 2)
        grid.addWidget(myParent.mouseYLine, 2, 3)
        grid.addWidget(myParent.mouseValueLine, 2, 4)
        grid.addWidget(pixelBitMaskLabel, 3, 1)
        grid.addWidget(myParent.pixelBitMask, 3, 2)
        grid.addWidget(btnSetPixelBitMask, 3, 3)
        grid.addWidget(myParent.cbdisplayImageEn, 3, 4)
        grid.addWidget(imageScaleLabel, 4, 1)
        grid.addWidget(myParent.imageScaleMaxLine, 4, 2)
        grid.addWidget(myParent.imageScaleMinLine, 4, 3)

        # complete tab1
        tab1.setLayout(grid)

        ######################################################
        # create widgets for tab 2 (File controls)
        ######################################################
        # button prev
        btnPrevFrame = QPushButton("Prev")
        btnPrevFrame.setMaximumWidth(150)
        btnPrevFrame.clicked.connect(myParent.prevFrame)
        btnPrevFrame.resize(btnPrevFrame.minimumSizeHint())

        # button next
        btnNextFrame = QPushButton("Next")
        btnNextFrame.setMaximumWidth(150)
        btnNextFrame.clicked.connect(myParent.nextFrame)
        btnNextFrame.resize(btnNextFrame.minimumSizeHint())

        # frame number
        myParent.frameNumberLine = QLineEdit()
        myParent.frameNumberLine.setMaximumWidth(100)
        myParent.frameNumberLine.setMinimumWidth(50)
        myParent.frameNumberLine.setText(str(1))

        # set layout to tab 2
        tab2Frame1 = QFrame()
        tab2Frame1.setFrameStyle(QFrame.Panel)
        tab2Frame1.setGeometry(100, 200, 0, 0)
        tab2Frame1.setLineWidth(1)

        # add widgets into tab2
        grid2 = QGridLayout()
        grid2.setSpacing(5)
        grid2.setColumnMinimumWidth(0, 1)
        grid2.setColumnMinimumWidth(2, 1)
        grid2.setColumnMinimumWidth(3, 1)
        grid2.setColumnMinimumWidth(5, 1)
        grid2.addWidget(tab2Frame1, 0, 0, 5, 7)
        grid2.addWidget(btnNextFrame, 1, 1)
        grid2.addWidget(btnPrevFrame, 1, 2)
        grid2.addWidget(myParent.frameNumberLine, 2, 1)

        # complete tab2
        tab2.setLayout(grid2)

        ######################################################
        # create widgets for tab 3 (Line Display 1)
        ######################################################

        # check boxes
        myParent.cbHorizontalLineEnabled = QCheckBox('Plot Horizontal Line')
        #
        myParent.cbVerticalLineEnabled = QCheckBox('Plot Vertical Line')
        #
        myParent.cbpixelTimeSeriesEnabled = QCheckBox('Pixel Time Series Line')
        myParent.cbImageZoomEnabled = QCheckBox('Image zoom')

        # button save trace to file
        btnSaveSeriesToFile = QPushButton("Save to file")
        btnSaveSeriesToFile.setMaximumWidth(150)
        btnSaveSeriesToFile.clicked.connect(myParent.SaveSeriesToFile)
        btnSaveSeriesToFile.resize(btnSaveSeriesToFile.minimumSizeHint())

        # set layout to tab 3
        tab3Frame1 = QFrame()
        tab3Frame1.setFrameStyle(QFrame.Panel)
        tab3Frame1.setGeometry(100, 200, 0, 0)
        tab3Frame1.setLineWidth(1)

        # add widgets into tab2
        grid3 = QGridLayout()
        grid3.setSpacing(5)
        grid3.setColumnMinimumWidth(0, 1)
        grid3.setColumnMinimumWidth(2, 1)
        grid3.setColumnMinimumWidth(3, 1)
        grid3.setColumnMinimumWidth(5, 1)
        grid3.addWidget(tab3Frame1, 0, 0, 5, 7)
        grid3.addWidget(myParent.cbHorizontalLineEnabled, 1, 1)
        grid3.addWidget(myParent.cbVerticalLineEnabled, 2, 1)
        grid3.addWidget(myParent.cbpixelTimeSeriesEnabled, 3, 1)
        grid3.addWidget(myParent.cbImageZoomEnabled, 1, 3)
        grid3.addWidget(btnSaveSeriesToFile, 4, 1)

        # complete tab3
        tab3.setLayout(grid3)

        ######################################################
        # create widgets for tab 4 (Line display 2)
        ######################################################

        # radio buttons
        # http://www.tutorialspoint.com/pyqt/pyqt_qradiobutton_widget.htm
        myParent.LinePlot2_RB1 = QRadioButton("Scope")
        myParent.LinePlot2_RB1.setChecked(True)
        myParent.LinePlot2_RB2 = QRadioButton("Env. Monitoring")

        # button save trace to file
        btnSaveMonitoringSeriesToFile = QPushButton("Save to file")
        btnSaveMonitoringSeriesToFile.setMaximumWidth(150)
        btnSaveMonitoringSeriesToFile.clicked.connect(myParent.SaveMonitoringSeriesToFile)
        btnSaveMonitoringSeriesToFile.resize(btnSaveMonitoringSeriesToFile.minimumSizeHint())

        # check boxes
        myParent.cbScopeCh0 = QCheckBox('Channel 0')
        myParent.cbScopeCh1 = QCheckBox('Channel 1')
        #
        myParent.cbEnvMonCh0 = QCheckBox('Strong back temp.')
        myParent.cbEnvMonCh1 = QCheckBox('Ambient temp.')
        myParent.cbEnvMonCh2 = QCheckBox('Relative Hum.')
        myParent.cbEnvMonCh3 = QCheckBox('ASIC (A.) current (mA)')
        myParent.cbEnvMonCh4 = QCheckBox('ASIC (D.) current (mA)')
        myParent.cbEnvMonCh5 = QCheckBox('Guard ring current (uA)')
        myParent.cbEnvMonCh6 = QCheckBox('Vcc_a (mV)')
        myParent.cbEnvMonCh7 = QCheckBox('Vcc_d (mV)')

        # set layout to tab 3
        tab4Frame1 = QFrame()
        tab4Frame1.setFrameStyle(QFrame.Panel)
        tab4Frame1.setGeometry(100, 200, 0, 0)
        tab4Frame1.setLineWidth(1)

        # add widgets into tab2
        grid4 = QGridLayout()
        grid4.setSpacing(5)
        grid4.setColumnMinimumWidth(0, 1)
        grid4.setColumnMinimumWidth(2, 1)
        grid4.setColumnMinimumWidth(3, 1)
        grid4.setColumnMinimumWidth(5, 1)
        grid4.addWidget(tab4Frame1, 0, 0, 7, 7)
        grid4.addWidget(myParent.LinePlot2_RB1, 1, 1)
        grid4.addWidget(myParent.cbScopeCh0, 2, 1)
        grid4.addWidget(myParent.cbScopeCh1, 3, 1)
        grid4.addWidget(myParent.LinePlot2_RB2, 1, 3)
        grid4.addWidget(myParent.cbEnvMonCh0, 2, 3)
        grid4.addWidget(myParent.cbEnvMonCh1, 3, 3)
        grid4.addWidget(myParent.cbEnvMonCh2, 4, 3)
        grid4.addWidget(myParent.cbEnvMonCh3, 5, 3)
        grid4.addWidget(myParent.cbEnvMonCh4, 2, 4)
        grid4.addWidget(myParent.cbEnvMonCh5, 3, 4)
        grid4.addWidget(myParent.cbEnvMonCh6, 4, 4)
        grid4.addWidget(myParent.cbEnvMonCh7, 5, 4)
        grid4.addWidget(btnSaveMonitoringSeriesToFile, 6, 1)

        # complete tab4
        tab4.setLayout(grid4)

        # Add tabs
        self.addTab(tab1, "Main")
        self.addTab(tab2, "File controls")
        self.addTab(tab3, "Line Display 1")
        self.addTab(tab4, "Line Display 2")

        self.setGeometry(300, 300, 300, 150)
        self.setWindowTitle('')
        self.show()
