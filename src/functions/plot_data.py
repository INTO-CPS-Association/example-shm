from typing import Tuple
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure


def plot_data(
        data: np.ndarray, fig_ax: Tuple[matplotlib.figure.Figure, plt.Axes]
        ) -> Tuple[matplotlib.figure.Figure, plt.Axes]:
    """
    Extracts aligned sensor data and runs system identification (sysID).

    Args:
        sampling_period: How many minutes of data to pass to sysid.
        aligner: An initialized Aligner object.
        fs: Sampling frequency to use in the OMA algorithm.

    Returns:
        A tuple (OMA_output, timestamp) if successful, or None if data is not ready.
    """
    if fig_ax is None:
        plt.ion()
        fig, ax1 = plt.subplots(figsize=(8, 6), tight_layout=True)
    else:
        fig, ax1 = fig_ax
        ax1.clear()

    for ii,x in enumerate(data):
        ax1.plot(x,label=f"Data: {ii}")
    ax1.legend()
    ax1.grid()

    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, ax1
