import os
import json
import struct
import threading
import time
import numpy as np
from pathlib import Path
from typing import Any
from datetime import datetime, timedelta

# Filepath to stored data .txt or .npy
FILEPATH = "filepath"

# If file is .txt or .csv
DELIMETER = ","     # "\t" or "" or "," or ";"
SKIP_HEADER = False # Skip header/first row
SKIP_COLOUMNS = 0   # Skip all coloumns up to value

TIMESTAMP_START = datetime.strptime('16/02/26 12:00:00.000000','%d/%m/%y %H:%M:%S.%f')

# JSONL Configuration
RECORDINGS_DIR = "record/mqtt_recordings" # Path to store to
JSONL_FILE_NAME = "recording_test.jsonl" # File name to store to

TOPICS = ["acc1", "acc2", "acc3", "acc4"] #Topic names stored
METADATA_TOPIC = "metadata1" # Metadata topic stored name

METADATA_TIMEINTERVAL = 10 #Number of seconds between every metadata message

METADATA = {
  "Descriptor": {
    "Descriptor length": "uint16",
    "Metadata version": "uint16",
    "Seconds since epoch": "uint64",
    "Nanoseconds": "uint64",
    "Samples from DAQ start": "uint64"
  },
  "Data": {
    "Type": "double",
    "Samples": 32,
    "Unit": "m/s^2"
  },
  "Sensor": {
    "Sensing": "acceleration",
    "Sensitivity": 100.0,
    "Sensitivity unit": "mV/(m/s^2)",
    "Vendor": "",
    "Type": "",
    "S/N": ""
  },
  "DAQ": {
    "Type": "DAQ_name",
    "MAC": "a1-a2-a3-a4",
    "IP": ""
  },
  "Analysis chain": [
    {
      "Name": "acquisition",
      "Output": "raw",
      "Sampling": 100.0
    }
  ],
  "Engineering": {
    "project": "name",
    "projectid": 1,
    "channelgroupname": "ch_g_name",
    "channelgroupid": 1,
    "channelName": "ch_name",
    "DOF": 1,
    "Node": 1,
    "Dir": 1
  },
  "TimeAtAquisitionStart": {
    "Seconds": 0,
    "Nanosec": 0
  }
}

# Thread-safe file locks
file_locks = {topic: threading.Lock() for topic in TOPICS}

DATA_TYPES = {"_Bool":"?",
                "short": "h",
                "unsigned short": "H",
                "int": "i",
                "unsigned int":"I",
                "long": "l",
                "unsigned long": "L",
                "long long": "q",
                "unsigned long long": "Q",
                "float": "f",
                "double": "d"}

def file_to_jsonl() -> None:
    """
    Convert .txt, .csv, .npy to jsonl file
    Args:
        None
    Returns:
        None
    """
    try:
        if not os.path.exists(RECORDINGS_DIR):
            # Ensure output directory exists
            Path(RECORDINGS_DIR).mkdir(parents=True, exist_ok=True)
        path  = os.path.join(RECORDINGS_DIR, JSONL_FILE_NAME)
    except Exception as e:
        print(f"[Error] {e}")
    path  = Path(RECORDINGS_DIR)/JSONL_FILE_NAME

    file_format = FILEPATH[-3:]
    if file_format == "txt" or (file_format == "csv"):
        data = np.genfromtxt(FILEPATH,dtype=np.float64,delimiter=DELIMETER,skip_header=SKIP_HEADER)
        data = data[:,SKIP_COLOUMNS:]
    elif file_format == "npy":
        data = np.load(FILEPATH)
    else:
        raise ValueError("File format not supported. .csv, .txt and .npy is allowed.")

    samples = METADATA["Data"]["Samples"]
    fs = METADATA["Analysis chain"][0]["Sampling"]
    print("Data array dimension:",data.shape)
    print("Number of samples pr. message:",samples)
    print("Sample frequency:",fs)

    n_sensors = data.shape[1]
    n_packages = int(data.shape[0]/samples)
    print("Number of sensors:",n_sensors)
    print("Number of packages:",n_packages)

    counter = 0
    prev_timestamp = None
    try:
        for ii in range(n_packages):
            timestamp = TIMESTAMP_START + timedelta(milliseconds=1/fs*1000*samples*ii) # Simulate increasing timestamps
            for jj in range(n_sensors):
                payload_data = data[samples*(ii):samples*(1+ii),jj]
                topic = TOPICS[jj]
                format_and_store_data(counter, payload_data.tolist(), topic, timestamp, path)
                
                if prev_timestamp is None:
                    prev_timestamp = timestamp
                else:
                    time_passed = (timestamp - prev_timestamp).total_seconds()
                    if time_passed > METADATA_TIMEINTERVAL:
                        format_and_store_data(counter, METADATA, METADATA_TOPIC, timestamp, path)
                        prev_timestamp = timestamp
            counter = counter + samples

    except KeyboardInterrupt:
        time.sleep(1)
        print("Keyboard interrupt.")
    else:
        print("[DONE].")


def format_and_store_data(counter: int, payload_data: Any, topic: str, timestamp: datetime, record_file_name: str):
    """
    Takes the payload input and stores it in a .jsonl file.

    Args:
        counter (int): samples counter
        payload_data (Any): Dict of metadata or list of data
        topic (str): Topic to publish
        Timestamp (datetime): Time format
        record_file_name (str): Path to file to append data to
    Returns:
        None
    """
    if isinstance(payload_data, list):
        descriptor = struct.pack("<HHQQQ", 28, 2, 0, 0, counter)
        data_payload = struct.pack(f"<{len(payload_data)}"+DATA_TYPES[METADATA["Data"]["Type"]], *payload_data)
        payload_bytes = descriptor + data_payload

    elif isinstance(payload_data,dict):
        payload_bytes = json.dumps(payload_data).encode('utf-8')
    else:
        raise ValueError(f"Unsupported data type: {type(payload_data)}")

    record = {
        "timestamp": timestamp.replace(tzinfo=None).isoformat(),
        "topic": topic,
        "origin": topic,
        "payload": list(payload_bytes)  # Byte data as list of ints
    }
    with file_locks[topic]:
        with open(record_file_name, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

if __name__ == "__main__":
    file_to_jsonl() # Times to loop