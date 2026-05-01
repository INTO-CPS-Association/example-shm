import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from datetime import datetime
import json
from methods.sysid import (
    sysid,
    get_sysid_output,
    publish_sysid_output,
    setup_client,
)
from paho.mqtt.client import Client as MQTTClient


@pytest.fixture
def sample_data():
    return np.random.randn(600, 3)


@pytest.fixture
def sysid_params():
    return {
        "Fs": 100.0,
        "block_shift": 5,
        "model_order": 6,
        "model_order_min": 1
    }


def test_sysid_returns_expected_keys(sample_data, sysid_params):
    result = sysid(sample_data, sysid_params)
    assert isinstance(result, dict)
    expected_keys = {'Fn_poles', 'Fn_poles_cov', 'Xi_poles', 'Xi_poles_cov', 'Phi_poles'}
    assert expected_keys.issubset(result.keys())


def test_sysid_transposes_data_if_needed(sysid_params):
    data = np.random.randn(3, 600)  # More columns than rows
    result = sysid(data, sysid_params)
    assert isinstance(result, dict)
    assert "Fn_poles" in result

def test_get_oma_results_success(mocker):
    fs = 100
    samples_needed = 600
    mock_data = np.random.randn(samples_needed, 3)
    mock_aligner = MagicMock()
    mock_aligner.extract.return_value = (mock_data, datetime.now())

    result, ts = get_sysid_output(600, mock_aligner, fs)

    assert result is not None
    assert "Fn_poles" in result

def test_get_oma_results_no_data(mocker):
    fs = 100
    mock_aligner = MagicMock()
    mock_aligner.extract.return_value = (np.empty((0, 3)), datetime.now())

    result, ts = get_sysid_output(6000, mock_aligner, fs)

    assert result is None
    assert ts is None


def test_get_oma_results_not_enough_samples(mocker):
    fs = 100
    mock_aligner = MagicMock()
    data = np.random.randn(100, 3)
    mock_aligner.extract.return_value = (data, datetime.now())

    result, ts = get_sysid_output(1000, mock_aligner, fs)  # ask for too many samples

    assert result is None
    assert ts is None


def test_get_oma_results_sysid_failure(mocker):
    fs = 100
    mock_aligner = MagicMock()
    mock_aligner.extract.return_value = (np.random.randn(600, 3), datetime.now())

    mocker.patch("methods.sysid.sysid", side_effect=Exception("fail"))

    result, ts = get_sysid_output(1, mock_aligner, fs)

    assert result is None
    assert ts is None


def test_publish_oma_results_retries_and_publishes_once(mocker):
    fs = 100
    dummy_result = {
        'Fn_poles': np.array([[3.2, 3.3], [3.4, 3.5]]),
        'Fn_poles_cov': np.array([[0.1, 0.1], [0.1, 0.1]]),
        'Xi_poles': np.array([[0.02, 0.03], [0.04, 0.05]]),
        'Xi_poles_cov': np.array([[0.001, 0.001], [0.001, 0.001]]),
        'Phi_poles': np.array([[1.0, 0.0], [0.0, 1.0]]),
    }

    mocker.patch("methods.sysid.time.sleep", return_value=None)

    mocker.patch(
        "methods.sysid.get_sysid_output",
        side_effect=[
            (None, None),
            (dummy_result, datetime(2024, 1, 1))
        ]
    )

    mocker.patch(
        "methods.sysid.convert_numpy_to_list",
        return_value={k: v.tolist() if hasattr(v, "tolist") else v for k, v in dummy_result.items()}
    )

    mock_client = MagicMock(spec=MQTTClient)
    mock_client.is_connected.return_value = True
    aligner = MagicMock()
    aligner.client = MagicMock()
    aligner_time = datetime.fromisoformat("2025-01-01 01:01:00.00000").isoformat()

    publish_sysid_output(mock_client, ["test/topic"], dummy_result, aligner_time)

    assert mock_client.publish.called
    assert mock_client.publish.call_count == 1
    assert mock_client.publish.call_args[0][0] == "test/topic"


def test_setup_client_with_multiple_topics(mocker):
    mqtt_config = {
        "host": "localhost",
        "port": 1883,
        "TopicsToSubscribe": ["topic1", "topic2"]
    }

    extract_mock = mocker.patch("methods.sysid.extract_fs_from_metadata", return_value=123.0)

    mock_mqtt_client = MagicMock()
    mocker.patch("methods.sysid.setup_mqtt_client", return_value=(mock_mqtt_client))

    client, fs = setup_client(mqtt_config)
    client.loop_stop()

    extract_mock.assert_called_once_with(mqtt_config)
    client.connect.assert_called_once_with("localhost", 1883, 60)
    client.loop_start.assert_called_once()
    assert client == mock_mqtt_client
    assert fs == 123.0
