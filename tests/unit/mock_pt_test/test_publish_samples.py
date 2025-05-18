# pylint: disable=import-error
import sys
from unittest.mock import MagicMock, patch

from io import StringIO
import struct
import unittest
import pytest

from unit.mock_pt_test.constants import (
    FAKE_SENSOR_READING,
    FAKE_OFFSET,
    EXPECTED_COLLECTED_SAMPLES,
    SAMPLE_BATCH,
    SAMPLE_COUNTER,
)

from pt_mock.publish_samples import collect_samples, send_batch, Batch, load_offsets, main
from pt_mock.constants import DEFAULT_OFFSET

# Mock hardware before imports
sys.modules["board"] = MagicMock()
sys.modules["busio"] = MagicMock()
sys.modules["adafruit_adxl37x"] = MagicMock()

pytestmark = pytest.mark.unit


class TestPublishUnit(unittest.TestCase):

    def test_collect_samples_applies_offset(self):
        mock_sensor = MagicMock()
        mock_sensor.acceleration = FAKE_SENSOR_READING

        samples = collect_samples(mock_sensor, offset=FAKE_OFFSET, n=3)
        self.assertEqual(samples, EXPECTED_COLLECTED_SAMPLES)


    @patch("pt_mock.publish_samples.MQTTClient.publish")
    def test_send_batch_publishes_correct_payload(self, _):
        mock_client = MagicMock()
        batch = Batch("fake/topic", SAMPLE_BATCH, SAMPLE_COUNTER)
        send_batch(mock_client, batch)

        # Check publish call
        mock_client.publish.assert_called_once()
        args, _ = mock_client.publish.call_args
        topic_arg, payload_arg = args[:2]

        self.assertEqual(topic_arg, "fake/topic")

        # Check payload size
        descriptor_size = struct.calcsize("<HHQQQ")
        expected_payload_size = descriptor_size + len(SAMPLE_BATCH) * 4
        self.assertEqual(len(payload_arg), expected_payload_size)

        # Check descriptor content
        descriptor = payload_arg[:descriptor_size]
        unpacked = struct.unpack("<HHQQQ", descriptor)
        self.assertEqual(unpacked[0], descriptor_size)  # descriptor_length
        self.assertEqual(unpacked[1], 1)  # metadata_version
        self.assertEqual(unpacked[4], SAMPLE_COUNTER)  # sample_counter


    @patch("pt_mock.publish_samples.MQTTClient.publish")
    def test_send_batch_with_empty_sample_list(self, _):
        mock_client = MagicMock()
        batch = Batch("test/empty", [], 0)
        send_batch(mock_client, batch)
        mock_client.publish.assert_called_once()
        args, _ = mock_client.publish.call_args
        descriptor_size = struct.calcsize("<HHQQQ")
        self.assertEqual(len(args[1]), descriptor_size)  # No sample data


    @patch("pt_mock.publish_samples.MQTTClient.publish")
    def test_send_batch_prints_expected_logs(self, _):
        mock_client = MagicMock()
        batch = Batch("test/topic", [0.1, 0.2], 99)

        with patch("sys.stdout", new_callable=StringIO) as fake_out:
            send_batch(mock_client, batch)
            output = fake_out.getvalue()
            self.assertIn("Publishing to: test/topic", output)
            self.assertIn("Sample Counter: 99", output)
            self.assertIn("Batch Size: 2", output)
            self.assertIn("Samples: [0.1, 0.2]", output)


    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="{ invalid json }")
    def test_load_offsets_returns_default_on_json_error(self, _):
        with patch("json.load", side_effect=ValueError("bad json")):
            offset1, offset2 = load_offsets("some_path.json")
            self.assertEqual((offset1, offset2), (DEFAULT_OFFSET, DEFAULT_OFFSET))


    @patch("pt_mock.publish_samples.send_batch")
    @patch("pt_mock.publish_samples.load_config")
    @patch("pt_mock.publish_samples.adafruit_adxl37x.ADXL375")
    @patch("pt_mock.publish_samples.time.sleep", return_value=None)
    def test_main_executes_sensor_loop_once(self, _, mock_adxl,
                                            mock_load_config, mock_send_batch):
        # Provide correct config structure
        mock_load_config.return_value = {
            "MQTT": {
                "ClientID": "test-client",
                "host": "mqtt.eclipseprojects.io",
                "port": 1883,
                "userId": "",
                "password": "",
                "QoS": 1,
                "TopicsToSubscribe": ["cpsens/test/sample/acc/raw/data"]
            }
        }

        mock_sensor = MagicMock()
        mock_sensor.acceleration = (1.0, 0.0, 0.0)
        mock_adxl.return_value = mock_sensor

        with patch("builtins.open", new_callable=unittest.mock.mock_open,
                   read_data='{"SensorOffsets": {"Sensor1": 0.0, "Sensor2": 0.0}}'):
            main(config_path="config/test.json", run_once=True)

        self.assertEqual(mock_send_batch.call_count, 2)

if __name__ == "__main__":
    unittest.main()
