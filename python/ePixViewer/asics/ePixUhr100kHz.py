import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from ePixViewer import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

class DataReceiverEpixUHR100kHz(DataReceiverBase):
    def __init__(self, numClusters, **kwargs):
        super().__init__(192, 168, numClusters, **kwargs)

        numLanes                = 16
        self.framePixelRow      = numClusters*12
        self.framePixelColumn   = numLanes*12
        numPixels               = int(self.framePixelRow * self.framePixelColumn)
        self.lane_map           = self.lane_map(numClusters, numLanes, numPixels)

    def read_uint12(self,data_chunk):
        #https://stackoverflow.com/questions/44735756/python-reading-12-bit-binary-files
        fst_uint8, mid_uint8, lst_uint8 = np.reshape(data_chunk, (data_chunk.shape[0] // 3, 3)).astype(np.uint16).T
        fst_uint12 = (fst_uint8 << 4) + (mid_uint8 >> 4)
        snd_uint12 = ((mid_uint8 % 16) << 8) + lst_uint8
        return np.reshape(np.concatenate((fst_uint12[:, None], snd_uint12[:, None]), axis=1), 2 * fst_uint12.shape[0])

    def lane_map(self, numClusters, numLanes, numPixels):
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
        for cluster_n in range (numClusters):
            column_map = np.append(column_map , (numClusters*cluster_map) + cluster_n)

        #cast column_map to int
        column_map=column_map.astype(int)

        #create the cluster_columns_map
        lane_map = np.concatenate([np.reshape(column_map*2,(int(12*numClusters),6)),np.reshape((column_map*2)+1,(int(12*numClusters),6))],axis =1 )
        lane_map = np.flip(lane_map,1)

        #re-linearize the cluster_columns_map
        lane_map = np.reshape(lane_map, int(numPixels/numLanes))
        
        return lane_map

    def frame_reorder(self,input_frame,lane_map, numLanes):
        frame= np.empty([self.framePixelRow,1])
        frame.fill(np.nan)

        for lane_n in range (numLanes):
            #taking one lane at the time
            frame_tmp = input_frame[lane_n,1:]
            #using the map
            lane_tmp = frame_tmp[lane_map]
            #reshape
            lane_tmp = np.reshape(lane_tmp, (self.framePixelRow,12))
            frame = np.concatenate([frame,lane_tmp],axis =1)

        return frame[np.logical_not(np.isnan(frame))]    

    
    def descramble(self, frame):
        #Intial setting
        numLanes                = 16 
        numPixels               = int(self.framePixelRow * self.framePixelColumn)
        frameSize               = (int(numPixels/numLanes)+1)* 24
        gainMSB                 = self.GainMSB.get()

        #create the frames
        current_frame_temp  = np.zeros((self.framePixelRow, self.framePixelColumn), dtype=int)
        rawData_12bit       = np.empty((numLanes,int(numPixels/numLanes)+1), dtype=int)

        #get the frames from the stream
        rawData_8bit = frame.getNumpy(0, frame.getPayload()).view(np.uint8)
        rawData_8bit = np.reshape(rawData_8bit[16:frameSize+16],(int(numPixels/numLanes)+1,24))
        rawData_8bit = np.flip(rawData_8bit,1).T

        #parse the 8bit chunks into the 12bit
        for j in range (int(numPixels/numLanes)+1):
            rawData_12bit[:,j] = self.read_uint12(rawData_8bit[:,j])

        #use the map to filter the pixels
        frame = self.frame_reorder(rawData_12bit, self.lane_map, numLanes)
        frame = np.reshape(frame, (self.framePixelRow,self.framePixelColumn))
        frame = frame.astype(int)

        current_frame_temp = np.flip(np.flip(frame,0),1)

        if gainMSB:
            current_frame_temp = np.where(current_frame_temp % 2 == 0, current_frame_temp // 2, (current_frame_temp - 1) // 2 + 2048)

        return np.bitwise_and(current_frame_temp, self.PixelBitMask.get())