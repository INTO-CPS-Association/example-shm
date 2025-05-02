from typing import Any
import numpy as np


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
    elif isinstance(obj, list):
        return [convert_numpy_to_list(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_to_list(item) for item in obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy_to_list(obj.tolist())
    elif isinstance(obj, complex):
        return {"real": obj.real, "imag": obj.imag}
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    else:
        try:
            # fallback: try converting if it's a NumPy scalar or unknown object
            if hasattr(obj, 'item'):
                return obj.item()
        except Exception:
            pass
    return obj
