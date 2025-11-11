from typing import Tuple, Dict, Any, List
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure
plt.rcParams['font.family'] = 'Times New Roman'

def plot_parameters(model_parameters: Dict[str, Any],
                    pars_to_update: List[str],
        fig_ax = None)-> Tuple[matplotlib.figure.Figure, Tuple[plt.Axes,plt.Axes]]:
    """
    Plot stabilization of clusters

    Args:
        model_parameters (Dict[str,Any]): Model parameters (YaFEM)
        parameters_to_update (np.ndarray[str]): String of keys to update in model_parameters
        fix_ax (tuple): fig and ax of plot to redraw
    Returns:
        fig_ax (tuple): fig and ax of plot

    """
    n_pars = len(pars_to_update)
    prev_data_x = []
    prev_data_y = []

    if fig_ax is None:
        plt.ion()
        fig, axes = plt.subplots(n_pars,1,figsize=(6, n_pars*2), tight_layout=True)
    else:
        fig, axes = fig_ax
        for ax in axes:
            line1 = ax.lines[0]
            xdata = line1.get_xdata().tolist()
            ydata = line1.get_ydata().tolist()
            prev_data_x.append(xdata)
            prev_data_y.append(ydata)
            ax.clear()

    for ii, ax in enumerate(axes):
        if fig_ax is not None:
            xdata = prev_data_x[ii]
            ydata = prev_data_y[ii]
            xdata.append(xdata[-1]+1)
        else:
            ydata = []
            xdata = [1]
        
        ydata.append(model_parameters[pars_to_update[ii]])
        ax.plot(xdata,ydata,'*-',color="k")
        ax.set_ylabel(pars_to_update[ii])
        ax.set_xlabel('Dataset [-]')

    fig.canvas.draw()
    fig.canvas.flush_events()
    return fig, axes



def plot_model_frequencies(omegaM: np.ndarray,
        fig_ax = None)-> Tuple[matplotlib.figure.Figure, Tuple[plt.Axes,plt.Axes]]:
    """
    Plot updated model frequencies

    Args:
        omegaM (np.ndarray): array of model eigenfrequencies
        fix_ax (tuple): fig and ax of plot to redraw
    Returns:
        fig_ax (tuple): fig and ax of plot

    """

    if fig_ax is None:
        plt.ion()
        fig, ax1 = plt.subplots(1,1,figsize=(6, 4), tight_layout=True)
        ydata = omegaM
        xdata = [1]
    else:
        ydata_prev = []
        fig, ax1 = fig_ax
        line1 = ax1.lines[0]
        xdata_prev = line1.get_xdata().tolist()
        for line in ax1.lines:
            ydata_prev.append(line.get_ydata())
        ax1.clear()

        xdata = np.hstack((xdata_prev,np.array(xdata_prev[-1])+1))
        ydata = np.hstack((np.asarray(ydata_prev),np.reshape(omegaM, (-1, 1))))
    
    for ii in range(len(omegaM)):
        ax1.plot(xdata,ydata[ii],'*-')
    ax1.set_ylabel("Model eigenfrequencies [Hz]")
    ax1.set_xlabel('Dataset [-]')

    fig.canvas.draw()
    fig.canvas.flush_events()
    return fig, ax1