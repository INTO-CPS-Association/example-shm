# User Guide

This guide outlines configuration and execution of the _example-shm_ application. It provides detailed information on the configuration parameters, command-line options, and execution procedures.

## Install

You can install the built package using pip:

```bash
$pip install dist/example_shm-<version>-py3-none-any.whl
```

Replace `<version>` with the actual version number (e.g., `0.5.0`).

## Create Configuration

The package requires a json configuration file and access to MQTT broker.
The format of configuration file is,

```json
{
    "MQTT": {
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
      "TopicsToPublish": ["sensors/1/acc/mode_clmodel_updateuster/data"]
    }
}
```

The file needs to be saved. The application looks for configuration in
`config/production.json`.

## Use

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

The following experiments can be run using
the package.

### Run Experiments

The following experiments can be run using
the package.

* **acceleration_readings** demonstrates the extraction of
  accelerometer measurements from MQTT data stream.
* **aligning_readings** collects and aligns the accelerometer measurements from multiple MQTT data streams.

* **sysid** demonstrates the use of `sys_id` with four cases:
    1. **sysid-and-plot**: plots natural frequencies.
    1. **sysid-and-print**: prints SysID results to console.
    1. **sysid-and-publish**: publishes one set of SysID results via MQTT to the config given under [sysid] config.
    1. **live-sysid-and-publish**: Continuously publishes SysID results via MQTT to the config given under [sysid] config.

* **mode-tracking** demonstrates the use of `mode_track` with three cases:
    1. **mode-tracking-with-local-sysid**: gets the pyOMA results by runing sysid
       locally, then runs the mode track.
    1. **mode-tracking-with-remote-sysid**: gets pyOMA results by subscribing,
       then runs the mode track. This is a one time operation.
    1. **live-mode-tracking-with-remote-sysid**: gets pyOMA results by subscribing,
       then runs the mode track. This operation runs in loop.

* **model-update** demonstrates the use of `model_update` with two cases:
    1. **model-update-local-sysid**: gets the mode track output, then uses it to
      run update model and get updated system parameters.
    1. **live-model-update-remote-sysid**: gets the mode track output by subscribing to
      MQTT topic, then uses the mode track output to run update model and get updated system parameters.

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
  live-clustering-with-remote-sysid
  live-mode-tracking-with-remote-sysid
  live-model-update-remote-sysid
  live-sysid-publish
  mode-tracking-with-local-sysid
  mode-tracking-with-remote-sysid
  model-update-local-sysid
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
