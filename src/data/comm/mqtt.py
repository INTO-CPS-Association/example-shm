"""
MQTT Client Setup and Utility Functions.

This module provides functions to set up an MQTT client, handle connections,
subscriptions, and message publishing using the Paho MQTT library.
"""
from typing import Any, Dict, List, Tuple
import json
import uuid
from paho.mqtt.client import Client as MQTTClient, CallbackAPIVersion, MQTTv5  # type: ignore
from collections.abc import Callable
import sys

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
        raise FileNotFoundError(
            f"Error: The file {config_path} was not found.") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Error: The file {config_path} could not be decoded as JSON.") from exc
    except Exception as exc:
        raise RuntimeError(f"An unexpected error occurred: {exc}") from exc


def create_on_connect_callback(topics, qos):
    """Creates an on_connect callback function for the MQTT client."""

    # pylint: disable=unused-argument
    def on_connect(client, _, __, rc, properties=None):  # noqa: ARG001
        print(f"on_connect: Connected with response code {rc}")
        if rc == 0:  # Connection was successful
            for topic in topics:
                print(f"Subscribing to topic: {topic}")
                #client.subscribe(topic, qos=qos)
        else:
            print("Connection failed with result code:", rc)

    return on_connect


def create_on_subscribe_callback():
    """Creates an on_subscribe callback function for the MQTT client."""

    # pylint: disable=unused-argument
    def on_subscribe(_, __, mid, granted_qos, properties=None):  # noqa: ARG001
        print(
            f"on_subscribe: Subscription ID {mid} with QoS levels {granted_qos}")

    return on_subscribe


def create_on_message_callback():
    """Creates an on_message callback function for the MQTT client."""

    def on_message(_, __, msg):  # noqa: ARG001
        print(f"on_message: Received message on {msg.topic}")

    return on_message


def create_on_publish_callback():
    """Creates an on_publish callback function for the MQTT client."""

    # pylint: disable=unused-argument
    def on_publish(_, __, mid, *args, **kwargs):  # noqa: ARG001
        print(f"on_publish: Message {mid} published.")

    return on_publish


def setup_mqtt_client(config: Dict[str,Any], topic_to_subscribe: str):
    """
    Initializes an MQTT client using a specific topic index from the subscription list.

    Args:
        config (Dict[str,Any]): MQTT client configuration.
        topic_to_subscribe (str): Topic to subscribe to.

    Returns:
        tuple: (MQTTClient, selected_topic)
    """
    mqttc = MQTTClient(
        client_id=f"{config['ClientID']}_{uuid.uuid4().hex[:6]}",
        callback_api_version=CallbackAPIVersion.VERSION2,
        protocol=MQTTv5,
    )

    if config["userId"]:
        mqttc.username_pw_set(config["userId"], config["password"])

    mqttc.on_connect = create_on_connect_callback(
        [topic_to_subscribe], config["QoS"])
    mqttc.on_subscribe = create_on_subscribe_callback()
    mqttc.on_message = create_on_message_callback()
    mqttc.on_publish = create_on_publish_callback()

    return mqttc

def setup_publish_client(config: Dict[str,Any]) -> MQTTClient:
    """
    Generate publish client
    Args:
        config (Dict[str,Any]): Configuration file for generating MQTT client
    Returns:
        mqtt_client (MQTTClient): MQTT client
    """
    publish_client = MQTTClient(
        client_id=config["ClientID"],
        protocol=MQTTv5,
        callback_api_version=CallbackAPIVersion.VERSION2
    )
    if config["userId"]:
        publish_client.username_pw_set(config["userId"], config["password"])
    publish_client.connect(config["host"], config["port"], keepalive=60)
    return publish_client

def start_mqtt(config: Dict[str,Any], _on_connect: Callable, _on_message: Callable = None) -> Tuple[MQTTClient,List[str],List[str]]:
    """
    Generate client from config file and intiate it.
    Args:
        config (Dict[str,Any]): Configuration file for generating MQTT client
        _on_connect (Callable): on_connect function
        _on_message (Callable): on_message function
    Returns:
        mqtt_client (MQTTClient): MQTT client
        subcribe_topics (List[str]): Topics to subscribe to
        publish_topics (List[str]): Topics to publish
    """
    mqtt_client = setup_mqtt_client(config,config["TopicsToSubscribe"][0])
    mqtt_client.connect(config["host"], config["port"], 60)
    mqtt_client.loop_start()
    mqtt_client.user_data_set({"topic": config["TopicsToSubscribe"][0], "qos": 1})
    mqtt_client.on_connect = _on_connect
    if _on_message is not None:
        mqtt_client.on_message = _on_message
    mqtt_client.connect(config["host"],
                        config["port"], keepalive=60)
    mqtt_client.loop_start()

    subcribe_topics = config["TopicsToSubscribe"]
    publish_topics = config["TopicsToPublish"]
    return mqtt_client, subcribe_topics, publish_topics

def reconnect_client(mqtt_client: MQTTClient) -> bool:
    """
    Args:
        mqtt_client (MQTTClient): MQTT client
    Returns:
        bool
    """
    if not mqtt_client.is_connected():
        print("Client disconnected. Reconnecting...")
        mqtt_client.reconnect()
    return True

def publish_to_mqtt(publish_client: MQTTClient, publish_topics: List[str],
                    payload: Dict[str,Any],
                    name: str) -> None:
    """
    Publish payload to publish topic

    Args:
        publish_client (MQTTClient):
        publish_topics (str): Timestamp of data
        payload (Dict[str,Any]): Payload to publish
        name (str): What is being published

    Returns:
    """

    try:
        if publish_topics is None or publish_topics == [] or publish_topics[0] == "":
            raise ValueError("No publish topic specified. Skipping publish.")

        message = json.dumps(payload)

        _ = reconnect_client(publish_client)

        for topic in publish_topics:
            publish_client.publish(topic, message, qos=1)
            print(f"Published {name} to {topic}")

    except Exception as e:
        print(f"\nFailed to publish {name}: {e}")

def shutdown(mqtt_client: MQTTClient,name: str = None):
    """
    Shutdown MQTT client
    Args:
        mqtt_client (MQTTClient): MQTT client
        name (str): What is shutting down
    Returns:
    """
    if name is not None:
        print("\nShutting down",name)
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    sys.stdout.flush()
