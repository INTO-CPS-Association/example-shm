import os
import json
import time
import struct
from typing import Dict
from datetime import datetime
from paho.mqtt.client import Client as MQTTClient
from data.comm.mqtt import (shutdown, load_config, setup_publish_client)

from data.accel.metadata_constants import DESCRIPTOR_LENGTH_BYTES

# MQTT Configuration
CONFIG_PATH = "config/replay.json"

RECORDINGS_DIR = "record/mqtt_recordings"
FILE_NAME = "recording_beam_reduced.jsonl"

REPLAY_SPEED = 1  # Multiplier for replay speed

BUSY_WAIT_THRESHOLD = 10/1000  # Threshold in seconds for busy waiting (10 ms)
KEEP_UP_TIME = -1 # If delay time (remaining) is lower than this time, warn the user that the replay speed is two fast.
PRINT_INTERVAL = 5

SINCE_START_COUNTER = {}
BATCH_SIZE = 16

LOOPS = 1 # Number of times to loop over the recording


def override_counter_in_payload(topic_key,payload_bytes) -> None:
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
        descriptor_length = struct.unpack("<H", payload_bytes[:DESCRIPTOR_LENGTH_BYTES])[0]
        (descriptor_length, _, __, ___,
            samples_from_daq_start,) = struct.unpack("<HHQQQ", payload_bytes[:descriptor_length])
        
        # Find the raw data
        payload = payload_bytes[descriptor_length:]
        
        accel_values = struct.unpack(f"<{BATCH_SIZE}f", payload)
        # Recreate the data payload to bytes
        data_payload = struct.pack(f"<{len(accel_values)}f", *accel_values)

        # Recreate the descriptor with the updated counter
        SINCE_START_COUNTER[topic_key] = SINCE_START_COUNTER.get(topic_key, 0) + BATCH_SIZE
        descriptor = struct.pack("<HHQQQ", 28, 2, 0, 0, SINCE_START_COUNTER[topic_key])
        #Add payload back together
        payload_bytes = descriptor + data_payload
        return payload_bytes

def publish_massage(publish_client: MQTTClient, PublishTopics: Dict[str,str], qos: int, topic_key: str, payload_bytes: bytes) -> None:
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
    except KeyboardInterrupt:
        raise RuntimeError("Replay interrupted by user.")

def replay_mqtt_messages(loop: int = 1) -> None:
    """
    Replay data using jsonl file
    
    Args:
        loop (int): Number of times to loop the recorded data
    Returns:
        None
    """
    config = load_config(CONFIG_PATH)
    MQTT_config = config["MQTT"]
    publish_client = setup_publish_client(MQTT_config)
    try:
        path = os.path.join(RECORDINGS_DIR, FILE_NAME)
        if not os.path.exists(path):
            raise ValueError(f"[Error] File not found: {path}")
    except Exception as e:
        print(f"[Error] {e}")

    try:
        with open(path, "r", encoding="utf-8") as replay_file:
            total_lines = len(replay_file.readlines())
            replay_file.close()
        publish_client.loop_start()
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
                    qos = record.get("qos", 0)

                    if isinstance(payload, list):
                        payload_bytes = bytes(payload)
                    elif isinstance(payload, str):
                        payload_bytes = bytes.fromhex(payload)
                    else:
                        raise ValueError("Invalid payload format")
                    if "metadata" not in topic_key:
                        payload_bytes = override_counter_in_payload(topic_key,payload_bytes)
                    
                    timestamp = datetime.fromisoformat(record["timestamp"])
                    if prev_timestamp is None:
                        delay = 0.0  # Send the first message immediately
                    else:
                        delay = (timestamp - prev_timestamp).total_seconds()
                        if delay < 0:
                            delay = 0.0  # Prevent negative delay

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

                    publish_massage(publish_client,MQTT_config["TopicsToPublish"],qos,topic_key,payload_bytes)
                    prev_timestamp = timestamp
                replay_file.close()
                print(f"[REPLAYED {counter+1}/{total_lines}]")
            t_end = time.perf_counter()
            print(f"\nTime it took to publish: {(t_end-t_start):.3f}s")
            print("Published messages per second:",total_lines/(t_end-t_start))
            print("Since_start_counter final",SINCE_START_COUNTER)
            if ii+1 >= loop:
                print("Restart replay function.")
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
    replay_mqtt_messages(loop=LOOPS) # Times to loop