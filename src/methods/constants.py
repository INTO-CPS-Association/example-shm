import numpy as np
# Constants for sysID
WAIT_METADATA = 11 # Wait max 11 seconds for getting metadata message

DEFAULT_FS = 250 # In case the Fs from metadata doesn't arrive

MIN_SAMPLES_NEEDED = 540  # Minimum samples for running sysid

BLOCK_SHIFT = 30

MODEL_ORDER = 20

# Constants for Model track
MSTAB_FACTOR = 0.4 # This is goning to be multiplied by the MODEL_ORDER to get the mstab
TMAC = 0.9

# Constants for Model Update
# 1st parameter is spring stiffness and 2nd is unbounded length 
X0 = np.array([1e1, 10e-3]) 

# Create bounds using element-wise i.e. different parameters have different bounds
BOUNDS = [(1e-2 * X0[0], 1e2 * X0[0]), (1e-2 * X0[1], 1e2 * X0[1])] 
