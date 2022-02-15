from typing import Set

from code_blocks.types import Definition, Reference, ResolvedReference


class Connector:
    def __init__(self):
        self._definitions: Set[Definition] = set()
        self._references: Set[Definition] = set()

        self._resolved_references: Set[ResolvedReference] = set()
