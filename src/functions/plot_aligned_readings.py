from typing import Tuple
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.axes
# pylint: disable=C0103, W0603, R0913, R0914, R0915, R0917
plt.rcParams['font.family'] = 'Times New Roman'

def plot_timeseries(data: np.ndarray[float], xdata: np.ndarray[float], ydata: np.ndarray[float],
        x_length: int = 20000, fig_ax = None)-> Tuple[matplotlib.figure.Figure,
                               Tuple[matplotlib.axes.Axes,matplotlib.axes.Axes]]:
    """
    Plot continous timeseries

    Args:
        data (np.ndarray[float]): Dictionary of clusters
        timestamp (str): Timestamp
        fs (float): Sampling frequency
        fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]): fig and ax of plot
        hold (bool): Block show figure
    Returns:
        fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]): fig and ax of plot

    """

    N = data.shape[1]
    ydata = np.hstack((ydata,data))
    xdata2 = np.arange(int(max(xdata))+1,int(max(xdata))+1+N)
    xdata = np.hstack((xdata,xdata2))

    if x_length is not None:
        if ydata.shape[1] > x_length:
            ydata = ydata[:,int(xdata.shape[0]-x_length):]
            xdata = xdata[int(xdata.shape[0]-x_length):]

    if fig_ax is None:
        plt.ion()
        fig, (ax1) = plt.subplots(1,1,figsize=(8, 3), tight_layout=True)
        for ii, y in enumerate(ydata):
            line = ax1.plot(xdata,y,'-',label="data "+ str(ii))
    else:
        fig, (ax1) = fig_ax
        lines = ax1.get_lines()
        for ii, y in enumerate(ydata):
            line = lines[ii]
            line.set_ydata(y)
            line.set_xdata(xdata)

    ax1.set_ylim(ydata.min()-abs(ydata.min())*0.05, ydata.max()+abs(ydata.min())*0.05)
    ax1.set_xlim(xdata.min(), xdata.max())
    ax1.legend()
    fig.canvas.draw()
    fig.canvas.flush_events()
    plt.pause(0.0001)

    return [fig,(ax1)], xdata, ydata
