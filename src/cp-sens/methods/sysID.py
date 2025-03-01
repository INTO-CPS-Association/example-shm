from pyoma2.setup.single import SingleSetup
from pyoma2.algorithms.ssi import SSIcov
import numpy as np

def sysid(data, Params):
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





