## Data for Testing the System Identification (sysID)

Acc_4DOF.txt:
    This file contains acceleration time-series data for a 4-degree-of-freedom (4-DOF) system.
    Format:
        - Each row represents a separate sensor channel.
        - Each column represents a time sample.
        
expected_sysid_output.npz:
    This file stores the expected output from running the `sysid()` function on the Acc_4DOF data.
    It contains the following
        - frequencies       : Identified natural frequencies (Fn_poles)
        - cov_freq          : Covariance of frequencies (Fn_poles_cov)
        - damping_ratios    : Identified damping ratios (Xi_poles)
        - cov_damping       : Covariance of damping ratios (Xi_poles_cov)
        - mode_shapes       : Identified mode shapes (Phi_poles)
        - poles_label       : Labels or indices of modal poles (Lab)

The `Acc_4DOF` data is fed into the system identification algorithm from an external file.

The output is captured and saved in `expected_sysid_output`. Since the `sysid()` function is deterministic, it should always produce the same output. This output is used to verify that `sysid()` in this project behaves as expected.
