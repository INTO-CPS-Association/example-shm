import json
import struct
import time
import board
import busio
import adafruit_adxl37x
from paho.mqtt.client import Client as MQTTClient

from data.sources.mqtt import setup_mqtt_client, load_config  

# --- MQTT Configuration ---
config = load_config("config/R-PI.json")
mqtt_config = config["MQTT_publish"]
mqtt_client, _ = setup_mqtt_client(mqtt_config)
mqtt_topic_base = "cpsens/DAQ_ID/MODULE_ID"

# --- Load Offset Config ---
offset_config_path = "config/offset.json"
try:
    with open(offset_config_path, "r") as f:
        offsetdata = json.load(f)
    offsets = offsetdata.get("SensorOffsets", {})
    offset1 = offsets.get("Sensor1", 0.0)
    offset2 = offsets.get("Sensor2", 0.0)
    print(f"Loaded offsets → Sensor1: {offset1}, Sensor2: {offset2}")
except Exception as e:
    print(f"Failed to load offset config: {e}")
    offset1 = 0.0
    offset2 = 0.0

# --- I2C and Sensor Setup ---
i2c = busio.I2C(board.SCL, board.SDA)

def enable_multiplexer_channel(channel: int) -> None:
    """Enables the specified channel (0–7) on the I2C multiplexer."""
    multiplexer_address = 0x70
    i2c.writeto(multiplexer_address, bytes([1 << channel]))
    time.sleep(0.01)

def setup_sensor() -> adafruit_adxl37x.ADXL375:
    """Initializes and returns a configured ADXL375 sensor instance."""
    sensor = adafruit_adxl37x.ADXL375(i2c)
    sensor.data_rate = 15  # Hz
    sensor.range = 2       # ±200g
    time.sleep(0.1)
    return sensor

def collect_samples(sensor: adafruit_adxl37x.ADXL375, offset: float, n: int = 32) -> list[float]:
    """
    Collects `n` acceleration samples (X-axis) from a sensor, applying the given offset.
    
    Args:
        sensor: The ADXL375 sensor instance.
        offset: Offset to subtract from each X reading.
        n: Number of samples to collect.
    
    Returns:
        A list of float values representing corrected acceleration data.
    """
    samples = []
    for _ in range(n):
        x = sensor.acceleration[0] - offset
        samples.append(x)
    return samples

def send_batch(mqttc: MQTTClient, topic: str, samples: list[float], sample_counter: int) -> None:
    """
    Constructs and sends a binary message over MQTT with sensor data.

    Args:
        mqttc: The MQTT client.
        topic: Topic to publish to.
        samples: List of acceleration samples.
        sample_counter: Total number of samples collected so far.
    """
    descriptor_format = "<HHQQQ"
    descriptor_length = struct.calcsize(descriptor_format)
    descriptor = struct.pack(
        descriptor_format,
        descriptor_length,
        1,  # metadata version
        0, 0,  # no timestamp
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

def main() -> None:
    """Main execution function: sets up sensors, collects data, and publishes to MQTT."""
    mqtt_client.connect(mqtt_config["Host"], mqtt_config["Port"], 60)
    mqtt_client.loop_start()

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
        # Sensor 1
        enable_multiplexer_channel(0)
        samples1 = collect_samples(sensor1, offset1, batch_size)
        topic1 = f"{mqtt_topic_base}/Sensor1/acc/raw/data"
        send_batch(mqtt_client, topic1, samples1, counter1)
        counter1 += batch_size

        # Sensor 2
        enable_multiplexer_channel(1)
        samples2 = collect_samples(sensor2, offset2, batch_size)
        topic2 = f"{mqtt_topic_base}/Sensor2/acc/raw/data"
        send_batch(mqtt_client, topic2, samples2, counter2)
        counter2 += batch_size

        time.sleep(0.02)

if __name__ == "__main__":
    main()
