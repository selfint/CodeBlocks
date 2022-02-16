import argparse
import os
from pathlib import Path
from typing import Optional

from code_blocks.graphviz_visualizer import GraphvizVisualizer
from code_blocks.lsp_client import LspClient
from code_blocks.lsp_server import LspServer
from code_blocks.parser import Parser
from code_blocks.resolver import Resolver


def main(project: Path, output: Optional[Path] = None):
    parser = Parser()

    for root, _, files in os.walk(project):
        for f in files:
            path = Path(root) / f
            if path.suffix == ".py":
                relative_path = path.relative_to(project).parts
                parser.consume(path.read_text(), relative_path)

    definitions, references = parser.definitions, parser.references

    print(f"Got {definitions=}")
    print(f"Got {references=}")

    lsp_server = LspServer(str(project))
    print("LSP server started")

    lsp_client = LspClient(lsp_server)
    print("LSP client connected")

    resolver = Resolver(lsp_client, project.as_uri())

    resolved_references = resolver.resolve(definitions, references)
    print(f"Got {resolved_references=}")

    visualizer = GraphvizVisualizer()
    visualizer.visualize(definitions, references, resolved_references, output)

    print("Shutting down LSP client")
    lsp_client.stop()

    print("Shutting down LSP server")
    lsp_server.stop()

    print("Done")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument("-p", "--project", type=Path, help="Path to project")
    arg_parser.add_argument(
        "-o", "--output", type=Path, help="Path to desired output file", required=False
    )

    args = arg_parser.parse_args()

    project: Path = args.project
    output: Path = args.output

    assert project.is_dir(), "Project path is not a directory"
    assert output is None or not output.exists(), "Output file exists"

    project = project.resolve().absolute()

    main(project, output)