import io
import os
import pytest
from unittest.mock import MagicMock

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/cp-sens")))

from data.accel.hbk.accelerometer import (
    create_on_connect_callback,
    create_on_subscribe_callback,
    create_on_message_callback,
    create_on_publish_callback,
    setup_mqtt_client
)

def test_on_connect_callback_success():
    topics = ["test/topic1", "test/topic2"]
    qos = 1
    on_connect = create_on_connect_callback(topics, qos)
    client = MagicMock()
    # Simulate a successful connection (rc == 0)
    on_connect(client, None, None, 0)
    # Verify that subscribe was called for each topic with the expected QoS.
    assert client.subscribe.call_count == len(topics)
    for topic in topics:
        client.subscribe.assert_any_call(topic, qos=qos)

def test_on_connect_callback_failure():
    topics = ["test/topic1", "test/topic2"]
    qos = 1
    on_connect = create_on_connect_callback(topics, qos)
    client = MagicMock()
    # Simulate a failed connection (rc != 0)
    on_connect(client, None, None, 1)
    # Verify that subscribe is not called when connection fails.
    client.subscribe.assert_not_called()

def test_on_subscribe_callback(capsys):
    on_subscribe = create_on_subscribe_callback()
    client = MagicMock()
    # Call on_subscribe with a sample message id and granted QoS list.
    on_subscribe(client, None, 42, [1, 1])
    captured = capsys.readouterr().out
    assert "Subscription ID 42" in captured
    assert "QoS levels [1, 1]" in captured

def test_on_message_callback(capsys):
    on_message = create_on_message_callback()
    client = MagicMock()

    # Create a fake message object.
    class FakeMsg:
        topic = "test/topic"
        payload = b"test payload"

    fake_msg = FakeMsg()
    on_message(client, None, fake_msg)
    captured = capsys.readouterr().out
    assert "Received message on test/topic" in captured
    assert "Message payload: test payload" in captured

def test_on_publish_callback(capsys):
    on_publish = create_on_publish_callback()
    client = MagicMock()
    on_publish(client, None, 99)
    captured = capsys.readouterr().out
    assert "Message 99 published" in captured

def test_setup_mqtt_client():
    dummy_config = {
        "MQTT": {
            "ClientID": "test_client",
            "userId": "test_user",
            "password": "test_pass",
            "TopicsToSubscribe": ["test/topic1", "test/topic2"],
            "QoS": 1,
            "host": "localhost",
            "port": 1883
        }
    }
    client = setup_mqtt_client(dummy_config)
    # Check that the client has the correct client_id.
    client_id = client._client_id.decode() if isinstance(client._client_id, bytes) else client._client_id
    assert client_id == "test_client"
    
    # Verify that all callback functions has been assigned.
    assert client.on_connect is not None
    assert client.on_subscribe is not None
    assert client.on_message is not None
    assert client.on_publish is not None