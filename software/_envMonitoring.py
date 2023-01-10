import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from ePixViewer.software._dataReceiver._dataReceiver import DataReceiverBase
import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy


class DataReceiverEnvMonitoring(pr.DataReceiver):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add(pr.LocalVariable(
            name = "StrongBackTemp",
            value = 0,
            description = "Strong back temperature"
        ))
        self.add(pr.LocalVariable(
            name = "AmbientTemp",
            value = 0,
            description = "Ambient temperature"
        ))
        self.add(pr.LocalVariable(
            name = "RelativeHum",
            value = 0,
            description = "Relative humidity"
        ))
        self.add(pr.LocalVariable(
            name = "ASICACurrent",
            value = 0,
            description = "ASIC (A.) current (mA)"
        ))
        self.add(pr.LocalVariable(
            name = "ASICDCurrent",
            value = 0,
            description = "ASIC (D.) current (mA)"
        ))
        self.add(pr.LocalVariable(
            name = "GuardRingCurrent",
            value = 0,
            description = "Guard ring current (uA)"
        ))
        self.add(pr.LocalVariable(
            name = "VccA",
            value = 0,
            description = "Vcc_a (mV)"
        ))
        self.add(pr.LocalVariable(
            name = "VccD",
            value = 0,
            description = "Vcc_d (mV)"
        ))

    def process(self, frame):
        with self.root.updateGroup():
            rawData = bytearray(frame.getPayload())
            frame.read(rawData, 0)
            envData = np.zeros((8,1), dtype='int32')
            for j in range(0,32):
                rawData.pop(0)
            for j in range(0,8):
                envData[j] = int.from_bytes(rawData[j*4:(j+1)*4], byteorder='little')
            envData[0] = envData[0] / 100
            envData[1] = envData[1] / 100
            envData[2] = envData[2] / 100
            self.StrongBackTemp.set(int(envData[0]), write = True)
            self.AmbientTemp.set(int(envData[1]), write = True)
            self.RelativeHum.set(int(envData[2]), write = True)
            self.ASICACurrent.set(int(envData[3]), write = True)
            self.ASICDCurrent.set(int(envData[4]), write = True)
            self.GuardRingCurrent.set(int(envData[5]), write = True)
            self.VccA.set(int(envData[6]), write = True)
            self.VccD.set(int(envData[7]), write = True)
            self.Updated.set(True, write = True)