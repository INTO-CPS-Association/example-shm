import numpy as np
from methods.sysID import sysid  


def test_sysid():
    # Define OMA parameters
    oma_params = {
        "Fs": 100.0,  # Sampling frequency in Hz
        "block_shift": 15,  # Block shift parameter
        "model_order": 10  # Model order
    }
    
    data = np.loadtxt('Acc_4DOF.txt')
    data = data.T
    # Perform system identification
    results = sysid(data, oma_params)
    
    # Assertions to verify output
    assert isinstance(results, dict), "Output should be a dictionary"
    assert "Fn" in results, "Result should contain 'Fn' key"
    assert "Phi" in results, "Result should contain 'Phi' key"
    assert "Obs" in results, "Result should contain 'Obs' key"
