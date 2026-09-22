from typing import Tuple, Dict, Any
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure
plt.rcParams['font.family'] = 'Times New Roman'

def plot_tracked_modes(
        tracked_clusters: Dict[str, Any],
        oma_params: Dict[str, Any],
        x_length: int = None,
        fig_ax: Any = None)-> Tuple[matplotlib.figure.Figure, Tuple[plt.Axes,plt.Axes]]:
    """
    Plot tracked modes

    Args:
        oma_results (dict): PyOMA results
        oma_params (dict): OMA parameters
    Returns:
        fig_ax (tuple): fig and ax of plot

    """

    xdata = []
    ydata = []
    if fig_ax is None:
        plt.ion()
        fig, (ax1) = plt.subplots(1,figsize=(6, 4), tight_layout=True)
        col = None
    else:
        fig, (ax1) = fig_ax
        # lines = ax1.get_lines()
        # col = []
        # for l in lines:
        #     col.append(l.get_color())
        ax1.clear()

    ii = 0
    max_x = []
    for key in tracked_clusters.keys():
        if key == "iteration":
            pass
        else:
            tracked_cluster_list = tracked_clusters[key]
            m_f = []
            x = []
            for cluster in tracked_cluster_list:
                m_f.append(cluster['median_f'])
                x.append(cluster['id']+1)

            # print(ii,"What cluster is plotting",np.mean(m_f))
            # if (col is not None) and (ii < len(col)):
            #     sc = ax1.scatter(x, m_f, marker="o", s=50, c=col[ii])
            #     breakpoint()
            # else:
            #     sc = ax1.scatter(x, m_f, marker="o", s=50)
            # col2 = sc.get_facecolors().tolist()
            # ax1.plot(x, m_f, color=col2[0])

            sc = ax1.scatter(x, m_f, marker="o", s=50)
            col2 = sc.get_facecolors().tolist()
            ax1.plot(x, m_f, color=col2[0])
            max_x.append(max(x))
            ii += 1

    ax1.set_ylabel("Eigenfrequency [Hz]", fontsize=20, color = 'black')
    ax1.set_xlabel("Dataset", fontsize=20, color = 'black')
    ax1.tick_params(axis='both', which='major', labelsize=17)

    ax1.set_ylim(0, oma_params['Fs']/2)
    if x_length is not None:
        ax1.set_xlim(np.maximum(max(max_x)-x_length,0),max(max_x)+1)
        ax1.set_xticks(np.arange(np.maximum(max(max_x)-x_length,0), np.maximum(max(max_x)+1,x_length), 5))
    # else:
    #     ax1.set_xticks(np.arange(0, np.maximum(max(max_x)+1,20), 5))
    

    # Add major and minor grid lines
    ax1.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax1.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)

    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, (ax1)