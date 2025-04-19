import sys
import unittest
from unittest.mock import patch, MagicMock
import pytest

# Mock hardware modules
sys.modules["board"] = MagicMock()
sys.modules["busio"] = MagicMock()
sys.modules["adafruit_adxl37x"] = MagicMock()

from mock_PT.publish_samples import main
from mockPT_test.constants import FAKE_SAMPLES_1, FAKE_SAMPLES_2

pytestmark = pytest.mark.integration
class TestPublishIntegration(unittest.TestCase):

    @patch("mock_PT.publish_samples.send_batch")
    @patch("mock_PT.publish_samples.collect_samples")
    @patch("mock_PT.publish_samples.setup_sensor")
    @patch("mock_PT.publish_samples.enable_multiplexer_channel")
    @patch("mock_PT.publish_samples.setup_mqtt_client")
    @patch("mock_PT.publish_samples.load_config")
    def test_main_runs_once_no_hardware(
        self,
        mock_load_config,
        mock_setup_mqtt_client,
        mock_enable_mux,
        mock_setup_sensor,
        mock_collect,
        mock_send,
    ):
        # Config and MQTT client
        mock_load_config.return_value = {
            "MQTT": {
                "ClientID": "test-client",
                "host": "localhost",
                "port": 1883,
                "userId": "",
                "password": "",
                "QoS": 1,
                "TopicsToSubscribe": ["unused/topic"]
            }
        }
        mock_mqtt = MagicMock()
        mock_setup_mqtt_client.return_value = (mock_mqtt, "topic")

        # Return two sensors
        mock_sensor_1 = MagicMock()
        mock_sensor_2 = MagicMock()
        mock_setup_sensor.side_effect = [mock_sensor_1, mock_sensor_2]

        # Simulated sensor data
        mock_collect.side_effect = [FAKE_SAMPLES_1, FAKE_SAMPLES_2]

        # Patch builtins.open to return a fake offset config
        fake_offset_file = '{"SensorOffsets": {"Sensor1": 1.0, "Sensor2": -2.0}}'
        with patch("builtins.open", new_callable=unittest.mock.mock_open, read_data=fake_offset_file):
            with patch("mock_PT.publish_samples.time.sleep", return_value=None):
                main(run_once=True)

        # Assert samples were collected and sent for both sensors
        self.assertEqual(mock_collect.call_count, 2)
        self.assertEqual(mock_send.call_count, 2)


if __name__ == "__main__":
    unittest.main()
