#------------Constants used in find_offset tests--------------------
# Constants for mocking time (Instead of waiting actual 10 seconds for calibration)
FAKE_START_TIME = 1000.0         # Arbitrary start time
TIME_STEP = 0.1                  # Each call to time.time() advances by 0.1 seconds
NUM_FAKE_TIME_CALLS = 500        # Total number of time.time() calls to simulate

# Constants for mocked sensor readings
ACCELERATION_SENSOR_1 = (1.0, 0.0, 0.0) 
ACCELERATION_SENSOR_2 = (-2.0, 0.0, 0.0)  

#------------Constants used in publish_samples test--------------------
FAKE_OFFSET_1 = 1.0
FAKE_OFFSET_2 = -2.0
FAKE_SAMPLES_1 = [1.0, 1.0, 1.0]
FAKE_SAMPLES_2 = [2.0, 2.0, 2.0]