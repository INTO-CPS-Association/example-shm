import os
import json
import time
from typing import Dict, Tuple
from datetime import datetime
from paho.mqtt.client import Client as MQTTClient
from data.comm.mqtt import (shutdown, load_config, setup_publish_client)

# MQTT Configuration
CONFIG_PATH = "config/replay.json"

RECORDINGS_DIR = "record/mqtt_recordings"
FILE_NAME = "recording.jsonl"

REPLAY_SPEED = 0.1  # Multiplier for replay speed
BUSY_WAIT_THRESHOLD = 0.01  # seconds: use busy-wait for gaps shorter than 10ms
PRINT_INTERVAL = 0.5  # seconds: throttle console output
MAX_INFLIGHT_MESSAGES = 30000  # max in-flight QoS=1 messages for high throughput


def send_message_sync(
    publish_client: MQTTClient,
    publish_topics: Dict[str, str],
    line: str,
    total: int,
    counter: int,
) -> Tuple[str, int]:
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
    topic = publish_topics[topic_key]

    publish_client.publish(topic, payload=payload_bytes, qos=qos)
    return topic, len(payload_bytes)


def replay_mqtt_messages(loop: int = 1) -> None:
    config = load_config(CONFIG_PATH)
    mqtt_config = config["MQTT"]
    publish_client = setup_publish_client(mqtt_config)
    publish_client.max_inflight_messages_set(MAX_INFLIGHT_MESSAGES)

    try:
        path = os.path.join(RECORDINGS_DIR, FILE_NAME)
        if not os.path.exists(path):
            raise ValueError(f"[Error] File not found: {path}")
    except Exception as exc:
        print(f"[Error] {exc}")
        return

    try:
        for ii in range(loop):
            print(f"Replay function iteration {ii+1}/{loop}.")
            publish_client.loop_start()
            t_start = time.perf_counter()
            accumulated_delay = 0.0

            with open(path, "r", encoding="utf-8") as count_file:
                total_lines = sum(1 for _ in count_file)

            with open(path, "r", encoding="utf-8") as replay_file:
                prev_timestamp = None
                last_print_time = t_start

                for counter, line in enumerate(replay_file):
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
                        target_time = t_start + accumulated_delay / REPLAY_SPEED

                        # Hybrid wait: sleep for coarse portion, busy-wait for fine portion
                        now = time.perf_counter()
                        remaining = target_time - now
                        if remaining > BUSY_WAIT_THRESHOLD:
                            time.sleep(remaining - BUSY_WAIT_THRESHOLD)
                        while time.perf_counter() < target_time:
                            time.sleep(0)  # Yield CPU while busy-waiting for sub-10ms precision

                        topic, payload_len = send_message_sync(
                            publish_client, mqtt_config["TopicsToPublish"],
                            line, total_lines, counter,
                        )

                        now = time.perf_counter()
                        if now - last_print_time >= PRINT_INTERVAL:
                            elapsed = accumulated_delay / REPLAY_SPEED
                            text = (
                                f"[REPLAYED {counter+1}/{total_lines}] → {topic} "
                                f"(len={payload_len}, t={elapsed:.5f}s)       "
                            )
                            print(text, end="\r")
                            last_print_time = now

                        prev_timestamp = timestamp
                    except Exception as exc:
                        print(f"\n[Error] Failed to process line: {exc}")

            print(
                f"\nWaiting for all messages ({total_lines} msg, "
                f"{accumulated_delay:.3f}s) to be sent..."
            )
            while publish_client._out_messages:
                remaining_count = len(publish_client._out_messages)
                text = (
                    f"Remaining messages to be sent: "
                    f"{str(remaining_count).zfill(len(str(total_lines)))}"
                )
                time.sleep(1)
                print(text, end="\r")

            publish_client.loop_stop()
            t_end = time.perf_counter()
            print(f"\nTime it took to publish: {(t_end - t_start):.3f}s")

            if ii + 1 >= loop:
                print("Restart replay function.")
    except KeyboardInterrupt:
        time.sleep(1)
        print("Keyboard interrupt.")
        shutdown(publish_client)
    else:
        shutdown(publish_client)
        print("[DONE].")

if __name__ == "__main__":
    replay_mqtt_messages(loop=10)  # Times to loop