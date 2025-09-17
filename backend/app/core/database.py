"""
CONFIGURACIÓN DE BASE DE DATOS PARA RECWAY
Conexión a PostgreSQL con SQLAlchemy
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from typing import Generator

# Configuración de la base de datos
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/recway_db"
)

# Crear motor de SQLAlchemy con CONNECTION POOLING para concurrencia
engine = create_engine(
    DATABASE_URL,
    # CONNECTION POOLING SETTINGS para múltiples usuarios simultáneos
    pool_size=20,          # Conexiones base en el pool
    max_overflow=30,       # Conexiones adicionales permitidas
    pool_timeout=30,       # Timeout para obtener conexión del pool
    pool_recycle=3600,     # Reciclar conexiones cada hora
    pool_pre_ping=True,    # Verificar conexiones antes de usar
    echo=False,            # Cambiar a True para debug SQL
    # PERFORMANCE TUNING
    connect_args={
        "options": "-c timezone=utc",
        "application_name": "RecWay_Backend"
    }
)

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

def get_db() -> Generator:
    """
    Generador de sesiones de base de datos para FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Inicializar base de datos (crear tablas si no existen)
    """
    # Importar todos los modelos aquí
    Base.metadata.create_all(bind=engine)
