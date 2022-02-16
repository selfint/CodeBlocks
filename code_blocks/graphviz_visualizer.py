from collections import defaultdict
from pathlib import Path
import graphviz
from code_blocks.types import Definition, Reference, ResolvedReference
from typing import DefaultDict, Dict, List, Optional, Set, Tuple


class GraphvizVisualizer:
    def __init__(self) -> None:
        pass

    @staticmethod
    def definition_to_id(definition: Definition) -> str:
        return "#".join(
            ["#".join(definition.path), "#".join(definition.scope), definition.name]
        )

    @staticmethod
    def reference_to_id(reference: Reference) -> str:
        return "#".join(
            [
                "#".join(reference.path),
                "#".join(reference.scope),
            ]
        )

    def visualize(
        self,
        definitions: Set[Definition],
        references: Set[Reference],
        resolved_references: Set[ResolvedReference],
        output: Optional[Path] = None,
    ):
        g = graphviz.Digraph("G", filename=output, format="png", engine="dot")
        g.attr("graph", rankdir="LR")

        files: DefaultDict[
            Tuple[str, ...], Tuple[Set[Definition], Set[Reference]]
        ] = defaultdict(lambda: (set(), set()))
        for d in definitions:
            files[d.path][0].add(d)
        for r in references:
            files[r.path][1].add(r)

        for path, (definitions, references) in files.items():
            path_str = "_".join(path)
            subgraph = graphviz.Digraph(f"cluster_{path_str}")
            subgraph.attr("graph", rankdir="LR")
            subgraph.attr("graph", label=path_str)

            for definition in definitions:
                label = (
                    "#".join(
                        [
                            "#".join(definition.path),
                            "#".join(definition.scope),
                        ]
                    )
                    + "#"
                    + definition.kind
                    + " "
                    + definition.name
                )
                subgraph.node(
                    name=self.definition_to_id(definition),
                    label=label,
                )

            for reference in references:
                label = "#".join(
                    [
                        "#".join(reference.path),
                        "#".join(reference.scope),
                    ]
                )
                subgraph.node(
                    name=self.reference_to_id(reference),
                    label=label,
                )

            g.subgraph(subgraph)

        for resolved_reference in resolved_references:
            if resolved_reference is None:
                continue
            g.edge(
                tail_name=self.reference_to_id(resolved_reference.reference),
                head_name=self.definition_to_id(resolved_reference.definition),
            )

        g.view()
