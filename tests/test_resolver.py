from typing import Set

from code_blocks.connector import Connector
from code_blocks.types import Definition, Reference, ResolvedReference


def assert_got_expected_resolved_references_from_definitions_and_references(
    definitions: Set[Definition],
    references: Set[Reference],
    expected_resolved_references: Set[ResolvedReference],
):
    connector = Connector()
    connector.update_definitions
