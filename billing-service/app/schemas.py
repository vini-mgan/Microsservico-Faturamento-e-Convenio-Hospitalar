from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models import ClaimStatus, InvoiceStatus


# Claim Schemas
class ClaimItemCreate(BaseModel):
    description: str
    code: Optional[str] = None
    value: float
    quantity: int = 1


class ClaimItemResponse(BaseModel):
    description: str
    code: Optional[str] = None
    value: float
    quantity: int

    class Config:
        from_attributes = True


class ClaimCreate(BaseModel):
    patient_id: str
    insurance_id: Optional[str] = None
    amount: float
    currency: str = "BRL"
    items: List[ClaimItemCreate]


class ClaimUpdate(BaseModel):
    status: Optional[ClaimStatus] = None
    insurance_id: Optional[str] = None


class ClaimResponse(BaseModel):
    id: str
    patient_id: str
    insurance_id: Optional[str] = None
    amount: float
    currency: str
    status: ClaimStatus
    items: List[ClaimItemResponse]
    created_at: datetime

    class Config:
        from_attributes = True


# Invoice Schemas
class InvoiceCreate(BaseModel):
    claim_id: Optional[str] = None
    patient_id: str
    amount: float
    currency: str = "BRL"


class InvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatus] = None


class InvoiceResponse(BaseModel):
    id: str
    claim_id: Optional[str] = None
    patient_id: str
    amount: float
    currency: str
    status: InvoiceStatus
    settled_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Eligibility Schemas
class EligibilityCheckRequest(BaseModel):
    patient_id: str
    insurance_id: str


class EligibilityCheckResponse(BaseModel):
    patient_id: str
    insurance_id: str
    is_eligible: bool
    message: Optional[str] = None
    checked_at: datetime

    class Config:
        from_attributes = True







