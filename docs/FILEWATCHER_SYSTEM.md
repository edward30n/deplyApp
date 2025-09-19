# FileWatcher System - Documentación Técnica

## 📋 Descripción General

El FileWatcher es un sistema de monitoreo automático que detecta archivos CSV cargados en la carpeta `uploads/csv/raw` y los procesa automáticamente utilizando algoritmos de machine learning para generar archivos JSON optimizados.

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    FILEWATCHER ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📁 uploads/csv/raw/         🔍 FileWatcher Monitor             │
│  ├─ archivo1.csv           ├─ Polling cada 2s                  │
│  ├─ archivo2.csv           ├─ Detecta nuevos CSV               │
│  └─ archivo3.csv           └─ Trigger procesamiento             │
│                                                                 │
│  🤖 CSV Processor           📊 ML Algorithms                    │
│  ├─ Validar CSV            ├─ pandas + numpy                   │
│  ├─ Procesar datos         ├─ scipy + scikit-learn             │
│  └─ Generar JSON           └─ Algoritmos de rutas              │
│                                                                 │
│  📤 Output Generation       🗂️ File Organization               │
│  ├─ uploads/json/output/    ├─ CSV → processed/                │
│  ├─ uploads/json/storage/   ├─ JSON rápido → output/           │
│  └─ Archivos históricos    └─ JSON histórico → storage/        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Configuración

### Variables de Entorno
```env
ENABLE_FILE_WATCHER=true     # Habilita el FileWatcher
CSV_RAW_DIR=uploads/csv/raw  # Carpeta monitoreada
JSON_OUTPUT_DIR=uploads/json/output
JSON_STORAGE_DIR=uploads/json/storage
CSV_PROCESSED_DIR=uploads/csv/processed
```

### Configuración de Azure
En el workflow de deployment (`azure-backend-deploy.yml`):
```yaml
echo "ENABLE_FILE_WATCHER=true" >> .env
```

## 📁 Estructura de Directorios

```
backend/uploads/
├── csv/
│   ├── raw/                 # 📥 CSV cargados (monitoreados)
│   └── processed/           # ✅ CSV procesados (archivo)
├── json/
│   ├── output/              # 🚀 JSON rápido (sobrescrito)
│   └── storage/             # 📚 JSON histórico (permanente)
└── logs/                    # 📝 Logs de procesamiento
```

## 🔍 Funcionamiento del FileWatcher

### 1. Inicialización
```python
# app/main.py
if start_file_watcher():
    logger.info("✅ File Watcher iniciado correctamente")
else:
    logger.warning("⚠️ No se pudo iniciar el File Watcher")
```

### 2. Monitoreo Continuo
- **Frecuencia**: Polling cada 2 segundos
- **Archivos**: Detecta archivos `.csv` en `uploads/csv/raw/`
- **Filtros**: Solo procesa archivos nuevos (no procesados)

### 3. Procesamiento Automático
```python
def run_process(nombre):
    try:
        print("[PROCESS] Iniciando procesamiento de:", nombre)
        from app.services.processing.csv_processor import csv_processor
        resultado = csv_processor.procesar_archivo_especifico(Path(nombre).name)
        print("[PROCESS] Resultado segmentos:", len(resultado))
    except Exception as e:
        print("[PROCESS][ERROR]", e)
```

### 4. Generación de Archivos
- **JSON Output**: `datosRecWay_output.json` (sobrescrito)
- **JSON Storage**: `datosRecWay_{archivo}_{timestamp}.json` (histórico)
- **CSV Procesado**: Movido a `uploads/csv/processed/`

## 📊 Flujo de Procesamiento

### Paso 1: Detección
```
[FILEWATCHER] Nuevo archivo detectado: ejemplo.csv
[FILEWATCHER] Tamaño: 1.2 MB
[FILEWATCHER] Iniciando procesamiento...
```

### Paso 2: Validación
- Verificar extensión `.csv`
- Validar estructura de datos
- Comprobar formato de coordenadas

### Paso 3: Procesamiento ML
- Carga de datos con pandas
- Aplicación de algoritmos de rutas
- Segmentación geográfica
- Optimización de trayectorias

### Paso 4: Generación de Output
- JSON optimizado para frontend
- Archivo histórico para auditoría
- Movimiento de CSV a carpeta procesados

### Paso 5: Notificación
```
[PROCESS] Resultado segmentos: 1247
[FILEWATCHER] Procesamiento completado exitosamente
[FILEWATCHER] Archivo movido a processed/
```

## 🔧 Configuración de Producción

### Gunicorn Settings
```bash
# Configurado para manejar FileWatcher
gunicorn -k uvicorn.workers.UvicornWorker -w 1 -t 120 -b 0.0.0.0:8000 app.main:app
```

### Memory Management
- **Plan**: P1v2 (3.5 GB RAM)
- **Workers**: 1 worker (evita competencia por memoria)
- **Timeout**: 120s para procesamiento completo

### Monitoreo
```python
def get_file_watcher_status():
    """Estado del file watcher con estadísticas"""
    return {
        "active": _file_watcher.is_active,
        "files_processed": _file_watcher.processed_count,
        "last_activity": _file_watcher.last_activity,
        "watch_folder": str(_file_watcher.watch_folder)
    }
```

## 🚨 Troubleshooting

### Problema: FileWatcher no inicia
**Síntomas**: Log muestra "⚠️ No se pudo iniciar el File Watcher"
**Solución**: 
1. Verificar `ENABLE_FILE_WATCHER=true`
2. Comprobar permisos de directorio
3. Revisar logs de Azure

### Problema: Archivos no se procesan
**Síntomas**: CSV en raw/ pero no hay JSON generado
**Solución**:
1. Verificar formato CSV válido
2. Comprobar memoria disponible
3. Revisar logs de procesamiento

### Problema: Memory errors
**Síntomas**: SIGKILL o Worker timeout
**Solución**:
1. Ya resuelto con plan P1v2
2. Reducir workers a 1
3. Aumentar timeout si necesario

## 📝 Logs y Monitoreo

### Logs de FileWatcher
```bash
# Ver logs en tiempo real
az webapp log tail --name recway-backend-central --resource-group recway-central-rg

# Buscar logs específicos
grep "FILEWATCHER" /home/LogFiles/application.log
grep "PROCESS" /home/LogFiles/application.log
```

### Endpoints de Monitoreo
- **Status**: `GET /api/v1/filewatcher/status`
- **Stats**: `GET /api/v1/filewatcher/stats`
- **Health**: `GET /api/v1/test`

## 🔄 API Integration

### Upload + FileWatcher Flow
1. **Upload**: `POST /api/v1/files/upload-csv`
2. **Background**: FileWatcher detecta automáticamente
3. **Process**: Procesamiento ML automático
4. **Output**: JSON disponible para frontend

### Sync vs Async
- **Async** (default): Upload + background processing
- **Sync**: Upload + procesamiento inmediato (parámetro `sync=true`)

## 📈 Performance Metrics

### Tiempos Típicos
- **Detección**: < 2 segundos
- **Validación**: < 1 segundo
- **Procesamiento**: 30-120 segundos (según tamaño)
- **Generación JSON**: < 5 segundos

### Capacidad
- **Archivos simultáneos**: 1 (procesamiento secuencial)
- **Tamaño máximo**: Limitado por memoria (P1v2)
- **Throughput**: ~1 archivo por minuto (archivos grandes)

## 🔮 Mejoras Futuras

1. **Procesamiento paralelo**: Múltiples workers para archivos grandes
2. **Cola de procesamiento**: Redis/Azure Service Bus
3. **Notificaciones**: WebSockets para updates en tiempo real
4. **Métricas avanzadas**: Application Insights integration
5. **Escalado automático**: Auto-scaling basado en carga

---
**Última Actualización**: 19 de Septiembre, 2025  
**Estado**: ✅ FUNCIONAL EN PRODUCCIÓN  
**Plan**: P1v2 con FileWatcher habilitado