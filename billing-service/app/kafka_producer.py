import json
import logging
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
from app.config import settings

logger = logging.getLogger(__name__)


def generate_event_id() -> str:
    """Gera eventId no formato: evt-{timestamp}-{random_string}
    Segue o padrão: evt-${Date.now()}-${Math.random().toString(36).substr(2, 9)}
    """
    import random
    import string
    # Date.now() retorna milissegundos desde epoch
    timestamp = int(datetime.now().timestamp() * 1000)
    # Math.random().toString(36).substr(2, 9) gera string alfanumérica base36 de 9 chars
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
    return f"evt-{timestamp}-{random_str}"


class KafkaEventProducer:
    def __init__(self):
        self._producer = None
        self.topic = settings.KAFKA_TOPIC_BILLING_EVENTS
    
    @property
    def producer(self):
        """Lazy initialization do producer Kafka"""
        if self._producer is None:
            try:
                self._producer = KafkaProducer(
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS.split(','),
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    api_version=(0, 10, 1)
                )
            except Exception as e:
                logger.warning(f"Kafka não disponível: {e}. Eventos não serão publicados.")
                self._producer = None
        return self._producer
    
    def _publish_event(self, event_type: str, resource_type: str, data: dict):
        """Publica evento no padrão definido"""
        if self.producer is None:
            logger.warning(f"Kafka não disponível. Evento {event_type} não publicado.")
            return False
        
        event = {
            "eventId": generate_event_id(),
            "eventType": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": settings.SERVICE_NAME,
            "resourceType": resource_type,
            "data": data
        }
        
        try:
            future = self.producer.send(
                self.topic,
                key=data.get("id", ""),
                value=event
            )
            future.get(timeout=10)
            logger.info(f"Evento publicado: {event_type} - {data.get('id', 'N/A')}")
            return True
        except (KafkaError, Exception) as e:
            logger.error(f"Erro ao publicar evento no Kafka: {e}")
            return False
    
    def publish_claim_submitted(self, claim_data: dict):
        """Publica evento ClaimSubmitted"""
        return self._publish_event(
            event_type="ClaimSubmitted",
            resource_type="Claim",
            data=claim_data
        )
    
    def publish_invoice_settled(self, invoice_data: dict):
        """Publica evento InvoiceSettled"""
        return self._publish_event(
            event_type="InvoiceSettled",
            resource_type="Invoice",
            data=invoice_data
        )
    
    def close(self):
        if self._producer is not None:
            self._producer.close()


# Instância global
kafka_producer = KafkaEventProducer()

