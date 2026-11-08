## Contents:
1. Purpose
2. Run the functions
3. Configuration file
3. Parameters

# Purpose
The record.py and replay.py files are used to record data from MQTT topics which later can be replayed and re-published with replay.py.

The MQTT recordings "recording.jsonl" and "recording_beam_reduced.jsonl" are recordings from [1], which demonstrates a
structual health monitoring workflow on a cantilever beam.

* "recording.jsonl" is a continuous live data sample from the beam described in [1] without a mass perturbation.
* "recording_beam_reduced.jsonl" is a data sample from the beam in [1]. Here the 90 datasets of 2 minutes is reduced to 30 datasets of 2 minutes. 10 datasets from each mass configuration.

In the folder "mqtt_recordings/reference_results_beam_recording" reference result plots for "recording_beam_reduced.jsonl" can be found. Here, tracking results and model updating results can be used as references when the results are reproduced. Though beware that the results vary based on the exact data that the aligner recieves and aligns together, so the references as a guide, not as the exact result you should expect to reproduce when using the package.

[1] "A digital twin platform for structural health monitoring"
Prasad Talasila, Dmitri Tcherniak, Anders M.D. Jensen, Swarup Mahato, Jakob V. Medom, Martin D. Ulriksen, Giuseppe Abbiati, A. Schörghofer-Queiroz, Peter G. Larsen, Lars Damkilde
Computer-Aided Civil and Infrastructure Engineering, 2026
https://doi.org/10.1016/j.cacaie.2026.100086

# Run the functions
The functions are directly run with:
```bash
python ./record/record.py

python ./record/replay.py
```
or through the package:
```bash
example-shm record.py

example-shm replay.py
```
Using the record and replay functionality through the package uses the config file provided by the command or the standard "production.json". 
So, a specefic configuration file with a custom path can be used as:
```bash
example-shm --config ./config/replay.json record.py

example-shm --config ./config/replay.json replay.py
```

# Configuration file
The record and replay files are configured to MQTT with a json file formatted as:
"MQTT": {
        "host": "",
        "port": 0000,
        "userId": "",
        "password": "",
        "ClientID": "ReplaySubscriber",
        "QoS": 1,
        "TopicsToSubscribe": {
            "PROJECT/CH_ID/PHYSICS/ANALYSIS/DATA_TYPE": "acc1",
            ""PROJECT/CH_ID/PHYSICS/ANALYSIS/DATA_TYPE": "metadata1",
            "PROJECT/CH_ID/PHYSICS/ANALYSIS/DATA_TYPE": "acc2",
            "PROJECT/CH_ID/PHYSICS/ANALYSIS/DATA_TYPE": "acc3",
        },
        "TopicsToPublish": {
            "acc1": "cpsens/recorded/1/data",
            "metadata1": "cpsens/recorded/1/metadata",
            "acc2": "cpsens/recorded/2/data",
            "acc3": "cpsens/recorded/3/data",
        }
      }
"TopicsToSubscribe" is a dictionary with the keys being the topics to subsribe. The items is the name the topics are stored as.
"TopicsToPublish" is a dictionary with the keys being the names of topics. The items is the topics of the published.

For more information regarding the config file read the USERGUIDE.md

# Parameters for record.py
CONFIG_PATH = "<path>.json": Path to config file
RECORDINGS_DIR = "<path>": Directory path to what folder to save recording to
FILE_NAME = "<name>.jsonl": filename for saved recording file
DURATION_SECONDS <float>: Recording duration in seconds 

# Parameters for replay.py
CONFIG_PATH = "<path>.json": Path to config file
RECORDINGS_DIR = "<path>": Directory path to what folder the file to replay
FILE_NAME = "<name>.jsonl": filename for file to replay
REPLAY_SPEED = <float>: Multiplier for replay speed
LOOPS = <int>: Number of times to loop over the recording
KEEP_UP_TIME = <float>: If delay time (remaining) is lower than this time, warn the user that the replay speed is two fast.
PRINT_INTERVAL = <float>: Interval between printing information
BUSY_WAIT_THRESHOLD = <float>: Threshold in seconds for how small a delay can be.
                                If the delay is too small, then the script will wait for 10 ms.
                                Otherwise the MQTT might not keep up.
