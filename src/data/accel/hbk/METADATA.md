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

#### Data Topic

```txt
cpsens/RPi_1234/1/1/acc/raw/data
```

This represents data coming from an accelerometer (`acc`), processed as raw data (`raw`), from channel 1 of module 1 on device `RPi_1234`.

#### Metadata Topic

```txt
cpsens/RPi_1234/1/1/acc/raw/metadata
```

This topic contains metadata for the raw data from the same device, module, and channel.

## Payload Format

### Data Topic Payload

The **data topic** payload consists of two parts:

1. **Descriptor**: Contains dynamic metadata related to the data.
1. **Data**: Contains the actual sensor readings (typically as binary data).

#### Example Data Topic Payload

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
            "cpsens/d8-3a-dd-f5-92-48/cpsns_Simulator/+/acc/raw/data",
            "cpsens/d8-3a-dd-f5-92-48/cpsns_Simulator/+/acc/raw/metadata",  

            "cpsens/d8-3a-dd-37-d3-08/3050-A-060_sn_106209/+/acc/raw/data",
            "cpsens/d8-3a-dd-37-d3-08/3050-A-060_sn_106209/+/acc/raw/metadata", 

            "cpsens/2c-cf-67-25-da-db/mcc172_21C2CCC/+/acc/raw/data",
            "cpsens/2c-cf-67-25-da-db/mcc172_21C2CCC/+/acc/raw/metadata", 

            "cpsens/d8-3a-dd-37-d2-7e/3160-A-042_sn_999998/+/acc/raw/data",
            "cpsens/d8-3a-dd-37-d2-7e/3160-A-042_sn_999998/+/acc/raw/metadata"  
        ]
    }
}