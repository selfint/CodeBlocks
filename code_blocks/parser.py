from __future__ import annotations

import ast
from typing import List, Union, Any, Tuple, Set

from code_blocks.types import Definition, Reference

DefinitionNode = Union[ast.FunctionDef, ast.ClassDef]
ReferenceNode = Union[ast.Call]


class Visitor(ast.NodeVisitor):
    def __init__(
        self,
        definitions: Set[Definition],
        references: Set[Reference],
        path: Tuple[str, ...],
    ):
        self.definitions = definitions
        self.references = references
        self._path = path

        self._scope: List[DefinitionNode] = []

    def generic_visit(self, node: ast.AST) -> Any:
        if hasattr(node, "col_offset") and len(self._scope) > 0:
            if node.col_offset <= self._scope[-1].col_offset:
                self._scope.pop()

        if isinstance(node, DefinitionNode):
            self._visit_definition(node)
        elif isinstance(node, ReferenceNode):
            self._visit_reference(node)

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

    def _visit_reference(self, node: ReferenceNode):
        if isinstance(node.func, ast.Name):
            reference = Reference(
                row=node.lineno,
                col=node.col_offset,
                scope=tuple(n.name for n in self._scope),
                path=self._path,
            )
            self.references.add(reference)
        elif isinstance(node.func, ast.Attribute):
            reference = Reference(
                row=node.lineno,
                col=node.func.value.end_col_offset + 1,
                scope=tuple(n.name for n in self._scope),
                path=self._path,
            )
            self.references.add(reference)


class Parser:
    def __init__(self) -> None:
        self._definitions: Set[Definition] = set()
        self._references: Set[Reference] = set()

    def consume(self, source: str, path: Tuple[str, ...]):
        """
        Consume target text, mark it as coming from target_path.

        :param source: Text to consume.
        :param path: Origin of source text.
        """

        tree = ast.parse(source, filename=path[-1])
        visitor = Visitor(self._definitions, self._references, path)

        visitor.visit(tree)

    @property
    def definitions(self):
        return self._definitions

    @property
    def references(self):
        return self._references
