# METADATA Documentation

## Overview

This document describes the structure and handling of the metadata and data topics used in the MQTT communication system for accelerometer sensors. It explains the format of the payloads, metadata versioning, data consistency checks, and handling sensor-specific metadata.

The MQTT system uses hierarchical topics to identify the source and type of data. The two key topics are:

1. **Data Topic**: Contains dynamic data from sensors.
1. **Metadata Topic**: Contains static information, including metadata related to the sensor, analysis chain, and engineering information.

## MQTT Topic Format

The MQTT topic structure follows the pattern:

```txt
cpsens/DAQ_ID/MODULE_ID/CH_ID/PHYSICS/ANALYSIS/DATA_ID
```

### Example Topics

#### Metadata Topic

```txt
cpsens/d3-f2-f3-b3/cpsns_Simulator/1/acc/raw/metadata
```

This represents metadata coming from an accelerometer (`acc`), processed as raw data (`raw`), from channel 1 of The cpsns_Simulator module on device `d3-f2-f3-b`.



### METADATA Topic Payload

#### Example METADATA Topic Payload

```json
{
  "Descriptor": {
    "Descriptor length": "uint16",
    "Metadata version": "uint16",
    "Seconds since epoch": "uint64",
    "Nanoseconds": "uint64",
    "Samples from DAQ start": "uint64"
  },
  "Data": {
    "Type": "float",
    "Samples": 32,
    "Unit": "m/s^2"
  },
  "Sensor": {
    "Sensing": "acceleration",
    "Sensitivity": 100.0,
    "Sensitivity unit": "mV/(m/s^2)",
    "Vendor": "HBK",
    "Type": "4507 B",
    "S/N": "12345"
  },
  "DAQ": {
    "Type": "DAQ_Simulator",
    "MAC": "d8-3a-dd-f5-92-48",
    "IP": ""
  },
  "Analysis chain": [
    {
      "Name": "acquisition",
      "Output": "raw",
      "Sampling": 512.0
    }
  ],
  "Engineering": {
    "project": "BLATIGUE-2",
    "projectid": 42,
    "channelgroupname": "DTU Blade",
    "channelgroupid": 1,
    "channelName": "156149X+",
    "DOF": 156149,
    "Node": 156149,
    "Dir": 1
  },
  "TimeAtAquisitionStart": {
    "Seconds": 1741618465,
    "Nanosec": 641669098
  }
}



#### Data Topic

```txt
cpsens/d3-f2-f3-b/cpsns_Simulator/1/acc/raw/data
```

This topic contains data for the raw data from the same device, module, and channel.


### Data Topic Payload

The **data topic** payload consists of two parts:

1. **Descriptor**: Contains dynamic metadata related to the data.
1. **Data**: Contains the actual sensor readings (typically as binary data).

#### Example Data Topic Payload

```json
{
  "descriptor": {
    "descriptor_length": 28,
    "metadata_version": 2,
    "seconds_since_epoch": 1742400339,
    "nanoseconds": 1504491492025,
    "samples_from_daq_start": 400319264
  },
  "data": {
    "type": "float",
    "values": [3.5, 4.3, 4.7]
  }
}
```


## MQTT Configuration

The acceleration measurements are streamed via MQTT broker. The following
configuration needs to be placed in `config/mqtt.json` and
credentials modified.

```json
{
    "MQTT": {
        "host": "test.mosquitto.org",
        "port": 1883,
        "userId": "",
        "password": "",
        "ClientID": "test_client_id",
        "QoS": 1,
        "TopicsToSubscribe": [
            "cpsens/d8-3a-dd-f5-92-48/cpsns_Simulator/0/acc/raw/data",
            "cpsens/d8-3a-dd-f5-92-48/cpsns_Simulator/0/acc/raw/metadata",    
            "cpsens/d8-3a-dd-f5-92-48/cpsns_Simulator/1/acc/raw/data",
            "cpsens/d8-3a-dd-f5-92-48/cpsns_Simulator/1/acc/raw/metadata",  
            "cpsens/d8-3a-dd-f5-92-48/cpsns_Simulator/2/acc/raw/data",
            "cpsens/d8-3a-dd-f5-92-48/cpsns_Simulator/2/acc/raw/metadata"
        ]
    }
}