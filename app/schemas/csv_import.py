from typing import Optional

from pydantic import BaseModel


class ColumnMapping(BaseModel):
    date: str
    amount: str
    description: str
    original_description: Optional[str] = None
    category: Optional[str] = None


class CSVPreviewRequest(BaseModel):
    content: str
    column_mapping: ColumnMapping
    date_format: str = "auto"
    amount_handling: str = "signed"  # signed, separate, type_column
    debit_column: Optional[str] = None
    credit_column: Optional[str] = None
    type_column: Optional[str] = None
    skip_rows: int = 0


class CSVImportRequest(BaseModel):
    account_id: int
    content: str
    column_mapping: ColumnMapping
    date_format: str = "auto"
    amount_handling: str = "signed"
    debit_column: Optional[str] = None
    credit_column: Optional[str] = None
    type_column: Optional[str] = None
    skip_rows: int = 0


class TransactionPreview(BaseModel):
    date: str
    amount: float
    description: str
    merchant: Optional[str] = None


class CSVPreviewResponse(BaseModel):
    total_rows: int
    preview: list[TransactionPreview]
    detected_format: Optional[str] = None


class CSVImportResponse(BaseModel):
    imported: int
    skipped: int
    errors: int


class FormatDetectionResponse(BaseModel):
    detected_format: Optional[str] = None
    columns: list[str]
    suggested_mapping: Optional[ColumnMapping] = None
    column_suggestions: dict[str, list[str]]
    sample_rows: list[dict]
