from scipy import signal
import numpy as np
from typing import Dict, Any

def signal_filter(data: np.ndarray[float], params: Dict[str,Any]) -> np.ndarray[float]:
    """
    Apply a butter filter to the input data array.

    Args:
        data (np.ndarray[float]): Input NumPy array containing the signal data to filter.
        params (params: Dict[str,Any]): Dictionary of filter parameters. Expected keys are:
            - 'Fs' (required): Sampling frequency used by 'scipy.signal.butter'.
            - 'filter_order' (optional): Filter order. Defaults to '4'.
            - 'filter_type' (optional): Filter type passed to 'scipy.signal.butter'
              (for example 'bandpass'). Defaults to 'bandpass'. If set to
              'None', filtering is skipped.
            - 'filter_cut-off' (optional): Cutoff frequency or frequencies passed to
              'scipy.signal.butter'. Defaults to 'np.array([0, 10**6])'.
    Returns:
        The filtered NumPy array, preserving the original orientation of ``data``.
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
            raise RuntimeError("Unexpected error in signal filtering") from e
    
    if N < ms:
        y = y.T

    return y
