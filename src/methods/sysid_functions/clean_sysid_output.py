from typing import Any, Dict, Tuple
import numpy as np
# pylint: disable=R0914

def extract_from_sysid(sysid_output: Dict[str, Any]) -> Tuple[np.ndarray[float],
                                                                     np.ndarray[float],
                                                                     np.ndarray[float],
                                                                     np.ndarray[float],
                                                                     np.ndarray[float]]:
    """
    Remove complex conjucates
    
    Args:
        sysid_output (Dict[str, Any]): Results from PyOMA-2
        params (Dict[str, Any]): Results from PyOMA-2
    Returns:
        frequencies (np.ndarray[float]): Frequencies (mean)
        std_freq (np.ndarray[float]): Standard deviation of frequency
        damping_ratios (np.ndarray[float]): Damping ratios (mean)
        std_damping (np.ndarray[float]): Standard deviation of damping ratio
        mode_shapes (np.ndarray[float]): Mode shapes
        std_mode_shapes (np.ndarray[float]) : Mode shapes standard deviation
        Ufx_list (np.ndarray[float]): = List of Ufx
    """
    # sysid results as numpy array
    frequencies = sysid_output['Fn_poles'].copy()
    std_freq = sysid_output['Fn_poles_std'].copy()
    damping_ratios = sysid_output['Xi_poles'].copy()
    std_damping = sysid_output['Xi_poles_std'].copy()
    mode_shapes = sysid_output['Phi_poles'].copy()
    std_mode_shapes = sysid_output['Phi_poles_std'].copy()
    Ufx_list = sysid_output['Ufx_list'].copy()

    return frequencies, std_freq, damping_ratios, std_damping, mode_shapes, std_mode_shapes, Ufx_list

def remove_highly_uncertain_points(sysid_output: Dict[str, Any], sysid_params: Dict[str, Any])-> Tuple[np.ndarray[float],
                                                                      np.ndarray[float],
                                                                      np.ndarray[float],
                                                                      np.ndarray[float],
                                                                      np.ndarray[np.complex128],
                                                                      np.ndarray[float]]:
    """
    Remove highly uncertain points
    
    Args:
        sysid_output (Dict[str, Any]): Results from PyOMA-2
        sysid_params (Dict[str, Any]): Parameters
    
    Returns:
        frequencies (np.ndarray): Frequencies (mean)
        std_freq (np.ndarray): Standard deviation of frequency
        damping_ratios (np.ndarray): Damping ratios (mean)
        std_damping (np.ndarray): Standard deviation of damping ratio
        mode_shapes (np.ndarray): Mode shapes
        std_mode_shapes (np.ndarray[float]) : Mode shapes standard deviation
        Ufx_list (np.ndarray[float]): = List of Ufx
    """
    (frequencies, std_freq, damping_ratios, std_damping, mode_shapes,
     std_mode_shapes, Ufx_list) = extract_from_sysid(sysid_output)

    # # #=================== Removing high uncertain poles =======================
    freq_coeff_variance_treshold = sysid_params.get('freq_coeff_variance_treshold', 0.5)
    damp_coeff_variance_treshold = sysid_params.get('damp_coeff_variance_treshold', 0.5)
    frequency_coefficient_variation = std_freq/frequencies
    damping_coefficient_variation = std_damping/damping_ratios
    indices_frequency = frequency_coefficient_variation > freq_coeff_variance_treshold
    indices_damping   = damping_coefficient_variation > damp_coeff_variance_treshold
    above_nyquist = frequencies > sysid_params['Fs']/2
    damping_std_0 = std_damping == 0
    combined_indices = np.logical_or(np.logical_or(indices_frequency,indices_damping),np.logical_or(above_nyquist,damping_std_0))
    frequencies[combined_indices] = np.nan
    damping_ratios[combined_indices] = np.nan
    std_freq[combined_indices] = np.nan
    std_damping[combined_indices] = np.nan
    mask = np.broadcast_to(np.expand_dims(combined_indices, axis=2), mode_shapes.shape)
    mode_shapes[mask] = np.nan
    std_mode_shapes[mask] = np.nan

    combined_indices2 = np.expand_dims(combined_indices, axis=2)
    combined_indices2 = np.repeat(combined_indices2, 2, axis=-1)
    combined_indices3 = np.expand_dims(combined_indices2, axis=3)
    combined_indices3 = np.repeat(combined_indices3, Ufx_list.shape[-1], axis=-1)
    mask = np.broadcast_to(combined_indices3, Ufx_list.shape)
    Ufx_list[mask] = np.nan

    return frequencies, std_freq, damping_ratios, std_damping, mode_shapes, std_mode_shapes, Ufx_list


def transform_sysid_features(frequencies_, std_freq_, damping_ratios_, std_damping_, mode_shapes_,
                            std_mode_shapes_, Ufx_list_) -> Tuple[np.ndarray[float],
                                                                    np.ndarray[float],
                                                                    np.ndarray[float],
                                                                    np.ndarray[float],
                                                                    np.ndarray[np.complex128],
                                                                    np.ndarray[float],
                                                                    np.ndarray[int]]:
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
    The frequency array will then have the shape (6,3). Initially (6,6)
    but the complex conjugates have been removed. So 6 is halved to 3.
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
        frequencies (np.ndarray): Frequencies (mean)
        std_freq (np.ndarray): Standard deviation of frequency
        damping_ratios (np.ndarray): Damping ratios (mean)
        std_damping (np.ndarray): Standard deviation of damping ratio
        mode_shapes (np.ndarray): Mode shapes
        std_mode_shapes (np.ndarray[float]): Mode shapes standard deviation

    Returns:
        frequencies (np.ndarray): Frequencies (mean)
        std_freq (np.ndarray): Standard deviation of frequency
        damping_ratios (np.ndarray): Damping ratios (mean)
        std_damping (np.ndarray): Standard deviation of damping ratio
        mode_shapes (np.ndarray): Mode shapes
        std_mode_shapes (np.ndarray[float]): Mode shapes standard deviation
        Ufx_list2 (np.ndarray[float]): List of Ufx
        model_orders (np.ndarray[int]): Array of model orders
    """

    #Transformation of data
    frequencies = np.transpose(frequencies_)
    frequencies = np.flip(frequencies, 0)
    sort_indices = np.argsort(frequencies,axis=1)
    frequencies = np.take_along_axis(frequencies, sort_indices, axis=1)
    std_freq = np.transpose(std_freq_)
    std_freq = np.flip(std_freq, 0)
    std_freq = np.take_along_axis(std_freq, sort_indices, axis=1)
    damping_ratios = np.transpose(damping_ratios_)
    damping_ratios = np.flip(damping_ratios, 0)
    damping_ratios = np.take_along_axis(damping_ratios, sort_indices, axis=1)
    std_damping = np.transpose(std_damping_)
    std_damping = np.flip(std_damping, 0)
    std_damping = np.take_along_axis(std_damping, sort_indices, axis=1)
    mode_shapes = np.moveaxis(mode_shapes_, [0, 1, 2], [1, 0, 2])
    std_mode_shapes = np.moveaxis(std_mode_shapes_, [0, 1, 2], [1, 0, 2])
    Ufx_list = np.moveaxis(Ufx_list_, [0, 1, 2, 3], [1, 0, 2, 3])

    mode_shapes2 = np.zeros(mode_shapes.shape,dtype=np.complex128)
    std_mode_shapes2 = np.zeros(std_mode_shapes.shape,dtype=np.float64)
    for ii, indices in enumerate(sort_indices):
        mode_shapes2[ii,:,:] = mode_shapes[(sort_indices.shape[0]-ii-1),indices,:]
        std_mode_shapes2[ii,:,:] = std_mode_shapes[(sort_indices.shape[0]-ii-1),indices,:]

    Ufx_list2 = np.zeros(Ufx_list.shape,dtype=np.float64)
    for ii, indices in enumerate(sort_indices):
        Ufx_list2[ii,:,:] = Ufx_list[(sort_indices.shape[0]-ii-1),indices,:,:]
    # Array of model orders
    model_order = np.arange(sort_indices.shape[0])
    model_orders = np.stack((model_order,) * sort_indices.shape[1], axis=1)
    model_orders = np.flip(model_orders)

    return frequencies, std_freq, damping_ratios, std_damping, mode_shapes2, std_mode_shapes2, Ufx_list2, model_orders

def clean_and_transform(sysid_output: Dict[str, Any], sysid_params: Dict[str, Any]) -> Tuple[np.ndarray[float],
                                                                      np.ndarray[float],
                                                                      np.ndarray[float],
                                                                      np.ndarray[float],
                                                                      np.ndarray[np.complex128],
                                                                      np.ndarray[float],
                                                                      np.ndarray[int]]:
    """
    Clean and transform sysid output from PyOMA
    Args:
        sysid_output (Dict[str, Any]): Results from PyOMA-2
        sysid_params (Dict[str, Any]): Parameters
    
    Returns:
        frequencies (np.ndarray): Frequencies (mean)
        std_freq (np.ndarray): Standard deviation of frequency
        damping_ratios (np.ndarray): Damping ratios (mean)
        std_damping (np.ndarray): Standard deviation of damping ratio
        mode_shapes (np.ndarray): Mode shapes
        std_mode_shapes (np.ndarray[float]): Mode shapes standard deviation
        model_orders (np.ndarray[int]): Array of model orders
    """

    (frequencies_, std_freq_, damping_ratios_, std_damping_, mode_shapes_, 
     std_mode_shapes_, Ufx_list_) = remove_highly_uncertain_points(sysid_output, sysid_params)

    (frequencies, std_freq, damping_ratios, std_damping, mode_shapes2, std_mode_shapes2,
     Ufx_list, model_orders) = transform_sysid_features(frequencies_, std_freq_, damping_ratios_, 
                                              std_damping_, mode_shapes_,  std_mode_shapes_, Ufx_list_)

    return frequencies, std_freq, damping_ratios, std_damping, mode_shapes2, std_mode_shapes2, Ufx_list, model_orders