from math import e
from typing import Tuple, Dict, Any
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.axes
import matplotlib.lines as mlines
import matplotlib.cm as cm
from src.methods.sysid_functions.clean_sysid_output import remove_highly_uncertain_points
from src.methods.sysid_functions.plot_sysid import (add_scatter_data,add_plot_standard_flair,add_plot_annotation)
plt.rcParams['font.family'] = 'Times New Roman'

def plot_clusters(clusters: Dict[str,dict],
        sysid_results: Dict[str, Any],
        sysid_params: Dict[str, Any],
        fig_ax = None,
        legend: bool = True)-> Tuple[matplotlib.figure.Figure,
                               Tuple[matplotlib.axes.Axes,matplotlib.axes.Axes]]:
    """
    Plot stabilization of clusters

    Args:
        clusters (Dict[str,dict]): Dictionary of clusters
        sysid_results (Dict[str,dict]): PyOMA results
        sysid_params (Dict[str,dict]): System identification parameters
        fix_ax (Tuple[plt.Figure, Tuple[plt.Axes]]): fig and ax of plot to redraw
        legend (bool): Plot legend or not
    Returns:
        fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]): fig and ax of plot

    """

    if fig_ax is None:
        plt.ion()
        fig, (ax1,ax2) = plt.subplots(1,2,figsize=(12, 6), tight_layout=True)
        title_number = 0
    else:
        fig, (ax1,ax2) = fig_ax
        title = fig.axes[0].get_title()
        ax1.clear()
        ax2.clear()

        iteration_number = title.split(' ')[-1]
        title_number = int(iteration_number) + 1

    #Pre-clean
    (frequencies, _, damping_ratios,
     __, ___, ____, _____) = remove_highly_uncertain_points(sysid_results,sysid_params)

    x = frequencies.flatten(order="f")
    y_model_order = np.array([i // len(frequencies) for i in range(len(x))]) * 1

    ax1 = add_scatter_data(ax1,x,y_model_order,None,error_dir="h",mark="^",
                           lab='Non clustered',size=20)
    

    colors = []
    for i, key in enumerate(clusters.keys()):
        cluster = clusters[key]
        model_order = cluster['model_order']
        ax1, col = add_scatter_cluster(ax1,cluster['f'],model_order,
                                    cluster['std_f'],i+1,error_dir="h")
        colors.append(col[0])
    ax1.clear()
    
    np.random.seed(1)
    colors2 = []
    for col in colors:
        if col in colors2:
            col2 = np.random.rand(3,)
            col1 = np.append(col2,[1])
            colors2.append(col1)
        else:
            colors2.append(col)


    # # # FREQUENCY ............................................................................
    std_bound = sysid_params['bound_multiplier']
    for i, key in enumerate(clusters.keys()):
        cluster = clusters[key]
        model_order = cluster['model_order']
        ax1, _ = add_scatter_cluster(ax1,cluster['f'],model_order,
                                       cluster['std_f'],i+1,error_dir="h",color=colors2[i])
        ax1.vlines(np.median(cluster['f']),min(model_order),
                   max(model_order),color=colors2[i])
        ax1 = add_global_mode(ax1, cluster, colors2[i], model_order=max(model_order)+1, type="freq")

    ax1 = add_plot_standard_flair(ax1,sysid_params)

    ax1.set_ylabel("Model order", fontsize=20, color = 'black')
    ax1.set_ylim(0, sysid_params['model_order'] + 2)

    ax1.set_title("Clustered stabilization diagram")
    if legend is True:
        lgd = ax1.legend(prop={'size': 10})
        add_global_marker_to_legend(lgd)

    ax1.set_title(f"Clustered stabilization diagram. Data set: {title_number}")


    # # # DAMPING ............................................................................
    ax2.set_ylabel("Damping ratio", fontsize=20, color = 'black')

    x = frequencies.flatten(order="f")
    y = damping_ratios.flatten(order="f")

    ax2 = add_scatter_data(ax2,x,y,None,error_dir="v", mark="^",size=20)

    damp_max_view = 0
    for i, key in enumerate(clusters.keys()):
        cluster = clusters[key]
        ax2, _ = add_scatter_cluster(ax2,cluster['f'],cluster['d'],
                                       cluster['std_d'],i,error_dir="v",color=colors2[i])
        ax2 = add_global_mode(ax2, cluster, colors2[i], type="damp")
        if max(cluster['d']+cluster['std_d']) > damp_max_view:
            damp_max_view = max(cluster['d']+cluster['std_d'])
        if 'global_ci' in cluster:
            if cluster['median_d']+cluster['global_ci'][1,1] > damp_max_view:
                damp_max_view = cluster['median_d']+cluster['global_ci'][1,1]

    ax2 = add_plot_annotation(ax2,x,y,y_model_order)
    ax2 = add_plot_standard_flair(ax2,sysid_params)

    ax2.set_title("Clustered damping ratios")
    if y[~np.isnan(y)].shape[0] > 1:
        ax2.set_ylim(0, damp_max_view+0.005)
    else:
        ax2.set_ylim(0, 0.1)

    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, (ax1,ax2)


def add_scatter_cluster(ax: matplotlib.axes.Axes, x: np.ndarray[float], y: np.ndarray[float],
                        std: np.ndarray[float], cluster_id = int,
                        error_dir: str = "h", color = None) -> Tuple[matplotlib.axes.Axes, Any]:
    """
    Add scatter plot of clusters to existing axes
    
    Args:
        ax (matplotlib.axes.Axes): ax from matplotlib
        x (np.ndarray[float]): x-axis data
        y (np.ndarray[float]): y-axis data
        std (np.ndarray[float]): covariance for errorbars
        cluster_id (int): Index of cluster for labeling
        error_dir (str): Direction of errorbars, either "h" horizontal or "v" vertical
    Returns:
        ax (matplotlib.axes.Axes): matplotlib axes
        col (matplotlib.colors): Color information
    """
    if color is None:
        sc = ax.scatter(x, y, marker="o", s=60, label=f'Cluster {cluster_id}')
    else:
        sc = ax.scatter(x, y, marker="o", s=60, label=f'Cluster {cluster_id}',facecolor = color)
    col = sc.get_facecolors().tolist()
    if std is not None:
        xerr = std
        if error_dir == "h":
            ax.errorbar(x, y, xerr=xerr, fmt="None", capsize=5, ecolor="gray", zorder=200)
        else:
            ax.errorbar(x, y, yerr=xerr, fmt="None", capsize=5, ecolor="gray", zorder=200)
    return ax, col

def add_global_mode(ax: matplotlib.axes.Axes, cluster: Dict[Any,str], col, model_order: int = 0, type = "freq"):
    """

    Args:
        ax (matplotlib.axes.Axes): ax from matplotlib
        cluster (Dict[str,Any]): Cluster dictionary
        col (matplotlib.colors): Color of cluster
        type (str): 'freq' og 'damp'
    Return:
        ax (matplotlib.axes.Axes): ax from matplotlib
    """
    if 'global_ci' in cluster:
        if type == "freq":
            ax.scatter(cluster['median_f'], model_order, marker="*", color=col, s=100)
            xerr_cluster = cluster['global_ci'][0,0]
            ax.errorbar(cluster['median_f'], model_order, xerr=xerr_cluster, fmt="None", capsize=5, ecolor="black",zorder=200)
            ax.fill_between(
                [cluster['median_f']-xerr_cluster,cluster['median_f']+xerr_cluster],
                [model_order,model_order],
                [min(cluster['model_order']),min(cluster['model_order'])],
                color=col,
                alpha=0.2,
            )
        elif type == "damp":
            ax.scatter(cluster['median_f'], cluster['median_d'], marker="D", color=col, s=60,zorder=100)
            xerr_cluster = cluster['global_ci'][1,1]
            ax.errorbar(cluster['median_f'], cluster['median_d'], yerr=xerr_cluster, fmt="None", capsize=5, ecolor="black",zorder=200)
            ax.fill_between(
                [min(cluster['f']),max(cluster['f'])],
                [cluster['median_d']+xerr_cluster,cluster['median_d']+xerr_cluster],
                [cluster['median_d']-xerr_cluster,cluster['median_d']-xerr_cluster],
                color=col,
                alpha=0.2,
            )
        else:
            print("Uncertainty type is wrong. type = 'freq' or 'damp'")

    return ax

def add_global_marker_to_legend(legend):
    """
    Add global marker to legend
    
    Args:
        legend (matplotlib.legend):
    Returns:
        legend (matplotlib.legend):

    """
    # from matplotlib.patches import Patch
    ax = legend.axes
    handles, labels = ax.get_legend_handles_labels()
    # handles.append(Patch(facecolor='grey', edgecolor='k'))
    global_marker = mlines.Line2D([], [], color='grey', marker='*', linestyle='solid',
                    markersize=10, label='Global mode')
    handles.append(global_marker)
    labels.append("Global mode")

    legend._legend_box = None
    legend._init_legend_box(handles, labels)
    legend._set_loc(legend._loc)
    legend.set_title(legend.get_title().get_text())
    
    return legend