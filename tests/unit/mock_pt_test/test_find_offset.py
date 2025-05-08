# pylint: disable=import-error
import sys
from unittest.mock import MagicMock, patch, mock_open
#  Mock hardware modules
sys.modules["board"] = MagicMock()
sys.modules["busio"] = MagicMock()
sys.modules["adafruit_adxl37x"] = MagicMock()

import unittest
import json
import os
import pytest



from unit.mock_pt_test.constants import (
    FAKE_START_TIME,
    TIME_STEP,
    NUM_FAKE_TIME_CALLS,
    ACCELERATION_SENSOR_1,
    ACCELERATION_SENSOR_2,
)
from pt_mock.find_offset import (
  calibrate_sensor,
  calibrate_on_channel,
  save_offset_config,
  load_config
)



pytestmark = pytest.mark.unit


class TestCalibrationUnit(unittest.TestCase):

    @patch("pt_mock.find_offset.time.time")
    def test_calibrate_sensor(self, mock_time):
        mock_sensor = MagicMock()
        mock_sensor.acceleration = ACCELERATION_SENSOR_1
        mock_sensor.range = 2
        mock_time.side_effect = iter(FAKE_START_TIME +
                                     i * TIME_STEP for i in range(NUM_FAKE_TIME_CALLS))
        result = calibrate_sensor(mock_sensor, "TestSensor", duration=10)
        self.assertAlmostEqual(result, 1.0, places=2)


    @patch("pt_mock.find_offset.adafruit_adxl37x.ADXL375")
    @patch("pt_mock.find_offset.enable_multiplexer_channel")
    def test_calibrate_on_channel(self, mock_enable_channel, mock_adxl):
        mock_sensor = MagicMock()
        mock_sensor.acceleration = ACCELERATION_SENSOR_2
        mock_adxl.return_value = mock_sensor
        with patch("pt_mock.find_offset.time.time") as mock_time:
            mock_time.side_effect = (
                FAKE_START_TIME +
                i * TIME_STEP for i in range(NUM_FAKE_TIME_CALLS)
            )
            offset = calibrate_on_channel(3, "SensorX", MagicMock(), duration=10)
            self.assertAlmostEqual(offset, 2.0, places=2)


    def test_save_offset_config(self):
        config = {"SensorOffsets": {"Sensor1": 1.0, "Sensor2": -0.5}}
        path = "test_offset.json"
        save_offset_config(path, config)

        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        self.assertEqual(loaded, config)
        os.remove(path)


    @patch("pt_mock.find_offset.time.time")
    def test_calibrate_sensor_zero_samples(self, mock_time):
        mock_sensor = MagicMock()
        mock_sensor.acceleration = ACCELERATION_SENSOR_1

        # Simulate start and end times being the same
        mock_time.side_effect = [1000, 1000]

        with self.assertRaises(ZeroDivisionError):
            calibrate_sensor(mock_sensor, "SensorZero", duration=0)


    @patch("builtins.open", new_callable=mock_open, read_data='{"MQTT": {"host": "localhost"}}')
    def test_load_config_success(self, mock_file):
        result = load_config("dummy/path.json")
        self.assertIn("MQTT", result)


    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_config_file_not_found(self, mock_file):
        with self.assertRaises(FileNotFoundError):
            load_config("nonexistent.json")


    @patch("builtins.open", new_callable=mock_open, read_data="not-json")
    def test_load_config_json_error(self, mock_file):
        with self.assertRaises(ValueError):
            load_config("corrupted.json")


    @patch("builtins.open", side_effect=Exception("weird crash"))
    def test_load_config_unexpected_exception(self, mock_file):
        with self.assertRaises(RuntimeError):
            load_config("unknown.json")
if __name__ == "__main__":
    unittest.main()
