import numpy as np
import matplotlib.pyplot as plt
# pylint: disable=C0103

def plot_spectral_density(y: np.ndarray[float],fs: float) -> None:
    """
    Plot spectral density
    
    Args:
        y (np.ndarray[float]): Data
        fs (float): Sampling frequency (Hz)
    Returns:
    """

    try:
        s, N = y.shape #Reshape y if it is transposed
    except:
        y = y.reshape(-1,1)
        s, N = y.shape
    if N < s:
        y = y.T
        s, N = y.shape

    # Spectrum test
    _, (ax1) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)
    duration = N/fs
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    # Applying FFT
    for ii in range(s):
        fft_result = np.fft.fft(y[ii,:])
        freq = np.fft.fftfreq(t.shape[-1], d=1/fs)

        # Plotting the spectrum
        ax1.plot(freq, np.abs(fft_result),label=str(ii))
        ax1.set_xlabel('Frequency (Hz)')
        ax1.set_ylabel('Amplitude')
        ax1.set_xlim(0,fs/2)
    ax1.legend()
    ax1.set_title("Filtered FFT")
    plt.show(block=False)
