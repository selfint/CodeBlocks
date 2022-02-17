from pathlib import Path
import graphviz
from code_blocks.types import Definition, ResolvedReference
from typing import Optional, Set, Tuple
from anytree import Node


def build_tree(
    definitions: Set[Definition], resolved_references: Set[ResolvedReference]
) -> Node:

    tree_dict = dict()

    for definition in definitions:
        definition_parent_hierarchy = tree_dict

        for part in definition.path + definition.scope + (definition.name,):
            if part not in definition_parent_hierarchy:
                definition_parent_hierarchy[part] = dict()

            definition_parent_hierarchy = definition_parent_hierarchy[part]

        print("@ TRE @", definition.name, definition_parent_hierarchy, tree_dict)

    for resolved_reference in resolved_references:
        reference = resolved_reference.reference
        reference_parent_hierarchy = tree_dict

        for part in reference.path + reference.scope:
            if part not in reference_parent_hierarchy:
                reference_parent_hierarchy[part] = dict()

            reference_parent_hierarchy = reference_parent_hierarchy[part]

    return tree_dict


class GraphvizVisualizer:
    def build_tree_graph(
        self,
        path: Tuple[str, ...],
        tree: dict,
    ) -> Optional[graphviz.Digraph]:

        if len(tree) == 0:
            return None

        path_str = "#".join(path)
        print("@ VIZ @", path_str)
        g = graphviz.Digraph(f"cluster_{path_str}" if path_str else None)
        g.attr("graph", rankdir="LR", label=path_str)
        if path_str:
            g.node(name=path_str, label=path_str)

        for k, v in tree.items():
            path_str = "#".join(path + (k,))
            print("@ VIZ @", path_str)
            subgraph = self.build_tree_graph(path + (k,), v)
            if subgraph is None:
                g.node(name=path_str, label=path_str)
            else:
                g.subgraph(subgraph)

        return g

    def visualize(
        self,
        definitions: Set[Definition],
        resolved_references: Set[ResolvedReference],
        output: Optional[Path] = None,
        view: bool = False,
    ):
        g = graphviz.Digraph()
        g.attr("graph", rankdir="LR")

        tree = build_tree(definitions, resolved_references)

        print("@ TRE @", str(tree))

        subgraph = self.build_tree_graph((), tree)
        g.subgraph(subgraph)

        # dedup edges
        edges = set()
        for resolved_reference in resolved_references:
            if resolved_reference is None:
                continue
            reference = resolved_reference.reference
            definition = resolved_reference.definition
            tail_name = "#".join(reference.path + reference.scope)
            head_name = "#".join(
                (definition.path + definition.scope) + (definition.name,)
            )
            print("@ CON @", tail_name, head_name)
            edges.add((tail_name, head_name))

        for tail_name, head_name in edges:
            g.edge(tail_name=tail_name, head_name=head_name)

        g.render(filename=output, format="svg", engine="dot", view=view)
