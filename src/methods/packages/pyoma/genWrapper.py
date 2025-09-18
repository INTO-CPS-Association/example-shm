import logging
import typing

import numpy as np

logger = logging.getLogger(__name__)



def applymask(list_arr, mask, len_phi) -> typing.List[np.ndarray]:
    """
    Apply a mask to a list of arrays, filtering their values based on the mask.

    Parameters
    ----------
    list_arr : list of np.ndarray
        List of arrays to be filtered. Arrays can be 2D or 3D.
    mask : np.ndarray
        2D boolean array indicating which values to keep (True) or set to NaN (False).
    len_phi : int
        The length of the mode shape dimension for expanding the mask to 3D.

    Returns
    -------
    list of np.ndarray
        List of filtered arrays with the same shapes as the input arrays.

    Notes
    -----
    - If an array in `list_arr` is 3D, the mask is expanded to 3D and applied.
    - If an array in `list_arr` is 2D, the original mask is applied directly.
    - Values not matching the mask are set to NaN.
    """
    # Expand the mask to 3D by adding a new axis (for mode shape)
    expandedmask1 = np.expand_dims(mask, axis=-1)
    # Repeat the mask along the new dimension
    expandedmask1 = np.repeat(expandedmask1, len_phi, axis=-1)
    list_filt_arr = []
    for arr in list_arr:
        if arr is None:
            list_filt_arr.append(None)
        elif arr.ndim == 3:
            list_filt_arr.append(np.where(expandedmask1, arr, np.nan))
        elif arr.ndim == 2:
            list_filt_arr.append(np.where(mask, arr, np.nan))
    return list_filt_arr




def HC_realEigen(Lambds) -> typing.Tuple[np.ndarray, np.ndarray]:
    """
    Apply Hard validation Criteria (HC), retaining only those elements which are negetive real part in eingenvalues.

    Parameters
    ----------
    Lambds : np.ndarray
        Array of eigenvalues.

    Returns
    -------
    filt_lambd : np.ndarray
        Array of the same shape as `Lambds` with elements that do not satisfy the condition set to NaN.
    mask : np.ndarray
        Boolean array of the same shape as `Lambds`, where True indicates that the element is with negetive real part of eigenvalues.

    """
    mask = (np.real(Lambds) < 0).astype(int)
    filt_lambd = Lambds * mask
    filt_lambd[filt_lambd == 0] = np.nan
    # should be the same as
    # filt_damp = np.where(Lambds, np.logical_and(np.real(Lambds) < 0), Lambds, np.nan)
    return filt_lambd, mask


# -----------------------------------------------------------------------------


def HC_removeZeroImg(Lambds) -> typing.Tuple[np.ndarray, np.ndarray]:
    """
    Apply Hard validation Criteria (HC), retaining only those elements which have non zero imaginary part in eingenvalues.

    Parameters
    ----------
    Lambds : np.ndarray
        Array of eigenvalues.

    Returns
    -------
    filt_lambd : np.ndarray
        Array of the same shape as `Lambds` with elements that do not satisfy the condition set to NaN.
    mask : np.ndarray
        Boolean array of the same shape as `Lambds`, where True indicates that the element is with negetive real part of eigenvalues.

    """
    # Create a mask where the imaginary part is not zero
    mask = ~np.isclose(np.imag(Lambds), 0).astype(bool)
    
    # Retain only the values where the imaginary part is not zero
    filt_lambd = np.where(mask, Lambds, np.nan)
    return filt_lambd, mask