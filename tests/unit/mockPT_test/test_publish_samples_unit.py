import unittest
from unittest.mock import MagicMock, patch
import struct
import sys
import pytest 

# Mock hardware before imports
sys.modules["board"] = MagicMock()
sys.modules["busio"] = MagicMock()
sys.modules["adafruit_adxl37x"] = MagicMock()

from mockpt.publish_samples import collect_samples, send_batch, Batch
from unit.mockPT_test.constants import FAKE_SENSOR_READING, FAKE_OFFSET, EXPECTED_COLLECTED_SAMPLES, SAMPLE_BATCH, SAMPLE_COUNTER


pytestmark = pytest.mark.integration
class TestPublishUnit(unittest.TestCase):

    def test_collect_samples_applies_offset(self):
        mock_sensor = MagicMock()
        mock_sensor.acceleration = FAKE_SENSOR_READING

        samples = collect_samples(mock_sensor, offset=FAKE_OFFSET, n=3)
        self.assertEqual(samples, EXPECTED_COLLECTED_SAMPLES)


    @patch("mockpt.publish_samples.MQTTClient.publish")
    def test_send_batch_publishes_correct_payload(self, mock_publish):
        mock_client = MagicMock()
        batch = Batch("fake/topic", SAMPLE_BATCH, SAMPLE_COUNTER)
        send_batch(mock_client, batch)

        # Verify publish was called
        mock_client.publish.assert_called_once()
        args, _ = mock_client.publish.call_args
        topic_arg, payload_arg = args[:2]

        self.assertEqual(topic_arg, "fake/topic")

        descriptor_size = struct.calcsize("<HHQQQ")
        expected_payload_size = descriptor_size + len(SAMPLE_BATCH) * 4
        self.assertEqual(len(payload_arg), expected_payload_size)


if __name__ == "__main__":
    unittest.main()
