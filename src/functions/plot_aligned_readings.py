from re import X
from typing import Tuple, Dict, Any
import time
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.figure
import matplotlib.axes
import matplotlib.animation as animation
plt.rcParams['font.family'] = 'Times New Roman'

def plot_timeseries_1(data: np.ndarray[float], xdata: np.ndarray[float], ydata: np.ndarray[float], timestamp: str, fs: float,
        x_length: int = 20000, fig_ax = None, hold: bool = False)-> Tuple[matplotlib.figure.Figure,
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



def plot_timeseries(data: np.ndarray[float], xdata: np.ndarray[float], ydata: np.ndarray[float], timestamp: str, fs: float,
        fig_ax = None, hold: bool = False, x_length: int = 5000)-> Tuple[matplotlib.figure.Figure,
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

    # print(xdata)
    n = data.shape[1]
    new_xdata = []
    for ii in range(n):
        reversed_ii = (data.shape[1]) - ii - 1
        new_xdata.append(datetime.datetime.fromisoformat(timestamp)-datetime.timedelta(seconds=((1/fs)*reversed_ii))) 
    new_xdata = np.array(new_xdata)
    # print(xdata.shape)
    xdata = np.append(xdata,new_xdata)
    # print(xdata,xdata.shape)
    # print(new_xdata,new_xdata.shape)
    # print(xdata[data.shape[1]-5:data.shape[1]+5])

    ydata = np.hstack((ydata,data))

    if x_length is not None:
            xdata = xdata[-int(x_length):]
            ydata = ydata[:,-int(x_length):]

    if fig_ax is None:
        plt.ion()
        fig, (ax1) = plt.subplots(1,1,figsize=(8, 3), tight_layout=True)
        for y in ydata:
            line = ax1.plot(xdata,y,'-')
    else:
        fig, (ax1) = fig_ax
        lines = ax1.get_lines()
        for ii, y in enumerate(ydata):
            line = lines[ii]
            line.set_ydata(y)
            line.set_xdata(xdata)

    ax1.set_ylim(ydata.min()-abs(ydata.min())*0.05, ydata.max()+abs(ydata.min())*0.05)
    ax1.set_xlim(xdata.min(), xdata.max())
    fig.canvas.draw()
    fig.canvas.flush_events()
    plt.pause(0.0001)
    
    return [fig,(ax1)], xdata, ydata

# def plot_timeseries(data: np.ndarray[float], xdata: np.ndarray[float], ydata: np.ndarray[float], timestamp: str, fs: float,
#         fig_ax = None, hold: bool = False, x_length: int = 5000)-> Tuple[matplotlib.figure.Figure,
#                                Tuple[matplotlib.axes.Axes,matplotlib.axes.Axes]]:
#     """
#     Plot continous timeseries

#     Args:
#         data (np.ndarray[float]): Dictionary of clusters
#         timestamp (str): Timestamp
#         fs (float): Sampling frequency
#         fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]): fig and ax of plot
#         hold (bool): Block show figure
#     Returns:
#         fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]): fig and ax of plot

#     """

#     # def animate(i,xdata,ydata):
        
#     #     try:
#     #         ax1.cla()
#     #         for y in ydata:
#     #             ax1.plot(xdata,y,'-')
            
#     #         print(i)
#     #         # include microseconds (%%f) so labels look like: 2025-11-18 12:34:56.123456
#     #         ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S.%f'))
#     #         xlabel_string = "Time passed [YY:MM:DD HH:MM:SS.MS]"
#     #         # Without microseconds: '%Y-%m-%d %H:%M:%S'
#     #         ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
#     #         xlabel_string = "Time passed [YY:MM:DD HH:MM:SS]"
#     #         ax1.set_xlabel(xlabel_string)
#     #         fig.autofmt_xdate(rotation=15)
#     #         plt.subplots_adjust(bottom=0.15)
#     #         ax1.grid()
#     #     except Exception as e:
#     #         print(f"Error in animation: {e}")

#     if fig_ax is None:
#         plt.ion()
#         fig, (ax1) = plt.subplots(1,1,figsize=(8, 3), tight_layout=True)
#     else:
#         fig, (ax1) = fig_ax
#         lines = ax1.get_lines()
    
#     n = data.shape[1]
#     for ii in range(n):
#         xdata = np.append(xdata,datetime.datetime.fromisoformat(timestamp)+datetime.timedelta(seconds=((1/fs)*ii)))

#     ydata = np.hstack((ydata,data))

#     if x_length is not None:
#             xdata = xdata[-int(x_length):]
#             ydata = ydata[:,-int(x_length):]
#     # _ = animation.FuncAnimation(fig, animate, fargs=(xdata,ydata), cache_frame_data=False)
#     # plt.pause(0.00001)

#     # ax1.draw_artist(ax1.patch)

#     if fig_ax is None:
#         for y in ydata:
#             # line = ax1.plot(xdata,y,'-')
#             line = ax1.plot(y,'-')
#     else:
#         # xlim_low, xlim_high = ax1.get_xlim()
#         # ylim_low, ylim_high = ax1.get_ylim()
#         # # ax1.set_xlim(xlim_low, (xdata.max() + 5))
  
#         for ii, y in enumerate(ydata):
#             line = lines[ii]
#             # print(len(line.get_ydata()),len(y))
#             line.set_ydata(y)
#             # line.set_xdata(xdata)
#             # ax1.draw_artist(line)

#     ax1.set_ylim(ydata.min()*0.95, ydata.max()*1.05)
#     # Without microseconds: '%Y-%m-%d %H:%M:%S'
#     # ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
#     # xlabel_string = "Time passed [YY:MM:DD HH:MM:SS]"
#     # ax1.set_xlabel(xlabel_string)
#     # fig.autofmt_xdate(rotation=15)
#     # # plt.subplots_adjust(bottom=0.15)
#     # plt.grid()

#     # for spine in ax1.spines.values(): 
#     #     ax1.draw_artist(spine)
#     # ax1.draw_artist(ax1.patch)
#     # ax1.draw_artist(ax1.xaxis)
#     # ax1.draw_artist(ax1.yaxis)
#     fig.canvas.draw()
#     fig.canvas.flush_events()
    
#     return [fig,(ax1)], xdata, ydata