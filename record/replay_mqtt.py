import os
import json
import time
from datetime import datetime
from paho.mqtt.client import Client as MQTTClient, CallbackAPIVersion, MQTTv5  # type: ignore

RECORDINGS_DIR = "record/mqtt_recordings"

TOPIC_MAPPING = {
    "data1.jsonl": "cpsens/recorded/1/data",
    "metadata.jsonl": "cpsens/recorded/1/metadata",
    "data2.jsonl": "cpsens/recorded/2/data"
}

PUBLISH_BROKER = {
    "host": "test.mosquitto.org",
    "port": 1883,
    "username": "",
    "password": "",
    "client_id": "ReplayPublisherTest"
}

def setup_publish_client(config: dict) -> MQTTClient:
    client = MQTTClient(
        client_id=config["client_id"],
        protocol=MQTTv5,
        callback_api_version=CallbackAPIVersion.VERSION2
    )
    if config["username"]:
        client.username_pw_set(config["username"], config["password"])
    client.connect(config["host"], config["port"], keepalive=60)
    return client

def replay_mqtt_messages():
    publish_client = setup_publish_client(PUBLISH_BROKER)
    publish_client.loop_start()

    files = {}
    for fname in TOPIC_MAPPING:
        path = os.path.join(RECORDINGS_DIR, fname)
        if not os.path.exists(path):
            print(f"[SKIP] File not found: {path}")
            continue
        files[fname] = open(path, "r", encoding="utf-8")

    iterators = {fname: iter(files[fname]) for fname in files}

    prev_timestamps = {fname: None for fname in files}
    done = set()


    while len(done) < len(files):
        for fname, fiter in iterators.items():
            if fname in done:
                continue

            try:
                line = next(fiter)
                record = json.loads(line.strip())
                payload = record["payload"]
                if isinstance(payload, list):
                    payload_bytes = bytes(payload)
                elif isinstance(payload, str):
                    payload_bytes = bytes.fromhex(payload)
                else:
                    raise ValueError("Invalid payload format")

                qos = record.get("qos", 1)
                timestamp_str = record.get("timestamp")
                if timestamp_str:
                    current_timestamp = datetime.fromisoformat(timestamp_str)
                    prev = prev_timestamps[fname]
                    if prev:
                        delay = (current_timestamp - prev).total_seconds()
                        if delay > 0:
                            time.sleep(delay)
                    prev_timestamps[fname] = current_timestamp

                topic = TOPIC_MAPPING[fname]
                publish_client.publish(topic, payload=payload_bytes, qos=qos)
                print(f"[{fname}] → {topic} (len={len(payload_bytes)})")

            except StopIteration:
                done.add(fname)
                print(f"[DONE] {fname} finished")
            except Exception as e:
                print(f"[ERROR] in {fname}: {e}")

    for f in files.values():
        f.close()

    time.sleep(1)
    publish_client.loop_stop()
    publish_client.disconnect()
    print("[DONEEEE].")

if __name__ == "__main__":
    replay_mqtt_messages()
