import numpy as np
import matplotlib.pyplot as plt

def plot_natural_frquencies(Fn_poles: np.ndarray, fig_ax: tuple = None) -> tuple:
    """
    Plots a Stability Diagram-like scatter plot of natural frequencies vs. model order.

    Args:
        Fn_poles (np.ndarray): 2D array (model_order x mode) of natural frequencies in Hz.
        fig_ax (tuple, optional): (fig, ax) to reuse the same matplotlib figure/axes.

    Returns:
        tuple: (fig, ax) used for plotting, can be reused for live updates.
    """
    if fig_ax is None:
        plt.ion()
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig, ax = fig_ax
        ax.clear()

    num_orders, num_modes = Fn_poles.shape
    model_orders = np.arange(1, num_orders + 1)

    freqs = []
    orders = []

    for i in range(num_orders):
        for j in range(num_modes):
            freq = Fn_poles[i, j]
            if not np.isnan(freq):
                freqs.append(freq)
                orders.append(model_orders[i])

    ax.scatter(freqs, orders, color='black', s=20)
    ax.set_title("Natural Frequencies vs. Model Order")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Model Order")
    ax.grid(True)
    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, ax
