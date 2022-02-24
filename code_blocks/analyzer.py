from collections import deque
from typing import Any, Dict, Optional, Set
from pandas import DataFrame, Series


Graph = Dict[Any, Set[Any]]


def _build_graph(df: DataFrame, src_col: str, dst_col: str) -> Graph:
    graph = dict(df[[src_col, dst_col]].groupby(src_col)[dst_col].groups)

    # convert values to lists instead of series
    graph = {k: set(df.loc[v, dst_col]) for k, v in graph.items()}

    # assign dst nodes to be leaf nodes if they aren't in the graph
    for dst_node in df[dst_col].unique():
        graph[dst_node] = graph.get(dst_node, set())

    return graph


def _find_shortest_path(graph, start, end):
    """
    Code by Eryk Kopczyński from https://www.python.org/doc/essays/graphs

    Note that this returns the path in a weird format, e.g., [[['A'], 'B'], 'D']
    """

    dist = {start: [start]}
    q = deque([start])  # changed to init queue from list
    while len(q):
        at = q.popleft()
        for next in graph[at]:
            if next not in dist:
                dist[next] = [dist[at], next]
                q.append(next)

    return dist.get(end)


def _flatten_path(p: list) -> list:
    """Convert [[['A'], 'B'], 'D'] to ['A', 'B', 'D']"""

    if len(p) == 1:
        return p

    else:
        return _flatten_path(p[0]) + [p[1]]


def get_distance(graph: Graph, start: Any, end: Any) -> Optional[int]:
    path = _find_shortest_path(graph, start, end)

    if path is not None:
        flattened_path = _flatten_path(path)

        # depth is the amount of connections
        depth = len(flattened_path) - 1

        return depth
    else:
        return None


def get_node_depth(node: Any, graph: Graph) -> int:
    return max(
        get_distance(graph, source, node) or 0
        for source in graph
    )


def get_depths(df: DataFrame, src_col: str, dst_col: str) -> Series:
    graph = _build_graph(df, src_col, dst_col)

    depths = Series({n: get_node_depth(n, graph) for n in graph})

    # make sure depths are relative to 0
    depths -= depths.min()

    return depths

