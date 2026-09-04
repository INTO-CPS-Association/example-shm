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
        fig, (ax1, ax2) = plt.subplots(1,2,figsize=(12, 6), tight_layout=True)
    else:
        fig, (ax1, ax2) = fig_ax
        ax1.clear()
        ax2.clear()

    
    colors = []
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
            colors.append(col2[0])
    ax1.clear()
    
    np.random.seed(1)
    colors2 = []
    for col in colors:
        if col in colors2:
            col2 = np.random.rand(3,)
            col1 = np.append(col2,[1])
            colors2.append(col1)
        else:
            colors2.append(col)

    ii = 0
    max_x = []
    max_d = 0
    for key in tracked_clusters.keys():
        if key != "iteration":
            tracked_cluster_list = tracked_clusters[key]
            m_f = []
            x = []
            g_freq_err_lower = []
            g_freq_err_upper = []
            damping_ratio = []
            g_damp_err_lower = []
            g_damp_err_upper = []
            for cluster in tracked_cluster_list:
                m_f.append(cluster['median_f'])
                x.append(cluster['id'])
                g_freq_err_lower.append(cluster['median_f']-cluster['global_ci'][0,0])
                g_freq_err_upper.append(cluster['median_f']+cluster['global_ci'][0,0])
                damping_ratio.append(cluster['median_d'])
                g_damp_err_lower.append(cluster['median_d']-cluster['global_ci'][1,1])
                g_damp_err_upper.append(cluster['median_d']+cluster['global_ci'][1,1])
                if cluster['median_d']+cluster['global_ci'][1,1] > max_d:
                    max_d = cluster['median_d']+cluster['global_ci'][1,1]

            ax1.scatter(x, m_f, marker="o", s=50, facecolor=colors2[ii])
            
            ax1.plot(x, m_f, color=colors2[ii],
                     label="Tracked cluster "+key+",f="+str(f"{np.mean(m_f):.2f}")+" [Hz]")
            max_x.append(max(x))

            ax1.fill_between(
                x,
                g_freq_err_lower,
                g_freq_err_upper,
                color=colors2[ii],
                alpha=0.2,
                zorder=100
            )

            sc = ax2.scatter(x, damping_ratio, marker="o", s=50, color=colors2[ii])
            ax2.plot(x, damping_ratio, color=colors2[ii])
            ax2.fill_between(
                x,
                g_damp_err_lower,
                g_damp_err_upper,
                color=colors2[ii],
                alpha=0.2,
                zorder=100
            )

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



    ax2.set_title("Tracked damping over datasets")
    ax2.set_ylabel("Damping ratio [-]", fontsize=20, color = 'black')
    ax2.set_xlabel("Dataset", fontsize=20, color = 'black')
    ax2.tick_params(axis='both', which='major', labelsize=17)

    ax2.set_ylim(0, max_d+0.005)
    if x_length is not None:
        ax2.set_xlim(np.maximum(max(max_x)-x_length,0),max(max_x)+1)
        ax2.set_xticks(np.arange(np.maximum(max(max_x)-x_length,0),
                                 np.maximum(max(max_x)+1,x_length), 5))

    # Add major and minor grid lines
    ax2.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax2.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)


    # ax1.legend()
    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, (ax1, ax2)
