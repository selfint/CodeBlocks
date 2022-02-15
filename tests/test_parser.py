from code_blocks.parser import Parser, Definition


def test_function_def_detection():
    source = """
def bar():
    pass
    """

    path = ("test", "foo.py")

    p = Parser()
    p.consume(source, path)

    expected_definitions = [
        Definition(2, 0, tuple(), path, "bar", "function")
    ]
    assert p.definitions == expected_definitions


def test_class_def_detection():
    source = """
class Test:
    pass
    """

    path = ("test", "foo.py")

    p = Parser()
    p.consume(source, path)

    expected_definitions = [
        Definition(2, 0, tuple(), path, "Test", "class")
    ]
    assert p.definitions == expected_definitions


def test_scope_detection():
    source = """
class Test:
    def foo():
        pass
    """

    path = ("test", "foo.py")

    p = Parser()
    p.consume(source, path)

    expected_definitions = [
        Definition(2, 0, tuple(), path, "Test", "class"),
        Definition(3, 4, ("Test",), path, "foo", "function"),
    ]
    assert p.definitions == expected_definitions


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

    p = Parser()
    p.consume(source1, path1)
    p.consume(source2, path2)

    expected_function_definitions = [
        Definition(2, 0, tuple(), path1, "bar", "function"),
        Definition(2, 0, tuple(), path2, "Test", "class"),
        Definition(3, 4, ("Test",), path2, "foo", "function"),
    ]

    assert p.definitions == expected_function_definitions
