import os
import sys
import numpy as np #type: ignore
import pytest #type: ignore

current_dir = os.path.dirname(os.path.abspath(__file__))
methods_dir = os.path.abspath(os.path.join(current_dir, "../../../src/cp-sens/methods"))
if methods_dir not in sys.path:
    sys.path.insert(0, methods_dir)

import sysID #type: ignore


def fake_SSIcov(name, method, br, ordmax, calc_unc):
    """
    Fake constructor that returns a dummy SSI algorithm instance.
    It replaces an invalid method 'cov_mm' with 'cov', implements _set_data,
    and pre-sets the result.
    """
    class FakeSSIcov:
        def __init__(self, name, method, br, ordmax, calc_unc):
            self.name = name
            self.method = method if method != "cov_mm" else "cov"
            self.br = br
            self.ordmax = ordmax
            self.calc_unc = calc_unc
            # Pre-set the result so that model_dump() can be called later.
            self.result = type("DummyRes", (), {
                "model_dump": lambda self: {"Fn_poles": np.array([1.0, 2.0, 3.0])}
            })()
        def run(self):
            pass
        def _set_data(self, data, fs):
            self.data = data
            self.fs = fs
            return self
    return FakeSSIcov(name, method, br, ordmax, calc_unc)

def test_sysid_calls(monkeypatch):
    # Dictionary to record call information.
    call_info = {
        "add_algorithms_called": False,
        "run_by_name_called": False,
        "algorithm_instance": None,
        "run_name": None
    }
    
    # Patch the SSIcov constructor in our sysID module.
    monkeypatch.setattr(sysID, "SSIcov", fake_SSIcov)
    
    # Save original methods for later use.
    original_add_algorithms = sysID.SingleSetup.add_algorithms
    original_run_by_name = sysID.SingleSetup.run_by_name

    # Patch add_algorithms to record its call and store the algorithm.
    def fake_add_algorithms(self, alg):
        call_info["add_algorithms_called"] = True
        call_info["algorithm_instance"] = alg
        if not hasattr(self, "algorithms"):
            self.algorithms = {}
        # Simulate storing the algorithm keyed by its name.
        self.algorithms[alg.name] = alg
        return original_add_algorithms(self, alg)

    # Patch run_by_name to record the call and force a dummy result.
    def fake_run_by_name(self, name):
        call_info["run_by_name_called"] = True
        call_info["run_name"] = name
        if not hasattr(self, "algorithms"):
            self.algorithms = {}
        # If the algorithm wasn't added, add a dummy algorithm.
        if name not in self.algorithms:
            class DummyAlg:
                @property
                def result(self):
                    class DummyRes:
                        def model_dump(self):
                            return {"Fn_poles": np.array([1.0, 2.0, 3.0])}
                    return DummyRes()
                def run(self):
                    pass
            self.algorithms[name] = DummyAlg()
        # Prepare a dummy result.
        dummy_result = type("DummyRes", (), {
            "model_dump": lambda self: {"Fn_poles": np.array([1.0, 2.0, 3.0])}
        })()
        # Force-update the algorithm instance's __dict__ to include our dummy result.
        self.algorithms[name].__dict__["result"] = dummy_result
        return self.algorithms[name].result.model_dump()
    
    monkeypatch.setattr(sysID.SingleSetup, "add_algorithms", fake_add_algorithms)
    monkeypatch.setattr(sysID.SingleSetup, "run_by_name", fake_run_by_name)
    
    # Prepare dummy data with more columns than rows (triggers transpose).
    data = np.array([[1, 2, 3],
                     [4, 5, 6]], dtype=np.float32)
    params = {"Fs": 100, "block_shift": 5, "model_order": 2}
    
    # Call the sysid function.
    output = sysID.sysid(data, params)
    
    # Verify that add_algorithms was called.
    assert call_info["add_algorithms_called"], "add_algorithms was not called"
    
    # Verify that run_by_name was called with the expected name.
    assert call_info["run_by_name_called"], "run_by_name was not called"
    assert call_info["run_name"] == "SSIcovmm_mt", (
        f"run_by_name was called with '{call_info['run_name']}' instead of 'SSIcovmm_mt'"
    )
    
    # Verify that the output contains the expected key.
    assert "Fn_poles" in output, "The output does not contain the key 'Fn_poles'"