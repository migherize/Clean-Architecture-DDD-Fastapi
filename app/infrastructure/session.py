"""
Módulo de configuración de la base de datos usando DatabaseStrategyFactory.
Provee la dependencia `get_db` para FastAPI.
"""

import os
from app.infrastructure.database_strategies import DatabaseStrategyFactory

DB_TYPE = os.getenv("DB", "sqlite")

db_strategy = DatabaseStrategyFactory.create_strategy(db_type=DB_TYPE)

SessionLocal = db_strategy.get_session

def get_db():
    """
    Genera una sesión de base de datos para FastAPI.
    Cierra automáticamente la sesión cuando la operación termina.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
