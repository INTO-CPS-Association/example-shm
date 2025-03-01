import numpy as np
import sysID  


def test_sysid():
    # Define OMA parameters
    oma_params = {
        "Fs": 100.0,  # Sampling frequency in Hz
        "block_shift": 15,  # Block shift parameter
        "model_order": 10  # Model order
    }
    
    np.random.seed(42)   
    test_data = np.random.randn(1000, 3) 
    # Perform system identification
    results = sysID.sysid(test_data, oma_params)
    
    # Assertions to verify output
    assert isinstance(results, dict), "Output should be a dictionary"
    assert "Fn" in results, "Result should contain 'Fn' key"
    assert "Phi" in results, "Result should contain 'Phi' key"
    assert "Obs" in results, "Result should contain 'Obs' key"
