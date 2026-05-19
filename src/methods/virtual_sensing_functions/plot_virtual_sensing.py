from typing import Tuple
import matplotlib.pyplot as plt
import numpy as np

# pylint: disable=C0103

def plot_virtual_sensing(data: np.ndarray[float], DOFs: list[int],
                         fig_ax: Tuple = None, title: (str) = None) -> None:
    """
    Plot virtual sensing results
    Args:
        data (np.ndarray):
        DOFs (list): List of DOFs to plot
        fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]):
        title (str): string for title
    Returns:
        fig_ax (Tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]): fig and ax of plot
    Plots:

    """
    if fig_ax is None:
        plt.ion()
        fig, ax1 = plt.subplots(1,1,figsize=(6, 6), tight_layout=True)
    else:
        fig, ax1 = fig_ax

    dof, N = data.shape #Reshape y if it is transposed
    if N < dof:
        data = data.T

    for dof in DOFs:
        ax1.plot(data[dof,:], label="DOF" + str(dof))

    ax1.legend()
    if title is not None:
        ax1.set_ylabel(title)
    ax1.set_xlabel("Sample [-]")

    return fig, ax1
