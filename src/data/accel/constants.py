MAX_MAP_SIZE = 52200  # The maximum number of samples saved in FIFO

LATENT_DATA_INDEX = 3  # For testing receiving a sample data late

TIMEOUT = 2  # Max wait time until enough samples are collected for the test_Accelerometer

INTERVAL = 0.001  # Check every 0.001s to see if samples are collected

MIN_LEN = 12  # Minimum length for binary decoding

MIN_SAMPLES_NEEDED = 100  # Minimum samples needed before running it to sysid


# The constants below are used to publish the test messages for test_accelerometer

BATCH_SIZE = 32  # Number of data samples in each message

DESCRIPTOR_LENGTH = 28  # Fixed length of the descriptor section in bytes

METADATA_VERSION = 2  # Version number for metadata, always set to 2

SECONDS = 1742400339  # Exaample value for seconds since epoch 

NANOSECONDS = 123456789  # Example  nanoseconds value 
