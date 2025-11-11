from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
from app.database import get_db
from app.schemas import InvoiceCreate, InvoiceUpdate, InvoiceResponse
from app.services.invoice_service import InvoiceService
from app.models import InvoiceStatus
from app.middleware.auth import require_permission
from app.middleware.observability import invoices_settled_total

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post("/", response_model=InvoiceResponse, status_code=201)
def create_invoice(invoice: InvoiceCreate, db: Session = Depends(get_db)):
    """Cria uma nova invoice (conta)"""
    try:
        created_invoice = InvoiceService.create_invoice(db, invoice)
        return created_invoice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar invoice: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to create invoice",
                "message": "Erro ao criar invoice. Verifique os logs para mais detalhes."
            }
        )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    """Busca uma invoice por ID"""
    invoice = InvoiceService.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice não encontrada")
    return invoice


@router.get("/", response_model=List[InvoiceResponse])
def list_invoices(
    patient_id: Optional[str] = Query(None, description="Filtrar por patient_id"),
    status: Optional[InvoiceStatus] = Query(None, description="Filtrar por status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Lista invoices com filtros opcionais"""
    invoices = InvoiceService.get_invoices(db, patient_id=patient_id, status=status, skip=skip, limit=limit)
    return invoices


@router.post("/{invoice_id}/settle", response_model=InvoiceResponse)
def settle_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    # Autenticação/Authorização (comentado para desenvolvimento)
    # user_claims: dict = Depends(require_permission("invoices:settle"))
):
    """Settles (liquida) uma invoice"""
    try:
        invoice = InvoiceService.settle_invoice(db, invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice não encontrada")
        # Métrica de negócio
        invoices_settled_total.inc()
        return invoice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao liquidar invoice: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to settle invoice",
                "message": "Erro ao liquidar invoice. Verifique os logs para mais detalhes."
            }
        )


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(invoice_id: str, invoice_update: InvoiceUpdate, db: Session = Depends(get_db)):
    """Atualiza uma invoice"""
    invoice = InvoiceService.update_invoice(db, invoice_id, invoice_update)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice não encontrada")
    return invoice

