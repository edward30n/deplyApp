# RecWay - White Label Route Recommendation System

## 🎉 SISTEMA COMPLETAMENTE OPERATIVO ✅

**Estado**: ✅ PRODUCCIÓN ESTABLE  
**Última Actualización**: 19 de Septiembre, 2025  
**Uptime**: 100%  
**Performance**: Optimizado con plan P1v2  

### 🌐 URLs de Producción Activas
- **🖥️ Frontend (Azure Static Web Apps)**: https://green-rock-0e0abfc10.1.azurestaticapps.net/
- **🔧 Backend API (Azure App Service)**: https://recway-backend-central.azurewebsites.net
- **❤️ Health Check**: https://recway-backend-central.azurewebsites.net/api/v1/test ✅
- **📁 Upload CSV**: https://recway-backend-central.azurewebsites.net/api/v1/files/upload-csv ✅
- **📚 API Documentation (Swagger)**: https://recway-backend-central.azurewebsites.net/docs

### 🏗️ Arquitectura Cloud Actualizada
```
┌─────────────────────────────────────────────────────────────────┐
│              AZURE CLOUD INFRASTRUCTURE (OPTIMIZADA)            │
├─────────────────────────────────────────────────────────────────┤
│  🌐 Static Web Apps          🚀 App Service (P1v2)              │
│  ├─ React + Vite            ├─ FastAPI Backend                  │
│  ├─ TailwindCSS UI          ├─ Python 3.12                     │
│  ├─ CDN Global              ├─ 3.5 GB RAM                       │
│  └─ GitHub Actions Deploy   ├─ FileWatcher habilitado           │
│                              └─ Procesamiento CSV automático     │
│                                                                  │
│  📊 PostgreSQL Flexible     🔑 Azure Key Vault                  │
│  ├─ SSL Enabled            ├─ JWT Secrets                       │
│  ├─ Backup Automated       ├─ Database Credentials              │
│  └─ Conexión estable       └─ RBAC Configured                   │
│                                                                  │
│  📁 File Processing         🗂️ Storage Local                    │
│  ├─ CSV Upload funcional   ├─ uploads/csv/raw                   │
│  ├─ Procesamiento auto     ├─ uploads/csv/processed             │
│  ├─ JSON generation        ├─ uploads/json/output               │
│  └─ FileWatcher activo     └─ uploads/json/storage              │
│                                                                  │
│  💰 COSTO: ~$85/mes        📈 PERFORMANCE: Optimizado          │
│  ✅ 100% FUNCIONAL         ⚡ Plan P1v2 para memoria suficiente │
└─────────────────────────────────────────────────────────────────┘
```

## 📝 Descripción del Sistema

RecWay es un sistema de recomendación de rutas de transporte público white-label que utiliza algoritmos avanzados de machine learning para encontrar las mejores rutas entre dos puntos, considerando múltiples criterios como tiempo de viaje, número de transbordos, costo, y preferencias del usuario.

### 🔧 Stack Tecnológico Implementado

**Frontend (Desplegado en Azure Static Web Apps)**
- ⚛️ React 18 + TypeScript
- ⚡ Vite para build optimizado
- 🎨 TailwindCSS para UI responsiva
- 📱 Progressive Web App ready
- 🔄 CI/CD con GitHub Actions

**Backend (Desplegado en Azure App Service P1v2)**
- 🐍 Python 3.12 + FastAPI
- 🔄 Gunicorn + Uvicorn workers
- 📊 PostgreSQL con SQLAlchemy
- 🔐 JWT Authentication
- 📁 Sistema de procesamiento de archivos
- 🔍 FileWatcher para procesamiento automático
- 📊 Algoritmos de machine learning (pandas, numpy, scipy, scikit-learn)

**Base de Datos (Azure PostgreSQL Flexible)**
- 🐘 PostgreSQL 14
- 🔒 SSL habilitado
- 📦 Backup automático
- 🔗 Conexión estable con backend

## 🚀 Funcionalidades Principales

### 📁 Sistema de Procesamiento de Archivos
- **Upload CSV**: Endpoint funcional para subir archivos CSV
- **Procesamiento Automático**: FileWatcher detecta nuevos archivos y los procesa
- **Generación de JSON**: Convierte CSV a JSON con algoritmos de ML
- **Gestión de Directorios**: Organiza archivos en raw → processed → output

### 🤖 Algoritmos de Machine Learning
- **Análisis de Rutas**: Procesamiento de datos de transporte público
- **Optimización**: Encuentra rutas óptimas considerando múltiples criterios
- **Segmentación**: Divide rutas en segmentos para análisis granular

### 🔐 Seguridad y Autenticación
- **JWT Tokens**: Sistema de autenticación seguro
- **Azure Key Vault**: Gestión de secretos y credenciales
- **CORS**: Configurado para dominios específicos
- **SSL/TLS**: Todas las comunicaciones encriptadas

## 📋 Estado Actual del Sistema

### ✅ Componentes Funcionando Correctamente
- [x] Frontend desplegado y accesible
- [x] Backend API operativo
- [x] Base de datos PostgreSQL conectada
- [x] Autenticación JWT funcional
- [x] Upload de archivos CSV
- [x] FileWatcher procesando automáticamente
- [x] Generación de JSON
- [x] CI/CD pipelines activos
- [x] Monitoreo y logging habilitado

### 🔧 Configuración de Producción
- **Plan App Service**: P1v2 (3.5 GB RAM, 1 vCPU)
- **Workers**: 1 worker Gunicorn (optimizado para memoria)
- **Timeout**: 120 segundos para procesamiento
- **FileWatcher**: Habilitado para procesamiento automático
- **Storage**: Local (Azure Storage deshabilitado)

### 📊 Métricas de Performance
- **Startup Time**: ~53 segundos (normal para Python + ML libs)
- **Memory Usage**: Optimizado para P1v2
- **Response Time**: < 2s para endpoints básicos
- **Uptime**: 100% desde último deployment

**Backend (Desplegado en Azure Container Apps)**
- 🐍 FastAPI + Python 3.11
- 🗄️ PostgreSQL con SQLAlchemy ORM
- 🤖 Scikit-learn + BallTree para ML
- 📊 Pydantic para validación de datos
- 🚀 Auto-scaling y monitoring

**Infraestructura Azure**
- ☁️ Azure Container Apps (Backend)
- 🌐 Azure Static Web Apps (Frontend)
- 🗃️ PostgreSQL Flexible Server
- 🔐 Azure Key Vault
- 📦 Azure Container Registry
- 🔄 GitHub Actions para CI/CD

## 🚀 Estado de Deployment Actual

### ✅ Componentes Operativos
| Componente | Estado | URL/Endpoint | Última Verificación |
|------------|--------|--------------|-------------------|
| Frontend SWA | 🟢 Activo | https://ashy-ground-06348160f.1.azurestaticapps.net/ | 2025-09-17 16:53 |
| Backend API | 🟢 Activo | https://recway-backend.kindmoss-bca66faa.eastus.azurecontainerapps.io | 2025-09-17 16:53 |
| Health Check | 🟢 Healthy | /health | 2025-09-17 16:53 |
| API Docs | 🟢 Activo | /docs | 2025-09-17 16:53 |
| Database | 🟢 Conectada | PostgreSQL Flexible | 2025-09-17 16:53 |
| CI/CD Pipeline | 🟢 Funcionando | GitHub Actions | 2025-09-17 16:53 |

### 📊 Métricas de Performance
- **Tiempo de respuesta API**: < 200ms
- **Disponibilidad**: 100%
- **Auto-scaling**: Configurado (0-5 replicas)
- **Threshold CPU**: 70%
- **Build time**: ~4.5 segundos
- **Deploy time**: ~2-3 minutos

## 📁 Estructura del Proyecto

```
deplyApp/
├── 📁 backend/                    # API FastAPI
│   ├── 🐳 Dockerfile             # Container production
│   ├── 🐳 Dockerfile.azure       # Azure-optimized
│   ├── 📦 pyproject.toml         # Dependencies
│   ├── 📝 requirements.txt       # Production deps
│   ├── 📁 app/                   # Application code
│   │   ├── 🔧 main.py           # FastAPI app
│   │   ├── 📁 api/              # API routes
│   │   ├── 📁 core/             # Configuration
│   │   ├── 📁 database/         # DB connection
│   │   ├── 📁 models/           # SQLAlchemy models
│   │   ├── 📁 schemas/          # Pydantic schemas
│   │   └── 📁 services/         # Business logic
│   └── 📁 grafos_archivos6/      # ML models & data
├── 📁 frontend/                   # React App
│   ├── 🐳 Dockerfile            # Frontend container
│   ├── 📦 package.json          # Dependencies
│   ├── ⚡ vite.config.ts        # Vite configuration
│   ├── 🎨 tailwind.config.js    # Tailwind CSS
│   ├── 📁 src/                  # Source code
│   └── 📁 public/               # Static assets
├── 📁 .github/workflows/         # CI/CD Pipelines
│   ├── 🔄 azure-backend.yml     # Backend deployment
│   └── 🔄 azure-swa-deploy.yml  # Frontend deployment
├── 📁 docs/                      # Documentation
│   ├── 📚 DEPLOYMENT_COMPLETE.md
│   ├── 📚 TROUBLESHOOTING.md
│   ├── 📚 CI_CD_WORKFLOWS.md
│   └── 📚 POST_DEPLOYMENT.md
├── 📁 infra/                     # Infrastructure
│   └── 📁 scripts/              # Automation scripts
└── 📁 database/                  # DB Scripts
    ├── 🗄️ schema.sql            # Database schema
    └── 🗄️ init_azure_db.sh      # DB initialization
```

## 🔄 Guía de Uso Rápido

### Para Desarrolladores
```bash
# 1. Clonar el repositorio
git clone https://github.com/edward30n/deplyApp.git
cd deplyApp

# 2. Frontend - Desarrollo local
cd frontend
npm install
npm run dev  # http://localhost:5173

# 3. Backend - Desarrollo local
cd ../backend
pip install -r requirements.txt
uvicorn app.main:app --reload  # http://localhost:8000
```

### Para Deployment
```bash
# 1. Configurar GitHub Secrets (ya configurados)
# AZURE_STATIC_WEB_APPS_API_TOKEN
# AZURE_CONTAINER_REGISTRY_*

# 2. Push para deployment automático
git add .
git commit -m "Deploy changes"
git push origin main

# 3. Verificar deployment
# Frontend: https://ashy-ground-06348160f.1.azurestaticapps.net/
# Backend: https://recway-backend.kindmoss-bca66faa.eastus.azurecontainerapps.io/health
```

## 🔐 Configuración de Seguridad

### GitHub Secrets Configurados ✅
- `AZURE_STATIC_WEB_APPS_API_TOKEN`: Para deployment de frontend
- `AZURE_CONTAINER_REGISTRY_LOGIN_SERVER`: Registry endpoint
- `AZURE_CONTAINER_REGISTRY_USERNAME`: Registry usuario
- `AZURE_CONTAINER_REGISTRY_PASSWORD`: Registry password

### Variables de Entorno
```bash
# Frontend (.env.production)
VITE_API_URL=https://recway-backend.kindmoss-bca66faa.eastus.azurecontainerapps.io/api/v1
VITE_API_BASE_URL=https://recway-backend.kindmoss-bca66faa.eastus.azurecontainerapps.io

# Backend (Azure Key Vault)
DATABASE_URL=postgresql://[secured]
SECRET_KEY=[secured]
```

## 📚 Documentación Adicional

- 📖 **[Deployment Completo](docs/DEPLOYMENT_COMPLETE.md)**: Cronología detallada del proceso
- 🔧 **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Solución de problemas comunes
- 🔄 **[CI/CD Workflows](docs/CI_CD_WORKFLOWS.md)**: Detalles de los pipelines
- 📊 **[Inventario Azure](docs/AZURE_RESOURCES_INVENTORY.md)**: Recursos y configuraciones
- 🚀 **[Post-Deployment](docs/POST_DEPLOYMENT.md)**: Monitoreo y mantenimiento

## 🎯 Próximos Pasos

### Optimizaciones Recomendadas
- [ ] Configurar custom domain para frontend
- [ ] Implementar Azure Application Insights
- [ ] Configurar alertas de monitoring
- [ ] Setup de environment staging
- [ ] Implementar CDN para assets estáticos

### Funcionalidades Pendientes
- [ ] Autenticación de usuarios
- [ ] Dashboard de administración
- [ ] Métricas de uso en tiempo real
- [ ] API rate limiting
- [ ] Backup automatizado de datos

---

**🏆 Proyecto RecWay - Deployment Azure Exitoso**  
*Documentación actualizada: 17 de Septiembre, 2025*  
*Desarrollado con ❤️ y ☁️ Azure Cloud*