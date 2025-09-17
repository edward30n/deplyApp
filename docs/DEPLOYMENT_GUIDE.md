# RecWay Deployment Guide: Production Ready Architecture

##  Objetivo
Metodología completa para deployment de RecWay en Azure con arquitectura escalable y "git push y listo".

---

##  Estado del Deployment

###  Completado
- [x] **Análisis inicial** - Referencias localhost eliminadas
- [x] **Configuración backend** - Variables de entorno flexibles
- [x] **Configuración frontend** - API URL dinámica
- [x] **CORS dinámico** - Adaptación automática por entorno
- [x] **Dockerfile optimizado** - Dependencias geográficas incluidas
- [x] **CI/CD completo** - GitHub Actions con OIDC
- [x] **Base de datos** - Schema PostgreSQL listo
- [x] **Infraestructura** - Scripts de bootstrap Azure
- [x] **Documentación** - Guías paso a paso
- [x] **Repositorio limpio** - https://github.com/edward30n/deplyApp

###  En Progreso
- [ ] **Ejecución bootstrap** - Crear recursos Azure
- [ ] **Configuración secretos** - Key Vault + GitHub
- [ ] **Primer deployment** - Validar pipeline completo

---

##  Arquitectura Final

`
 Frontend (Static Web Apps)
     HTTPS/CDN Global
    
 Load Balancer & Autoscale (App Service S1)
    
    
 Backend Container (ACR + App Service)
    
    
 PostgreSQL Flexible Server
 Azure Storage Account
 Key Vault (Managed Identity)
 Application Insights
`

### Componentes Clave
- **Plan S1**: Autoscale automático (13 instancias)
- **Blue-Green**: Deployment slots para zero downtime
- **Seguridad**: Managed Identity + Key Vault references
- **Monitoring**: Application Insights + Log Analytics

---

##  Backend Configuration - COMPLETADO

### Variables de Entorno
`ash
# .env.local (desarrollo)
ENV=local
DATABASE_URI=postgresql://user:pass@localhost:5432/recway_db
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=["http://localhost:5173"]
ENABLE_FILE_WATCHER=true

# .env.azure (producción) - vía Key Vault
ENV=azure
DATABASE_URI=@Microsoft.KeyVault(SecretUri=...)
FRONTEND_URL=https://recway-frontend.azurestaticapps.net
CORS_ORIGINS=["https://recway-frontend.azurestaticapps.net"]
ENABLE_FILE_WATCHER=false
`

### CORS Dinámico
`python
# app/core/config.py
def get_cors_origins():
    if settings.ENV == "local":
        return ["http://localhost:3000", "http://localhost:5173"]
    return json.loads(os.getenv("CORS_ORIGINS", '["https://recway-frontend.azurestaticapps.net"]'))
`

### Health Check
`python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
`

---

##  Frontend Configuration - COMPLETADO

### API Configuration
`	ypescript
// src/config/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const buildApiUrl = (endpoint: string): string => {
  return ${API_BASE_URL};
};
`

### Environment Variables
`ash
# .env.development
VITE_API_URL=http://localhost:8000
VITE_ENV=development

# .env.production (en build)
VITE_API_URL=https://recway-backend-central.azurewebsites.net
VITE_ENV=production
`

---

##  Container Configuration

### Dockerfile.azure
`dockerfile
FROM python:3.11-slim

# Dependencias geográficas para geopandas/osmnx
RUN apt-get update && apt-get install -y \
    curl gdal-bin libgdal-dev libspatialindex-dev \
    libgeos-dev proj-bin libproj-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
`

---

##  CI/CD Pipeline

### GitHub Actions - Backend
**Archivo**: .github/workflows/deploy_backend.yml

**Flujo**:
1. **Trigger**: Push a main con cambios en ackend/**
2. **OIDC Login**: Sin credenciales hardcodeadas
3. **Build**: Docker con buildx
4. **Push**: ACR con tags prod-{sha} y latest
5. **Deploy**: App Service apunta a nueva imagen
6. **Configure**: App settings base
7. **Restart**: Aplicación

### GitHub Actions - Frontend
**Archivo**: .github/workflows/deploy_frontend_swa.yml

**Flujo**:
1. **Trigger**: Push a main con cambios en rontend/**
2. **Setup**: Node 20
3. **Build**: npm ci + build con Vite
4. **Configure**: VITE_API_URL para producción
5. **Deploy**: Static Web Apps

---

##  Database Configuration

### Schema Completo
- **Ubicación**: database/schema.sql
- **Incluye**: Autenticación, usuarios, empresas, datos viales, sensores
- **Inicialización**: Script database/init_azure_db.sh

### Connection String
`ash
postgresql://user:password@recway-db-new.postgres.database.azure.com:5432/recWay_db?sslmode=require
`

---

##  Checklist de Deployment

### 0. Prerrequisitos
- [ ] Azure CLI instalado y autenticado: z login
- [ ] GitHub repo con Actions habilitadas
- [ ] Repositorio: https://github.com/edward30n/deplyApp

### 1. Infraestructura Azure
`ash
# Ejecutar bootstrap (una sola vez)
chmod +x infra/scripts/azure_bootstrap.sh
./infra/scripts/azure_bootstrap.sh
`

### 2. Configurar Secretos
`ash
# Key Vault secrets
az keyvault secret set -n recway-secret-key --vault-name recway-keyvault-02 --value "jwt_secret_fuerte"
az keyvault secret set -n recway-db-uri --vault-name recway-keyvault-02 --value "postgresql://..."
az keyvault secret set -n recway-storage-conn --vault-name recway-keyvault-02 --value "connection_string"
`

### 3. App Settings
`ash
# Con Key Vault references
az webapp config appsettings set -g recway-rg -n recway-backend-central --settings \
  WEBSITES_PORT=8000 ENV=azure API_V1_STR=/api/v1 ENABLE_FILE_WATCHER=false \
  SECRET_KEY=@Microsoft.KeyVault(...) \
  DATABASE_URI=@Microsoft.KeyVault(...) \
  AZURE_STORAGE_CONNECTION_STRING=@Microsoft.KeyVault(...)
`

### 4. GitHub Secrets
`
AZURE_CLIENT_ID=xxx-xxx-xxx
AZURE_TENANT_ID=xxx-xxx-xxx  
AZURE_SUBSCRIPTION_ID=xxx-xxx-xxx
AZURE_STATIC_WEB_APPS_API_TOKEN=xxx
`

### 5. Base de Datos
`ash
# Inicializar schema
./database/init_azure_db.sh
`

### 6. Primer Deployment
`ash
git push origin main
`

### 7. Verificación
`ash
# Health checks
curl https://recway-backend-central.azurewebsites.net/health
curl https://recway-backend-central.azurewebsites.net/api/v1/recway/processing-stats
`

---

##  Troubleshooting

### Logs en Tiempo Real
`ash
az webapp log tail -g recway-rg -n recway-backend-central
`

### Container Issues
`ash
# Ver configuración actual
az webapp config appsettings list -g recway-rg -n recway-backend-central

# Verificar imagen en ACR
az acr repository show-tags -n recwayacr2 --repository recway-backend
`

### Rollback
`ash
# Cambiar a tag anterior
az webapp config container set -g recway-rg -n recway-backend-central \
  --docker-custom-image-name recwayacr2.azurecr.io/recway-backend:prod-<commit_anterior>
`

---

##  Monitoreo

### URLs de Verificación
- **Backend Health**: https://recway-backend-central.azurewebsites.net/health
- **Frontend**: https://recway-frontend.azurestaticapps.net
- **Application Insights**: Azure Portal  recway-ai

### Métricas Clave
- CPU utilization (target: <70%)
- Memory usage
- Response times
- Error rates (target: <1%)
- Database connection health

---

##  Próximos Pasos

1.  **Documentación actualizada**
2.  **Ejecutar azure_bootstrap.sh**
3.  **Configurar secretos y GitHub**
4.  **Primer deployment**
5.  **Validación completa**

---

** Estado**: Ready for Production Deployment  
**Última actualización**: 2025-09-17  
**Responsable**: DevOps Team
