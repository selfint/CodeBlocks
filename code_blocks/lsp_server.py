import subprocess
import queue

from pathlib import Path
from queue import Queue
from threading import Thread
from typing import IO, Optional


class LspServer:
    def __init__(self, root_dir: str) -> None:
        self._lsp_server_proc = subprocess.Popen(
            "pyright-langserver --stdio",
            shell=True,
            cwd=root_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        # make sure stdin/out were started
        assert self._lsp_server_proc.stdin is not None, "Failed to get stdin"
        assert self._lsp_server_proc.stdout is not None, "Failed to get stdout"

        self._root_uri = Path(root_dir).resolve().absolute().as_uri()
        self._lsp_proc_id = self._lsp_server_proc.pid
        self._stdin: IO = self._lsp_server_proc.stdin
        self._stdout: IO = self._lsp_server_proc.stdout
        self._stdin_q: "Queue[bytes]" = Queue()
        self._stdout_q: "Queue[bytes]" = Queue()

        self._stop = False
        self._stdin_thread = Thread(target=self._write_stdin)
        self._stdout_thread = Thread(target=self._read_stdout)

        self._stdin_thread.start()
        self._stdout_thread.start()

    def _write_stdin(self):
        while not self._stop:

            # check if we have stdin to send to server
            try:
                stdin = self._stdin_q.get(block=False)
            except queue.Empty:
                stdin = None

            # send stdin
            if stdin is not None:
                print("# SEN #", stdin.decode())
                self._stdin.write(stdin)
                self._stdin.flush()

    def _read_stdout(self):
        while not self._stop:

            # check if server wrote stdout
            stdout = self._stdout.read(1)

            # push any stdout bytes we got to the stdout queue
            if len(stdout) > 0:
                self._stdout_q.put(stdout)

    def stop(self):
        """Stop LSP server process and communicator thread."""

        self._stop = True
        self._lsp_server_proc.terminate()
        self._stdin_thread.join()
        self._stdout_thread.join()

    def send(self, data: bytes):
        """Add data to be scheduled to send to server.

        Args:
            data (bytes): Bytes to send to server.
        """

        self._stdin_q.put(data, block=True)

    def read_bytes(self) -> Optional[bytes]:
        """Read next bytes from the LSP server stdout.

        Can be an arbitrary amount of bytes.

        Returns:
            Optional[bytes]: Byte from LSP server stdout, if there is one, None if not.
        """

        # return bytes if stdout q has any
        try:
            return self._stdout_q.get(block=False)
        except queue.Empty:
            return None
