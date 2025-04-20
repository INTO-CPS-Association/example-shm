# TODO

1. Add local mock setup as data source
1. Add and integrate _SysID_ into the project
1. Add _Mode Tracking_ function block
1. Integrate model solving using _YaFEM_ package
1. Integrate _Model Update_ function block
1. Wrap both _SysID_ and _Model Update_
   into MQTT blocks.
1. Perform live distributed simulation
   of _SysID_ and _Model Update_.
1. Save the received MQTT readings into
   1. json file to be pushed into InfluxDB
   1. json file
   1. `.bin` file used by Dmitri
1. Load structured data into numpy from `.bin` file used by Dmitri
      (script available in
      `https://dtl-server-2.st.lab.au.dk/TestUserDTaaS/notebooks/common/hbk/pyOMA-2%20test/OMA_on_my_beam.py`)
