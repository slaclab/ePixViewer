import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from ePixViewer import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

class DataReceiverEpixUHRMHzMode(DataReceiverBase):
    def __init__(self, **kwargs):
        super().__init__(56, 64, **kwargs)

        self.framePixelRow = 56
        self.framePixelColumn = 64
        self.counter = 0
        self.lane_map_MHz = self.lane_map_MHz()

    def read_uint12(self,data_chunk):
        #https://stackoverflow.com/questions/44735756/python-reading-12-bit-binary-files
        fst_uint8, mid_uint8, lst_uint8 = np.reshape(data_chunk, (data_chunk.shape[0] // 3, 3)).astype(np.uint16).T
        fst_uint12 = (fst_uint8 << 4) + (mid_uint8 >> 4)
        snd_uint12 = ((mid_uint8 % 16) << 8) + lst_uint8
        return np.reshape(np.concatenate((fst_uint12[:, None], snd_uint12[:, None]), axis=1), 2 * fst_uint12.shape[0])

    def lane_map_MHz(self):
        column_map = []
        cluster_map = np.empty(8)
        
        #create the cluster map
        for index in range (8):
            cluster_map[index] = index
        #cast cluster_map to int
        cluster_map=cluster_map.astype(int)
        
        #split the cluster in the 2 sp columns
        cluster_map = np.concatenate([np.reshape(cluster_map [0:len(cluster_map)//2], (4,1)),np.reshape(cluster_map [len(cluster_map)//2:], (4,1))],axis =1 )
        
        #re-linearize the cluster_map
        cluster_map = np.reshape(cluster_map, 8)
        
        #create the column map
        for cluster_n in range (14):
            column_map = np.append(column_map , (14*cluster_map) + cluster_n)
        
        #cast column_map to int
        column_map=column_map.astype(int)
        
        #create the cluster_columns_map
        lane_map = np.concatenate([np.reshape(column_map*2,(56,2)),np.reshape((column_map*2)+1,(56,2))],axis =1 )
        
        #re-linearize the cluster_columns_map
        lane_map = np.reshape(lane_map, 224)
        
        return lane_map

    def frame_reorder_MHz(self,input_frame,lane_map):
        frame= np.empty([56,1])
        frame.fill(np.nan)
        for lane_n in range (16):
            #taking one lane at the time
            frame_tmp = input_frame[lane_n,1:]
            #using the map
            lane_tmp = frame_tmp[lane_map]
            #reshape
            lane_tmp = np.reshape(lane_tmp, (56,4))
            frame = np.concatenate([frame,lane_tmp],axis =1)
        return frame[np.logical_not(np.isnan(frame))] 

    
    def descramble(self, frame):
        #create the frames
        current_frame_temp = np.zeros((self.framePixelRow, self.framePixelColumn), dtype=int)
        rawData_12bit = np.empty((16,225), dtype=int)

        #get the frames from the stream
        rawData_8bit = frame.getNumpy(0, frame.getPayload()).view(np.uint8)
        rawData_8bit = np.reshape(rawData_8bit[16:5416],(225,24))
        rawData_8bit = np.flip(rawData_8bit,1).T

        #parse the 8bit chunks into the 12bit
        for j in range (225):
            rawData_12bit[:,j] = self.read_uint12(rawData_8bit[:,j])

        #use the map to filter the pixels
        frame = self.frame_reorder_MHz(rawData_12bit, self.lane_map_MHz)
        frame = np.reshape(frame, (56,64))
        frame = frame.astype(int)

        current_frame_temp = np.flip(frame,0)

        return np.bitwise_and(current_frame_temp, self.PixelBitMask.get())