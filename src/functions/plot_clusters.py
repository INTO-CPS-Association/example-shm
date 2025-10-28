from typing import Tuple, Dict, Any
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure
from functions.clean_sysid_output import remove_highly_uncertain_points
from functions.plot_sysid import (add_scatter_data,add_plot_standard_flair,add_plot_annotation)
plt.rcParams['font.family'] = 'Times New Roman'


# def plot_clusters(clusters: Dict[str,dict],
#         sysid_results: Dict[str, Any],
#         sysid_params: Dict[str, Any],
#         fig_ax = None)-> Tuple[matplotlib.figure.Figure, Tuple[plt.Axes,plt.Axes]]:
#     """
#     Plot stabilization of clusters

#     Args:
#         clsuters (dict): Dictionary of clusters
#         sysid_results (dict): PyOMA results
#         sysid_params (dict): sysid parameters
#         fix_ax (tuple): fig and ax of plot to redraw
#     Returns:
#         fig_ax (tuple): fig and ax of plot

#     """

#     if fig_ax is None:
#         plt.ion()
#         fig, (ax1,ax2) = plt.subplots(1,2,figsize=(12, 6), tight_layout=True)
#         title_number = 0
#     else:
#         fig, (ax1,ax2) = fig_ax
#         title = fig.axes[0].get_title()
#         ax1.clear()
#         ax2.clear()

#         iteration_number = title.split(' ')[-1]
#         #print(iteration_number)
#         title_number = int(iteration_number) + 1

#     #Pre-clean
#     frequencies, cov_freq, damping_ratios, cov_damping, _ = remove_highly_uncertain_points(sysid_results,sysid_params)

#     ax1.set_ylabel("Model order", fontsize=20, color = 'black')

#     x = frequencies.flatten(order="f")
#     y_model_order = np.array([i // len(frequencies) for i in range(len(x))]) * 1

#     ax1 = add_scatter_data(ax1,x,y_model_order,None)

#     idx = 0
#     for i, key in enumerate(clusters.keys()):
#         cluster = clusters[key]
#         MO = cluster['model_order']
#         freq_cluster = cluster['f']
#         freq_cov_cluster = cluster['cov_f']

#         sc = ax1.scatter(freq_cluster, MO, marker="o", s=40, label=f'Cluster {i}')
#         col = sc.get_facecolors().tolist()
#         ax1.vlines(np.median(freq_cluster),min(cluster['model_order']),
#                    max(cluster['model_order']),color=col)

#         xerr_cluster = np.sqrt(freq_cov_cluster) * 2
#         # ax1.errorbar(freq_cluster, MO, xerr=xerr_cluster,
#         #              fmt="None", capsize=5, ecolor="gray",zorder=200)
        
#         ax1, col = add_scatter_cluster(ax1,cluster['f'],cluster['model_order'],cluster['cov_f'])
#         idx += 1

#     ax1 = add_plot_standard_flair(ax1,sysid_params)

#     ax1.set_ylim(0, sysid_params['model_order'] + 1)
#     # Add major and minor grid lines
#     ax1.legend(prop={'size': 20})
#     ax1.set_title(f"Data set: {title_number}")

#     # # # ............................................................................

#     ax2.set_ylabel("Damping ratio", fontsize=20, color = 'black')
#     ax2.set_xlabel("Frequency [Hz]", fontsize=20, color = 'black')
#     ax2.tick_params(axis='both', which='major', labelsize=17)

#     x = frequencies.flatten(order="f")
#     y = damping_ratios.flatten(order="f")

#     sc = ax2.scatter(x, y, marker="^", s=20, c="r", zorder=0, label='Non clustered')
#     if cov_freq is not None:
#         xerr = np.sqrt(cov_damping) * 2
#         xerr = xerr.flatten(order="f")
#         ax2.errorbar(x, y, yerr=xerr, fmt="None", capsize=5, ecolor="gray")

#     for i, key in enumerate(clusters.keys()):
#         cluster = clusters[key]
#         freq_cluster = cluster['f']
#         damp_cluster = cluster['d']
#         damp_cov_cluster = cluster['cov_d']

#         ax2.scatter(freq_cluster, damp_cluster, s=50, zorder=3)
#         xerr_cluster = np.sqrt(damp_cov_cluster) * 2
#         ax2.errorbar(freq_cluster, damp_cluster, yerr=xerr_cluster,
#                      fmt="None", capsize=5, ecolor="gray")

#     for i, txt in enumerate(y_model_order):
#         ax2.annotate(str(txt), (x[i], y[i]))
    
#     if y[~np.isnan(y)].shape[0] > 1:
#         ax2.set_ylim(0, max(max(y[~np.isnan(y)])+0.005,0.1))
#     else:
#         ax2.set_ylim(0, 0.1)
#     ax2.set_xlim(0, sysid_params['Fs']/2)

#     # Add major and minor grid lines
#     ax2.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
#     ax2.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)

#     fig.tight_layout()
#     fig.canvas.draw()
#     fig.canvas.flush_events()

#     return fig, (ax1,ax2)

def plot_clusters(clusters: Dict[str,dict],
        sysid_results: Dict[str, Any],
        sysid_params: Dict[str, Any],
        fig_ax = None)-> Tuple[matplotlib.figure.Figure, Tuple[plt.Axes,plt.Axes]]:
    """
    Plot stabilization of clusters

    Args:
        clsuters (dict): Dictionary of clusters
        sysid_results (dict): PyOMA results
        sysid_params (dict): sysid parameters
        fix_ax (tuple): fig and ax of plot to redraw
    Returns:
        fig_ax (tuple): fig and ax of plot

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
    ax1.legend(prop={'size': 20})
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


def add_scatter_cluster(ax,x,y,cov,i,error_dir="h"):
    sc = ax.scatter(x, y, marker="o", s=60, label=f'Cluster {i}')
    col = sc.get_facecolors().tolist()
    if cov is not None:
        xerr = np.sqrt(cov) * 2
        if error_dir == "h":
            ax.errorbar(x, y, xerr=xerr, fmt="None", capsize=5, ecolor="gray", zorder=200)
        else:
            ax.errorbar(x, y, yerr=xerr, fmt="None", capsize=5, ecolor="gray", zorder=200)
    return ax, col