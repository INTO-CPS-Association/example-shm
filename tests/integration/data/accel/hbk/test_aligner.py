import time
import json
import os
import pytest
import struct
import numpy as np

from data.accel.hbk.aligner import Aligner
from constants import DESCRIPTOR_LENGTH, METADATA_VERSION, SECONDS, NANOSECONDS, BATCH_SIZE
from data.comm.mqtt import setup_mqtt_client, load_config
import uuid

pytestmark = pytest.mark.integration
connect_delay = float(os.environ.get("MQTT_CONNECT_DELAY"))

@pytest.fixture(scope="function")
def mqtt_client_and_config():
    config = load_config("config/test.json")
    mqtt_config = config["MQTT"].copy()
    mqtt_config["ClientID"] = f"test_{uuid.uuid4().hex[:6]}"

    client, _ = setup_mqtt_client(mqtt_config, topic_index=0)
    client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    client.loop_start()
    time.sleep(connect_delay)

    yield client, mqtt_config

    client.loop_stop()
    client.disconnect()


@pytest.fixture(scope="function")
def mqtt_setup():
    config = load_config("config/test.json")
    mqtt_config = config["MQTT"].copy()
    mqtt_config["ClientID"] = f"test_{uuid.uuid4().hex[:6]}"

    # Setup MQTT client once
    client, _ = setup_mqtt_client(mqtt_config, 0)
    client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    client.loop_start()
    time.sleep(connect_delay)

    # Extract topics manually
    topics = [
        config["MQTT"]["TopicsToSubscribe"][0],
        config["MQTT"]["TopicsToSubscribe"][1],
        config["MQTT"]["TopicsToSubscribe"][2],
    ]

    yield client, topics

    client.loop_stop()
    client.disconnect()


def publish_samples(client, topic, values: np.ndarray, start_key: int):
    """
    Publishes a list of float values to the given MQTT topic using the expected binary format.
    Data is split into 32-sample batches (BATCH_SIZE).
    """
    for batch_start in range(0, len(values), BATCH_SIZE):
        batch_end = batch_start + BATCH_SIZE
        batch_values = values[batch_start:batch_end]
        data_bytes = b''.join([struct.pack("<f", float(v)) for v in batch_values])
        descriptor = struct.pack("<H H Q Q Q",
                                 DESCRIPTOR_LENGTH,
                                 METADATA_VERSION,
                                 SECONDS,
                                 NANOSECONDS,
                                 start_key + batch_start)
        payload = descriptor + data_bytes
        result = client.publish(topic, payload, qos=1)
        result.wait_for_publish()
    print(f"[PUBLISH DEBUG] Topic: {topic}, Start key: {start_key}, Batch size: {len(batch_values)}")


def test_aligner_continuous_block_required(mqtt_setup):
    client, topics = mqtt_setup
    aligner = Aligner(client, topics=topics, map_size=512)

    # CH1 and CH2: send full keys
    for key in [0, 32, 64, 96, 128, 160, 192, 224]:
        publish_samples(client, topics[0], np.arange(32), start_key=key)
        publish_samples(client, topics[1], np.arange(32), start_key=key)

    # CH3: skip key 64 to break continuity
    for key in [0, 32, 96, 128, 160, 192, 224]:
        publish_samples(client, topics[2], np.arange(32), start_key=key)

    time.sleep(1.5)  # Let messages arrive

    aligned, _ = aligner.extract(128)  # Should use keys 96, 128, 160, 192 (128 samples)

    assert aligned.shape == (3, 128), f"Expected 128 aligned rows, got {aligned.shape}"
    assert np.allclose(aligned[0, :5], np.arange(5)), "Check data from channel 1"
    assert np.allclose(aligned[2, :5], np.arange(5)), "Check data from channel 3"


def test_aligner_extract_removes_used_and_older_data(mqtt_setup):
    client, topics = mqtt_setup
    aligner = Aligner(client, topics=topics, map_size=512)

    # Send 5 batches (160 samples) to all 3 channels
    for key in [0, 32, 64, 96, 128]:
        for topic in topics:
            publish_samples(client, topic, np.arange(32), start_key=key)

    time.sleep(1)

    # Extract 96 samples → should consume keys 0, 32, 64 (96 samples)
    aligned, _ = aligner.extract(96)

    assert aligned.shape == (3, 96), "Expected 96 aligned samples"

    # Now check the internal maps
    for i, ch in enumerate(aligner.channels):
        with ch._lock:
            remaining_keys = list(ch.data_map.keys())
            print(f"[DEBUG] Channel {i+1} remaining keys after extract: {remaining_keys}")
            assert all(k > 64 for k in remaining_keys), \
                f"Channel {i+1} still contains old data (keys <= 64): {remaining_keys}"


def test_aligner_single_channel_extract_and_cleanup(mqtt_setup):
    client, topics = mqtt_setup
    one_topic = [topics[0]]  # Use only the first topic

    aligner = Aligner(client, topics=one_topic, map_size=512)

    # Publish 128 samples to the single channel (4 batches of 32)
    for key in [0, 32, 64, 96]:
        publish_samples(client, topics[0], np.arange(32) + key, start_key=key)

    time.sleep(1)

    # Extract 64 samples from the single channel
    extracted, _ = aligner.extract(64)

    assert extracted.shape == (1, 64), f"Expected shape (64, 1), got {extracted.shape}"
    assert np.allclose(extracted.flatten()[:5], [0, 1, 2, 3, 4]), "Unexpected values in extracted data"

    # Ensure keys 0 and 32 were removed, and 64+ remain
    ch = aligner.channels[0]
    with ch._lock:
        remaining_keys = list(ch.data_map.keys())
        print(f"[DEBUG] Remaining keys in single channel: {remaining_keys}")
        assert all(k > 32 for k in remaining_keys), f"Expected only keys > 32, but got {remaining_keys}"
