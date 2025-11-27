import os
import json
import threading
import time
from typing import Dict
from datetime import datetime
from paho.mqtt.client import Client as MQTTClient
from data.comm.mqtt import (shutdown, load_config, setup_publish_client)

# MQTT Configuration
CONFIG_PATH = "config/replay.json"

RECORDINGS_DIR = "record/mqtt_recordings"
FILE_NAME = "recording.jsonl"

REPLAY_SPEED = 0.1  # Multiplier for replay speed

def send_message(publish_client: MQTTClient, PublishTopics: Dict[str,str], line: str, delay: float, total: int, counter: int):
    try:
        record = json.loads(line.strip())
        payload = record["payload"]
        if isinstance(payload, list):
            payload_bytes = bytes(payload)
        elif isinstance(payload, str):
            payload_bytes = bytes.fromhex(payload)
        else:
            raise ValueError("Invalid payload format")

        qos = record.get("qos", 1)
        topic_key = record.get("topic")
        topic = PublishTopics[topic_key]
        
        publish_client.publish(topic, payload=payload_bytes, qos=qos)
        text = (f"[REPLAYED {counter+1}/{total}] → {topic} (len={len(payload_bytes)}, delay={delay:.5f}s)       ")
        print(text,end="\r")
    except KeyboardInterrupt:
        raise RuntimeError("Replay interrupted by user.")

def replay_mqtt_messages(loop: int = 1) -> None:
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
        for ii in range(loop):
            print(f"Replay function iteration {ii+1}/{loop}.")
            publish_client.loop_start()
            t_start = time.time()
            accumulated_delay = 0.0
            with open(path, "r") as f:
                total_lines = len(f.readlines())
                f.close()

            with open(path, "r") as f:
                prev_timestamp = None
                for counter, line in enumerate(f):
                    # if counter >= 256:
                    #     break
                    try:
                        message = json.loads(line.strip())
                        timestamp = datetime.fromisoformat(message["timestamp"])
                        if prev_timestamp is None:
                            delay = 0.0  # Send the first message immediately
                        else:
                            delay = (timestamp - prev_timestamp).total_seconds()
                            if delay < 0:
                                delay = 0.0  # Prevent negative delay
                        accumulated_delay += delay
                        replay_delay = delay / REPLAY_SPEED
                        threading.Timer(replay_delay, send_message, args=(publish_client,MQTT_config["TopicsToPublish"],line,replay_delay,total_lines,counter,)).start()
                        prev_timestamp = timestamp
                    except Exception as e:
                        print(f"\n[Error] Failed to process line: {e}")
                f.close()

            time.sleep(2)
            print(f"\nWaiting for all messages ({total_lines}msg. {accumulated_delay:.3f}s) to be sent...")
            while publish_client._out_messages:
                text = f"Remaining messages to be sent: {str(len(publish_client._out_messages)).zfill(len(str(total_lines)))}"
                time.sleep(1)
                print(text,end="\r")
            publish_client.loop_stop()
            t_end = time.time()
            print(f"\nTime it took to publish: {(t_end-t_start):.3f}s")

            if ii+1 >= loop:
                print("Restart replay function.")
    except KeyboardInterrupt:
        time.sleep(1)
        print("Keyboard interrupt.")
        shutdown(publish_client)
    else:
        shutdown(publish_client)
        print("[DONE].")

if __name__ == "__main__":
    replay_mqtt_messages(loop=10) # Times to loop