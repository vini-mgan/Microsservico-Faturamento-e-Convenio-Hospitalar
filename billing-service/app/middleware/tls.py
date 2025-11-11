"""
Configuração TLS/mTLS para Zero-trust
"""
import ssl
import logging
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)


def get_ssl_context(server_side: bool = True) -> ssl.SSLContext:
    """
    Cria contexto SSL para TLS/mTLS
    
    Args:
        server_side: True para servidor, False para cliente
    
    Returns:
        SSLContext configurado
    """
    # Configurações TLS
    tls_enabled = getattr(settings, 'TLS_ENABLED', 'false').lower() == 'true'
    cert_file = getattr(settings, 'TLS_CERT_FILE', None)
    key_file = getattr(settings, 'TLS_KEY_FILE', None)
    ca_file = getattr(settings, 'TLS_CA_FILE', None)
    
    if not tls_enabled:
        logger.warning("TLS desabilitado. Use apenas em desenvolvimento.")
        return None
    
    context = ssl.create_default_context(
        ssl.Purpose.CLIENT_AUTH if server_side else ssl.Purpose.SERVER_AUTH
    )
    
    # Carregar certificado e chave do servidor
    if cert_file and key_file:
        try:
            context.load_cert_chain(cert_file, key_file)
            logger.info(f"Certificado carregado: {cert_file}")
        except Exception as e:
            logger.error(f"Erro ao carregar certificado: {e}")
            raise
    
    # mTLS: verificar certificados do cliente
    if server_side and ca_file:
        try:
            context.load_verify_locations(ca_file)
            context.verify_mode = ssl.CERT_REQUIRED
            logger.info(f"mTLS habilitado com CA: {ca_file}")
        except Exception as e:
            logger.error(f"Erro ao carregar CA para mTLS: {e}")
            raise
    
    # Configurações de segurança
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.set_ciphers('HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA')
    
    return context


def get_client_ssl_context() -> ssl.SSLContext:
    """Cria contexto SSL para cliente (mTLS)"""
    return get_ssl_context(server_side=False)







