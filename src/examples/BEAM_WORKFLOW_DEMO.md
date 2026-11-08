## BEAM WORKFLOW DEMONSTRATION
This is a demonstration of the workflow for reproducing the beam results from [1].

# List of contents
1. Background
2. Setup
2. 1. Setup configuration file
2. 2. Setup replay file
3. Replay data
4. Run


## 1. Background
The beam is a cantilever beam (steel ruler) with 4 accelerometers. The experiment consist of two mass perturbations at 10grams and 20grams at the tip.

The beam data is stored in `record/mqtt_recordings/recording_beam_reduced.jsonl`. This is a reduced dataset from [1]. Here, the 90 datasets of 2 minutes is reduced to 30 datasets of 2 minutes. 10 datasets from each mass perturbation.

[1] "A digital twin platform for structural health monitoring"
Prasad Talasila, Dmitri Tcherniak, Anders M.D. Jensen, Swarup Mahato, Jakob V. Medom, Martin D. Ulriksen, Giuseppe Abbiati, A. Schörghofer-Queiroz, Peter G. Larsen, Lars Damkilde
Computer-Aided Civil and Infrastructure Engineering, 2026
https://doi.org/10.1016/j.cacaie.2026.100086

## 2. Setup
# 2.1 Setup configuration file
A MQTT configuration .json file must be setup with `TopicsToPublish` as a dictionary.
Host, port must be filled and possibly also userId and password if required.
```json
{
"MQTT": {
       "host": "",
        "port": 0000,
        "userId": "",
        "password": "",
        "ClientID": "ReplaySubscriber",
        "QoS": 1,
        "TopicsToSubscribe": {
        },
        "TopicsToPublish": {
            "acc1": "cpsens/recorded/1/data",
            "metadata1": "cpsens/recorded/1/metadata",
            "acc2": "cpsens/recorded/2/data",
            "acc3": "cpsens/recorded/3/data",
            "acc4": "cpsens/recorded/4/data"
        }
      }
}
```
Here, the keys are the names in the jsonl file, and the items are the topic names the data will be published as.

After "MQTT" the confifuration file is filled with:
```json
{
"sysid": {
        "host": "",
        "port": 0000,
        "userId": "",
        "password": "",
        "ClientID": "Sysid",
        "QoS": 1,
        "SamplesToCollect": 30720,
        "MetadataToSubscribe": ["cpsens/recorded/1/metadata"],
        "TopicsToSubscribe": [
            "cpsens/recorded/1/data",
            "cpsens/recorded/2/data",
            "cpsens/recorded/3/data",
            "cpsens/recorded/4/data"
        ],
        "TopicsToPublish": ["cpsens/recorded/sysid/data"]
      },

    "mode_cluster": {
      "host": "",
      "port": 0000,
      "userId": "",
      "password": "",
      "ClientID": "Clustering",
      "QoS": 1,
      "TopicsToSubscribe": ["cpsens/recorded/sysid/data"],
      "TopicsToPublish": ["cpsens/recorded/mode_cluster/data"]
    },

    "model_update": {
      "host": "",
      "port": 0000,
      "userId": "",
      "password": "",
      "ClientID": "ModelUpdate",
      "QoS": 1,
      "TopicsToSubscribe": ["cpsens/recorded/mode_cluster/data"],
      "TopicsToPublish": ["cpsens/recorded/model_update/data"]
    },
    "virtual_sensing": {
      "host": "",
      "port": 0000,
      "userId": "",
      "password": "",
      "ClientID": "VirtualSensing",
      "QoS": 1,
      "SamplesToCollect": 30720,
      "MetadataToSubscribe": ["cpsens/recorded/1/metadata"],
      "TopicsToSubscribe": [
            "cpsens/recorded/1/data",
            "cpsens/recorded/2/data",
            "cpsens/recorded/3/data",
            "cpsens/recorded/4/data"
        ],
      "TopicsToPublish": ["cpsens/recorded/virtual_sensing/data"]
    },

    "stress": {
      "host": "",
      "port": 0000,
      "userId": "",
      "password": "",
      "ClientID": "StressEstimation",
      "QoS": 1,
      "TopicsToSubscribe": ["cpsens/recorded/virtual_sensing/data"],
      "TopicsToPublish": ["cpsens/recorded/stress/data"]
    },

    "fatigue": {
      "host": "",
      "port": 0000,
      "userId": "",
      "password": "",
      "ClientID": "Fatigue",
      "QoS": 1,
      "TopicsToSubscribe": ["cpsens/recorded/stress/data"],
      "TopicsToPublish": []
    }
}
```
Number of samples is required for some of the functionalities. Here "SamplesToCollect": 30720 , is 120 seconds of data at 256 Hz sampling rate.


# 2.2 Setup replay file
Inside `record/replay.py`: some parameters must be specified:

```py
# MQTT Configuration
CONFIG_PATH = "config/replay.json" # This path is overwritten when "example-shm --config <config path> replay" is used.
RECORDINGS_DIR = "record/mqtt_recordings"
FILE_NAME = "recording_beam_reduced.jsonl"
REPLAY_SPEED = 1  # Multiplier for replay speed
LOOP = 1          # Number of times to loop data
```

For more information read README.md under the "record" folder.

## 3. Replay data
The replay script can then be run with:
```bash
example-shm --config <config path> replay
```
or directly
```bash
python record/replay.py
poetry run python record/replay.py
```

## 4. Run 
Run these functions in parallel:

Read replayed data and apply system identification. Publish the results.
```bash
example-shm --config <config path> live-sysid-publish

example-shm --config <config path> live-mode-tracking-with-remote-sysid

example-shm --config <config path> live-model-update-with-remote-sysid
```
then run this command:
```bash
example-shm --config <config path> live-fatigue-with-local-stress-estimation
```
or all of these three commands:
```bash
example-shm --config <config path> live-virtual-sensing-and-publish

example-shm --config <config path> live-stress-estimation-subscribe-and-publish

example-shm --config <config path> live-fatigue-with-remote-stress-estimation
```

In `record/mqtt_recordings/reference_results_beam_recording` png files for reference results can be found.