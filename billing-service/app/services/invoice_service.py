from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uuid
from app.models import Invoice, InvoiceStatus
from app.schemas import InvoiceCreate, InvoiceUpdate
from app.kafka_producer import kafka_producer


class InvoiceService:
    @staticmethod
    def create_invoice(db: Session, invoice_data: InvoiceCreate) -> Invoice:
        """Cria uma nova invoice"""
        invoice_id = f"INV{uuid.uuid4().hex[:6].upper()}"
        
        invoice = Invoice(
            id=invoice_id,
            claim_id=invoice_data.claim_id,
            patient_id=invoice_data.patient_id,
            amount=invoice_data.amount,
            currency=invoice_data.currency,
            status=InvoiceStatus.PENDING
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        return invoice
    
    @staticmethod
    def get_invoice(db: Session, invoice_id: str) -> Optional[Invoice]:
        """Busca uma invoice por ID"""
        return db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    @staticmethod
    def get_invoices(
        db: Session,
        patient_id: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Invoice]:
        """Lista invoices com filtros opcionais"""
        query = db.query(Invoice)
        
        if patient_id:
            query = query.filter(Invoice.patient_id == patient_id)
        if status:
            query = query.filter(Invoice.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def settle_invoice(db: Session, invoice_id: str) -> Optional[Invoice]:
        """Settles (liquida) uma invoice e publica evento"""
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return None
        
        if invoice.status == InvoiceStatus.SETTLED:
            return invoice
        
        invoice.status = InvoiceStatus.SETTLED
        invoice.settled_at = datetime.utcnow()
        
        db.commit()
        db.refresh(invoice)
        
        # Publicar evento InvoiceSettled
        event_data = {
            "id": invoice.id,
            "claimId": invoice.claim_id,
            "patientId": invoice.patient_id,
            "amount": float(invoice.amount),
            "currency": invoice.currency,
            "status": invoice.status.value,
            "settledAt": invoice.settled_at.isoformat() + "Z" if invoice.settled_at else None,
            "createdAt": invoice.created_at.isoformat() + "Z"
        }
        kafka_producer.publish_invoice_settled(event_data)
        
        return invoice
    
    @staticmethod
    def update_invoice(db: Session, invoice_id: str, invoice_update: InvoiceUpdate) -> Optional[Invoice]:
        """Atualiza uma invoice"""
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return None
        
        if invoice_update.status:
            invoice.status = invoice_update.status
        
        db.commit()
        db.refresh(invoice)
        return invoice







