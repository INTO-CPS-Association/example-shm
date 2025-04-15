
# Wind Turbine Mock Setup

![Photo of the physical mock setup, including Raspberry Pi and ADXL375 sensors.](figures/physical_setup.png)

## Purpose of the Mock Setup

The purpose of this physical setup is to act as a mock representation of a wind turbine (WT) foundation. It simulates the collection of vibration data in a controlled environment. The goal is to generate acceleration data from physical sensors that resemble the measurements collected from real WT structures.

Although the output of this setup is not used for operational decision making, it plays an important role in testing key components of the Digital Twin (DT) system. These components include data acquisition, calibration, processing, and real-time data streaming.

## Hardware and Layout Description

The physical setup consists of:

- Raspberry Pi 3 Model B+
- Two ADXL375 accelerometer sensors
- PCA9548 I²C multiplexer (enables connection of multiple I2C devices)
- A flexible mounting surface

The sensors are attached to a flexible ruler, which acts as a test structure. This structure can be subjected to vibration by applying airflow using a small fan, allowing the setup to mimic wind-induced structural movement.

Each of the ADXL375 sensors is connected to a separate channel on the PCA9548 I²C multiplexer, which in turn is connected to the I²C interface of the Raspberry Pi. This allows multiple sensors with the same I²C address to be used simultaneously by switching between them programmatically.

In the `publish_samples.py` script, the I²C interface is initialized using the `busio` and `board` libraries:

```python
i2c = busio.I2C(board.SCL, board.SDA)
```

The active channel on the multiplexer is selected by sending a control byte to its address (`0x70`). Each bit in the control byte corresponds to one of the eight possible channels. For example, enabling channel 0 is done by setting the first bit:

```python
def enable_multiplexer_channel(channel: int):
    multiplexer_address = 0x70
    i2c.writeto(multiplexer_address, bytes([1 << channel]))
    time.sleep(0.01)
```

After enabling a channel, the ADXL375 sensor connected to that channel is initialized by creating a new instance of the sensor driver and configuring its parameters such as data rate and measurement range:

```python
def setup_sensor():
    sensor = adafruit_adxl37x.ADXL375(i2c)
    sensor.data_rate = 10  # Hz
    sensor.range = 2       # ±200g
    time.sleep(0.1)
    return sensor
```

This procedure is repeated for each sensor by first enabling the corresponding multiplexer channel and then initializing the sensor. During the main acquisition loop, these steps are also used to switch between sensors before collecting new data.

## Sensor Calibration Process

Each sensor is calibrated to remove inherent bias before use. The `findoffset.py` script is used for this purpose. Before running the script, the sensors are placed on a stable surface. Then the x-axis readings are collected continuously over a duration of 10 seconds for each sensor. The average of these readings is computed and treated as the offset value, which represents the deviation from the expected resting value of 0 m/s². This offset is stored in a configuration file, which is later used in the publish_samples.py script to correct raw readings.

## Data Acquisition and Publishing

![Overview of the mock setup data pipeline](setup_Diagram.png)

Before starting the publish_samples.py script for collecting and publishing the data, a separate calibration script (`find_offset.py`) is executed to compute and store offset values in a configuration file. This offset represents the sensor's bias when resting and is used to correct all subsequent readings.

The `publish_samples.py` script is responsible for the full acquisition and publishing pipeline. It collects raw acceleration data from each sensor, applies the corresponding offset from the configuration file, then formats a binary message and publishes it to the MQTT broker.

Each message contains a descriptor and a payload of 32-bit floating point acceleration values (in m/s²).

The descriptor contains the following fields:

- `descriptor_length (uint16)`
- `metadata_version (uint16)`
- `seconds_since_epoch (uint64)`
- `nanoseconds (uint64)`
- `samples_from_daq_start (uint64)`

The `seconds_since_epoch` and `nanoseconds` fields are set to zero in this mock setup, as precise timestamping is not required. The `samples_from_daq_start` counter increments with each published batch and serves as a proxy for time.

In this setup, the sampling rate of the ADXL375 sensors is set to `20 Hz`, but it can be adjusted according to the testing requirements.

The MQTT topic naming follows the structure:

```
cpsens/DAQ_ID/MODULE_ID/CH_ID/acc/raw/data
```

Each sensor publishes its data to a unique topic. This structure supports organized data flow and facilitates integration with downstream components in the DT system.

The overall data flow is illustrated in the figure above.

The data acquisition and publishing process is implemented in Python and organized into modular functions. In the publish_samples.py script, the function `collect_samples` is responsible for retrieving raw acceleration readings from the sensor and applying the previously calculated offset. The sensor is read `n` times (default 32), and the x-axis values are corrected using the offset before being stored in a local list:

```python
def collect_samples(sensor, offset: float, n: int = 32) -> list:
    samples = []
    for _ in range(n):
        x = sensor.acceleration[0] - offset
        samples.append(x)
        time.sleep(0.005)
    return samples
```

Once a calibrated batch of samples has been collected, it is passed to the `send_batch` function. This function first constructs a binary descriptor containing descriptor length, metadata version, and the number of samples collected since the start of acquisition. In this mock setup, timestamp fields are not used and are set to zero. The data samples are then encoded as an array of 32-bit floating point values:

```python
descriptor = struct.pack("<HHQQQ", 28, 1, 0, 0, sample_counter)
data_payload = struct.pack(f"<{len(samples)}f", *samples)
```

Finally, the descriptor and data payload are concatenated into a single binary message and published to the appropriate MQTT topic using quality of service level 1:

```python
payload = descriptor + data_payload
mqttc.publish(topic, payload, qos=1, retain=False)
```

This structured messaging format ensures that each MQTT packet contains both descriptor and sensor readings in a consistent and machine-readable format.
