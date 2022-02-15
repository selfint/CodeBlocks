from typing import Tuple, List, Set

from code_blocks.parser import Parser
from code_blocks.types import Definition


def test_function_def_detection():
    source = """
def bar():
    pass
    """

    path = ("test", "foo.py")
    sources = [(source, path)]

    expected_definitions = {Definition(2, 0, tuple(), path, "bar", "function")}

    assert_got_expected_definitions_from_sources(sources, expected_definitions)


def test_class_def_detection():
    source = """
class Test:
    pass
    """

    path = ("test", "foo.py")
    sources = [(source, path)]

    expected_definitions = {Definition(2, 0, tuple(), path, "Test", "class")}

    assert_got_expected_definitions_from_sources(sources, expected_definitions)


def test_scope_detection():
    source = """
class Test:
    def foo():
        pass
    """

    path = ("test", "foo.py")

    sources = [(source, path)]
    expected_definitions = {
        Definition(2, 0, tuple(), path, "Test", "class"),
        Definition(3, 4, ("Test",), path, "foo", "function"),
    }

    assert_got_expected_definitions_from_sources(sources, expected_definitions)


def test_definition_eq():
    l1 = Definition(0, 0, ("a", "b"), ("c", "d"), "def", "function")
    l2 = Definition(0, 0, ("a", "b"), ("c", "d"), "def", "function")
    l3 = Definition(0, 1, ("a", "b"), ("c", "d"), "def", "function")
    l4 = Definition(0, 0, ("a", "e"), ("c", "d"), "def", "function")
    l5 = Definition(0, 0, ("a", "b"), ("c", "d"), "def", "class")

    assert l1 == l2
    assert l1 != l3
    assert l1 != l3
    assert l1 != l4
    assert l2 != l5


def test_multiple_sources():
    source1 = """
def bar():
    pass
"""

    path1 = ("test", "foo.py")

    source2 = """
class Test:
    def foo():
        pass
"""
    path2 = ("test", "baz.py")
    sources = [(source1, path1), (source2, path2)]

    expected_definitions = {
        Definition(2, 0, tuple(), path1, "bar", "function"),
        Definition(2, 0, tuple(), path2, "Test", "class"),
        Definition(3, 4, ("Test",), path2, "foo", "function"),
    }

    assert_got_expected_definitions_from_sources(sources, expected_definitions)


def assert_got_expected_definitions_from_sources(
    sources: List[Tuple[str, Tuple[str, ...]]], expected_definitions: Set[Definition]
):
    p = Parser()
    for source, path in sources:
        p.consume(source, path)

    assert p.definitions == expected_definitions
