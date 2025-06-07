import os
import time
import json
import threading
from datetime import datetime
import paho.mqtt.client as mqtt

# MQTT Configuration
MQTT_CONFIG = {
    "host": "test.mosquitto.org",
    "port": 1883,
    "userId": "xxxx",
    "password": "xxxx",
    "ClientID": "xxxx",
    "QoS": 1,
    "TopicsToSubscribe": {
        "cpsens/d8-3a-dd-37-d2-7e/3160-A-042_sn_999998/1/acc/raw/data": "record/mqtt_recordings/data1.jsonl",
        "cpsens/d8-3a-dd-37-d2-7e/3160-A-042_sn_999998/1/acc/raw/metadata": "record/mqtt_recordings/metadata.jsonl",
        "cpsens/d8-3a-dd-37-d2-7e/3160-A-042_sn_999998/2/acc/raw/data": "record/mqtt_recordings/data2.jsonl"
    }
}

DURATION_SECONDS = 3000 

# Ensure output directory exists
os.makedirs("mqtt_recordings", exist_ok=True)

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
        timestamp = datetime.utcnow().isoformat()
        record = {
            "timestamp": timestamp,
            "payload": list(msg.payload)  # Byte data as list of ints
        }
        file_path = MQTT_CONFIG["TopicsToSubscribe"][topic]
        with file_locks[topic]:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")


def record_mqtt():
    client = mqtt.Client(client_id=MQTT_CONFIG["ClientID"], protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
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
