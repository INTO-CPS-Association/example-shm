from typing import Tuple, Dict, Any
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.axes
from functions.clean_sysid_output import remove_highly_uncertain_points
from functions.plot_sysid import (add_scatter_data,add_plot_standard_flair,add_plot_annotation)
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
     _, _) = remove_highly_uncertain_points(sysid_results,sysid_params)

    x = frequencies.flatten(order="f")
    y_model_order = np.array([i // len(frequencies) for i in range(len(x))]) * 1

    ax1 = add_scatter_data(ax1,x,y_model_order,None,error_dir="h",mark="^",
                           lab='Non clustered',size=20)

    for i, key in enumerate(clusters.keys()):
        cluster = clusters[key]
        model_order = cluster['model_order']
        ax1, col = add_scatter_cluster(ax1,cluster['f'],model_order,
                                       cluster['cov_f'],i,error_dir="h")
        ax1.vlines(np.median(cluster['f']),min(model_order),
                   max(model_order),color=col)

    ax1 = add_plot_standard_flair(ax1,sysid_params)

    ax1.set_ylabel("Model order", fontsize=20, color = 'black')
    ax1.set_ylim(0, sysid_params['model_order'] + 1)
    ax1.set_title("Clustered stabilization diagram")
    if legend is True:
        ax1.legend(prop={'size': 10})
    ax1.set_title(f"Clustered stabilization diagram. Data set: {title_number}")

    # # # ............................................................................

    ax2.set_ylabel("Damping ratio", fontsize=20, color = 'black')

    x = frequencies.flatten(order="f")
    y = damping_ratios.flatten(order="f")

    ax2 = add_scatter_data(ax2,x,y,None,error_dir="v", mark="^",size=20)

    for i, key in enumerate(clusters.keys()):
        cluster = clusters[key]
        ax2, col = add_scatter_cluster(ax2,cluster['f'],cluster['d'],
                                       cluster['cov_d'],i,error_dir="v")

    ax2 = add_plot_annotation(ax2,x,y,y_model_order)
    ax2 = add_plot_standard_flair(ax2,sysid_params)
    
    ax2.set_title("Clustered damping ratios")
    if y[~np.isnan(y)].shape[0] > 1:
        ax2.set_ylim(0, max(max(y[~np.isnan(y)])+0.005,0.1))
    else:
        ax2.set_ylim(0, 0.1)

    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, (ax1,ax2)


def add_scatter_cluster(ax: matplotlib.axes.Axes, x: np.ndarray[float], y: np.ndarray[float],
                        cov: np.ndarray[float], cluster_id = int,
                        error_dir: str = "h") -> Tuple[matplotlib.axes.Axes, Any]:
    """
    Add scatter plot of clusters to existing axes
    
    Args:
        ax (matplotlib.axes.Axes): ax from matplotlib
        x (np.ndarray[float]): x-axis data
        y (np.ndarray[float]): y-axis data
        cov (np.ndarray[float]): covariance for errorbars
        cluster_id (int): Index of cluster for labeling
        error_dir (str): Direction of errorbars, either "h" horizontal or "v" vertical

    Returns:
        ax (matplotlib.axes.Axes): matplotlib axes
        col (Any): Color information
    """
    sc = ax.scatter(x, y, marker="o", s=60, label=f'Cluster {cluster_id}')
    col = sc.get_facecolors().tolist()
    if cov is not None:
        xerr = np.sqrt(cov) * 2
        if error_dir == "h":
            ax.errorbar(x, y, xerr=xerr, fmt="None", capsize=5, ecolor="gray", zorder=200)
        else:
            ax.errorbar(x, y, yerr=xerr, fmt="None", capsize=5, ecolor="gray", zorder=200)
    return ax, col
