from typing import Optional, Any, NoReturn
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.dates as mdates
from mpl_toolkits.axes_grid1 import make_axes_locatable
from methods.fatigue_functions.bin_functions import (bin_func, bin_func2D)
from methods.fatigue_functions.EOF_RUL import eof_rul
# pylint: disable=C0103, C0301, R0912, R0913, R0914, R0915, R0917, W3301, W1401

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.sans-serif'] = 'cm'
plt.rcParams['mathtext.fontset'] = 'cm'
plt.rcParams["font.family"] = "Times New Roman"


def plot_sn_curve(sn_curve: dict[str, Any], result: dict[str, Any],
                  hist_data: dict[str, Any] = None, fig_ax = None,**kwargs
                  ) -> tuple[matplotlib.figure.Figure, dict[str,Any]]:
    """Plot SN curve

    Args:
        sn_curve (dict): Dictionary consisting of SN curve parameters
        result (dict): Dictionary of results from continous data stream
    **kwargs (Any)
        - hist_type (str): "bar" (default), "line" or "spectrum"
        - title (str): Title to plot
        - bin_width (int): Width of the bins default=10
        - hist_data (dict):  Previous histogram data, should be applied together with stress_list and n_count, supply hist_data = {} if is not known
        - bins (int): Number of bins to use, not recomended for continuous updating histogram
        - fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]): figure and axis from matplotlib

    Returns
        fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]): figure and axis from matplotlib
        hist_data (dict): Histogram data for next iteration

    """


    hist_type = kwargs.get("hist_type","bar")
    title_string = kwargs.get("title","S-N curve")

    stress_list_1 = result["stress_res"]
    stress_list_2 = result["stress_res_residual"]
    stress_list_ = stress_list_1+stress_list_2

    # For plotting with residual part together with previous hist
    hist_tot, bin_edges = bin_func(stress_list_, hist_data,**kwargs)

    #For next plot, without residual data
    hist_next, bin_edges_next = bin_func(stress_list_1, hist_data,**kwargs)

    #Clear previous figure
    if fig_ax is None:
        plt.ion()
        fig, ax = plt.subplots(1,1,figsize=(6, 6), tight_layout=True)
    else:
        fig, ax = fig_ax
        ax.clear()

    xlim2 = 10**9
    m = sn_curve['m'].copy()
    m = [m[0]] + m #Dubplicate first value
    n_d = sn_curve['N_D']
    c = sn_curve['C'].copy()
    c = [c[0]] + c #Dubplicate first value
    yy = []
    if n_d[0] == 0:
        xx = [1] + [xlim2]
    else:
        xx = [1] + n_d + [xlim2]
    for ii,x in enumerate(xx):
        if m[ii] == 0: #Run-off
            yy = yy + [yy[-1]] #Duplicate last point
        else:
            yy.append((c[ii]/x)**(1/m[ii])) #Calculate stress value

    #Plotting S-N curve
    ax.loglog(xx, yy,color=(0.1,0.1,0.1),linewidth=3,label="S-N curve")
    ax.grid(color=(0.4,0.4,0.4), linestyle='-', linewidth=0.5, which="major")
    ax.grid(color=(0.8,0.8,0.8), linestyle='-', linewidth=0.5, which="minor")

    #Plotting histgram
    bin_edges = bin_edges.tolist()
    hist = hist_tot.tolist()
    if hist_type == "spectrum":
        hist.reverse()
        bin_edges.reverse()
        hist = [0] + hist #Start hist from 0
        hist = np.add.accumulate(hist) #Make an acummulated list of hist
        hist = hist.tolist()
        #Stress spectrum or cumulative frequency distribution
        ax.stairs(bin_edges[0:-1],hist,fill=True,
                    color=(0.05,0.03,0.53),label="Stress spectrum")
    elif hist_type == "line":
        bin_edges = bin_edges[1:]
        hist = [1] + hist + [1]
        bin_edges = [1] + bin_edges + [bin_edges[-1]]
        #Stress histogram as line
        ax.loglog(hist,bin_edges,marker=".",color=(0.05,0.03,0.53)
                    ,linewidth=2,label="Stress histogram")
    else:
        bin_edges_new = [val for val in bin_edges for _ in (0, 1)]
        hist_new = [val for val in hist for _ in (0, 1)]
        hist_new = [0.01] + hist_new + [0.01]
        #Stress histogram
        ax.loglog(hist_new,bin_edges_new,color=(0.05,0.03,0.53),linewidth=2,
                    label="Stress histogram")
        y = [0.1]*len(hist_new)
        ax.fill_between(hist_new,y,bin_edges_new,color=(0.05,0.03,0.53))

    ax.set(ylim = (1,max(max(bin_edges)*2,1000)), xlim=(1,xlim2))
    ax.set(ylim = (1,10000), xlim=(1,10**8))

    d_t = result["D_t"]
    ax.text(5*10**6, 1.8, "$D_{\mathrm{tot}}$ = "+ f"{float(d_t):.3e}", size=13, rotation=0.,
    ha="center", va="center",
    bbox={"boxstyle": "Square",
            "ec": (1., 0.5, 0.5),
            "fc": (1., 0.8, 0.8)
            } #ec edge color, fc face color
    )

    ax.set_title(title_string)
    ax.set(xlabel = "Fatigue life, N [cycles]",
           ylabel = r'Stress range, $\Delta\hat{\sigma}_R$ [MPa]')
    ax.legend()
    plt.subplots_adjust(bottom=0.15)

    fig.canvas.draw()
    fig.canvas.flush_events()

    hist_data = {
                "hist":hist_next,
                "bin_edges":[bin_edges_next]
            }
    return (fig, ax), hist_data

def sn_curve_plotdata(sn_curve: dict[str, Any], result: dict[str, Any], hist_prev,**kwargs
                    ) -> tuple[list[float], list[float], list[float], list[float], dict[str,Any]]:
    """Plot SN curve

    Args
        sn_curve (dict): Dictionary consisting of SN curve parameters
        result (dict): Dictionary of results from continous data stream
        hist_prev (dict):  Previous histogram data
    **kwargs (Any)
        - hist_type (str): "bar" (default) or "spectrum"
        - bin_width (float): Width of the bins default=10
        - bins (int): Number of bins to use, not recomended for continuous updating histogram

    Returns:
        x_curve (list(float)): S-N curve data for x-axis
        y_curve (list(float)): S-N curve data for y-axis
        x_points (list(float)): Histogram data for x-axis
        y_points (list(float)): Histogram data for y-axis
        hist_data (dict): Histogram data for next iteration
    """

    #SN-curve
    xlim2 = 10**9
    m = sn_curve['m'].copy()
    m = [m[0]] + m #Dubplicate first value
    n_d = sn_curve['N_D']
    c = sn_curve['C'].copy()
    c = [c[0]] + c #Dubplicate first value
    yy = []
    if n_d[0] == 0:
        xx = [1] + [xlim2]
    else:
        xx = [1] + n_d + [xlim2]
    for ii,x in enumerate(xx):
        if m[ii] == 0: #Run-off
            yy = yy + [yy[-1]] #Duplicate last point
        else:
            yy.append((c[ii]/x)**(1/m[ii])) #Calculate stress value
    x_curve = xx
    y_curve = yy

    #Histgram
    hist_type = kwargs.get("hist_type","bar")

    stress_list_1 = result["stress_res"]
    stress_list_2 = result["stress_res_residual"]
    stress_list_ = stress_list_1+stress_list_2

    #For plotting with residual part together with previous hist
    hist_tot, bin_edges = bin_func(stress_list_,hist_prev,**kwargs)
    #For next plot, without residual data
    hist_next, bin_edges_next = bin_func(stress_list_1,hist_prev,**kwargs)

    bin_edges = bin_edges.tolist()
    hist = hist_tot.tolist()
    if hist_type == "spectrum":
        hist.reverse()
        bin_edges.reverse()
        hist = [0] + hist #Start hist from 0
        hist = np.add.accumulate(hist).tolist() #Make an acummulated list of hist

        y_points = [val for val in bin_edges for _ in (0, 1)]
        x_points = [val for val in hist for _ in (0, 1)]
        y_points.pop(-1)
        x_points.pop(0)
    else: #histogram
        y_points = [val for val in bin_edges for _ in (0, 1)]
        hist_new = [val for val in hist for _ in (0, 1)]
        x_points = [1] + hist_new + [1]
    hist_data = {
        "hist":hist_next,
        "bin_edges":[bin_edges_next]
    }

    return x_curve, y_curve, x_points, y_points, hist_data

def plot_histogram(result: dict[str, Any], fig_ax = None, hist_data: dict[str,Any] = None,
                   **kwargs: Optional[Any]) -> tuple[matplotlib.figure.Figure, dict[str,Any]]:
    """Bin the given stress list
    Optionally save a histogram

    Args:
        result (dict): Dictionary of results from continous data stream
        fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]): fig and ax of plot
        hist_data (dict): Previous histogram data, should be applied together with stress_list and n_count
        **kwargs    :   n_counts, list of int
            Counts of stress ranges
        **kwargs    :   s_mean, list of float
            List of stress means for 3D plot
        **kwargs    :   binwidth, int
            Use ad fixed width for bins
        **kwargs    :   title_string, str
            String for title name
        **kwargs    :   colormap, str
            Name of a valid colormap, default=plasma


    Outputs
    ----------
    fig     :   object
        figure object
    ax      :   object
        axes object
    """

    stress_list_1 = result["stress"]
    # n_count_1 = result["n_rain"]
    stress_list_2 = result["stress_residual"]
    # n_count_2 = result["n_rain_residual"]
    stress_list_ = stress_list_1+stress_list_2

    s_mean_1 = result["mean_rain"]
    s_mean_2 = result["mean_rain_residual"]
    s_mean_ = s_mean_1 + s_mean_2

    #Clear old figure
    if fig_ax is None:
        plt.ion()
        fig, ax = plt.subplots(1,1,figsize=(6, 6), tight_layout=True)
    else:
        fig, ax, cax, ax_histx, ax_histy = fig_ax
        # ax = fig.get_axes()[0]
        # cax = fig.get_axes()[1]
        # ax_histx = fig.get_axes()[2]
        # ax_histy = fig.get_axes()[3]
        ax.clear()
        cax.remove()
        ax_histx.remove()
        ax_histy.remove()

    static_mean = kwargs.get("static_mean",0)
    #For this plot
    xx = stress_list_
    yy = [x + static_mean for x in s_mean_]
    #For next plot
    xx1 = stress_list_1
    yy1 = [x + static_mean for x in s_mean_1]

    #Histogram data and bins
    #For plotting with residual part together with previous hist
    hist, x_edges, y_edges = bin_func2D(xx,yy,hist_data,**kwargs)
    #For next iteration
    hist_next, x_edges_next, y_edges_next = bin_func2D(xx1,yy1,hist_data,**kwargs)

    #Save for next plot
    hist_data = {
        "hist":hist_next,
        "bin_edges":[x_edges_next,y_edges_next]
    }


    #Plotting heatmap
    map_user = kwargs.get("colormap","plasma")
    extent = [x_edges[0],x_edges[-1],y_edges[0],y_edges[-1]]
    im = ax.imshow(hist,extent=extent,cmap=map_user, aspect='auto')

    ax.set_xticks(x_edges[::2])
    ax.set_yticks(y_edges[::2])
    ax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False, labelsize=8)
    ax.tick_params(right=True, labelright=True, left=False, labelleft=False, labelsize=8)
    ax.set_xticklabels(ax.get_xticklabels(), rotation='vertical', ha='center')
    ax.set_yticklabels(ax.get_yticklabels())
    title_string = kwargs.get('title_string',"Heatmap")
    ax.set_title(title_string,x=0.5,y=-0.15)
    ax.grid()


    # create new Axes on the right and on the top of the current Axes
    divider = make_axes_locatable(ax)

    #Colorbar
    cax = divider.append_axes('left', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical',location="left",label="Frequency")

    #Histogram plots
    char_x = len(str(max(x_edges)))
    char_y = max(len(str(min(y_edges))),len(str(max(y_edges))))
    ax_histx = divider.append_axes("top", 1.2, pad=0.08*char_x, sharex=ax)
    ax_histy = divider.append_axes("right", 1.2, pad=0.08*char_y, sharey=ax)
    # make some labels invisible
    ax_histx.xaxis.set_tick_params(labelbottom=False)
    ax_histy.yaxis.set_tick_params(labelleft=False)
    #Summing up
    x_hist = np.sum(hist,axis=0)
    y_hist = np.sum(hist,axis=1)
    #Histograms/stairs
    ax_histx.stairs(x_hist, x_edges,fill=True,color=(0.05,0.03,0.53))
    ax_histy.stairs(np.flip(y_hist), y_edges,fill=True,
                    orientation='horizontal',color=(0.05,0.03,0.53))
    ax_histx.grid()
    ax_histy.grid()
    ax_histx.set_title("Stress range histogram")
    ax_histy.set_title("Mean stress hisogram",x=1.2,y=0,rotation=270)
    ax_histy.set_xlabel("Frequency",rotation="horizontal")
    ax_histx.set_ylabel("Frequency",rotation="vertical")

    plt.subplots_adjust(bottom=0.15)

    fig.canvas.draw()
    fig.canvas.flush_events()

    return (fig, ax, cax, ax_histx, ax_histy), hist_data

def heatmap_data(hist2d_prev, result: dict[str, Any], **kwargs: Optional[Any]
                 ) -> tuple[np.ndarray, list[float], list[float], np.ndarray]:
    """Bin the given stress list
    Optionally save a histogram

    Parameters
    ----------
    hist2d_prev    :    2D list of flaot
        Previous histogram count, should be applied together with stress_list and n_count
    result  : dict
        Dictionary of results from continous data stream
    **kwargs    :   bin_width, int
        Width of the bins default=10
    **kwargs    :   xbin_width, int
        Override width of the x bins default (only if yy is present)
    **kwargs    :   ybin_width, int
        Override width of the y bins default (only if yy is present)
    **kwargs    :   xbins, int
        Override number of x bins to use, not recomended for continuous updating histogram
    **kwargs    :   ybins, int
        Override number of y bins to use, not recomended for continuous updating histogram
    **kwargs    :   bins, int
        Override number of x bins to use, not recomended for continuous updating histogram   
    


    Outputs
    ----------
    hist2d  :   2D list of float
        Heatmap z/height data
    x_edges :   list of float
        list of edges
    y_edges :   list of float
        list of edges
    hist2D_next :   2D list of float
        Heatmap z/height data for next iteration
    """
    stress_list_1 = result["stress"]
    stress_list_2 = result["stress_residual"]
    stress_list_ = stress_list_1+stress_list_2

    s_mean_1 = result["mean_rain"]
    s_mean_2 = result["mean_rain_residual"]
    s_mean_ = s_mean_1 + s_mean_2

    #For this plot
    xx = stress_list_
    yy = s_mean_
    #For next plot
    xx1 = stress_list_1
    yy1 = s_mean_1

    #Histogram data and bins
    #For plotting with residual part together with previous hist
    hist2d, x_edges, y_edges = bin_func2D(xx,hist2d_prev,yy,**kwargs)
    #For next iteration
    hist_next, x_edges_next, y_edges_next = bin_func2D(xx1,hist2d_prev,yy1,**kwargs)

    x_hist_next = np.sum(hist2d,axis=0)
    y_hist_next = np.sum(hist2d,axis=1)

    #Save for next plot
    hist2d_next = {
        "hist":hist_next,
        "bin_edges":[x_edges_next,y_edges_next],
        "hist1D":[x_hist_next,y_hist_next]
    }

    return hist2d, x_edges, y_edges, hist2d_next

def plot_damage(result: dict[str, Any], fig_ax = None,
                **kwargs: Optional[Any]) -> matplotlib.figure.Figure:
    """Plot PM damage in a running graph

    Args:
        result (dict): Dictionary of results from continous data stream
        fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]): fig and ax of plot
        **kwargs    :   title, str
            Title to plot
        **kwargs    :   y_max_lim, int
            How many samples for the running graph

    Returns
        fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]): fig and ax of plot
    """

    #Calculate damage
    d = result["D"]
    d_res = result["D_residual"]

    #Get plot data from previous figure
    if fig_ax is None:
        plt.ion()
        fig, ax = plt.subplots(1,1,figsize=(6, 6), tight_layout=True)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width, box.height*0.87])

        x = [0]
        y1 = [d+d_res]
        y2 = [d]
    else:
        fig, ax = fig_ax
        line1 = ax.get_lines()[0]
        line2 = ax.get_lines()[1]
        xdata = line1.get_xdata().tolist()
        ydata = line1.get_ydata().tolist()
        y2data = line2.get_ydata().tolist()
        # plt.figure(fig)
        ax.clear()

        x = xdata + [xdata[-1]+1]
        y1 = ydata + [result["D_t"]]
        y2 = y2data + [d]

    #Plotting
    y_length = kwargs.get("y_max_lim",60)
    if x[-1] > y_length:
        x = x[-(y_length+1):]
        y1 = y1[-(y_length+1):]
        y2 = y2[-(y_length+1):]

    ax.plot(x,y1,label="Total damage",color="k",linewidth=2)
    ax.plot(x,y2,label="Instant damage",color=(0.05,0.03,0.53))
    ax.set(xlabel="Sample",ylabel="PM damage",
           xlim=(max(max(x)-y_length,0), max(max(x),y_length)),yscale="log")
    ylim_min = min(y2)
    ax.set_ylim(ylim_min,10**1)
    ax.grid(color=(0.4,0.4,0.4), linestyle='-', linewidth=0.5, which="major")
    ax.grid(color=(0.8,0.8,0.8), linestyle='-', linewidth=0.5, which="minor")
    ax.get_xaxis().get_major_formatter().labelOnlyBase = False
    ax.legend(loc="upper center",bbox_to_anchor=(0.37, 1.2),ncol=2)
    title_string = kwargs.get("title","Palmgreen-Miner damage")
    ax.set_title(title_string, x=0.5, y=1.2)
    damage_text = (f"$D_t$ = {float(y1[-1]):.3e} \n"
                    f"$D_i$ = {float(y2[-1]):.3e} ")

    ax.text(0.89, 1.1, damage_text, size=11,
            ha="center", va="center", transform = ax.transAxes,
            bbox={'boxstyle':"Square",
                    'ec':(1., 0.5, 0.5),
                    'fc':(1., 0.8, 0.8)
                    }
            )

    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, ax

def plot_cld(sn_curve: dict[str, Any],s_y,s_u,result: dict[str, Any],
             fig_ax = None,**kwargs: Optional[Any]) -> matplotlib.figure.Figure:
    """Plot Haigh diagram with Goodman line.
    Also called a constant life diagram (CLD)

    Args
        S_d (int): Fatigue strength at zero mean stress, R = -1, N=10**6
        s_y (int): Yield strength
        s_u (int): Ultimate tensile strength
        result (dict): Dictionary of results from continous data stream
        fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]): fig and ax of plot
    **kwargs:
        title (str): Title to plot
        points (int): Maximum points to display
    
    Returns:
        fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]): fig and ax of plot
    """

    #Get plot data from previous figure
    if fig_ax is None:
        plt.ion()
        fig, ax = plt.subplots(1,1,figsize=(6, 6), tight_layout=True)
        prev_data = []
    else:
        fig, ax = fig_ax
        line = ax.collections[0]
        prev_data = line.get_offsets()
        ax.clear()

    n_d = sn_curve["N_D"]
    c = sn_curve["C"]
    m = sn_curve["m"]
    s_d = (c[-1]/n_d[-1])**(1/m[-1])

    x_yield = [-s_y,0,s_y]
    y_yield = [0,s_y,0]

    x_intersect_r = (s_d*1.4)/np.tan((2*np.pi)/360*45)
    x_r = [-x_intersect_r,0,x_intersect_r]
    y_r = [s_d*1.4,0,s_d*1.4]

    x_r1 = [0, 0]
    y_r1 = [0, s_y*1.25]


    ax.plot(x_yield,y_yield,linewidth=0.6,color=(0.5,0.5,0.5))
    ax.plot(x_r,y_r,linewidth=1,color="k",linestyle='dashed')
    ax.plot(x_r1,y_r1,linewidth=1,color="k",linestyle='dashed')
    title_string = kwargs.get("title","Haigh diagram")
    ax.set(xlabel = "Mean stress, $σ_m$ [MPa]",
           ylabel = 'Allowable stress amplitude, $σ_R$ [MPa]',
           title=title_string)

    x_intersect = (s_y-s_d)/np.tan((2*np.pi)/360*45)
    ax.plot([-x_intersect,0,s_u],[s_d,s_d,0],color=(0.55,0.4,0.2),
            linewidth=2,label="Modified Goodman")
    #ax.plot([-145,0,s_u],[S_d,S_d,0],color=(0.5,0.4,0.2),linewidth=2,label="Gerber")
    ax.text(s_y/2**(1/2)+10, s_y/2**(1/2)+10, "R=0", size=11, ha="center", va="center")
    ax.text(-s_y/2**(1/2)-10, s_y/2**(1/2)+10, "R=-∞", size=11, ha="center", va="center")
    ax.text(0, s_y*1.25+10, "R=-1", size=11, ha="center", va="center")

    stress = result["stress"] #Stress range
    stress_amplitude = [x/2 for x in stress]
    mean_list = result["mean_rain"]

    if len(prev_data) != 0:
        for x in (prev_data):
            mean_list.append(x[0])
            stress_amplitude.append(x[1])

    points = kwargs.get("points",200)
    if len(mean_list) > points:
        mean_list = mean_list[:points]
        stress_amplitude = stress_amplitude[:points]

    ax.scatter(mean_list,stress_amplitude,color="b",label="Stresses",alpha=0.1)

    ax.legend()
    ax.set_xlim(min((-s_y*1.2),min(mean_list)),max((s_u*1.2),max(mean_list)))
    ax.set_ylim(0,max((s_y*1.5),max(stress_amplitude)))
    ax.set_aspect('equal', 'box')

    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, ax

def plot_rainflow(data: dict[str, Any] ,dt: Optional[float] = 1) -> NoReturn:
    """ Plot rainflow counting
    Args
        data (dict): Dictionary of results from continous data stream
        dt (float): Float determining the time between each action (speed of visualization)
    Returns:
    
    """
    plt.ion()
    fig, ax = plt.subplots(1,1,figsize=(6, 6), tight_layout=True)
    titles = ["Original","Removing repeating values","Removing intermediate values","Counting"]
    x_lim = len(data["0"])


    def line_intersection(line1, line2):
        xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
        ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

        def det(a, b):
            return a[0] * b[1] - a[1] * b[0]

        div = det(xdiff, ydiff)
        if div == 0:
            raise Exception('lines do not intersect')

        d = (det(*line1), det(*line2))
        x = det(d, xdiff) / div
        y = det(d, ydiff) / div
        return x, y

    for ii,x in enumerate(data.keys()):
        ax.clear()
        ax.plot(data[x], marker = "o", color="k", zorder=1)
        if ii >= 3:
            x_lim = len(data[x])
        removed = []
        if ii < len(data.keys())-1:
            for id2 in range(len(data[str(ii+1)])):
                if data[str(ii+1)][id2] != data[str(ii)][id2]:
                    removed = [float(data[str(ii)][id2]), float(data[str(ii)][id2+1])]
                    removed_id = [id2,id2+1]
                    break
            if removed:
                if removed[0] > removed[1]:
                    xx = removed_id + [removed_id[1]+1]
                    y1 = removed + [removed[0]]
                    y2 = [max(removed)]*3

                    a = (xx[0],max(removed))
                    b = (xx[2],max(removed))
                    line1 = (a,b)

                    a = (xx[1],y1[1])
                    b = (xx[2],float(data[str(ii)][removed_id[1]+1]))
                    line2 = (a,b)
                    x_c,_ = line_intersection(line1,line2)

                    xx[2] = x_c
                    ax.plot(xx,y1,color="r",marker="o", zorder=2)
                    ax.plot(xx,y2,color="r", zorder=2)
                    ax.fill_between(xx,y1,y2,color="r", alpha=0.3)
                else:
                    xx = [removed_id[0]-1] + removed_id
                    y1 = [removed[1]] + removed
                    y2 = [max(removed)]*3

                    a = (xx[0],max(removed))
                    b = (xx[2],max(removed))
                    line1 = (a,b)

                    a = (xx[1],y1[1])
                    b = (xx[0],float(data[str(ii)][removed_id[0]-1]))
                    line2 = (a,b)
                    x_c,_ = line_intersection(line1,line2)

                    xx[0] = x_c

                    ax.plot(xx,y1,color="r",marker="o", zorder=2)
                    ax.plot(xx,y2,color="r", zorder=2)
                    ax.fill_between(xx,y1,y2,color="r", alpha=0.3)


        if ii < 3:
            ax.set_title(titles[ii])
        else:
            ax.set_title(titles[3])
        ax.grid()
        ax.set_xlim(0,x_lim)
        plt.pause(dt)

    plt.close(fig)

def plot_eol_rul(result: dict[str, Any], inital_time: datetime,
                 current_time: datetime, output_time_unit: Optional[str] = "hrs",
                 damage_sum: Optional[float] = 1,
                 x_length: Optional[int] = None, fig_ax = None) -> matplotlib.figure.Figure:
    """Plot end-of-life and remaining-useful-life diagram

    Args
        result (dict): Dictionary of results from continous data stream
        initial time (datetime): Datetime of starting time reference
        current time (datetime): Datetime of now
        output_time_unit (str): String determining the output format "years", "days", "hrs"
        damage_sum (float): Palmgren miner damage sum at failure
        x_length (int): Integer determining the length of a running plot
        fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]): fig and ax of plot

    Returns:
        fig_ax (Tuple[plt.Figure, Tuple[plt.Axes]]): fig and ax of plot
    """

    #Get plot data from previous figure
    if fig_ax is None:
        plt.ion()
        fig, (ax1) = plt.subplots(1,1,figsize=(6, 6), tight_layout=True)
        xdata_eol = []
        ydata_eol = []
        xdata_rul = []
        ydata_rul = []
    else:
        fig, ax1 = fig_ax
        line1 = ax1.lines[0]
        xdata_eol = line1.get_xdata().tolist()
        ydata_eol = line1.get_ydata().tolist()

        # ax2 = fig.get_axes()[0]
        line2 = ax1.lines[1]
        xdata_rul = line2.get_xdata().tolist()
        ydata_rul = line2.get_ydata().tolist()
        ax1.clear()

        if x_length is not None:
            xdata_eol = xdata_eol[-x_length:]
            ydata_eol = ydata_eol[-x_length:]
            xdata_rul = xdata_rul[-x_length:]
            ydata_rul = ydata_rul[-x_length:]
        # ax2.clear()

    time_passed = current_time - inital_time
    eol, rul = eof_rul(result,time_passed,output_time_unit,damage_sum=damage_sum)

    xdata_eol = xdata_eol + [current_time]
    ydata_eol = ydata_eol + [eol]

    xdata_rul = xdata_rul + [current_time]
    ydata_rul = ydata_rul + [rul]


    plt.xticks(rotation=45)
    ax1.plot(xdata_eol,ydata_eol,'*-',label="EOL",zorder=0)
    #ax1.set_title("End Of Life (EOF) and Remaining Useful Life (RUL)")
    ax1.set_ylabel("EOL ["+output_time_unit+"]")
    ax1.set_xlabel("Time passed")
    #ax1.set_xticklabels(ax1.get_xticks(),rotation=45)

    ax1.plot(xdata_rul,ydata_rul,c="r",label="RUL",zorder=3)
    ax1.set_ylabel("EOL and RUL ["+output_time_unit+"]")

    if output_time_unit == "years":
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        xlabel_string = "Time passed [YY:MM:DD]"
    elif output_time_unit == "days":
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        xlabel_string = "Time passed [MM:DD HH:mm]"
    elif output_time_unit == "hrs":
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H-%M'))
        xlabel_string = "Time passed [HH:mm]"
    else:
        xlabel_string = "Time passed [cycles]"
    ax1.set_xlabel(xlabel_string)
    fig.autofmt_xdate()
    plt.subplots_adjust(bottom=0.15)
    ax1.grid()
    ax1.legend()
    #ax2.set_xticklabels(ax2.get_xticks(),rotation=45)

    damage_text = "$D_{\mathrm{tot}}$ = " + f"{float(result['D_t']):.3e}"

    ax1.text(0.5, 0.925, damage_text, size=13,
            ha="center", va="center", transform = ax1.transAxes,
            bbox={'boxstyle':"Square",
                    'ec':(1., 0.5, 0.5),
                    'fc':(1., 0.8, 0.8)
                    }
            )

    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, ax1
