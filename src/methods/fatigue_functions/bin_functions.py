from typing import Any, Optional
import numpy as np 

def bin_func(xx: list[float], hist_data: dict[str, Any], **kwargs: Optional[Any]) -> tuple[list[int], list[float]]:
    """Plot SN curve

    Args:
    xx (List(float)): Stress list
    hist_data (dict): Previous histogram data. First iteration hist = {}
        -'hist' (List(int)): Previus histogram data
        -'bin_edges' (List(float)): Previus bin edges
    yy (List(float)): mean stress list, default = []
    **kwargs (any):
        - bin_width (int): Width of the bins default=10
        - bins (int): Override number of x bins to use, not recomended for continuous updating histogram

    Returns:
    hist (List(float)): Next histogram data
    x_edges (List(float): Next bin edges
    """
    
    def align_hist1D(xx: list[float], hist_prev: list[float], bins_prev: list[float], **kwargs: Optional[Any]) -> tuple[np.ndarray, list[float]]:
        """Aligns 1D histograms, such that they can be added together correctly

        Parameters
        ----------
        xx :   list of float
            Stress list
        hist_prev   :   array of int
            Previous histogram
        bins_prev  :   array of float
            Previous bin edges
        **kwargs    :   bin_width, int
            Width of the bins default=10
        **kwargs    :   bins, int
            Override number of x bins to use, not recomended for continuous updating histogram

        Outputs
        ----------
        hist        :   array
            New histogram
        bin_edges  :   Array of float
            bin edges
            
        """
        
        try:
            bin_width = kwargs.get("bin_width",10) #Get bin width if supplied
            rem1 = max(xx) % bin_width #Remainder
            rem2 = min(xx) % bin_width #Remainder
            nbins = ((max(xx)+bin_width-rem1-(min(xx)-rem2))//bin_width) #Calculate number of bins
            nbins = kwargs.get("bins",nbins) #Get number of bins if supplied, and override nbins

            #Find new histogram
            hist_new, bins_new = np.histogram(xx,bins=round(nbins),range=(round(min(xx)-rem2,2),round(max(xx)+bin_width-rem1,2))) #Histogram
            if (bins_new[1]-bins_new[0]) != bin_width:
                hist_new, bins_new = np.histogram(xx,bins=round(nbins+1),range=(round(min(xx)-rem2,2),round(max(xx)+bin_width-rem1,2))) #Histogram

            #If the previous histogram does not exist
            if np.sum(hist_prev) == [0]:
                hist_prev = np.array([0]*len(hist_new))
                bins_prev = bins_new

            #Aligning by adding zeros around the arrays
            binwidth = round(bins_new[1]-bins_new[0],2)
            if min(bins_new) < min(bins_prev):
                diff = round((min(bins_prev)-min(bins_new))/binwidth)
                hist_prev = np.concatenate((np.zeros(diff),hist_prev))
            elif min(bins_new) > min(bins_prev):
                diff = round((min(bins_new)-min(bins_prev))/binwidth)
                hist_new = np.concatenate((np.zeros(diff),hist_new))
            
            if max(bins_new) < max(bins_prev):
                diff = round((max(bins_prev)-max(bins_new))/binwidth)
                hist_new = np.concatenate((hist_new,np.zeros(diff)))
            elif max(bins_new) > max(bins_prev):
                diff = round((max(bins_new)-max(bins_prev))/binwidth)
                hist_prev = np.concatenate((hist_prev,np.zeros(diff)))

            nbins = round((max(max(bins_new),max(bins_prev))-min(min(bins_new),min(bins_prev))) / (bins_new[1]-bins_new[0]) + 1)

            bin_edges = np.linspace(min(min(bins_new),min(bins_prev)),max(max(bins_new),max(bins_prev)),nbins)
            hist = np.add(hist_new,hist_prev) #Add hist counts together

            return hist.astype(dtype=np.int64), bin_edges
        except RuntimeError as e:
            print("binfunc Debug info", e)
            print(hist_prev)
            print(hist_new)
            print(len(hist_new),len(hist_prev))
            print(bins_prev)
            print(bins_new)
            print(len(bins_new),len(bins_prev))
            print(binwidth)
            print(diff)
    
    try:
        hist_prev = hist_data["hist"]
        bins_prev = hist_data["bin_edges"]
        
    except:
        hist_prev = np.zeros((1,1))
        bins_prev = [[],[]]

    #Align data
    hist, edges = align_hist1D(xx,hist_prev,bins_prev[0],**kwargs)
    
    return hist, edges
    
def bin_func2D(xx: list[float], hist_data: dict[str,any],
                yy: list[float], **kwargs: Optional[Any]) -> tuple[np.ndarray, list[float], list[float]]:
    """Plot SN curve

    Args:
    xx (List(float): Stress list
    hist_data (dict): Previous histogram data. First iteration hist = {}
        -'hist' (List(List(float))): Previus histogram data
        -'bin_edges' (List(float)): Previus bin edges
    yy (List(float): mean stress list, default = []
    **kwargs (any):
        - bin_width (int): Width of the bins default=10
        - xbin_width (int): Override width of the x bins default
        - ybin_width (int): Override width of the y bins default
        - xbins (int): Override number of x bins to use, not recomended for continuous updating histogram
        - ybins (int): Override number of y bins to use, not recomended for continuous updating histogram
        - bins (int): Override number of x bins to use, not recomended for continuous updating histogram

    Returns:
    hist (List(List(float))): Next histogram data
    x_edges (List(float): Next bin edges
    y_edges (List(float): Optional
    """
    def align_hist2D(xx: list[float], yy: list[float],
                        hist_prev: np.ndarray, xbins_prev: list[float],
                        ybins_prev: list[float], **kwargs: Optional[Any]) -> tuple[np.ndarray, list[float], list[float]]:
        """Aligns 2D histograms, such that they can be added together correctly

        Parameters
        ----------
        xx :   list of float
            Stress list
        yy  :   list of float
            mean stress list
        hist_prev   :   array2D of int
            Previous histogram
        xbins_prev  :   array of float
            Previous x bin edges
        ybins_prev  :   array of float
            Previous y bin edges
        **kwargs    :   bin_width, int
            Width of the bins default=10
        **kwargs    :   xbin_width, int
            Override width of the x bins default
        **kwargs    :   ybin_width, int
            Override width of the y bins default
        **kwargs    :   xbins, int
            Override number of x bins to use, not recomended for continuous updating histogram
        **kwargs    :   ybins, int
            Override number of y bins to use, not recomended for continuous updating histogram

        Outputs
        ----------
        hist        :   array2D of int
            Histogram
        xbin_edges  :   Array of float
            x bin edges
        ybin_edges  :   Array of float
            y bin edges
            
        """
        bin_width = kwargs.get("bin_width",10) #Get bin width if supplied
        lim_bin_width = 0.01
        if bin_width < lim_bin_width:
            print(f"Bin width can't be less than {lim_bin_width}. Going forth with bin_width = {lim_bin_width}")
            bin_width = lim_bin_width
        elif round(bin_width,2) != bin_width:
            bin_width = round(bin_width,2)
            print("Bin width can't have a precision less than 0.0. Going forth with bin_width =",bin_width)
        xbin_width = kwargs.get("xbin_width",bin_width) #Get bin width if supplied
        if xbin_width < lim_bin_width:
            print(f"x-bin width can't be less than {lim_bin_width}. Going forth with xbin_width = {lim_bin_width}")
            xbin_width = lim_bin_width
        elif round(xbin_width,2) != xbin_width:
            xbin_width = round(xbin_width,2)
            print("x-bin width can't have a precision less than 0.01. Going forth with xbin_width =",xbin_width)
        ybin_width = kwargs.get("ybin_width",bin_width) #Get bin width if supplied
        if ybin_width < lim_bin_width:
            print(f"y-bin width can't be less than {lim_bin_width}. Going forth with ybin_width = {lim_bin_width}")
            ybin_width = lim_bin_width
        elif round(ybin_width,2) != ybin_width:
            ybin_width = round(ybin_width,2)
            print("y-bin width can't have a precision less than 0.01. Going forth with ybin_width =",ybin_width)
        
        nbins_x = np.ceil(max(xx)/xbin_width) #Calculate number of bins
        nbins_x = kwargs.get("xbins",nbins_x) #Get number of bins if supplied, and override nbins
        nbins_y = (np.ceil(max(yy)/ybin_width)-np.floor(min(yy)/ybin_width)) #Calculate number of bins
        nbins_y = kwargs.get("ybins",nbins_y) #Get number of bins if supplied, and override nbins

        
        rem = max(xx) % xbin_width #Remainder
        rem2 = min(yy) % ybin_width #Remainder
        rem3 = max(yy) % ybin_width #Remainder

        #Find new histrogram
        hist_new, xbins_new, ybins_new = np.histogram2d(xx,yy,bins=(round(nbins_x),round(nbins_y)),range=((0,round(max(xx)+bin_width-rem,2)),(round(min(yy)-rem2,2),round(max(yy)+bin_width-rem3,2)))) #Histogram
        hist_new = np.transpose(hist_new)
        #If the previous histogram does not exist
        if np.sum(hist_prev) == [0]:
            hist_prev = np.zeros((hist_new.shape))
            xbins_prev = xbins_new
            ybins_prev = ybins_new
        

        xbinwidth = round(xbins_new[1]-xbins_new[0],2)
        ybinwidth = round(ybins_new[1]-ybins_new[0],2)

        #Aligning by adding zeros around the matricies
        try:
            if min(xbins_new) > min(xbins_prev):
                diff = round((min(xbins_new)-min(xbins_prev))/xbinwidth)
                hist_new = np.hstack((np.zeros((hist_new.shape[0],diff)),hist_new))
            elif min(xbins_new) < min(xbins_prev):
                diff = round((min(xbins_prev)-min(xbins_new))/xbinwidth)
                hist_prev = np.hstack((np.zeros((hist_prev.shape[0],diff)),hist_prev))
            
            if min(ybins_new) > min(ybins_prev):
                diff = round((min(ybins_new)-min(ybins_prev))/ybinwidth)
                hist_new = np.vstack((hist_new,np.zeros((diff,hist_new.shape[1]))))
            elif min(ybins_new) < min(ybins_prev):
                diff = round((min(ybins_prev)-min(ybins_new))/ybinwidth)
                hist_prev = np.vstack((hist_prev,np.zeros((diff,hist_prev.shape[1]))))
            
            if max(xbins_new) < max(xbins_prev):
                diff = round((max(xbins_prev)-max(xbins_new))/xbinwidth)
                hist_new = np.hstack((hist_new,np.zeros((hist_new.shape[0],diff))))
            elif max(xbins_new) > max(xbins_prev):
                diff = round((max(xbins_new)-max(xbins_prev))/xbinwidth)
                hist_prev = np.hstack((hist_prev,np.zeros((hist_prev.shape[0],diff))))

            if max(ybins_new) < max(ybins_prev):
                diff = round((max(ybins_prev)-max(ybins_new))/ybinwidth)
                hist_new = np.vstack((np.zeros((diff,hist_new.shape[1])),hist_new))
            elif max(ybins_new) > max(ybins_prev):
                diff = round((max(ybins_new)-max(ybins_prev))/ybinwidth)
                hist_prev = np.vstack((np.zeros((diff,hist_prev.shape[1])),hist_prev))

            #Added hisogram and bin edges
            hist = np.add(hist_new,hist_prev.astype(dtype=np.float64)) #Add hist counts together
        except RuntimeError as e:
            print("problem",e)
            breakpoint()
        nbins_x = hist.shape[1]
        nbins_y = hist.shape[0]
        xbin_edges = np.linspace(0,max(max(xbins_new),max(xbins_prev)),round(nbins_x)+1)
        ybin_edges = np.linspace(min(min(ybins_new),min(ybins_prev)),max(max(ybins_new),max(ybins_prev)),round(nbins_y)+1)
        

        return hist.astype(dtype=np.int64), xbin_edges, ybin_edges

    try:
        hist_prev = hist_data["hist"]
        bins_prev = hist_data["bin_edges"]
        
    except:
        hist_prev = np.zeros((1,1))
        bins_prev = [[],[]]

    #Align data
    hist, x_edges, y_edges = align_hist2D(xx,yy,hist_prev,bins_prev[0],bins_prev[1],**kwargs)
    
    return hist, x_edges, y_edges
