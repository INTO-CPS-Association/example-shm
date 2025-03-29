import time
import json
import pytest
import struct

import numpy as np
from data.accel.hbk.Accelerometer import Accelerometer  # type: ignore
from constants import DESCRIPTOR_LENGTH, METADATA_VERSION, SECONDS, NANOSECONDS, BATCH_SIZE
from data.sources.mqtt import setup_mqtt_client, load_config
import uuid


@pytest.fixture(scope="function")
def mqtt_client():
    config = load_config("config/test.json")
    mqtt_config = config["MQTT"].copy()
    mqtt_config["ClientID"] = f"test_{uuid.uuid4().hex[:6]}"  

    topic_index = 0  
    client, selected_topic = setup_mqtt_client(mqtt_config, topic_index)  

    client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    client.loop_start()  
    time.sleep(0.1)  

    yield client, selected_topic
    client.loop_stop()
    client.disconnect()


@pytest.fixture(scope="function")
def client_and_topic(mqtt_client):
    client, topic = mqtt_client
    return client, topic


@pytest.fixture(scope="function")
def accelerometer_instance(client_and_topic):
    client, topic = client_and_topic 
    return Accelerometer(client, topic=topic, map_size=192)


@pytest.fixture(autouse=True)
def clear_fifo(accelerometer_instance):
    with accelerometer_instance._lock:
        accelerometer_instance.data_map.clear()
    yield



def publish_binary_samples(client, topic, start, end):
    """Helper function to publish  32 samples per message."""
    for batch_start in range(start, end, BATCH_SIZE):  
        batch_end = min(batch_start + BATCH_SIZE, end)  
        data_samples = [struct.pack("<f", float(i)) for i in range(batch_start, batch_end)]

        descriptor = struct.pack("<H H Q Q Q", DESCRIPTOR_LENGTH, METADATA_VERSION, SECONDS, NANOSECONDS, batch_start)
        payload = descriptor + b"".join(data_samples)

        result = client.publish(topic, payload, qos=1)
        result.wait_for_publish()  









def test_accelerometer_read_in_steps(client_and_topic, accelerometer_instance):
    """
    Test that reading in steps correctly retrieves the oldest samples 
    while removing only the requested number of samples.

    Steps:
    1. Publish 64 samples with values 0 to 63.
    2. Read 30 samples -> Expect [0, 1, ..., 29].
    3. Read another 30 samples -> Expect [30, 31, ..., 59].
    4. Verify:
       - The retrieved samples match the expected sequences.
       - The remaining samples in the buffer match expectations.
    """
    client, topic = client_and_topic  

    # Step 1: Publish 64 samples (values 0 to 63)
    publish_binary_samples(client, topic, 0, 64)
    total_samples = 0

    while total_samples < 64:  
        with accelerometer_instance._lock:
            total_samples = sum(len(deque) for deque in accelerometer_instance.data_map.values())

    # Read the first 30 samples
    status_1, data_1 = accelerometer_instance.read(30)
    assert np.allclose(data_1, np.arange(30)), f"Order mismatch: {data_1[:10]}"

    # Read the next 30 samples
    status_2, data_2 = accelerometer_instance.read(30)
    assert np.allclose(data_2, np.arange(30, 60)), f"Order mismatch: {data_2[:10]}"

    with accelerometer_instance._lock:
        remaining_samples = sum(len(deque) for deque in accelerometer_instance.data_map.values())

    assert remaining_samples == 4, f"Expected 4 samples left, but found {remaining_samples}"



def test_accelerometer_read_full_fifo(client_and_topic, accelerometer_instance):
    """
    Test that the accelerometer correctly stores and retrieves the full FIFO capacity.

    Steps:
    1. Publish exactly 96 samples.
    2. Read all 96 samples.
    3. Verify:
       - The status is 1 (all requested samples retrieved).
       - The shape is (96,).
       - The data is in sequential order from 0 to 95.
    """
    client, topic = client_and_topic  

    publish_binary_samples(client, topic, 0, 96)
    total_samples = 0

    while total_samples < 96: 
        with accelerometer_instance._lock:
            total_samples = sum(len(deque) for deque in accelerometer_instance.data_map.values())

    status, data = accelerometer_instance.read(96)

    assert status == 1, f"Expected status 1, but got {status}"
    assert data.shape == (96,), f"Unexpected shape: {data.shape}" 
    assert np.allclose(data, np.arange(96)), f"Order mismatch: {data[:10]}"


def test_accelerometer_read_partial_fifo(client_and_topic, accelerometer_instance):
    """
    Test that when reading fewer samples than available, the oldest samples are retrieved.

    Steps:
    1. Publish 64 samples.
    2. Read only 32 samples.
    3. Verify:
       - The status is 1 (exact number of requested samples retrieved).
       - The shape is (32,).
       - The first 32 samples (0–31) are retrieved.
    """
    client, topic = client_and_topic  

    publish_binary_samples(client, topic, 0, 64)
    total_samples = 0

    while total_samples < 64: 
        with accelerometer_instance._lock:
            total_samples = sum(len(deque) for deque in accelerometer_instance.data_map.values())

    status, data = accelerometer_instance.read(32)

    assert np.allclose(data, np.arange(32)), f"Order mismatch: {data[:10]}"
    assert status == 1, f"Expected status 1, but got {status}"
    assert data.shape == (32,), f"Unexpected shape: {data.shape}" 


def test_accelerometer_read_insufficient_samples(client_and_topic, accelerometer_instance):
    """
    Test that the accelerometer correctly handles cases where fewer samples exist than requested.

    Steps:
    1. Publish 64 samples.
    2. Request 96 samples (more than available).
    3. Verify:
       - The status is 0 (not enough samples).
       - The shape is (64,).
       - All 64 samples are returned.
    """
    client, topic = client_and_topic  

    publish_binary_samples(client, topic, 0, 64)
    total_samples = 0

    while total_samples < 64: 
        with accelerometer_instance._lock:
            total_samples = sum(len(deque) for deque in accelerometer_instance.data_map.values())

    status, data = accelerometer_instance.read(96)

    assert status == 0, f"Expected status 0, but got {status}"
    assert data.shape == (64,), f"Unexpected shape: {data.shape}" 


def test_accelerometer_appending_more_samples_than_max(client_and_topic, accelerometer_instance):
    """
    Test that when publishing more than the max FIFO size, only the most recent data is stored.

    The max FIFO size is set to 192, but we publish 224 samples.

    Steps:
    1. Publish 224 samples.
    2. Request all 224 samples (to check if old ones were removed).
    3. Verify:
       - The status is 0 (not all requested samples are available).
       - The shape is (192,).
    """
    client, topic = client_and_topic  

    publish_binary_samples(client, topic, 0, 224)
    total_samples = 0

    while total_samples < 192: 
        with accelerometer_instance._lock:
            total_samples = sum(len(deque) for deque in accelerometer_instance.data_map.values())

    status, data = accelerometer_instance.read(224)

    assert status == 0, f"Expected status 0, but got {status}"
    assert data.shape == (192,), f"Unexpected shape: {data.shape}" 






def test_accelerometer_reordering_late_sample(client_and_topic, accelerometer_instance):
    """
    Simulates delayed delivery of the middle batch (32-63) and checks if the accelerometer correctly 
    orders samples based on `samples_from_daq_start`.
    """
    client, topic = client_and_topic

    # Publish first batch (0–31)
    publish_binary_samples(client, topic, 0, 32)

    # Publish last batch (64–95) BEFORE the middle batch
    publish_binary_samples(client, topic, 64, 96)

    # Publish middle batch (32–63) AFTER last batch
    publish_binary_samples(client, topic, 32, 64)

    # Wait for all samples to arrive
    total_samples = 0
    while total_samples < 96:  # Max wait time: 5 seconds
        with accelerometer_instance._lock:
            total_samples = sum(len(deque) for deque in accelerometer_instance.data_map.values())
    status, data = accelerometer_instance.read(96)


    assert status == 1, f"Expected status 1, but got {status}"
    assert data.shape == (96,), f"Unexpected shape: {data.shape}"
    expected_data = np.arange(96)  # Expected: 0, 1, 2, ..., 95
    assert np.allclose(data, expected_data), f"Data order mismatch! Got: {data[:10]}..."



