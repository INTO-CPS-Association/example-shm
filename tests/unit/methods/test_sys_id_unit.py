import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from datetime import datetime
import json
from methods.sys_id import (
    sysid,
    convert_numpy_to_list,
    get_oma_results,
    publish_oma_results,
    extract_fs_from_metadata,
    _on_metadata,
    setup_client,
)
from paho.mqtt.client import Client as MQTTClient


@pytest.fixture
def sample_data():
    return np.random.randn(600, 3)


@pytest.fixture
def oma_params():
    return {
        "Fs": 100.0,
        "block_shift": 5,
        "model_order": 6
    }


def test_sysid_returns_expected_keys(sample_data, oma_params):
    result = sysid(sample_data, oma_params)
    assert isinstance(result, dict)
    expected_keys = {'Fn_poles', 'Fn_poles_cov', 'Xi_poles', 'Xi_poles_cov', 'Phi_poles', 'Lab'}
    assert expected_keys.issubset(result.keys())


def test_sysid_transposes_data_if_needed(oma_params):
    data = np.random.randn(3, 600)  # More columns than rows
    result = sysid(data, oma_params)
    assert isinstance(result, dict)
    assert "Fn_poles" in result


def test_convert_numpy_to_list_handles_various_types():
    input_data = {
        "array": np.array([1, 2, 3]),
        "complex": 1 + 2j,
        "nested": [np.float64(1.5), {"x": np.array([[1, 2]])}],
        "int": np.int64(42),
        "float": np.float32(3.14)
    }
    output = convert_numpy_to_list(input_data)
    assert output["array"] == [1, 2, 3]
    assert "real" in output["complex"]
    assert isinstance(output["nested"][0], float)
    assert isinstance(output["int"], int)
    assert isinstance(output["float"], float)


def test_get_oma_results_success(mocker):
    mocker.patch("methods.sys_id.FS", 100)
    samples_needed = 100 * 60 * 0.1  # 600
    mock_data = np.random.randn(int(samples_needed), 3)
    mock_aligner = MagicMock()
    mock_aligner.extract.return_value = (mock_data, datetime.now())

    result, ts = get_oma_results(0.1, mock_aligner)
    assert result is not None
    assert "Fn_poles" in result


def test_get_oma_results_no_data(mocker):
    mock_aligner = MagicMock()
    mock_aligner.extract.return_value = (np.empty((0, 3)), datetime.now())
    result, ts = get_oma_results(1, mock_aligner)
    assert result is None
    assert ts is None


def test_get_oma_results_not_enough_samples(mocker):
    mock_aligner = MagicMock()
    data = np.random.randn(100, 3)
    mock_aligner.extract.return_value = (data, datetime.now())
    result, ts = get_oma_results(10, mock_aligner)  # ask for too many samples
    assert result is None
    assert ts is None


def test_get_oma_results_sysid_failure(mocker):
    mock_aligner = MagicMock()
    mock_aligner.extract.return_value = (np.random.randn(600, 3), datetime.now())
    mocker.patch("methods.sys_id.sysid", side_effect=Exception("fail"))
    result, ts = get_oma_results(1, mock_aligner)
    assert result is None
    assert ts is None


def test_publish_oma_results_handles_publish_and_reconnect(mocker):
    mocker.patch("methods.sys_id.get_oma_results", return_value=(
        {"Fn_poles": [1, 2], "Fn_poles_cov": [], "Xi_poles": [],
         "Xi_poles_cov": [], "Phi_poles": [], "Lab": []},
        datetime(2025, 1, 1, 12, 0)
    ))

    mock_client = MagicMock()
    mock_client.is_connected.return_value = False
    mock_client.reconnect.return_value = None
    mock_client.publish.return_value = None

    mock_aligner = MagicMock()

    mocker.patch("time.sleep", side_effect=[None, KeyboardInterrupt])

    publish_oma_results(0.1, mock_aligner, mock_client, "test/topic")

    mock_client.reconnect.assert_called_once()
    mock_client.publish.assert_called_once()


def test_extract_fs_from_metadata_reads_fs(mocker):
    mock_mqtt = MagicMock(spec=MQTTClient)
    mock_mqtt.loop_start.return_value = None
    mock_mqtt.loop_stop.return_value = None
    mock_mqtt.connect.return_value = None
    mock_mqtt.subscribe.return_value = None

    mocker.patch("methods.sys_id.setup_mqtt_client", return_value=(mock_mqtt, None))

    # Simulate metadata message
    payload = json.dumps({"Analysis chain": [{"Sampling": 200}]}).encode("utf-8")
    message = MagicMock()
    message.payload = payload

    _on_metadata(mock_mqtt, {"metadata_topic": "meta"}, message)
    assert isinstance(_on_metadata, object)  

    config = {
        "TopicsToSubscribe": ["sensor/topic", "meta"],
        "host": "localhost",
        "port": 1883
    }
    fs = extract_fs_from_metadata(config)
    assert isinstance(fs, (int, float))


def test_setup_client_invokes_metadata_logic(mocker):
    mock_client = MagicMock()
    mocker.patch("methods.sys_id.setup_mqtt_client", return_value=(mock_client, None))
    mocker.patch("methods.sys_id.extract_fs_from_metadata", return_value=100)

    config = {
        "topics": ["data/topic", "meta/topic"],
        "TopicsToSubscribe": ["data/topic", "meta/topic"],
        "host": "localhost",
        "port": 1883
    }

    client = setup_client(config)
    assert isinstance(client, MagicMock)
    client.connect.assert_called_once()
    client.loop_start.assert_called_once()
