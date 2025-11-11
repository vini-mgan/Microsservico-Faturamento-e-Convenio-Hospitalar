from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import time
import logging
import json
from prometheus_client import Counter, Histogram, Gauge
from typing import Callable

logger = logging.getLogger(__name__)

# Métricas Prometheus
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint']
)

# Métricas de negócio
claims_created_total = Counter(
    'billing_claims_created_total',
    'Total claims created'
)

invoices_settled_total = Counter(
    'billing_invoices_settled_total',
    'Total invoices settled'
)

eligibility_checks_total = Counter(
    'billing_eligibility_checks_total',
    'Total eligibility checks',
    ['result']
)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware para observabilidade: logging estruturado, métricas e tracing"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        # Iniciar métrica de requests em progresso
        http_requests_in_progress.labels(
            method=request.method,
            endpoint=request.url.path
        ).inc()
        
        start_time = time.time()
        
        # Logging estruturado da requisição
        log_data = {
            "timestamp": time.time(),
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        logger.info(f"Request iniciada: {json.dumps(log_data)}")
        
        try:
            response = await call_next(request)
            
            # Calcular duração
            duration = time.time() - start_time
            
            # Atualizar métricas
            status_code = response.status_code
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            # Logging estruturado da resposta
            log_data.update({
                "status_code": status_code,
                "duration_seconds": duration,
                "response_size": response.headers.get("content-length", 0)
            })
            logger.info(f"Request completada: {json.dumps(log_data)}")
            
            # Adicionar headers de tracing
            response.headers["X-Request-Duration"] = str(duration)
            response.headers["X-Request-Id"] = request.headers.get("X-Request-Id", "unknown")
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Métricas de erro
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=500
            ).inc()
            
            # Logging estruturado de erro
            log_data.update({
                "status_code": 500,
                "duration_seconds": duration,
                "error": str(e),
                "error_type": type(e).__name__
            })
            logger.error(f"Request com erro: {json.dumps(log_data)}", exc_info=True)
            
            raise
        finally:
            # Decrementar métrica de requests em progresso
            http_requests_in_progress.labels(
                method=request.method,
                endpoint=request.url.path
            ).dec()


def setup_structured_logging():
    """Configura logging estruturado"""
    import sys
    from pythonjsonlogger import jsonlogger
    
    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    log_handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(log_handler)
    root_logger.setLevel(logging.INFO)

