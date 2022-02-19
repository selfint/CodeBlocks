from typing import Dict, NamedTuple, Tuple

PathLineScopes = Dict[Tuple[str, ...], Dict[int, Tuple[str, ...]]]


class Definition(NamedTuple):
    row: int
    col: int
    scope: Tuple[str, ...]
    path: Tuple[str, ...]
    name: str
    kind: str


class Reference(NamedTuple):
    row: int
    scope: Tuple[str, ...]
    path: Tuple[str, ...]


class ResolvedReference(NamedTuple):
    reference: Reference
    definition: Definition
