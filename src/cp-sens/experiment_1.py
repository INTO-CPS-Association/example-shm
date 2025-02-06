from data.accel.accelerometer import IAccelerometer
from data.accel.random import RandomSource
from data.accel.senseHAT import senseHAT

def main():
    random: IAccelerometer = RandomSource()
    print(random.read())
    sensehat: IAccelerometer = senseHAT()
    print(sensehat.read())

if __name__ == '__main__':
    main()