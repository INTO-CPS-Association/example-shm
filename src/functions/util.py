from typing import Any
import numpy as np

# pylint: disable=R0911
def convert_numpy_to_list(obj: Any) -> Any:
    """
    Recursively convert NumPy arrays and complex numbers to JSON-safe types.

    Args:
        obj: Any data type.

    Returns:
        A fully JSON-serializable version of the input.
    """
    if isinstance(obj, dict):
        return {k: convert_numpy_to_list(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_numpy_to_list(item) for item in obj]
    if isinstance(obj, tuple):
        return tuple(convert_numpy_to_list(item) for item in obj)
    if isinstance(obj, np.ndarray):
        return convert_numpy_to_list(obj.tolist())
    if isinstance(obj, complex):
        return {"real": obj.real, "imag": obj.imag}
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    try:
        # fallback: try converting if it's a NumPy scalar or unknown object
        if hasattr(obj, 'item'):
            return obj.item()
    except Exception:
        pass
    return obj
