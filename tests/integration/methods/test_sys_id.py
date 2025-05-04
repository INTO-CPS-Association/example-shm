import pytest
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock

from methods import sys_id

def test_sysid():
    # Define OMA parameters
    oma_params = {
        "Fs": 100,  # Sampling frequency in Hz
        "block_shift": 30,  # Block shift parameter
        "model_order": 20  # Model order
    }
    
    # Load test data
    data = np.loadtxt('tests/integration/input_data/Acc_4DOF.txt').T

    # Perform system identification
    sysid_output = sys_id.sysid(data, oma_params)
    
    # Extract results using dictionary keys
    frequencies = sysid_output['Fn_poles']
    cov_freq = sysid_output['Fn_poles_cov']
    damping_ratios = sysid_output['Xi_poles']
    cov_damping = sysid_output['Xi_poles_cov']
    mode_shapes = sysid_output['Phi_poles']
    poles_label = sysid_output['Lab']

    # Load stored reference results
    stored_data = np.load('tests/integration/input_data/expected_sysid_output.npz')
    stored_frequencies = stored_data['frequencies']
    stored_cov_freq = stored_data['cov_freq']
    stored_damping_ratios = stored_data['damping_ratios']
    stored_cov_damping = stored_data['cov_damping']
    stored_mode_shapes = stored_data['mode_shapes']
    stored_poles_label = stored_data['poles_label']


    tolerance = 0.4
    assert np.allclose(frequencies, stored_frequencies, atol=tolerance, equal_nan=True), "Frequencies do not match!"
    assert np.allclose(cov_freq, stored_cov_freq, atol=tolerance, equal_nan=True), "Covariance frequencies do not match!"
    assert np.allclose(damping_ratios, stored_damping_ratios, atol=tolerance, equal_nan=True), "Damping ratios do not match!"
    assert np.allclose(cov_damping, stored_cov_damping, atol=tolerance, equal_nan=True), "Covariance damping ratios do not match!"
    assert np.allclose(mode_shapes, stored_mode_shapes, atol=tolerance, equal_nan=True), "Mode shapes do not match!"
    assert np.array_equal(poles_label, stored_poles_label), "Pole labels do not match!"


def test_sysid_full_flow_success():
    """
    Simulates full OMA flow: aligned data → sysid → conversion to JSON-safe format.
    """
    # Simulate 600 samples, 3 channels (e.g., 1 min * 10 Hz)
    data = np.random.randn(3, 600)

    oma_params = {
        "Fs": 100,
        "block_shift": 30,
        "model_order": 20
    }

    oma_result = sys_id.sysid(data, oma_params)

    # Check output structure
    assert isinstance(oma_result, dict)
    for key in ["Fn_poles", "Xi_poles", "Phi_poles"]:
        assert key in oma_result
        assert isinstance(oma_result[key], list) or isinstance(oma_result[key], np.ndarray)

    # Convert to JSON-safe structure
    converted = sys_id.convert_numpy_to_list(oma_result)
    assert isinstance(converted, dict)
    assert isinstance(converted["Fn_poles"], list)


def test_get_oma_results_integration(mocker):
    from datetime import datetime
    import numpy as np
    from methods import sys_id

    fs = 100  # sampling frequency
    mock_aligner = MagicMock()

    number_of_minutes = 0.1
    samples = int(fs * 60 * number_of_minutes)  # 600 samples
    mock_data = np.random.randn(samples, 3)
    mock_timestamp = datetime.now()

    mock_aligner.extract.return_value = (mock_data, mock_timestamp)

    oma_output, timestamp = sys_id.get_oma_results(number_of_minutes, mock_aligner, fs)

    assert isinstance(oma_output, dict)
    assert "Fn_poles" in oma_output
    assert timestamp == mock_timestamp


def test_sysid_raises_on_empty_data():
    """
    SSI should raise an error if data is empty (simulating a low-data scenario).
    """
    data = np.empty((0, 3))  # No samples

    oma_params = {
        "Fs": 10.0,
        "block_shift": 5,
        "model_order": 6
    }

    with pytest.raises(Exception):
        sys_id.sysid(data, oma_params)
