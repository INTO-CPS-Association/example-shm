import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from functions.sysid import sysid
from functions.plot_sysid import (plot_stabilization_diagram,
                                  plot_clusters,
                                  plot_stabilization_diagram_for_paper,
                                  plot_clusters_for_paper)
from functions.clustering import (cluster_func)
from functions.model_update import (par_est)

def initial_run(data,Params,model_pars,plot=True):

    sysid_output = sysid(data, Params)

    if plot==True:
        fix_ax1 = plot_stabilization_diagram(oma_results=sysid_output,oma_params=Params,fig_ax=None)
        fix_ax1 = plot_stabilization_diagram_for_paper(oma_results=sysid_output,oma_params=Params,fig_ax=None)
        plt.show(block=False)
        sys.stdout.flush()

    # Clustering
    _, _, cluster_dict = cluster_func(sysid_output, Params)

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
        res = minimize(lambda x: par_est(x, cluster_dict, model_pars,pars_to_update, Params), Params['MU_initial_start_values'], bounds=Params['MU_initial_bounds'], options={'maxiter': 1000})
        if res.success == True:
            # Get the optimized parameter values
            X = res.x
            print(f'Updated values: {X}')
        else:
            print("Model update unsuccesful")

        # Updated model parameter       
        
    except ValueError as e:
        print(f"Skipping model updating due to error: {e}")

    return X, cluster_dict