from settings import PARAMS

# In messages received from /data topics. The first 2 bytes tells the length of the descriptor
DESCRIPTOR_LENGTH_BYTES = 2

WAIT_METADATA = 21 # Wait max 21 seconds for getting metadata message. Usually metadata is send every 10 seconds.

DEFAULT_METADATA = {"Descriptor": {
                        "Descriptor length": 28,
                        "Metadata version": 2,
                        "Seconds since epoch": 0,
                        "Nanoseconds": 0,
                        "Samples from DAQ start": 0
                        },
                    "Data":{
                        "Samples":-1,
                        "Type":"float"},
                    "Analysis chain":[{
                        "Sampling": PARAMS['Fs']
                        }]
                    }
