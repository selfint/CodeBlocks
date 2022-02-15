# CodeBlocks

Represent a Python project in a graphical way.

## How it works

1. A `Parser` is created.

1. The `Parser` then *consumes* all the .py files in the project directory.

1. For each file, all function and class definitions are located using the `ast` library.

1. For each function and class definition, all its references are located using the Language Server Protocol, via the `sansio-lsp-client` library.

1. For each reference, an arrow is created from the current *location* (defined as path.to.file.class.function), to the target *location*.

1. For each function and class definition, a node is created for their *location*s.

1. Finally, the nodes and arrows are graphed using the `graphviz` library.

