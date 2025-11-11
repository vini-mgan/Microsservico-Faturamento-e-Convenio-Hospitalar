from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import datetime
import uuid
from app.models import Claim, ClaimItem, ClaimStatus
from app.schemas import ClaimCreate, ClaimUpdate, ClaimItemCreate
from app.kafka_producer import kafka_producer


class ClaimService:
    @staticmethod
    def create_claim(db: Session, claim_data: ClaimCreate) -> Claim:
        """Cria um novo claim"""
        claim_id = f"CLM{uuid.uuid4().hex[:6].upper()}"
        
        # Criar claim
        claim = Claim(
            id=claim_id,
            patient_id=claim_data.patient_id,
            insurance_id=claim_data.insurance_id,
            amount=claim_data.amount,
            currency=claim_data.currency,
            status=ClaimStatus.PENDING
        )
        db.add(claim)
        db.flush()
        
        # Criar itens do claim
        for item_data in claim_data.items:
            item = ClaimItem(
                claim_id=claim_id,
                description=item_data.description,
                code=item_data.code,
                value=item_data.value,
                quantity=item_data.quantity
            )
            db.add(item)
        
        db.commit()
        db.refresh(claim)
        
        # Publicar evento ClaimSubmitted
        claim_items = db.query(ClaimItem).filter(ClaimItem.claim_id == claim_id).all()
        event_data = {
            "id": claim_id,
            "patientId": claim.patient_id,
            "insuranceId": claim.insurance_id,
            "amount": float(claim.amount),
            "currency": claim.currency,
            "status": claim.status.value,
            "items": [
                {
                    "description": item.description,
                    "code": item.code,
                    "value": float(item.value),
                    "quantity": item.quantity
                }
                for item in claim_items
            ],
            "createdAt": claim.created_at.isoformat() + "Z"
        }
        kafka_producer.publish_claim_submitted(event_data)
        
        return claim
    
    @staticmethod
    def get_claim(db: Session, claim_id: str) -> Optional[Claim]:
        """Busca um claim por ID"""
        return db.query(Claim).filter(Claim.id == claim_id).first()
    
    @staticmethod
    def get_claims(
        db: Session,
        patient_id: Optional[str] = None,
        status: Optional[ClaimStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Claim]:
        """Lista claims com filtros opcionais"""
        query = db.query(Claim)
        
        if patient_id:
            query = query.filter(Claim.patient_id == patient_id)
        if status:
            query = query.filter(Claim.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_claim(db: Session, claim_id: str, claim_update: ClaimUpdate) -> Optional[Claim]:
        """Atualiza um claim"""
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            return None
        
        if claim_update.status:
            claim.status = claim_update.status
        if claim_update.insurance_id is not None:
            claim.insurance_id = claim_update.insurance_id
        
        db.commit()
        db.refresh(claim)
        return claim
    
    @staticmethod
    def get_claim_items(db: Session, claim_id: str) -> List[ClaimItem]:
        """Busca itens de um claim"""
        return db.query(ClaimItem).filter(ClaimItem.claim_id == claim_id).all()







