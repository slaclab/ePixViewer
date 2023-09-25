# epix-viewer
Viewer for ePix readouts

## Usage

The follwing section describes how to use the different features available in the ePixViewer repository.
In order to use this module, you must:

1. Add the git submodule to your project
2. Create your _Root.py script 
3. Implement the Viewers you want and connect them as described bellow

### Image viewer

1. Import the device of your choice (e.g.: ePixHr10K2M) in your _Root.py script
    ```python
    from ePixViewer.software.deviceFiles import ePixHr10k2M
    ```
2. Set numOfLanes (number of lanes) variable:
    ```python
    self.numOfLanes = 5
    ```
3. Prepare variables to connect AXI streams
    ```python
    self.dataStream    = [None for i in range(self.numOfLanes)]
    
    #Create rateDrop and Unbarcher if needed
    self.rate          = [rogue.interfaces.stream.RateDrop(True, 0.1) for i in range(self.numOfLanes)]
    self.unbatchers    = [rogue.protocols.batcher.SplitterV1() for lane in range(self.numOfLanes)]
    ```
4. Instantiate and connect dataReceiver following the example bellow
    ```python
    for lane in range(self.numOfLanes):
        #Connect data stream
        if not self.sim:
            self.dataStream[lane] = rogue.hardware.axi.AxiStreamDma(dev,0x100*lane+0,1)
        else:
            self.dataStream[lane] = rogue.interfaces.stream.TcpClient('localhost',24002+2*lane)
            
        self.add(ePixHr10k2M.DataReceiverEpixHr10k2M(name = f"DataReceiver{lane}"))
        self.dataStream[lane] >> self.rate[lane] >> self.unbatchers[lane] >> getattr(self, f"DataReceiver{lane}")
   ```
   
> The python code is used to illustrate. Neverthless, a few parameters have to be customized for your own setup:
>    1. `ePixHr10k2M.DataReceiverEpixHr10k2M`: depends on the device you connects
>    2. The use of rateDrop and Unbatchers depend on your firmware implementation
>    3. Addresses might vary depending on your design
   
### Scope viewer

1. Import the ScopeDataReceiver files in your _Root.py script
    ```python
    from ePixViewer.software import ScopeDataReceiver
    ```
2. Set numOfScopes (number of scopes) variable:
    ```python
    self.numOfScopes = 4
    ```
3. Prepare variables to connect AXI Streams
    ```python
    self.oscopeStream  = [None for i in range(self.numOfScopes)]
    ```
2. Instantiate and connect scopeDataReceiver:
    ```python
    for vc in range(self.numOfScopes):
        if not self.sim:
            self.oscopeStream[vc] = rogue.hardware.axi.AxiStreamDma(dev,0x100*6+vc,1)
        else:
            self.oscopeStream[vc] = rogue.interfaces.stream.TcpClient('localhost',24024+2*vc)
            
        self.add(ScopeDataReceiver(name = f"ScopeData{vc}"))
        self.oscopeStream[vc] >> getattr(self, f"ScopeData{vc}")
    ```

### Env viewer

1. Import the ScopeDataReceiver files in your _Root.py script
    ```python
    from ePixViewer.software import EnvDataReceiver
    ```
2. Set numOfAdcmons (number of environment ADCs) variable:
    ```python
    self.numOfAdcmons = 4
    ```
3. Prepare variables to connect AXI Streams
    ```python
    self.adcMonStream  = [None for i in range(self.numOfAdcmons)]
    ```
4. Configure the channels
    ```python
    envConf = [
        [
            {   'id': 0, 'name': 'Therm 0 (deg. C)',      'conv': lambda data: -68.305*data+93.308, 'color': '#FFFFFF'  },
            {   'id': 1, 'name': 'Therm 1 (deg. C)',      'conv': lambda data: -68.305*data+93.308, 'color': '#FF00FF' },
            {   'id': 2, 'name': 'Analog VIN (volts)',    'conv': lambda data: data, 'color': '#00FFFF'  },
            {   'id': 3, 'name': 'ASIC C0 AVDD (Amps)',   'conv': lambda data: data, 'color': '#FFFF00'  },
            {   'id': 4, 'name': 'ASIC C0 DVDD (Amps)',   'conv': lambda data: data, 'color': '#F0F0F0'  },
            {   'id': 5, 'name': 'ASIC C1 AVDD (Amps)',   'conv': lambda data: data, 'color': '#F0500F'  },
            {   'id': 6, 'name': 'ASIC C1 DVDD (Amps)',   'conv': lambda data: data, 'color': '#503010'  },
            {   'id': 7, 'name': 'ASIC C2 AVDD (Amps)',   'conv': lambda data: data, 'color': '#777777'  }
        ],
        [
            {   'id': 0, 'name': 'Therm 2 (deg. C)',      'conv': lambda data: -68.305*data+93.308, 'color': '#FFFFFF'  },
            {   'id': 1, 'name': 'Therm 3 (deg. C)',      'conv': lambda data: -68.305*data+93.308, 'color': '#FF00FF' },
            {   'id': 2, 'name': 'ASIC C2 DVDD (Amps)',   'conv': lambda data: data, 'color': '#00FFFF'  },
            {   'id': 3, 'name': 'ASIC C3 DVDD (Amps)',   'conv': lambda data: data, 'color': '#FFFF00'  },
            {   'id': 4, 'name': 'ASIC C3 AVDD (Amps)',   'conv': lambda data: data, 'color': '#F0F0F0'  },
            {   'id': 5, 'name': 'ASIC C4 DVDD (Amps)',   'conv': lambda data: data, 'color': '#F0500F'  },
            {   'id': 6, 'name': 'ASIC C4 AVDD (Amps)',   'conv': lambda data: data, 'color': '#503010'  },
            {   'id': 7, 'name': 'Humidity (%)',          'conv': lambda data: 45.8*data-21.3, 'color': '#777777'  }
        ],
        [
            {   'id': 0, 'name': 'Therm 4 (deg. C)',      'conv': lambda data: -68.305*data+93.308, 'color': '#FFFFFF'  },
            {   'id': 1, 'name': 'Therm 5 (deg. C)',      'conv': lambda data: -68.305*data+93.308, 'color': '#FF00FF' },
            {   'id': 2, 'name': 'ASIC C0 V2 5A (volts)', 'conv': lambda data: data, 'color': '#00FFFF'  },
            {   'id': 3, 'name': 'ASIC C1 V2 5A (volts)', 'conv': lambda data: data, 'color': '#FFFF00'  },
            {   'id': 4, 'name': 'ASIC C2 V2 5A (volts)', 'conv': lambda data: data, 'color': '#F0F0F0'  },
            {   'id': 5, 'name': 'ASIC C3 V2 5A (volts)', 'conv': lambda data: data, 'color': '#F0500F'  },
            {   'id': 6, 'name': 'ASIC C4 V2 5A (volts)', 'conv': lambda data: data, 'color': '#503010'  },
            {   'id': 7, 'name': 'Digital VIN (volts)',   'conv': lambda data: data, 'color': '#777777'  }
        ],
        [
            {   'id': 0, 'name': 'Therm dig. 0 (deg. C)', 'conv': lambda data: -68.305*(data)+93.308, 'color': '#FFFFFF'  },
            {   'id': 1, 'name': 'Therm dig. 1 (deg. C)', 'conv': lambda data: -68.305*(data)+93.308, 'color': '#FF00FF' },
            {   'id': 2, 'name': 'Humidity dig. (%)',     'conv': lambda data: data*45.8-21.3, 'color': '#00FFFF'  },
            {   'id': 3, 'name': '1V8 (volts)',           'conv': lambda data: data, 'color': '#FFFF00'  },
            {   'id': 4, 'name': '2V5 (volts)',           'conv': lambda data: data, 'color': '#F0F0F0'  },
            {   'id': 5, 'name': 'Vout 6V 10A (Amps)',    'conv': lambda data: 10*data, 'color': '#F0500F'  },
            {   'id': 6, 'name': 'Mon VCC (volts)',       'conv': lambda data: data, 'color': '#503010'  },
            {   'id': 7, 'name': 'Raw voltage (volts)',   'conv': lambda data: 3* data, 'color': '#777777'  }
        ]
    ]
    ```
2. Instantiate and connect EnvDataReceiver:
    ```python
    for vc in range(self.numOfScopes):
        if not self.sim:
            self.adcMonStream[vc] = rogue.hardware.axi.AxiStreamDma(dev,0x100*6+vc,1)
        else:
            self.adcMonStream[vc] = rogue.interfaces.stream.TcpClient('localhost',24016+2*vc)
            
        self.add(
            EnvDataReceiver(
                config = envConf[vc], 
                clockT = 6.4e-9, 
                rawToData = lambda raw: (2.5 * float(raw & 0xffffff)) / 16777216, 
                name = f"EnvData{vc}"
            )
        )
        self.adcMonStream[vc] >> getattr(self, f"EnvData{vc}")
    ```

