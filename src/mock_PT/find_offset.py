import time
import json
from typing import Any, Dict
import busio  # pylint: disable=import-error
import board  # pylint: disable=import-error
import adafruit_adxl37x  # pylint: disable=import-error

from data.comm.mqtt import load_config
from mock_pt.constants import CALIBRATION_TIME, SENSOR_RANGE, DEFAULT_OFFSET
# Initialize I2C
i2c: busio.I2C = busio.I2C(board.SCL, board.SDA)

def enable_multiplexer_channel(channel: int) -> None:
    """
    Enables the specified channel on the I2C multiplexer (e.g., TCA9548A).
    
    Args:
        channel (int): The channel index to enable (0-7).
    """
    multiplexer_address: int = 0x70
    i2c.writeto(multiplexer_address, bytes([1 << channel]))
    time.sleep(0.01)


def save_offset_config(path: str, config: Dict[str, Any]) -> None:
    """
    Saves the offset configuration dictionary to a JSON file.

    Args:
        path (str): File path to save the configuration.
        config (Dict[str, Any]): The configuration data.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def calibrate_sensor(sensor: Any, sensor_label: str,
                     duration: int = CALIBRATION_TIME) -> float:
    """
    Calibrates an ADXL375 sensor by collecting acceleration values from
    the x-axis over a specified duration and computing the average
    as the offset.

    Args:
        sensor (Any): An instance of the ADXL375 sensor.
        sensor_label (str): A label for identifying the sensor during output.
        duration (int): Duration in seconds to collect data (default is 10).

    Returns:
        float: Calculated x-axis offset.
    """
    print(f"Calibrating {sensor_label}: please hold the sensor flat "
          f"for {duration} seconds...")
    sensor.range = SENSOR_RANGE
    start_time: float = time.time()
    samples: list[float] = []

    while time.time() - start_time < duration:
        reading: tuple[float, float, float] = sensor.acceleration
        samples.append(reading[0])  # x-axis

    avg_x: float = sum(samples) / len(samples)
    print(f"Average acceleration for {sensor_label} (x-axis): "
          f"{avg_x:.2f} m/s²")
    offset_x: float = avg_x
    print(f"Calculated offset for {sensor_label} (x-axis): "
          f"{offset_x:.2f} m/s²")

    return offset_x


def calibrate_on_channel(channel: int, label: str, i2c_bus: busio.I2C,
                         duration: int = 10) -> float:
    """
    Activates a multiplexer channel, initializes a sensor on that channel,
    and performs calibration.

    Args:
        channel (int): The multiplexer channel to activate.
        label (str): Sensor label used in output logs.
        i2c_bus (busio.I2C): The shared I2C bus.
        duration (int): Duration in seconds to calibrate (default is 10).

    Returns:
        float: Computed x-axis offset for the sensor.
    """
    enable_multiplexer_channel(channel)
    time.sleep(0.5)
    sensor = adafruit_adxl37x.ADXL375(i2c_bus)
    time.sleep(0.2)
    return calibrate_sensor(sensor, label, duration)


def main() -> None:
    """
    Main routine for calibrating two ADXL375 sensors on different
    I2C multiplexer channels.
    Results are saved to a JSON config file.
    """
    print("Starting calibration for both sensors...")
    config_path: str = "config/offset.json"
    try:
        config = load_config(config_path)
    except FileNotFoundError:
        print("Offset config not found — creating new one.")
        config = {"SensorOffsets": {"Sensor1": DEFAULT_OFFSET, "Sensor2": DEFAULT_OFFSET}}

    if "SensorOffsets" not in config:
        config["SensorOffsets"] = {"Sensor1": DEFAULT_OFFSET, "Sensor2": DEFAULT_OFFSET}

    offset1: float = calibrate_on_channel(0, "Sensor1", i2c)
    offset2: float = calibrate_on_channel(1, "Sensor2", i2c)

    config["SensorOffsets"]["Sensor1"] = offset1
    config["SensorOffsets"]["Sensor2"] = offset2

    save_offset_config(config_path, config)
    print("Calibration complete. Offsets updated in offset.json.")

if __name__ == "__main__":
    main()
