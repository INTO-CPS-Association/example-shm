import numpy as np
import matplotlib.pyplot as plt

def plot_spectral_density(y,N,params):
    # Spectrum test
    fig1, (ax1) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)
    fs = params['Fs']  # Sampling frequency (Hz)
    duration = N/256
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    # Applying FFT
    for ii, y_data in enumerate(y[:,0]):
        fft_result = np.fft.fft(y[ii,:])
        freq = np.fft.fftfreq(t.shape[-1], d=1/fs)

        # Plotting the spectrum
        ax1.plot(freq, np.abs(fft_result))
        ax1.set_xlabel('Frequency (Hz)')
        ax1.set_ylabel('Amplitude')
        ax1.set_xlim(0,fs/2)
    ax1.legend(["acc1,node7","acc2,node6","acc3,node5","acc4,node4"])
    ax1.set_title("Filtered FFT")
    plt.show(block=False)