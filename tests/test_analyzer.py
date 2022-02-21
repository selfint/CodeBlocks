from typing import List
import pandas as pd
from code_blocks.analyzer import get_depths


def assert_expected_depths(src_col: list, dst_col: list, expected: List[int]):
    df = pd.DataFrame({"src": src_col, "dst": dst_col})
    expected = pd.Series(expected)
    actual = get_depths(df, "src", "dst")

    pd.testing.assert_series_equal(expected, actual)



def test_get_depths():
    assert_expected_depths([1, 2, 3], [2, 3, 4], [0, 1, 2])


def test_get_depths_when_loop():
    assert_expected_depths([1, 2, 3], [2, 3, 1], [0, 0, 0])


def test_get_depths_when_also_loop():
    assert_expected_depths([1, 2, 3], [2, 3, 2], [0, 1, 1])

