# METADATA Documentation

## Overview
This document describes the structure and handling of the metadata and data topics used in the MQTT communication system for accelerometer sensors. It explains the format of the payloads, metadata versioning, data consistency checks, and handling sensor-specific metadata.

The MQTT system uses hierarchical topics to identify the source and type of data. The two key topics are:
1. **Data Topic**: Contains dynamic data from sensors.
2. **Metadata Topic**: Contains static information, including metadata related to the sensor, analysis chain, and engineering information.

## MQTT Topic Format
The MQTT topic structure follows the pattern:

cpsens/DAQ_ID/MODULE_ID/CH_ID/PHYSICS/ANALYSIS/DATA_ID


### Example Topics:
- **Data Topic**:
cpsens/RPi_1234/1/1/acc/raw/data


This represents data coming from an accelerometer (`acc`), processed as raw data (`raw`), from channel 1 of module 1 on device `RPi_1234`.

- **Metadata Topic**:
cpsens/RPi_1234/1/1/acc/raw/metadata

This topic contains metadata for the raw data from the same device, module, and channel.

## Payload Format

### Data Topic Payload
The **data topic** payload consists of two parts:
1. **Descriptor**: Contains dynamic metadata related to the data.
2. **Data**: Contains the actual sensor readings (typically as binary data).

#### Example Data Topic Payload:
```json
{
"descriptor": {
  "length": 10,
  "timestamp": "1638493434",
  "metadata_version": 1
},
"data": {
  "type": "double",
  "values": [0.5, 0.3, 0.7]
},
"sensor": {
  "sensing": "acceleration",
  "sensitivity": 100,
  "unit": "mV/ms-2"
},
"DAQ_device": {
  "IP_address": "192.168.100.101",
  "type": "Raspberry PI"
},
"analysis_chain": {
  "analysis1": {
    "name": "raw",
    "sampling_rate_Sa_per_s": 100
  }
}
}


