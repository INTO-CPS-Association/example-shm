## Data for Testing the System Identification (sysID)

The `Acc_4DOF` data is fed into the system identification algorithm from an external file.

The output is captured and saved in `expected_sysid_output`. Since the `sysid()` function is deterministic, it should always produce the same output. This output is used to verify that `sysid()` in this project behaves as expected.
