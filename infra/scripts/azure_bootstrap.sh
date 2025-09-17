#!/usr/bin/env bash
set -euo pipefail

RG="recway-rg"
LOC="eastus"
ACR="recwayacr2"
KV="recway-keyvault-02"
SAPLAN="recway-plan-prod"          # S1 en prod
WEB="recway-backend-central"
SWA="recway-frontend"              # ya existente o créalo en portal
PG="recway-db-new"
STG="recwaystorage02"

echo "==> Creando Resource Group"
az group create -n "$RG" -l "$LOC"

echo "==> ACR"
az acr create -g "$RG" -n "$ACR" --sku Standard --admin-enabled false

echo "==> Key Vault"
az keyvault create -g "$RG" -n "$KV"

echo "==> PostgreSQL Flexible"
az postgres flexible-server create -g "$RG" -n "$PG" -l "$LOC" \
  --tier Burstable --sku-name Standard_B1ms --storage-size 64 --version 16 \
  --public-access 0.0.0.0-0.0.0.0

echo "==> Storage Account"
az storage account create -g "$RG" -n "$STG" -l "$LOC" --sku Standard_LRS

echo "==> App Service Plan (S1 para autoscale/slots) y Web App"
az appservice plan create -g "$RG" -n "$SAPLAN" --is-linux --sku S1
az webapp create -g "$RG" -p "$SAPLAN" -n "$WEB" --runtime "PYTHON|3.11"

echo "==> Identity del Web App"
az webapp identity assign -g "$RG" -n "$WEB"

echo "==> Permisos: App → ACR (AcrPull)"
PRINCIPAL_ID=$(az webapp identity show -g "$RG" -n "$WEB" --query principalId -o tsv)
ACR_ID=$(az acr show -g "$RG" -n "$ACR" --query id -o tsv)
az role assignment create --assignee-object-id "$PRINCIPAL_ID" --role "AcrPull" --scope "$ACR_ID"

echo "==> Permisos: App → Key Vault (Key Vault Secrets User)"
KV_ID=$(az keyvault show -g "$RG" -n "$KV" --query id -o tsv)
az role assignment create --assignee-object-id "$PRINCIPAL_ID" --role "Key Vault Secrets User" --scope "$KV_ID"

echo "==> Health Check"
az webapp config set -g "$RG" -n "$WEB" --generic-configurations '{"healthCheckPath":"/health"}'

echo "==> Slot 'staging' (blue-green)"
az webapp deployment slot create -g "$RG" -n "$WEB" --slot staging

echo "==> Autoscale básico (1→3 instancias según CPU)"
WEB_ID=$(az webapp show -g "$RG" -n "$WEB" --query id -o tsv)
az monitor autoscale create \
  --name "autoscale-$WEB" --resource "$WEB_ID" --resource-group "$RG" \
  --min-count 1 --max-count 3 --count 1
az monitor autoscale rule create --resource-group "$RG" --autoscale-name "autoscale-$WEB" \
  --condition "Percentage CPU > 70 avg 10m" --scale out 1
az monitor autoscale rule create --resource-group "$RG" --autoscale-name "autoscale-$WEB" \
  --condition "Percentage CPU < 30 avg 10m" --scale in 1

echo "==> Application Insights"
AI="recway-ai"
az monitor app-insights component create -g "$RG" -l "$LOC" -a "$AI"
CONN=$(az monitor app-insights component show -g "$RG" -a "$AI" --query connectionString -o tsv)
az webapp config appsettings set -g "$RG" -n "$WEB" --settings APPLICATIONINSIGHTS_CONNECTION_STRING="$CONN"

echo "==> Listo."

echo ""
echo "======================================"
echo "PRÓXIMOS PASOS MANUALES:"
echo "======================================"
echo ""
echo "1. Cargar secretos al Key Vault:"
echo "   az keyvault secret set -n recway-secret-key --vault-name $KV --value \"<jwt_secret_fuerte>\""
echo "   az keyvault secret set -n recway-db-uri --vault-name $KV \\"
echo "     --value \"postgresql://<user>:<pass>@$PG.postgres.database.azure.com:5432/recWay_db?sslmode=require\""
echo "   az keyvault secret set -n recway-storage-conn --vault-name $KV --value \"<connection_string_storage>\""
echo ""
echo "2. Configurar App Settings con Key Vault references:"
echo "   az webapp config appsettings set -g $RG -n $WEB --settings \\"
echo "     WEBSITES_PORT=8000 ENV=azure API_V1_STR=/api/v1 ENABLE_FILE_WATCHER=false \\"
echo "     FRONTEND_URL=https://$SWA.azurestaticapps.net \\"
echo "     CORS_ORIGINS='[\"https://$SWA.azurestaticapps.net\"]' \\"
echo "     SECRET_KEY=@Microsoft.KeyVault\\(SecretUri=https://$KV.vault.azure.net/secrets/recway-secret-key/\\) \\"
echo "     DATABASE_URI=@Microsoft.KeyVault\\(SecretUri=https://$KV.vault.azure.net/secrets/recway-db-uri/\\) \\"
echo "     AZURE_STORAGE_CONNECTION_STRING=@Microsoft.KeyVault\\(SecretUri=https://$KV.vault.azure.net/secrets/recway-storage-conn/\\)"
echo ""
echo "3. Configurar GitHub Secrets:"
echo "   - AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID (para OIDC)"
echo "   - AZURE_STATIC_WEB_APPS_API_TOKEN (del portal de Azure SWA)"
echo ""
echo "4. Crear Azure Static Web App (si no existe):"
echo "   - Ve al portal de Azure y crea el SWA con nombre: $SWA"
echo ""
echo "5. URLs para verificar:"
echo "   - Backend: https://$WEB.azurewebsites.net/health"
echo "   - Frontend: https://$SWA.azurestaticapps.net"
echo ""