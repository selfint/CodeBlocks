import pandas as pd
from code_blocks.analyzer import get_depths


def test_get_depths():
    df = pd.DataFrame({"src": [1,2,3], "dst": [2,3,4]})
    expected = pd.Series([0,1,2])
    actual = get_depths(df, "src", "dst")

    pd.testing.assert_series_equal(expected, actual)


def test_get_depths_when_loop():
    df = pd.DataFrame({"src": [1,2,3], "dst": [2,3,1]})
    expected = pd.Series([0,0,0])
    actual = get_depths(df, "src", "dst")

    pd.testing.assert_series_equal(expected, actual)


def test_get_depths_when_also_loop():
    df = pd.DataFrame({"src": [1,2,3], "dst": [2,3,2]})
    expected = pd.Series([0,1,1])
    actual = get_depths(df, "src", "dst")

    pd.testing.assert_series_equal(expected, actual)

