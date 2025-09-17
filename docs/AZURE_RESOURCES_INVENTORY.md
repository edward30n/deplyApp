# 📊 Inventario de Recursos Azure - RecWay

**Fecha**: 2025-09-17  
**Analista**: Sistema de Documentación Automática

## 🎯 Objetivo
Documentar el estado actual de recursos Azure para planificar limpieza controlada y deployment de SWA.

---

## 🟢 **recway-central-rg** (PRESERVAR - NO TOCAR)
> Grupo funcional que debe mantenerse como respaldo

| Recurso | Tipo | Ubicación | Estado |
|---------|------|-----------|--------|
| `recway-backend-central` | App Service | Central US | 🟢 Funcional |
| `recway-db-new` | PostgreSQL Flexible | Central US | 🟢 Funcional |
| `recway-frontend` | Static Web App | Central US | 🟢 Funcional |
| `recway-keyvault-02` | Key Vault | Central US | 🟢 Funcional |
| `recway-plan-central` | App Service Plan | Central US | 🟢 Funcional |
| `recwayacr2` | Container Registry | Central US | 🟢 Funcional |
| `recwaystorage02` | Storage Account | Central US | 🟢 Funcional |

---

## 🟡 **recway-dev-rg** (LIMPIEZA CONTROLADA)
> Grupo de desarrollo - Candidatos para limpieza y reorganización

### 🔴 Recursos Duplicados/Obsoletos (CANDIDATOS A ELIMINAR)
| Recurso | Tipo | Problema | Acción Sugerida |
|---------|------|-----------|----------------|
| `recway-frontend-dev` | App Service | Duplicado - Reemplazar por SWA | ❌ Eliminar |
| `recway-frontend-swa-dev` | Static Web App | Ya existe - Verificar estado | ⚠️ Evaluar |
| `recway-dev-kv-3634` | Key Vault | Duplicado - Solo uno necesario | ❌ Eliminar |
| `recway-dev-kv-7619` | Key Vault | Duplicado - Solo uno necesario | ❌ Eliminar |
| `recway-dev-keyvault` | Key Vault | Duplicado - Solo uno necesario | ⚠️ Evaluar |

### 🟢 Recursos Útiles (MANTENER)
| Recurso | Tipo | Ubicación | Propósito |
|---------|------|-----------|-----------|
| `recway-backend-dev` | App Service | Central US | Backend desarrollo |
| `staging (recway-backend-dev/staging)` | App Service Slot | Central US | Staging slot |
| `recway-dev-db` | PostgreSQL Flexible | East US | DB desarrollo |
| `recway-dev-plan` | App Service Plan | Central US | Plan para backend |
| `recwaydevacr` | Container Registry | Central US | Registry desarrollo |
| `recwaydevstorage` | Storage Account | East US | Storage desarrollo |

### 🔧 Recursos de Monitoreo (EVALUAR)
| Recurso | Tipo | Necesario |
|---------|------|-----------|
| `recway-dev-ai` | Application Insights | ✅ Útil para monitoreo |
| `managed-recway-dev-ai-ws` | Log Analytics | ✅ Útil para monitoreo |

---

## 🎯 **Plan de Limpieza Sugerido**

### Fase 1: Eliminar Duplicados Obvios
```bash
# Key Vaults duplicados (mantener recway-dev-keyvault)
az keyvault delete -n recway-dev-kv-3634 -g recway-dev-rg
az keyvault delete -n recway-dev-kv-7619 -g recway-dev-rg

# Frontend App Service (reemplazar por SWA)
az webapp delete -n recway-frontend-dev -g recway-dev-rg
```

### Fase 2: Evaluar SWA Existente
```bash
# Verificar estado de SWA existente
az staticwebapp show -n recway-frontend-swa-dev -g recway-dev-rg
```

### Fase 3: Crear Nueva Arquitectura Limpia
- Usar SWA existente o crear nuevo
- Configurar CORS en backend existente
- Documentar conexiones

---

## 📋 Próximos Pasos
1. ✅ Crear documentación
2. 🔄 Verificar estado actual de recursos
3. ⏳ Ejecutar limpieza controlada
4. ⏳ Implementar SWA deployment

---

**Última actualización**: 2025-09-17  
**Estado**: Documentación inicial completada