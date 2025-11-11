from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from app.routers import claims, invoices, eligibility
from app.middleware.slos import router as slos_router
from app.middleware.observability import ObservabilityMiddleware, setup_structured_logging
from app.middleware.tls import get_ssl_context
from app.database import engine, Base
from app.config import settings
import logging

# Configurar logging estruturado
setup_structured_logging()
logger = logging.getLogger(__name__)

# Criar tabelas (se MySQL estiver disponível)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Tabelas criadas/verificadas com sucesso")
except Exception as e:
    logger.warning(f"MySQL não disponível: {e}. Tabelas serão criadas quando o banco estiver disponível.")

app = FastAPI(
    title="Billing Service",
    description="Microsserviço de Faturamento & Convênios (Billing/Claims)",
    version="1.0.0"
)

# Middleware de Observabilidade (deve ser adicionado primeiro)
app.add_middleware(ObservabilityMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(claims.router)
app.include_router(invoices.router)
app.include_router(eligibility.router)
app.include_router(slos_router)

# Métricas Prometheus
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
def root():
    return {
        "service": "billing-service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}

