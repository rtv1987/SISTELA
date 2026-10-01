from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def no_float(value):
    if isinstance(value, (float, bool)):
        raise ValueError("Dešimtainius skaičius siųskite tekstu, pvz. '0.1'.")
    return value


Quantity = Annotated[
    Decimal, BeforeValidator(no_float), Field(ge=0, max_digits=24, decimal_places=6)
]
Price = Annotated[Decimal, BeforeValidator(no_float), Field(ge=0, max_digits=24, decimal_places=6)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProjectCreate(InputModel):
    name: str = Field(min_length=1, max_length=200)
    customer: str = Field(default="", max_length=300)
    system_type: str = Field(min_length=1, max_length=100)


class ProjectOut(ProjectCreate):
    deleted_at: str | None
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    created_at: str
    updated_at: str


class LineCreate(InputModel):
    system_type: str = Field(default="", max_length=100)
    line_type: Literal["Material", "Work", "Equipment", "Other"] = "Other"
    project_description: str = Field(min_length=1, max_length=4000)
    technical_reference: str = Field(default="", max_length=500)
    unit: str = Field(default="", max_length=40)
    quantity: Quantity = Decimal("0")
    output_description: str = Field(min_length=1, max_length=4000)
    material_price: Price | None = None
    work_price: Price | None = None
    notes: str = Field(default="", max_length=4000)
    sistela_code: str = Field(default="", max_length=100)
    sistela_original_description: str = Field(default="", max_length=4000)


class LineEdit(LineCreate):
    """PUT with full editable content and optimistic version for future autosave."""

    version: int = Field(ge=1)


class LineOut(LineCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    section_id: str | None
    source_position: str
    sistela_code: str
    sistela_original_description: str
    confidence: Decimal | None
    mapping_status: str
    source_document_id: str | None
    source_page: int | None
    source_raw_text: str
    sort_order: int
    version: int
    created_at: str
    updated_at: str
    entered_at: str | None
    deleted_at: str | None
    review_data: dict


class GridEdit(InputModel):
    id: str
    version: int = Field(ge=1)
    values: dict


class GridDelete(InputModel):
    id: str
    version: int = Field(ge=1)


class GridCommand(InputModel):
    edits: list[GridEdit] = Field(default_factory=list, max_length=500)
    creates: list[LineCreate] = Field(default_factory=list, max_length=500)
    deletes: list[GridDelete] = Field(default_factory=list, max_length=500)
    duplicates: list[GridDelete] = Field(default_factory=list, max_length=500)


class ImportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    source_document_id: str
    status: str
    parser_version: str
    started_at: str
    completed_at: str | None
    error_message: str | None
    rows_detected: int
    warnings: list[dict]
    pages: list[int]
    elapsed_ms: int | None
    options: dict = Field(default_factory=dict)
