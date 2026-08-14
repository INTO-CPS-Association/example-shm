# User Guide

This guide outlines configuration and execution of the _example-shm_ application. It provides detailed information on the configuration parameters, command-line options, and execution procedures.

There are two ways to run the package, either directly from the repository code as a developer or as a build package. The latter is described further down in this file in section 2.


## 1. Run package with developer setup.

## Step 1.1 Initiate virtual enviroment with poetry

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # On Windows
source .venv/bin/activate        # On Linux

pip install poetry               #Specifically install poetry to your system
    # If you have poetry installed globally
    poetry env activate              # shows the command to activate venv
poetry install                   # installs all required python packages
```
## Step 1.2 Setup configuration file
config/ consist of a set of standard configuration files.
`production.json.template`          For general digital twin purposes
`replay.json.template`              For recording and replaying data
`replay_production.json.template`   For running function blocks with replayed data

Copy the needed config files and remove `.template` to use them.

Add MQTT connection information, credentials and topics.
For production purposes the MQTT topics structure follows the pattern:

```txt
cpsens/DAQ_ID/MODULE_ID/CH_ID/PHYSICS/ANALYSIS/DATA_TYPE
```
Where DATA_TYPE could be metadata or plain data.

## Step 1.3: Create Configuration

The package requires a json configuration file and access to MQTT broker.
The format of configuration file is,

```json
{
    "sysid": {
        "host": "",
        "port": 0,
        "userId": "",
        "password": "",
        "ClientID": "NOT_NEEDED",
        "QoS": 1,
        "SamplesToCollect": 2560,
        "MetadataToSubscribe":["sensors/1/acc/raw/metadata"],
        "TopicsToSubscribe": [
          "sensors/1/acc/raw/data",
          "sensors/2/acc/raw/data",
          "sensors/3/acc/raw/data",
          "sensors/4/acc/raw/data"
        ],
        "TopicsToPublish": ["sensors/1/acc/sysid/data"]
      },

    "mode_cluster": {
      "host": "",
      "port": 0,
      "userId": "",
        "password": "",
      "ClientID": "NOT_NEEDED",
      "QoS": 2,
      "TopicsToSubscribe": ["sensors/1/acc/sysid/data"],
      "TopicsToPublish": ["sensors/1/acc/mode_cluster/data"]
    },

    "model_update": {
      "host": "",
      "port": 0,
      "userId": "",
        "password": "",
      "ClientID": "NOT_NEEDED",
      "QoS": 2,
      "TopicsToSubscribe": ["sensors/1/acc/mode_cluster/data"],
      "TopicsToPublish": ["sensors/1/acc/model_update/data"]
    },

    "virtual_sensing": {
      "host": "",
      "port": 0,
      "userId": "",
        "password": "",
      "ClientID": "NOT_NEEDED",
      "QoS": 2,
      "SamplesToCollect": 2560,
      "MetadataToSubscribe":["sensors/1/acc/raw/metadata"],
      "TopicsToSubscribe": [
          "sensors/1/acc/raw/data",
          "sensors/2/acc/raw/data",
          "sensors/3/acc/raw/data",
          "sensors/4/acc/raw/data"
        ],
        "TopicsToPublish": ["sensors/1/acc/virtual_sensing/data"]
    },

    "stress": {
      "host": "",
      "port": 0,
      "userId": "",
        "password": "",
      "ClientID": "NOT_NEEDED",
      "QoS": 2,
      "TopicsToSubscribe": ["sensors/1/acc/virtual_sensing/data"],
      "TopicsToPublish": ["sensors/1/acc/stress/data"]
    },

    "fatigue": {
      "host": "",
      "port": 0,
      "userId": "",
        "password": "",
      "ClientID": "NOT_NEEDED",
      "QoS": 2,
      "TopicsToSubscribe": ["sensors/1/acc/stress/data"],
      "TopicsToPublish": []
    }
}
}
```
Where the MQTT topic structure follows the pattern:
`PROJECT/CH_ID/PHYSICS/ANALYSIS/DATA_TYPE`
Where `DATA_TYPE` could be metadata or plain data.

The file needs to be saved. The application looks for configuration in
`config/production.json`.


## Step 1.4 Change settings
There are some settings that can be changed for the specific use case.

* **Sample time**
This is how many samples should be used for sysid. The value uses the time in minutes and the sample frequency, fs,
to calculate the correct ammount of samples.

Inside a config file, e.c. `<config>.json`, the samples to collect can be changed: `SamplesToCollect`.

* **Parameters**
Inside  `method/constants.py` the parameters for system identification, mode clustering, mode tracking and model updating
can be changed.

* **Model**
A digital YAFEM model can be added to `models/<your_model>`.
Inside  `method/constants.py` the model paramters can be set together with the paths to the model folder and the model function file.


## Step 1.5 Run examples
The following experiments can be run using the package.

* **acceleration_readings** demonstrates the use of `Accelerometer` class to extract
  accelerometer measurements from MQTT data stream.
* **aligning_readings** demonstrates the use of `Aligner` class to collect and
  align accelerometer measurements from multiple MQTT data streams.
* **live_align_readings_and_plot** continiuously  collect and
  align accelerometer measurements from multiple MQTT data streams. The data is then plotted.

* **record-and-replay** demonstrates the use of the record and replay function
    1. **record**: records data for a set amount of time defined in the `record.py` file.
    2. **replay**: replays data from a `.jsonl` file in the `replay.py` file. Replay speed and number of times to loop can also be set.

* **sysid** demonstrates the use of `sysid` with four cases:
    1. **sysid-and-plot**: plots natural frequencies.
    2. **sysid-and-print**: prints sysid output to console.
    3. **sysid-and-publish**: publishes one set of sysid output via MQTT to the config given under [sysid] config.
    4. **live-sysid-and-publish**: Continuously publishes sysid output via MQTT to the config given under [sysid] config.

* **Clustering** demonstrates the use of `clustering` with four cases:
    1. **clustering-with-local-sysid**: gets the sysid output by runing sysid
       locally, then runs the mode clustering.
    2. **clustering-with-remote-sysid**: gets sysid output by subscribing,
       then runs the mode clustering. This is a one time operation.
    3. **live-clustering-with-remote-sysid**: gets sysid output by subscribing,
       then runs the mode clustering. This operation runs in loop.
    4. **live-clustering-with-remote-sysid-and-publish**: gets sysid output by subscribing,
       then runs the mode clustering. The cluster results are published. This operation runs in loop.

* **mode-tracking** demonstrates the use of `mode_tracking` with three cases:
    1. **mode-tracking-with-local-sysid**: gets the sysid output by runing sysid
       locally, then runs mode clustering and mode tracking.
    2. **mode-tracking-with-remote-sysid**: gets sysid output by subscribing,
       then runs mode clustering and mode tracking. This is a one time operation.
    3. **live-mode-tracking-with-remote-sysid**: gets sysid output by subscribing,
       then runs mode clustering and mode tracking. This operation runs in loop.

* **model-update** demonstrates the use of `model_update` with three cases:
    1. **model-update-local-sysid**: gets the sysid output, then uses it to
      run update model and get updated system parameters.
    2. **live-model-update-with-remote-sysid**: gets the sysid output by subscribing to
      MQTT topic, then runs mode clustering to run update model and get updated system parameters.
    3. **live-model-update-with-remote-clustering**: gets the mode clustering output by subscribing to
      MQTT topic, then uses the mode clustering output to run update model and get updated system parameters.

* **virtual-sensing** demonstrates the use of `virtual_sensing` with three cases:
    1. **virtual-sensing**: Reads latest model parameters, applies a filter if specified and estimates the displacements and accelerations for all unmeasured DOFs.
    2. **virtual-sensing-and-plot**: Reads latest model parameters, applies a filter if specified and estimates the displacements and accelerations for all unmeasured DOFs. The accelerations are plotted in the end.
    3. **live-virtual-sensing**: Continuously runs `virtual-sensing`. Reads latest model parameters, applies a filter if specified and estimates the displacements and accelerations for all unmeasured DOFs.
    4. **live-virtual-sensing-and-publish**: Continuously runs `virtual-sensing`. Reads latest model parameters, applies a filter if specified and estimates the displacements and accelerations for all unmeasured DOFs. These displacements and model parameters are published.

* **stress-strain-estimation** demonstrates the use of `stress_strain_estimation` with three cases:
    1. **stress-strain-estimation**: Reads latest model parameters and calculates the bending stress and forces for a 2D beam.
    2. **stress-strain-estimation-and-plot**: Reads latest model parameters and calculates and plots the bending stress and forces for a 2D beam.
    3. **live-stress-strain-estimation**: Continuously runs `stress-strain-estimation`. Reads latest model parameters and calculates the bending stress and forces for a 2D beam.
    4. **live-stress-estimation-subscribe-and-publish**: Continuously subscribes to virtual sensing results and apply stress estimation. The stresses are then published.

* **fatigue**
    1. **fatigue-with-local-stress-estimation**: Run stress-stain-estimation and run fatigue calculations and plot fatigue the results.
    2. **live-fatigue-with-local-stress-estimation**: Continuously run stress-stain-estimation and run fatigue calculations and plot fatigue the results.
    3. **live-fatigue-with-remote-stress-estimation**: Continuously subscribe to stress-estimation results and run fatigue calculations and plot fatigue the results.
    4. **plot-rainflow**: Plots rainflow counting algorithm



```bash
python .\src\examples\example.py align-readings  # run an experiment with real data (Needs "production.json" Config)
```

To run the examples with specified config, use

```bash
python .\src\examples\example.py --config .path_to\production.json align-readings
```

Example,

```bash
python .\src\examples\example.py --config .\config\production.json align-readings
```

## 2. Record and replay data
Record and replay data is also possible. Here a `config/replay.json` config file must be defined before hand.

Inside `record/record.py` some parameters must be specified:

```py
config_path = "config/replay.json"
config = load_config(config_path)
MQTT_CONFIG = config["MQTT"]

RECORDINGS_DIR = "record/mqtt_recordings"
FILE_NAME = "recording.jsonl"

DURATION_SECONDS = 20 # This is how many seconds of data that are recorded
```

The same goes for `record/replay.py`:

```py
# MQTT Configuration
CONFIG_PATH = "config/replay.json"

RECORDINGS_DIR = "record/mqtt_recordings"
FILE_NAME = "recording.jsonl"

REPLAY_SPEED = 1  # Multiplier for replay speed
LOOP = 1          # Number of times to loop data
```

The files can then be run with:
```bash
poetry run example-shm record
poetry run example-shm replay
```

or directly
```bash
poetry run python record/record.py
poetry run python record/replay.py
```


## 3. Install the Package from Poetry Build

A build of the package can be used for distribution.
To install the package built using `poetry`, follow these steps:

### Step 2.1: Build the Package

```bash
poetry build
```

This will create a `.whl` file in the `dist/` directory,
e.g., `dist/cp_sens-0.6.4-py3-none-any.whl`.

### Step 2.2: Create and Activate a Virtual Environment

```py
python -m venv .venv
source .venv/bin/activate        # On Linux/macOS
.\.venv\Scripts\Activate.ps1     # On Windows
```

### Step 2.3: Install the Built Package

```py
pip install example_shm-<version>-py3-none-any.whl
```

Replace `<version>` with the version number found in the `.whl`
filename. (e.g `0.6.4`).

## Step 2.5: Use

Launch the bridge with the default configuration:

```bash
$example-shm
```

The file needs to be saved. The application looks for configuration in
`config/production.json`. A different configuration can be provided by
using

```bash
example-shm --config <config-file>
```

You can find the available experiments by running the program

```bash
$example-shm
Usage: example-shm [OPTIONS] COMMAND [ARGS]...

Options:
  --config TEXT  Path to config file
  --help         Show this message and exit.

Commands:
  accelerometers
  align-readings
  clustering-with-local-sysid
  clustering-with-remote-sysid
  fatigue-with-local-stress-estimation
  live-align-readings-and-plot
  live-clustering-with-remote-sysid
  live-clustering-with-remote-sysid-and-publish
  live-fatigue-with-local-stress-estimation
  live-fatigue-with-remote-stress-estimation
  live-mode-tracking-with-remote-sysid
  live-model-update-with-remote-clustering
  live-model-update-with-remote-sysid
  live-stress-estimation-subscribe-and-publish
  live-stress-strain-estimation
  live-sysid-publish
  live-virtual-sensing
  live-virtual-sensing-and-publish
  mode-tracking-with-local-sysid
  mode-tracking-with-remote-sysid
  model-update-with-local-sysid
  plot-rainflow
  record
  replay
  stress-strain-estimation
  stress-strain-estimation-and-plot
  sysid-and-plot
  sysid-and-print
  sysid-and-publish
  virtual-sensing
  virtual-sensing-and-plot
```

To run the examples with the default config (`config/production.json`), use:

```bash
$example-shm
Usage: example-shm accelerometers
```

To run the examples with a custom config, use:

```bash
$example-shm
Usage: example-shm  --config <config-file> accelerometers
```

## Distributed Setup Overview

This explains the setup needed to run the distributed version of the example-shm pipeline.

## Machine 1: Edge Layer – Raspberry Pi with Accelerometers

This machine connects to ADXL375 sensors and is responsible for acquiring raw sensor data.
It performs calibration and continuously publishes sensor data over MQTT.

**Step 1**: Run calibration to find sensor offsets

```bash
poetry run python src/scripts/find_offset.py
```

**Step 2**: Start publishing raw accelerometer data

```bash
poetry run python src/scripts/publish_samples.py
```

## Machine 2: Fog Layer – Data Alignment and System Identification

This machine subscribes to MQTT topics from Machine 1. It aligns multi-channel data, runs system identification,
and publishes the pyOMA output.

Run the aligner and system identification pipeline

```bash
poetry run python src/examples/example.py sysid-and-publish
```

## Machine 3: Cloud Layer – Mode Tracking and Model Update

This machine subscribes to the pyOMA output, performs mode clustering and updates the structural model.

Run mode clustering and model update

```bash
poetry run python src/examples/example.py model-update-with-remote-sysid
```
