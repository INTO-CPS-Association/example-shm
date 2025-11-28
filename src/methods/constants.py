import numpy as np
import sys
from pathlib import Path
sys.path.append(Path.cwd().__str__())
from models.beam import beam_yafem_model as model

# Constants for sysID
WAIT_METADATA = 11 # Wait max 11 seconds for getting metadata message

DEFAULT_FS = 250 # In case the Fs from metadata doesn't arrive

MIN_SAMPLES_NEEDED = 540  # Minimum samples for running sysid

# Parameters
PARAMS = {}

#Pre-clean
PARAMS['freq_variance_treshold'] = 0.1
PARAMS['damp_variance_treshold'] = 10**6

PARAMS['Fs'] = 256                             # Sample frequency
PARAMS['model_order_min'] = 2                   # Set the min model order
PARAMS['model_order'] = 15                      # Set the max model order for analysis
PARAMS['block_shift'] = 30                      # Block size in Hankel matrix

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

# Params for model updating
PARAMS['tMAC_MU'] = 0.7

PARAMS['modes_search_paring'] = 6
PARAMS['pars_to_update'] = ["k_rot","m"]
PARAMS['MU_start_values'] = np.array([10, 0.015])
PARAMS['MU_bounds'] = [(0.01, 1000), (0, 1000)]
PARAMS['MU_modes'] = [1,2,3]

MODEL_DIR = "models/beam"
MODEL_PARS_NAME = "beam_pars.jsonl"
MODEL_FUNC = model.eval_yafem_model
MODEL_PARAMETERS = {'modes': PARAMS['modes_search_paring'],
            'dofs_sel': np.array([[7,1],[6,1],[5,1],[4,1]]),
            'k_rot': None, 
            'l4': 0.1289,
            'm': None,
            }
