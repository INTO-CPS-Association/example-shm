import time
import pytest
import json
import numpy as np
from accel.hbk.Accelerometer import Accelerometer  # type: ignore

from collections import deque


class DummyMsg:
    """A dummy MQTT message to simulate incoming payloads."""
    def __init__(self, payload):
        self.payload = payload


@pytest.fixture
def dummy_mqtt_client():
    """
    Create a dummy MQTT client implementing the minimal methods required by Accelerometer.
    """
    class DummyMQTTClient:
        def __init__(self):
            self.on_message = None

        def subscribe(self, topic):
            self.topic = topic

        def loop_forever(self):
            pass  # Prevent blocking during tests

    return DummyMQTTClient()


@pytest.fixture
def accelerometer_instance(dummy_mqtt_client):
    """
    Creates an Accelerometer instance with a FIFO size of 100 for testing.
    """
    return Accelerometer(dummy_mqtt_client, topic="accelerometer/data", fifo_size=100)


def simulate_mqtt_messages(accel, messages):
    """
    Simulates incoming MQTT messages by calling _on_message() directly.
    """
    for msg_data in messages:
        msg_payload = json.dumps(msg_data).encode("utf-8")
        dummy_msg = DummyMsg(msg_payload)
        accel._on_message(None, None, dummy_msg)

    # Allow time for messages to be processed
    time.sleep(1) 

def test_accelerometer_read_full_fifo(accelerometer_instance):
    """
    Test Scenario 1: Read 100 samples when 100 are available.
    """
    messages = [{"accel_readings": {"x": i, "y": i * 2, "z": i * 3}} for i in range(100)]
    simulate_mqtt_messages(accelerometer_instance, messages)

    status, data = accelerometer_instance.read(requested_samples=100)

    # Verify status and shape
    assert status == 1  # Should return full requested amount
    assert data.shape == (100, 3)  # 100 samples, 3 axes (x, y, z)




def test_accelerometer_read_partial_fifo(accelerometer_instance):
    """
    Test Scenario 2: Read 50 samples when 100 are available (should return latest 50).
    """
    messages = [{"accel_readings": {"x": i, "y": i * 2, "z": i * 3}} for i in range(100)]
    simulate_mqtt_messages(accelerometer_instance, messages)

    # Read latest 50 samples
    status, data = accelerometer_instance.read(requested_samples=50)

    # Verify status and shape
    assert status == 1  # Full requested amount is available
    assert data.shape == (50, 3)  # 50 samples, 3 axes

    # Verify data contains latest 50 samples (should be from index 50 to 99)
    expected_x_values = np.arange(50, 100)  # X values should be [50, 51, ..., 99]
    assert np.allclose(data[:, 0], expected_x_values)


def test_accelerometer_read_insufficient_samples(accelerometer_instance):
    """
    Test Scenario 3: Read 100 samples when only 50 are available.
    """
    # Simulate only 50 messages in the FIFO
    messages = [{"accel_readings": {"x": i, "y": i * 2, "z": i * 3}} for i in range(50)]
    simulate_mqtt_messages(accelerometer_instance, messages)

    # Try to read 100 samples
    status, data = accelerometer_instance.read(requested_samples=100)

    # Verify status and shape
    assert status == 0  # Not enough samples available
    assert data.shape == (50, 3)  # Only 50 samples available


