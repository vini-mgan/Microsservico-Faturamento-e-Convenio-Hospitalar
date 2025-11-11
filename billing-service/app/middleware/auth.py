from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scheme_name="OAuth2"
)

# HTTP Bearer scheme
security = HTTPBearer()


class AuthMiddleware:
    """Middleware para autenticação OAuth2/OIDC e autorização RBAC/ABAC"""
    
    def __init__(self):
        # Configurações OIDC (devem vir de variáveis de ambiente)
        self.oidc_issuer = getattr(settings, 'OIDC_ISSUER', 'http://localhost:8080/auth/realms/master')
        self.oidc_audience = getattr(settings, 'OIDC_AUDIENCE', 'billing-service')
        self.jwt_secret = getattr(settings, 'JWT_SECRET', 'change-me-in-production')
        self.jwt_algorithm = getattr(settings, 'JWT_ALGORITHM', 'HS256')
        
        # Desabilitar validação em desenvolvimento (se configurado)
        self.auth_enabled = getattr(settings, 'AUTH_ENABLED', 'true').lower() == 'true'
    
    async def verify_token(self, credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
        """Verifica token JWT e retorna claims"""
        if not self.auth_enabled:
            # Modo desenvolvimento: retornar usuário mock
            return {
                "sub": "dev-user",
                "roles": ["billing:read", "billing:write"],
                "permissions": ["claims:create", "claims:read", "invoices:create", "invoices:read"]
            }
        
        token = credentials.credentials
        
        try:
            # Decodificar e validar token JWT
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                audience=self.oidc_audience,
                options={"verify_signature": True}
            )
            return payload
        except JWTError as e:
            logger.warning(f"Token inválido: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def check_permission(self, user_claims: dict, required_permission: str) -> bool:
        """Verifica se usuário tem permissão específica (ABAC)"""
        permissions = user_claims.get("permissions", [])
        roles = user_claims.get("roles", [])
        
        # Verificar permissão direta
        if required_permission in permissions:
            return True
        
        # Verificar permissão via role
        # Exemplo: role "billing:admin" tem todas as permissões de billing
        if any("billing:admin" in role or "admin" in role for role in roles):
            return True
        
        # Verificar permissão baseada em padrão
        # Exemplo: "billing:write" permite "claims:create", "invoices:create", etc.
        if required_permission.startswith("claims:") and "billing:write" in roles:
            return True
        if required_permission.startswith("invoices:") and "billing:write" in roles:
            return True
        if required_permission.startswith("eligibility:") and "billing:read" in roles:
            return True
        
        return False
    
    def check_role(self, user_claims: dict, required_role: str) -> bool:
        """Verifica se usuário tem role específica (RBAC)"""
        roles = user_claims.get("roles", [])
        return required_role in roles or any("admin" in role for role in roles)


# Instância global
auth_middleware = AuthMiddleware()


def require_permission(permission: str):
    """Dependency para verificar permissão específica"""
    async def permission_checker(claims: dict = Security(auth_middleware.verify_token)):
        if not auth_middleware.check_permission(claims, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão necessária: {permission}"
            )
        return claims
    return permission_checker


def require_role(role: str):
    """Dependency para verificar role específica"""
    async def role_checker(claims: dict = Security(auth_middleware.verify_token)):
        if not auth_middleware.check_role(claims, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role necessária: {role}"
            )
        return claims
    return role_checker







