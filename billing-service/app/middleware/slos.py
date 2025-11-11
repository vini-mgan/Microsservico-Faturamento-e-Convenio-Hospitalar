"""
SLOs (Service Level Objectives) e Health Checks Avançados
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
import time
import json
from app.database import get_db, engine
from app.redis_client import get_redis
from app.kafka_producer import kafka_producer
from prometheus_client import Gauge
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])

# Métricas de SLO
service_availability = Gauge(
    'billing_service_availability',
    'Service availability (1 = available, 0 = unavailable)'
)

database_connection_status = Gauge(
    'billing_database_connection_status',
    'Database connection status (1 = connected, 0 = disconnected)'
)

redis_connection_status = Gauge(
    'billing_redis_connection_status',
    'Redis connection status (1 = connected, 0 = disconnected)'
)

kafka_connection_status = Gauge(
    'billing_kafka_connection_status',
    'Kafka connection status (1 = connected, 0 = disconnected)'
)


def check_database() -> Dict[str, Any]:
    """Verifica conexão com banco de dados"""
    try:
        start = time.time()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000
        return {"status": "healthy", "latency_ms": round(latency, 2)}
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


def check_redis() -> Dict[str, Any]:
    """Verifica conexão com Redis"""
    try:
        redis = get_redis()
        if redis is None:
            return {"status": "unhealthy", "error": "Redis client not initialized"}
        start = time.time()
        redis.ping()
        latency = (time.time() - start) * 1000
        return {"status": "healthy", "latency_ms": round(latency, 2)}
    except Exception as e:
        logger.error(f"Redis check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


def check_kafka() -> Dict[str, Any]:
    """Verifica conexão com Kafka"""
    try:
        # Verificar se producer está disponível
        if kafka_producer.producer is None:
            return {"status": "unhealthy", "error": "Kafka producer not initialized"}
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Kafka check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@router.get("/")
def health_check():
    """Health check básico"""
    return {"status": "healthy", "service": "billing-service"}


@router.get("/ready", status_code=status.HTTP_200_OK)
def readiness_check():
    """
    Readiness check - verifica se serviço está pronto para receber tráfego
    SLO: Disponibilidade > 99.9%
    """
    checks = {
        "database": check_database(),
        "redis": check_redis(),
        "kafka": check_kafka()
    }
    
    all_healthy = all(check["status"] == "healthy" for check in checks.values())
    
    # Atualizar métricas
    database_connection_status.set(1 if checks["database"]["status"] == "healthy" else 0)
    redis_connection_status.set(1 if checks["redis"]["status"] == "healthy" else 0)
    kafka_connection_status.set(1 if checks["kafka"]["status"] == "healthy" else 0)
    service_availability.set(1 if all_healthy else 0)
    
    response_data = {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": time.time()
    }
    
    # Retornar 503 se não estiver pronto
    if not all_healthy:
        from fastapi import Response
        return Response(
            content=json.dumps(response_data),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json"
        )
    
    return response_data


@router.get("/live")
def liveness_check():
    """
    Liveness check - verifica se serviço está vivo
    """
    return {
        "status": "alive",
        "service": "billing-service",
        "timestamp": time.time()
    }


# Nota: O endpoint /metrics é montado diretamente no main.py via make_asgi_app()

