from pyoma2.setup.single import SingleSetup
from pyoma.ssiWrapper import SSIcov

import numpy as np

def sysid(data, Params):
    """
    Perform system identification using the Covariance-based Stochastic Subspace Identification (SSI-COV) method.

    This function transposes the data if needed, initializes a system identification setup,
    applies the SSI-COV algorithm, and returns the identified model parameters.

    Args:
        data (numpy.ndarray): Input time-series data, where rows represent time steps and 
                              columns represent different sensor channels.
        Params (dict): Dictionary containing parameters for the system identification process:
            - 'Fs' (float): Sampling frequency of the input data.
            - 'block_shift' (int): Block shift parameter for the SSI algorithm.
            - 'model_order' (int): Maximum model order for the system identification.

    Returns:
        dict: A dictionary containing the results of the SSI-COV model, including estimated
              frequencies, damping ratios, and mode shapes.
    """
    if data.shape[0] < data.shape[1]:
        data = data.T
    print(f"Data dimensions: {data.shape}")
    print(f"OMA parameters: {Params}")

    mySetup = SingleSetup(data, fs=Params['Fs'])
    ssi_mode_track = SSIcov(
        name="SSIcovmm_mt",
        method='cov_mm',
        br=Params['block_shift'],
        ordmax=Params['model_order'],
        calc_unc=True
    )

    mySetup.add_algorithms(ssi_mode_track)
    mySetup.run_by_name("SSIcovmm_mt")
    
    OUTPUT = ssi_mode_track.result.model_dump()
    return OUTPUT





