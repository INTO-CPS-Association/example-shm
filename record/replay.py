import os
import json
import threading
import time
from datetime import datetime
from paho.mqtt.client import Client as MQTTClient, CallbackAPIVersion, MQTTv5  # type: ignore
from data.comm.mqtt import shutdown
RECORDINGS_DIR = "record/mqtt_recordings"
FILE_NAME = "recording.jsonl"

TOPIC_MAPPING = {
    "acc1": "cpsens/recorded/1/data",
    "metadata1": "cpsens/recorded/1/metadata",
    "acc2": "cpsens/recorded/2/data",
    "acc3": "cpsens/recorded/3/data",
    "acc4": "cpsens/recorded/4/data"
}

PUBLISH_BROKER = {
    "host": " ",
    "port": 0,
    "userId": "",
    "password": "",
    "ClientID": "ReplayPublisher"
}

REPLAY_SPEED = 1  # Multiplier for replay speed

def setup_publish_client(config: dict) -> MQTTClient:
    client = MQTTClient(
        client_id=config["ClientID"],
        protocol=MQTTv5,
        callback_api_version=CallbackAPIVersion.VERSION2
    )
    if config["userId"]:
        client.username_pw_set(config["userId"], config["password"])
    client.connect(config["host"], config["port"], keepalive=60)
    return client

def send_message(publish_client: MQTTClient, line: str, delay: float):
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
        topic = TOPIC_MAPPING.get(topic_key, topic_key)
        publish_client.publish(topic, payload=payload_bytes, qos=qos)
        print(f"[REPLAYED] → {topic} (len={len(payload_bytes)}, delay={delay:.4f}s)")
    except KeyboardInterrupt:
        raise RuntimeError("Replay interrupted by user.")

def replay_mqtt_messages(loop: bool = False) -> None:
    publish_client = setup_publish_client(PUBLISH_BROKER)
    
    try:
        path = os.path.join(RECORDINGS_DIR, FILE_NAME)
        if not os.path.exists(path):
            raise ValueError(f"[Error] File not found: {path}")
    except Exception as e:
        print(f"[Error] {e}")

    try:
        while True:
            publish_client.loop_start()
            t_start = time.time()
            accumulated_delay = 0.0
            threads = []
            with open(path, "r") as f:
                prev_timestamp = None
                for line in f:
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
                        t = threading.Timer(replay_delay, send_message, args=(publish_client,line,replay_delay,)).start()
                        threads.append(t)
                        prev_timestamp = timestamp
                    except Exception as e:
                        print(f"[Error] Failed to process line: {e}")
                f.close()
            time.sleep(2)
            print(f"Waiting for all messages ({accumulated_delay:.1f}s) to be sent...")

            publish_client.loop_stop()
            t_end = time.time()
            print(f"({(t_end-t_start):.1f}s)")

            if loop is not True:
                break
            else:
                print("Restart replay function.")
    except KeyboardInterrupt:
        print("Keyboard interrupt.")
        for t in threads:
            t.cancel()
        shutdown(publish_client)

    shutdown(publish_client)
    print("[DONE].")
    t_end = time.time()
    print(f"({(t_end-t_start):.1f}s)")

if __name__ == "__main__":
    replay_mqtt_messages(loop=True) # True will loop forever
