import numpy as np
# pylint: disable=C0103, C0301

# Parameters
PARAMS = {}

##################################
### Settings for signal filter ###
##################################

PARAMS['filter_type'] = None                             # 'lowpass', 'bandpass', 'highpass' or None for no filtering
PARAMS['expansion_modes'] = [1,2,3]                    # What modes to use for expansion
PARAMS['filter_order'] = 4                             # Order/strength of butterworth filter
PARAMS['filter_cut-off'] = np.array([0.5,90])          # Cut of frequency(ies) for the butterworth filter [lower/upper cut-off value] or [>lower cut-off value<,upper cut-off value]

###########################
### Settings for sysID ###
###########################

#Pre-clean coefficient of variance trhesholds
PARAMS['freq_coeff_variance_treshold'] = 0.5   #Should be 1 or less.
PARAMS['damp_coeff_variance_treshold'] = 0.5   #Should be 1 or less.

PARAMS['Fs'] = 256.0                            # Samplefrequency
PARAMS['model_order_min'] = 2                   # Set the min model order
PARAMS['model_order'] = 15                      # Set the max model order for analysis
PARAMS['block_shift'] = 30                      # Block size in Hankel matrix

###############################
### Settings for clustering ###
###############################

PARAMS['mstab'] = 6                             # minimum number of frequencies to be validate as cluster
PARAMS['tMAC'] = 0.95                           # MAC threshold to be included in cluster
PARAMS['bound_multiplier']  = 2                 # Standard deviation multiplier
PARAMS['allignment_factor'] = [0.05,0.01]       # Factors for allignment

#############################
### Settings for tracking ###
#############################

PARAMS['phi_cri'] = 0.8                   # MAC criteria [%]
PARAMS['freq_cri'] = 0.2                  # Frequency difference criteria [%]
PARAMS['obj_cri'] = 0.1                   # criteria for closely related clusters
# If more clusters match, and it is not clear what cluster is best,
# then check if the difference of the objective function values are less than the criteria.
# Then it is probably the one with higest MAC rather than frequency [difference]
PARAMS['alpha'] = 0.05                    # Significance level

###################################
### Settings for model updating ###
###################################

PARAMS['verbose_interval'] = 5                         # How often will model update information be printed.
PARAMS['tMAC_MU'] = 0.7                                # MAC Pairing threshold.
PARAMS['modes_search_paring'] = 6                      # How many mode of the model to search through when pairing is done. 
PARAMS['pars_to_update'] = ["k_rot","m"]               # Parameters to update.
PARAMS['MU_start_values'] = np.array([10, 0.015])      # Initial values for parameters.
PARAMS['MU_bounds'] = [(0.01, 1000), (0, 1000)]        # Lower and upper bounds of paramters [par1(Lower bound, upper bound), par2(Lower bound, upper bound)]

MODEL_DIR = "models/beam" #Path to model
MODEL_PARS_NAME = "beam_pars.jsonl" #File name for parameters
from models.beam import beam_yafem_model as model #Import model
MODEL_FUNC = model.eval_yafem_model #Function name of model
# Default model parameters to use
MODEL_PARAMETERS = {'modes': PARAMS['modes_search_paring'],     # How many mode of the model to search through when pairing is done.
            # 'dofs_sel': np.array([[7,1],[6,1],[5,1],[4,1]]),    # How input data maps to model DOFs
            'dofs_sel': np.array([[7,1],[4,1]]),    # How input data maps to model DOFs
            'k_rot': 1,         # Inital values to use, if no previous saved parameters is found
            'l4': 0.1289,       # Inital values to use, if no previous saved parameters is found
            'm': 0,             # Inital values to use, if no previous saved parameters is found
            }

####################################
### Settings for modal expansion ###
####################################

PARAMS['output_type'] = 2                                           # system output type: 0-displacement; 1-velocities, 2-acceleration
PARAMS['detrend_integration_order'] = 2                             # Order of detrend applied integrated signal, 0 = mean, 1 = linear, 2 = second order etc.
PARAMS['beam_elements'] = np.array([3,4,5,6,7,8,9])                 # Order of elements in myModel that is beams
PARAMS['sensor_loc'] = np.array([[7,1],[6,1],[5,1],[4,1]])          # sensor location

######################################
### Settings for stress estimation ###
######################################
# For estimating stress
PARAMS['element_type'] = np.array(["beam2d","beam2d","beam2d","beam2d","beam2d","beam2d","beam2d"])     #Element types
PARAMS['elements'] = np.array([3,4,5,6,7,8,9])          #Elements picked out
PARAMS['y'] = np.array([1e-3/2,1e-3/2,1e-3/2,1e-3/2,1e-3/2,1e-3/2,1e-3/2])      #Moment of inertia of each element
PARAMS["dofs_extract"] = np.array([[8,3],[8,2],[8,1],[7,3],[7,2],[7,1],[6,3],[6,2],[6,1],[5,3],[5,2],[5,1],[4,3],[4,2],[4,1],[3,3],[2,3],[1,3],[1,2],[1,1]]) # Degrees of freedom to extract
PARAMS['ElementsToPlot'] = [0, 1, 2, 3, 4, 5, 6]        #Elements to plot stress data from.
PARAMS['s'] = 1         #Stress to use, s = 3 in the case of a 2D beam: axial, curvature/bending at 1. node (bottom), curvature/bending at 2. node (top)

#####################################
### Settings for fatigue analysis ###
#####################################

from methods.fatigue_functions.IIW import iiw_sn #Import fatigue curve
t = 2
k_thick = 1         #(25/t)**(0.1) #Base material. k_thick = 1 for t under 25mm
R = -120/160        # sigma_min / sigma_max
k_rs = -0.4*R + 1.2         #Low residual stress
mean_stress = 25        #To be adjusted
R_m = 360       #MPa #Ultimate tensile strength Low value for s235
k_mean = 1      # 1 - mean_stress/R_m #Modified Goodman
SaftyFactor = 1 * 1/k_thick * 1/k_rs * 1/k_mean
SN_CURVE = iiw_sn(140,"sigma",SF=SaftyFactor,signal_type="VA") #Fatigue SN curve
FATIGUE_DOF = [3, 2] #  [node, s] = What node to look at, what stress element to use (Look at description for PARAMS['s']).
DAMAGE_SUM = 0.5        #Palmgreen-Miner damage limit
