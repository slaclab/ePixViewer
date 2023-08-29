# epix-viewer
Viewer for ePix readouts

## Usage

1. Add the git submodule to the project
2. Add the DataReceiver/Pseudoscope/EnvMonitor to the Root Class

    ```
    self.add(DataReceiverEpixUHR(name = f"DataReceiver0"))
    self.add(DataReceiverPseudoScope(name = f"Pseudoscope0"))
    self.add(DataReceiverEnvMonitoring(name = f"EnvMonitor0"))
    ```

3. Setup RateDrop object. this is needed for the data and enviroment monitor streams

    ```
    self.rate = rogue.interfaces.stream.RateDrop(True,0.1)
    self.dmaStream[0][1] >> self.rate >> self.DataReceiver0    
    ```

4. The calls to the run the displays can be added to the register tree with subprocess

    ```
    @self.command()
        @self.command()
        def DisplayViewer0():
            subprocess.Popen(["python", <Full path to runLiveDisplay.py script>/runLiveDisplay.py", "--dataReceiver", "rogue://0/root.DataReceiver0", "image", "--title", "DataReceiver0", "--sizeY", "192", "--sizeX", "384"], shell=False)
    @self.command()
    def DisplayPseudoScope():
        subprocess.call(['<Full path to runLiveDisplay.py script>/runLiveDisplay.py --dataReceiver rogue://0/root.Pseudoscope0 pseudoscope &'], shell=True)
    @self.command()
    def DisplayEnvMonitor():
        subprocess.call(['<Full path to runLiveDisplay.py script>/runLiveDisplay.py --dataReceiver rogue://0/root.EnvMonitor0 monitor &'], shell=True)
    ```
