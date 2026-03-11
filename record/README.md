# Purpose
The record.py and replay.py files are used to record data from MQTT topics which later can be replayed and re-published with replay.py.

# Run the functions
The functions are directly run with:
```bash
python ./record/record.py

python ./record/replay.py
```

# Parameters for record.py

CONFIG_PATH = "<path>.json": Path to config file

RECORDINGS_DIR : Directory path to what folder to save recording to

FILE_NAME = "<name>.jsonl": filename for saved recording file

DURATION_SECONDS: Recording duration in seconds 

# Parameters for replay.py

CONFIG_PATH = "<path>.json": Path to config file

RECORDINGS_DIR : Directory path to what folder the file to replay
FILE_NAME = "<name>.jsonl": filename for file to replay

REPLAY_SPEED:  # Multiplier for replay speed
 
KEEP_UP_TIME: If delay time (remaining) is lower than this time, warn the user that the replay speed is two fast.

PRINT_INTERVAL: Interval between printing information

BATCH_SIZE: Number of values in every MQTT package

LOOPS: Number of times to loop over the recording
