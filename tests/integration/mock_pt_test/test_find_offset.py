import pytest
from unittest.mock import patch, MagicMock, mock_open
import sys

# Mock hardware dependencies
sys.modules["board"] = MagicMock()
sys.modules["busio"] = MagicMock()
sys.modules["adafruit_adxl37x"] = MagicMock()

from mock_pt.find_offset import main
from integration.mock_pt_test.constants import (
    FAKE_START_TIME,
    TIME_STEP,
    NUM_FAKE_TIME_CALLS,
    ACCELERATION_SENSOR_1,
    ACCELERATION_SENSOR_2,
)

@pytest.mark.integration
@patch("mock_pt.find_offset.save_offset_config")
@patch("mock_pt.find_offset.load_config")
@patch("mock_pt.find_offset.enable_multiplexer_channel")
@patch("mock_pt.find_offset.adafruit_adxl37x.ADXL375")
@patch("mock_pt.find_offset.time.sleep", return_value=None)
def test_main_runs_without_hardware(
    mock_sleep,
    mock_adxl,
    mock_enable_mux,
    mock_load_config,
    mock_save_offset
):
    mock_load_config.return_value = {}
    sensor1 = MagicMock()
    sensor1.acceleration = ACCELERATION_SENSOR_1
    sensor2 = MagicMock()
    sensor2.acceleration = ACCELERATION_SENSOR_2
    mock_adxl.side_effect = [sensor1, sensor2]
    with patch("mock_pt.find_offset.time.time") as mock_time:
        mock_time.side_effect = [FAKE_START_TIME + i * TIME_STEP for i in range(NUM_FAKE_TIME_CALLS)]
        main()

    mock_save_offset.assert_called_once_with("config/offset.json", {
        "SensorOffsets": {
            "Sensor1": 1.0,
            "Sensor2": -2.0
        }
    })


@pytest.mark.integration
@patch("mock_pt.find_offset.save_offset_config")
@patch("mock_pt.find_offset.load_config", side_effect=FileNotFoundError("Simulated missing config"))
@patch("mock_pt.find_offset.enable_multiplexer_channel")
@patch("mock_pt.find_offset.adafruit_adxl37x.ADXL375")
@patch("mock_pt.find_offset.time.sleep", return_value=None)
def test_main_creates_offset_file_when_missing(
    mock_sleep,
    mock_adxl,
    mock_enable_mux,
    mock_load_config,
    mock_save_offset
):
    sensor1 = MagicMock()
    sensor1.acceleration = ACCELERATION_SENSOR_1
    sensor2 = MagicMock()
    sensor2.acceleration = ACCELERATION_SENSOR_2
    mock_adxl.side_effect = [sensor1, sensor2]
    with patch("mock_pt.find_offset.time.time") as mock_time:
        mock_time.side_effect = [FAKE_START_TIME + i * TIME_STEP for i in range(NUM_FAKE_TIME_CALLS)]
        main()

    mock_save_offset.assert_called_once_with("config/offset.json", {
        "SensorOffsets": {
            "Sensor1": 1.0,
            "Sensor2": -2.0
        }
    })


@pytest.mark.integration
@patch("mock_pt.find_offset.save_offset_config")
@patch("mock_pt.find_offset.enable_multiplexer_channel")
@patch("mock_pt.find_offset.adafruit_adxl37x.ADXL375")
@patch("mock_pt.find_offset.time.sleep", return_value=None)
@patch("builtins.open", new_callable=mock_open, read_data='{"SensorOffsets": {"Sensor1": 0.123, "Sensor2": 999.0}}')
def test_main_overwrites_existing_offset_json(
    mock_open_file,
    mock_sleep,
    mock_adxl,
    mock_enable_mux,
    mock_save_offset
):
    # Simulate existing offset.json with wrong values
    sensor1 = MagicMock()
    sensor1.acceleration = ACCELERATION_SENSOR_1  # [1.0, 1.0, ..., 1.0]
    sensor2 = MagicMock()
    sensor2.acceleration = ACCELERATION_SENSOR_2  # [-2.0, -2.0, ..., -2.0]
    mock_adxl.side_effect = [sensor1, sensor2]
    with patch("mock_pt.find_offset.time.time") as mock_time:
        mock_time.side_effect = [FAKE_START_TIME + i * TIME_STEP for i in range(NUM_FAKE_TIME_CALLS)]
        main()

    # The new values should overwrite old ones
    expected_overwritten_config = {
        "SensorOffsets": {
            "Sensor1": 1.0,
            "Sensor2": -2.0
        }
    }
    mock_save_offset.assert_called_once_with("config/offset.json", expected_overwritten_config)
