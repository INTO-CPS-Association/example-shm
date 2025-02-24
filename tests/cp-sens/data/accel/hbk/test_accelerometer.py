# test_accelerometer.py
import time
import threading
import os
import sys
import pytest #type: ignore
import json



current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.abspath(os.path.join(current_dir, "../../../../../src/cp-sens/data"))
if data_dir not in sys.path:
    sys.path.insert(0, data_dir)

from accel.hbk.Accelerometer  import Accelerometer  #type: ignore



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
        def loop_start(self):
            pass
    return DummyMQTTClient()

def test_accelerometer_read_single(dummy_mqtt_client):
    """
    Test that Accelerometer.read() returns a single sample correctly.
    """
    # Instantiate Accelerometer with the dummy MQTT client and topic.
    accel = Accelerometer(dummy_mqtt_client, topic="accelerometer/data")
    
    # Prepare test data to simulate an MQTT message.
    test_timestamp = int(time.time() * 1000000)
    test_data = {
        "timestamp": test_timestamp,
        "accel": {
            "x": 1.1,
            "y": 2.2,
            "z": 3.3
        }
    }
    dummy_payload = json.dumps(test_data).encode("utf-8")
    dummy_msg = DummyMsg(dummy_payload)
    
    # Simulate message arrival after a short delay.
    def simulate_message():
        time.sleep(0.1)
        dummy_mqtt_client.on_message(None, None, dummy_msg)
    
    threading.Thread(target=simulate_message).start()
    
    # The result should be the simulated message.
    result = accel.read()
    
    # Verify the result.
    assert result["timestamp"] == test_timestamp
    assert result["accel"]["x"] == pytest.approx(1.1)
    assert result["accel"]["y"] == pytest.approx(2.2)
    assert result["accel"]["z"] == pytest.approx(3.3)

def test_accelerometer_read_multiple(dummy_mqtt_client):
    """
    Test that Accelerometer.read(samples=2) averages two samples correctly.
    """
    accel = Accelerometer(dummy_mqtt_client, topic="accelerometer/data")
    
    # Prepare two test messages.
    test_timestamp1 = int(time.time() * 1000000)
    data1 = {
        "timestamp": test_timestamp1,
        "accel": {"x": 1.0, "y": 2.0, "z": 3.0}
    }
    test_timestamp2 = test_timestamp1 + 1000
    data2 = {
        "timestamp": test_timestamp2,
        "accel": {"x": 3.0, "y": 4.0, "z": 5.0}
    }
    
    msg1 = DummyMsg(json.dumps(data1).encode("utf-8"))
    msg2 = DummyMsg(json.dumps(data2).encode("utf-8"))
    
    # Simulate two message arrivals.
    def simulate_messages():
        time.sleep(0.1)
        dummy_mqtt_client.on_message(None, None, msg1)
        time.sleep(0.1)
        dummy_mqtt_client.on_message(None, None, msg2)
    
    threading.Thread(target=simulate_messages).start()
    
    # Read two samples; the read method will average them.
    result = accel.read(samples=2)
    
    expected_avg = {
        "x": (1.0 + 3.0) / 2,
        "y": (2.0 + 4.0) / 2,
        "z": (3.0 + 5.0) / 2
    }
    
    # Use the timestamp from the second message.
    assert result["timestamp"] == test_timestamp2
    assert result["accel"]["x"] == pytest.approx(expected_avg["x"])
    assert result["accel"]["y"] == pytest.approx(expected_avg["y"])
    assert result["accel"]["z"] == pytest.approx(expected_avg["z"])
