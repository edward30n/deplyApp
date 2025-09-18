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

# Test endpoint for CI/CD
@app.get("/api/v1/test")
async def test_endpoint():
    """Test endpoint to verify automated deployment"""
    return {
        "status": "success",
        "message": "🚀 Backend CI/CD deployment working!",
        "python_version": "3.12",
        "deployment_date": "2025-09-18"
    }

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

# Debug endpoint to check database tables
@app.get("/api/v1/debug/tables")
def debug_tables(db: Session = Depends(get_db)):
    """
    Debug endpoint to check database tables status
    """
    try:
        from sqlalchemy import text
        from app.models.user import Country
        
        result = {}
        
        # Check if countries table exists
        try:
            table_exists = db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'countries'
                );
            """)).scalar()
            result["countries_table_exists"] = table_exists
        except Exception as e:
            result["countries_table_exists"] = f"Error: {str(e)}"
        
        # Try to count countries
        try:
            count = db.query(Country).count()
            result["countries_count"] = count
        except Exception as e:
            result["countries_count"] = f"Error: {str(e)}"
        
        # Try to get first few countries
        try:
            countries = db.query(Country).limit(3).all()
            result["sample_countries"] = [{"code": c.code, "name": c.name} for c in countries]
        except Exception as e:
            result["sample_countries"] = f"Error: {str(e)}"
            
        return result
        
    except Exception as e:
        return {"error": str(e)}

# Simple CORS test endpoint
@app.get("/api/v1/test/cors")
def test_cors():
    """
    Simple endpoint to test CORS and basic connectivity
    """
    return {
        "status": "ok",
        "message": "CORS and connectivity working",
        "timestamp": "2025-09-17",
        "service": "RecWay API"
    }

# List all database tables
@app.get("/api/v1/debug/list-tables")
def list_all_tables(db: Session = Depends(get_db)):
    """
    List all tables in the database
    """
    try:
        from sqlalchemy import text
        
        # Query to get all tables
        result = db.execute(text("""
            SELECT 
                table_name,
                table_schema,
                table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        
        tables = []
        for row in result:
            tables.append({
                "table_name": row[0],
                "schema": row[1], 
                "type": row[2]
            })
        
        # Also get table sizes and row counts
        table_info = []
        for table in tables:
            try:
                # Get row count
                count_result = db.execute(text(f"SELECT COUNT(*) FROM {table['table_name']}"))
                row_count = count_result.scalar()
                
                table_info.append({
                    "name": table['table_name'],
                    "schema": table['schema'],
                    "type": table['type'],
                    "row_count": row_count
                })
            except Exception as e:
                table_info.append({
                    "name": table['table_name'],
                    "schema": table['schema'], 
                    "type": table['type'],
                    "row_count": f"Error: {str(e)}"
                })
        
        return {
            "total_tables": len(tables),
            "tables": table_info
        }
        
    except Exception as e:
        return {"error": str(e)}

# Countries endpoint (needed by frontend)
@app.get("/api/v1/countries")
def get_countries():
    """
    Get list of available countries for frontend signup
    Returns hardcoded list for now due to DB issues
    """
    # Static phone prefixes mapping 
    countries_with_prefixes = [
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
    
    return countries_with_prefixes

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
