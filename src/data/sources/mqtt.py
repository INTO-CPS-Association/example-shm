"""
MQTT Client Setup and Utility Functions.

This module provides functions to set up an MQTT client, handle connections, 
subscriptions, and message publishing using the Paho MQTT library.
"""

import json
from paho.mqtt.client import Client as MQTTClient, CallbackAPIVersion, MQTTv5  # type: ignore


def load_config(config_path: str) -> dict:
    """
    Loads JSON configuration from the provided config path.

    Args:
        config_path (str): Path to the JSON configuration file.

    Returns:
        dict: The loaded configuration.

    Raises:
        FileNotFoundError: If the file is not found.
        ValueError: If the file cannot be decoded as JSON.
        RuntimeError: For any other unexpected error.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            json_config = json.load(file)
        print("JSON configuration loaded successfully.")
        return json_config
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Error: The file {config_path} was not found.") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Error: The file {config_path} could not be decoded as JSON.") from exc
    except Exception as exc:
        raise RuntimeError(f"An unexpected error occurred: {exc}") from exc


def create_on_connect_callback(topics, qos):
    """Creates an on_connect callback function for the MQTT client."""

    def on_connect(client, userdata, flags, rc, properties=None):  # noqa: ARG001
        print(f"on_connect: Connected with response code {rc}")
        if rc == 0:  # Connection was successful
            for topic in topics:
                print(f"Subscribing to topic: {topic}")
                client.subscribe(topic, qos=qos)
        else:
            print("Connection failed with result code:", rc)

    return on_connect


def create_on_subscribe_callback():
    """Creates an on_subscribe callback function for the MQTT client."""

    def on_subscribe(client, userdata, mid, granted_qos, properties=None):  # noqa: ARG001
        print(f"on_subscribe: Subscription ID {mid} with QoS levels {granted_qos}")

    return on_subscribe


def create_on_message_callback():
    """Creates an on_message callback function for the MQTT client."""

    def on_message(client, userdata, msg):  # noqa: ARG001
        print(f"on_message: Received message on {msg.topic}")

    return on_message


def create_on_publish_callback():
    """Creates an on_publish callback function for the MQTT client."""

    def on_publish(client, userdata, mid, *args, **kwargs):  # noqa: ARG001
        print(f"on_publish: Message {mid} published.")

    return on_publish


def setup_mqtt_client(config, topic_index=0):
    """
    Initializes an MQTT client using a specific topic index from the subscription list.

    Args:
        config (dict): MQTT client configuration.
        topic_index (int, optional): Index of the topic to subscribe to. Defaults to 0.

    Returns:
        tuple: (MQTTClient, selected_topic)
    """
    mqttc = MQTTClient(
        client_id=config["ClientID"],
        callback_api_version=CallbackAPIVersion.VERSION2,
        protocol=MQTTv5,
    )

    if config["userId"]:
        mqttc.username_pw_set(config["userId"], config["password"])

    topics_list = config["TopicsToSubscribe"]
    if topic_index < 0 or topic_index >= len(topics_list):
        raise ValueError(
            f"Invalid topic index: {topic_index}. Available range: 0-{len(topics_list) - 1}"
        )

    selected_topic = topics_list[topic_index]

    mqttc.on_connect = create_on_connect_callback([selected_topic], config["QoS"])
    mqttc.on_subscribe = create_on_subscribe_callback()
    mqttc.on_message = create_on_message_callback()
    mqttc.on_publish = create_on_publish_callback()

    return mqttc, selected_topic
