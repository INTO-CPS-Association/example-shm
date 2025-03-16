import numpy as np
from src.methods.sysID import sysid  

def test_sysid():
    # Define OMA parameters
    oma_params = {
        "Fs": 100,  # Sampling frequency in Hz
        "block_shift": 30,  # Block shift parameter
        "model_order": 20  # Model order
    }
    
    # Load test data
    data = np.loadtxt('tests/input_data/Acc_4DOF.txt').T

    # Perform system identification
    sysid_output = sysid(data, oma_params)
    
    # Extract results using dictionary keys
    frequencies = sysid_output['Fn_poles']
    cov_freq = sysid_output['Fn_poles_cov']
    damping_ratios = sysid_output['Xi_poles']
    cov_damping = sysid_output['Xi_poles_cov']
    mode_shapes = sysid_output['Phi_poles']
    poles_label = sysid_output['Lab']

    # Load stored reference results
    stored_data = np.load('tests/input_data/expected_sysid_output.npz')
    stored_frequencies = stored_data['frequencies']
    stored_cov_freq = stored_data['cov_freq']
    stored_damping_ratios = stored_data['damping_ratios']
    stored_cov_damping = stored_data['cov_damping']
    stored_mode_shapes = stored_data['mode_shapes']
    stored_poles_label = stored_data['poles_label']


    tolerance = 1e-6
    assert np.allclose(frequencies, stored_frequencies, atol=tolerance, equal_nan=True), "Frequencies do not match!"
    assert np.allclose(cov_freq, stored_cov_freq, atol=tolerance, equal_nan=True), "Covariance frequencies do not match!"
    assert np.allclose(damping_ratios, stored_damping_ratios, atol=tolerance, equal_nan=True), "Damping ratios do not match!"
    assert np.allclose(cov_damping, stored_cov_damping, atol=tolerance, equal_nan=True), "Covariance damping ratios do not match!"
    assert np.allclose(mode_shapes, stored_mode_shapes, atol=tolerance, equal_nan=True), "Mode shapes do not match!"
    assert np.array_equal(poles_label, stored_poles_label), "Pole labels do not match!"
