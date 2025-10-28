from typing import Tuple, Dict, Any
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure
from functions.clean_sysid_output import (remove_complex_conjugates,remove_highly_uncertain_points)
plt.rcParams['font.family'] = 'Times New Roman'


def plot_pre_stabilization_diagram(
        sysid_results: Dict[str, Any],
        sysid_params: Dict[str, Any],
        fig_ax)-> Tuple[matplotlib.figure.Figure, Tuple[plt.Axes,plt.Axes]]:

    """
    Plot stabilization of raw sysid data before pre-cleaning

    Args:
        sysid_results (dict): Pyoma results
        sysid_params (dict): sysid parameters
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

    frequencies, damping_ratios, cov_freq, cov_damping, _ = remove_complex_conjugates(sysid_results)

    x = frequencies.flatten(order="f")
    y_model_order = np.array([i // len(frequencies) for i in range(len(x))]) * 1

    ax1 = add_scatter_data(ax1,x,y_model_order,cov_freq,error_dir="h")
    ax1 = add_plot_standard_flair(ax1,sysid_params)

    ax1.set_ylabel("Model order", fontsize=20, color = 'black')
    ax1.set_ylim(0, sysid_params['model_order'] + 1)

    # # # ............................................................................

    x = frequencies.flatten(order="f")
    y = damping_ratios.flatten(order="f")

    ax2 = add_scatter_data(ax2,x,y,cov_damping,error_dir="v")
    ax2 = add_plot_annotation(ax2,x,y,y_model_order)
    ax2 = add_plot_standard_flair(ax2,sysid_params)

    ax2.set_ylabel("Damping ratio", fontsize=20, color = 'black')
    ax2.set_ylim(0, max(y[~np.isnan(y)])+0.005)

    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, (ax1,ax2)


def plot_stabilization_diagram(
        sysid_results: Dict[str, Any],
        sysid_params: Dict[str, Any],
        fig_ax)-> Tuple[matplotlib.figure.Figure, Tuple[plt.Axes,plt.Axes]]:
    """
    Plot stabilization of sysid data before after pre-cleaning

    Args:
        sysid_results (dict): PyOMA results
        sysid_params (dict): sysid parameters
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
    frequencies, cov_freq, damping_ratios, cov_damping, _ = remove_highly_uncertain_points(sysid_results,sysid_params)

    x = frequencies.flatten(order="f")
    y_model_order = np.array([i // len(frequencies) for i in range(len(x))]) * 1

    ax1 = add_scatter_data(ax1,x,y_model_order,cov_freq,error_dir="h")
    ax1 = add_plot_standard_flair(ax1,sysid_params)

    ax1.set_ylabel("Model order", fontsize=20, color = 'black')
    ax1.set_ylim(0, sysid_params['model_order'] + 1)

    # # # ............................................................................

    x = frequencies.flatten(order="f")
    y = damping_ratios.flatten(order="f")

    ax2 = add_scatter_data(ax2,x,y,cov_damping,error_dir="v")
    ax2 = add_plot_annotation(ax2,x,y,y_model_order)
    ax2 = add_plot_standard_flair(ax2,sysid_params)

    ax2.set_ylabel("Damping ratio", fontsize=20, color = 'black')
    ax2.set_ylim(0, max(y[~np.isnan(y)])+0.005)

    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, (ax1,ax2)


def add_scatter_data(ax,x,y,cov,error_dir,mark="o",lab='Non clustered',size=50):
    ax.scatter(x, y, marker=mark, s=size, c="r", label = lab)
    if cov is not None:
        xerr = np.sqrt(cov) * 2
        xerr = xerr.flatten(order="f")
        if error_dir == "h":
            ax.errorbar(x, y, xerr=xerr, fmt="None", capsize=5, ecolor="gray")
        else:
            ax.errorbar(x, y, yerr=xerr, fmt="None", capsize=5, ecolor="gray")
    return ax

def add_plot_standard_flair(ax,sysid_params):
    ax.set_xlabel("Frequency [Hz]", fontsize=20, color = 'black')
    ax.tick_params(axis='both', which='major', labelsize=17)

    ax.set_xlim(0, sysid_params['Fs']/2)

    # Add major and minor grid lines
    ax.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)

    return ax

def add_plot_annotation(ax,x,y,y_model_order):
    for i, txt in enumerate(y_model_order):
        ax.annotate(str(txt), (x[i], y[i]))
    return ax
