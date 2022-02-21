import time
from queue import Queue
from threading import Thread
from typing import Any, Optional, Type

from sansio_lsp_client.client import CAPABILITIES, Client
from sansio_lsp_client.events import ConfigurationRequest
from sansio_lsp_client.events import Definition as DefinitionEvent
from sansio_lsp_client.events import (
    Event,
    Initialized,
    PublishDiagnostics,
    References,
    RegisterCapabilityRequest,
    ShowMessageRequest,
)
from sansio_lsp_client.structs import (
    TextDocumentIdentifier,
    TextDocumentItem,
    TextDocumentPosition,
)

from code_blocks.lsp_server import LspServer


class LspClient:
    def __init__(self, lsp_server: LspServer) -> None:
        self._lsp_server = lsp_server

        # disable progress reporting
        CAPABILITIES["window"]["workDoneProgress"] = False

        # start client (implicitly sends an "initialize" request to the lsp)
        self._client = Client(self._lsp_server.lsp_proc_id, self._lsp_server.root_uri)
        self._client_events: "Queue[Event]" = Queue()

        # start client event reader
        self._start_client_event_reader()

        # send initialize message to lsp
        self.send()

        # wait for client to initialize
        _ = self._await_event(Initialized)

        # send initialized message to server
        self.send()

    def stop(self):
        self._stop_client_event_reader()

    def _start_client_event_reader(self):
        self._read_events = True
        self._client_event_reader = Thread(target=self._read_client_events)
        self._client_event_reader.start()

    def _stop_client_event_reader(self):
        self._read_events = False
        self._client_event_reader.join()

    def _read_client_events(self):
        while self._read_events:
            data = self._lsp_server.read_bytes()
            if data is not None:
                for event in self._client.recv(data):
                    self._client_events.put(event)

    def _await_event(
        self,
        event_type: Type[Event] = Event,
        timeout: Optional[float] = None,
        auto_reply: Optional[bool] = False,
    ) -> Any:
        if timeout is not None:
            start = time.time()

        while timeout is None or time.time() - start < timeout:
            while not self._client_events.empty():
                event = self._client_events.get()
                do_return = isinstance(event, event_type)
                if do_return:
                    print("@ GOT @", repr(event))
                else:
                    print("@ IGN @", repr(event))

                if auto_reply and isinstance(
                    event,
                    ShowMessageRequest
                    # | WorkDoneProgressCreate
                    | RegisterCapabilityRequest | ConfigurationRequest,
                ):
                    event.reply()
                    self.send()

                if do_return:
                    return event

    def notify_open(self, text_document_item: TextDocumentItem):
        # notify LSP we opened the file
        self._client.did_open(text_document_item)
        self.send()

        # wait for server to acknowledge we opened the file
        self._await_event(PublishDiagnostics, auto_reply=True)

    def notify_close(self, text_document_identifier: TextDocumentIdentifier):
        # notify LSP we closed the file
        self._client.did_close(text_document_identifier)
        self.send()

    def send(self):
        send_buf = self._client.send()
        self._lsp_server.send(send_buf)

    def request_definition(
        self, text_document_position: TextDocumentPosition
    ) -> DefinitionEvent:

        # request definition of reference
        self._client.definition(text_document_position)
        self.send()

        # wait for response
        definition_event: DefinitionEvent = self._await_event(DefinitionEvent)

        return definition_event

    def request_references(
        self, text_document_position: TextDocumentPosition
    ) -> References:

        # request references of position
        self._client.references(text_document_position)
        self.send()

        # wait for response
        references: References = self._await_event(References, auto_reply=True)

        return references
