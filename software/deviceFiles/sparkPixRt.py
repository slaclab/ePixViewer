import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from ePixViewer.software._dataReceiver import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

class DataReceiverSparkPixRt(DataReceiverBase):
    def __init__(self, numClusters, **kwargs):
        super().__init__(48, 48,numClusters,  **kwargs)

        self.framePixelRow = 48
        self.framePixelColumn = 48
        self.counter = 0
        self.row_map = self.row_map_RT()

    def read_uint12(self,data_chunk):
        #https://stackoverflow.com/questions/44735756/python-reading-12-bit-binary-files
        fst_uint8, mid_uint8, lst_uint8 = np.reshape(data_chunk, (data_chunk.shape[0] // 3, 3)).astype(np.uint16).T
        fst_uint12 = (fst_uint8 << 4) + (mid_uint8 >> 4)
        snd_uint12 = ((mid_uint8 % 16) << 8) + lst_uint8
        return np.reshape(np.concatenate((fst_uint12[:, None], snd_uint12[:, None]), axis=1), 2 * fst_uint12.shape[0])

    def row_map_RT(self):
        row_map = np.empty([12,48])
        row_map.fill(np.nan)
        cluster_map = np.empty(72)
        
        #create the sp map
        sp_map = np.array([0,1,2,3,4,5,6,7,8])
        
        # create the cluster map
        for index in range (72):
            cluster_map[index] = index
            
        #cast cluster_map to int
        cluster_map=cluster_map.astype(int)
        
        #split the cluster in the 2 sp columns
        cluster_map = np.concatenate([np.reshape(cluster_map [0:len(cluster_map)//2], (12,3)), np.flip(np.reshape(cluster_map [len(cluster_map)//2:], (12,3)),1)],axis =1 )
        
        # re-linearize the cluster_map
        cluster_map = np.reshape(cluster_map, (12,6))
        
        #create the row map
        for lanes_n in range (8):
            row_map = np.concatenate([row_map,8*(cluster_map) + lanes_n],axis =1)
            
        return row_map[np.logical_not(np.isnan(row_map))]

    def row_reorder_RT(self,input_frame,row_map):  
        frame_map = []
        for rows in range (4):
            #taking one lane at the time
            frame_tmp = input_frame[3-rows,3:]
            #using the map
            row_map=row_map.astype(int)
            frame_tmp = frame_tmp[row_map]
            #
            frame_map = np.append(frame_map , frame_tmp)
        return frame_map  

    
    def descramble(self, frame):
        # print('Debug: Frame counter {}'.format(self.counter))
        # self.counter = self.counter + 1
        gainMSB                 = self.GainMSB.get()
        
        #create the frames
        current_frame_temp = np.zeros((self.framePixelRow, self.framePixelColumn), dtype=int)
        rawData_12bit = np.empty((4,579), dtype=int)

        #get the frames from the stream
        rawData_8bit = frame.getNumpy(0, frame.getPayload()).view(np.uint8)
        rawData_8bit = np.reshape(rawData_8bit[16:3490],(579,6))
        rawData_8bit = np.flip(rawData_8bit,1).T

        #parse the 8bit chunks into the 12bit
        for j in range (579):
            rawData_12bit[:,j] = self.read_uint12(rawData_8bit[:,j])

        #use the map to filter the pixels
        frame = self.row_reorder_RT(rawData_12bit, self.row_map)
        frame = np.reshape(frame, (48,48))
        frame = frame.astype(int)

        current_frame_temp = np.flip(frame,0)

        if gainMSB:
            current_frame_temp = np.where(current_frame_temp % 2 == 0, current_frame_temp // 2, (current_frame_temp - 1) // 2 + 2048)


        return np.bitwise_and(current_frame_temp, self.PixelBitMask.get())