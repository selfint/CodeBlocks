from typing import Dict, List, Set, Tuple

from code_blocks.parser import Parser
from code_blocks.types import Definition, Reference


def assert_got_expected_definitions_from_sources(
    sources: List[Tuple[str, Tuple[str, ...]]], expected_definitions: Set[Definition]
):
    p = Parser()
    for source, path in sources:
        p.consume(source, path)

    assert p.definitions == expected_definitions


def assert_got_expected_path_line_scopes_from_sources(
    sources: List[Tuple[str, Tuple[str, ...]]],
    expected_path_line_scopes: Dict[Tuple[str, ...], Dict[int, Tuple[str, ...]]],
):
    p = Parser()
    for source, path in sources:
        p.consume(source, path)

    assert p.path_line_scopes == expected_path_line_scopes


def test_function_def_detection():
    source = """
def bar():
    pass
    """

    path = ("test", "foo.py")
    sources = [(source, path)]

    expected_definitions = {Definition(2, 4, tuple(), path, "bar", "function")}

    assert_got_expected_definitions_from_sources(sources, expected_definitions)


def test_class_def_detection():
    source = """
class Test:
    pass
    """

    path = ("test", "foo.py")
    sources = [(source, path)]

    expected_definitions = {Definition(2, 6, tuple(), path, "Test", "class")}

    assert_got_expected_definitions_from_sources(sources, expected_definitions)


def test_definition_scope_detection():
    source = """
class Test:
    def foo():
        pass
    """

    path = ("test", "foo.py")

    sources = [(source, path)]
    expected_definitions = {
        Definition(2, 6, tuple(), path, "Test", "class"),
        Definition(3, 8, ("Test",), path, "foo", "function"),
    }

    assert_got_expected_definitions_from_sources(sources, expected_definitions)


def test_line_scope_detection_one_file():
    source = """
class Test:
    def __init__(self):
        pass

    def foo(self):
        pass

class Two:
    def __init__(self):
        pass
    """

    path = ("test", "foo.py")

    sources = [(source, path)]
    expected_line_scopes = {
        path: {
            2: (),
            3: ("Test",),
            4: ("Test", "__init__"),
            6: ("Test",),
            7: ("Test", "foo"),
            9: (),
            10: ("Two",),
            11: ("Two", "__init__"),
        }
    }

    assert_got_expected_path_line_scopes_from_sources(sources, expected_line_scopes)


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
        Definition(2, 4, tuple(), path1, "bar", "function"),
        Definition(2, 6, tuple(), path2, "Test", "class"),
        Definition(3, 8, ("Test",), path2, "foo", "function"),
    }

    assert_got_expected_definitions_from_sources(sources, expected_definitions)


def test_multiple_classes_in_one_file():
    source = """
class FirstClass:
    pass
    

class SecondClass:
    pass
    """

    path = ("bar.py",)
    sources = [(source, path)]

    expected_definitions = {
        Definition(2, 6, (), path, "FirstClass", "class"),
        Definition(6, 6, (), path, "SecondClass", "class"),
    }

    assert_got_expected_definitions_from_sources(sources, expected_definitions)


def test_multiple_classes_with_methods_in_one_file():
    source = """
class FirstClass:
    def __init__(self):
        pass

    def first_method(self):
        pass
    

class SecondClass:
    def __init__(self):
        pass

    def second_method(self):
        pass
    """

    path = ("bar.py",)
    sources = [(source, path)]

    expected_definitions = {
        Definition(2, 6, (), path, "FirstClass", "class"),
        Definition(3, 8, ("FirstClass",), path, "__init__", "function"),
        Definition(6, 8, ("FirstClass",), path, "first_method", "function"),
        Definition(10, 6, (), path, "SecondClass", "class"),
        Definition(11, 8, ("SecondClass",), path, "__init__", "function"),
        Definition(14, 8, ("SecondClass",), path, "second_method", "function"),
    }

    assert_got_expected_definitions_from_sources(sources, expected_definitions)
