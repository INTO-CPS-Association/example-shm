#------------Constats used in find_offset tests--------------------

# Constants for mocking time
FAKE_START_TIME = 1000.0         # Arbitrary start time
TIME_STEP = 0.1                  # Each call to time.time() advances by 0.1 seconds
NUM_FAKE_TIME_CALLS = 500        # Total number of time.time() calls to simulate

# Constants for mocked sensor readings
ACCELERATION_SENSOR_1 = (1.0, 0.0, 0.0)  # Expected x = 1.0
ACCELERATION_SENSOR_2 = (2.0, 0.0, 0.0)  # Expected x = 2.0


#------------Constants used in publish_samples test--------------------
FAKE_SENSOR_READING = (2.0, 0.0, 0.0)
FAKE_OFFSET = 1.0
EXPECTED_COLLECTED_SAMPLES = [1.0, 1.0, 1.0]

SAMPLE_BATCH = [0.1, 0.2, 0.3]
SAMPLE_COUNTER = 42
