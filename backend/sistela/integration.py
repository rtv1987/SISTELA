"""Evidence-based capabilities. This is not a user-editable feature-flag registry."""
from dataclasses import asdict, dataclass
from typing import Literal


@dataclass(frozen=True)
class IntegrationCapability:
    id: str
    name: str
    status: Literal["available", "analysis_only", "blocked"]
    production: bool
    writes_to_sistela: bool
    evidence: str
    limitation: str


def capabilities() -> list[dict]:
    return [asdict(item) for item in (
        IntegrationCapability("manual_entry", "SISTELA Entry Mode", "available", True, False,
                              "Local clipboard and user-confirmed progress.",
                              "The user enters values in SISTELA and verifies normative units."),
        IntegrationCapability("xlsx", "Excel darbo lentelė", "available", True, False,
                              "Local XLSX import/export round-trip tests.",
                              "A working spreadsheet, not a verified SISTELA import format."),
        IntegrationCapability("dbf_read", "Istorinių DBF importas", "available", True, False,
                              "Six original archives, hashes, schemas and sd/dd joins tested.",
                              "Read-only sd/dd/nd profile with review and provenance; not a normative catalogue."),
        IntegrationCapability("package_text_read", "Package Text analizė (EXPERIMENTAL)", "analysis_only", False, False,
                              "Lossless text/line analysis; no authentic package sample provided.",
                              "Semantic grammar, field meanings and compatibility are UNKNOWN."),
        IntegrationCapability("package_text_export", "Package Text eksportas", "blocked", False, False,
                              "No verified grammar or SISTELA round-trip.",
                              "Experimental adapter fails closed; absent from production export routes."),
        IntegrationCapability("dbf_write", "Eksperimentinis DBF eksportas (EXPERIMENTAL)", "analysis_only", False, False,
                              "Golden archive accepted by SISTELA (customer report); regenerated clone still unverified.", "Clone experiments only. Project export blocked on real acceptance and unknown calculations/IDs."),
    )]
