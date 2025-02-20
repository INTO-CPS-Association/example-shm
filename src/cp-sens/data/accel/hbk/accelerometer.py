import json
import os
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
    def on_subscribe(client, userdata, mid, granted_qos):
        print(f"on_subscribe: Subscription ID {mid} with QoS levels {granted_qos}")
    return on_subscribe
def create_on_subscribe_callback():
    def on_subscribe(client, userdata, mid, granted_qos):
        print(f"on_subscribe: Subscription ID {mid} with QoS levels {granted_qos}")
    return on_subscribe

def create_on_message_callback():
    def on_message(client, userdata, msg):
        print(f"on_message: Received message on {msg.topic}")
        print(f"Message payload: {msg.payload.decode()}")
    return on_message
def create_on_message_callback():
    def on_message(client, userdata, msg):
        print(f"on_message: Received message on {msg.topic}")
        print(f"Message payload: {msg.payload.decode()}")
    return on_message

def create_on_publish_callback():
    def on_publish(client, userdata, mid):
        print(f"on_publish: Message {mid} published.")
    return on_publish

def setup_mqtt_client(config):
    mqttc = MQTTClient(
        client_id=config["MQTT"]["ClientID"],
        callback_api_version=CallbackAPIVersion.VERSION2,
        protocol=MQTTv5  
    )
    if config["MQTT"]["userId"]:
        mqttc.username_pw_set(config["MQTT"]["userId"], config["MQTT"]["password"])

    # Assign callbacks.
    mqttc.on_connect = create_on_connect_callback(config["MQTT"]["TopicsToSubscribe"],
                                                  config["MQTT"]["QoS"])
    mqttc.on_subscribe = create_on_subscribe_callback()
    mqttc.on_message = create_on_message_callback()
    mqttc.on_publish = create_on_publish_callback()
    return mqttc

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "../../config/mqtt.json")
    json_config = load_config(config_path)
    mqttc = setup_mqtt_client(json_config)
    mqttc.connect(json_config["MQTT"]["host"], json_config["MQTT"]["port"], 60)
    mqttc.loop_start()