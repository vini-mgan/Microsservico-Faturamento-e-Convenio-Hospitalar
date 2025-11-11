from sqlalchemy import Column, String, Numeric, DateTime, Integer, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.database import Base


class ClaimStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"


class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    SETTLED = "settled"
    CANCELLED = "cancelled"


class ClaimItem(Base):
    __tablename__ = "claim_items"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    claim_id = Column(String(50), nullable=False, index=True)
    description = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)  # Código TUSS
    value = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())


class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(String(50), primary_key=True, index=True)
    patient_id = Column(String(50), nullable=False, index=True)
    insurance_id = Column(String(100), nullable=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="BRL")
    status = Column(SQLEnum(ClaimStatus), nullable=False, default=ClaimStatus.PENDING)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(String(50), primary_key=True, index=True)
    claim_id = Column(String(50), nullable=True, index=True)
    patient_id = Column(String(50), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="BRL")
    status = Column(SQLEnum(InvoiceStatus), nullable=False, default=InvoiceStatus.PENDING)
    settled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class EligibilityCheck(Base):
    __tablename__ = "eligibility_checks"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(String(50), nullable=False, index=True)
    insurance_id = Column(String(100), nullable=False, index=True)
    is_eligible = Column(Integer, nullable=False, default=0)  # 0 = false, 1 = true
    message = Column(Text, nullable=True)
    checked_at = Column(DateTime, server_default=func.now())







