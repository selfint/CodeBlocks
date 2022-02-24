from typing import Dict
import pandas as pd
from code_blocks.analyzer import get_depths


def assert_expected_depths(src_col: list, dst_col: list, expected: Dict[int, int]):
    df = pd.DataFrame({"src": src_col, "dst": dst_col})
    actual = get_depths(df, "src", "dst").to_dict()

    assert actual == expected



def test_get_depths():
    assert_expected_depths(
        [1, 2, 3],
        [2, 3, 4],
        {1: 0, 2: 1, 3: 2, 4: 3},
    )


def test_get_depths_when_loop():
    assert_expected_depths(
        [1, 2, 3],
        [2, 3, 1],
        {1: 0, 2: 0, 3: 0},
    )


def test_get_depths_when_also_loop():
    assert_expected_depths(
        [1, 2, 3],
        [2, 3, 2],
        {1: 0, 2: 1, 3: 2},
    )


def test_get_depths_multiple_connections_per_node():
    assert_expected_depths(
        [1, 2, 2],
        [2, 3, 4],
        {1: 0, 2: 1, 3: 2, 4: 2},
    )


def test_get_depths_multiple_connections_per_node_and_loop():
    assert_expected_depths(
        [1, 2, 2],
        [2, 1, 3],
        {1: 0, 2: 0, 3: 1},
    )

