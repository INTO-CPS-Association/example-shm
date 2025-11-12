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
    legend = True)-> Tuple[Any, Tuple[Any, Any]]:
    """
    Plot stabilization of clusters

    Args:
        clsuters (Dict[str,dict]): Dictionary of clusters
        sysid_results (Dict[str,dict]): PyOMA results
        sysid_params (Dict[str,dict]): sysid parameters
        fix_ax (Tuple[matplotlib.figure.Figure, Tuple[matplotlib.axes.Axes,matplotlib.axes.Axes]]): fig and ax of plot to redraw
    Returns:
        fig_ax (Tuple[matplotlib.figure.Figure, Tuple[matplotlib.axes.Axes,matplotlib.axes.Axes]]): fig and ax of plot

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
    frequencies, cov_freq, damping_ratios, cov_damping, _ = remove_highly_uncertain_points(sysid_results,sysid_params)

    x = frequencies.flatten(order="f")
    y_model_order = np.array([i // len(frequencies) for i in range(len(x))]) * 1

    ax1 = add_scatter_data(ax1,x,y_model_order,None,error_dir="h",mark="^",lab='Non clustered',size=20)

    for i, key in enumerate(clusters.keys()):
        cluster = clusters[key]
        MO = cluster['model_order']
        ax1, col = add_scatter_cluster(ax1,cluster['f'],MO,cluster['cov_f'],i,error_dir="h")
        ax1.vlines(np.median(cluster['f']),min(MO),
                   max(MO),color=col)

    ax1 = add_plot_standard_flair(ax1,sysid_params)

    ax1.set_ylabel("Model order", fontsize=20, color = 'black')
    ax1.set_ylim(0, sysid_params['model_order'] + 1)
    if legend is True:
        ax1.legend(prop={'size': 10})
    ax1.set_title(f"Data set: {title_number}")

    # # # ............................................................................

    ax2.set_ylabel("Damping ratio", fontsize=20, color = 'black')

    x = frequencies.flatten(order="f")
    y = damping_ratios.flatten(order="f")

    ax2 = add_scatter_data(ax2,x,y,None,error_dir="v", mark="^",size=20)

    for i, key in enumerate(clusters.keys()):
        cluster = clusters[key]
        ax2, col = add_scatter_cluster(ax2,cluster['f'],cluster['d'],cluster['cov_d'],i,error_dir="v")

    ax2 = add_plot_annotation(ax2,x,y,y_model_order)
    ax2 = add_plot_standard_flair(ax2,sysid_params)
    
    if y[~np.isnan(y)].shape[0] > 1:
        ax2.set_ylim(0, max(max(y[~np.isnan(y)])+0.005,0.1))
    else:
        ax2.set_ylim(0, 0.1)

    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, (ax1,ax2)


def add_scatter_cluster(ax: matplotlib.axes.Axes, x: np.ndarray, y: np.ndarray, cov: np.ndarray, cluster_id: int, error_dir: str = "h") -> Tuple[matplotlib.axes.Axes, Any]:
    """
    Add scatter plot of clusters to existing axes
    
    Args:
        ax (matplotlib.axes.Axes): ax from matplotlib
        x (np.ndarray): x-axis data
        y (np.ndarray): y-axis data
        cov (np.ndarray): covariance for errorbars
        cluster_id (int): Index of cluster for labeling
        error_dir (str): Direction of errorbars, either "h" horizontal or "v" vertical

    Returns:
        ax (matplotlib.axes.Axes):
        col (Any):
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