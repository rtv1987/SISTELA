"""Domain storage. Historical descriptions never become catalogue truth implicitly."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


def new_id() -> str:
    return str(uuid4())


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExactDecimal(TypeDecorator):
    """SQLite NUMERIC would silently introduce binary float rounding."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, float):
            raise ValueError("Use Decimal or decimal text, not float")
        value = Decimal(value)
        if not value.is_finite():
            raise ValueError("Decimal must be finite")
        return format(value, "f")

    def process_result_value(self, value, dialect):
        return Decimal(value) if value is not None else None


class Base(DeclarativeBase):
    pass


class Identity:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)


class Timestamps:
    created_at: Mapped[str] = mapped_column(default=utc_now)
    updated_at: Mapped[str] = mapped_column(default=utc_now, onupdate=utc_now)


class Project(Identity, Timestamps, Base):
    __tablename__ = "projects"
    name: Mapped[str]
    customer: Mapped[str] = mapped_column(default="")
    system_type: Mapped[str]
    status: Mapped[str] = mapped_column(default="draft")


class SourceDocument(Identity, Base):
    __tablename__ = "source_documents"
    __table_args__ = (
        UniqueConstraint("project_id", "checksum"),
        UniqueConstraint("project_id", "id"),
    )
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    filename: Mapped[str]
    file_type: Mapped[str]
    checksum: Mapped[str]
    storage_path: Mapped[str]
    page_count: Mapped[int | None]
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(default=utc_now)


class EstimateSection(Identity, Base):
    __tablename__ = "estimate_sections"
    __table_args__ = (UniqueConstraint("project_id", "id"),)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str]
    sort_order: Mapped[int] = mapped_column(default=0)


class EstimateLine(Identity, Timestamps, Base):
    __tablename__ = "estimate_lines"
    __table_args__ = (
        UniqueConstraint("project_id", "id"),
        ForeignKeyConstraint(
            ["project_id", "section_id"], ["estimate_sections.project_id", "estimate_sections.id"]
        ),
        ForeignKeyConstraint(
            ["project_id", "source_document_id"],
            ["source_documents.project_id", "source_documents.id"],
        ),
        CheckConstraint("line_type IN ('Material','Work','Other')"),
        CheckConstraint("mapping_status IN ('unmapped','suggested','confirmed')"),
        CheckConstraint("source_page IS NULL OR source_page > 0"),
        Index("ix_lines_project_order", "project_id", "sort_order"),
    )
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    section_id: Mapped[str | None]
    system_type: Mapped[str] = mapped_column(default="")
    line_type: Mapped[str] = mapped_column(default="Other")
    source_position: Mapped[str] = mapped_column(default="")
    project_description: Mapped[str] = mapped_column(Text)
    technical_reference: Mapped[str] = mapped_column(default="")
    unit: Mapped[str] = mapped_column(default="")
    quantity: Mapped[Decimal] = mapped_column(ExactDecimal, default=Decimal("0"))
    sistela_code: Mapped[str] = mapped_column(default="")
    sistela_original_description: Mapped[str] = mapped_column(Text, default="")
    output_description: Mapped[str] = mapped_column(Text)
    material_price: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    work_price: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    confidence: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    mapping_status: Mapped[str] = mapped_column(default="unmapped")
    source_document_id: Mapped[str | None]
    source_page: Mapped[int | None]
    source_raw_text: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(default=0)
    version: Mapped[int] = mapped_column(default=1)
    deleted_at: Mapped[str | None]
    entered_at: Mapped[str | None]


class SistelaMapping(Identity, Timestamps, Base):
    __tablename__ = "sistela_mappings"
    __table_args__ = (
        UniqueConstraint("system_type", "normalized_source_text", "source_unit", "sistela_code", name="uq_mapping_source_unit_code"),
        CheckConstraint("usage_count >= 0 AND confirmed_count >= 0", name="ck_mapping_counts"),
    )
    system_type: Mapped[str]
    source_text: Mapped[str]
    source_unit: Mapped[str] = mapped_column(default="")
    normalized_source_text: Mapped[str]
    sistela_code: Mapped[str]
    sistela_description: Mapped[str] = mapped_column(Text, default="")
    usage_count: Mapped[int] = mapped_column(default=0)
    confirmed_count: Mapped[int] = mapped_column(default=0)
    last_used_at: Mapped[str | None]


class ImportRun(Identity, Base):
    __tablename__ = "import_runs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "source_document_id"],
            ["source_documents.project_id", "source_documents.id"],
        ),
        CheckConstraint("status IN ('running','completed','needs_review','failed')"),
    )
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    source_document_id: Mapped[str]
    status: Mapped[str] = mapped_column(default="running")
    parser_version: Mapped[str]
    started_at: Mapped[str] = mapped_column(default=utc_now)
    completed_at: Mapped[str | None]
    error_message: Mapped[str | None]
    rows_detected: Mapped[int] = mapped_column(default=0)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    pages: Mapped[list] = mapped_column(JSON, default=list)
    elapsed_ms: Mapped[int | None]
    options: Mapped[dict] = mapped_column(JSON, default=dict)


class Requirement(Identity, Base):
    __tablename__ = "requirements"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "related_estimate_line_id"],
            ["estimate_lines.project_id", "estimate_lines.id"],
        ),
        ForeignKeyConstraint(
            ["project_id", "source_document_id"],
            ["source_documents.project_id", "source_documents.id"],
        ),
    )
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    related_estimate_line_id: Mapped[str | None]
    source_document_id: Mapped[str | None]
    source_page: Mapped[int | None]
    requirement_text: Mapped[str] = mapped_column(Text)
    requirement_type: Mapped[str]


class GridChange(Identity, Base):
    __tablename__ = "grid_changes"
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    before: Mapped[dict] = mapped_column(JSON)
    after_versions: Mapped[dict] = mapped_column(JSON)
    undone: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[str] = mapped_column(default=utc_now)


class MappingConfirmation(Identity, Base):
    __tablename__ = "mapping_confirmations"
    mapping_id: Mapped[str] = mapped_column(ForeignKey("sistela_mappings.id"))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    line_id: Mapped[str] = mapped_column(ForeignKey("estimate_lines.id"))
    previous_code: Mapped[str]
    selected_code: Mapped[str]
    source_text: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=utc_now)
