import sys
import time
import uuid
import struct
import pytest
import numpy as np
from unittest.mock import patch, MagicMock, mock_open

# Mock sensor-specific modules
sys.modules["board"] = MagicMock()
sys.modules["busio"] = MagicMock()
sys.modules["adafruit_adxl37x"] = MagicMock()

from mock_pt.publish_samples import main, send_batch, Batch, collect_samples, load_offsets, initialize_sensor
from mock_pt.constants import SAMPLES_PER_MESSAGE, SENSOR_REFRESH_RATE, SENSOR_RANGE
from data.comm.mqtt import setup_mqtt_client, load_config


@pytest.fixture(scope="function")
def mqtt_client():
    config = load_config("config/test.json")
    mqtt_config = config["MQTT"].copy()
    mqtt_config["ClientID"] = f"test_{uuid.uuid4().hex[:6]}"
    client, _ = setup_mqtt_client(mqtt_config)
    client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    client.loop_start()
    time.sleep(1.0)
    yield client
    client.loop_stop()
    client.disconnect()


def test_send_batch_actual_publish(mqtt_client):
    samples = [0.1 * i for i in range(SAMPLES_PER_MESSAGE)]
    batch = Batch(
        topic="cpsens/test/sample/acc/raw/data",
        samples=samples,
        sample_counter=123
    )
    send_batch(mqtt_client, batch)
    assert True  # No exceptions means success


def test_collect_samples_actual_offset():
    sensor_mock = MagicMock()
    sensor_mock.acceleration = (9.81, 0.0, 0.0)
    result = collect_samples(sensor_mock, offset=0.81, n=4)
    assert result == [9.0] * 4


@patch("mock_pt.publish_samples.setup_sensor")
@patch("mock_pt.publish_samples.enable_multiplexer_channel")
@patch("mock_pt.publish_samples.time.sleep", return_value=None)
def test_main_runs_once_with_real_mqtt(mock_sleep, mock_mux, mock_setup_sensor):
    mock_sensor = MagicMock()
    mock_setup_sensor.side_effect = [mock_sensor, mock_sensor]
    mock_sensor.acceleration = (1.0, 0.0, 0.0)

    main(config_path="config/test.json", run_once=True)
    assert True


@patch("builtins.open", new_callable=mock_open, read_data="not-a-valid-json")
def test_main_falls_back_when_offset_config_is_corrupt(mock_file):
    with patch("mock_pt.publish_samples.collect_samples", return_value=[0.0] * SAMPLES_PER_MESSAGE), \
         patch("mock_pt.publish_samples.setup_sensor") as mock_sensor, \
         patch("mock_pt.publish_samples.send_batch") as mock_send, \
         patch("mock_pt.publish_samples.enable_multiplexer_channel"), \
         patch("mock_pt.publish_samples.setup_mqtt_client") as mock_mqtt, \
         patch("mock_pt.publish_samples.load_config") as mock_config:

        mock_config.return_value = {
            "MQTT": {
                "ClientID": "test-client",
                "host": "localhost",
                "port": 1883,
                "userId": "",
                "password": "",
                "QoS": 1,
                "TopicsToSubscribe": ["topic1"]
            }
        }
        mock_sensor.return_value = MagicMock()
        mock_mqtt.return_value = (MagicMock(), "topic")
        with patch("mock_pt.publish_samples.time.sleep", return_value=None):
            main(run_once=True)
        assert mock_send.call_count == 2


def test_load_offsets_returns_correct_values_from_file():
    fake_file_content = '{"SensorOffsets": {"Sensor1": 1.23, "Sensor2": -4.56}}'
    with patch("builtins.open", new_callable=mock_open, read_data=fake_file_content):
        offset1, offset2 = load_offsets("config/fake.json")
        assert offset1 == 1.23
        assert offset2 == -4.56



@patch("mock_pt.publish_samples.adafruit_adxl37x.ADXL375")
@patch("mock_pt.publish_samples.time.sleep", return_value=None)
@patch("mock_pt.publish_samples.enable_multiplexer_channel")
def test_initialize_sensor_sets_refresh_rate_and_range(
    mock_enable_mux, mock_sleep, mock_adxl_class
):
    # Create two fake sensors
    mock_sensor1 = MagicMock()
    mock_sensor2 = MagicMock()
    mock_adxl_class.side_effect = [mock_sensor1, mock_sensor2]
    i2c = MagicMock()
    # Call twice to simulate both sensors being setup
    sensor1 = initialize_sensor(i2c, channel=0, label="Sensor1")
    sensor2 = initialize_sensor(i2c, channel=1, label="Sensor2")
    # Ensure multiplexer was called with correct channels
    mock_enable_mux.assert_any_call(i2c, 0)
    mock_enable_mux.assert_any_call(i2c, 1)
    assert mock_enable_mux.call_count == 2

    # Assert that the refresh rate and range were set
    assert mock_sensor1.data_rate == SENSOR_REFRESH_RATE
    assert mock_sensor1.range == SENSOR_RANGE
    assert mock_sensor2.data_rate == SENSOR_REFRESH_RATE
    assert mock_sensor2.range == SENSOR_RANGE

    # Return values should match the mocked sensor objects
    assert sensor1 == mock_sensor1
    assert sensor2 == mock_sensor2
