#!/usr/bin/env bash
set -euo pipefail

# Configuración para recursos ACTIVOS únicamente
RG="recway-rg"
LOC="eastus"
KV="recway-keyvault-02"
SAPLAN="recway-plan-prod"
WEB="recway-backend-central"
SWA="recway-frontend"
PG="recway-db-new"

echo "==> Creando Resource Group"
az group create -n "$RG" -l "$LOC"

echo "==> Key Vault (para secretos de producción)"
az keyvault create -g "$RG" -n "$KV"

echo "==> PostgreSQL Flexible Server"
az postgres flexible-server create -g "$RG" -n "$PG" -l "$LOC" \
  --tier Burstable --sku-name Standard_B1ms --storage-size 32 --version 13 \
  --public-access 0.0.0.0-0.0.0.0

echo "==> App Service Plan (Basic B1 - suficiente para producción simple)"
az appservice plan create -g "$RG" -n "$SAPLAN" --is-linux --sku B1

echo "==> Web App (App Service Central)"
az webapp create -g "$RG" -p "$SAPLAN" -n "$WEB" --runtime "PYTHON|3.11"

echo "==> Managed Identity para Web App"
az webapp identity assign -g "$RG" -n "$WEB"

echo "==> Permisos: App Service → Key Vault (para secretos)"
PRINCIPAL_ID=$(az webapp identity show -g "$RG" -n "$WEB" --query principalId -o tsv)
KV_ID=$(az keyvault show -g "$RG" -n "$KV" --query id -o tsv)
az role assignment create --assignee-object-id "$PRINCIPAL_ID" --role "Key Vault Secrets User" --scope "$KV_ID"

echo "==> Health Check configurado"
az webapp config set -g "$RG" -n "$WEB" --generic-configurations '{"healthCheckPath":"/health"}'

echo "==> Configuración básica completada"

echo ""
echo "======================================"
echo "RECURSOS CREADOS (SOLO LOS NECESARIOS):"
echo "======================================"
echo ""
echo "✅ Resource Group: $RG"
echo "✅ Key Vault: $KV"
echo "✅ PostgreSQL: $PG"
echo "✅ App Service Plan: $SAPLAN (B1)"
echo "✅ App Service: $WEB"
echo ""
echo "======================================"
echo "CONFIGURACIÓN MANUAL REQUERIDA:"
echo "======================================"
echo ""
echo "1. Crear Azure Static Web App desde el portal:"
echo "   - Nombre: $SWA"
echo "   - Conectar con GitHub: edward30n/deplyApp"
echo "   - Build preset: React"
echo "   - App location: frontend"
echo "   - Output location: dist"
echo ""
echo "2. Configurar secretos en Key Vault:"
echo "   az keyvault secret set -n recway-secret-key --vault-name $KV --value \"<jwt_secret_fuerte>\""
echo "   az keyvault secret set -n recway-db-uri --vault-name $KV \\"
echo "     --value \"postgresql://<user>:<pass>@$PG.postgres.database.azure.com:5432/recway_db?sslmode=require\""
echo ""
echo "3. Configurar App Settings en App Service:"
echo "   az webapp config appsettings set -g $RG -n $WEB --settings \\"
echo "     WEBSITES_PORT=8000 \\"
echo "     ENV=production \\"
echo "     API_V1_STR=/api/v1 \\"
echo "     FRONTEND_URL=https://$SWA.azurestaticapps.net \\"
echo "     CORS_ORIGINS='[\"https://$SWA.azurestaticapps.net\"]' \\"
echo "     SECRET_KEY=@Microsoft.KeyVault\\(SecretUri=https://$KV.vault.azure.net/secrets/recway-secret-key/\\) \\"
echo "     DATABASE_URI=@Microsoft.KeyVault\\(SecretUri=https://$KV.vault.azure.net/secrets/recway-db-uri/\\)"
echo ""
echo "4. URLs de verificación:"
echo "   - Backend: https://$WEB.azurewebsites.net/health"
echo "   - Frontend: https://$SWA.azurestaticapps.net"
echo ""
echo "💡 NOTA: Este script crea SOLO los recursos que está usando el código actual"
echo ""