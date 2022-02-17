from typing import Tuple, List, Set

from code_blocks.parser import Parser
from code_blocks.types import Definition, Reference


def assert_got_expected_definitions_from_sources(
    sources: List[Tuple[str, Tuple[str, ...]]], expected_definitions: Set[Definition]
):
    p = Parser()
    for source, path in sources:
        p.consume(source, path)

    assert p.definitions == expected_definitions


def assert_got_expected_references_from_sources(
    sources: List[Tuple[str, Tuple[str, ...]]], expected_references: Set[Reference]
):
    p = Parser()
    for source, path in sources:
        p.consume(source, path)

    assert p.references == expected_references


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


def test_scope_detection():
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


def test_function_references():
    source = """
def foo():
    pass
    
foo()
    """

    path = ("bar.py",)
    sources = [(source, path)]

    expected_references = {Reference(5, 0, tuple(), path)}

    assert_got_expected_references_from_sources(sources, expected_references)


def test_method_references():
    source = """
class Test:
    def foo():
        pass
    
t = Test()
t.foo()
    """

    path = ("bar.py",)
    sources = [(source, path)]

    expected_references = {
        Reference(6, 4, (), path),
        Reference(7, 2, (), path),
    }

    assert_got_expected_references_from_sources(sources, expected_references)


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
