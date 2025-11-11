from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from fastapi import HTTPException
from app.config import settings
import logging

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.mysql_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,
    pool_reset_on_return='commit'
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency para obter sessão do banco de dados com tratamento de erros"""
    db = SessionLocal()
    try:
        # Testa conexão antes de retornar
        db.execute(text("SELECT 1"))
        yield db
    except OperationalError as e:
        db.close()
        logger.error(f"Erro de conexão com banco de dados: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Database unavailable",
                "message": "MySQL não está disponível. Por favor, inicie o MySQL ou verifique a configuração.",
                "hint": "Execute: docker-compose up -d (se usar Docker) ou inicie o MySQL manualmente"
            }
        )
    except SQLAlchemyError as e:
        db.rollback()
        db.close()
        logger.error(f"Erro SQLAlchemy: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database error",
                "message": str(e)
            }
        )
    except Exception as e:
        db.close()
        logger.error(f"Erro inesperado no banco de dados: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unexpected database error",
                "message": str(e)
            }
        )
    finally:
        db.close()




