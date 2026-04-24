from typing import Tuple
import matplotlib.pyplot as plt
import numpy as np

def plot_stress(data: np.ndarray, elements: list, s: int, fig_ax: Tuple = None, title: str = None) -> None: 
    """
    Plot vitrual sensing results
    Args:
        data (np.ndarray): stress/forces
        elements (list): List of elements to plot
        s (int): What force/stress to plot 0, 1 or 2 for 2D beam
        fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]):
        title_str (str): string for title
    Returns:
        None
    Plots:
        Stress plot

    """
    if fig_ax is None:
        plt.ion()
        fig, ax1 = plt.subplots(1,1,figsize=(6, 6), tight_layout=True)
    else:
        fig, ax1 = fig_ax

    for element in elements:
        ax1.plot(data[element,s], label=("Element" + str(element)+"s=",s))
    
    ax1.legend()
    if title is not None:
        ax1.set_ylabel(title)
    ax1.set_xlabel("Sample [-]")
    
    plt.show(block=True)
    
    return fig, ax1