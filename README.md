# epix-viewer
Viewer for ePix readouts

## Usage

1. Add the git submodule to the project
2. Add the DataReceiver/Pseudoscope/EnvMonitor to the Root Class

    ```
    self.add(epix_viewer.dataReceivers.DataReceiverEpixUHR(name = f"DataReceiver0"))
    self.add(epix_viewer.dataReceivers.DataReceiverPseudoScope(name = f"Pseudoscope0"))
    self.add(epix_viewer.dataReceivers.DataReceiverEnvMonitoring(name = f"EnvMonitor0"))
    ```

3. Setup RateDrop object. this is needed for the data and enviroment monitor streams

    `self.rate = rogue.interfaces.stream.RateDrop(True,0.1)`

4. The calls to the run the displays can be added to the register tree with subprocess

    ```
    @self.command()
    def DisplayViewer():
        subprocess.call(['scripts/runLiveDisplay.py --dataReceiver rogue://0/root.DataReceiver0 image &'], shell=True)
    @self.command()
    def DisplayPseudoScope():
        subprocess.call(['scripts/runLiveDisplay.py --dataReceiver rogue://0/root.Pseudoscope0 pseudoscope &'], shell=True)
    @self.command()
    def DisplayEnvMonitor():
        subprocess.call(['scripts/runLiveDisplay.py --dataReceiver rogue://0/root.EnvMonitor0 monitor &'], shell=True)
    ```   