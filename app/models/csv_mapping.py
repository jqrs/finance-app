from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class CSVMapping(Base):
    """Store column mappings for different CSV formats."""
    __tablename__ = "csv_mappings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)

    # Column mapping as JSON
    # {"date": "Transaction Date", "amount": "Amount", "description": "Description"}
    column_mapping = Column(JSON, nullable=False)

    # Date format string, e.g., "%m/%d/%Y" or "%Y-%m-%d"
    date_format = Column(String(50), default="%Y-%m-%d")

    # How to determine amount sign
    # "signed" = amount column has sign
    # "separate" = debit/credit in separate columns
    # "type_column" = a column indicates debit/credit
    amount_handling = Column(String(20), default="signed")
    debit_column = Column(String(100))
    credit_column = Column(String(100))
    type_column = Column(String(100))

    # Skip header rows
    skip_rows = Column(Integer, default=0)

    account = relationship("Account", back_populates="csv_mappings")
