import os
from collections import defaultdict
from pathlib import Path
from typing import Any, List, Optional, Set, Tuple, Type
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from sansio_lsp_client import References
from sansio_lsp_client.events import Definition as DefinitionEvent
from sansio_lsp_client.events import Event
from sansio_lsp_client.structs import (
    Position,
    TextDocumentIdentifier,
    TextDocumentItem,
    TextDocumentPosition,
)

from code_blocks.lsp_client import LspClient
from code_blocks.types import Definition, PathLineScopes, Reference, ResolvedReference


def uri_to_path(uri: str) -> Path:
    parsed = urlparse(uri)
    host = "{0}{0}{mnt}{0}".format(os.path.sep, mnt=parsed.netloc)
    return Path(
        os.path.normpath(os.path.join(host, url2pathname(unquote(parsed.path))))
    )


class Resolver:
    def __init__(self, lsp_client: LspClient, root_uri: str):
        self._lsp_client = lsp_client
        self._root_uri = root_uri
        self._root_path = uri_to_path(self._root_uri)

    def consume(self, source: str, path: Tuple[str, ...]):

        # convert reference relative path to full path uri
        path_uri = f"{self._root_uri}/{os.path.sep.join(path)}"

        # create LSP objects pointing to reference file and position
        text_document_item = TextDocumentItem(
            uri=path_uri, languageId="python", version=1, text=source
        )

        # notify LSP we opened the file
        self._lsp_client.notify_open(text_document_item)

    def resolve_definitions(
        self, definitions: Set[Definition], path_line_scopes: PathLineScopes
    ) -> Set[ResolvedReference]:
        """Get all references to all given definitions.

        Args:
            definitions (Set[Definition]): Definitions to get references of.

        Returns:
            Set[ResolvedReference]: All references to the given definitions.
        """

        resolved_references: Set[ResolvedReference] = set()

        for definition in definitions:
            references = self.get_definition_resolved_references(
                definition, path_line_scopes
            )
            resolved_references = resolved_references.union(references)

        return resolved_references

    def get_definition_resolved_references(
        self, definition: Definition, path_line_scopes: PathLineScopes
    ) -> Set[ResolvedReference]:

        # get reference locations from LSP
        references: References = self.get_definition_references(definition)

        # return an empty set if no references were found
        if references.result is None:
            return set()

        # resolve all references to the definition
        resolved_references = set()
        for reference_location in references.result:

            # get location path relative to root path
            location_path = uri_to_path(reference_location.uri)
            relative_path = location_path.relative_to(self._root_path)

            # get reference position
            row = reference_location.range.start.line + 1
            col = reference_location.range.start.character

            # make sure the reference isn't the definition itself
            if relative_path.parts == definition.path:
                if row == definition.row and col == definition.col:
                    continue

            # get reference scope
            scope = path_line_scopes[relative_path.parts][row]

            # build resolved reference to the definition
            reference = Reference(row, scope, relative_path.parts)
            resolved_reference = ResolvedReference(reference, definition)

            resolved_references.add(resolved_reference)

        return resolved_references

    def get_definition_references(self, definition: Definition) -> References:

        # convert reference relative path to full path uri
        path_uri = f"{self._root_uri}/{os.path.sep.join(definition.path)}"

        # create LSP objects pointing to reference file and position
        text_document_identifier = TextDocumentIdentifier(uri=path_uri)

        # LSP starts rows from 0, we start from 1, so we need to subtract 1
        position = Position(line=definition.row - 1, character=definition.col)

        # get text document position of reference
        text_document_position = TextDocumentPosition(
            textDocument=text_document_identifier, position=position
        )

        # request definition of reference
        references: References = self._lsp_client.request_references(
            text_document_position
        )

        return references
