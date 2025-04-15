import io
import os
import json
import pytest
from unittest.mock import MagicMock


from data.sources import mqtt
from data.sources.mqtt import (
    create_on_connect_callback,
    create_on_subscribe_callback,
    create_on_message_callback,
    create_on_publish_callback,
    setup_mqtt_client,
    load_config
)
def test_load_config_success(tmp_path):
    config_data = {"key": "value"}
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    loaded = load_config(str(config_file))
    assert loaded == config_data


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("non_existing_config.json")


def test_load_config_invalid_json(tmp_path):
    invalid_file = tmp_path / "bad_config.json"
    invalid_file.write_text("{invalid_json: True", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(str(invalid_file))


def test_load_config_unexpected_exception(monkeypatch):

    def bad_open(*args, **kwargs):
        raise OSError("Unexpected OS error")

    monkeypatch.setattr("builtins.open", bad_open)

    with pytest.raises(RuntimeError):
        mqtt.load_config("config.json")


def test_setup_mqtt_client_invalid_index():
    dummy_config = {
        "ClientID": "test_client",
        "userId": "test_user",
        "password": "test_pass",
        "TopicsToSubscribe": ["topic1"],
        "QoS": 1,
        "host": "localhost",
        "port": 1883
    }

    with pytest.raises(ValueError):
        setup_mqtt_client(dummy_config, topic_index=5)


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
    on_subscribe(client, None, 42, [1, 1], properties=None)
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
    #assert "Message payload: test payload" in captured


def test_on_publish_callback(capsys):
    on_publish = create_on_publish_callback()
    client = MagicMock()
    on_publish(client, None, 99)
    captured = capsys.readouterr().out
    assert "Message 99 published" in captured


def test_setup_mqtt_client():
    dummy_config = {
        "ClientID": "test_client",  # Ensure ClientID is at the correct level
        "userId": "test_user",
        "password": "test_pass",
        "TopicsToSubscribe": ["test/topic1", "test/topic2"],
        "QoS": 1,
        "host": "localhost",
        "port": 1883
    }
    # Unpack the returned tuple
    client, selected_topic = setup_mqtt_client(dummy_config)

    # Check that the client has the correct client_id.
    client_id = client._client_id.decode() if isinstance(client._client_id, bytes) else client._client_id
    assert client_id == "test_client"

    # Verify that all callback functions have been assigned.
    assert client.on_connect is not None
    assert client.on_subscribe is not None
    assert client.on_message is not None
    assert client.on_publish is not None

