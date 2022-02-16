from collections import defaultdict
import os
from pathlib import Path
from typing import Any, Optional, Set, Type
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname


from code_blocks.types import Definition, Reference, ResolvedReference
from code_blocks.lsp_client import LspClient
from sansio_lsp_client.events import Definition as DefinitionEvent
from sansio_lsp_client.events import Event
from sansio_lsp_client.structs import (
    TextDocumentIdentifier,
    TextDocumentItem,
    TextDocumentPosition,
    Position,
)


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

    def _get_next_event(self, event_type: Type[Event] = Event) -> Any:
        self._lsp_client._await_event(event_type)

    def reference_to_text_document_position(
        self, reference: Reference
    ) -> TextDocumentPosition:
        """
        Convert a Reference to a TextDocumentPosition
        :param reference: Reference to convert.
        :return: TextDocumentPosition of reference.
        """

        path_uri = f"{self._root_uri}/{os.path.sep.join(reference.path)}"
        text_document_identifier = TextDocumentIdentifier(uri=path_uri)
        position = Position(line=reference.row, character=reference.col)

        text_document_position = TextDocumentPosition(
            textDocument=text_document_identifier, position=position
        )

        return text_document_position

    def get_matching_definition(
        self, definitions: Set[Definition], definition_event: DefinitionEvent
    ) -> Optional[Definition]:
        """Get the matching Definition for a given DefinitionEvent, from the
        given defintions set.

        Args:
            definitions (Set[Definition]): Possible matching definitions
            definition_event (DefinitionEvent): DefenitionEvent from LSP

        Returns:
            Optional[Definition]: Matching Definition if found, None if none were found
        """

        # make sure defintion event has a result
        if definition_event.result is None:
            return None

        # get the location
        location = definition_event.result
        if isinstance(location, list):
            location = location[0]

        # LSP starts rows from 0, we start from 1
        row = location.range.start.line + 1
        col = location.range.start.character

        # get relative path from root dir
        root_path = len(uri_to_path(self._root_uri).parts)
        def_path = tuple(uri_to_path(location.uri).parts)[root_path:]

        # build the expected location tuple
        expected_defintion_location = (def_path, row, col)

        # look for matching defintions
        for definition in definitions:
            defintion_location = (definition.path, definition.row, definition.col)

            if defintion_location == expected_defintion_location:
                return definition

    def resolve(
        self, definitions: Set[Definition], references: Set[Reference]
    ) -> Set[ResolvedReference]:
        """
        Resolve the given references to the given definitions.

        :param definitions: Definitions that references can be resolved to.
        :param references: References that need to be resolved.
        :return: Set of resolved references.
        """

        # group all references by their file
        file_reference_groups = defaultdict(set)
        for reference in references:
            file_reference_groups[reference.path].add(reference)

        resolved_references = set()
        for file_path, file_references in file_reference_groups.items():

            # convert reference relative path to full path uri
            path_uri = f"{self._root_uri}/{os.path.sep.join(file_path)}"

            # load source file
            text = uri_to_path(path_uri).read_text()

            # create LSP objects pointing to reference file and position
            text_document_item = TextDocumentItem(
                uri=path_uri, languageId="python", version=1, text=text
            )
            text_document_identifier = TextDocumentIdentifier(uri=path_uri)

            # notify LSP we opened the file
            self._lsp_client.notify_open(text_document_item)

            for reference in file_references:
                resolved_reference = self.resolve_reference(definitions, reference)
                resolved_references.add(resolved_reference)

            # notify LSP we closed the file
            self._lsp_client.notify_close(text_document_identifier)

        return resolved_references

    def resolve_reference(
        self, definitions: Set[Definition], reference: Reference
    ) -> Optional[ResolvedReference]:
        """Resolve a given reference to one of the given definitions.

        Args:
            definitions (Set[Definition]): Possible definitions to resolve reference to.
            reference (Reference): Reference to resolve to a definition.

        Returns:
            Optional[ResolvedReference]: ResolvedReference of given reference if found,
                                         None if not.
        """

        # convert reference relative path to full path uri
        path_uri = f"{self._root_uri}/{os.path.sep.join(reference.path)}"

        # create LSP objects pointing to reference file and position
        text_document_identifier = TextDocumentIdentifier(uri=path_uri)

        # LSP starts rows from 0, we start from 1, so we need to subtract 1
        position = Position(line=reference.row - 1, character=reference.col)

        # get text document position of reference
        text_document_position = TextDocumentPosition(
            textDocument=text_document_identifier, position=position
        )

        # request definition of reference
        definition_event = self._lsp_client.request_definition(text_document_position)

        # get matching definition for definition event
        matching_definition = self.get_matching_definition(
            definitions, definition_event
        )

        # create a resolved reference if a matching definition was found
        if matching_definition is not None:
            return ResolvedReference(
                reference=reference,
                definition=matching_definition,
            )
        else:
            return None
