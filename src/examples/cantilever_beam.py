import numpy as np
from methods.packages.cantilever_beam.cantileverbeam_initial_update import initial_run
from methods.packages.model_updater import model_updating_run
from methods.packages.cantilever_beam.modal_expansion import modal_expansion_run
from methods.packages.mode_tracking import track_for_plotting
from functions.cantilever_beam_plots.results_plot import cantilever_beam_plots
from functions.cantilever_beam_plots.fatigue_results import fatigue_plots


def run_cantilever_beam(config_path):

    # PARAMS:
    Params = {}

    Params['Fs'] = 256                              # Sample frequency
    Params['model_order_min'] = 2                   # Set the min model order
    Params['model_order'] = 15                      # Set the max model order for analysis
    Params['block_shift'] = 30                      # Block size in Hankel matrix
    Params['sensor_order'] = np.array([0, 2, 1, 3]) # sensor location in data

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

    Params['pars_to_update'] = ["k_rot","m"]
    Params['MU_start_values'] = np.array([10, 0.015])
    Params['MU_bounds'] = [(0.01, 1000), (0, 1000)]
    Params['MU_modes'] = [1,2,3]

    Params['updated_values'] = Params['MU_start_values'] 

    # Params for mode tracking
    Params['phi_cri'] = 0.8 #0.98                   # MAC criteria [%]
    Params['freq_cri'] = 0.2 #0.2                   # Frequency difference criteria [%]
    Params['obj_cri'] = 0.1                         # If more clusters match, an it is not clear what cluster is best, then check if the difference of the objective function values are less than the criteria. Then it is probably the one with higest MAC rather than frequency [difference]

    # Params for modal expansion:
    Params['sensor_loc'] = np.array([[7,1],[6,1],[5,1],[4,1]])          # sensor location
    Params['validation_sensor_loc'] = np.array([[4,1]])                 # Validation sensor
    Params['output_type'] = 2                                           # system output type: 0-displacement; 1-velocities, 2-acceleration
    Params['model_sel_DOF'] = "all"

    # USER INPUT: 1 ..................................................................................
    # Load the saved 2-minute blocks
    blocks = np.load('./src/data/cantilever_beam/two_minute_blocks.npy')  # shape: (90, 30720, 4)

    data = blocks[0,:,:]
    # Rearranged order: [0, 2, 1, 3] (swap columns 1 and 2)
    data = data[:, Params['sensor_order']]

    # Running inital model update estimating the rotational stiffness and length
    print("====== Initial model update ======")
    model_pars={'modes': Params['MU_initial_modes'],
            'dofs_sel': Params['sensor_loc'],
            'k_rot': None, 
            'l4': None,
            'm': 0,
            }
    updated_parameters, initial_model_update_results = initial_run(data,Params,model_pars,plot=False)
    Params['k_rot'] = updated_parameters[0]
    Params['l4'] = updated_parameters[1]
    print(f"Model updating done. k_rot = {Params['k_rot']}, l4 = {Params['l4']}")
    
    #Initial model 
    model_pars={'modes': Params['MU_initial_modes'],
            'dofs_sel': Params['sensor_loc'],
            'k_rot': None, 
            'l4': None,
            'm': 0,
            }

    print("\n====== Clustering, tracking, model updating and modal expansion on full data ======")

    #Initilizationc
    tracked_modaldata = {}
    tracked_updatedParams = {}
    tracked_updatedFreq = {}
    modal_expansion_data = {}
    tracked_clusters = {}

    #Specefic block start
    experiment = 0
    blocks = blocks[experiment:,:,:]
    for ii, block in enumerate(blocks):
        
        data = block[:, Params['sensor_order']] #Order of accelerometers.
        dataset = ii+experiment
        print(f"Data set: {dataset}")

        #System identification, mode tracking and Model updating
        if ii == 0:
            fig_ax1 = None
            fig_ax2 = None
            fig_ax3 = None

        model_pars2={'modes': 6,
                'dofs_sel': Params['sensor_loc'],
                'k_rot': None, 
                'l4': Params['l4'],
                'm': None,
                }
        model_update = True
        pack = model_updating_run(data,Params,model_pars2,tracked_clusters,(fig_ax1,fig_ax2,fig_ax3),plot=True,model_updating=model_update)

        #Unpacking data
        cleaned_dict = pack[0]
        tracked_clusters = pack[1]
        (fig_ax1,fig_ax2,fig_ax3) = pack[2]
        
        #Unpacking if model_updating is done
        print(model_pars)
        if len(pack) > 3:
            updateded_params = pack[3]
            omegaM = pack[4]
            model_pars = pack[5]
            Params['updated_values'][0] = model_pars['k_rot']
            Params['updated_values'][1] = model_pars['m']
            tracked_updatedParams[ii] = updateded_params #Preperation for storing data
            tracked_updatedFreq[ii] = omegaM #Preperation for storing data
        else:
            # Updated model with latest parameters, even if model_updating failed
            idx = 0
            for key in model_pars:
                if str(key) in Params['pars_to_update']:
                    model_pars[key] = Params['updated_values'][idx]
                    idx += 1

        print(model_pars)
        #Modal expansion
        d_hat, stress_beam, strain_beam, moment_beam = modal_expansion_run(data,Params,model_pars,plot=False)
        #print(stress_beam.shape) #First index is element no. second index is nodal DOF (Axial, bending node 1, bending node 2), last index is measurement no.

        if 'bending_stress' in locals():
            bending_stress = np.append(bending_stress,[stress_beam[3,1,:]],axis=0) #0 is axial, 1 is bending bottom node, 2 is bending top node
        else:
            bending_stress = np.array([stress_beam[3,1,:]])


    tracked_modaldata = track_for_plotting(tracked_clusters)   

    print(f"Model updating, modal expansion and fatigue estimation done")
    print(f"l4 = {Params['l4']}")

    cantilever_beam_plots(tracked_modaldata,tracked_clusters,tracked_updatedParams,tracked_updatedFreq,modal_expansion_data,bending_stress,initial_model_update_results,all_at_once=True)

    fatigue_plots(bending_stress)
