from __future__ import annotations

import ast
from typing import Any, Dict, List, Set, Tuple, Union

from code_blocks.types import Definition, PathLineScopes

DefinitionNode = Union[ast.FunctionDef, ast.ClassDef]


class Visitor(ast.NodeVisitor):
    def __init__(
        self,
        definitions: Set[Definition],
        line_scopes: Dict[int, Tuple[str, ...]],
        path: Tuple[str, ...],
    ):
        self.definitions = definitions
        self.line_scopes = line_scopes
        self._path = path

        self._scope: List[DefinitionNode] = []

    def generic_visit(self, node: ast.AST) -> Any:
        while (
            hasattr(node, "col_offset")
            and len(self._scope) > 0
            and node.col_offset <= self._scope[-1].col_offset
        ):
            self._scope.pop()

        if hasattr(node, "lineno"):

            # if the scope of this line has already been set, don't change it
            # if it hasn't been set, set it to the current scope
            # NOTE: this assumes that there aren't lines with more than one definition
            self.line_scopes[node.lineno] = self.line_scopes.get(
                node.lineno, tuple(n.name for n in self._scope)
            )

        if isinstance(node, DefinitionNode):
            self._visit_definition(node)

        super(Visitor, self).generic_visit(node)

    def _visit_definition(self, node: DefinitionNode):
        if isinstance(node, ast.FunctionDef):
            kind = "function"
            keyword_offset = len("def ")
        else:
            kind = "class"
            keyword_offset = len("class ")

        location = Definition(
            row=node.lineno,
            col=node.col_offset + keyword_offset,
            scope=tuple(n.name for n in self._scope),
            path=self._path,
            name=node.name,
            kind=kind,
        )

        self.definitions.add(location)
        self._scope.append(node)


class Parser:
    def __init__(self) -> None:
        self._definitions: Set[Definition] = set()
        self._path_line_scopes: PathLineScopes = dict()

    def consume(self, source: str, path: Tuple[str, ...]):
        """
        Consume target text, mark it as coming from target_path.

        :param source: Text to consume.
        :param path: Origin of source text.
        """

        tree = ast.parse(source, filename=path[-1])

        # init path line scopes of the given path
        self._path_line_scopes[path] = dict()

        visitor = Visitor(self._definitions, self._path_line_scopes[path], path)

        visitor.visit(tree)

    @property
    def definitions(self):
        return self._definitions

    @property
    def path_line_scopes(self):
        return self._path_line_scopes
