import time
import json
import board  # type: ignore
import busio  # type: ignore
import adafruit_adxl37x  # type: ignore

# Initialize I2C
i2c = busio.I2C(board.SCL, board.SDA)

def enable_multiplexer_channel(channel):
    multiplexer_address = 0x70
    i2c.writeto(multiplexer_address, bytes([1 << channel]))
    time.sleep(0.01)

# Load configuration file (offset.json)
config_path = "config/offset.json"
try:
    with open(config_path, "r") as f:
        offset_config = json.load(f)
    print("Configuration loaded successfully.")
except Exception as e:
    print(f"Error loading configuration: {e}")
    offset_config = {}

# Ensure that SensorOffsets are set if not already defined
if "SensorOffsets" not in offset_config:
    offset_config["SensorOffsets"] = {"Sensor1": 0, "Sensor2": 0}

def calibrate_sensor(sensor, sensor_label, duration=10):
    """
    Calibrates an ADXL375 sensor using its processed acceleration values.
    Collects sensor.acceleration data for 'duration' seconds, computes the average
    for the x-axis, and calculates the offset as:
        offset = (average reading) - (expected reading for x-axis)
    """
    print(f"Calibrating {sensor_label}: please hold the sensor flat for {duration} seconds...")
    sensor.range = 2 
    start_time = time.time()
    samples = []
    while time.time() - start_time < duration:
        reading = sensor.acceleration
        samples.append(reading[0])  # Only use x-axis values

    n = len(samples)
    avg_x = sum(samples) / n
    print(f"Average acceleration for {sensor_label} (x-axis): {avg_x:.2f} m/s²")

    # The expected value for the x-axis when the sensor is flat is 0 (no acceleration)
    offset_x = avg_x
    print(f"Calculated offset for {sensor_label} (x-axis): {offset_x:.2f}")

    return offset_x

def main():
    print("Starting calibration for both sensors...")

    # Calibrate Sensor 1 on multiplexer channel 0
    enable_multiplexer_channel(0)
    time.sleep(0.2)
    sensor1 = adafruit_adxl37x.ADXL375(i2c)
    time.sleep(0.5)
    offset1 = calibrate_sensor(sensor1, "Sensor1")
    time.sleep(0.2)

    # Calibrate Sensor 2 on multiplexer channel 1
    enable_multiplexer_channel(1)
    time.sleep(0.5)
    sensor2 = adafruit_adxl37x.ADXL375(i2c)
    time.sleep(0.2)
    offset2 = calibrate_sensor(sensor2, "Sensor2")

    # Update configuration with the new sensor offsets
    offset_config["SensorOffsets"]["Sensor1"] = offset1  
    offset_config["SensorOffsets"]["Sensor2"] = offset2  

    with open(config_path, "w") as f:
        json.dump(offset_config, f, indent=4)
    print("Calibration complete. Offsets updated in offset.json.")

if __name__ == "__main__":
    main()


