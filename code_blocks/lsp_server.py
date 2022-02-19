import subprocess
from pathlib import Path


class LspServer:
    def __init__(self, root_dir: str) -> None:
        self._lsp_server = subprocess.Popen(
            "pyright-langserver --stdio",
            shell=True,
            cwd=root_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        self._root_uri = Path(root_dir).resolve().absolute().as_uri()
        self._lsp_proc_id = self._lsp_server.pid

    def stop(self):
        self._lsp_server.terminate()
