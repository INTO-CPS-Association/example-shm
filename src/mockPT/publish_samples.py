import json
import struct
import time
import os
import board
import busio
import adafruit_adxl37x
import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTv5, CallbackAPIVersion

# --- MQTT Configuration ---
mqtt_host = "test.mosquitto.org"
mqtt_port = 1883
mqtt_client_id = "dual_sensor_publisher"
mqtt_topic_base = "cpsens/DAQ_ID/MODULE_ID"

# --- Load Offset Config ---
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "offset.json")
try:
    with open(config_path, "r") as f:
        config = json.load(f)
    offsets = config.get("SensorOffsets", {})
    offset1 = offsets.get("Sensor1", 0.0)
    offset2 = offsets.get("Sensor2", 0.0)
    print(f"Loaded offsets → Sensor1: {offset1}, Sensor2: {offset2}")
except Exception as e:
    print(f"Failed to load config: {e}")
    offset1 = 0.0
    offset2 = 0.0

# --- MQTT Setup ---
def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected to MQTT broker with result code", rc)

def on_publish(client, userdata, mid, reason_code, properties=None):
    print(f"Message {mid} published (reason: {reason_code})")

def setup_mqtt_client():
    client = mqtt.Client(
        client_id=mqtt_client_id,
        protocol=MQTTv5,
        callback_api_version=CallbackAPIVersion.VERSION2
    )
    client.on_connect = on_connect
    client.on_publish = on_publish
    return client

# --- I2C and Sensor Setup ---
i2c = busio.I2C(board.SCL, board.SDA)

def enable_multiplexer_channel(channel: int):
    multiplexer_address = 0x70
    i2c.writeto(multiplexer_address, bytes([1 << channel]))
    time.sleep(0.01)

def setup_sensor():
    sensor = adafruit_adxl37x.ADXL375(i2c)
    sensor.data_rate = 15 
    sensor.range = 2
    time.sleep(0.1)
    return sensor

# --- Data Publishing ---
def collect_samples(sensor, offset: float, n: int = 32) -> list:
    samples = []
    for _ in range(n):
        x = sensor.acceleration[0] - offset
        samples.append(x)
    return samples

def send_batch(mqttc, topic, samples, sample_counter):
    descriptor_format = "<HHQQQ"
    descriptor_length = struct.calcsize(descriptor_format)
    descriptor = struct.pack(
        descriptor_format,
        descriptor_length,
        1,  
        0, 0, 
        sample_counter
    )
    data_payload = struct.pack(f"<{len(samples)}f", *samples)
    payload = descriptor + data_payload
    mqttc.publish(topic, payload, qos=1, retain=False)

    avg_val = sum(samples) / len(samples)
    print(f"\nPublishing to: {topic}")
    print(f"Sample Counter: {sample_counter}")
    print(f"Batch Size: {len(samples)}")
    print(f"Samples: {samples}")

# --- Main ---
def main():
    mqttc = setup_mqtt_client()
    mqttc.connect(mqtt_host, mqtt_port, 60)
    mqttc.loop_start()

    # Set up both sensors
    print("Initializing Sensor1 on channel 0...")
    enable_multiplexer_channel(0)
    sensor1 = setup_sensor()

    print("Initializing Sensor2 on channel 1...")
    enable_multiplexer_channel(1)
    sensor2 = setup_sensor()

    counter1 = 0
    counter2 = 0
    batch_size = 32

    while True:
        # Sensor 1 (channel 0)
        enable_multiplexer_channel(0)
        samples1 = collect_samples(sensor1, offset1, batch_size)
        topic1 = f"{mqtt_topic_base}/Sensor1/acc/raw/data"
        send_batch(mqttc, topic1, samples1, counter1)
        counter1 += batch_size

        # Sensor 2 (channel 1)
        enable_multiplexer_channel(1)
        samples2 = collect_samples(sensor2, offset2, batch_size)
        topic2 = f"{mqtt_topic_base}/Sensor2/acc/raw/data"
        send_batch(mqttc, topic2, samples2, counter2)
        counter2 += batch_size

        time.sleep(0.02) 
if __name__ == "__main__":
    main()




