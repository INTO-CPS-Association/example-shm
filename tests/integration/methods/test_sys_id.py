import pytest
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock

from methods import sysid



def test_sysid():
    # Define OMA parameters
    sysid_params = {
        "Fs": 100,  # Sampling frequency in Hz
        "block_shift": 30,  # Block shift parameter
        "model_order": 20,  # Model order
        "model_order_min": 1 # Lowest model order
    }
    
    # Load test data
    data = np.loadtxt('tests/integration/input_data/Acc_4DOF.txt').T

    # Perform system identification
    sysid_output = sysid.sysid(data, sysid_params)
    
    # Extract results using dictionary keys
    frequencies = sysid_output['Fn_poles']
    cov_freq = sysid_output['Fn_poles_cov']
    damping_ratios = sysid_output['Xi_poles']
    cov_damping = sysid_output['Xi_poles_cov']
    mode_shapes = sysid_output['Phi_poles']



    # Load stored reference results
    stored_data = np.load('tests/integration/input_data/expected_sysid_output.npz')
    stored_frequencies = stored_data['frequencies']
    stored_cov_freq = stored_data['cov_freq']
    stored_damping_ratios = stored_data['damping_ratios']
    stored_cov_damping = stored_data['cov_damping']
    stored_mode_shapes = stored_data['mode_shapes']
    

    tolerance = 0.4
    assert np.allclose(frequencies, stored_frequencies, atol=tolerance, equal_nan=True), "Frequencies do not match!"
    assert np.allclose(cov_freq, stored_cov_freq, atol=tolerance, equal_nan=True), "Covariance frequencies do not match!"
    assert np.allclose(damping_ratios, stored_damping_ratios, atol=tolerance, equal_nan=True), "Damping ratios do not match!"
    assert np.allclose(cov_damping, stored_cov_damping, atol=tolerance*2, equal_nan=True), "Covariance damping ratios do not match!"
    assert np.allclose(mode_shapes, stored_mode_shapes, atol=tolerance, equal_nan=True), "Mode shapes do not match!"

def test_oma_full_flow_success():
    """
    Simulates full OMA flow: aligned data → sysid → conversion to JSON-safe format.
    """
    # Simulate 600 samples, 3 channels (e.g., 1 min * 10 Hz)
    data = np.random.randn(3, 600)

    sysid_params = {
        "Fs": 100,
        "block_shift": 30,
        "model_order": 6,
        "model_order_min": 1
    }

    sysid_result = sysid.sysid(data, sysid_params)

    # Check output structure
    assert isinstance(sysid_result, dict)
    for key in ["Fn_poles", "Xi_poles", "Phi_poles"]:
        assert key in sysid_result
        assert isinstance(sysid_result[key], list) or isinstance(sysid_result[key], np.ndarray)

    # Convert to JSON-safe structure
    converted = sysid.convert_numpy_to_list(sysid_result)
    assert isinstance(converted, dict)
    assert isinstance(converted["Fn_poles"], list)


def test_get_oma_results_integration(mocker):
    from datetime import datetime
    import numpy as np
    from methods import sysid

    fs = 100  # sampling frequency
    mock_aligner = MagicMock()

    number_of_minutes = 0.1
    samples = int(fs * 60 * number_of_minutes)  # 600 samples
    mock_data = np.random.randn(samples, 3)
    mock_timestamp = datetime.now()

    mock_aligner.extract.return_value = (mock_data, mock_timestamp)

    sysid_output, timestamp = sysid.get_sysid_output(number_of_minutes, mock_aligner, fs)

    assert isinstance(sysid_output, dict)
    assert "Fn_poles" in sysid_output
    assert timestamp == mock_timestamp.isoformat()


def test_oma_raises_on_empty_data():
    """
    SSI should raise an error if data is empty (simulating a low-data scenario).
    """
    data = np.empty((0, 3))  # No samples

    sysid_params = {
        "Fs": 10.0,
        "block_shift": 5,
        "model_order": 6,
        "model_order_min": 1
    }

    with pytest.raises(Exception):
        sysid.sysid(data, sysid_params)
