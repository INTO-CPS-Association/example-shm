import numpy as np
# Constants for sysID
WAIT_METADATA = 11 # Wait max 11 seconds for getting metadata message

DEFAULT_FS = 250 # In case the Fs from metadata doesn't arrive

MIN_SAMPLES_NEEDED = 540  # Minimum samples for running sysid

# Constants for Model Update
# 1st parameter is spring stiffness and 2nd is unbounded length
X0 = np.array([1e1, 10e-3])

# Create bounds using element-wise i.e. different parameters have different bounds
BOUNDS = [(1e-2 * X0[0], 1e2 * X0[0]), (1e-2 * X0[1], 1e2 * X0[1])]




# Parameters
PARAMS = {}

#Pre-clean
PARAMS['freq_variance_treshold'] = 0.1
PARAMS['damp_variance_treshold'] = 10**6

PARAMS['Fs'] = 256                             # Sample frequency
PARAMS['model_order_min'] = 2                   # Set the min model order
PARAMS['model_order'] = 15                      # Set the max model order for analysis
PARAMS['block_shift'] = 30                      # Block size in Hankel matrix
PARAMS['sensor_order'] = np.array([0, 2, 1, 3]) # sensor location in data

# Params for clustering:
PARAMS['mstab'] = 6               # minimum number of frequencies to be validate as cluster
PARAMS['tMAC'] = 0.95                           # MAC threshold to be included in cluster
PARAMS['bound_multiplier']  = 2                 # Standard deviation multiplier
PARAMS['allignment_factor'] = [0.05,0.01]       # Factors for allignment

# Params for mode tracking
PARAMS['phi_cri'] = 0.8 #0.98                   # MAC criteria [%]
PARAMS['freq_cri'] = 0.2 #0.2                   # Frequency difference criteria [%]
PARAMS['obj_cri'] = 0.1
# If more clusters match, an it is not clear what cluster is best,
# then check if the difference of the objective function values are less than the criteria.
# Then it is probably the one with higest MAC rather than frequency [difference]
