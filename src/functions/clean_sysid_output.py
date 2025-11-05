import numpy as np

def remove_complex_conjugates(sysid_output):
    """
    Remove complex conjucates
    
    Args:
        sysid_output (Dict[str, Any]): Results from Pysysid-2
    
    Returns:
        frequencies (np.ndarray): Frequencies (mean)
        cov_freq (np.ndarray): Covariance of frequency
        damping_ratios (np.ndarray): Damping ratios (mean)
        cov_damping (np.ndarray): Covariance of damping ratio
        mode_shapes (np.ndarray): Mode shapes
    """
    sysid = sysid_output.copy()
    # sysid results as numpy array
    frequencies = sysid['Fn_poles'].copy()
    cov_freq    = sysid['Fn_poles_cov'].copy()
    damping_ratios = sysid['Xi_poles'].copy()
    cov_damping    = sysid['Xi_poles_cov'].copy()
    mode_shapes = sysid['Phi_poles'].copy()

    # Remove the complex conjugate entries
    frequencies = frequencies[::2]              # This is 'S' as per algorithm
    damping_ratios = damping_ratios[::2]        # This is 'S' as per algorithm
    mode_shapes = mode_shapes[::2, :, :]
    cov_freq = cov_freq[::2]           
    cov_damping = cov_damping[::2]

    return frequencies, cov_freq, damping_ratios, cov_damping, mode_shapes

def transform_sysid_features(frequencies_,cov_freq_,damping_ratios_,cov_damping_,mode_shapes_):
    """
    Transform sysid results

    Transpose, flip and sort arrays, such that arrays maps directly to the stabilization diagram.
    This means the the frequency array maps directly to the plot:
    MO.
    5.| x    x     
    4.| x          
    3.| x          
    2.|      x
    1.|
    0.|
       -1----4------- Frequency
    The frequency array will then have the shape (6,3). Initially (6,6) but the complex conjugates have been removed. So 6 is halved to 3.
    6 for each model order, including 0 and 3 for maximum poles in a modelorder
    The frequency array will then become:
      _0_1_
    0| 1 4
    1| 1 Nan
    0| 1 Nan
    0| Nan 4
    0| Nan Nan
    0| Nan Nan
    
    Args:
        frequencies_ (np.ndarray): Frequencies (mean)
        cov_freq_ (np.ndarray): Covariance of frequency
        damping_ratios_ (np.ndarray): Damping ratios (mean)
        cov_damping_ (np.ndarray): Covariance of damping ratio
        mode_shapes_ (np.ndarray): Mode shapes
    
    Returns:
        frequencies (np.ndarray): Frequencies (mean)
        cov_freq (np.ndarray): Covariance of frequency
        damping_ratios (np.ndarray): Damping ratios (mean)
        cov_damping (np.ndarray): Covariance of damping ratio
        mode_shapes (np.ndarray): Mode shapes
    """

    #Transformation of data
    frequencies = np.transpose(frequencies_)
    frequencies = np.flip(frequencies, 0)
    sort_indices = np.argsort(frequencies,axis=1)
    frequencies = np.take_along_axis(frequencies, sort_indices, axis=1)
    cov_freq = np.transpose(cov_freq_)
    cov_freq = np.flip(cov_freq, 0)
    cov_freq = np.take_along_axis(cov_freq, sort_indices, axis=1)
    damping_ratios = np.transpose(damping_ratios_)
    damping_ratios = np.flip(damping_ratios, 0)
    damping_ratios = np.take_along_axis(damping_ratios, sort_indices, axis=1)
    cov_damping = np.transpose(cov_damping_)
    cov_damping = np.flip(cov_damping, 0)
    cov_damping = np.take_along_axis(cov_damping, sort_indices, axis=1)
    mode_shapes = np.moveaxis(mode_shapes_, [0, 1, 2], [1, 0, 2])
    
    mode_shapes2 = np.zeros(mode_shapes.shape,dtype=np.complex128)
    for ii, indices in enumerate(sort_indices):
        mode_shapes2[ii,:,:] = mode_shapes[(sort_indices.shape[0]-ii-1),indices,:]

    # Array of model orders
    model_order = np.arange(sort_indices.shape[0])
    model_orders = np.stack((model_order,) * sort_indices.shape[1], axis=1)
    model_orders = np.flip(model_orders)

    return frequencies, cov_freq, damping_ratios, cov_damping, mode_shapes2, model_orders

def remove_highly_uncertain_points(sysid_output,sysid_params):
    """
    Remove highly uncertain points
    
    Args:
        sysid_output (Dict[str, Any]): Results from Pysysid-2
        sysid_params (Dict[str, Any]): Parameters
    
    Returns:
        frequencies (np.ndarray): Frequencies (mean)
        cov_freq (np.ndarray): Covariance of frequency
        damping_ratios (np.ndarray): Damping ratios (mean)
        cov_damping (np.ndarray): Covariance of damping ratio
        mode_shapes (np.ndarray): Mode shapes
    """
    frequencies, cov_freq, damping_ratios, cov_damping, mode_shapes = remove_complex_conjugates(sysid_output)

    # # #=================== Removing high uncertain poles =======================
    freq_variance_treshold = sysid_params.get('freq_variance_treshold', 0.1)
    damp_variance_treshold = sysid_params.get('damp_variance_treshold', 10**6)
    frequency_coefficient_variation = np.sqrt(cov_freq)/frequencies
    damping_coefficient_variation = np.sqrt(cov_damping)/damping_ratios
    indices_frequency = frequency_coefficient_variation > freq_variance_treshold
    indices_damping   = damping_coefficient_variation > damp_variance_treshold
    above_nyquist = frequencies > sysid_params['Fs']/2
    combined_indices = np.logical_or(np.logical_or(indices_frequency,indices_damping),above_nyquist)
    frequencies[combined_indices] = np.nan
    damping_ratios[combined_indices] = np.nan
    cov_freq[combined_indices] = np.nan
    cov_damping[combined_indices] = np.nan
    mask = np.broadcast_to(np.expand_dims(combined_indices, axis=2), mode_shapes.shape)
    mode_shapes[mask] = np.nan

    return frequencies, cov_freq, damping_ratios, cov_damping, mode_shapes