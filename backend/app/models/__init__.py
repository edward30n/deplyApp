# Import all models to ensure they are registered with SQLAlchemy
from .user import User, AuthToken
from .company import Company
from .recway import (
    Segmento, Geometria, IndicesSegmento, HuecoSegmento,
    Muestra, IndicesMuestra, HuecoMuestra,
    FuenteDatosDispositivo, RegistroSensores
)

__all__ = [
    "User", "AuthToken", "Company",
    "Segmento", "Geometria", "IndicesSegmento", "HuecoSegmento",
    "Muestra", "IndicesMuestra", "HuecoMuestra", 
    "FuenteDatosDispositivo", "RegistroSensores"
]
