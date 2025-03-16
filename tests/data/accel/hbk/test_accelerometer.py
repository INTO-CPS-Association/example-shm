import time
import json
import pytest
import numpy as np
from data.accel.hbk.Accelerometer import Accelerometer  # type: ignore
from data.sources.mqtt import setup_mqtt_client, load_config
from data.accel.constants import LATENT_DATA_INDEX
import time
import uuid



@pytest.fixture(scope="function")
def mqtt_client():
    """
    Creates and configures an MQTT client for testing.

    - Loads the MQTT configuration from a JSON file.
    - Extracts the "default" profile from the configuration.
    - Generates a unique `ClientID` to prevent conflicts during testing.
    - Initializes and connects an MQTT client.
    - Ensures the client is disconnected after the test is complete.

    Returns:
        Tuple: (paho.mqtt.client.Client, str) Configured MQTT client instance and the selected topic.
    """
    config = load_config("src/config/mqtt.json")
    mqtt_config = config["MQTT"]["default"].copy()  # Extract the "default" profile
    
    # Generate unique client ID
    mqtt_config["ClientID"] = f"test_{uuid.uuid4().hex[:6]}"  

    topic_index = 0  # Set the index of the topic to subscribe to 

    # Pass the mqtt_config and topic_index
    client, selected_topic = setup_mqtt_client(mqtt_config, topic_index)  

    client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    yield client, selected_topic
    client.disconnect()  # Ensure client is disconnected after each test

@pytest.fixture(scope="function")
def client_and_topic(mqtt_client):
    client, topic = mqtt_client
    return client, topic

@pytest.fixture(scope="function")
def accelerometer_instance(client_and_topic):
    """
    Creates a new Accelerometer instance for testing.

    - Uses the `client_and_topic` fixture to provide an initialized MQTT client.
    - Creates an `Accelerometer` instance subscribed to the selected topic.
    - Ensures a fresh instance is provided for each test.

    Parameters:
        client: The pre-configured MQTT client.

    Returns:
        Accelerometer: A new instance of the Accelerometer class for testing.
    """
    client, topic = client_and_topic 
    return Accelerometer(
        client, 
        topic=topic, 
        fifo_size=100
    )

@pytest.fixture(autouse=True)
def clear_fifo(accelerometer_instance):
    """Automatically clears the FIFO buffer before each test."""
    with accelerometer_instance._lock:
        accelerometer_instance._fifo.clear()
        accelerometer_instance._timestamps.clear()
    yield






def test_accelerometer_read_full_fifo(client_and_topic, accelerometer_instance):
    client, topic = client_and_topic  
    # Publish 
    for i in range(100):
        payload = json.dumps({
            "descriptor": {
                "timestamp": i,  # 0,1,2...99
                "length": 10,
                "metadata_version": 1
            },
            "data": {
                "type": "double",
                "values": [i, i*2, i*3]
            }
        })
        client.publish(topic, payload)

    # Verify FIFO contents
    while len(accelerometer_instance._fifo) < 100:
        print("Waiting to fill FIFO", len(accelerometer_instance._fifo))
    
    status, data = accelerometer_instance.read(100)
    assert status == 1
    assert np.allclose(data[:, 0], np.arange(100)), \
        f"Order mismatch. Here is the first 10 entries: {data[:10, 0]}"






def test_accelerometer_read_partial_fifo(client_and_topic, accelerometer_instance):
    client, topic = client_and_topic 
    for i in range(100):
        payload = json.dumps({
            "descriptor": {
                "timestamp": i,  # 0,1,2...99
                "length": 10,
                "metadata_version": 1
            },
            "data": {
                "type": "double",
                "values": [i, i*2, i*3]
            }
        })
        client.publish(topic, payload)

    # Verify FIFO contents
    while len(accelerometer_instance._fifo) < 100:
        print("wating to fill FIFO",len(accelerometer_instance._fifo))
    
    status, data = accelerometer_instance.read(50)

    # Verify status and shape
    assert status == 1  # Full requested amount is available
    assert data.shape == (50, 3)  # 50 samples, 3 axes

    # Verify data contains latest 50 samples 
    expected_x_values = np.arange(50, 100)  # X values should be [50, 51, ..., 99]
    assert np.allclose(data[:, 0], expected_x_values)
    





def test_accelerometer_read_insufficient_samples(client_and_topic, accelerometer_instance):
    client, topic = client_and_topic 
    """
    Test Scenario: Read 100 samples when only 50 are available. Status should be 0.
    """

    # Publish only 50 samples 
    for i in range(50):
        payload = json.dumps({
            "descriptor": {
                "timestamp": i,  # 0-49
                "length": 10,
                "metadata_version": 1
            },
            "data": {
                "type": "double",
                "values": [i, i*2, i*3]
            }
        })
        client.publish(topic, payload)

    
    while len(accelerometer_instance._fifo) < 50:
        print("Waiting for FIFO to reach 50 samples", len(accelerometer_instance._fifo))

    # Attempt to read 100 samples
    status, data = accelerometer_instance.read(100)

    # Verify status and results
    assert status == 0, f"Expected status 0, got {status}"
    assert data.shape == (50, 3), f"Expected shape (50,3), got {data.shape}"
    
    # Verify all available samples are returned
    if data.shape[0] > 0:
        assert np.allclose(data[:, 0], np.arange(50)), \
            f"Data mismatch. Here is the   first 10 entries: {data[:10, 0]}"
        







def test_accelerometer_appending_more_samples_than_max(client_and_topic, accelerometer_instance):
    client, topic = client_and_topic 

    # Publish 100 samples (0-99)
    for i in range(100):
        payload = json.dumps({
            "descriptor": {"timestamp": i, "length": 10, "metadata_version": 1},
            "data": {"values": [i, i*2, i*3]}
        })
        client.publish(topic, payload)  


    while len(accelerometer_instance._fifo) < 100:
        print (len(accelerometer_instance._fifo))


    # Publish 50 new samples (100-149)
    for i in range(100, 150):
        payload = json.dumps({
            "descriptor": {"timestamp": i, "length": 10, "metadata_version": 1},
            "data": {"values": [i, i*2, i*3]}
        })
        client.publish(topic, payload)

    time.sleep(0.5) # Needed to remove old data and append new

    # THe FIFO max size is set at 100, so now the FIFO should only contain the latest 100 samples i.e (50-149) for the X axis

    status, data = accelerometer_instance.read(100)
    assert status == 1, f"Status {status} with {len(data)} samples"
    assert data.shape == (100, 3), f"Unexpected shape {data.shape}"
    
    # Verify samples 50-149 (oldest 50 should have been trimmed)
    expected_x = np.arange(50, 150)
    assert np.allclose(data[:, 0], expected_x), \
        f"First entries: {data[:100, 0]}\nExpected start: 50-149"





def test_accelerometer_reordering_late_sample(client_and_topic, accelerometer_instance):
    client, topic = client_and_topic 
    """
    Test Scenario: Late-arriving samples are inserted in correct position
    """

    # Publish all samples except timestamp 3 
    for i in range(10):
        if i == LATENT_DATA_INDEX:
            continue  # Skip the late sample
        payload = json.dumps({
            "descriptor": {
                "timestamp": i,
                "length": 10,
                "metadata_version": 1
            },
            "data": {
                "type": "double",
                "values": [i, i*2, i*3]
            }
        })
        client.publish(topic, payload)



    # Send the late sample (timestamp 3)
    payload = json.dumps({
        "descriptor": {
            "timestamp": LATENT_DATA_INDEX,
            "length": 10,
            "metadata_version": 1
        },
        "data": {
            "type": "double",
            "values": [3, 6, 9]
        }
    })
    client.publish(topic, payload)
    
    # To make sure we got the latent data sample in the FIFO
    while len(accelerometer_instance._fifo) < 10 :
       print ("FIFO size", len(accelerometer_instance._fifo))

    # Verify ordered results
    status, data = accelerometer_instance.read(10)
    assert status == 1
    assert np.allclose(data[:, 0], np.arange(10)), \
        f"Out of order. Received: {data[:, 0].tolist()}"