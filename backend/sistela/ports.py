"""Extension contracts only; unverified integrations cannot write output."""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Protocol

from .schemas import LineOut, ProjectOut


@dataclass(frozen=True)
class ExportResult:
    path: Path
    warnings: tuple[str, ...] = ()


class SistelaExporter(Protocol):
    def export(
        self, project: ProjectOut, lines: list[LineOut], destination: Path
    ) -> ExportResult: ...


class DbfArchiveExporter:
    """Production port remains closed; experimental clones use SistelaDbfExporter."""
    status = "EXPERIMENTAL"

    def export(self, project, lines, destination):
        raise NotImplementedError("DBF writing requires a verified SISTELA round-trip test")


class PackageTextExporter:
    def export(self, project, lines, destination):
        raise NotImplementedError("SISTELA package text format is unverified")


@dataclass(frozen=True)
class MappingSuggestion:
    sistela_code: str
    sistela_description: str
    confidence: Decimal
    reason: str


class AiMappingProvider(Protocol):
    def suggest(self, description: str, system_type: str) -> list[MappingSuggestion]: ...


class DisabledAiMappingProvider:
    def suggest(self, description: str, system_type: str) -> list[MappingSuggestion]:
        return []
