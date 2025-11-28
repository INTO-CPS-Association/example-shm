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


## Step 1.3 Change settings
There are some settings that can be changed for the specific use case.

* **Sample time**
This is how many samples should be used for sysid. The value uses the time in minutes and the sample frequency, fs,
to calculate the correct ammount of samples.

Inside `examples/run_sysid.py`, `examples/run_mode_clustering.py`, `examples/run_mode_tracking.py`, `examples/run_model_update.py`
the sample time can be changed: `number_of_minutes`.

* **Parameters**
Inside  `method/constans.py` the parameters for system identification, mode clustering, mode tracking and model updating
can be changed.

* **Model**
A digital YAFEM model can be added to `models/<your_model>`.
Inside  `method/constans.py` the model paramters can be set together with the paths to the model folder and the model function file.


## Step 1.4 Run examples
The following experiments can be run using the package.

* **acceleration_readings** demonstrates the use of `Accelerometer` class to extract
  accelerometer measurements from MQTT data stream.
* **aligning_readings** demonstrates the use of `Aligner` class to collect and
  align accelerometer measurements from multiple MQTT data streams.

* **sysid** demonstrates the use of `sysid` with four cases:
    1. **sysid-and-plot**: plots natural frequencies.
    2. **sysid-and-print**: prints sysid output to console.
    3. **sysid-and-publish**: publishes one set of sysid output via MQTT to the config given under [sysid] config.
    4. **live-sysid-and-publish**: Continuously publishes sysid output via MQTT to the config given under [sysid] config.

* **Clustering** demonstrates the use of `clustering` with three cases:
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

* **model-update** demonstrates the use of `model_update` with two cases:
    1. **model-update-local-sysid**: gets the sysid output, then uses it to
      run update model and get updated system parameters.
    2. **live-model-update-with-remote-sysid**: gets the sysid output by subscribing to
      MQTT topic, then runs mode clustering to run update model and get updated system parameters.
    3. **live-model-update-with-remote-clustering**: gets the mode clustering output by subscribing to
      MQTT topic, then uses the mode clustering output to run update model and get updated system parameters.

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



## 2. Install the Package from Poetry Build

To install the package built using `poetry`, follow these steps:

### Step 2.1: Build the Package

```bash
poetry build
```

This will create a `.whl` file in the `dist/` directory,
e.g., `dist/cp_sens-0.6.0-py3-none-any.whl`.

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
filename. (e.g `0.6.0`).

## Step 2.4: Create Configuration

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
    }
}
```
Where the MQTT topic structure follows the pattern:
`PROJECT/CH_ID/PHYSICS/ANALYSIS/DATA_TYPE`
Where `DATA_TYPE` could be metadata or plain data.

The file needs to be saved. The application looks for configuration in
`config/production.json`.

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
  align-readings-plot
  clustering-with-local-sysid
  clustering-with-remote-sysid
  live-clustering-with-remote-sysid
  live-clustering-with-remote-sysid-and-publish
  live-mode-tracking-with-remote-sysid
  live-model-update-with-remote-clustering
  live-model-update-with-remote-sysid
  live-sysid-publish
  mode-tracking-with-local-sysid
  mode-tracking-with-remote-sysid
  model-update-with-local-sysid
  sysid-and-plot
  sysid-and-print
  sysid-and-publish
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
