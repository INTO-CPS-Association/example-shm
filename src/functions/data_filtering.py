from scipy import signal
import numpy as np

def filter(data,params) -> np.ndarray[float]:
    """

    """

    y = data
    ms, N = y.shape #Reshape y if it is transposed
    if N < ms:
        y = y.T

    # Band-pass filtering of data
    try:
        filter_order = params.get('filter_order', 4)
        filter_type = params.get('filter_type', 'bandpass')
        filter_cut_off = params.get('filter_cut-off', np.array([0,10**6]))
        if filter_type is not None:
            sos = signal.butter(filter_order, filter_cut_off, filter_type, analog=False, fs = params['Fs'], output='sos')
            y = signal.sosfilt(sos, y)
            
    except Exception as e:
            print(f"Unexpected error: {e}")
    
    if N < ms:
        y = y.T

    return y
