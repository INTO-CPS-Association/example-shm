# In messages received from /data topics. The first 2 bytes tells the length of the descriptor
DESCRIPTOR_LENGTH_BYTES = 2

WAIT_METADATA = 11 # Wait max 11 seconds for getting metadata message

DEFAULT_METADATA = {"Descriptor": {
                            "Descriptor length": 28,
                            "Metadata version": 2,
                            "Seconds since epoch": 0,
                            "Nanoseconds": 0,
                            "Samples from DAQ start": 0
                            },
                            "Data":{"Samples":-1,
                            "Type":"float"}}