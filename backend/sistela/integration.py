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
        IntegrationCapability("package_text_export", "TXT eksportas (EXPERIMENTAL)", "analysis_only", False, False,
                              "Official 2011 package grammar subset with local parser round-trip. Real SISTELA acceptance pending.",
                              "Experimental export only; parameter 89 required, unsupported forms blocked."),
        IntegrationCapability("normative_read", "SISTELA normatyvinė bazė", "available", True, False,
                              "Read-only DBF/FPT import with provenance and local FTS search.",
                              "Licensed files supplied locally; unresolved units and relationships remain explicit."),
        IntegrationCapability("dbf_write", "Eksperimentinis DBF eksportas (EXPERIMENTAL)", "analysis_only", False, False,
                              "Golden archive accepted by SISTELA (customer report); regenerated clone still unverified.", "Clone experiments only. Project export blocked on real acceptance and unknown calculations/IDs."),
    )]
