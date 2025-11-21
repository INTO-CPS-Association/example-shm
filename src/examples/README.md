# Examples

This directory contains examples demonstrating how to use
the **EXAMPLE-SHM** package.

## Install the Package from Poetry Build

To install the package built using `poetry`, follow these steps:

### Step 1: Build the Package

```bash
poetry build
```

This will create a `.whl` file in the `dist/` directory,
e.g., `dist/cp_sens-0.1.0-py3-none-any.whl`.

### Step 2: Create and Activate a Virtual Environment

```py
python -m venv .venv
source .venv/bin/activate        # On Linux/macOS
.\.venv\Scripts\Activate.ps1     # On Windows
```

### Step 3: Install the Built Package

```py
pip install example_shm-<version>-py3-none-any.whl
```

Replace `<version>` with the version number found in the `.whl`
filename. (e.g `0.1.0`).

## Running the Examples

There are 5 examples.

* **acceleration_readings** demonstrates the use of `Accelerometer` class to extract
  accelerometer measurements from MQTT data stream.
* **aligning_readings** demonstrates the use of `Aligner` class to collect and
  align accelerometer measurements from multiple MQTT data streams.

* **sysid** demonstrates the use of `sysid` with four cases:
    1. **sysid-and-plot**: plots natural frequencies.
    1. **sysid-and-print**: prints sysid output to console.
    1. **sysid-and-publish**: publishes one set of sysid output via MQTT to the config given under [sysid] config.
    1. **live-sysid-and-publish**: Continuously publishes sysid output via MQTT to the config given under [sysid] config.

* **Clustering** demonstrates the use of `clustering` with three cases:
    1. **clustering-with-local-sysid**: gets the sysid output by runing sysid
       locally, then runs the mode clustering.
    1. **clustering-with-remote-sysid**: gets sysid output by subscribing,
       then runs the mode clustering. This is a one time operation.
    1. **live-clustering-with-remote-sysid**: gets sysid output by subscribing,
       then runs the mode clustering. This operation runs in loop.
    1. **live-clustering-with-remote-sysid-and-publish**: gets sysid output by subscribing,
       then runs the mode clustering. The cluster results are published. This operation runs in loop.

* **mode-tracking** demonstrates the use of `mode_tracking` with three cases:
    1. **mode-tracking-with-local-sysid**: gets the sysid output by runing sysid
       locally, then runs mode clustering and mode tracking.
    1. **mode-tracking-with-remote-sysid**: gets sysid output by subscribing,
       then runs mode clustering and mode tracking. This is a one time operation.
    1. **live-mode-tracking-with-remote-sysid**: gets sysid output by subscribing,
       then runs mode clustering and mode tracking. This operation runs in loop.

* **model-update** demonstrates the use of `model_update` with two cases:
    1. **model-update-local-sysid**: gets the sysid output, then uses it to
      run update model and get updated system parameters.
    1. **live-model-update-with-remote-sysid**: gets the sysid output by subscribing to
      MQTT topic, then runs mode clustering to run update model and get updated system parameters.
    1. **live-model-update-with-remote-clustering**: gets the mode clustering output by subscribing to
      MQTT topic, then uses the mode clustering output to run update model and get updated system parameters.

To run the examples with the default config, use: (It may be necessary to change backslash "\" to slash "/")

```bash
python .\src\examples\example.py accelerometers
python .\src\examples\example.py align-readings
python .\src\examples\example.py sysid-and-print
python .\src\examples\example.py sysid-and-plot
python .\src\examples\example.py sysid-and-publish
python .\src\examples\example.py live-sysid-publish
python .\src\examples\example.py clustering-with-local-sysid
python .\src\examples\example.py clustering-with-remote-sysid
python .\src\examples\example.py live-clustering-with-remote-sysid
python .\src\examples\example.py live-clustering-with-remote-sysid-and-publish
python .\src\examples\example.py mode-tracking-with-local-sysid
python .\src\examples\example.py mode-tracking-with-remote-sysid
python .\src\examples\example.py live-mode-tracking-with-remote-sysid
python .\src\examples\example.py model-update-with-local-sysid
python .\src\examples\example.py live-model-update-with-remote-sysid
python .\src\examples\example.py live-model-update-with-remote-clustering

```

To run the examples with specified config, use

```bash
python .\src\examples\example.py --config .path_to\production.json align-readings
```

Example,

```bash
python .\src\examples\example.py --config .\config\production.json align-readings
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
and publishes pyOMA results.

Run the aligner and system identification pipeline

```bash
poetry run python src/examples/example.py oma-and-publish
```

## Machine 3: Cloud Layer – Mode Tracking and Model Update

This machine subscribes to pyOMA results, performs mode tracking and updates the structural model.

Run mode tracking and model update

```bash
poetry run python src/examples/example.py model-update-remote-sysid
```
