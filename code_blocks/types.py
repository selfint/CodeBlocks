from typing import NamedTuple, Tuple


class Definition(NamedTuple):
    row: int
    col: int
    scope: Tuple[str, ...]
    path: Tuple[str, ...]
    name: str
    kind: str


class Reference(NamedTuple):
    row: int
    col: int
    scope: Tuple[str, ...]
    path: Tuple[str, ...]


class ResolvedReference(NamedTuple):
    reference: Reference
    definition: Definition
