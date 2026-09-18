import json
import time
import struct
from pathlib import Path
from typing import Dict
from datetime import datetime
from paho.mqtt.client import Client as MQTTClient
from data.comm.mqtt import (shutdown, load_config, setup_publish_client)

# User configurable MQTT Configuration
CONFIG_PATH = "config/replay.json"
RECORDINGS_DIR = Path(__file__).parent / "mqtt_recordings"
FILE_NAME = "recording_beam_reduced.jsonl"

REPLAY_SPEED = 1  # Multiplier for replay speed
LOOPS = 1 # Number of times to loop over the recording

#Non important parameters
BUSY_WAIT_THRESHOLD = 10/1000  # Threshold in seconds for how small a delay can be.
                                # If the delay is too small, then the script will wait for 10 ms.
                                # Otherwise the MQTT might not keep up.
KEEP_UP_TIME = -1 # If delay time (remaining) is lower than this time,
                    # warn the user that the replay speed is two fast.
PRINT_INTERVAL = 5
SINCE_START_COUNTER = {}



def override_counter_in_payload(topic_key,payload_bytes, metadata) -> None:
    """
    Overrides the recorded 'samples_from_daq_start' counter with a replay counter.
    This is important when the recording is looped.
    Args:
        topic_key (str): Topic string used as a dict key
        paylpad_bytes (bytes): Payload in bytes 
    Returns: 
        payload_bytes (bytes): Payload in bytes
    """
    # Find and remove the descriptor from the payload
    # Trying to load in big-endian and little-endian ways
    char_LE, char_BE = '<','>'
    _, metadataVer_LE = struct.unpack_from(char_LE+'HH', payload_bytes) # assumes little endian here
    _, metadataVer_BE = struct.unpack_from(char_BE+'HH', payload_bytes) # assumes big endian here
    # print(metadataVer_LE,metadataVer_BE)
    char_Endian = char_LE if metadataVer_LE < metadataVer_BE else char_BE
    descriptor_length, metadata_version = struct.unpack_from(char_Endian+"HH", payload_bytes)
    # (descriptor_length, _, __, ___, _____,) = struct.unpack(char_Endian+"HHQQQ", payload_bytes[:descriptor_length]) # H = Unsigned short (2 bytes), Q = Unsigned long long (8 bytes)

    if metadata_version < 2:
        raise Exception("Metadata version too old.")
    else:
        md_samples = metadata["Data"]["Samples"]
        data_type = metadata["Data"]["Type"]
        # Extract sensor data

        data_types = {"_Bool":"?",
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
        try:
            byte_type = data_types[data_type]
        except:
            raise ValueError(f"Byte type [{data_type}] not possible. These data types are available: ",data_types.keys())

        if md_samples <= 0: #Variable or unknown
            payload_len = len(payload_bytes)
            num_samples = round((payload_len-descriptor_length)/struct.calcsize(byte_type))
        else:
            num_samples = md_samples
    
    # Find the raw data
    payload = payload_bytes[descriptor_length:]
    accel_values = struct.unpack(char_Endian+str(num_samples)+byte_type, payload)

    # Recreate the data payload to bytes
    data_payload = struct.pack(char_Endian+str(num_samples)+byte_type, *accel_values)

    # Recreate the descriptor with the updated counter
    SINCE_START_COUNTER[topic_key] = SINCE_START_COUNTER.get(topic_key, 0) + num_samples
    descriptor = struct.pack(char_Endian+"HHQQQ", 28, 2, 0, 0, SINCE_START_COUNTER[topic_key])
    #Add payload back together
    payload_bytes = descriptor + data_payload
    return payload_bytes

def publish_message(publish_client: MQTTClient, PublishTopics: Dict[str,str], qos: int,
                    topic_key: str, payload_bytes: bytes) -> None:
    """
    Publish message
    Args:
        publish_client (MQTTClient): Publish client
        PublishTopics (Dict[str,str]): Topics to publish
        qos (int): Quality of service
        topic_key (str): Topic string used as a dict key
        paylpad_bytes (bytes): Payload in bytes 
    Return:
        None
    """

    try:
        topic = PublishTopics[topic_key]
        publish_client.publish(topic, payload=payload_bytes, qos=qos)
    except KeyboardInterrupt as exc:
        raise KeyboardInterrupt("Replay interrupted by user.") from exc

def replay_mqtt_messages(config_path: str, loop: int = 1) -> None:
    """
    Replay data using jsonl file
    
    Args:
        config_path (str): Path to config file
        loop (int): Number of times to loop the recorded data
    Returns:
        None
    """
    config = load_config(config_path)
    MQTT_config = config["MQTT"]
    publish_client, publish_topics = setup_publish_client(MQTT_config, verbose = False)
    origin_list = []
    try:
        path = RECORDINGS_DIR / FILE_NAME
        if not path.exists():
            raise ValueError(f"[Error] File not found: {path}")

        with open(path, "r", encoding="utf-8") as replay_file:
            total_lines = len(replay_file.readlines())
            replay_file.close()

        with open(path, "r") as replay_file:
            metadata = None
            for counter, line in enumerate(replay_file):
                record = json.loads(line.strip())
                payload = record["payload"]
                topic_key = record.get("topic")

                if isinstance(payload, list):
                    payload_bytes = bytes(payload)
                elif isinstance(payload, str):
                    payload_bytes = bytes.fromhex(payload)
                else:
                    raise ValueError("Invalid payload format")

                if "metadata" in topic_key:
                    metadata = json.loads(payload_bytes.decode("utf-8"))
                    print("Metadata found: ",metadata)
                    break

        if metadata is None:
            print("Metadata not found. Trying with this default metadata")
            metadata = {"Descriptor": {
                            "Descriptor length": 28,
                            "Metadata version": 2,
                            "Seconds since epoch": 0,
                            "Nanoseconds": 0,
                            "Samples from DAQ start": 0
                            },
                            "Data":{"Samples":-1,
                            "Type":"float"}}
            print("Default metadata: ",metadata)
            

        for ii in range(loop):
            print(f"Replay function iteration {ii+1}/{loop}.")
            accumulated_delay = 0.0
            t_start = time.perf_counter()
            print_t = t_start
            prev_timestamp = None
            with open(path, "r", encoding="utf-8") as replay_file:
                for counter, line in enumerate(replay_file):
                    record = json.loads(line.strip())
                    payload = record["payload"]
                    topic_key = record.get("topic")
                    origin = record.get("origin")
                    if origin not in origin_list:
                        print(f"Topic: {topic_key}, with origin topic:",origin)
                        if topic_key in publish_topics:
                            print("Publish topic:",publish_topics[topic_key])
                        origin_list.append(origin)
                    qos = record.get("qos", 0)

                    if isinstance(payload, list):
                        payload_bytes = bytes(payload)
                    elif isinstance(payload, str):
                        payload_bytes = bytes.fromhex(payload)
                    else:
                        raise ValueError("Invalid payload format")

                    if "metadata" not in topic_key:
                        payload_bytes = override_counter_in_payload(topic_key,payload_bytes,metadata)

                    timestamp = datetime.fromisoformat(record["timestamp"])
                    if prev_timestamp is None:
                        delay = 0.0  # Send the first message immediately
                    else:
                        delay = (timestamp - prev_timestamp).total_seconds()
                        if delay < 0:
                            delay = 0.0  # Prevent negative delay
                    if delay > 60:
                        print(f"Large time difference in data. Results in dlay of: {delay:.3f} seconds")

                    accumulated_delay += delay
                    target_time = t_start + accumulated_delay / REPLAY_SPEED
                    time_now = time.perf_counter()

                    if (time_now-print_t) > PRINT_INTERVAL:
                        print(f"[REPLAYED {counter+1}/{total_lines}]")
                        print_t = time.perf_counter()

                    sleep_time = target_time - time_now
                    if sleep_time < KEEP_UP_TIME:
                        print("[WARNING] Can't keep up. Replay speed to fast.")
                        print(sleep_time,target_time,time_now)
                    if sleep_time > BUSY_WAIT_THRESHOLD:
                        time.sleep(sleep_time - BUSY_WAIT_THRESHOLD)
                    while time.perf_counter() < target_time:
                        time.sleep(0)  # Yield CPU while busy-waiting for sub-10ms precision

                    publish_message(publish_client,MQTT_config["TopicsToPublish"],qos,
                                    topic_key, payload_bytes)
                    prev_timestamp = timestamp
                replay_file.close()
                print(f"[REPLAYED {total_lines}/{total_lines}]")
            t_end = time.perf_counter()
            print(f"\nTime it took to publish: {(t_end-t_start):.3f}s")
            print("Published messages per second:",total_lines/(t_end-t_start))
            print("Since_start_counter final",SINCE_START_COUNTER)
            while publish_client._out_messages:
                remaining_count = len(publish_client._out_messages)
                text = (
                    f"Remaining messages to be sent: "
                    f"{str(remaining_count).zfill(len(str(total_lines)))}"
                )
                time.sleep(1)
                print(text, end="\r")
        publish_client.loop_stop()
    except KeyboardInterrupt:
        print("Keyboard interrupt.")
        shutdown(publish_client)
    else:
        shutdown(publish_client)
        print("[DONE].")

if __name__ == "__main__":
    replay_mqtt_messages(CONFIG_PATH, loop=LOOPS) # Times to loop
