import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from methods.packages.sys_id import sysid
from functions.sysid_plot import (plot_stabilization_diagram,
                                  plot_stabilization_diagram_for_paper,
                                  plot_clusters,
                                  plot_clusters_for_paper)
from methods.packages.clustering import (cluster_func)
from methods.packages.model_update import (par_est,pair_calculate)
from methods.packages.cantilever_beam import eval_yafem_model as beam_new

def initial_run(data,Params,model_pars,plot=True):

    sysid_output = sysid(data, Params)

    if plot==True:
        fix_ax1 = plot_stabilization_diagram(oma_results=sysid_output,oma_params=Params,fig_ax=None)
        fix_ax1 = plot_stabilization_diagram_for_paper(oma_results=sysid_output,oma_params=Params,fig_ax=None)
        plt.show(block=False)
        sys.stdout.flush()

    # Clustering
    _, _, cluster_dict = cluster_func(sysid_output, Params, plot=False)

    # for key in cluster_dict.keys():
    #     cluster = cluster_dict[key]
    #     print(cluster['median_f'],np.mean(cluster['d']),np.median(cluster['d']))

    if plot==True:
        fix_ax2 = plot_clusters(clusters=cluster_dict,oma_results=sysid_output,oma_params=Params,fig_ax=None)
        fix_ax2 = plot_clusters_for_paper(clusters=cluster_dict,oma_results=sysid_output,oma_params=Params,fig_ax=None)
        #fix_ax3 = plot_clusters_old(clusters=cleaned_clusters,oma_results=sysid_output,oma_params=Params,fig_ax=None)
        plt.show(block=True)
        sys.stdout.flush()

    # # Initial values
    x0 = Params['MU_initial_start_values']  # 1st parameter is spring stiffness and 2nd is unbounded length

    # # Create bounds using element-wise i.e. different parameters have different bounds
    bounds = Params['MU_initial_bounds'] # bounds for stiffness, k_rot, and length, l4

    X = None
    pars_to_update = Params['pars_to_update_initial']
    try:
        res = minimize(lambda x: par_est(x, cluster_dict, model_pars, pars_to_update, Params), Params['MU_initial_start_values'], bounds=Params['MU_initial_bounds'], options={'maxiter': 1000})
        if res.success == True:
            # Get the optimized parameter values
            X = res.x
            print(f'Updated values: {X}')
        else:
            print("Model update unsuccesful")

        # Updated model parameter       
        
    except ValueError as e:
        print(f"Skipping model updating due to error: {e}")


    pars_before={'modes': Params['MU_initial_modes'],
            'dofs_sel': Params['sensor_loc'],
            'k_rot': Params['MU_initial_start_values'][0], 
            'l4': Params['MU_initial_start_values'][1],
            'm': 0,
            }
    
    omegaM, phi, PhiM, myModel = beam_new.eval_yafem_model(pars_before)
    paired_frequencies_1, paired_mode_shapes_1, omegaM_1, PhiM_1 = pair_calculate(omegaM, PhiM, cluster_dict, Params)

    pars_after = {'modes': Params['MU_initial_modes'],
                  'dofs_sel': Params['sensor_loc'],
                  'k_rot': X[0],
                  'l4': X[1],
                  'm': 0
                }
    omegaM, phi, PhiM, myModel = beam_new.eval_yafem_model(pars_after)
    paired_frequencies_2, paired_mode_shapes_2, omegaM_2, PhiM_2 = pair_calculate(omegaM, PhiM, cluster_dict, Params)

    freq_error_before = 100 * np.abs(omegaM_1 - paired_frequencies_1) / paired_frequencies_1
    freq_error_after = 100 * np.abs(omegaM_2 - paired_frequencies_2) / paired_frequencies_2

    # Compute MAC_1
    MACn = np.abs(np.diag(np.conj(paired_mode_shapes_1).T @ PhiM_1))**2
    MACd = np.diag(np.conj(paired_mode_shapes_1).T @ paired_mode_shapes_1) * np.diag(np.conj(PhiM_1).T @ PhiM_1)
    MAC_1 = MACn / MACd

    # Compute MAC_2
    MACn = np.abs(np.diag(np.conj(paired_mode_shapes_2).T @ PhiM_2))**2
    MACd = np.diag(np.conj(paired_mode_shapes_2).T @ paired_mode_shapes_2) * np.diag(np.conj(PhiM_2).T @ PhiM_2)
    MAC_2 = MACn / MACd

    initial_model_update_results = (freq_error_before,freq_error_after,MAC_1,MAC_2)

    return X, initial_model_update_results