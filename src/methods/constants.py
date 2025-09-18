import numpy as np
# Constants for sysID
WAIT_METADATA = 11 # Wait max 11 seconds for getting metadata message

DEFAULT_FS = 800 #256 # In case the Fs from metadata doesn't arrive

MIN_SAMPLES_NEEDED = 800*2#256*2  # Minimum samples for running sysid

PARAMS = {}
PARAMS['Fs'] = 256                              # Sample frequency
PARAMS['model_order_min'] = 2                   # Set the min model order
PARAMS['model_order'] = 15                      # Set the max model order for analysis
PARAMS['block_shift'] = 30                      # Block size in Hankel matrix
PARAMS['sensor_order'] = np.array([0, 2, 1, 3]) # sensor location in data

# Params for clustering:
PARAMS['mstab'] = 6                             # minimum number of frequencies to be validate as cluster
PARAMS['tMAC'] = 0.95                           # MAC threshold to be included in cluster
PARAMS['bound_multiplier']  = 2                 # Standard deviation multiplier
PARAMS['allignment_factor'] = [0.05,0.01]       # Factors for allignment

# Params for model updating
PARAMS['tMAC_MU'] = 0.7

PARAMS['pars_to_update_initial'] = ["k_rot","l4"]
PARAMS['MU_initial_start_values'] = np.array([10, 0.170])
PARAMS['MU_initial_bounds'] = [(0.01, 1000), (0.071, 0.296)]
PARAMS['MU_initial_modes'] = [1,2,3]

PARAMS['pars_to_update'] = ["k_rot","m"]
PARAMS['MU_start_values'] = np.array([10, 0.015])
PARAMS['MU_bounds'] = [(0.01, 1000), (0, 1000)]
PARAMS['MU_modes'] = [1,2,3]

# Params for mode tracking
PARAMS['phi_cri'] = 0.8 #0.98                   # MAC criteria [%]
PARAMS['freq_cri'] = 0.2 #0.2                   # Frequency difference criteria [%]
PARAMS['obj_cri'] = 0.1                         # If more clusters match, an it is not clear what cluster is best,
                                                # then check if the difference of the objective function values are less than the criteria.
                                                # Then it is probably the one with higest MAC rather than frequency [difference]

# Params for modal expansion:
PARAMS['sensor_loc'] = np.array([[7,1],[6,1],[5,1],[4,1]])          # sensor location
PARAMS['validation_sensor_loc'] = np.array([[4,1]])                 # Validation sensor
PARAMS['output_type'] = 2                                           # system output type: 0-displacement; 1-velocities, 2-acceleration
PARAMS['model_sel_DOF'] = "all" # np.array([[8,1],[1,1],[3,1],[2,1],[4,1],[7,1],[6,1],[5,1]])
