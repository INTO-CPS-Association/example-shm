import sys
from unittest.mock import MagicMock, patch
import unittest
import json
import os
import pytest 

#  Mock hardware modules
sys.modules["board"] = MagicMock()
sys.modules["busio"] = MagicMock()
sys.modules["adafruit_adxl37x"] = MagicMock()

from unit.mockPT_test.constants import FAKE_START_TIME, TIME_STEP, NUM_FAKE_TIME_CALLS, ACCELERATION_SENSOR_1, ACCELERATION_SENSOR_2
from mock_PT.find_offset import calibrate_sensor, calibrate_on_channel, save_offset_config

pytestmark = pytest.mark.integration

class TestCalibrationUnit(unittest.TestCase):

    @patch("mock_PT.find_offset.time.time")
    def test_calibrate_sensor(self, mock_time):
        mock_sensor = MagicMock()
        mock_sensor.acceleration = ACCELERATION_SENSOR_1
        mock_sensor.range = 2

        mock_time.side_effect = iter(FAKE_START_TIME + i * TIME_STEP for i in range(NUM_FAKE_TIME_CALLS))
        result = calibrate_sensor(mock_sensor, "TestSensor", duration=10)
        self.assertAlmostEqual(result, 1.0, places=2)


    @patch("mock_PT.find_offset.adafruit_adxl37x.ADXL375")
    @patch("mock_PT.find_offset.enable_multiplexer_channel")
    def test_calibrate_on_channel(self, mock_enable_channel, mock_adxl):
        mock_sensor = MagicMock()
        mock_sensor.acceleration = ACCELERATION_SENSOR_2
        mock_adxl.return_value = mock_sensor

        with patch("mock_PT.find_offset.time.time") as mock_time:
            mock_time.side_effect = iter(FAKE_START_TIME + i * TIME_STEP for i in range(NUM_FAKE_TIME_CALLS))
            offset = calibrate_on_channel(3, "SensorX", MagicMock(), duration=10)
            self.assertAlmostEqual(offset, 2.0, places=2)


    def test_save_offset_config(self):
        config = {"SensorOffsets": {"Sensor1": 1.0, "Sensor2": -0.5}}
        path = "test_offset.json"
        save_offset_config(path, config)

        with open(path, "r") as f:
            loaded = json.load(f)

        self.assertEqual(loaded, config)
        os.remove(path)


if __name__ == "__main__":
    unittest.main()
