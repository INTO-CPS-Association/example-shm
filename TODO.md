# TODO

1. Convert live HBK data into numpy array

2. Integrate synchronous MQTT class into
   codebase

3. Add and integrate SysID into the project

4. Add local ADXL375 setup as data source

5. Integrate model update into the project
   (use YaFEM package)

6. Wrap both _SysID_ and _Model Update_
   into MQTT blocks.

7. Perform live distributed simulation
   of _SysID_ and _Model Update_.

8. Save the received MQTT readings into
   1. `.bin` file used by Dmitri
   2. json file
   3. json file to be pushed into MongoDB

9.  Load structured data into numpy from
   1. `.bin` file used by Dmitri
      (script available in
      `https://dtl-server-2.st.lab.au.dk/TestUserDTaaS/notebooks/common/hbk/pyOMA-2%20test/OMA_on_my_beam.py`)
