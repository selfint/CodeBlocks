from __future__ import annotations
from typing import List, NamedTuple, Union, Any, Tuple, Set

import ast

DefinitionNode = Union[ast.FunctionDef, ast.ClassDef]


class Definition(NamedTuple):
    row: int
    col: int
    scope: Tuple[str, ...]
    path: Tuple[str, ...]
    name: str
    kind: str


class Visitor(ast.NodeVisitor):
    def __init__(
        self,
        definitions: Set[Definition],
        path: Tuple[str, ...],
    ):
        self.definitions = definitions
        self._path = path

        self._scope: List[DefinitionNode] = []

    def generic_visit(self, node: ast.AST) -> Any:
        if hasattr(node, "col_offset") and len(self._scope) > 0:
            if node.col_offset < self._scope[-1].col_offset:
                self._scope.pop()

        if isinstance(node, DefinitionNode):
            if isinstance(node, ast.FunctionDef):
                kind = "function"
            elif isinstance(node, ast.ClassDef):
                kind = "class"
            else:
                raise TypeError(f"Got Definition of unknown type: {type(node)}")

            location = Definition(
                row=node.lineno,
                col=node.col_offset,
                scope=tuple(n.name for n in self._scope),
                path=self._path,
                name=node.name,
                kind=kind,
            )
            self.definitions.add(location)
            self._scope.append(node)

        super(Visitor, self).generic_visit(node)


class Parser:
    def __init__(self) -> None:
        self._definitions: Set[Definition] = set()

    def consume(self, source: str, path: Tuple[str, ...]):
        """
        Consume target text, mark it as coming from target_path.

        :param source: Text to consume.
        :param path: Origin of source text.
        """

        tree = ast.parse(source, filename=path[-1])
        visitor = Visitor(self._definitions, path)

        visitor.visit(tree)

    @property
    def definitions(self):
        return self._definitions
