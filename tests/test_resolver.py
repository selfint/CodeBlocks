import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple, List, Set

from code_blocks.resolver import Resolver
from code_blocks.types import ResolvedReference, Reference, Definition


class LspTestEnv:
    def __init__(self, sources: List[Tuple[str, Tuple[str, ...]]]):
        self._sources = sources

        self._tempdir = tempfile.mkdtemp(prefix="codeblocks-lsp-test-env")

        for source, path in sources:
            full_path = Path(self._tempdir) / os.path.sep.join(path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(source)

        self._lsp_proc: subprocess.Popen = subprocess.Popen(
            "pyright-langserver --stdio",
            shell=True,
            cwd=self._tempdir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        print(1)

    @property
    def lsp_proc_id(self) -> int:
        return self._lsp_proc.pid

    @property
    def root_uri(self) -> str:
        return f"file://{self._tempdir}"

    def __del__(self):
        shutil.rmtree(self._tempdir, ignore_errors=True)
        self._lsp_proc.terminate()


def assert_got_expected_resolved_references_from_definitions_and_references(
    sources: List[Tuple[str, Tuple[str, ...]]],
    definitions: Set[Definition],
    references: Set[Reference],
    expected_resolved_references: Set[ResolvedReference],
):
    test_env = LspTestEnv(sources)

    resolver = Resolver(test_env.lsp_proc_id, test_env.root_uri)

    assert resolver.resolve(definitions, references) == expected_resolved_references


def test_resolve_single_file_single_method():
    source = """
def foo():
    pass

foo()
    """
    path = ("bar.py",)
    sources = [(source, path)]

    definitions = {Definition(2, 4, tuple(), path, "foo", "function")}
    references = {Reference(5, 0, tuple(), path)}

    expected_resolved_references = {
        ResolvedReference(
            reference=list(references)[0], definition=list(definitions)[0]
        )
    }

    assert_got_expected_resolved_references_from_definitions_and_references(
        sources, definitions, references, expected_resolved_references
    )


def test_resolve_two_files_single_method():
    source1 = """
def foo():
    pass
    """
    path1 = ("bar.py",)

    source2 = """
from bar import foo

foo()
    """
    path2 = ("baz.py",)
    sources = [(source1, path1), (source2, path2)]

    definitions = {Definition(2, 4, tuple(), path1, "foo", "function")}
    references = {Reference(4, 0, tuple(), path2)}

    expected_resolved_references = {
        ResolvedReference(
            reference=list(references)[0], definition=list(definitions)[0]
        )
    }

    assert_got_expected_resolved_references_from_definitions_and_references(
        sources, definitions, references, expected_resolved_references
    )
