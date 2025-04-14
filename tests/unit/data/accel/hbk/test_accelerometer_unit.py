import struct
import threading
import pytest
import numpy as np
from unittest.mock import MagicMock
from data.accel.hbk.accelerometer import Accelerometer
from data.accel.metadata_constants import DESCRIPTOR_LENGTH_BYTES

pytestmark = pytest.mark.unit

@pytest.fixture
def mock_mqtt_client():
    return MagicMock()


@pytest.fixture
def test_accelerometer(mock_mqtt_client):
    return Accelerometer(mock_mqtt_client, topic="test/topic", map_size=128)

class MockMQTTMessage:
    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = payload


def make_mock_payload(start_key: int, num_samples: int = 32) -> bytes:
    descriptor_length = 28
    descriptor = struct.pack("<H H Q Q Q", descriptor_length, 1, 0, 0, start_key)
    data = struct.pack(f"<{num_samples}f", *[float(i + start_key) for i in range(num_samples)])
    return descriptor + data


def test_process_message_stores_data(test_accelerometer):
    key = 0
    payload = make_mock_payload(key)
    msg = MockMQTTMessage(topic="test/topic", payload=payload)

    test_accelerometer.process_message(msg)

    keys = test_accelerometer.get_sorted_keys()
    assert keys == [key]
    samples = test_accelerometer.get_samples_for_key(key)
    assert samples == [float(i + key) for i in range(32)]  


def test_get_batch_size(test_accelerometer):
    payload = make_mock_payload(200)
    msg = MockMQTTMessage("test/topic", payload)
    test_accelerometer.process_message(msg)

    batch_size = test_accelerometer.get_batch_size()
    assert batch_size == 32


def test_clear_used_data_removes_samples_and_keys(test_accelerometer):
    # Add three batches: 0–31, 32–63, 64–95
    for i in range(3):
        msg = MockMQTTMessage("test/topic", make_mock_payload(i * 32))
        test_accelerometer.process_message(msg)

    assert len(test_accelerometer.get_sorted_keys()) == 3

    # Remove 50 samples starting from key 32
    test_accelerometer.clear_used_data(32, 50)

    remaining_keys = test_accelerometer.get_sorted_keys()
    assert 0 not in remaining_keys

    remaining_samples = sum(len(test_accelerometer.get_samples_for_key(k)) for k in remaining_keys)
    print(f"Remaining keys: {remaining_keys}")
    print(f"Remaining samples: {remaining_samples}")

    # Batch at key 32: 32 samples
    # Batch at key 64: 32 samples
    # We removed 50 → should leave 64 - 50 = 14
    assert remaining_samples == 14


def test_read_fewer_than_available(test_accelerometer):
    for i in range(3):
        msg = MockMQTTMessage("test/topic", make_mock_payload(i * 32))
        test_accelerometer.process_message(msg)

    status, data = test_accelerometer.read(50)
    assert status == 1
    assert data.shape == (50,)
    assert np.allclose(data, np.arange(50))


def test_read_more_than_available_returns_partial(test_accelerometer):
    for i in range(2):
        msg = MockMQTTMessage("test/topic", make_mock_payload(i * 32))
        test_accelerometer.process_message(msg)

    status, data = test_accelerometer.read(96)
    assert status == 0
    assert data.shape == (64,)
    assert np.allclose(data, np.arange(64))


def test_get_samples_for_nonexistent_key_returns_none(test_accelerometer):
    assert test_accelerometer.get_samples_for_key(1234) is None

def test_get_batch_size_returns_none_when_empty(test_accelerometer):
    assert test_accelerometer.get_batch_size() is None


def test_on_message_invokes_process_in_thread(test_accelerometer, mocker):
    msg = MockMQTTMessage("test/topic", make_mock_payload(0))
    process_mock = mocker.patch.object(test_accelerometer, "process_message")
    thread_mock = mocker.patch("threading.Thread")

    test_accelerometer._on_message(None, None, msg)

    thread_mock.assert_called_once()
    assert thread_mock.call_args.kwargs["target"].__name__ == "safe_process"
    assert thread_mock.call_args.kwargs["daemon"] is True


def test_process_message_handles_short_payload(test_accelerometer, capsys):
    msg = MockMQTTMessage("test/topic", b"too short")
    test_accelerometer.process_message(msg)
    captured = capsys.readouterr()
    assert "Error processing message" in captured.out


def test_clear_used_data_across_many_keys(test_accelerometer):
    # Add 4 keys of 16 samples each = 64 samples
    for i in range(4):
        msg = MockMQTTMessage("test/topic", make_mock_payload(i * 16, num_samples=16))
        test_accelerometer.process_message(msg)

    keys_before = test_accelerometer.get_sorted_keys()
    assert len(keys_before) == 4

    test_accelerometer.clear_used_data(start_key=16, samples_to_remove=48)

    keys_after = test_accelerometer.get_sorted_keys()
    assert 0 not in keys_after
    remaining_samples = sum(len(test_accelerometer.get_samples_for_key(k)) for k in keys_after)
    assert remaining_samples == 0  # Because the first 16 is considered outdated, and got deleted also.


def test_read_across_batches(test_accelerometer):
    # Add 3 keys with 20 samples each = 60 total
    for i in range(3):
        msg = MockMQTTMessage("test/topic", make_mock_payload(i * 20, num_samples=20))
        test_accelerometer.process_message(msg)

    status, data = test_accelerometer.read(50)
    assert status == 1
    assert data.shape == (50,)
    assert np.allclose(data, np.arange(50))


def test_acquire_lock_returns_threading_lock(test_accelerometer):
    lock = test_accelerometer.acquire_lock()
    assert isinstance(lock, type(threading.Lock()))


def test_process_message_triggers_eviction_when_map_size_exceeded():

    acc = Accelerometer(mqtt_client=MagicMock(), topic="test/topic", map_size=64)

    # Add three batches: each has 32 samples (total 96), map_size is 64 → should trigger eviction
    for key in [0, 32, 64]:
        payload = make_mock_payload(key)
        msg = MockMQTTMessage(topic="test/topic", payload=payload)
        acc.process_message(msg)

    # Now only the two newest batches (32 and 64) should remain
    keys = acc.get_sorted_keys()
    assert keys == [32, 64], f"Eviction did not occur correctly. Remaining keys: {keys}"


def test_clear_used_data_with_zero_samples_to_remove_does_nothing(test_accelerometer):
    # Add a single batch
    msg = MockMQTTMessage("test/topic", make_mock_payload(0))
    test_accelerometer.process_message(msg)

    test_accelerometer.clear_used_data(0, 0)
    # Data should remain untouched
    assert test_accelerometer.get_sorted_keys() == [0]
    assert test_accelerometer.get_samples_for_key(0) == [float(i) for i in range(32)]
