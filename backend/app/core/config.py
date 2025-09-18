import os
import json
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    PROJECT_NAME = os.getenv("PROJECT_NAME", "RecWay")
    API_V1_STR = os.getenv("API_V1_STR", "/api/v1")
    SECRET_KEY = os.getenv("SECRET_KEY", "recway-secret-key-change-in-production")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    DATABASE_URI = os.getenv("DATABASE_URI", "postgresql://postgres:edward123@localhost:5432/recWay_db")
    
    # Storage settings (local + future Azure)
    USE_AZURE_STORAGE = os.getenv("USE_AZURE_STORAGE", "false").lower() == "true"
    AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    
    # Azure container names (for future use)
    STORAGE_CONTAINER_CSV_RAW = os.getenv("STORAGE_CONTAINER_CSV_RAW", "csv-raw")
    STORAGE_CONTAINER_CSV_PROCESSED = os.getenv("STORAGE_CONTAINER_CSV_PROCESSED", "csv-processed")
    STORAGE_CONTAINER_PROCESSED_JSON = os.getenv("STORAGE_CONTAINER_PROCESSED_JSON", "processed-json")
    STORAGE_CONTAINER_GRAPH_DATA = os.getenv("STORAGE_CONTAINER_GRAPH_DATA", "graph-data")
    STORAGE_CONTAINER_UPLOADS = os.getenv("STORAGE_CONTAINER_UPLOADS", "uploads")
    
    # Local storage base paths (mirroring Azure containers)
    LOCAL_STORAGE_BASE = os.getenv("LOCAL_STORAGE_BASE", "uploads")
    # Nota: estos paths son relativos al cwd cuando ejecutas uvicorn (normalmente la carpeta 'backend')
    CSV_RAW_DIR = os.getenv("CSV_RAW_DIR", os.path.join(LOCAL_STORAGE_BASE, "csv", "raw"))
    CSV_PROCESSED_DIR = os.getenv("CSV_PROCESSED_DIR", os.path.join(LOCAL_STORAGE_BASE, "csv", "processed"))
    JSON_OUTPUT_DIR = os.getenv("JSON_OUTPUT_DIR", os.path.join(LOCAL_STORAGE_BASE, "json", "output"))
    JSON_STORAGE_DIR = os.getenv("JSON_STORAGE_DIR", os.path.join(LOCAL_STORAGE_BASE, "json", "storage"))
    GRAPHS_DIR = os.getenv("GRAPHS_DIR", os.path.join("grafos_archivos6"))
    GRAPHML_DIR = os.getenv("GRAPHML_DIR", os.path.join("grafos_archivos5"))
    
    # Runtime toggles - Definir primero para usar en CORS
    ENV = os.getenv("ENV", "local")  # local | azure | staging | prod
    ENABLE_FILE_WATCHER = os.getenv("ENABLE_FILE_WATCHER", "true").lower() == "true"
    
    # URLs básicas
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # CORS Configuration - Flexible para desarrollo/producción  
    CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "")
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """
        Configuración dinámica de CORS origins.
        Prioridad: CORS_ORIGINS (JSON) -> FRONTEND_URL -> defaults
        """
        # Si hay CORS_ORIGINS definido como JSON
        if self.CORS_ORIGINS_STR:
            try:
                origins = json.loads(self.CORS_ORIGINS_STR)
                if isinstance(origins, list):
                    return origins
            except json.JSONDecodeError:
                pass
        
        # Fallback a FRONTEND_URL + common local URLs + Azure Static Web Apps
        origins = []
        if self.FRONTEND_URL:
            origins.append(self.FRONTEND_URL)
        
        # Agregar Azure Static Web Apps URL (producción)
        azure_swa_url = "https://green-rock-0e0abfc10.1.azurestaticapps.net"
        if azure_swa_url not in origins:
            origins.append(azure_swa_url)
        
        # Agregar URLs locales comunes para desarrollo
        if self.ENV == "local":
            local_origins = [
                "http://localhost:5173",
                "http://localhost:3000", 
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000"
            ]
            for origin in local_origins:
                if origin not in origins:
                    origins.append(origin)
        
        return origins if origins else ["*"]
    
    # Email settings
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@recway.com")
    EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "RecWay")
    
    # URLs for email links (use properties to reference instance variables)
    @property
    def PASSWORD_RESET_URL(self) -> str:
        return f"{self.FRONTEND_URL}/reset-password"
    
    @property  
    def EMAIL_VERIFICATION_URL(self) -> str:
        return f"{self.FRONTEND_URL}/verify-email"
    
    # Server configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", os.getenv("WEBSITES_PORT", "8000")))
    
    @property
    def USE_PROXY_HEADERS(self) -> bool:
        return os.getenv("USE_PROXY_HEADERS", "true" if self.ENV == "azure" else "false").lower() == "true"

settings = Settings()
