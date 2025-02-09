import json
import os
from paho.mqtt.client import Client as MQTTClient # type: ignore 

# Load configuration from json_config.json
current_directory = os.path.dirname(os.path.abspath(__file__))
json_config_path = os.path.join(current_directory, 'json_config.json')

try:
    with open(json_config_path, 'r') as f:
        json_config = json.load(f)
    print("JSON configuration loaded successfully.")
except FileNotFoundError:
    print(f"Error: The file {json_config_path} was not found.") 
    raise

# setup
mqttc = MQTTClient(client_id=json_config["MQTT"]["ClientID"])

#authentication
if json_config["MQTT"]["userId"]:
    mqttc.username_pw_set(json_config["MQTT"]["user"], json_config["MQTT"]["password"])


# Callback functions for MQTT client
def on_connect(mqttc, userdata, flags, rc, properties=None):
    print(f"on_connect: Connected with response code {rc}")
    # Subscribe to relevant topics for accelerometer data
    for topic in json_config["MQTT"]["TopicsToSubscribe"]:
        print(f"Subscribing to the topic {topic}...")
        mqttc.subscribe(topic, qos=json_config["MQTT"]["QoS"])


# I had to change the parameter "msg" to "mid", so instead of the message topic its now the message id
def on_subscribe(mqttc, userdata, mid, granted_qos):
    print(f"on_subscribe: Subscription ID {mid} with QoS levels {granted_qos}")

def on_message(client, userdata, msg):
    print(f"on_message: Received message on {msg.topic}")
    print(f"Message payload: {msg.payload.decode()}")  # Handle the message

def on_publish(client, userdata, mid):
    print(f"on_publish: Message {mid} published.")
    

# Connect to the broker using host and port from the config
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_subscribe = on_subscribe
mqttc.on_publish = on_publish

mqttc.connect(json_config["MQTT"]["host"], json_config["MQTT"]["port"], 60)
mqttc.loop_start()
