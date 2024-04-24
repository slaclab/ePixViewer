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

    def read_uint12(self,data_chunk):
        #https://stackoverflow.com/questions/44735756/python-reading-12-bit-binary-files
        fst_uint8, mid_uint8, lst_uint8 = np.reshape(data_chunk, (data_chunk.shape[0] // 3, 3)).astype(np.uint16).T
        fst_uint12 = (fst_uint8 << 4) + (mid_uint8 >> 4)
        snd_uint12 = ((mid_uint8 % 16) << 8) + lst_uint8
        return np.reshape(np.concatenate((fst_uint12[:, None], snd_uint12[:, None]), axis=1), 2 * fst_uint12.shape[0])

    def lane_map_uhr100(self):
        column_map = []
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

        #re-linearize the cluster_map
        cluster_map = np.reshape(cluster_map, 72)

        #create the column map
        for cluster_n in range (14):
            column_map = np.append(column_map , (14*cluster_map) + cluster_n)

        #cast column_map to int
        column_map=column_map.astype(int)

        #create the cluster_columns_map
        lane_map = np.concatenate([np.reshape(column_map*2,(168,6)),np.reshape((column_map*2)+1,(168,6))],axis =1 )

        #re-linearize the cluster_columns_map
        lane_map = np.reshape(lane_map, 2016)
        
        return lane_map

    def descramble(self, frame):
        #Intial setting
        frameSize               = 48400
        gainMSB                 = self.GainMSB.get()

        #create the frames
        full_frame          = np.empty((168,192), dtype=int)
        full_frame_12bit    = np.empty((1008,32), dtype=int)

        #get the frames from the stream
        rawData_8bit = frame.getNumpy(0, frame.getPayload()).view(np.uint8)
        # I remove the first 8 bytes that are trash. we should have 48384 bytes: 168*192*12 bit/8bit
        # each of the 8 columns represents one of the lanes
        rawData_8bit = np.reshape(rawData_8bit[16:frameSize],(6048,8))


        for lanes in range(8):
            lane_48bit = np.empty((1008,6))
            lane_12bit = np.empty((1008,4), dtype='int')
            #I am going back to the 64 bit
            lane_raw = rawData_8bit[:,lanes]
            lane_64bit = np.flip(np.reshape(lane_raw, (756,8)),1)
            # now each row is the output of the 48:64 gearbox.
            for i in range(252):
                lane_48bit[0+i*4,0:6]=lane_64bit[0+i*3,2:8]
                lane_48bit[1+i*4,0:4]=lane_64bit[1+i*3,4:8]
                lane_48bit[1+i*4,4:6]=lane_64bit[0+i*3,0:2]
                lane_48bit[2+i*4,0:2]=lane_64bit[2+i*3,6:8]
                lane_48bit[2+i*4,2:8]=lane_64bit[1+i*3,0:4]
                lane_48bit[3+i*4,0:6]=lane_64bit[2+i*3,0:6]
            
            #now we need to shift from 8bit per entry to 12bit per entry
            for j in range (1008):
                lane_12bit[j,:] = self.read_uint12(lane_48bit[j,:])
                
            lane_12bit = np.flip(lane_12bit,1)
            full_frame_12bit[:,lanes*4:(lanes*4)+4] = lane_12bit


        for columns in range(16):
            slice_lane = full_frame_12bit[:,columns*2:(columns*2)+2]
            slice_lane = np.reshape(slice_lane, 2016)
            a = self.lane_map_uhr100()

            column_tmp = slice_lane[a]
            column_tmp = np.flip(np.reshape(column_tmp, (168,12)),0)
            
            full_frame[:,columns*12:(columns*12)+12] = column_tmp

        if gainMSB:
            full_frame = np.where(full_frame % 2 == 0, full_frame // 2, (full_frame - 1) // 2 + 2048)

        return full_frame
