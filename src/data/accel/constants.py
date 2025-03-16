MAX_FIFO_SIZE = 10000  # The maximum number of samples saved in FIFO

LATENT_DATA_INDEX = 3  # For testing receiving a sample data late

TIMEOUT = 2  # Max wait time until enough samples are collected for the test_Accelerometer

INTERVAL = 0.001  # Check every 0.001s to see if samples are collected

MIN_LEN = 12  # Minimum length for binary decoding

MIN_SAMPLES_NEEDED = 2000  # Minimum samples needed before running it to sysid
