import numpy as np
import pytest
#from pyoma2.setup.single import SingleSetup
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
pyoma_dir = os.path.abspath(os.path.join(current_dir, "../../../src/cp-sens/methods"))
if pyoma_dir not in sys.path:
    sys.path.insert(0, pyoma_dir)
from pyoma.ssiM import SSIcov
from  sysID import sysid 


np.random.seed(42)  # For reproducibility
  
test_data = np.random.randn(3, 1000)  # Simulated random data



def test_sysid():
    # Define OMA parameters
    oma_params = {
        "Fs": 100.0,  # Sampling frequency in Hz
        "block_shift": 15,  # Block shift parameter
        "model_order": 10  # Model order
    }
    
    # Perform system identification
    results = sysid(test_data, oma_params)
    
    # Assertions to verify output
    assert isinstance(results, dict), "Output should be a dictionary"
    assert "frequencies" in results, "Result should contain 'frequencies' key"
    assert "damping_ratios" in results, "Result should contain 'damping_ratios' key"
    assert len(results["frequencies"]) > 0, "Frequencies should not be empty"
    assert len(results["damping_ratios"]) > 0, "Damping ratios should not be empty"
