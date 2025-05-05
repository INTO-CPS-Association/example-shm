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

* **run_pyoma** demonstrates the use of `sys_id` with 3 cases: 
    1. run_experiment_3_plot: plots natural frequencies.
    2. run_experiment_3_print: prints OMA results to console.
    3. run_experiment_3_publish: publishes OMA results via MQTT to the config given under [sysid] config.

* **mode_tracking** demonstrates the use of `mode_track` with 2 cases: 
    1. run_experiment_4: gets the pyOMA results by runing sysid locally, then runs the mode track.
    2. run_experiment_4_subscribe: gets pyOMA results by subscribing, then runs the mode track.

* **updating_paramteres** demonstrates the use of `model_update` : 
    run_experiment_5: gets the mode track output, then uses it to run model_update to get updated system parameters.

To run the examples with the default config, use:

```bash
python .\src\examples\example.py experiment-1
python .\src\examples\example.py experiment-2
python .\src\examples\example.py experiment-3-print
python .\src\examples\example.py experiment-3-plot
python .\src\examples\example.py experiment-3-publish
python .\src\examples\example.py experiment-4
python .\src\examples\example.py experiment-4-subscribe
python .\src\examples\example.py experiment-5



```

To run the examples with specified config, use

```bash
python .\src\examples\example.py --config .path_to\production.json experiment-1
```

Example,

```bash
python .\src\examples\example.py --config .\config\production.json experiment-1
```
