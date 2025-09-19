# Troubleshooting Guide - RecWay Sistema

## 📋 Guía Completa de Resolución de Problemas

**Última Actualización**: 19 de Septiembre, 2025  
**Sistema**: RecWay en Azure P1v2 con FileWatcher  
**Estado**: Documentación actualizada para sistema actual

## 🎯 Endpoints Actuales para Testing

### URLs de Producción
```bash
# Frontend
Frontend: https://green-rock-0e0abfc10.1.azurestaticapps.net/

# Backend API
API Base: https://recway-backend-central.azurewebsites.net
Health: https://recway-backend-central.azurewebsites.net/api/v1/test
Docs: https://recway-backend-central.azurewebsites.net/docs
CSV Upload: https://recway-backend-central.azurewebsites.net/api/v1/files/upload-csv
```

### Quick Health Check
```bash
# Test básico del sistema
curl -X GET "https://recway-backend-central.azurewebsites.net/api/v1/test"
# Expected: {"status": "healthy", "timestamp": "..."}

# Test de documentación API
curl -X GET "https://recway-backend-central.azurewebsites.net/docs"
# Expected: Swagger UI HTML response
```

## 🔧 Problemas Comunes del Sistema

### 1. FileWatcher Issues

#### Problema: FileWatcher no procesa CSV uploads
```bash
# Verificar estado del FileWatcher
curl -X GET "https://recway-backend-central.azurewebsites.net/api/v1/filewatcher/status"

# Verificar logs de Azure App Service
az webapp log tail --name recway-backend-central --resource-group recway-central-rg

# Síntomas comunes:
# - CSVs uploaded pero no procesados
# - No aparecen archivos en uploads/csv/
# - Errores de memoria en logs
```

**Soluciones**:
```bash
# 1. Verificar que ENABLE_FILE_WATCHER=true en Azure
az webapp config appsettings list --name recway-backend-central --resource-group recway-central-rg | grep ENABLE_FILE_WATCHER

# 2. Verificar memoria disponible (P1v2 = 3.5GB)
az webapp show --name recway-backend-central --resource-group recway-central-rg --query "sku"

# 3. Restart app service si es necesario
az webapp restart --name recway-backend-central --resource-group recway-central-rg
```

#### Problema: Errores de memoria con ML libraries
```bash
# Error típico en logs:
# "MemoryError: Unable to allocate array"
# "Worker timeout"
```

**Soluciones**:
```bash
# Verificar plan actual (debe ser P1v2)
az appservice plan show --name recway-plan-central --resource-group recway-central-rg

# Si es B1, scale up a P1v2:
az appservice plan update --name recway-plan-central --resource-group recway-central-rg --sku P1v2

# Verificar memoria usage
az webapp show --name recway-backend-central --resource-group recway-central-rg --query "sku.capacity"
```

### 2. Backend API Issues

#### Problema: 502 Bad Gateway
```bash
# Síntomas:
# - API endpoints return 502
# - App no responde
# - Timeout errors
```

**Diagnóstico**:
```bash
# 1. Check app service status
az webapp show --name recway-backend-central --resource-group recway-central-rg --query "state"

# 2. Check logs
az webapp log tail --name recway-backend-central --resource-group recway-central-rg

# 3. Check deployment status
az webapp deployment list --name recway-backend-central --resource-group recway-central-rg
```

**Soluciones**:
```bash
# 1. Restart app service
az webapp restart --name recway-backend-central --resource-group recway-central-rg

# 2. Check environment variables
az webapp config appsettings list --name recway-backend-central --resource-group recway-central-rg

# 3. Re-deploy if necessary
# (Trigger GitHub Actions workflow o push to main)
```

#### Problema: Database Connection Issues
```bash
# Error típico:
# "could not connect to server: Connection refused"
# "SSL connection error"
```

**Diagnóstico**:
```bash
# 1. Check database status
az postgres flexible-server show --name recway-db-new --resource-group recway-central-rg

# 2. Check connection string
az webapp config appsettings list --name recway-backend-central --resource-group recway-central-rg | grep DATABASE_URL

# 3. Test connection from Azure CLI
az postgres flexible-server connect --name recway-db-new --admin-user [username] --database-name postgres
```

**Soluciones**:
```bash
# 1. Restart database if needed
az postgres flexible-server restart --name recway-db-new --resource-group recway-central-rg

# 2. Update connection string if changed
az webapp config appsettings set --name recway-backend-central --resource-group recway-central-rg --settings DATABASE_URL="new-connection-string"

# 3. Check firewall rules
az postgres flexible-server firewall-rule list --name recway-db-new --resource-group recway-central-rg
```

### 3. Frontend Issues

#### Problema: Frontend no carga o 404 errors
```bash
# Síntomas:
# - Blank page
# - 404 en rutas
# - Assets no cargan
```

**Diagnóstico**:
```bash
# 1. Check Static Web App status
az staticwebapp show --name recway-frontend --resource-group recway-central-rg

# 2. Check last deployment
az staticwebapp environment list --name recway-frontend

# 3. Test direct URL
curl -I https://green-rock-0e0abfc10.1.azurestaticapps.net/
```

**Soluciones**:
```bash
# 1. Check staticwebapp.config.json routing
# Debe incluir navigationFallback para SPA

# 2. Re-deploy frontend
# Push to main branch o trigger GitHub Actions

# 3. Clear CDN cache
az staticwebapp hostname delete --name recway-frontend --hostname green-rock-0e0abfc10.1.azurestaticapps.net
az staticwebapp hostname set --name recway-frontend --hostname green-rock-0e0abfc10.1.azurestaticapps.net
```

#### Problema: API calls failing from frontend
```bash
# Error típico en browser console:
# "CORS error"
# "Network error"
# "Failed to fetch"
```

**Soluciones**:
```javascript
// 1. Verificar API base URL en frontend
console.log('API URL:', import.meta.env.VITE_API_BASE_URL)

// 2. Verificar CORS en backend
// app/main.py debe incluir frontend domain
```

```python
# Backend CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://green-rock-0e0abfc10.1.azurestaticapps.net"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. CI/CD Issues

#### Problema: GitHub Actions deployment failure
```bash
# Síntomas:
# - Workflow fails
# - Red X en GitHub Actions
# - Deployment not triggered
```

**Diagnóstico**:
```bash
# 1. Check GitHub Actions logs
# GitHub → Actions → Failed workflow → Logs

# 2. Check secrets
# GitHub → Settings → Secrets and variables → Actions

# 3. Verify Azure resources exist
az webapp list --resource-group recway-central-rg --output table
az staticwebapp list --resource-group recway-central-rg --output table
```

**Soluciones**:
```bash
# 1. Update GitHub secrets if expired
# AZURE_PUBLISH_PROFILE might need refresh:
az webapp deployment list-publishing-profiles --name recway-backend-central --resource-group recway-central-rg --xml

# 2. Re-trigger workflow
# GitHub → Actions → Re-run failed jobs

# 3. Check workflow file syntax
# .github/workflows/ YAML validation
```

## 📊 Performance Issues

### High Memory Usage (P1v2 Plan)
```bash
# Monitor memory usage
az webapp log tail --name recway-backend-central --resource-group recway-central-rg | grep -i memory

# Memory optimization tips:
# 1. Limit ML model loading in FileWatcher
# 2. Use pagination for large CSV files
# 3. Clear cache periodically
```

### Slow Response Times
```bash
# Test response times
curl -w "@curl-format.txt" -o /dev/null -s "https://recway-backend-central.azurewebsites.net/api/v1/test"

# curl-format.txt content:
# time_namelookup:  %{time_namelookup}\n
# time_connect:     %{time_connect}\n
# time_total:       %{time_total}\n
```

**Optimizaciones**:
```bash
# 1. Enable Application Insights
az monitor app-insights component create --app recway-insights --location CentralUS --resource-group recway-central-rg

# 2. Scale up if needed
az appservice plan update --name recway-plan-central --resource-group recway-central-rg --sku P2v2

# 3. Add CDN for static content
az cdn profile create --name recway-cdn --resource-group recway-central-rg --sku Standard_Microsoft
```

## 🛠️ Debug Commands Útiles

### Sistema General
```bash
# Resource overview
az resource list --resource-group recway-central-rg --output table

# Check all app services
az webapp list --resource-group recway-central-rg --query "[].{Name:name,State:state,URL:defaultHostName}" --output table

# Monitor costs
az consumption usage list --top 10 --output table
```

### Backend Específico
```bash
# Application logs
az webapp log tail --name recway-backend-central --resource-group recway-central-rg

# Environment variables
az webapp config appsettings list --name recway-backend-central --resource-group recway-central-rg --output table

# Deployment slots
az webapp deployment slot list --name recway-backend-central --resource-group recway-central-rg

# Scale info
az appservice plan show --name recway-plan-central --resource-group recway-central-rg --query "{Name:name,Sku:sku,NumberOfWorkers:numberOfWorkers}"
```

### Database Específico
```bash
# Database status
az postgres flexible-server show --name recway-db-new --resource-group recway-central-rg --query "{Name:name,State:state,Version:version}"

# Connection info
az postgres flexible-server show --name recway-db-new --resource-group recway-central-rg --query "fullyQualifiedDomainName"

# Firewall rules
az postgres flexible-server firewall-rule list --name recway-db-new --resource-group recway-central-rg --output table
```

### Frontend Específico
```bash
# Static Web App status
az staticwebapp show --name recway-frontend --resource-group recway-central-rg --query "{Name:name,DefaultHostname:defaultHostname,RepositoryUrl:repositoryUrl}"

# Environments
az staticwebapp environment list --name recway-frontend --output table

# Custom domains
az staticwebapp hostname list --name recway-frontend --output table
```

## 🚨 Emergency Procedures

### Complete System Recovery
```bash
# 1. Stop all services
az webapp stop --name recway-backend-central --resource-group recway-central-rg

# 2. Backup database
az postgres flexible-server backup list --name recway-db-new --resource-group recway-central-rg

# 3. Restart in order
az postgres flexible-server restart --name recway-db-new --resource-group recway-central-rg
sleep 30
az webapp start --name recway-backend-central --resource-group recway-central-rg

# 4. Verify all endpoints
curl https://recway-backend-central.azurewebsites.net/api/v1/test
curl https://green-rock-0e0abfc10.1.azurestaticapps.net/
```

### Rollback Deployment
```bash
# Backend rollback
az webapp deployment slot swap --name recway-backend-central --resource-group recway-central-rg --slot staging --target-slot production

# Frontend rollback
# Use GitHub Actions to revert to previous commit
git revert [commit-hash]
git push origin main
```

## 📞 Support Information

### Azure Support
- **Subscription**: Check Azure portal for support plans
- **Docs**: https://docs.microsoft.com/en-us/azure/
- **Status**: https://status.azure.com/

### GitHub Support  
- **Actions**: https://docs.github.com/en/actions
- **Status**: https://www.githubstatus.com/

### Application Logs Locations
- **Backend**: Azure Portal → App Service → Log stream
- **Database**: Azure Portal → PostgreSQL → Logs  
- **Frontend**: GitHub Actions logs for deployment issues

---

## ✅ Troubleshooting Checklist

### When System is Down
- [ ] Check Azure resource status (all resources)
- [ ] Verify GitHub Actions workflows
- [ ] Test all endpoints with curl
- [ ] Check application logs
- [ ] Verify database connectivity
- [ ] Confirm environment variables
- [ ] Test FileWatcher functionality
- [ ] Verify P1v2 plan is active
- [ ] Check memory and CPU usage
- [ ] Validate CORS configuration

### Before Calling for Help
- [ ] Collected relevant error messages
- [ ] Checked Azure portal status
- [ ] Reviewed GitHub Actions logs
- [ ] Tested endpoints manually
- [ ] Verified resource configuration
- [ ] Attempted basic restart procedures

**🎉 TROUBLESHOOTING GUIDE ACTUALIZADO Y COMPLETO! 🎉**