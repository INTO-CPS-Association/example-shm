from pyoma2.setup.single import SingleSetup            # Single setup for pyoma
from pyoma2.algorithms.ssi import SSIcov             # Used method cov based SSI


def sysid(data, Params):
    
    if data.shape[0]<data.shape[1]:
        data = data.T                           # transpose it if data has more column than row

    ssi_system = SingleSetup(data, fs=Params['Fs'])
    ssi_mode_track = SSIcov(name="SSIcovmm_mt", method='cov_mm', br=Params['block_shift'], ordmin=Params['model_order_min'],ordmax=Params['model_order'], calc_unc=True) 

    ssi_system.add_algorithms(ssi_mode_track)                      # Add algorithms to the class
    ssi_system.run_by_name("SSIcovmm_mt")                          # run

    # save dict of results
    OUTPUT = ssi_mode_track.result.model_dump()
    
    return OUTPUT