import numpy as np
from beam import beam_yafem_model as model
from methods.fatigue_functions.IIW import iiw_sn
# pylint: disable=C0103, C0301

# Constants for sysID
WAIT_METADATA = 11 # Wait max 11 seconds for getting metadata message

DEFAULT_FS = 256 # In case the Fs from metadata doesn't arrive

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
PARAMS['phi_cri'] = 0.8                 # MAC criteria [%]
PARAMS['freq_cri'] = 0.2                  # Frequency difference criteria [%]
PARAMS['obj_cri'] = 0.1                   # criteria for closely related clusters
# If more clusters match, an it is not clear what cluster is best,
# then check if the difference of the objective function values are less than the criteria.
# Then it is probably the one with higest MAC rather than frequency [difference]
PARAMS['l_lastest_clusters'] = 5                # l number of clusters to compare with

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
            'k_rot': 1, 
            'l4': 0.1289,
            'm': 0,
            }


# Params for modal expansion:
PARAMS['expansion_modes'] = PARAMS['MU_modes']
PARAMS['filter_order'] = 4                                          # Order/strength of butterworth filter
PARAMS['filter_type'] = 'bandpass'                                   # 'lowpass', 'bandpass', 'highpass' or None
PARAMS['filter_cut-off'] = np.array([0.5,90])                           # Cut of frequency(ies) for the butterworth filter [lower/upper cut-off value] or [>lower cut-off value<,upper cut-off value]
PARAMS['output_type'] = 2                                           # system output type: 0-displacement; 1-velocities, 2-acceleration
PARAMS['detrend_integration_order'] = 2                             # Order of detrend applied integrated signal, 0 = mean, 1 = linear, 2 = second order etc.
PARAMS['beam_elements'] = np.array([3,4,5,6,7,8,9])                 # Order of elements in myModel that is beams
PARAMS['sensor_loc'] = np.array([[7,1],[6,1],[5,1],[4,1]])          # sensor location

# For estimating stress
PARAMS['element_type'] = np.array(["beam2d","beam2d","beam2d","beam2d","beam2d","beam2d","beam2d"])
PARAMS['elements'] = np.array([3,4,5,6,7,8,9])
PARAMS['y'] = np.array([1e-3/2,1e-3/2,1e-3/2,1e-3/2,1e-3/2,1e-3/2,1e-3/2])
PARAMS["dofs_extract"] = np.array([[8,3],[8,2],[8,1],[7,3],[7,2],[7,1],[6,3],[6,2],[6,1],[5,3],[5,2],[5,1],[4,3],[4,2],[4,1],[3,3],[2,3],[1,3],[1,2],[1,1]])

t = 2
k_thick = 1 #(25/t)**(0.1) #Base material. k_thick = 1 for t under 25mm
R = -120/160 # sigma_min / sigma_max
k_rs = -0.4*R + 1.2 #Low residual stress
mean_stress = 25 #To be adjusted
R_m = 360 #MPa #Ultimate tensile strength Low value for s235
k_mean = 1# 1 - mean_stress/R_m #Modified Goodman
SaftyFactor = 1 * 1/k_thick * 1/k_rs * 1/k_mean
SN_CURVE = iiw_sn(140,"sigma",SF=SaftyFactor,signal_type="VA")
FATIGUE_DOF = [3, 2]
DAMAGE_SUM = 0.5
