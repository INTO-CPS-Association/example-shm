import os
import sys
import numpy as np #type: ignore
import pytest #type: ignore

current_dir = os.path.dirname(os.path.abspath(__file__))
methods_dir = os.path.abspath(os.path.join(current_dir, "../../../src/cp-sens/methods"))
if methods_dir not in sys.path:
    sys.path.insert(0, methods_dir)

import sysID #type: ignore

