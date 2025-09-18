import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from methods.packages.sys_id import sysid
from functions.sysid_plot import (plot_clusters)
from methods.packages.clustering import (cluster_func)
from methods.packages.mode_tracking import (cluster_tracking)
from methods.packages.model_update import (par_est)
from methods.packages.cantilever_beam import eval_yafem_model as beam_new

def model_updating_run(data,Params,model_pars,tracked_clusters,fig_axes,plot=False,model_updating=False):

    (fig_ax1,fig_ax2,fig_ax3) = fig_axes

    sysid_output = sysid(data, Params)

    # Cluster generation
    cluster_dict_before, cluster_dict_allignment, cluster_dict = cluster_func(sysid_output, Params, plot=False)

    # Stabilization graph
    if plot==True:
        fig_ax3 = plot_clusters(clusters=cluster_dict,oma_results=sysid_output,oma_params=Params,fig_ax=fig_ax3)
        plt.show(block=False)
        sys.stdout.flush()

    # Cluster tracking
    tracked_clusters = cluster_tracking(cluster_dict,tracked_clusters,Params)

    # # Initial values
    x0 = Params['MU_start_values']  # 1st parameter is spring stiffness and 2nd is tip mass
    # # Create bounds using element-wise i.e. different parameters have different bounds
    bounds = Params['MU_bounds'] # bounds for stiffness and tip mass

    X = None
    pars_to_update = Params['pars_to_update']
    if model_updating is True:
        try:
            res = minimize(lambda x: par_est(x, cluster_dict, model_pars, pars_to_update, Params), Params['MU_start_values'], bounds=Params['MU_bounds'], options={'maxiter': 1000})
            # Get the optimized parameter values
            X = res.x
            print(f'Updated values: {X}')

            # Updated model parameter
            id = 0
            for key in model_pars:
                if str(key) in pars_to_update:
                    model_pars[key] = X[id]
                    id += 1
            
            omegaMU, phi, PhiMU, myModel = beam_new.eval_yafem_model(model_pars)
            
            
        except ValueError as e:
            print(f"Skipping model updating due to error: {e}")
            

        if X is not None:
            return [cluster_dict, tracked_clusters,(fig_ax1, fig_ax2, fig_ax3), X, omegaMU, model_pars]
        else:
            return [cluster_dict, tracked_clusters,(fig_ax1, fig_ax2, fig_ax3)]
    else:
        return [cluster_dict, tracked_clusters,(fig_ax1, fig_ax2, fig_ax3)]
