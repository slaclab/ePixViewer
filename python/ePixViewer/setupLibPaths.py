#-----------------------------------------------------------------------------
# This file is part of the 'Simple-PGPv4-KCU105-Example'. It is subject to
# the license terms in the LICENSE.txt file found in the top-level directory
# of this distribution and at:
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
# No part of the 'Simple-PGPv4-KCU105-Example', including this file, may be
# copied, modified, propagated, or distributed except according to the terms
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------
import pyrogue as pr
import os

top_level_arr = os.path.realpath(__file__).split('/')[:-1]
top_level = '/'.join(top_level_arr) + '/'

pr.addLibraryPath(top_level+'../')
#pr.addLibraryPath(top_level+'./ePixViewer/python')
