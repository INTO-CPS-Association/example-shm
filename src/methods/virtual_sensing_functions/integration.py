from scipy.fft import fft, ifft
import numpy as np
from numpy.polynomial import Polynomial

def frequency_based_integration(y,params,order = 2):
    
    print("Integration with order:",order)

    ms, N = y.shape
    # Displacement estimation with frequency-domain integration
    if params['output_type'] == 0:
        Disp = y
    else: #If the output type is not displacements apply frequency based integration
        y_ = y - np.mean(y, axis=1, keepdims=True)
        YY = fft(y_.T, axis=0)
        Y = YY.T
        Nh = (N + 1) // 2
        cK = np.arange(1, Nh)
        D = np.zeros_like(Y, dtype=complex)
        omj = 1j * 2 * np.pi * cK * params['Fs'] / N
        
        if params['output_type'] == 1: #Velocity outputs
            D[:, 1:Nh] = Y[:, 1:Nh] / omj
            D[:, Nh:] = np.conj(np.flip(D[:, 1:Nh], axis=1))
        elif params['output_type'] == 2: #Acceleration outputs
            D[:, 1:Nh] = Y[:, 1:Nh] / (omj ** 2)
            D[:, Nh:] = np.conj(np.flip(D[:, 1:Nh], axis=1))
        else:
            raise ValueError('Unknown measurement type - please fix.')

        #Convert from frequency to physical domain
        Disp2 = ifft(D.T, axis=0)
        #print(f"Disp2: {Disp2.shape}")
        x = np.arange(Disp2.shape[0])  # Time indices or sample points
        Disp1 = np.zeros_like(Disp2)  # Initialize the detrended array with the same shape
        for i in range(Disp2.shape[1]):  # Loop over each column (sensor)
            # Fit a second-order polynomial to the data (column-wise)
            poly_coeffs = Polynomial.fit(x, Disp2[:, i], order)
            # Calculate the trend (second-order polynomial evaluated at x)
            trend = poly_coeffs(x)
            # Subtract the trend from the data
            Disp1[:, i] = Disp2[:, i] - trend
        Disp = Disp1.T

    if np.linalg.norm(np.imag(Disp)) > np.linalg.norm(np.real(Disp)) * 1e-8:
        raise ValueError('The displacements are complex-valued - please fix.')
    else:
        Disp = np.real(Disp)
    
    return Disp