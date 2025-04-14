import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from data.accel.hbk.aligner import Aligner  # type: ignore


@pytest.fixture
def mock_accelerometers():
    accelerometers = []
    for ch_idx in range(3):
        acc = MagicMock()
        acc.get_batch_size.return_value = 4
        acc.get_sorted_keys.return_value = [0, 4, 8, 12, 16]
        acc.get_samples_for_key.side_effect = lambda key, ch=ch_idx: [float(key + i) for i in range(4)]
        acc.clear_used_data = MagicMock()
        accelerometers.append(acc)
    return accelerometers


@pytest.fixture
def aligner_with_mock_channels(mock_accelerometers):
    with patch("data.accel.hbk.aligner.Accelerometer", side_effect=mock_accelerometers):
        client = MagicMock()
        topics = ["topic1", "topic2", "topic3"]
        aligner = Aligner(client, topics)
    return aligner, mock_accelerometers


def test_find_continuous_key_groups(aligner_with_mock_channels):
    aligner, _ = aligner_with_mock_channels
    batch_size, groups = aligner.find_continuous_key_groups()

    assert batch_size == 4
    assert groups == [[0, 4, 8, 12, 16]]


def test_extract_with_enough_samples(aligner_with_mock_channels):
    aligner, accelerometers = aligner_with_mock_channels

    result, _ = aligner.extract(8)

    assert result.shape == (3, 8)
    expected = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    assert np.allclose(result[0], expected)

    for acc in accelerometers:
        acc.clear_used_data.assert_called_once_with(0, 8)


def test_extract_too_few_samples_returns_empty(aligner_with_mock_channels):
    aligner, _ = aligner_with_mock_channels

    result = aligner.extract(210)  # more than available it should return empty array, no timestamp
    assert result.shape == (0, 3)


def test_find_continuous_key_groups_no_channels():
    aligner = Aligner(mqtt_client=MagicMock(), topics=[])
    batch_size, key_groups = aligner.find_continuous_key_groups()
    assert batch_size is None and key_groups is None

def test_find_continuous_key_groups_handles_last_group():
    aligner = Aligner(mqtt_client=MagicMock(), topics=["t1", "t2"])
    
    ch1 = MagicMock()
    ch2 = MagicMock()
    ch1.get_batch_size.return_value = 4
    ch2.get_batch_size.return_value = 4
    ch1.get_sorted_keys.return_value = [0, 4, 8]
    ch2.get_sorted_keys.return_value = [0, 4, 8]
    aligner.channels = [ch1, ch2]

    batch_size, groups = aligner.find_continuous_key_groups()
    assert groups == [[0, 4, 8]]

def test_find_continuous_key_groups_returns_none_when_batch_size_none():
    ch = MagicMock()
    ch.get_batch_size.return_value = None
    ch.get_sorted_keys.return_value = [0, 32]

    aligner = Aligner(mqtt_client=MagicMock(), topics=[])
    aligner.channels = [ch]

    batch_size, key_groups = aligner.find_continuous_key_groups()
    assert batch_size is None
    assert key_groups is None



def test_extract_skips_initial_and_gaps_until_valid_block(aligner_with_mock_channels):
    aligner, accelerometers = aligner_with_mock_channels

    # Total keys in the system
    partial_keys = [0, 16, 32]  # Only 48 samples — should be ignored
    missing_keys = [48, 64]     # Break continuity
    valid_keys = [80, 96, 112, 128, 144, 160, 176, 192, 208, 224, 240]  
    all_keys = partial_keys + valid_keys

    batch_size = 16
    required_samples = 128
    required_keys = required_samples // batch_size  # 8

    for acc in accelerometers:
        acc.get_batch_size.return_value = batch_size
        acc.get_sorted_keys.return_value = all_keys
        acc.clear_used_data = MagicMock()
        acc.get_samples_for_key.side_effect = lambda key: [float(key + i) for i in range(batch_size)]

    # Extract 128 samples
    result, _ = aligner.extract(required_samples)

    # Assert correct shape
    assert result.shape == (3, 128), f"Expected (3, 128), got {result.shape}"

    # Expect samples from the first aligned block starting at key 80
    expected_values = [float(80 + i) for i in range(128)]
    actual_values = result[0].tolist()

    assert np.allclose(actual_values, expected_values), \
        f"Expected starting from 80, got {actual_values[:10]}"
