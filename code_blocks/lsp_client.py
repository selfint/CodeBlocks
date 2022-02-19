import time
from pathlib import Path
from queue import Empty, Queue
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


class PathReader:
    def __init__(self, path: Path, queue: "Queue[bytes]") -> None:
        self._read = True
        self._reader_thread = Thread(target=self._path_to_queue, args=(path, queue))
        self._reader_thread.start()

    def _path_to_queue(self, path: Path, queue: "Queue[bytes]"):
        """Push any bytes written to given path to the given queue.

        Will stop reading when _read is set to False.

        Args:
            path (Path): Path to read bytes from
            queue (Queue[bytes]): Queue to push bytes to
        """

        with path.open("rb") as f:
            while self._read:
                b = f.read1(1)
                queue.put(b)

    def stop(self):
        self._read = False
        self._reader_thread.join(timeout=1)


class LspClient:
    def __init__(self, lsp_server: LspServer) -> None:
        self._lsp_server = lsp_server

        self._lsp_stdin = Path(f"/proc/{self._lsp_server._lsp_proc_id}/fd/0")
        self._lsp_stdout = Path(f"/proc/{self._lsp_server._lsp_proc_id}/fd/1")

        self._lsp_stdout_q: "Queue[bytes]" = Queue()
        self._lsp_stdout_reader = PathReader(self._lsp_stdout, self._lsp_stdout_q)

        # disable progress reporting
        CAPABILITIES["window"]["workDoneProgress"] = False

        # start client (implicitly sends an "initialize" request to the lsp)
        self._client = Client(self._lsp_server._lsp_proc_id, self._lsp_server._root_uri)
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
        self._lsp_stdout_reader.stop()
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
            try:
                data = self._lsp_stdout_q.get(timeout=0.5)
            except Empty:
                if self._read_events:
                    continue
                else:
                    break
            else:
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
        print("# SEN #", send_buf.decode())
        self._lsp_stdin.write_bytes(send_buf)

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
