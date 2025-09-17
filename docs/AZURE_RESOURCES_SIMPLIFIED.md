# Azure Resources Inventory - RecWay Project (ACTUALIZADO - SOLO RECURSOS ACTIVOS)

## 📊 ESTADO ACTUAL DE RECURSOS AZURE
**Fecha de actualización**: 17 de Septiembre, 2025  
**Estado del proyecto**: ✅ PRODUCCIÓN OPERATIVA  
**Subscription**: Azure Subscription  
**Región Principal**: East US  

---

## 🏗️ ARQUITECTURA SIMPLIFICADA (SOLO RECURSOS ACTIVOS)

```
                    ┌─────────────────────────────────────┐
                    │        AZURE SUBSCRIPTION           │
                    │                                     │
   ┌────────────────┼─────────────────────────────────────┼────────────────┐
   │                │          RESOURCE GROUP             │                │
   │                │         rg-recway-prod              │                │
   │                └─────────────────────────────────────┘                │
   │                                                                       │
   │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐ │
   │  │  Static Web     │ │  App Service    │ │      PostgreSQL         │ │
   │  │     Apps        │ │    Central      │ │   Flexible Server       │ │
   │  │                 │ │                 │ │                         │ │
   │  │ Frontend React  │ │ Backend FastAPI │ │ recway-db-server        │ │
   │  └─────────────────┘ └─────────────────┘ └─────────────────────────┘ │
   │                                                                       │
   │  ┌─────────────────┐                                                  │
   │  │   Key Vault     │          📝 NOTA: Solo 4 recursos               │
   │  │                 │             necesarios para el                  │
   │  │ kv-recway-prod  │             código actual                       │
   │  └─────────────────┘                                                  │
   └───────────────────────────────────────────────────────────────────────┘
```

---

## 📋 RECURSOS ACTIVOS (ÚNICAMENTE LOS USADOS)

### 1. 🌐 Azure Static Web Apps
**Nombre**: `RecWay Frontend`  
**Resource Group**: `rg-recway-prod`  
**Ubicación**: East US 2  
**SKU**: Free Tier  
**Estado**: ✅ **ACTIVO Y FUNCIONAL**

#### URLs y Endpoints
- **🌐 Primary URL**: https://ashy-ground-06348160f.1.azurestaticapps.net/
- **📊 Status**: ✅ Active
- **🔄 Deployment**: GitHub Actions automatizado
- **⚡ Build Status**: ✅ Success

---

### 2. 🚀 Azure App Service Central
**Nombre**: `recway-backend-central`  
**Resource Group**: `rg-recway-prod`  
**Ubicación**: Central US  
**SKU**: B1 (Basic)  
**Estado**: ✅ **ÚNICO BACKEND FUNCIONAL**

#### URLs y Endpoints
- **🔧 API Base URL**: https://recway-backend-central.azurewebsites.net
- **❤️ Health Check**: https://recway-backend-central.azurewebsites.net/health ✅
- **🌍 Countries API**: https://recway-backend-central.azurewebsites.net/api/v1/countries ✅
- **📚 API Documentation**: https://recway-backend-central.azurewebsites.net/docs

#### Configuración
- **Runtime**: Python 3.11
- **Health Check**: Configurado en `/health`
- **Managed Identity**: Habilitado para Key Vault
- **CORS**: Configurado para Static Web Apps

---

### 3. 🗄️ PostgreSQL Flexible Server
**Nombre**: `recway-db-server`  
**Resource Group**: `rg-recway-prod`  
**Ubicación**: East US  
**SKU**: B1ms (Burstable, 1 vCore, 2GB RAM)  
**Estado**: ✅ **OPERATIVO**

#### Connection Details
- **🔌 Server**: recway-db-server.postgres.database.azure.com
- **🚪 Port**: 5432
- **🗃️ Database**: recway_prod
- **👤 Admin User**: recwayadmin
- **🔐 SSL Mode**: Required

#### Security Configuration
- **Firewall**: Solo servicios Azure permitidos
- **SSL**: Forzado
- **Backup**: 7 días de retención

---

### 4. 🔐 Azure Key Vault
**Nombre**: `kv-recway-prod`  
**Resource Group**: `rg-recway-prod`  
**Ubicación**: East US  
**SKU**: Standard  
**Estado**: ✅ **CONFIGURADO PARA SECRETOS**

#### Secrets Configurados
- `database-url`: Connection string para PostgreSQL
- `secret-key`: JWT secret para autenticación
- Otros secretos de aplicación según necesidad

#### Access Policies
- **App Service Central**: Permisos de lectura de secretos
- **Managed Identity**: Configurado correctamente

---

## 💰 COSTOS ACTUALES (SOLO RECURSOS ACTIVOS)

| Servicio | SKU | Costo/Mes (Estimado) |
|----------|-----|----------------------|
| Static Web Apps | Free | $0.00 |
| App Service Central | B1 | ~$13.00 |
| PostgreSQL Flexible | B1ms | ~$25.00 |
| Key Vault | Standard | ~$3.00 |
| **TOTAL SIMPLIFICADO** | | **~$41.00/mes** |

**💡 Ahorro logrado**: Reducción de ~$77 a ~$41 = **47% de ahorro**

---

## ❌ RECURSOS ELIMINADOS (NO USADOS POR EL CÓDIGO)

### Eliminados del Código y Configuración:
1. ❌ **Azure Container Apps** - Health check funcionaba, APIs fallaban
2. ❌ **Azure Container Registry** - Solo alimentaba Container Apps no funcional  
3. ❌ **App Service Dev** - Duplicado, APIs fallaban
4. ❌ **Storage Account** - Archivos ML están almacenados localmente
5. ❌ **Application Insights** - No configurado en código actual
6. ❌ **Autoscaling Rules** - No necesarios para B1
7. ❌ **Staging Slots** - No usados

### Archivos de Configuración Eliminados:
- `backend/Dockerfile` 
- `backend/Dockerfile.azure`
- `frontend/Dockerfile`
- `.github/workflows/azure-deploy.yml` (Container Apps)

### Scripts Simplificados:
- `infra/scripts/azure_bootstrap.sh` - Solo recursos necesarios
- `backend/.env.azure` - Sin referencias a Storage Account

---

## 🔄 GITHUB ACTIONS (SOLO LO NECESARIO)

### Workflow Activo:
- **azure-swa-deploy.yml**: ✅ Deploy de Static Web Apps
  - Trigger: Push a main (frontend changes)
  - Funcionando correctamente

### Secrets Necesarios:
- `AZURE_STATIC_WEB_APPS_API_TOKEN`: Para deployment de frontend

---

## 🎯 CONFIGURACIÓN FINAL RECOMENDADA

### Para App Service Central:
```bash
# Variables de entorno necesarias:
WEBSITES_PORT=8000
ENV=production
API_V1_STR=/api/v1
FRONTEND_URL=https://ashy-ground-06348160f.1.azurestaticapps.net
CORS_ORIGINS=["https://ashy-ground-06348160f.1.azurestaticapps.net"]
SECRET_KEY=@Microsoft.KeyVault(SecretUri=https://kv-recway-prod.vault.azure.net/secrets/secret-key/)
DATABASE_URI=@Microsoft.KeyVault(SecretUri=https://kv-recway-prod.vault.azure.net/secrets/database-url/)
```

### Para Static Web Apps:
```bash
# Frontend configurado con:
VITE_API_URL=https://recway-backend-central.azurewebsites.net
```

---

**📊 Estado**: ARQUITECTURA SIMPLIFICADA Y OPTIMIZADA  
**🔄 Próxima revisión**: 24 de Septiembre, 2025  
**👤 Responsable**: Equipo DevOps RecWay  
**💡 Resultado**: 47% de ahorro en costos, 100% funcionalidad mantenida