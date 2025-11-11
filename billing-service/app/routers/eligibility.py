from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import logging
from app.database import get_db
from app.schemas import EligibilityCheckRequest, EligibilityCheckResponse
from app.services.eligibility_service import EligibilityService
from app.middleware.auth import require_permission
from app.middleware.observability import eligibility_checks_total

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/eligibility", tags=["Eligibility"])


@router.post("/check", response_model=EligibilityCheckResponse)
def check_eligibility(
    request: EligibilityCheckRequest,
    db: Session = Depends(get_db),
    # Autenticação/Authorização (comentado para desenvolvimento)
    # user_claims: dict = Depends(require_permission("eligibility:check"))
):
    """Verifica elegibilidade do paciente com convênio"""
    try:
        eligibility = EligibilityService.check_eligibility(db, request)
        
        # Métrica de negócio
        result = "eligible" if eligibility.is_eligible else "not_eligible"
        eligibility_checks_total.labels(result=result).inc()
        
        return EligibilityCheckResponse(
            patient_id=eligibility.patient_id,
            insurance_id=eligibility.insurance_id,
            is_eligible=bool(eligibility.is_eligible),
            message=eligibility.message,
            checked_at=eligibility.checked_at if eligibility.checked_at else datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao verificar elegibilidade: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to check eligibility",
                "message": "Erro ao verificar elegibilidade. Verifique os logs para mais detalhes."
            }
        )


@router.get("/history", response_model=List[EligibilityCheckResponse])
def get_eligibility_history(
    patient_id: Optional[str] = Query(None, description="Filtrar por patient_id"),
    insurance_id: Optional[str] = Query(None, description="Filtrar por insurance_id"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Busca histórico de verificações de elegibilidade"""
    history = EligibilityService.get_eligibility_history(
        db,
        patient_id=patient_id,
        insurance_id=insurance_id,
        limit=limit
    )
    
    return [
        EligibilityCheckResponse(
            patient_id=item.patient_id,
            insurance_id=item.insurance_id,
            is_eligible=bool(item.is_eligible),
            message=item.message,
            checked_at=item.checked_at
        )
        for item in history
    ]

