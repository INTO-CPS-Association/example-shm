import numpy as np
import pickle as pk
import os
import matplotlib.pyplot as plt
from functions.cantileverbeam_initial_update import initial_run
from functions.inital_model_error import calculate_inital_model_error
from functions.cantileverbeam_update import model_updating_run
from functions.modal_expansion import (modal_expansion_run,modal_expansion_validation)
from functions.stress_estimation import estimate_stress
from functions.results_plot import cantilever_beam_plots
from functions.fatigue_results import fatigue_plots
from functions.mode_tracking import track_for_plotting

# cantilever_beam_plots(path="C:/example-shm/record/scripts_paper_results/data")
# fatigue_plots()
# quit()
dirname = os.path.dirname(__file__)

# PARAMS: this should go to config_sysid.json file
Params = {}

Params['path'] = dirname

Params['Fs'] = 256                              # Sample frequency
Params['model_order_min'] = 2                   # Set the min model order
Params['model_order'] = 15                      # Set the max model order for analysis
Params['block_shift'] = 30                      # Block size in Hankel matrix
Params['sensor_order'] = np.array([0, 2, 1, 3]) # sensor location in data
Params['sensor_loc'] = np.array([[7,1],[6,1],[5,1],[4,1]])          # sensor location

#Params for pre-clean:*
Params['freq_variance_treshold'] = 0.1
Params['damp_variance_treshold'] = 10**6

# Params for clustering:
Params['mstab'] = 6                             # minimum number of frequencies to be validate as cluster
Params['tMAC'] = 0.95                           # MAC threshold to be included in cluster
Params['bound_multiplier']  = 2                 # Standard deviation multiplier
Params['allignment_factor'] = [0.05,0.01]       # Factors for allignment

# Params for model updating
Params['tMAC_MU'] = 0.7

Params['pars_to_update_initial'] = ["k_rot","l4"]
Params['MU_initial_start_values'] = np.array([10, 0.170])
Params['MU_initial_bounds'] = [(0.01, 1000), (0.071, 0.296)]
Params['MU_initial_modes'] = [1,2,3]
Params['modes_search_paring'] = 6

Params['pars_to_update'] = ["k_rot","m"]
Params['MU_start_values'] = np.array([10, 0.015])
Params['MU_bounds'] = [(0.01, 1000), (0, 1000)]
Params['MU_modes'] = [1,2,3]

Params['updated_values'] = Params['MU_start_values'].copy()            #Updated values of k_rot and m, which allows for modal expansion even when modelupdating failed.

# Params for mode tracking
Params['phi_cri'] = 0.8 #0.98                   # MAC criteria [%]
Params['freq_cri'] = 0.2 #0.2                   # Frequency difference criteria [%]
Params['obj_cri'] = 0.02 #0.1                         # If more clusters match, an it is not clear what cluster is best, then check if the difference of the objective function values are less than the criteria. Then it is probably the one with higest MAC rather than frequency [difference]

# Params for modal expansion:
Params['expansion_modes'] = Params['MU_modes']
Params['filter_order'] = 4                                          # Order/strength of butterworth filter 
Params['filter_type'] = 'bandpass'                                   # 'lowpass', 'bandpass', 'highpass' or None
Params['filter_cut-off'] = np.array([0.5,90])                           # Cut of frequency(ies) for the butterworth filter [lower/upper cut-off value] or [>lower cut-off value<,upper cut-off value]
Params['output_type'] = 2                                           # system output type: 0-displacement; 1-velocities, 2-acceleration
Params['detrend_integration_order'] = 2                             # Order of detrend applied integrated signal, 0 = mean, 1 = linear, 2 = second order etc.
Params['beam_elements'] = np.array([3,4,5,6,7,8,9])                 # Order of elements in myModel that is beams
Params['validation_sensor_loc'] = np.array([[4,1]])                 # Validation sensor


# USER INPUT: 1 ..................................................................................
# Load the saved 2-minute blocks

filename = os.path.join(dirname, 'data/two_minute_blocks.npy')
blocks = np.load(filename)  # shape: (90, 30720, 4)

data = blocks[0,:,:]
# Rearranged order:
data = data[:, Params['sensor_order']] #  [0, 2, 1, 3] (swap columns 1 and 2)

# Running inital model update estimating the rotational stiffness and length
print("====== Initial model update ======")

model_pars={'modes': Params['MU_initial_modes'],
            'dofs_sel': Params['sensor_loc'],
            'k_rot': None, 
            'l4': None,
            'm': 0,
            }

updated_parameters, cluster_dict_ini = initial_run(data,Params,model_pars,plot=False)
Params['k_rot'] = updated_parameters[0]
Params['l4'] = updated_parameters[1]
Params['updated_values'][0] = Params['k_rot']
print(f"Model updating done. k_rot = {Params['k_rot']}, l4 = {Params['l4']}")

calculate_inital_model_error(updated_parameters,cluster_dict_ini,Params)

#Initial model 
pars_model = {'modes': Params['MU_modes'],
              'dofs_sel': Params['sensor_loc'],
              'k_rot': Params['k_rot'],
              'l4': Params['l4'],
              'm': 0
                }

print("\n====== Clustering, tracking, model updating and modal expansion on full data ======")

#Initilizationc
tracked_modaldata = {}
tracked_updatedParams = {}
tracked_updatedFreq = {}
modal_expansion_data = {}
tracked_clusters = {}
tracked_max_disp = []

#Specefic block start
experiment = 0
blocks = blocks[experiment:,:,:]
update_succes = []
for ii, block in enumerate(blocks):
    data = block[:, Params['sensor_order']] #Order of accelerometers.
    dataset = ii+experiment
    print(f"Data set: {dataset}")

    #System identification, mode tracking and Model updating
    if ii == 0:
        fig_ax1 = None
        fig_ax2 = None
        fig_ax3 = None
        fig_ax4 = None

    model_pars2={'modes': Params['modes_search_paring'],
            'dofs_sel': Params['sensor_loc'],
            'k_rot': None, 
            'l4': Params['l4'],
            'm': None,
            }
    model_update = True
    pack = model_updating_run(data,Params,model_pars2,tracked_clusters,(fig_ax1,fig_ax2,fig_ax3,fig_ax4),plot=True,model_updating=model_update)

    #Unpacking data
    cleaned_dict = pack[0]
    tracked_clusters = pack[1]
    (fig_ax1,fig_ax2,fig_ax3,fig_ax4) = pack[2]
    
    #Unpacking if model_updating is done
    if len(pack) > 3:
        update_succes.append(ii)
        updateded_params = pack[3]
        omegaM = pack[4]
        model_pars = pack[5]
        Params['updated_values'][0] = model_pars['k_rot']
        Params['updated_values'][1] = model_pars['m']
        tracked_updatedParams[ii] = updateded_params #Preperation for storing data
        tracked_updatedFreq[ii] = omegaM #Preperation for storing data
    else:
        # Updated model with latest parameters, even if model_updating failed
        id = 0
        for key in model_pars2:
            if str(key) in Params['pars_to_update']:
                model_pars[key] = Params['updated_values'][id]
                id += 1
            else:
                model_pars[key] = model_pars2[key]    

    #Modal expansion
    d_hat = modal_expansion_run(data,Params,model_pars,plot=False)

    extraction_dict = {}
    extraction_dict['element_type'] = np.array(["beam2d","beam2d","beam2d","beam2d","beam2d","beam2d","beam2d"])
    extraction_dict['elements'] = np.array([3,4,5,6,7,8,9])
    extraction_dict['y'] = np.array([1e-3/2,1e-3/2,1e-3/2,1e-3/2,1e-3/2,1e-3/2,1e-3/2])
    
    moment, stress, strain = estimate_stress(model_pars, d_hat, extraction_dict)

    expansion_validation = modal_expansion_validation(data,Params,model_pars,plot=False)
    modal_expansion_data[ii] = expansion_validation

    if 'bending_stress' in locals():
        bending_stress = np.append(bending_stress,[stress[2,1,:]],axis=0) #0 is axial, 1 is bending bottom node, 2 is bending top node
    else:
        bending_stress = np.array([stress[2,1,:]])

tracked_modaldata = track_for_plotting(tracked_clusters)

#Saving data

filename = os.path.join(Params['path'], 'data/cluster_dict_ini.pkl')
with open(filename, "wb") as f:
    pk.dump(cluster_dict_ini, f)

filename = os.path.join(Params['path'], 'data/tracked_modaldatadata.pkl')
with open(filename, "wb") as f:
    pk.dump(tracked_modaldata, f)

filename = os.path.join(Params['path'], 'data/tracked_modes.pkl')
with open(filename, "wb") as f:
    pk.dump(tracked_clusters, f)

if model_update == True:
    filename = os.path.join(Params['path'], 'data/tracked_updatedParams.pkl')
    with open(filename, "wb") as f:
        pk.dump(tracked_updatedParams, f)
        
    filename = os.path.join(Params['path'], 'data/tracked_updatedFreq.pkl')
    with open(filename, "wb") as f:
        pk.dump(tracked_updatedFreq, f)

    filename = os.path.join(Params['path'], 'data/modal_expansion_data.pkl')
    with open(filename, "wb") as f:
        pk.dump(modal_expansion_data, f)

    filename = os.path.join(Params['path'], 'data/stress_estimation')
    np.save(filename, bending_stress)

print(f"Model updating, modal expansion and fatigue estimation done")
print(f"l4 = {Params['l4']}")

plt.show(block=True)