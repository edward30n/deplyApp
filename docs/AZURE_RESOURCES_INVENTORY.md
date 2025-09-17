#  Inventario de Recursos Azure - RecWay Production

**Fecha**: 2025-09-17  
**Estado**: Deployment Ready - Arquitectura Limpia  
**Repositorio**: https://github.com/edward30n/deplyApp  

##  Arquitectura de Deployment

Arquitectura **"Git push y listo"** con escalabilidad y buenas prácticas:

| Componente | Servicio Azure | Nombre del Recurso | Propósito |
|------------|----------------|-------------------|-----------|
| **Frontend** | Static Web Apps | ecway-frontend | CDN global, SSL automático |
| **Backend** | App Service Linux | ecway-backend-central | API FastAPI con autoscale |
| **Base de Datos** | PostgreSQL Flexible | ecway-db-new | Base de datos principal |
| **Imágenes** | Container Registry | ecwayacr2 | Imágenes Docker del backend |
| **Archivos** | Storage Account | ecwaystorage02 | Archivos y procesamiento |
| **Secretos** | Key Vault | ecway-keyvault-02 | Gestión segura de secretos |
| **Monitoreo** | Application Insights | ecway-ai | Observabilidad y telemetría |
| **Escalado** | App Service Plan S1 | ecway-plan-prod | Autoscale + slots |

---

##  Recursos Creados por el Bootstrap

### Resource Group: ecway-rg
**Ubicación**: East US

| Recurso | Tipo | SKU/Plan | Estado | Configuración Especial |
|---------|------|----------|--------|----------------------|
| ecwayacr2 | Container Registry | Standard |  Activo | Admin deshabilitado, Managed Identity |
| ecway-keyvault-02 | Key Vault | Standard |  Activo | Managed Identity access |
| ecway-db-new | PostgreSQL Flexible | B1ms |  Activo | v16, SSL required, Public access |
| ecwaystorage02 | Storage Account | Standard_LRS |  Activo | Para uploads y procesamiento |
| ecway-plan-prod | App Service Plan | S1 Linux |  Activo | **Autoscale habilitado** |
| ecway-backend-central | App Service | - |  Activo | **Slots: staging**, Managed Identity |
| ecway-ai | Application Insights | - |  Activo | Conectado al App Service |

### Configuraciones Especiales

#### Autoscale Configuration
- **Mínimo**: 1 instancia
- **Máximo**: 3 instancias  
- **Scale Out**: CPU >70% durante 10 min
- **Scale In**: CPU <30% durante 10 min

#### Security & Identity
- **Managed Identity**: Habilitada en App Service
- **Roles asignados**:
  - AcrPull en Container Registry
  - Key Vault Secrets User en Key Vault

#### Deployment Slots
- **Production**: Slot principal
- **Staging**: Para blue-green deployments

---

##  Secretos en Key Vault

| Secret Name | Propósito | Formato |
|-------------|-----------|---------|
| ecway-secret-key | JWT signing key | String fuerte para firmas |
| ecway-db-uri | Database connection | postgresql://user:pass@server:5432/db?sslmode=require |
| ecway-storage-conn | Azure Storage | Connection string completa |

---

##  CI/CD Pipeline

### GitHub Actions Workflows

#### Backend Pipeline (.github/workflows/deploy_backend.yml)
**Triggers**: Push a main con cambios en ackend/**

1. **OIDC Login** a Azure (sin secretos hardcodeados)
2. **Build & Push** imagen Docker a ACR
3. **Deploy** a App Service con nuevo tag
4. **Configure** app settings base
5. **Restart** aplicación

#### Frontend Pipeline (.github/workflows/deploy_frontend_swa.yml)  
**Triggers**: Push a main con cambios en rontend/**

1. **Build** aplicación Vite/React
2. **Configure** VITE_API_URL para producción
3. **Deploy** a Static Web Apps

### App Settings Configurados

`ash
WEBSITES_PORT=8000
ENV=azure
API_V1_STR=/api/v1
ENABLE_FILE_WATCHER=false
FRONTEND_URL=https://recway-frontend.azurestaticapps.net
CORS_ORIGINS=["https://recway-frontend.azurestaticapps.net"]

# Key Vault References
SECRET_KEY=@Microsoft.KeyVault(SecretUri=https://recway-keyvault-02.vault.azure.net/secrets/recway-secret-key/)
DATABASE_URI=@Microsoft.KeyVault(SecretUri=https://recway-keyvault-02.vault.azure.net/secrets/recway-db-uri/)
AZURE_STORAGE_CONNECTION_STRING=@Microsoft.KeyVault(SecretUri=https://recway-keyvault-02.vault.azure.net/secrets/recway-storage-conn/)
`

---

##  URLs de Verificación

### Endpoints de Health Check
- **Backend**: https://recway-backend-central.azurewebsites.net/health
- **API Stats**: https://recway-backend-central.azurewebsites.net/api/v1/recway/processing-stats
- **Frontend**: https://recway-frontend.azurestaticapps.net

### Monitoreo
- **Application Insights**: Azure Portal  recway-ai
- **App Service Metrics**: Azure Portal  recway-backend-central  Metrics
- **Logs en tiempo real**: z webapp log tail -g recway-rg -n recway-backend-central

---

##  Operaciones Diarias

### Deployment
`ash
# Automatic deployment
git push origin main
`

### Rollback
`ash
# Cambiar a tag anterior
az webapp config container set -g recway-rg -n recway-backend-central \
  --docker-custom-image-name recwayacr2.azurecr.io/recway-backend:prod-<commit_anterior>

# O usar slot swap
az webapp deployment slot swap -g recway-rg -n recway-backend-central --slot staging
`

### Scaling Manual
`ash
# Aumentar máximo de instancias
az monitor autoscale update -g recway-rg -n autoscale-recway-backend-central --max-count 10

# Upgrade a Premium plan
az appservice plan update -g recway-rg -n recway-plan-prod --sku P1V3
`

---

##  Estado del Deployment

-  **Infraestructura**: Creada y configurada
-  **CI/CD**: Workflows funcionando  
-  **Seguridad**: Key Vault + Managed Identity
-  **Escalabilidad**: Autoscale configurado
-  **Monitoreo**: Application Insights activo
-  **Database**: Schema aplicado
-  **Documentación**: Actualizada

** ESTADO: PRODUCTION READY**

---

**Última actualización**: 2025-09-17  
**Próxima revisión**: Después del primer deployment  
**Responsable**: DevOps Team  
