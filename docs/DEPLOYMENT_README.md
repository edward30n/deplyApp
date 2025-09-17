# RecWay Azure Deployment Guide

## 🎯 Objetivo
"Git push y listo" con escalabilidad y buenas prácticas:

- **Frontend**: Azure Static Web Apps (SWA) - CDN global, SSL automático
- **Backend**: App Service Linux (Plan S1 para autoscale y slots)
- **Imágenes**: Azure Container Registry (ACR)
- **DB**: PostgreSQL Flexible Server
- **Archivos**: Azure Storage Account
- **Secretos**: Key Vault con Managed Identity
- **CI/CD**: GitHub Actions con OIDC (sin credenciales hardcodeadas)

## 📁 Estructura del Proyecto

```
/ (repo raíz)
├─ backend/
│  ├─ app/...
│  ├─ requirements.txt
│  └─ Dockerfile.azure          # ✅ Creado
├─ frontend/
│  ├─ src/...
│  └─ package.json
├─ infra/
│  └─ scripts/azure_bootstrap.sh # ✅ Creado
└─ .github/workflows/
   ├─ deploy_backend_clean.yml   # ✅ Creado
   └─ deploy_frontend_clean.yml  # ✅ Creado
```

## 🚀 Paso a Paso de Deployment

### 1. Provisionar Recursos de Azure (Una sola vez)

Ejecuta el script de bootstrap:

```bash
# Dale permisos de ejecución
chmod +x infra/scripts/azure_bootstrap.sh

# Ejecuta (asegúrate de estar logueado con az login)
./infra/scripts/azure_bootstrap.sh
```

**Recursos que crea:**
- Resource Group: `recway-rg`
- ACR: `recwayacr2`
- Key Vault: `recway-keyvault-02`
- PostgreSQL: `recway-db-new`
- Storage: `recwaystorage02`
- App Service Plan S1: `recway-plan-prod` (para autoscale/slots)
- Web App: `recway-backend-central`
- Application Insights: `recway-ai`
- Autoscale configurado (1→3 instancias según CPU)
- Slot staging para blue-green deployment

### 2. Configurar Secretos en Key Vault

```bash
RG=recway-rg
KV=recway-keyvault-02
PG=recway-db-new

# Secretos de aplicación
az keyvault secret set -n recway-secret-key --vault-name $KV --value "tu_jwt_secret_super_fuerte_aqui"

az keyvault secret set -n recway-db-uri --vault-name $KV \
  --value "postgresql://usuario:password@$PG.postgres.database.azure.com:5432/recWay_db?sslmode=require"

# Obtén la connection string del storage
STORAGE_CONN=$(az storage account show-connection-string -g $RG -n recwaystorage02 --query connectionString -o tsv)
az keyvault secret set -n recway-storage-conn --vault-name $KV --value "$STORAGE_CONN"
```

### 3. Configurar App Settings con Key Vault References

```bash
RG=recway-rg
KV=recway-keyvault-02
WEB=recway-backend-central
SWA=recway-frontend

az webapp config appsettings set -g $RG -n $WEB --settings \
  WEBSITES_PORT=8000 \
  ENV=azure \
  API_V1_STR=/api/v1 \
  ENABLE_FILE_WATCHER=false \
  FRONTEND_URL=https://$SWA.azurestaticapps.net \
  CORS_ORIGINS='["https://'$SWA'.azurestaticapps.net"]' \
  SECRET_KEY=@Microsoft.KeyVault\(SecretUri=https://$KV.vault.azure.net/secrets/recway-secret-key/\) \
  DATABASE_URI=@Microsoft.KeyVault\(SecretUri=https://$KV.vault.azure.net/secrets/recway-db-uri/\) \
  AZURE_STORAGE_CONNECTION_STRING=@Microsoft.KeyVault\(SecretUri=https://$KV.vault.azure.net/secrets/recway-storage-conn/\)
```

### 4. Configurar Azure Static Web App

1. Ve al **Azure Portal**
2. Crea un **Static Web App** con nombre: `recway-frontend`
3. Conecta con tu repo de GitHub
4. Copia el **Deployment Token** del portal

### 5. Configurar GitHub Secrets

En tu repo de GitHub → **Settings** → **Secrets and variables** → **Actions**:

#### Para OIDC (Backend):
```
AZURE_CLIENT_ID=xxx-xxx-xxx
AZURE_TENANT_ID=xxx-xxx-xxx  
AZURE_SUBSCRIPTION_ID=xxx-xxx-xxx
```

#### Para Static Web Apps (Frontend):
```
AZURE_STATIC_WEB_APPS_API_TOKEN=xxx (del portal de Azure SWA)
```

#### Configurar OIDC App Registration:
```bash
# Crear app registration para OIDC
az ad app create --display-name "RecWay-GitHub-OIDC" --sign-in-audience AzureADMyOrg

# Obtener el CLIENT_ID
CLIENT_ID=$(az ad app list --display-name "RecWay-GitHub-OIDC" --query "[0].appId" -o tsv)

# Crear service principal
az ad sp create --id $CLIENT_ID

# Asignar role contributor
az role assignment create --assignee $CLIENT_ID --role Contributor --scope /subscriptions/$(az account show --query id -o tsv)

# Configurar federated credential para GitHub
az ad app federated-credential create \
  --id $CLIENT_ID \
  --parameters '{
    "name": "RecWay-GitHub-Main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:edward30n/deplyApp:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'

echo "CLIENT_ID: $CLIENT_ID"
echo "TENANT_ID: $(az account show --query tenantId -o tsv)"
echo "SUBSCRIPTION_ID: $(az account show --query id -o tsv)"
```

### 6. Verificar Health Check en Backend

Agrega este endpoint a tu FastAPI si no lo tienes:

```python
# En app/main.py o donde tengas las rutas
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
```

## 🔄 Flujo de Deployment Diario

### Deployment Automático:
```bash
git add .
git commit -m "feat: nueva funcionalidad"
git push origin main
```

**Lo que sucede:**
1. **Frontend**: GitHub Actions compila Vite y despliega a SWA
2. **Backend**: GitHub Actions build Docker, push a ACR y App Service apunta al nuevo tag
3. **Resultado**: En ~5-10 minutos tienes todo actualizado

### Verificación Post-Deploy:
```bash
# Backend health check
curl https://recway-backend-central.azurewebsites.net/health

# Backend API check  
curl https://recway-backend-central.azurewebsites.net/api/v1/recway/processing-stats

# Frontend
open https://recway-frontend.azurestaticapps.net
```

## 🔧 Troubleshooting

### Ver logs en tiempo real:
```bash
# App Service logs
az webapp log tail -g recway-rg -n recway-backend-central

# Ver configuración actual
az webapp config appsettings list -g recway-rg -n recway-backend-central
```

### Rollback manual:
```bash
# Cambiar a tag anterior del contenedor
az webapp config container set -g recway-rg -n recway-backend-central \
  --docker-custom-image-name recwayacr2.azurecr.io/recway-backend:prod-<commit_anterior>

# O usar slot swap si desplegaste en staging
az webapp deployment slot swap -g recway-rg -n recway-backend-central --slot staging
```

### Debugging común:

1. **Error de conexión a DB**: Verifica que los App Settings apunten correctamente al Key Vault
2. **CORS errors**: Confirma que `CORS_ORIGINS` incluya la URL correcta del SWA
3. **Container no inicia**: Revisa logs con `az webapp log tail`
4. **ACR pull errors**: Verifica que Managed Identity tenga rol `AcrPull`

## 📊 Monitoreo

- **Application Insights**: https://portal.azure.com → recway-ai
- **Métricas de App Service**: CPU, memoria, requests
- **Logs estructurados**: Application Insights → Logs
- **Alertas**: Configura en Azure Monitor para CPU >80%, errores HTTP 5xx

## 🎛️ Escalabilidad

**Autoscale ya configurado:**
- Min: 1 instancia
- Max: 3 instancias  
- Scale out: CPU >70% por 10 min
- Scale in: CPU <30% por 10 min

**Para mayor escala:**
```bash
# Aumentar máximo de instancias
az monitor autoscale update -g recway-rg -n autoscale-recway-backend-central --max-count 10

# Cambiar a plan Premium (más CPU/RAM)
az appservice plan update -g recway-rg -n recway-plan-prod --sku P1V3
```

## ✅ Checklist de Deployment

- [ ] Script bootstrap ejecutado exitosamente
- [ ] Secretos cargados en Key Vault
- [ ] App Settings configurados con Key Vault references
- [ ] Static Web App creado y token configurado
- [ ] GitHub secrets configurados (OIDC + SWA)
- [ ] Health check endpoint implementado
- [ ] Workflows ejecutándose sin errores
- [ ] URLs funcionando correctamente
- [ ] CORS configurado para SWA
- [ ] Application Insights recibiendo telemetría

---

**🎉 ¡Con esto tienes un deployment production-ready con "git push y listo"!**

Para cualquier duda o mejora, revisa la documentación en:
- [Azure App Service](https://docs.microsoft.com/azure/app-service/)
- [Azure Static Web Apps](https://docs.microsoft.com/azure/static-web-apps/)
- [GitHub Actions con Azure](https://docs.microsoft.com/azure/developer/github/)