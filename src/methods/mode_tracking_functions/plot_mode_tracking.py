from typing import Tuple, Dict, Any
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.axes
plt.rcParams['font.family'] = 'Times New Roman'

def plot_tracked_modes(
        tracked_clusters: Dict[str, Any],
        sysid_params: Dict[str, Any],
        fig_ax: Any = None,
        x_length: int = None)-> Tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]:
    """
    Plot tracked modes

    Args:
        tracked_clusters (Dict[str, Any]): Tracked clusters
        sysid_params (Dict[str, Any]): System identification parameters
        fig_ax (Tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]): fig and ax of plot
        x_length (int): Limit on x axis for tracked modes, default=None.
    Returns:
        fig_ax (Tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]): fig and ax of plot

    """

    if fig_ax is None:
        plt.ion()
        fig, (ax1) = plt.subplots(1,figsize=(8, 6), tight_layout=True)
    else:
        fig, (ax1) = fig_ax
        ax1.clear()

    ii = 0
    max_x = []
    for key in tracked_clusters.keys():
        if key != "iteration":
            tracked_cluster_list = tracked_clusters[key]
            m_f = []
            x = []
            for cluster in tracked_cluster_list:
                m_f.append(cluster['median_f'])
                x.append(cluster['id'])
            sc = ax1.scatter(x, m_f, marker="o", s=50)
            col2 = sc.get_facecolors().tolist()
            ax1.plot(x, m_f, color=col2[0],label="Tracked cluster "+key+", f="+str(f"{np.mean(m_f):.2f}")+" [Hz]")
            max_x.append(max(x))
            ii += 1

    ax1.set_title("Tracked modes over datasets")
    ax1.set_ylabel("Eigenfrequency [Hz]", fontsize=20, color = 'black')
    ax1.set_xlabel("Dataset", fontsize=20, color = 'black')
    ax1.tick_params(axis='both', which='major', labelsize=17)

    ax1.set_ylim(0, sysid_params['Fs']/2)
    if x_length is not None:
        ax1.set_xlim(np.maximum(max(max_x)-x_length,0),max(max_x)+1)
        ax1.set_xticks(np.arange(np.maximum(max(max_x)-x_length,0),
                                 np.maximum(max(max_x)+1,x_length), 5))

    # Add major and minor grid lines
    ax1.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax1.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)

    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, ax1
