from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging

from app.api.v1.auth import auth_router
from app.core.config import settings
from app.database.session import get_db
import app.models
from app.api.endpoints.upload import router as upload_router
from app.api.endpoints.auto_processing import router as auto_processing_router
from app.api.endpoints.recway_processing import router as recway_processing_router
from app.api.v1.export import router as data_export_router  # Router funcional de exportación
from app.api.v1.optimization import router as optimized_export_router  # Router optimizado
from app.services.monitoring.file_watcher import start_file_watcher, stop_file_watcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="RecWay API with Secure JWT Authentication",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS con configuración dinámica
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log de la configuración CORS para debugging
logger.info(f"🌐 CORS configurado para entorno: {settings.ENV}")
logger.info(f"🌐 CORS origins permitidos: {settings.CORS_ORIGINS}")
logger.info(f"🌐 Frontend URL: {settings.FRONTEND_URL}")
logger.info(f"🌐 Base URL: {settings.BASE_URL}")

# Include secure authentication endpoints
app.include_router(auth_router)
app.include_router(upload_router, prefix=settings.API_V1_STR + "/files", tags=["files"])
app.include_router(auto_processing_router, prefix=settings.API_V1_STR + "/auto-process", tags=["auto-processing"])
app.include_router(recway_processing_router, prefix=settings.API_V1_STR + "/recway", tags=["recway-processing"])
app.include_router(data_export_router, tags=["data-export"])  # Router funcional de exportación
app.include_router(optimized_export_router, tags=["optimized-export"])  # Router optimizado

# Eventos de aplicación
@app.on_event("startup")
async def startup_event():
    """Eventos que se ejecutan al iniciar la aplicación"""
    logger.info("Iniciando RecWay API...")
    
    # Iniciar file watcher para procesamiento automático
    if start_file_watcher():
        logger.info("✅ File Watcher iniciado correctamente")
    else:
        logger.warning("⚠️ No se pudo iniciar el File Watcher")

@app.on_event("shutdown")
async def shutdown_event():
    """Eventos que se ejecutan al cerrar la aplicación"""
    logger.info("Cerrando RecWay API...")
    
    # Detener file watcher
    stop_file_watcher()
    logger.info("✅ File Watcher detenido")

# Countries endpoint (needed by frontend)
@app.get("/api/v1/countries")
def get_countries(db: Session = Depends(get_db)):
    """
    Get list of available countries for frontend signup
    """
    from app.models.user import Country
    
    try:
        countries = db.query(Country).order_by(Country.name).all()
        
        # If no countries found, try to initialize them
        if not countries:
            init_countries(db)
            countries = db.query(Country).order_by(Country.name).all()
        
        # Static phone prefixes mapping since it's not in DB schema
        phone_prefixes = {
            'CO': '+57', 'US': '+1', 'MX': '+52', 'AR': '+54', 'BR': '+55',
            'CL': '+56', 'PE': '+51', 'EC': '+593', 'ES': '+34', 'UK': '+44'
        }
        
        return [
            {
                "code": country.code,
                "name": country.name,
                "phone_prefix": phone_prefixes.get(country.code, "+1")
            }
            for country in countries
        ]
    except Exception as e:
        logger.error(f"Error getting countries: {e}")
        # Return hardcoded list as fallback
        return [
            {"code": "CO", "name": "Colombia", "phone_prefix": "+57"},
            {"code": "US", "name": "United States", "phone_prefix": "+1"},
            {"code": "MX", "name": "Mexico", "phone_prefix": "+52"},
            {"code": "AR", "name": "Argentina", "phone_prefix": "+54"},
            {"code": "BR", "name": "Brazil", "phone_prefix": "+55"},
            {"code": "CL", "name": "Chile", "phone_prefix": "+56"},
            {"code": "PE", "name": "Peru", "phone_prefix": "+51"},
            {"code": "EC", "name": "Ecuador", "phone_prefix": "+593"},
            {"code": "ES", "name": "Spain", "phone_prefix": "+34"},
            {"code": "UK", "name": "United Kingdom", "phone_prefix": "+44"}
        ]

@app.post("/api/v1/init-countries")
def init_countries(db: Session = Depends(get_db)):
    """
    Initialize countries table if it doesn't exist or is empty
    """
    from app.models.user import Country
    from sqlalchemy import text
    
    try:
        # Check if table exists and create if not
        try:
            # Try to create table if it doesn't exist
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS countries (
                    code CHAR(2) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL
                );
            """))
            db.commit()
        except Exception as e:
            logger.warning(f"Table creation warning (probably already exists): {e}")
            db.rollback()
        
        # Check if we have countries
        existing_count = db.query(Country).count()
        if existing_count > 0:
            return {"message": f"Countries already initialized ({existing_count} found)"}
        
        # Insert countries
        countries_data = [
            ("CO", "Colombia"),
            ("US", "United States"),
            ("MX", "Mexico"),
            ("AR", "Argentina"),
            ("BR", "Brazil"),
            ("CL", "Chile"),
            ("PE", "Peru"),
            ("EC", "Ecuador"),
            ("ES", "Spain"),
            ("UK", "United Kingdom")
        ]
        
        for code, name in countries_data:
            country = Country(code=code, name=name)
            db.add(country)
        
        db.commit()
        
        return {"message": f"Successfully initialized {len(countries_data)} countries"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing countries: {e}")
        raise HTTPException(status_code=500, detail=f"Error initializing countries: {str(e)}")

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RecWay API",
        "version": "1.0.0"
    }

@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }
