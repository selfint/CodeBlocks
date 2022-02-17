import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import time
from typing import Tuple, List, Set

from code_blocks.resolver import Resolver
from code_blocks.lsp_client import LspClient
from code_blocks.lsp_server import LspServer
from code_blocks.types import PathLineScopes, ResolvedReference, Reference, Definition


class LspTestEnv:
    def __init__(self, sources: List[Tuple[str, Tuple[str, ...]]]):
        self._sources = sources

        self._tempdir = tempfile.mkdtemp(prefix="codeblocks-lsp-test-env")

        for source, path in sources:
            full_path = Path(self._tempdir) / os.path.sep.join(path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(source)

        self.lsp_server = LspServer(self._tempdir)

    @property
    def lsp_proc_id(self) -> int:
        return self._lsp_proc.pid

    @property
    def root_uri(self) -> str:
        return f"file://{self._tempdir}"

    def __del__(self):
        self.lsp_server.stop()
        shutil.rmtree(self._tempdir, ignore_errors=True)


def assert_got_expected_resolved_references_from_definitions_and_path_line_scopes(
    sources: List[Tuple[str, Tuple[str, ...]]],
    definitions: Set[Definition],
    path_line_scopes: PathLineScopes,
    expected_resolved_references: Set[ResolvedReference],
):
    test_env = LspTestEnv(sources)

    lsp_client = LspClient(test_env.lsp_server)

    resolver = Resolver(lsp_client, test_env.root_uri)

    for source, path in sources:
        resolver.consume(source, path)

    resolved_references = resolver.resolve_definitions(definitions, path_line_scopes)

    try:
        assert resolved_references == expected_resolved_references

    finally:
        lsp_client.stop()


def test_resolve_single_file_single_method():
    source = """
def foo():
    pass

foo()
    """
    path = ("bar.py",)
    sources = [(source, path)]

    definitions = {Definition(2, 4, tuple(), path, "foo", "function")}
    references = {Reference(5, tuple(), path)}

    path_line_scopes = {
        path: {
            2: (),
            3: ("foo",),
            5: (),
        }
    }

    expected_resolved_references = {
        ResolvedReference(
            reference=list(references)[0], definition=list(definitions)[0]
        )
    }

    assert_got_expected_resolved_references_from_definitions_and_path_line_scopes(
        sources, definitions, path_line_scopes, expected_resolved_references
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
    references = [Reference(4, tuple(), path2), Reference(2, (), path2)]

    path_line_scopes = {
        path1: {
            2: (),
            3: ("foo",),
        },
        path2: {
            2: (),
            4: (),
        },
    }

    expected_resolved_references = {
        ResolvedReference(reference=references[0], definition=list(definitions)[0]),
        ResolvedReference(reference=references[1], definition=list(definitions)[0]),
    }

    assert_got_expected_resolved_references_from_definitions_and_path_line_scopes(
        sources, definitions, path_line_scopes, expected_resolved_references
    )


def test_resolve_multiple_files_multiple_references():
    source1 = """
from file_two import func_two

def func_one():
    pass

func_one()
func_two()
    """
    path1 = ("file_one.py",)

    source2 = """
from file_three import func_three

def func_two():
    pass

func_three()
    """
    path2 = ("file_two.py",)

    source3 = """
def func_three():
    pass
    """
    path3 = ("file_three.py",)

    sources = [(source1, path1), (source2, path2), (source3, path3)]

    path_line_scopes = {
        ("file_one.py",): {
            2: (),
            4: (),
            5: ("func_one",),
            7: (),
            8: (),
        },
        ("file_two.py",): {
            2: (),
            4: (),
            5: ("func_two",),
            7: (),
        },
        ("file_three.py",): {
            2: (),
            3: ("func_three",),
        },
    }

    definitions = [
        Definition(
            row=4,
            col=4,
            scope=(),
            path=("file_one.py",),
            name="func_one",
            kind="function",
        ),
        Definition(
            row=4,
            col=4,
            scope=(),
            path=("file_two.py",),
            name="func_two",
            kind="function",
        ),
        Definition(
            row=2,
            col=4,
            scope=(),
            path=("file_three.py",),
            name="func_three",
            kind="function",
        ),
    ]

    references = [
        Reference(row=7, scope=(), path=("file_one.py",)),
        Reference(row=8, scope=(), path=("file_one.py",)),
        Reference(row=7, scope=(), path=("file_two.py",)),
        Reference(row=2, scope=(), path=("file_one.py",)),
        Reference(row=2, scope=(), path=("file_two.py",)),
    ]

    d = definitions
    r = references

    expected_resolved_references = {
        ResolvedReference(reference=r[0], definition=d[0]),
        ResolvedReference(reference=r[1], definition=d[1]),
        ResolvedReference(reference=r[2], definition=d[2]),
        ResolvedReference(reference=r[3], definition=d[1]),
        ResolvedReference(reference=r[4], definition=d[2]),
    }

    assert_got_expected_resolved_references_from_definitions_and_path_line_scopes(
        sources, set(definitions), path_line_scopes, expected_resolved_references
    )


def test_resolve_class_constructor():
    source = """
class Test:
    def __init__(self):
        pass

t = Test()
    """
    path = ("foo.py",)

    sources = [(source, path)]

    definitions = [
        Definition(row=2, col=6, scope=(), path=path, name="Test", kind="class"),
        Definition(
            row=3, col=8, scope=("Test",), path=path, name="__init__", kind="function"
        ),
    ]

    references = [Reference(row=6, scope=(), path=path)]

    path_line_scopes = {
        path: {
            2: (),
            3: ("Test",),
            4: ("Test", "__init__"),
            6: (),
        }
    }

    expected_resolved_references = {
        ResolvedReference(reference=references[0], definition=definitions[0])
    }

    assert_got_expected_resolved_references_from_definitions_and_path_line_scopes(
        sources, set(definitions), path_line_scopes, expected_resolved_references
    )


def test_resolve_class_method():
    source = """
class Test:
    def __init__(self):
        pass

    def foo(self):
        pass

t = Test()
t.foo()
    """
    path = ("foo.py",)

    sources = [(source, path)]

    definitions = [
        Definition(row=2, col=6, scope=(), path=path, name="Test", kind="class"),
        Definition(
            row=3, col=8, scope=("Test",), path=path, name="__init__", kind="function"
        ),
        Definition(
            row=6, col=8, scope=("Test",), path=path, name="foo", kind="function"
        ),
    ]

    references = [
        Reference(row=9, scope=(), path=path),
        Reference(row=10, scope=(), path=path),
    ]

    path_line_scopes = {
        path: {
            2: (),
            3: ("Test",),
            4: ("Test", "__init__"),
            6: ("Test",),
            7: ("Test", "foo"),
            9: (),
            10: (),
        }
    }

    expected_resolved_references = {
        ResolvedReference(reference=references[0], definition=definitions[0]),
        ResolvedReference(reference=references[1], definition=definitions[2]),
    }

    assert_got_expected_resolved_references_from_definitions_and_path_line_scopes(
        sources, set(definitions), path_line_scopes, expected_resolved_references
    )
