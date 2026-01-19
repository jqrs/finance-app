from io import StringIO

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import Transaction
from app.models.account import Account
from app.schemas.csv_import import (
    CSVPreviewRequest,
    CSVPreviewResponse,
    CSVImportRequest,
    CSVImportResponse,
    FormatDetectionResponse,
    ColumnMapping,
    TransactionPreview,
)
from app.services.csv_import import (
    detect_format,
    infer_columns,
    parse_csv,
    generate_import_hash,
    KNOWN_FORMATS,
)

router = APIRouter()


@router.post("/detect", response_model=FormatDetectionResponse)
async def detect_csv_format(file: UploadFile = File(...)):
    """
    Upload a CSV file and detect its format.
    Returns column names, detected format, and suggested mappings.
    """
    content = await file.read()
    content_str = content.decode("utf-8")

    try:
        df = pd.read_csv(StringIO(content_str), nrows=10)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    columns = df.columns.tolist()
    detected = detect_format(df)
    suggestions = infer_columns(df)

    # Build suggested mapping
    suggested_mapping = None
    if detected and detected in KNOWN_FORMATS:
        fmt = KNOWN_FORMATS[detected]
        suggested_mapping = ColumnMapping(
            date=fmt["mapping"]["date"],
            amount=fmt["mapping"].get("amount", ""),
            description=fmt["mapping"]["description"],
            original_description=fmt["mapping"].get("original_description"),
        )
    elif suggestions["date"] and suggestions["amount"] and suggestions["description"]:
        suggested_mapping = ColumnMapping(
            date=suggestions["date"][0],
            amount=suggestions["amount"][0],
            description=suggestions["description"][0],
        )

    # Get sample rows
    sample_rows = df.head(5).to_dict(orient="records")

    return FormatDetectionResponse(
        detected_format=detected,
        columns=columns,
        suggested_mapping=suggested_mapping,
        column_suggestions=suggestions,
        sample_rows=sample_rows,
    )


@router.post("/preview", response_model=CSVPreviewResponse)
async def preview_import(request: CSVPreviewRequest):
    """
    Preview parsed transactions before importing.
    """
    try:
        transactions = parse_csv(
            content=request.content,
            column_mapping=request.column_mapping.model_dump(),
            date_format=request.date_format,
            amount_handling=request.amount_handling,
            debit_column=request.debit_column,
            credit_column=request.credit_column,
            type_column=request.type_column,
            skip_rows=request.skip_rows,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    # Detect format for info
    df = pd.read_csv(StringIO(request.content), nrows=5)
    detected = detect_format(df)

    preview = [
        TransactionPreview(
            date=t["date"],
            amount=t["amount"],
            description=t["description"],
            merchant=t.get("merchant"),
        )
        for t in transactions[:10]
    ]

    return CSVPreviewResponse(
        total_rows=len(transactions),
        preview=preview,
        detected_format=detected,
    )


@router.post("/import", response_model=CSVImportResponse)
async def import_transactions(
    request: CSVImportRequest,
    db: Session = Depends(get_db),
):
    """
    Import transactions from CSV into the database.
    Automatically deduplicates based on hash.
    """
    # Verify account exists
    account = db.query(Account).filter(Account.id == request.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        transactions = parse_csv(
            content=request.content,
            column_mapping=request.column_mapping.model_dump(),
            date_format=request.date_format,
            amount_handling=request.amount_handling,
            debit_column=request.debit_column,
            credit_column=request.credit_column,
            type_column=request.type_column,
            skip_rows=request.skip_rows,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    imported = 0
    skipped = 0
    errors = 0

    for txn in transactions:
        try:
            # Generate hash for deduplication
            import_hash = generate_import_hash(
                date=txn["date"],
                amount=txn["amount"],
                description=txn["description"],
                account_id=request.account_id,
            )

            # Check for duplicate
            existing = db.query(Transaction).filter(
                Transaction.import_hash == import_hash
            ).first()

            if existing:
                skipped += 1
                continue

            # Create new transaction
            new_txn = Transaction(
                account_id=request.account_id,
                date=txn["date"],
                amount=txn["amount"],
                description=txn["description"],
                original_description=txn["original_description"],
                merchant=txn.get("merchant"),
                import_hash=import_hash,
            )
            db.add(new_txn)
            imported += 1

        except Exception as e:
            errors += 1
            continue

    db.commit()

    return CSVImportResponse(
        imported=imported,
        skipped=skipped,
        errors=errors,
    )


@router.get("/formats")
async def list_known_formats():
    """List all known CSV formats that can be auto-detected."""
    formats = []
    for name, info in KNOWN_FORMATS.items():
        formats.append({
            "name": name,
            "columns": list(info["identifier_columns"]),
            "date_format": info["date_format"],
            "amount_handling": info["amount_handling"],
        })
    return formats
