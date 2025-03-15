import json
import os
import time
from paho.mqtt.client import Client as MQTTClient, CallbackAPIVersion, MQTTv5  # type: ignore

def load_config(config_path: str) -> dict:
    """
    Loads JSON configuration from the provided config path.

    Raises:
        FileNotFoundError: If the file is not found.
        ValueError: If the file cannot be decoded as JSON.
        Exception: For any other unexpected error.
    """
    try:
        with open(config_path, "r") as f:
            json_config = json.load(f)
        print("JSON configuration loaded successfully.")
        return json_config
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file {config_path} was not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Error: The file {config_path} could not be decoded as JSON.")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")


def create_on_connect_callback(topics, qos):
    def on_connect(client, userdata, flags, rc, properties=None):
        print(f"on_connect: Connected with response code {rc}")
        if rc == 0:  # Connection was successful
            for topic in topics:
                print(f"Subscribing to the topic {topic}...")
                client.subscribe(topic, qos=qos)
        else:
            print("Connection failed with result code:", rc)
    return on_connect

def create_on_subscribe_callback():
    def on_subscribe(client, userdata, mid, granted_qos, properties=None):
        print(f"on_subscribe: Subscription ID {mid} with QoS levels {granted_qos}")
        
    return on_subscribe

def create_on_message_callback():
    def on_message(client, userdata, msg):
        print(f"on_message: Received message on {msg.topic}")
    return on_message

def create_on_publish_callback():
    def on_publish(client, userdata, mid, *args, **kwargs):
        print(f"on_publish: Message {mid} published.")
    return on_publish

def setup_mqtt_client(config, topic_index=0):
    """Initialize client using a specific topic index from the subscription list."""
    mqttc = MQTTClient(
        client_id=config["ClientID"],  # Direct access to keys
        callback_api_version=CallbackAPIVersion.VERSION2,
        protocol=MQTTv5  
    )
    
    if config["userId"]:
        mqttc.username_pw_set(config["userId"], config["password"])
    
    # Ensure topic_index is valid
    topics_list = config["TopicsToSubscribe"]
    if topic_index < 0 or topic_index >= len(topics_list):
        raise ValueError(f"Invalid topic index: {topic_index}. Available range: 0-{len(topics_list) - 1}")

    selected_topic = topics_list[topic_index]

    mqttc.on_connect = create_on_connect_callback([selected_topic], config["QoS"])
    mqttc.on_subscribe = create_on_subscribe_callback()
    mqttc.on_message = create_on_message_callback()
    mqttc.on_publish = create_on_publish_callback()
    
    return mqttc, selected_topic
