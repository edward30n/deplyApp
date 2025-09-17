# RecWay - Troubleshooting Guide

## 🚨 GUÍA COMPLETA DE SOLUCIÓN DE PROBLEMAS
**Proyecto**: RecWay - White Label Route Recommendation System  
**Fecha**: 17 de Septiembre, 2025  
**Versión**: 1.0  
**Estado**: Basado en problemas reales resueltos durante deployment  

---

## 📋 ÍNDICE DE PROBLEMAS

1. [Frontend Static Web Apps](#frontend-static-web-apps)
2. [Backend Container Apps](#backend-container-apps)
3. [Base de Datos PostgreSQL](#base-de-datos-postgresql)
4. [GitHub Actions CI/CD](#github-actions-cicd)
5. [Azure Container Registry](#azure-container-registry)
6. [Variables de Entorno](#variables-de-entorno)
7. [Conectividad y Networking](#conectividad-y-networking)
8. [Performance y Scaling](#performance-y-scaling)

---

## 🌐 FRONTEND STATIC WEB APPS

### ❌ Problema #1: Página "Congratulations" en lugar de la aplicación
**Síntoma**: 
- El sitio https://ashy-ground-06348160f.1.azurestaticapps.net/ muestra "Congratulations on your new site!" en lugar de la aplicación React
- GitHub Actions workflow se ejecuta exitosamente
- Build local funciona correctamente

**Diagnóstico**:
```bash
# Verificar que la URL responde
curl -I https://ashy-ground-06348160f.1.azurestaticapps.net/

# Revisar contenido de la respuesta
curl https://ashy-ground-06348160f.1.azurestaticapps.net/ | head -n 20
```

**Causas Comunes**:
1. Workflow con `paths` trigger muy restrictivo
2. App location incorrecta en el workflow
3. Output location mal configurada
4. Build no ejecutándose en el workflow

**Solución Aplicada**:
```yaml
# ❌ Configuración problemática
name: Deploy SWA
on:
  push:
    branches: [ main ]
    paths:
      - "frontend/**"  # Muy restrictivo
      - ".github/workflows/azure-swa-deploy.yml"

# ✅ Configuración corregida  
name: Deploy to Azure Static Web Apps
on:
  push:
    branches: [ main ]  # Sin paths restrictivos
  workflow_dispatch:

env:
  VITE_API_URL: https://recway-backend.kindmoss-bca66faa.eastus.azurecontainerapps.io/api/v1
  VITE_API_BASE_URL: https://recway-backend.kindmoss-bca66faa.eastus.azurecontainerapps.io

jobs:
  build_and_deploy_job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          action: "upload"
          app_location: "frontend"
          output_location: "dist"
```

**Pasos para Verificar**:
1. Confirmar que el workflow se ejecuta tras push
2. Verificar logs del workflow en GitHub Actions
3. Comprobar que la SWA se actualiza (puede tomar 2-3 minutos)
4. Revisar contenido HTML de la respuesta

---

### ❌ Problema #2: Variables de entorno no inyectadas en build
**Síntoma**:
- La aplicación no se conecta al backend
- Error de CORS o endpoints no encontrados
- Variables VITE_* no definidas en runtime

**Diagnóstico**:
```bash
# En desarrollo local
npm run build
# Verificar que .env.production tiene las variables

# En GitHub Actions
# Revisar logs del build para ver si las variables están presentes
```

**Solución**:
```yaml
# Agregar variables de entorno en workflow level
env:
  VITE_API_URL: https://recway-backend.kindmoss-bca66faa.eastus.azurecontainerapps.io/api/v1
  VITE_API_BASE_URL: https://recway-backend.kindmoss-bca66faa.eastus.azurecontainerapps.io

# También asegurar que en el frontend hay un .env.production
VITE_API_URL=https://recway-backend.kindmoss-bca66faa.eastus.azurecontainerapps.io/api/v1
VITE_API_BASE_URL=https://recway-backend.kindmoss-bca66faa.eastus.azurecontainerapps.io
```

---

### ❌ Problema #3: Build failures en Vite
**Síntoma**:
- GitHub Actions falla en el step de build
- Errores de TypeScript o dependencias

**Diagnóstico y Solución**:
```bash
# Verificar dependencias localmente
cd frontend
npm ci
npm run build

# Si hay errores de TypeScript
npm run type-check

# Verificar package.json scripts
{
  "scripts": {
    "build": "tsc -b && vite build",
    "type-check": "tsc --noEmit"
  }
}
```

---

## 🚀 BACKEND CONTAINER APPS

### ❌ Problema #4: Container no inicia o se reinicia constantemente
**Síntoma**:
- Health check devuelve 503 o timeout
- Logs muestran errores de inicio
- Replicas en 0 o restart loop

**Diagnóstico**:
```bash
# Verificar logs de Container Apps
az containerapp logs show --name recway-backend --resource-group rg-recway-prod

# Verificar estado de replicas
az containerapp revision list --name recway-backend --resource-group rg-recway-prod
```

**Causas Comunes**:
1. Variables de entorno faltantes o incorrectas
2. Puerto incorrecto en container configuration
3. Problemas de conectividad con PostgreSQL
4. Falta de recursos (CPU/Memory)

**Solución**:
```bash
# Verificar configuración de puerto
# Container debe escuchar en puerto 8000
# Ingress debe estar configurado para targetPort: 8000

# Verificar variables de entorno desde Key Vault
az containerapp secret list --name recway-backend --resource-group rg-recway-prod

# Revisar y corregir si es necesario
az containerapp update --name recway-backend --resource-group rg-recway-prod \
  --set-env-vars DATABASE_URL=secretref:database-url
```

---

### ❌ Problema #5: Auto-scaling no funciona
**Síntoma**:
- Container no escala bajo carga
- Se mantiene en 1 replica siempre
- CPU alto pero no hay scale-out

**Diagnóstico y Solución**:
```bash
# Verificar reglas de scaling
az containerapp show --name recway-backend --resource-group rg-recway-prod \
  --query "properties.template.scale"

# Configuración correcta:
{
  "minReplicas": 0,
  "maxReplicas": 5,
  "rules": [
    {
      "name": "cpu-scaling",
      "custom": {
        "type": "cpu",
        "metadata": {
          "value": "70"
        }
      }
    }
  ]
}
```

---

## 🗄️ BASE DE DATOS POSTGRESQL

### ❌ Problema #6: Connection refused o timeout
**Síntoma**:
- Backend no puede conectar a PostgreSQL
- Error: "connection refused" o "timeout"
- Health check falla

**Diagnóstico**:
```bash
# Desde Container Apps, verificar conectividad
# (Esto se debe hacer desde dentro del container)
psql -h recway-db-server.postgres.database.azure.com -U recwayadmin -d recway_prod

# Verificar firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group rg-recway-prod \
  --name recway-db-server
```

**Solución**:
```bash
# Asegurar que Container Apps puede acceder
az postgres flexible-server firewall-rule create \
  --resource-group rg-recway-prod \
  --name recway-db-server \
  --rule-name "AllowAzureServices" \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Verificar SSL configuration
# Connection string debe incluir sslmode=require
DATABASE_URL="postgresql://recwayadmin:password@recway-db-server.postgres.database.azure.com/recway_prod?sslmode=require"
```

---

### ❌ Problema #7: SSL connection errors
**Síntoma**:
- Error: "SSL connection has been closed unexpectedly"
- Error: "could not establish SSL connection"

**Solución**:
```python
# En el backend, asegurar SSL configuration correcta
# En database/connection.py o similar
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Si es necesario, agregar parámetros SSL explícitos
if "sslmode" not in SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL += "?sslmode=require"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"sslmode": "require"}
)
```

---

## 🔄 GITHUB ACTIONS CI/CD

### ❌ Problema #8: Workflow no se ejecuta tras push
**Síntoma**:
- Push a main no dispara workflow
- Workflow existe pero aparece como "skipped"

**Diagnóstico**:
```yaml
# Verificar triggers en .github/workflows/*.yml
on:
  push:
    branches: [ main ]  # Debe coincidir con branch actual
  workflow_dispatch:     # Permite trigger manual
```

**Solución**:
1. Verificar que el push va a la branch correcta (main)
2. Quitar paths restrictivos si existen
3. Verificar que el workflow file está en `.github/workflows/`
4. Usar `workflow_dispatch` para trigger manual

---

### ❌ Problema #9: Secrets no configurados o expirados
**Síntoma**:
- Error: "Error: Could not authenticate"
- Workflow falla en steps de deployment

**Solución**:
```bash
# Verificar secrets en GitHub Repository Settings > Secrets
# Secrets requeridos:
AZURE_STATIC_WEB_APPS_API_TOKEN
AZURE_CONTAINER_REGISTRY_LOGIN_SERVER
AZURE_CONTAINER_REGISTRY_USERNAME  
AZURE_CONTAINER_REGISTRY_PASSWORD

# Regenerar SWA token si está expirado
az staticwebapp secrets list --name RecWayFrontend --resource-group rg-recway-prod
```

---

### ❌ Problema #10: Node_modules en repository
**Síntoma**:
- Git commit incluye miles de archivos
- Repository muy pesado
- Build failures por conflictos

**Solución**:
```bash
# Limpiar repository
git reset --soft HEAD~1
git reset HEAD .
git clean -fd
rm -rf frontend/node_modules

# Asegurar .gitignore correcto
echo "frontend/node_modules/" >> .gitignore
echo "frontend/dist/" >> .gitignore

# Commit solo archivos necesarios
git add .github/workflows/
git add frontend/package.json
git add frontend/src/
git commit -m "Fix deployment"
```

---

## 📦 AZURE CONTAINER REGISTRY

### ❌ Problema #11: Image push failures
**Síntoma**:
- Error: "unauthorized: authentication required"
- Docker push falla en GitHub Actions

**Solución**:
```bash
# Verificar credentials
az acr credential show --name recwayregistry

# En GitHub Actions, verificar secrets:
# AZURE_CONTAINER_REGISTRY_LOGIN_SERVER=recwayregistry.azurecr.io
# AZURE_CONTAINER_REGISTRY_USERNAME=recwayregistry
# AZURE_CONTAINER_REGISTRY_PASSWORD=[admin password]

# Workflow step correcto:
- name: Build and push image
  run: |
    docker build -t ${{ secrets.AZURE_CONTAINER_REGISTRY_LOGIN_SERVER }}/recway-backend:latest .
    docker push ${{ secrets.AZURE_CONTAINER_REGISTRY_LOGIN_SERVER }}/recway-backend:latest
```

---

## 🔧 VARIABLES DE ENTORNO

### ❌ Problema #12: Environment variables no definidas
**Síntoma**:
- Error 500 en backend por missing variables
- Frontend no conecta a API

**Checklist de Variables**:

**Frontend (.env.production)**:
```bash
VITE_API_URL=https://recway-backend.kindmoss-bca66faa.eastus.azurecontainerapps.io/api/v1
VITE_API_BASE_URL=https://recway-backend.kindmoss-bca66faa.eastus.azurecontainerapps.io
```

**Backend (Azure Key Vault)**:
```bash
DATABASE_URL=postgresql://recwayadmin:***@recway-db-server.postgres.database.azure.com/recway_prod?sslmode=require
SECRET_KEY=***
ENVIRONMENT=production
```

**Solución**:
```bash
# Verificar variables en Container Apps
az containerapp show --name recway-backend --resource-group rg-recway-prod \
  --query "properties.template.containers[0].env"

# Agregar variable faltante
az containerapp update --name recway-backend --resource-group rg-recway-prod \
  --set-env-vars VARIABLE_NAME=secretref:variable-secret-name
```

---

## 🌐 CONECTIVIDAD Y NETWORKING

### ❌ Problema #13: CORS errors en frontend
**Síntoma**:
- Error en browser console: "blocked by CORS policy"
- Frontend no puede hacer requests al backend

**Solución Backend (FastAPI)**:
```python
# En main.py
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configurar CORS para producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ashy-ground-06348160f.1.azurestaticapps.net",
        "http://localhost:5173",  # Para desarrollo
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## ⚡ PERFORMANCE Y SCALING

### ❌ Problema #14: Slow response times
**Síntoma**:
- API responses > 1 segundo
- Frontend lento al cargar

**Diagnóstico y Optimización**:
```bash
# Verificar métricas de Container Apps
az monitor metrics list \
  --resource "/subscriptions/.../resourceGroups/rg-recway-prod/providers/Microsoft.App/containerApps/recway-backend" \
  --metric "Requests" \
  --interval PT1M

# Verificar uso de CPU/Memory
az monitor metrics list \
  --resource "/subscriptions/.../resourceGroups/rg-recway-prod/providers/Microsoft.App/containerApps/recway-backend" \
  --metric "UsageNanoCores,WorkingSetBytes" \
  --interval PT1M
```

**Optimizaciones**:
1. Aumentar recursos del container si necesario
2. Optimizar queries de base de datos
3. Implementar caching
4. Verificar que auto-scaling funciona

---

## 🔍 HERRAMIENTAS DE DIAGNÓSTICO

### Comandos Útiles para Debugging

**Container Apps**:
```bash
# Ver logs en tiempo real
az containerapp logs show --name recway-backend --resource-group rg-recway-prod --follow

# Verificar estado de health
curl https://recway-backend.kindmoss-bca66faa.eastus.azurecontainerapps.io/health

# Ver configuración completa
az containerapp show --name recway-backend --resource-group rg-recway-prod
```

**Static Web Apps**:
```bash
# Verificar deployment status
az staticwebapp show --name RecWayFrontend --resource-group rg-recway-prod

# Ver build logs (en GitHub Actions)
# GitHub > Actions > Latest workflow run > View logs
```

**PostgreSQL**:
```bash
# Test connection
az postgres flexible-server connect --name recway-db-server --username recwayadmin

# Ver métricas
az monitor metrics list --resource "/subscriptions/.../resourceGroups/rg-recway-prod/providers/Microsoft.DBforPostgreSQL/flexibleServers/recway-db-server" --metric "cpu_percent,memory_percent"
```

---

## 📞 ESCALACIÓN Y CONTACTOS

### Niveles de Soporte
1. **Nivel 1**: Self-service usando esta guía
2. **Nivel 2**: Verificar Azure Service Health
3. **Nivel 3**: Crear ticket de soporte Azure
4. **Nivel 4**: Contactar especialista en arquitectura

### Resources de Ayuda
- **Azure Status**: https://status.azure.com/
- **GitHub Status**: https://www.githubstatus.com/
- **Azure Support**: https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade
- **Documentation**: https://docs.microsoft.com/azure/

### Información para Soporte
Al crear tickets, incluir:
- Resource Group: `rg-recway-prod`
- Subscription ID: [subscription-id]
- Region: East US
- Timestamp del problema
- Error messages exactos
- Pasos para reproducir

---

**🛠️ Guía Mantenida por**: Equipo DevOps RecWay  
**📅 Última Actualización**: 17 de Septiembre, 2025  
**📋 Basada en**: Problemas reales resueltos durante deployment  
**🔄 Próxima Revisión**: 1 de Octubre, 2025