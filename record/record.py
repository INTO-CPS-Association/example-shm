import os
import time
import json
import threading
import datetime
from paho.mqtt.client import Client as MQTTClient, CallbackAPIVersion, MQTTv5
from data.comm.mqtt import load_config

# MQTT Configuration
config_path = "config/replay.json"
config = load_config(config_path)
MQTT_CONFIG = config["MQTT"]

RECORDINGS_DIR = "record/mqtt_recordings"
FILE_NAME = "recording2.jsonl"

DURATION_SECONDS = 20  # Recording duration in seconds 

# Ensure output directory exists
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# Thread-safe file locks
file_locks = {topic: threading.Lock() for topic in MQTT_CONFIG["TopicsToSubscribe"]}


def on_connect(client, userdata, flags, rc, properties):
    print("Connected with result code", rc)
    for topic in MQTT_CONFIG["TopicsToSubscribe"]:
        client.subscribe(topic, qos=MQTT_CONFIG["QoS"])
        print(f"Subscribed to {topic}")


def on_message(client, userdata, msg):
    topic = msg.topic
    if topic in MQTT_CONFIG["TopicsToSubscribe"]:
        timestamp = datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat()
        record = {
            "timestamp": timestamp,
            "topic": topic,
            "payload": list(msg.payload)  # Byte data as list of ints
        }
        file_path = os.path.join(RECORDINGS_DIR,FILE_NAME)
        with file_locks[topic]:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")


def record_mqtt():
    client = MQTTClient(client_id=MQTT_CONFIG["ClientID"], protocol=MQTTv5, callback_api_version=CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_CONFIG["userId"], MQTT_CONFIG["password"])
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_CONFIG["host"], MQTT_CONFIG["port"], keepalive=60)
    client.loop_start()

    print(f"Recording for {DURATION_SECONDS} seconds...")
    time.sleep(DURATION_SECONDS)

    client.loop_stop()
    client.disconnect()
    print("Recording complete.")


if __name__ == "__main__":
    record_mqtt()
