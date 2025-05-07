# pylint: disable=import-error
import json
import struct
import time
from typing import Tuple, List
from dataclasses import dataclass
import board  # type: ignore
import busio  # type: ignore
import adafruit_adxl37x  # type: ignore
from paho.mqtt.client import Client as MQTTClient

from data.comm.mqtt import load_config, setup_mqtt_client
from pt_mock.constants import (
    SAMPLES_PER_MESSAGE,
    SENSOR_REFRESH_RATE,
    SENSOR_RANGE,
    DEFAULT_OFFSET,
)


@dataclass
class SensorTask:
    i2c: busio.I2C
    channel: int
    label: str
    sensor: adafruit_adxl37x.ADXL375
    offset: float
    batch_size: int
    counter: int

@dataclass
class Batch:
    topic: str
    samples: List[float]
    sample_counter: int


def load_offsets(path: str) -> Tuple[float, float]:
    """
    Loads x-axis offsets for Sensor1 and Sensor2 from a JSON configuration file.

    Args:
        path (str): Path to the offset configuration file.

    Returns:
        Tuple[float, float]: A tuple containing the offset values for Sensor1 and Sensor2.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            offsetdata = json.load(f)
        offsets = offsetdata.get("SensorOffsets", {})
        offset1 = offsets.get("Sensor1", DEFAULT_OFFSET)
        offset2 = offsets.get("Sensor2", DEFAULT_OFFSET)
        print(f"Loaded offsets → Sensor1: {offset1}, Sensor2: {offset2}")
        return offset1, offset2
    except Exception as e:
        print(f"Failed to load offset config: {e}")
        return DEFAULT_OFFSET, DEFAULT_OFFSET


def enable_multiplexer_channel(i2c: busio.I2C, channel: int) -> None:
    """
    Enables a specific channel on the I2C multiplexer.

    Args:
        i2c (busio.I2C): The I2C bus instance.
        channel (int): The channel index to activate (0–7).
    """
    multiplexer_address = 0x70
    i2c.writeto(multiplexer_address, bytes([1 << channel]))
    time.sleep(0.01)


def setup_sensor(i2c: busio.I2C) -> adafruit_adxl37x.ADXL375:
    """
    Initializes and configures an ADXL375 sensor on the specified I2C bus.

    The sensor is configured with:
    - data_rate = 15 Hz
    - range = ±200g

    Returns:
        Configured ADXL375 sensor instance.
    """
    sensor = adafruit_adxl37x.ADXL375(i2c)
    sensor.data_rate = SENSOR_REFRESH_RATE
    sensor.range = SENSOR_RANGE
    time.sleep(0.1)
    return sensor


def collect_samples(sensor: adafruit_adxl37x.ADXL375, offset: float,
                    n: int = SAMPLES_PER_MESSAGE) -> List[float]:
    """
    Collects `n` x-axis acceleration samples from the given sensor,
    applying the offset to each.

    Args:
        sensor: ADXL375 sensor instance.
        offset: Offset to subtract from each raw reading.
        n: Number of samples to collect (default 16).

    Returns:
        List of float values (corrected acceleration in m/s²).
    """
    samples = []
    for _ in range(n):
        x = sensor.acceleration[0] - offset
        samples.append(x)
    return samples


def send_batch(mqttc: MQTTClient, batch: Batch) -> None:
    """
    Constructs and sends a binary message over MQTT with sensor data.

    Each message contains a binary descriptor and payload of 32-bit floats
    (acceleration in m/s²).
    The descriptor includes:
    - descriptor_length (uint16)
    - metadata_version (uint16)
    - seconds_since_epoch (uint64, set to 0)
    - nanoseconds (uint64, set to 0)
    - samples_from_daq_start (uint64)

    Args:
        mqttc (MQTTClient): The MQTT client.
        batch (Batch): A Batch object containing topic, samples, and sample counter.
    """
    descriptor_format = "<HHQQQ"
    descriptor_length = struct.calcsize(descriptor_format)
    descriptor = struct.pack(
        descriptor_format,
        descriptor_length,
        1,  # metadata version
        0, 0,  # no timestamp
        batch.sample_counter
    )
    data_payload = struct.pack(f"<{len(batch.samples)}f", *batch.samples)
    payload = descriptor + data_payload

    mqttc.publish(batch.topic, payload, qos=1, retain=False)

    print(f"\nPublishing to: {batch.topic}")
    print(f"Sample Counter: {batch.sample_counter}")
    print(f"Batch Size: {len(batch.samples)}")
    print(f"Samples: {batch.samples}")


def process_sensor(task: SensorTask, mqtt_client: MQTTClient,
                   mqtt_topic_base: str) -> int:
    """
    Processes one cycle of data acquisition and publishing for
    a given sensor task.

    This includes:
    - Enabling the sensor's multiplexer channel
    - Collecting a batch of x-axis acceleration data
    - Sending the batch to an MQTT topic

    Args:
        task (SensorTask): The task configuration for the sensor.
        mqtt_client (MQTTClient): The active MQTT client.
        mqtt_topic_base (str): The base MQTT topic path.

    Returns:
        int: The updated sample counter after the batch is published.
    """
    enable_multiplexer_channel(task.i2c, task.channel)
    samples = collect_samples(task.sensor, task.offset, task.batch_size)
    topic = f"{mqtt_topic_base}/{task.label}/acc/raw/data"
    send_batch(mqtt_client, Batch(topic, samples, task.counter))
    return task.counter + task.batch_size


def initialize_sensor(i2c: busio.I2C, channel: int,
                      label: str) -> adafruit_adxl37x.ADXL375:
    """
    Initializes and returns a configured sensor instance on the specified
    I2C multiplexer channel.

    Args:
        i2c (busio.I2C): The I2C bus.
        channel (int): The channel index to enable.
        label (str): Label for logging/debug output.

    Returns:
        adafruit_adxl37x.ADXL375: The configured sensor instance.
    """
    print(f"Initializing {label} on channel {channel}...")
    enable_multiplexer_channel(i2c, channel)
    return setup_sensor(i2c)


def main(config_path: str = "config/R-PI.json",
         offset_path: str = "config/offset.json",
         run_once: bool = False) -> None:
    config = load_config(config_path)
    mqtt_config = config["MQTT"]
    mqtt_client, _ = setup_mqtt_client(mqtt_config)

    mqtt_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    mqtt_client.loop_start()

    offset1, offset2 = load_offsets(offset_path)

    i2c = busio.I2C(board.SCL, board.SDA)
    sensors = {
        "Sensor1": initialize_sensor(i2c, 0, "Sensor1"),
        "Sensor2": initialize_sensor(i2c, 1, "Sensor2"),
    }
    counters = {"Sensor1": 0, "Sensor2": 0}
    mqtt_topic_base = "cpsens/DAQ_ID/MODULE_ID"

    while True:
        task1 = SensorTask(i2c=i2c, channel=0, label="Sensor1",
                           sensor=sensors["Sensor1"], offset=offset1,
                           batch_size=SAMPLES_PER_MESSAGE, counter=counters["Sensor1"])
        counters["Sensor1"] = process_sensor(task1, mqtt_client,
                                             mqtt_topic_base)

        task2 = SensorTask(i2c=i2c, channel=1, label="Sensor2",
                           sensor=sensors["Sensor2"], offset=offset2,
                           batch_size=SAMPLES_PER_MESSAGE, counter=counters["Sensor2"])
        counters["Sensor2"] = process_sensor(task2, mqtt_client,
                                             mqtt_topic_base)

        if run_once:
            break
        time.sleep(0.02)


if __name__ == "__main__":
    main()
