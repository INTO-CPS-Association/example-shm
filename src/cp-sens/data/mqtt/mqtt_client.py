import json
import paho.mqtt.client as mqtt
from paho.mqtt.client import Client as MQTTClient
from paho.mqtt.client import MQTTv5

class MQTT:
    def __init__(self, config):
        with open(config, 'r') as f:
            config = json.load(f)
            self.host = config['mqtt']['host']
            self.port = config['mqtt']['port']
            self.username = config['mqtt']['username']
            self.password = config['mqtt']['password']
            self.topic = config['mqtt']['topic']
        self.client = None
        self._mqtt_config()

    def _mqtt_config(self) -> None:
        self.client = MQTTClient(client_id='accelerometer',
                                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                                    protocol=MQTTv5, transport='tcp')
        self.client.username_pw_set(self.username, self.password)
        #self.client.on_publish = self._on_publish
        self.client.on_message = self._on_message
        self.client.connect(self.host, self.port)
        self.client.loop_start()

    def _on_publish(self) -> None:
        print('message published')

    def publish(self, message) -> None:
        self.client.publish(self.topic, message, qos=1)

    def subscribe(self) -> None:
        self.client.subscribe(self.topic, qos=1)

    def _on_message(self, client, userdata, msg) -> None:
        print(f"Message received: {msg.payload.decode()} on topic {msg.topic}")

    def stop(self) -> None:
        self.client.disconnect()
        self.client.loop_stop()