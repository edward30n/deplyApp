#  RecWay Documentation Hub

Documentación completa para el deployment y operación de RecWay en Azure.

##  Quick Start

**¿Nuevo en el proyecto?** Sigue esta secuencia:

1. **[DEPLOYMENT_README.md](DEPLOYMENT_README.md)**  Guía paso a paso completa
2. **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**  Metodología y configuración técnica  
3. **[AZURE_RESOURCES_INVENTORY.md](AZURE_RESOURCES_INVENTORY.md)**  Inventario de recursos Azure

##  Índice de Documentación

| Documento | Propósito | Estado |
|-----------|-----------|--------|
| **[DEPLOYMENT_README.md](DEPLOYMENT_README.md)** |  Guía completa paso a paso |  Actualizado |
| **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** |  Metodología técnica detallada |  Actualizado |
| **[AZURE_RESOURCES_INVENTORY.md](AZURE_RESOURCES_INVENTORY.md)** |  Inventario de recursos Azure |  Actualizado |
| **[AZURE_SWA_DEPLOYMENT.md](AZURE_SWA_DEPLOYMENT.md)** |  Static Web Apps específico |  Legacy |

##  Arquitectura Overview

`
 Frontend (Static Web Apps)
     HTTPS/CDN Global
    
 App Service S1 (Autoscale 13)
    
    
 Container (ACR) +  PostgreSQL +  Key Vault
    
    
 Application Insights +  Storage Account
`

### Componentes Clave
- **"Git push y listo"**: CI/CD automático con GitHub Actions
- **Escalabilidad**: Autoscale automático basado en CPU
- **Seguridad**: Managed Identity + Key Vault references
- **Zero Downtime**: Blue-green deployment con slots
- **Observabilidad**: Application Insights + health checks

##  Deployment Flow

`mermaid
graph LR
    A[git push main] --> B[GitHub Actions]
    B --> C[Build Docker]
    C --> D[Push to ACR]
    D --> E[Deploy App Service]
    E --> F[Build React]
    F --> G[Deploy SWA]
    G --> H[ Live]
`

##  Guías por Rol

###  Desarrollador
1. **Setup Local**: Seguir configuración en DEPLOYMENT_GUIDE.md
2. **Variables de Entorno**: Copiar .env.local  .env
3. **Desarrollo**: 
pm run dev (frontend) + uvicorn app.main:app --reload (backend)
4. **Deploy**: git push origin main

###  DevOps/SRE
1. **Bootstrap Inicial**: ./infra/scripts/azure_bootstrap.sh
2. **Configurar Secretos**: Key Vault + GitHub Secrets
3. **Monitoreo**: Application Insights + alertas
4. **Scaling**: Configurar autoscale rules

###  Operations
1. **Health Checks**: URLs en AZURE_RESOURCES_INVENTORY.md
2. **Logs**: z webapp log tail -g recway-rg -n recway-backend-central
3. **Rollback**: Slot swap o cambio de imagen
4. **Scaling**: Azure Portal o Azure CLI

##  Configuración por Entorno

###  Local Development
`ash
# Backend
ENV=local
DATABASE_URI=postgresql://user:pass@localhost:5432/recway_db
FRONTEND_URL=http://localhost:5173

# Frontend  
VITE_API_URL=http://localhost:8000
`

###  Azure Production
`ash
# Backend (vía Key Vault)
ENV=azure
DATABASE_URI=@Microsoft.KeyVault(SecretUri=...)
FRONTEND_URL=https://recway-frontend.azurestaticapps.net

# Frontend (build-time)
VITE_API_URL=https://recway-backend-central.azurewebsites.net
`

##  Checklist de Estado

###  Infraestructura
-  **Recursos Azure**: Creados vía bootstrap script
-  **CI/CD Pipeline**: GitHub Actions configurado
-  **Base de Datos**: Schema PostgreSQL listo
-  **Seguridad**: Key Vault + Managed Identity
-  **Monitoring**: Application Insights configurado

###  Deployment Pipeline
-  **Backend**: ACR  App Service con autoscale
-  **Frontend**: Static Web Apps con CDN
-  **Database**: PostgreSQL Flexible con SSL
-  **Storage**: Azure Storage para archivos

###  Operaciones
-  **Health Checks**: /health endpoint configurado
-  **Logging**: Structured logs + Application Insights
-  **Alerting**: Configurado para CPU, memoria, errores
-  **Backup**: Automated database backups

##  Emergency Procedures

###  Rollback Rápido
`ash
# Cambiar a imagen anterior
az webapp config container set -g recway-rg -n recway-backend-central \
  --docker-custom-image-name recwayacr2.azurecr.io/recway-backend:prod-<commit-anterior>

# O usar slot swap
az webapp deployment slot swap -g recway-rg -n recway-backend-central --slot staging
`

###  Debugging
`ash
# Ver logs en tiempo real
az webapp log tail -g recway-rg -n recway-backend-central

# Ver configuración
az webapp config appsettings list -g recway-rg -n recway-backend-central
`

##  Contactos

- **Repository**: https://github.com/edward30n/deplyApp
- **Issues**: GitHub Issues
- **Documentation**: Esta carpeta /docs

---

** Última actualización**: 2025-09-17  
** Estado**: Production Ready  
** Mantenido por**: DevOps Team
