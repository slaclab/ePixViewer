#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Title      : Script for running live display
#-----------------------------------------------------------------------------
# File       : runLiveDisplay.py
# Author     : Jaeyoung (Daniel) Lee
# Created    : 2022-07-28
# Last update: 2022-07-28
#-----------------------------------------------------------------------------
# Description:
# Script for running live display
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
top_level = f'{os.getcwd()}/' 
import setupLibPaths
import argparse
import pyrogue.pydm
import sys

from ePixViewer.software import *


parser = argparse.ArgumentParser('Pyrogue Client')

parser.add_argument('--serverList',
                    type=str,
                    help="Server address: 'host:port' or list of addresses: 'host1:port1,host2:port2'",
                    default='localhost:9099')

parser.add_argument('--dataReceiver',
                    type=str,
                    help='Rogue Data Receiver path string',
                    default=None)

parser.add_argument('--title',
                    type=str,
                    default=None,
                    help='Title of display')

parser.add_argument('cmd',
                    type=str,
                    choices=['image','pseudoscope','monitor'],
                    help='Client command to issue')

parser.add_argument('--sizeY',
                    type=int,
                    default=1000,
                    help='Rows of image')

parser.add_argument('--sizeX',
                    type=int,
                    default=800,
                    help='Columns of image')

args = parser.parse_args()

if args.cmd == 'image':
    runReceiverDisplay(dataReceiver=args.dataReceiver, serverList=args.serverList, title=args.title, sizeY=args.sizeY, sizeX=args.sizeX)
elif args.cmd == 'monitor':
    runMonitorDisplay(dataReceiver=args.dataReceiver, serverList=args.serverList)
elif args.cmd == 'pseudoscope':
    runScopeDisplay(dataReceiver=args.dataReceiver, serverList=args.serverList)



#ePixLiveDisplay.runEpixDisplay(serverList='localhost:9099', ui='/u/gu/jaeylee/epix-hr-single-10k/software/python/ePixViewer/ePixGUIEnvMonitoring.py')