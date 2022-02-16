from pathlib import Path
from typing import Any, Type

from sansio_lsp_client.client import Client
from sansio_lsp_client.events import ConfigurationRequest
from sansio_lsp_client.events import Definition as DefinitionEvent
from sansio_lsp_client.events import Event, RegisterCapabilityRequest
from sansio_lsp_client.structs import (
    TextDocumentIdentifier,
    TextDocumentItem,
    TextDocumentPosition,
)


class LspClient:
    def __init__(self, lsp_proc_id: int, root_uri: str) -> None:
        self._lsp_proc_id = lsp_proc_id
        self._root_uri = root_uri

        self._client = Client(lsp_proc_id, root_uri)
        self._client_stdin = Path(f"/proc/{self._lsp_proc_id}/fd/0")
        self._client_stdout = Path(f"/proc/{self._lsp_proc_id}/fd/1")

        # send initialize message of client
        self._client_stdin.write_bytes(self._client.send())

        # wait for client to initialize
        with self._client_stdout.open("rb") as stdout:
            while not self._client.is_initialized:
                data = stdout.read(1)
                for event in self._client.recv(data):
                    print(event)

        # send initialized message to server
        self._client_stdin.write_bytes(self._client.send())

    def _get_next_event(self, event_type: Type[Event] = Event) -> Any:
        with self._client_stdout.open("rb") as stdout:
            while True:
                data = stdout.read(1)
                for event in self._client.recv(data):
                    if isinstance(event, event_type):
                        return event
                    else:
                        print("@@@@", event)

    def notify_open(self, text_document_item: TextDocumentItem):
        # notify LSP we opened the file
        self._client.did_open(text_document_item)
        self._client_stdin.write_bytes(self._client.send())

        # reply to RegisterCapabilityRequest
        next_event: RegisterCapabilityRequest = self._get_next_event(
            RegisterCapabilityRequest
        )
        next_event.reply()
        self._client_stdin.write_bytes(self._client.send())

        # reply to 3 ConfigurationRequest
        for _ in range(3):
            next_event: ConfigurationRequest = self._get_next_event(
                ConfigurationRequest
            )
            next_event.reply()
            self._client_stdin.write_bytes(self._client.send())

    def notify_close(self, text_document_identifier: TextDocumentIdentifier):
        # notify LSP we closed the file
        self._client.did_close(text_document_identifier)
        self._client_stdin.write_bytes(self._client.send())

    def request_definition(
        self, text_document_position: TextDocumentPosition
    ) -> DefinitionEvent:

        # request definition of reference
        self._client.definition(text_document_position)
        self._client_stdin.write_bytes(self._client.send())

        # wait for response
        definition_event: DefinitionEvent = self._get_next_event(DefinitionEvent)

        return definition_event
