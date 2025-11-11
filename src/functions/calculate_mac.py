import numpy as np

def calculate_mac(reference_mode_shape: np.array, second_mode_shape: np.array) -> float:
    """
        Calculate Modal Assurance Criterion (MAC)

        Args:
            reference_mode (np.array): Mode shape to compare to
            mode_shape (np.array): Mode shape to compare
        Returns:
            MAC (float): Modal Assurance Criterion 

    """
    numerator = np.abs(np.dot(reference_mode_shape.conj().T, second_mode_shape)) ** 2
    denominator = np.dot(reference_mode_shape.conj().T,
                         reference_mode_shape) * np.dot(second_mode_shape.conj().T,
                                                         second_mode_shape)
    return np.real(numerator / denominator)