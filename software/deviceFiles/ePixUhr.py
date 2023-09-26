import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from ePixViewer.software._dataReceiver import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

class DataReceiverEpixUHR(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(168, 192, **kwargs)

        self.framePixelRow = 168
        self.framePixelColumn = 192
        self.counter = 0
        self.lane_map = self.lane_map()

    def read_uint12(self,data_chunk):
        #https://stackoverflow.com/questions/44735756/python-reading-12-bit-binary-files
        fst_uint8, mid_uint8, lst_uint8 = np.reshape(data_chunk, (data_chunk.shape[0] // 3, 3)).astype(np.uint16).T
        fst_uint12 = (fst_uint8 << 4) + (mid_uint8 >> 4)
        snd_uint12 = ((mid_uint8 % 16) << 8) + lst_uint8
        return np.reshape(np.concatenate((fst_uint12[:, None], snd_uint12[:, None]), axis=1), 2 * fst_uint12.shape[0])

    def lane_map(self):
        column_map = []
        cluster_map = np.empty(72)
        #create the sp map
        sp_map = np.array([0,3,6,1,4,7,2,5,8])

        #create the cluster map
        for index in range (8):
            cluster_map[sp_map+(index*9)] = range(index,65+index,8)

        #cast cluster_map to int
        cluster_map=cluster_map.astype(int)

        #split the cluster in the 2 sp columns
        cluster_map = np.concatenate([np.reshape(cluster_map [0:len(cluster_map)//2], (12,3)),np.flip(np.reshape(cluster_map [len(cluster_map)//2:], (12,3)),1)],axis =1 )

        #re-linearize the cluster_map
        cluster_map = np.reshape(cluster_map, 72)

        #create the column map
        for cluster_n in range (14):
            column_map = np.append(column_map , (14*cluster_map) + cluster_n)

        #cast column_map to int
        column_map=column_map.astype(int)

        #create the cluster_columns_map
        lane_map = np.concatenate([np.reshape(column_map*2,(168,6)),np.reshape((column_map*2)+1,(168,6))],axis =1 )

        lane_map = np.flip(lane_map,1)

        #re-linearize the cluster_columns_map
        lane_map = np.reshape(lane_map, 2016)
        
        return lane_map

    def frame_reorder(self,input_frame,lane_map):
        frame= np.empty([168,1])
        frame.fill(np.nan)

        for lane_n in range (16):
            #taking one lane at the time
            frame_tmp = input_frame[lane_n,1:]
            #using the map
            lane_tmp = frame_tmp[lane_map]
            #reshape
            lane_tmp = np.reshape(lane_tmp, (168,12))
            frame = np.concatenate([frame,lane_tmp],axis =1)

        return frame[np.logical_not(np.isnan(frame))]    

    
    def descramble(self, frame):
        # print('Debug: Frame counter {}'.format(self.counter))
        # self.counter = self.counter + 1
        
        #create the frames
        current_frame_temp = np.zeros((self.framePixelRow, self.framePixelColumn), dtype=int)
        rawData_12bit = np.empty((16,2017), dtype=int)

        #get the frames from the stream
        rawData_8bit = frame.getNumpy(0, frame.getPayload()).view(np.uint8)
        rawData_8bit = np.reshape(rawData_8bit[16:48424],(2017,24))
        rawData_8bit = np.flip(rawData_8bit,1).T

        #parse the 8bit chunks into the 12bit
        for j in range (2017):
            rawData_12bit[:,j] = self.read_uint12(rawData_8bit[:,j])

        #use the map to filter the pixels
        frame = self.frame_reorder(rawData_12bit, self.lane_map)
        frame = np.reshape(frame, (168,192))
        frame = frame.astype(int)

        current_frame_temp = np.flip(np.flip(frame,0),1)

        return np.bitwise_and(current_frame_temp, self.PixelBitMask.get())