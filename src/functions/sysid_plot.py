from typing import Tuple, Dict, Any
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure
from methods.packages.clustering import (remove_complex_conjugates,remove_highly_uncertain_points)
plt.rcParams['font.family'] = 'Times New Roman'


def plot_pre_stabilization_diagram(
        oma_results: Dict[str, Any],
        oma_params: Dict[str, Any],
        fig_ax)-> Tuple[matplotlib.figure.Figure, Tuple[plt.Axes,plt.Axes]]:

    """
    Plot stabilization of raw OMA data before pre-cleaning

    Args:
        oma_results (dict): PyOMA results
        oma_params (dict): OMA parameters
        fix_ax (tuple): fig and ax of plot to redraw
    Returns:
        fig_ax (tuple): fig and ax of plot

    """


    if fig_ax is None:
        plt.ion()
        fig, (ax1,ax2) = plt.subplots(1,2,figsize=(8, 6), tight_layout=True)
    else:
        fig, (ax1,ax2) = fig_ax
        ax1.clear()
        ax2.clear()

    frequencies, damping_ratios, _, cov_freq, cov_damping = remove_complex_conjugates(oma_results)

    ax1.set_ylabel("Model order", fontsize=20, color = 'black')
    ax1.set_xlabel("Frequency [Hz]", fontsize=20, color = 'black')
    ax1.tick_params(axis='both', which='major', labelsize=17)

    x = frequencies.flatten(order="f")
    y_model_order = np.array([i // len(frequencies) for i in range(len(x))]) * 1

    ax1.scatter(x, y_model_order, marker="o", s=50, c="r")
    if cov_freq is not None:
        xerr = 2*np.sqrt(cov_freq)
        xerr = xerr.flatten(order="f")
        ax1.errorbar(x, y_model_order, xerr=xerr, fmt="None", capsize=5, ecolor="gray")

    ax1.set_ylim(0, oma_params['model_order'] + 1)
    ax1.set_xlim(0, oma_params['Fs']/2)

    # Add major and minor grid lines
    ax1.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax1.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)

    # # # ............................................................................

    ax2.set_ylabel("Damping ratio", fontsize=20, color = 'black')
    ax2.set_xlabel("Frequency [Hz]", fontsize=20, color = 'black')
    ax2.tick_params(axis='both', which='major', labelsize=17)

    x = frequencies.flatten(order="f")
    y = damping_ratios.flatten(order="f")

    ax2.scatter(x, y, marker="o", s=50, c="r")
    if cov_freq is not None:
        xerr = np.sqrt(cov_damping) * 2
        xerr = xerr.flatten(order="f")
        ax2.errorbar(x, y, yerr=xerr, fmt="None", capsize=5, ecolor="gray")

    ax2.set_ylim(0, 0.1+0.005)
    ax2.set_xlim(0, oma_params['Fs']/2)

    for i, txt in enumerate(y_model_order):
        ax2.annotate(str(txt), (x[i], y[i]))

    # Add major and minor grid lines
    ax2.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax2.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)

    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, (ax1,ax2)

def plot_stabilization_diagram(
        oma_results: Dict[str, Any],
        oma_params: Dict[str, Any],
        fig_ax)-> Tuple[matplotlib.figure.Figure, Tuple[plt.Axes,plt.Axes]]:
    """
    Plot stabilization of OMA data before after pre-cleaning

    Args:
        oma_results (dict): PyOMA results
        oma_params (dict): OMA parameters
    Returns:
        fig_ax (tuple): fig and ax of plot

    """

    if fig_ax is None:
        plt.ion()
        fig, (ax1,ax2) = plt.subplots(1,2,figsize=(8, 6), tight_layout=True)
    else:
        fig, (ax1,ax2) = fig_ax
        ax1.clear()
        ax2.clear()

    #Pre-clean
    frequencies, cov_freq, damping_ratios, cov_damping, _ = remove_highly_uncertain_points(oma_results,oma_params)

    ax1.set_ylabel("Model order", fontsize=20, color = 'black')
    ax1.set_xlabel("Frequency [Hz]", fontsize=20, color = 'black')
    ax1.tick_params(axis='both', which='major', labelsize=17)

    x = frequencies.flatten(order="f")
    y_model_order = np.array([i // len(frequencies) for i in range(len(x))]) * 1

    ax1.scatter(x, y_model_order, marker="o", s=50, c="r")

    if cov_freq is not None:
        xerr = 2*np.sqrt(cov_freq)
        xerr = xerr.flatten(order="f")
        ax1.errorbar(x, y_model_order, xerr=xerr, fmt="None", capsize=5, ecolor="gray")

    ax1.set_ylim(0, oma_params['model_order'] + 1)
    ax1.set_xlim(0, oma_params['Fs']/2)

    # Add major and minor grid lines
    ax1.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax1.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)

    # # # ............................................................................

    ax2.set_ylabel("Damping ratio", fontsize=20, color = 'black')
    ax2.set_xlabel("Frequency [Hz]", fontsize=20, color = 'black')
    ax2.tick_params(axis='both', which='major', labelsize=17)

    x = frequencies.flatten(order="f")
    y = damping_ratios.flatten(order="f")

    ax2.scatter(x, y, marker="o", s=50, c="r")

    if cov_freq is not None:
        xerr = np.sqrt(cov_damping) * 2
        xerr = xerr.flatten(order="f")
        ax2.errorbar(x, y, yerr=xerr, fmt="None", capsize=5, ecolor="gray")

    for i, txt in enumerate(y_model_order):
        ax2.annotate(str(txt), (x[i], y[i]))

    ax2.set_ylim(0, max(y[~np.isnan(y)])+0.005)
    ax2.set_xlim(0, oma_params['Fs']/2)

    # Add major and minor grid lines
    ax2.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax2.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)

    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, (ax1,ax2)

def plot_clusters(clusters: Dict[str,dict],
        oma_results: Dict[str, Any],
        oma_params: Dict[str, Any],
        fig_ax = None)-> Tuple[matplotlib.figure.Figure, Tuple[plt.Axes,plt.Axes]]:
    """
    Plot stabilization of clusters

    Args:
        clsuters (dict): Dictionary of clusters
        oma_results (dict): PyOMA results
        oma_params (dict): OMA parameters
        fix_ax (tuple): fig and ax of plot to redraw
    Returns:
        fig_ax (tuple): fig and ax of plot

    """

    if fig_ax is None:
        plt.ion()
        #fig, (ax1,ax2) = plt.subplots(1,2,figsize=(8, 6), tight_layout=True)
        fig, (ax1,ax2) = plt.subplots(1,2,figsize=(12, 6), tight_layout=True)
        title_number = 0
    else:
        fig, (ax1,ax2) = fig_ax
        title = fig.axes[0].get_title()
        ax1.clear()
        ax2.clear()

        iteration_number = title.split(' ')[-1]
        #print(iteration_number)
        title_number = int(iteration_number) + 1

    #Pre-clean
    frequencies, cov_freq, damping_ratios, cov_damping, _ = remove_highly_uncertain_points(oma_results,oma_params)

    ax1.set_ylabel("Model order", fontsize=20, color = 'black')
    ax1.set_xlabel("Frequency [Hz]", fontsize=20, color = 'black')
    ax1.tick_params(axis='both', which='major', labelsize=17)

    x = frequencies.flatten(order="f")
    y_model_order = np.array([i // len(frequencies) for i in range(len(x))]) * 1

    ax1.scatter(x, y_model_order, marker="^", s=20, c="r", zorder=0, label='Non clustered')

    if cov_freq is not None:
        xerr = 2*np.sqrt(cov_freq)
        xerr = xerr.flatten(order="f")
        ax1.errorbar(
            x, y_model_order, xerr=xerr, fmt="None", capsize=5, ecolor="r", zorder=1
        )

    idx = 0
    for i, key in enumerate(clusters.keys()):
        cluster = clusters[key]
        MO = cluster['model_order']
        freq_cluster = cluster['f']
        freq_cov_cluster = cluster['cov_f']

        sc = ax1.scatter(freq_cluster, MO, marker="o", s=40, label=f'Cluster {i}')
        col = sc.get_facecolors().tolist()
        ax1.vlines(np.median(freq_cluster),min(cluster['model_order']),
                   max(cluster['model_order']),color=col)

        xerr_cluster = np.sqrt(freq_cov_cluster) * 2
        ax1.errorbar(freq_cluster, MO, xerr=xerr_cluster,
                     fmt="None", capsize=5, ecolor="gray",zorder=200)
        idx += 1

    ax1.set_ylim(0, oma_params['model_order'] + 1)
    ax1.set_xlim(0, oma_params['Fs']/2)
    # Add major and minor grid lines
    ax1.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax1.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)
    ax1.legend(prop={'size': 20}) #bbox_to_anchor=(0.1, 1.1)
    ax1.set_title(f"Data set: {title_number}")

    # # # ............................................................................

    ax2.set_ylabel("Damping ratio", fontsize=20, color = 'black')
    ax2.set_xlabel("Frequency [Hz]", fontsize=20, color = 'black')
    ax2.tick_params(axis='both', which='major', labelsize=17)

    x = frequencies.flatten(order="f")
    y = damping_ratios.flatten(order="f")

    sc = ax2.scatter(x, y, marker="^", s=20, c="r", zorder=0, label='Non clustered')
    if cov_freq is not None:
        xerr = np.sqrt(cov_damping) * 2
        xerr = xerr.flatten(order="f")
        ax2.errorbar(x, y, yerr=xerr, fmt="None", capsize=5, ecolor="gray")

    for i, key in enumerate(clusters.keys()):
        cluster = clusters[key]
        freq_cluster = cluster['f']
        damp_cluster = cluster['d']
        damp_cov_cluster = cluster['cov_d']

        ax2.scatter(freq_cluster, damp_cluster, s=50, zorder=3)
        xerr_cluster = np.sqrt(damp_cov_cluster) * 2
        ax2.errorbar(freq_cluster, damp_cluster, yerr=xerr_cluster,
                     fmt="None", capsize=5, ecolor="gray")

    for i, txt in enumerate(y_model_order):
        ax2.annotate(str(txt), (x[i], y[i]))
    
    if y[~np.isnan(y)].shape[0] > 1:
        ax2.set_ylim(0, max(max(y[~np.isnan(y)])+0.005,0.1))
    else:
        ax2.set_ylim(0, 0.1)
    ax2.set_xlim(0, oma_params['Fs']/2)

    # Add major and minor grid lines
    ax2.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax2.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)

    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, (ax1,ax2)

def plot_stabilization_diagram_for_paper(
        oma_results: Dict[str, Any],
        oma_params: Dict[str, Any],
        fig_ax)-> Tuple[matplotlib.figure.Figure, Tuple[plt.Axes,plt.Axes]]:
    """
    Plot stabilization of OMA data before after pre-cleaning for paper

    Args:
        oma_results (dict): PyOMA results
        oma_params (dict): OMA parameters
    Returns:
        fig_ax (tuple): fig and ax of plot

    """
    if fig_ax is None:
        plt.ion()
        fig, (ax1) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)
    else:
        fig, (ax1) = fig_ax
        ax1.clear()

    #Pre-clean
    frequencies, cov_freq, damping_ratios, cov_damping,_ = remove_highly_uncertain_points(oma_results,oma_params)

    ax1.set_ylabel("Model order", fontsize=20, color = 'black')
    ax1.set_xlabel("Frequency [Hz]", fontsize=20, color = 'black')
    ax1.tick_params(axis='both', which='major', labelsize=17)

    x = frequencies.flatten(order="f")
    y_model_order = np.array([i // len(frequencies) for i in range(len(x))]) * 1

    ax1.scatter(x, y_model_order, marker="o", s=50, c="r")

    if cov_freq is not None:
        xerr = 2*np.sqrt(cov_freq)
        xerr = xerr.flatten(order="f")
        ax1.errorbar(x, y_model_order, xerr=xerr, fmt="None", capsize=5, ecolor="gray")

    ax1.set_ylim(0, oma_params['model_order'] + 1)
    ax1.set_xlim(0, oma_params['Fs']/2)

    # Add major and minor grid lines
    ax1.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax1.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)

    # # # ............................................................................

    if fig_ax is None:
        plt.ion()
        fig, (ax2) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)
    else:
        fig, (ax2) = fig_ax
        ax2.clear()
    ax2.set_ylabel("Damping ratio", fontsize=20, color = 'black')
    ax2.set_xlabel("Frequency [Hz]", fontsize=20, color = 'black')
    ax2.tick_params(axis='both', which='major', labelsize=17)

    x = frequencies.flatten(order="f")
    y = damping_ratios.flatten(order="f")

    ax2.scatter(x, y, marker="o", s=50, c="r")

    if cov_freq is not None:
        xerr = np.sqrt(cov_damping) * 2
        xerr = xerr.flatten(order="f")
        ax2.errorbar(x, y, yerr=xerr, fmt="None", capsize=5, ecolor="gray")

    ax2.set_ylim(0, max(y[~np.isnan(y)])+0.005)
    ax2.set_xlim(0, oma_params['Fs']/2)

    # Add major and minor grid lines
    ax2.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax2.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)

    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, (ax1,ax2)

def plot_clusters_for_paper(clusters: Dict[str,dict],
        oma_params: Dict[str, Any],
        fig_ax)-> Tuple[matplotlib.figure.Figure, Tuple[plt.Axes,plt.Axes]]:
    """
    Plot stabilization of clusters for paper

    Args:
        clsuters (dict): Dictionary of clusters
        oma_results (dict): PyOMA results
        oma_params (dict): OMA parameters
        fix_ax (tuple): fig and ax of plot to redraw
    Returns:
        fig_ax (tuple): fig and ax of plot

    """
    if fig_ax is None:
        plt.ion()
        fig, (ax1) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)
    else:
        fig, (ax1) = fig_ax
        ax1.clear()

    ax1.set_ylabel("Model order", fontsize=20, color = 'black')
    ax1.set_xlabel("Frequency [Hz]", fontsize=20, color = 'black')
    ax1.tick_params(axis='both', which='major', labelsize=17)

    idx = 0
    for i, key in enumerate(clusters.keys()):

        cluster = clusters[key]
        MO = cluster['model_order']
        freq_cluster = cluster['f']
        freq_cov_cluster = cluster['cov_f']

        ax1.scatter(freq_cluster, MO, marker="o", s=50, label=f'Cluster {i+1}')

        xerr_cluster = np.sqrt(freq_cov_cluster) * 2
        ax1.errorbar(freq_cluster, MO, xerr=xerr_cluster,
                     fmt="None", capsize=5, ecolor="gray",zorder=200)
        idx += 1

    ax1.set_ylim(0, oma_params['model_order'] + 1)
    ax1.set_xlim(0, oma_params['Fs']/2)
    # Add major and minor grid lines
    ax1.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax1.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)
    ax1.legend(prop={'size': 20}) #bbox_to_anchor=(0.1, 1.1)

    # # # ............................................................................

    if fig_ax is None:
        plt.ion()
        fig, (ax2) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)

    else:
        fig, (ax2) = fig_ax
        ax2.clear()

    ax2.set_ylabel("Damping ratio", fontsize=20, color = 'black')
    ax2.set_xlabel("Frequency [Hz]", fontsize=20, color = 'black')
    ax2.tick_params(axis='both', which='major', labelsize=17)

    for i, key in enumerate(clusters.keys()):
        cluster = clusters[key]
        freq_cluster = cluster['f']
        damp_cluster = cluster['d']
        damp_cov_cluster = cluster['cov_d']
        xerr = np.sqrt(damp_cov_cluster) * 2
        xerr = xerr.flatten(order="f")

        ax2.scatter(freq_cluster, damp_cluster, s=50, zorder=3,label=f'Cluster {i+1}')
        xerr_cluster = np.sqrt(damp_cov_cluster) * 2
        ax2.errorbar(freq_cluster, damp_cluster, yerr=xerr_cluster,
                     fmt="None", capsize=5, ecolor="gray")

    ax2.set_ylim(0, max(damp_cluster)+0.005)
    ax2.set_xlim(0, oma_params['Fs']/2)
    ax2.legend(prop={'size': 20})

    # Add major and minor grid lines
    ax2.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax2.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)

    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, (ax1,ax2)
