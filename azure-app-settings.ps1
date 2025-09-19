# Script para configurar Azure App Service Settings para CORS y Base de Datos
# Ejecutar este script manualmente si el CLI de Azure falla

$resourceGroup = "recway-central-rg"
$appName = "recway-backend-central"

Write-Host "=== Configurando Azure App Service Settings ===" -ForegroundColor Green

# Configuración CORS - URL del Azure Static Web Apps
$corsOrigins = '["https://green-rock-0e0abfc10.1.azurestaticapps.net", "http://localhost:5173", "http://localhost:3000"]'
$frontendUrl = "https://green-rock-0e0abfc10.1.azurestaticapps.net"

# Database URI para Azure PostgreSQL
$databaseUri = "postgresql://recway_user:Edward123!@recway-db-new.postgres.database.azure.com:5432/recway_db?sslmode=require"

Write-Host "Configurando variables de entorno..." -ForegroundColor Yellow

try {
    # CORS Configuration
    az webapp config appsettings set --name $appName --resource-group $resourceGroup --settings CORS_ORIGINS="$corsOrigins"
    az webapp config appsettings set --name $appName --resource-group $resourceGroup --settings FRONTEND_URL="$frontendUrl"
    az webapp config appsettings set --name $appName --resource-group $resourceGroup --settings ENV="azure"
    
    # Database Configuration
    az webapp config appsettings set --name $appName --resource-group $resourceGroup --settings DATABASE_URI="$databaseUri"
    
    # Other production settings
    az webapp config appsettings set --name $appName --resource-group $resourceGroup --settings USE_AZURE_STORAGE="false"
    
    Write-Host "✅ Configuración completada exitosamente!" -ForegroundColor Green
    
    # Verificar configuración
    Write-Host "`nVerificando configuración..." -ForegroundColor Yellow
    az webapp config appsettings list --name $appName --resource-group $resourceGroup --query "[?name=='CORS_ORIGINS' || name=='FRONTEND_URL' || name=='DATABASE_URI' || name=='ENV']" --output table
    
} catch {
    Write-Host "❌ Error configurando variables: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n📌 CONFIGURACIÓN MANUAL REQUERIDA:" -ForegroundColor Yellow
    Write-Host "Ve a Azure Portal > App Services > recway-backend-central > Configuration > Application settings" -ForegroundColor Cyan
    Write-Host "`nAgregar estas variables:" -ForegroundColor White
    Write-Host "CORS_ORIGINS = $corsOrigins" -ForegroundColor Gray
    Write-Host "FRONTEND_URL = $frontendUrl" -ForegroundColor Gray
    Write-Host "DATABASE_URI = $databaseUri" -ForegroundColor Gray
    Write-Host "ENV = azure" -ForegroundColor Gray
    Write-Host "USE_AZURE_STORAGE = false" -ForegroundColor Gray
}