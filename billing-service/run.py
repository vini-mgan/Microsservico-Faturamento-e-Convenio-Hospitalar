import uvicorn
import os
from app.config import settings
from app.middleware.tls import get_ssl_context

if __name__ == "__main__":
    # Configurar SSL/TLS se habilitado
    ssl_context = get_ssl_context(server_side=True)
    
    # Desabilitar reload em produção/Docker (melhor performance)
    reload = os.getenv("RELOAD", "false").lower() == "true"

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=reload,
        ssl_keyfile=getattr(settings, 'TLS_KEY_FILE', None) if ssl_context else None,
        ssl_certfile=getattr(settings, 'TLS_CERT_FILE', None) if ssl_context else None,
    )

