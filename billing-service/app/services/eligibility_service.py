from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.models import EligibilityCheck
from app.redis_client import get_redis
from app.schemas import EligibilityCheckRequest
import json
import logging

logger = logging.getLogger(__name__)


class EligibilityService:
    @staticmethod
    def check_eligibility(db: Session, request: EligibilityCheckRequest) -> EligibilityCheck:
        """Verifica elegibilidade do paciente com convênio"""
        redis = get_redis()
        cache_key = f"eligibility:{request.patient_id}:{request.insurance_id}"
        
        # Tentar buscar do cache Redis (se disponível)
        if redis:
            try:
                cached = redis.get(cache_key)
                if cached:
                    cached_data = json.loads(cached)
                    logger.info(f"Elegibilidade encontrada no cache para {request.patient_id}")
                    # Criar objeto EligibilityCheck com checked_at atual
                    eligibility = EligibilityCheck(
                        id=0,
                        patient_id=request.patient_id,
                        insurance_id=request.insurance_id,
                        is_eligible=cached_data["is_eligible"],
                        message=cached_data.get("message")
                    )
                    # Definir checked_at manualmente (não vem do banco)
                    eligibility.checked_at = datetime.utcnow()
                    return eligibility
            except Exception as e:
                logger.warning(f"Erro ao acessar cache Redis: {e}")
        
        # Simular verificação de elegibilidade (aqui seria integração TISS/ANS)
        # Por padrão, assumimos elegível se não houver restrições
        is_eligible = True
        message = "Paciente elegível para o procedimento"
        
        # Verificar tabelas TUSS no Redis (cache) - se disponível
        if redis:
            try:
                tuss_cache_key = f"tuss:{request.insurance_id}"
                tuss_data = redis.get(tuss_cache_key)
                if tuss_data:
                    # Processar dados TUSS se necessário
                    pass
            except Exception as e:
                logger.warning(f"Erro ao acessar cache TUSS: {e}")
        
        # Criar registro de verificação
        eligibility = EligibilityCheck(
            patient_id=request.patient_id,
            insurance_id=request.insurance_id,
            is_eligible=1 if is_eligible else 0,
            message=message
        )
        db.add(eligibility)
        db.commit()
        db.refresh(eligibility)
        
        # Cachear resultado (TTL de 1 hora) - se Redis estiver disponível
        if redis:
            try:
                cache_data = {
                    "is_eligible": is_eligible,
                    "message": message
                }
                redis.setex(cache_key, 3600, json.dumps(cache_data))
            except Exception as e:
                logger.warning(f"Erro ao salvar no cache Redis: {e}")
        
        return eligibility
    
    @staticmethod
    def get_eligibility_history(
        db: Session,
        patient_id: Optional[str] = None,
        insurance_id: Optional[str] = None,
        limit: int = 10
    ):
        """Busca histórico de verificações de elegibilidade"""
        query = db.query(EligibilityCheck)
        
        if patient_id:
            query = query.filter(EligibilityCheck.patient_id == patient_id)
        if insurance_id:
            query = query.filter(EligibilityCheck.insurance_id == insurance_id)
        
        return query.order_by(EligibilityCheck.checked_at.desc()).limit(limit).all()




