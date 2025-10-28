import json
import time
from typing import Any, Dict
from paho.mqtt.client import Client as MQTTClient
from data.accel.constants import WAIT_METADATA
from data.comm.mqtt import setup_mqtt_client

def extract_fs_from_metadata(mqtt_config: Dict[str, Any]) -> int:
    fs_result = {"fs": None}

    def _on_metadata(client: MQTTClient, userdata, message) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            fs_candidate = payload["Analysis chain"][0]["Sampling"]
            if fs_candidate:
                fs_result["fs"] = fs_candidate
                print(f"Extracted Fs from metadata: {fs_candidate}")
                client.unsubscribe(userdata["metadata_topic"])
        except Exception as e:
            print(f"Failed to extract Fs: {e}")

    metadata_topic = mqtt_config["TopicsToSubscribe"][1]
    client, _ = setup_mqtt_client(mqtt_config, topic_index=1)
    client.user_data_set({"metadata_topic": metadata_topic})
    client.message_callback_add(metadata_topic, _on_metadata)
    client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    client.subscribe(metadata_topic)
    client.loop_start()

    start_time = time.time()
    while fs_result["fs"] is None and (time.time() - start_time) < WAIT_METADATA:
        time.sleep(0.1)
    client.loop_stop()
    if fs_result["fs"] is None:
        raise TimeoutError("Sampling frequency not received within timeout")
    return fs_result["fs"]
