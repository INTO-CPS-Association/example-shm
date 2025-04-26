import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from typing import Optional, Tuple, List, Dict


def plot_natural_frequencies(
    Fn_poles: np.ndarray,
    freqlim: Optional[Tuple[float, float]] = None,
    fig_ax: Optional[Tuple] = None
) -> Tuple:
    """
    Plots a stabilization diagram with optional frequency range filtering.

    Args:
        Fn_poles (np.ndarray): 2D array [model_order x mode] of natural frequencies.
        freqlim (tuple, optional): (f_min, f_max) frequency range to plot.
        fig_ax (tuple, optional): Reuse (fig, ax) for interactive updates.

    Returns:
        (fig, ax): The matplotlib figure and axes used for plotting.
    """
    if fig_ax is None:
        plt.ion()
        fig, ax = plt.subplots(figsize=(8, 5))
    else:
        fig, ax = fig_ax
        ax.clear()

    num_orders, num_modes = Fn_poles.shape
    freqs, orders = [], []
    for i in range(num_orders):
        for j in range(num_modes):
            freq = Fn_poles[i, j]
            if not np.isnan(freq):
                model_order = num_orders - i  
                if freqlim is None or (freqlim[0] <= freq <= freqlim[1]):
                    freqs.append(freq)
                    orders.append(model_order)

    ax.scatter(freqs, orders, color='red', s=10)

    ax.set_title("Stabilization Diagram")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Model order")
    ax.set_ylim(0, num_orders + 1)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.grid(True)

    if freqlim:
        ax.set_xlim(freqlim)
    else:
        ax.set_xlim(0, max(freqs) * 1.05)

    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, ax
