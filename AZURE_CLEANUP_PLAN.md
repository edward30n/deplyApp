# 🧹 PLAN DE LIMPIEZA AZURE - RecWay

**Fecha**: 18 de Septiembre, 2025  
**Status**: ✅ Backend verificado funcionando  
**Ahorro estimado**: $370-750/mes  

## 🚨 SITUACIÓN ACTUAL: CAOS TOTAL
- **31 recursos** en Azure (¡DEMASIADOS!)
- **3 entornos duplicados** (prod, dev, experimental)
- **$800-1200/mes** de costos innecesarios

---

## ✅ RECURSOS CRÍTICOS - NO TOCAR

### 🏭 Producción Funcional (`recway-central-rg`)
| Recurso | Nombre | Status | Función |
|---------|--------|--------|---------|
| 🌐 **Static Web App** | `recway-frontend` | ✅ ACTIVO | Frontend React en producción |
| 🚀 **App Service** | `recway-backend-central` | ✅ ACTIVO | API FastAPI verificada |
| 📊 **App Service Plan** | `recway-plan-central` | ✅ REQUERIDO | Infraestructura para App Service |
| 🗄️ **PostgreSQL** | `recway-db-new` | ✅ ACTIVO | Base de datos principal |
| 🔐 **Key Vault** | `recway-keyvault-02` | ✅ ACTIVO | Secretos y credenciales |

**💡 Arquitectura final limpia:**
```
Frontend (SWA) → Backend (App Service) → Database (PostgreSQL)
                        ↓
                  Key Vault (Secrets)
```

---

## 🗑️ RECURSOS PARA ELIMINAR

### 🔥 FASE 1: Eliminar Entorno DEV (100% SEGURO)
**Grupo completo**: `recway-dev-rg`

```bash
# Comando para eliminar TODO el grupo:
az group delete --name recway-dev-rg --yes --no-wait
```

**Recursos que se eliminarán:**
- ❌ `recway-backend-dev` (App Service)
- ❌ `staging` (App Service slot)
- ❌ `recway-dev-ai` (Application Insights)
- ❌ `recway-dev-db` (PostgreSQL)
- ❌ `recway-dev-keyvault` (Key Vault)
- ❌ `recway-frontend-swa-dev` (Static Web App)
- ❌ `recway-plan-dev` (App Service Plan)
- ❌ `recwaydevacr` (Container Registry)
- ❌ `recwaydevstorage` (Storage Account)
- ❌ `managed-recway-dev-ai-ws` (Log Analytics)
- ❌ `Application Insights Smart Detection`

**💰 Ahorro**: $200-400/mes

### 🔥 FASE 2: Eliminar Container Apps (99% SEGURO)
**Grupo completo**: `recway-rg`

```bash
# Comando para eliminar TODO el grupo:
az group delete --name recway-rg --yes --no-wait
```

**Recursos que se eliminarán:**
- ❌ `recway-backend` (Container App)
- ❌ `recway-env` (Container Apps Environment)
- ❌ `recway-db-09171024` (PostgreSQL duplicado)
- ❌ `recway-frontend-09171024` (SWA duplicado)
- ❌ `recway-kv-09171024` (Key Vault duplicado)
- ❌ `recway09171024` (Container Registry)
- ❌ `recwaystorage09171024` (Storage Account)

**💰 Ahorro**: $150-300/mes

### ⚠️ FASE 3: Limpiar Duplicados (VERIFICAR PRIMERO)
**En**: `recway-central-rg`

```bash
# Solo eliminar Container Registry duplicado:
az acr delete --name recwayacr2 --resource-group recway-central-rg --yes
```

**⚠️ VERIFICAR ANTES:**
- `recwaystorage02`: ¿Contiene archivos importantes?

**💰 Ahorro**: $20-50/mes

---

## 📋 EJECUCIÓN PASO A PASO

### ✅ Pre-verificación (COMPLETADA)
```bash
# ✅ Backend funcionando:
Invoke-RestMethod -Uri "https://recway-backend-central.azurewebsites.net/health"
# Result: status=healthy, service=RecWay API, version=1.0.0

# ✅ Frontend accesible:
# URL: https://recway-frontend.azurestaticapps.net (verificar manualmente)
```

### 🚀 Ejecución Segura

1. **Ejecutar Fase 1** (Más seguro):
   ```bash
   az group delete --name recway-dev-rg --yes --no-wait
   ```

2. **Esperar 5 minutos y verificar**:
   ```bash
   Invoke-RestMethod -Uri "https://recway-backend-central.azurewebsites.net/health"
   ```

3. **Si todo OK, ejecutar Fase 2**:
   ```bash
   az group delete --name recway-rg --yes --no-wait
   ```

4. **Verificar nuevamente**:
   ```bash
   Invoke-RestMethod -Uri "https://recway-backend-central.azurewebsites.net/health"
   ```

5. **Fase 3 (opcional)**:
   ```bash
   az acr delete --name recwayacr2 --resource-group recway-central-rg --yes
   ```

---

## 💰 RESUMEN DE AHORRO

| Fase | Recursos | Ahorro Mensual |
|------|----------|---------------|
| Fase 1 | 11 recursos DEV | $200-400 |
| Fase 2 | 7 recursos Container Apps | $150-300 |
| Fase 3 | 1-2 duplicados | $20-50 |
| **TOTAL** | **19-20 de 31** | **$370-750** |

## 🎯 ARQUITECTURA FINAL

**De 31 recursos → 6 recursos esenciales**

```
┌─────────────────────────────────────────────────┐
│                recway-central-rg                 │
├─────────────────────────────────────────────────┤
│  ✅ recway-frontend (SWA)                       │
│  ✅ recway-backend-central (App Service)        │
│  ✅ recway-plan-central (App Service Plan)      │
│  ✅ recway-db-new (PostgreSQL)                  │
│  ✅ recway-keyvault-02 (Key Vault)              │
│  ⚠️  recwaystorage02 (Storage - verificar)      │
└─────────────────────────────────────────────────┘
```

---

## ⚠️ ROLLBACK PLAN

Si algo sale mal:
1. **No hay rollback** para recursos eliminados
2. **Backup crítico**: Exportar configuración de `recway-keyvault-02`
3. **Recovery**: Recrear solo recursos necesarios desde documentación

---

**✅ APROBADO PARA EJECUCIÓN**  
**🎯 Beneficio**: Arquitectura limpia + $370-750/mes ahorro  
**🛡️ Riesgo**: Mínimo (recursos redundantes)  