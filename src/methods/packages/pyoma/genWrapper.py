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



def MAC(phi_X: np.ndarray, phi_A: np.ndarray) -> np.ndarray:
    """
    Calculates the Modal Assurance Criterion (MAC) between two sets of mode shapes.

    Parameters
    ----------
    phi_X : ndarray
        Mode shape matrix X, shape: (n_locations, n_modes) or n_locations.
    phi_A : ndarray
        Mode shape matrix A, shape: (n_locations, n_modes) or n_locations.

    Returns
    -------
    ndarray
        MAC matrix. Returns a single MAC value if both `phi_X` and `phi_A` are
        one-dimensional arrays.

    Raises
    ------
    Exception
        If mode shape matrices have more than 2 dimensions or if their first dimensions do not match.
    """
    if phi_X.ndim == 1:
        phi_X = phi_X[:, np.newaxis]

    if phi_A.ndim == 1:
        phi_A = phi_A[:, np.newaxis]

    if phi_X.ndim > 2 or phi_A.ndim > 2:
        raise Exception(
            f"Mode shape matrices must have 1 or 2 dimensions (phi_X: {phi_X.ndim}, phi_A: {phi_A.ndim})"
        )

    if phi_X.shape[0] != phi_A.shape[0]:
        raise Exception(
            f"Mode shapes must have the same first dimension (phi_X: {phi_X.shape[0]}, "
            f"phi_A: {phi_A.shape[0]})"
        )

    # mine
    # MAC = np.abs(np.dot(phi_X.conj().T, phi_A)) ** 2 / (
    #     (np.dot(phi_X.conj().T, phi_X)) * (np.dot(phi_A.conj().T, phi_A))
    # )
    # original
    MAC = np.abs(np.conj(phi_X).T @ phi_A) ** 2
    MAC = MAC.astype(complex)
    for i in range(phi_X.shape[1]):
        for j in range(phi_A.shape[1]):
            MAC[i, j] = MAC[i, j] / (
                np.conj(phi_X[:, i]) @ phi_X[:, i] * np.conj(phi_A[:, j]) @ phi_A[:, j]
            )

    if MAC.shape == (1, 1):
        MAC = MAC[0, 0]

    return MAC.real


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


def SC_apply(Fn, Xi, Phi, ordmin, ordmax, step, err_fn, err_xi, err_phi) -> np.ndarray:
    """
    Apply Soft validation Criteria (SC) to determine the stability of modal parameters between consecutive orders.

    Parameters
    ----------
    Fn : np.ndarray
        Array of natural frequencies.
    Xi : np.ndarray
        Array of damping ratios.
    Phi : np.ndarray
        Array of mode shapes.
    ordmin : int
        Minimum model order.
    ordmax : int
        Maximum model order.
    step : int
        Step size for increasing model order.
    err_fn : float
        Tolerance for the natural frequency error.
    err_xi : float
        Tolerance for the damping ratio error.
    err_phi : float
        Tolerance for the mode shape error.

    Returns
    -------
    Lab : np.ndarray
        Array of labels indicating stability (1 for stable, 0 for unstable).
    """
    # inirialise labels
    Lab = np.zeros(Fn.shape, dtype="int")

    # SOFT CONDITIONS
    # STABILITY BETWEEN CONSECUTIVE ORDERS
    for oo in range(ordmin, ordmax + 1, step):
        o = int(oo / step)

        f_n = Fn[:, o].reshape(-1, 1)
        xi_n = Xi[:, o].reshape(-1, 1)
        phi_n = Phi[:, o, :]

        f_n1 = Fn[:, o - 1].reshape(-1, 1)
        xi_n1 = Xi[:, o - 1].reshape(-1, 1)
        phi_n1 = Phi[:, o - 1, :]

        # Skip the first order as it has no previous order to compare with
        if o == 0:
            continue

        for i in range(len(f_n)):
            try:
                idx = np.nanargmin(np.abs(f_n1 - f_n[i]))

                cond1 = np.abs(f_n[i] - f_n1[idx]) / f_n[i]
                cond2 = np.abs(xi_n[i] - xi_n1[idx]) / xi_n[i]
                cond3 = 1 - MAC(phi_n[i, :], phi_n1[idx, :])
                if cond1 < err_fn and cond2 < err_xi and cond3 < err_phi:
                    Lab[i, o] = 1  # Stable
                else:
                    Lab[i, o] = 0  # Nuovo polo o polo instabile
            except Exception as e:
                # If f_n[i] is nan, do nothin, n.b. the lab stays 0
                logger.debug(e)
    return Lab
