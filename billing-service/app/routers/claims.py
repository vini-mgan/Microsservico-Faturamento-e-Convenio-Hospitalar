from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
from app.database import get_db
from app.schemas import ClaimCreate, ClaimUpdate, ClaimResponse, ClaimItemResponse
from app.services.claim_service import ClaimService
from app.models import ClaimStatus
from app.middleware.auth import require_permission
from app.middleware.observability import claims_created_total

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/claims", tags=["Claims"])


@router.post("/", response_model=ClaimResponse, status_code=201)
def create_claim(
    claim: ClaimCreate,
    db: Session = Depends(get_db),
    # Autenticação/Authorização (comentado para desenvolvimento)
    # user_claims: dict = Depends(require_permission("claims:create"))
):
    """Cria um novo claim (guia)"""
    try:
        created_claim = ClaimService.create_claim(db, claim)
        # Métrica de negócio
        claims_created_total.inc()
    except HTTPException:
        # Re-raise HTTPExceptions (já tratadas)
        raise
    except Exception as e:
        logger.error(f"Erro ao criar claim: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to create claim",
                "message": "Erro ao criar claim. Verifique os logs para mais detalhes."
            }
        )
    
    # Buscar itens para resposta
    items = ClaimService.get_claim_items(db, created_claim.id)
    claim_dict = {
        "id": created_claim.id,
        "patient_id": created_claim.patient_id,
        "insurance_id": created_claim.insurance_id,
        "amount": float(created_claim.amount),
        "currency": created_claim.currency,
        "status": created_claim.status,
        "items": [
            ClaimItemResponse(
                description=item.description,
                code=item.code,
                value=float(item.value),
                quantity=item.quantity
            )
            for item in items
        ],
        "created_at": created_claim.created_at
    }
    return claim_dict


@router.get("/{claim_id}", response_model=ClaimResponse)
def get_claim(claim_id: str, db: Session = Depends(get_db)):
    """Busca um claim por ID"""
    claim = ClaimService.get_claim(db, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim não encontrado")
    
    items = ClaimService.get_claim_items(db, claim_id)
    claim_dict = {
        "id": claim.id,
        "patient_id": claim.patient_id,
        "insurance_id": claim.insurance_id,
        "amount": float(claim.amount),
        "currency": claim.currency,
        "status": claim.status,
        "items": [
            ClaimItemResponse(
                description=item.description,
                code=item.code,
                value=float(item.value),
                quantity=item.quantity
            )
            for item in items
        ],
        "created_at": claim.created_at
    }
    return claim_dict


@router.get("/", response_model=List[ClaimResponse])
def list_claims(
    patient_id: Optional[str] = Query(None, description="Filtrar por patient_id"),
    status: Optional[ClaimStatus] = Query(None, description="Filtrar por status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Lista claims com filtros opcionais"""
    claims = ClaimService.get_claims(db, patient_id=patient_id, status=status, skip=skip, limit=limit)
    
    result = []
    for claim in claims:
        items = ClaimService.get_claim_items(db, claim.id)
        result.append({
            "id": claim.id,
            "patient_id": claim.patient_id,
            "insurance_id": claim.insurance_id,
            "amount": float(claim.amount),
            "currency": claim.currency,
            "status": claim.status,
            "items": [
                ClaimItemResponse(
                    description=item.description,
                    code=item.code,
                    value=float(item.value),
                    quantity=item.quantity
                )
                for item in items
            ],
            "created_at": claim.created_at
        })
    
    return result


@router.patch("/{claim_id}", response_model=ClaimResponse)
def update_claim(claim_id: str, claim_update: ClaimUpdate, db: Session = Depends(get_db)):
    """Atualiza um claim"""
    claim = ClaimService.update_claim(db, claim_id, claim_update)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim não encontrado")
    
    items = ClaimService.get_claim_items(db, claim_id)
    claim_dict = {
        "id": claim.id,
        "patient_id": claim.patient_id,
        "insurance_id": claim.insurance_id,
        "amount": float(claim.amount),
        "currency": claim.currency,
        "status": claim.status,
        "items": [
            ClaimItemResponse(
                description=item.description,
                code=item.code,
                value=float(item.value),
                quantity=item.quantity
            )
            for item in items
        ],
        "created_at": claim.created_at
    }
    return claim_dict

