import json
import time
from typing import Any, Dict
from paho.mqtt.client import Client as MQTTClient
from data.accel.constants import WAIT_METADATA
from data.comm.mqtt import setup_mqtt_client


def _on_metadata(client: MQTTClient, userdata: Dict[str, str], message) -> None:
    """
    MQTT callback to extract sampling frequency from incoming metadata.

    Args:
        client: MQTT client instance.
        userdata: Dictionary containing metadata topic.
        message: Incoming MQTT message.
    """
    try:
        payload = json.loads(message.payload.decode("utf-8"))
        fs_candidate = payload["Analysis chain"][0]["Sampling"]
        if fs_candidate:
            global FS  # pylint: disable=global-statement
            FS = fs_candidate
            print(f"Extracted Fs from metadata: {FS}")
            client.unsubscribe(userdata["metadata_topic"])
    except Exception as e:
        print(f"Failed to extract Fs: {e}")


def extract_fs_from_metadata(mqtt_config: Dict[str, Any]) -> int:
    """
    Connects to MQTT broker and waits for metadata to extract sampling frequency.

    Args:
        mqtt_config: MQTT connection configuration.
    """
    metadata_topic = mqtt_config["TopicsToSubscribe"][1]
    metadata_client, _ = setup_mqtt_client(mqtt_config, topic_index=1)
    metadata_client.user_data_set({"metadata_topic": metadata_topic})
    metadata_client.message_callback_add(metadata_topic, _on_metadata)

    metadata_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    metadata_client.subscribe(metadata_topic)
    metadata_client.loop_start()

    initial_fs = FS
    start_time = time.time()
    # Wait until the Metadata arrives
    while FS == initial_fs and (time.time() - start_time) < WAIT_METADATA:
        time.sleep(0.1)

    metadata_client.loop_stop()
    print(f"Sampling frequency FS = {FS}")

    return FS
