from __future__ import annotations
from typing import List, NamedTuple, Union, Any, Tuple

import ast

Definition = Union[ast.FunctionDef, ast.ClassDef]


class Location(NamedTuple):
    row: int
    col: int
    scope: Tuple[str, ...]
    path: Tuple[str, ...]


class Visitor(ast.NodeVisitor):
    def __init__(
        self,
        function_definitions: List[Location],
        class_definitions: List[Location],
        path: Tuple[str],
    ):
        self.function_definitions = function_definitions
        self.class_definitions = class_definitions
        self._path = path

        self._scope: List[Definition] = []

    def generic_visit(self, node: ast.AST) -> Any:
        if hasattr(node, "col_offset") and len(self._scope) > 0:
            if node.col_offset < self._scope[-1].col_offset:
                self._scope.pop()

        if isinstance(node, Definition):
            location = Location(
                row=node.lineno,
                col=node.col_offset,
                scope=tuple(n.name for n in self._scope),
                path=self._path,
            )

            if isinstance(node, ast.FunctionDef):
                self.function_definitions.append(location)
            elif isinstance(node, ast.ClassDef):
                self.class_definitions.append(location)
            else:
                raise TypeError(f"Got Definition of unknown type: {type(node)}")

            self._scope.append(node)

        super(Visitor, self).generic_visit(node)


class Parser:
    def __init__(self) -> None:
        self._function_definitions: List[Location] = []
        self._class_definitions: List[Location] = []

    def consume(self, source: str, path: List[str]):
        """
        Consume target text, mark it as coming from target_path.

        :param source: Text to consume.
        :param path: Origin of source text.
        """

        tree = ast.parse(source, filename=path[-1])
        visitor = Visitor(self._function_definitions, self._class_definitions, path)

        visitor.visit(tree)

    @property
    def class_definitions(self):
        return self._class_definitions

    @property
    def function_definitions(self):
        return self._function_definitions
