import numpy as np #type: ignore
from pyoma2.setup.single import SingleSetup
from pyoma2.algorithms.ssi import SSIcov

def sysid(data, Params):
    """
    Perform system identification using OMA (Operational Modal Analysis).

    Parameters:
      data (numpy.ndarray): The input data array.
      Params (dict): Dictionary with OMA parameters. It must include:
          - Fs: Sampling frequency.
          - block_shift: Block shift used in the algorithm.
          - model_order: Model order for the identification.

    Returns:
      dict: Dictionary of OMA results from the SSI analysis.
    """
    # If the data has more columns than rows, transpose it.
    if data.shape[0] < data.shape[1]:
        data = data.T
    print(f"Data dimensions: {data.shape}")
    print(f"OMA parameters: {Params}")

    # Setup the OMA algorithm
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

    # Dump and return the results dictionary
    OUTPUT = ssi_mode_track.result.model_dump()
    return OUTPUT
