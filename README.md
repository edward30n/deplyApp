# RecWay - Deployment Ready ✅

Este es el repositorio limpio de RecWay, listo para deployment en Azure con escalabilidad y buenas prácticas.

## 🌐 URLs de Producción

- **Frontend**: https://ashy-ground-06348160f.1.azurestaticapps.net
- **Backend API**: https://recway-backend.kindmoss-bca66faa.eastus.azurecontainerapps.io
- **Health Check**: https://recway-backend.kindmoss-bca66faa.eastus.azurecontainerapps.io/health

**Última actualización**: 2025-09-17 16:27 UTC

##  Estructura del Proyecto

- ackend/ - API FastAPI con Python 3.11
- rontend/ - Aplicación React/Vite  
- docs/ - Documentación completa del proyecto
- infra/ - Scripts de infraestructura Azure
- .github/workflows/ - CI/CD con GitHub Actions

##  Quick Start

1. **Lee la documentación completa:** [docs/DEPLOYMENT_README.md](docs/DEPLOYMENT_README.md)
2. **Ejecuta el bootstrap de Azure:** ./infra/scripts/azure_bootstrap.sh
3. **Configura los secretos de GitHub**
4. **¡Haz push y listo!** git push origin main

##  Arquitectura

- **Frontend**: Azure Static Web Apps
- **Backend**: App Service Linux (Plan S1 + autoscale)
- **DB**: PostgreSQL Flexible Server
- **Storage**: Azure Storage Account
- **Secrets**: Key Vault con Managed Identity
- **CI/CD**: GitHub Actions con OIDC

¡Todo configurado para "git push y listo"! 
