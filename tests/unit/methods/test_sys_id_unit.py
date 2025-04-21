import pytest
import numpy as np
from unittest.mock import MagicMock
from datetime import datetime
import json

from methods.sys_id import (
    sysid,
    convert_numpy_to_list,
    get_oma_results,
    publish_oma_results,
)


@pytest.fixture
def sample_data():
    data = np.random.randn(3, 600)  # 500 time steps, 3 sensors
    return data


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


def test_convert_numpy_to_list_handles_nested_structures():
    input_data = {
        "array": np.array([1, 2, 3]),
        "complex": 1 + 2j,
        "nested": [np.float64(1.5), {"x": np.array([[1, 2]])}]
    }
    output = convert_numpy_to_list(input_data)
    assert isinstance(output["array"], list)
    assert "real" in output["complex"]
    assert isinstance(output["nested"][0], float)


def test_get_oma_results_success(mocker, sample_data, oma_params):
    mock_aligner = MagicMock()
    timestamp = datetime.now()
    mock_aligner.extract.return_value = (sample_data, timestamp)

    result, ts = get_oma_results(mock_aligner, oma_params)
    assert result is not None
    assert ts == timestamp
    assert "Fn_poles" in result


def test_get_oma_results_insufficient_data(mocker, oma_params):
    mock_aligner = MagicMock()
    mock_aligner.extract.return_value = (np.empty((0, 3)), datetime.now())

    result, ts = get_oma_results(mock_aligner, oma_params)
    assert result is None
    assert ts is None


def test_publish_oma_results_handles_publish_failure(mocker, sample_data, oma_params):
    mock_aligner = MagicMock()
    timestamp = datetime(2024, 1, 1, 12, 0, 0)
    mock_aligner.extract.return_value = (sample_data, timestamp)

    mock_client = MagicMock()
    mock_client.is_connected.return_value = True
    mock_client.publish.side_effect = Exception("Simulated failure")

    mocker.patch("time.sleep", side_effect=KeyboardInterrupt)

    publish_oma_results(mock_aligner, oma_params, mock_client, "test/topic")
