from code_blocks.parser import Parser, Location


def test_function_def_detection():
    source = """
def bar():
    pass
    """

    path = ["test", "foo.py"]

    p = Parser()
    p.consume(source, path)

    assert len(p.function_definitions) == 1
    assert len(p.class_definitions) == 0

    funcdef = p.function_definitions[0]

    assert funcdef.row == 2
    assert funcdef.col == 0
    assert funcdef.scope == tuple()
    assert funcdef.path == path


def test_class_def_detection():
    source = """
class Test:
    pass
    """

    path = ["test", "foo.py"]

    p = Parser()
    p.consume(source, path)

    assert len(p.function_definitions) == 0
    assert len(p.class_definitions) == 1

    classdef = p.class_definitions[0]

    assert classdef.row == 2
    assert classdef.col == 0
    assert classdef.scope == tuple()
    assert classdef.path == path


def test_scope_detection():
    source = """
class Test:
    def foo():
        pass
    """

    path = ["test", "foo.py"]

    p = Parser()
    p.consume(source, path)

    assert len(p.function_definitions) == 1
    assert len(p.class_definitions) == 1

    classdef = p.class_definitions[0]

    assert classdef.row == 2
    assert classdef.col == 0
    assert classdef.scope == tuple()
    assert classdef.path == path

    funcdef = p.function_definitions[0]

    assert funcdef.row == 3
    assert funcdef.col == 4
    assert funcdef.scope == ("Test",)
    assert funcdef.path == path


def test_location_eq():
    l1 = Location(0, 0, ("a", "b"), ("c", "d"))
    l2 = Location(0, 0, ("a", "b"), ("c", "d"))
    l3 = Location(0, 1, ("a", "b"), ("c", "d"))
    l4 = Location(0, 0, ("a", "e"), ("c", "d"))

    assert l1 == l2
    assert l1 != l3
    assert l1 != l3
    assert l1 != l4
