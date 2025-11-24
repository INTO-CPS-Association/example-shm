import os
import time
import json
import threading
import datetime
from paho.mqtt.client import Client as MQTTClient, CallbackAPIVersion, MQTTv311

# MQTT Configuration
MQTT_CONFIG = {
    "host": "",
    "port":  0,
    "userId": "",
    "password": "",
    "ClientID": "",
    "QoS": 1,
    "file_path": "record/mqtt_recordings",
    "file_name": "recording.jsonl",
    "TopicsToSubscribe": {
        "cpsens/d8-3a-dd-37-d2-7e/3050-A-060_sn_106209/1/acc/raw/data": "acc1",
        "cpsens/d8-3a-dd-37-d2-7e/3050-A-060_sn_106209/1/acc/raw/metadata": "metadata1",
        "cpsens/d8-3a-dd-37-d2-7e/3050-A-060_sn_106209/2/acc/raw/data": "acc2",
        "cpsens/d8-3a-dd-37-d2-7e/3050-A-060_sn_106209/3/acc/raw/data": "acc3",
        "cpsens/d8-3a-dd-37-d2-7e/3050-A-060_sn_106209/4/acc/raw/data": "acc4"
    }
}

DURATION_SECONDS = 300  # Recording duration in seconds 

# Ensure output directory exists
os.makedirs(MQTT_CONFIG["file_path"], exist_ok=True)

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
        data_name = MQTT_CONFIG["TopicsToSubscribe"][topic]
        record = {
            "timestamp": timestamp,
            "topic": data_name,
            "payload": list(msg.payload)  # Byte data as list of ints
        }
        file_path = os.path.join(MQTT_CONFIG["file_path"],MQTT_CONFIG["file_name"])
        with file_locks[topic]:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")


def record_mqtt():
    client = MQTTClient(client_id=MQTT_CONFIG["ClientID"], protocol=MQTTv311, callback_api_version=CallbackAPIVersion.VERSION2)
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
