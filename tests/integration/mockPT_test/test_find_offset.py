import sys
from unittest.mock import patch, MagicMock
import unittest
import pytest

# Mock hardware modules
sys.modules["board"] = MagicMock()
sys.modules["busio"] = MagicMock()
sys.modules["adafruit_adxl37x"] = MagicMock()

from mockPT_test.constants import FAKE_START_TIME, TIME_STEP, NUM_FAKE_TIME_CALLS, ACCELERATION_SENSOR_1, ACCELERATION_SENSOR_2
from mockpt.find_offset import main

pytestmark = pytest.mark.integration

class TestCalibrationIntegration(unittest.TestCase):
    @patch("mockpt.find_offset.save_offset_config")
    @patch("mockpt.find_offset.load_config")
    @patch("mockpt.find_offset.enable_multiplexer_channel")
    @patch("mockpt.find_offset.adafruit_adxl37x.ADXL375")
    @patch("mockpt.find_offset.time.sleep", return_value=None)
    def test_main_runs_without_hardware(
        self,
        mock_sleep,
        mock_adxl_class,
        mock_enable_channel,
        mock_load_config,
        mock_save_offset_config
    ):
        mock_load_config.return_value = {}

        mock_sensor1 = MagicMock()
        mock_sensor1.acceleration = ACCELERATION_SENSOR_1

        mock_sensor2 = MagicMock()
        mock_sensor2.acceleration = ACCELERATION_SENSOR_2

        mock_adxl_class.side_effect = [mock_sensor1, mock_sensor2]

        with patch("mockpt.find_offset.time.time") as mock_time:
            mock_time.side_effect = [FAKE_START_TIME + i * TIME_STEP for i in range(NUM_FAKE_TIME_CALLS)]
            main()

        expected_config = {
            "SensorOffsets": {
                "Sensor1": 1.0,
                "Sensor2": -2.0
            }
        }
        mock_save_offset_config.assert_called_once_with("config/offset.json", expected_config)


if __name__ == "__main__":
    unittest.main()
