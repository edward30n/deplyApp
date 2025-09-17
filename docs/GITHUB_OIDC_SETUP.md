# 🔐 Configuración GitHub OIDC para Azure

## Comandos para crear App Registration

### 1. Crear App Registration
```bash
az ad app create --display-name "RecWay GitHub Actions"
```

### 2. Obtener App ID
```bash
APP_ID=$(az ad app list --display-name "RecWay GitHub Actions" --query "[0].appId" -o tsv)
echo "App ID: $APP_ID"
```

### 3. Crear Service Principal
```bash
az ad sp create --id $APP_ID
```

### 4. Asignar permisos
```bash
az role assignment create \
  --role "Contributor" \
  --assignee $APP_ID \
  --scope /subscriptions/b63bb596-8e31-4ce3-83c3-fd6fa633e446/resourceGroups/recway-rg
```

### 5. Crear credencial federada para GitHub
```bash
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "RecWay-GitHub-Main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:edward30n/deplyApp:ref:refs/heads/main",
    "description": "GitHub Actions deployment from main branch",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

### 6. Obtener información para GitHub Secrets
```bash
echo "AZURE_CLIENT_ID: $APP_ID"
echo "AZURE_TENANT_ID: e15fe7da-d2f7-4de4-b9fd-8b64a93c60be"
echo "AZURE_SUBSCRIPTION_ID: b63bb596-8e31-4ce3-83c3-fd6fa633e446"
echo "AZURE_STATIC_WEB_APPS_API_TOKEN: 1fbca8fbd0c9492944b15518f4ff31c2d989d9176b36ff9128690816c5b20e3401-891963c1-043b-4d09-9083-749b1ad58b8a00f000606348160f"
```

## GitHub Secrets a configurar

1. Ve a https://github.com/edward30n/deplyApp/settings/secrets/actions
2. Agrega estos 4 secretos:
   - `AZURE_CLIENT_ID`: (valor del App ID obtenido arriba)
   - `AZURE_TENANT_ID`: `e15fe7da-d2f7-4de4-b9fd-8b64a93c60be`
   - `AZURE_SUBSCRIPTION_ID`: `b63bb596-8e31-4ce3-83c3-fd6fa633e446`
   - `AZURE_STATIC_WEB_APPS_API_TOKEN`: `1fbca8fbd0c9492944b15518f4ff31c2d989d9176b36ff9128690816c5b20e3401-891963c1-043b-4d09-9083-749b1ad58b8a00f000606348160f`