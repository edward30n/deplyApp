"""
Endpoints para el procesamiento automático de archivos CSV
"""
from typing import List, Dict
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from app.services.processing.csv_processor import csv_processor
from app.services.monitoring.file_watcher import start_file_watcher, stop_file_watcher, get_file_watcher_status
from app.database.session import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/process-and-store/{filename}")
async def process_and_store_file(filename: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Procesar un archivo CSV específico Y almacenar los resultados en la base de datos
    """
    try:
        import requests
        from app.core.config import settings
        from pathlib import Path
        
        logger.info(f"Iniciando procesamiento y almacenamiento de archivo: {filename}")
        
        # Verificar que el archivo existe
        archivo_path = Path(csv_processor.carpeta_csv) / filename
        if not archivo_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Archivo {filename} no encontrado en {csv_processor.carpeta_csv}"
            )
        
        # Función de procesamiento en background
        async def proceso_completo():
            try:
                # 1. Procesar archivo con algoritmos
                logger.info(f"Paso 1: Procesando {filename} con algoritmos...")
                resultado_procesamiento = csv_processor.procesar_archivo_especifico(filename)
                
                if not resultado_procesamiento:
                    logger.error(f"Error en procesamiento de algoritmos para {filename}")
                    return {"error": "Error en procesamiento de algoritmos"}
                
                # 2. Determinar rutas de archivos
                archivo_csv = Path(csv_processor.carpeta_almacenamiento_csv) / filename
                # Preferimos el JSON histórico único por archivo
                base = filename[:-4] if filename.lower().endswith('.csv') else filename
                archivo_json_hist = Path(csv_processor.carpeta_almacenamiento_json) / f"datos{base}save.json"
                if archivo_json_hist.exists():
                    archivo_json = archivo_json_hist
                else:
                    # Fallback al último JSON en salida rápida
                    output_dir = Path(csv_processor.carpeta_archivos_json)
                    candidates = sorted(output_dir.glob("datos*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
                    archivo_json = candidates[0] if candidates else output_dir / f"datos{base}.json"
                
                # Verificar que los archivos existen
                if not archivo_csv.exists():
                    logger.error(f"Archivo CSV procesado no encontrado: {archivo_csv}")
                    return {"error": "Archivo CSV procesado no encontrado"}
                
                if not archivo_json.exists():
                    logger.error(f"Archivo JSON no encontrado: {archivo_json}")
                    return {"error": "Archivo JSON no encontrado"}
                
                # 3. Llamar al endpoint de almacenamiento
                logger.info(f"Paso 2: Almacenando resultados en base de datos...")
                
                # Usar el endpoint de recway_processing
                url = f"{settings.BASE_URL}{settings.API_V1_STR}/recway/process-and-store"
                params = {
                    "csv_file_path": str(archivo_csv),
                    "json_file_path": str(archivo_json)
                }
                
                response = requests.post(url, params=params)
                
                if response.status_code == 200:
                    storage_result = response.json()
                    logger.info(f"Almacenamiento exitoso para {filename}: {storage_result}")
                    return {
                        "status": "success",
                        "filename": filename,
                        "processing_result": resultado_procesamiento,
                        "storage_result": storage_result
                    }
                else:
                    logger.error(f"Error en almacenamiento: {response.status_code} - {response.text}")
                    return {
                        "status": "partial_success",
                        "filename": filename,
                        "processing_result": resultado_procesamiento,
                        "storage_error": response.text
                    }
                    
            except Exception as e:
                logger.error(f"Error en proceso completo para {filename}: {e}")
                return {"error": str(e)}
        
        # Ejecutar en background
        background_tasks.add_task(proceso_completo)
        
        return {
            "status": "processing_started",
            "message": f"El procesamiento completo del archivo {filename} ha iniciado en segundo plano",
            "filename": filename,
            "steps": [
                "1. Procesamiento con algoritmos RecWay",
                "2. Almacenamiento en base de datos"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error iniciando procesamiento completo de {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error iniciando procesamiento completo: {str(e)}"
        )


@router.post("/process-pending-and-store")
async def process_pending_and_store_all(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Procesar TODOS los archivos CSV pendientes Y almacenar en base de datos
    """
    try:
        logger.info("Iniciando procesamiento completo de todos los archivos pendientes")
        
        # Buscar archivos pendientes
        archivos_pendientes = csv_processor.buscar_archivos_por_nombre(
            csv_processor.carpeta_csv, 
            csv_processor.prefijo_busqueda
        )
        
        if not archivos_pendientes:
            return {
                "status": "no_files",
                "message": "No hay archivos pendientes para procesar"
            }
        
        # Función de procesamiento masivo en background
        async def proceso_masivo():
            import requests
            from app.core.config import settings
            from pathlib import Path
            
            resultados = []
            
            for archivo in archivos_pendientes:
                try:
                    logger.info(f"Procesando archivo {archivo} en lote...")
                    
                    # 1. Procesar con algoritmos
                    resultado_procesamiento = csv_processor.procesar_archivo_especifico(archivo)
                    
                    if resultado_procesamiento:
                        # 2. Almacenar en BD
                        archivo_csv = Path(csv_processor.carpeta_almacenamiento_csv) / archivo
                        base = archivo[:-4] if archivo.lower().endswith('.csv') else archivo
                        archivo_json_hist = Path(csv_processor.carpeta_almacenamiento_json) / f"datos{base}save.json"
                        if archivo_json_hist.exists():
                            archivo_json = archivo_json_hist
                        else:
                            output_dir = Path(csv_processor.carpeta_archivos_json)
                            candidates = sorted(output_dir.glob("datos*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
                            archivo_json = candidates[0] if candidates else output_dir / f"datos{base}.json"
                        
                        if archivo_csv.exists() and archivo_json.exists():
                            url = f"{settings.BASE_URL}{settings.API_V1_STR}/recway/process-and-store"
                            params = {
                                "csv_file_path": str(archivo_csv),
                                "json_file_path": str(archivo_json)
                            }
                            
                            response = requests.post(url, params=params)
                            
                            resultados.append({
                                "archivo": archivo,
                                "procesamiento": "exitoso",
                                "almacenamiento": "exitoso" if response.status_code == 200 else "error",
                                "detalles": response.json() if response.status_code == 200 else response.text
                            })
                        else:
                            resultados.append({
                                "archivo": archivo,
                                "procesamiento": "exitoso",
                                "almacenamiento": "error",
                                "detalles": "Archivos de salida no encontrados"
                            })
                    else:
                        resultados.append({
                            "archivo": archivo,
                            "procesamiento": "error",
                            "almacenamiento": "no_ejecutado",
                            "detalles": "Error en algoritmos de procesamiento"
                        })
                        
                except Exception as e:
                    logger.error(f"Error procesando {archivo}: {e}")
                    resultados.append({
                        "archivo": archivo,
                        "procesamiento": "error",
                        "almacenamiento": "no_ejecutado",
                        "detalles": str(e)
                    })
            
            logger.info(f"Procesamiento masivo completado. {len(resultados)} archivos procesados")
            return resultados
        
        # Ejecutar en background
        background_tasks.add_task(proceso_masivo)
        
        return {
            "status": "mass_processing_started",
            "message": f"El procesamiento completo de {len(archivos_pendientes)} archivos ha iniciado en segundo plano",
            "archivos_pendientes": archivos_pendientes,
            "total_archivos": len(archivos_pendientes)
        }
        
    except Exception as e:
        logger.error(f"Error iniciando procesamiento masivo: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error iniciando procesamiento masivo: {str(e)}"
        )


@router.post("/process-pending")
async def process_pending_files(background_tasks: BackgroundTasks):
    """
    Procesar todos los archivos CSV pendientes en la carpeta raw
    """
    try:
        logger.info("Iniciando procesamiento de archivos pendientes")
        
        # Ejecutar procesamiento en background
        def proceso_background():
            return csv_processor.procesar_archivos_pendientes()
        
        background_tasks.add_task(proceso_background)
        
        return {
            "status": "processing_started",
            "message": "El procesamiento de archivos pendientes ha iniciado en segundo plano"
        }
        
    except Exception as e:
        logger.error(f"Error iniciando procesamiento: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error iniciando procesamiento: {str(e)}"
        )

@router.post("/process-file/{filename}")
async def process_specific_file(filename: str, background_tasks: BackgroundTasks):
    """
    Procesar un archivo CSV específico
    """
    try:
        logger.info(f"Iniciando procesamiento de archivo: {filename}")
        
        # Ejecutar procesamiento en background
        def proceso_background():
            return csv_processor.procesar_archivo_especifico(filename)
        
        background_tasks.add_task(proceso_background)
        
        return {
            "status": "processing_started",
            "message": f"El procesamiento del archivo {filename} ha iniciado en segundo plano",
            "filename": filename
        }
        
    except Exception as e:
        logger.error(f"Error iniciando procesamiento de {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error iniciando procesamiento: {str(e)}"
        )

@router.get("/process-status")
async def get_process_status():
    """
    Obtener estado del procesamiento (archivos pendientes)
    """
    try:
        # Buscar archivos pendientes
        archivos_pendientes = csv_processor.buscar_archivos_por_nombre(
            csv_processor.carpeta_csv, 
            csv_processor.prefijo_busqueda
        )
        
        return {
            "archivos_pendientes": len(archivos_pendientes),
            "archivos": archivos_pendientes,
            "carpeta_raw": csv_processor.carpeta_csv,
            "carpeta_procesados": csv_processor.carpeta_almacenamiento_csv
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estado: {str(e)}"
        )

@router.get("/processed-files")
async def get_processed_files():
    """
    Obtener lista de archivos ya procesados
    """
    try:
        from pathlib import Path
        
        carpeta_procesados = Path(csv_processor.carpeta_almacenamiento_csv)
        carpeta_json = Path(csv_processor.carpeta_archivos_json)
        
        # Listar archivos CSV procesados
        archivos_csv = []
        if carpeta_procesados.exists():
            archivos_csv = [f.name for f in carpeta_procesados.glob("*.csv")]
        
        # Listar archivos JSON generados
        archivos_json = []
        if carpeta_json.exists():
            archivos_json = [f.name for f in carpeta_json.glob("*.json")]
        
        return {
            "archivos_csv_procesados": archivos_csv,
            "archivos_json_generados": archivos_json,
            "total_procesados": len(archivos_csv),
            "total_json": len(archivos_json)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo archivos procesados: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo archivos procesados: {str(e)}"
        )

@router.delete("/clear-processed")
async def clear_processed_files():
    """
    Limpiar archivos procesados (solo para desarrollo/testing)
    """
    try:
        import shutil
        from pathlib import Path
        
        carpeta_procesados = Path(csv_processor.carpeta_almacenamiento_csv)
        carpeta_json_output = Path(csv_processor.carpeta_archivos_json)
        carpeta_json_storage = Path(csv_processor.carpeta_almacenamiento_json)
        
        archivos_eliminados = 0
        
        # Limpiar CSV procesados
        if carpeta_procesados.exists():
            for archivo in carpeta_procesados.glob("*.csv"):
                archivo.unlink()
                archivos_eliminados += 1
        
        # Limpiar JSON output
        if carpeta_json_output.exists():
            for archivo in carpeta_json_output.glob("*.json"):
                archivo.unlink()
                archivos_eliminados += 1
        
        # Limpiar JSON storage
        if carpeta_json_storage.exists():
            for archivo in carpeta_json_storage.glob("*.json"):
                archivo.unlink()
                archivos_eliminados += 1
        
        return {
            "status": "success",
            "message": f"Se eliminaron {archivos_eliminados} archivos procesados",
            "archivos_eliminados": archivos_eliminados
        }
        
    except Exception as e:
        logger.error(f"Error limpiando archivos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error limpiando archivos: {str(e)}"
        )

@router.delete("/clear-raw")
async def clear_raw_files():
    """
    Limpiar absolutamente todo el contenido de la carpeta uploads
    (mantiene las carpetas pero elimina todos los archivos)
    """
    try:
        from pathlib import Path
        
        # Obtener la carpeta base de uploads
        uploads_dir = Path(csv_processor.carpeta_csv).parent.parent  # uploads/csv/raw -> uploads
        archivos_eliminados = 0
        carpetas_limpiadas = []
        
        logger.info(f"Iniciando limpieza completa de uploads: {uploads_dir}")
        
        # Limpiar todas las subcarpetas de uploads recursivamente
        if uploads_dir.exists():
            for carpeta in uploads_dir.rglob('*'):
                if carpeta.is_file():
                    # Eliminar archivo (excepto .gitkeep)
                    if carpeta.name != '.gitkeep':
                        carpeta.unlink()
                        archivos_eliminados += 1
                        logger.info(f"Eliminado: {carpeta.relative_to(uploads_dir)}")
                elif carpeta.is_dir() and carpeta != uploads_dir:
                    # Añadir carpeta a la lista (para información)
                    carpeta_rel = str(carpeta.relative_to(uploads_dir))
                    if carpeta_rel not in carpetas_limpiadas:
                        carpetas_limpiadas.append(carpeta_rel)
        
        return {
            "status": "success",
            "message": f"Se eliminaron {archivos_eliminados} archivos de toda la carpeta uploads",
            "archivos_eliminados": archivos_eliminados,
            "carpetas_limpiadas": sorted(carpetas_limpiadas),
            "uploads_dir": str(uploads_dir),
            "nota": "Se mantuvieron todas las carpetas y archivos .gitkeep"
        }
        
    except Exception as e:
        logger.error(f"Error limpiando uploads completo: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error limpiando uploads: {str(e)}"
        )

@router.delete("/clear-csv-only")
async def clear_csv_files_only():
    """
    Limpiar solo archivos CSV de la carpeta raw (opción más conservadora)
    """
    try:
        from pathlib import Path
        
        carpeta_raw = Path(csv_processor.carpeta_csv)
        archivos_eliminados = 0
        
        # Limpiar solo CSV en raw
        if carpeta_raw.exists():
            for archivo in carpeta_raw.glob("*.csv"):
                archivo.unlink()
                archivos_eliminados += 1
                logger.info(f"Eliminado archivo CSV: {archivo.name}")
        
        return {
            "status": "success",
            "message": f"Se eliminaron {archivos_eliminados} archivos CSV de la carpeta raw",
            "archivos_eliminados": archivos_eliminados,
            "carpeta": str(carpeta_raw)
        }
        
    except Exception as e:
        logger.error(f"Error limpiando archivos CSV: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error limpiando archivos CSV: {str(e)}"
        )

@router.delete("/delete-raw-file/{filename}")
async def delete_specific_raw_file(filename: str):
    """
    Eliminar un archivo CSV específico de la carpeta raw
    """
    try:
        from pathlib import Path
        
        carpeta_raw = Path(csv_processor.carpeta_csv)
        archivo_path = carpeta_raw / filename
        
        if not archivo_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Archivo {filename} no encontrado en carpeta raw"
            )
        
        if not filename.lower().endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Solo se pueden eliminar archivos .csv"
            )
        
        archivo_path.unlink()
        logger.info(f"Eliminado archivo específico: {filename}")
        
        return {
            "status": "success",
            "message": f"Archivo {filename} eliminado exitosamente",
            "filename": filename,
            "carpeta": str(carpeta_raw)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando archivo {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando archivo: {str(e)}"
        )

@router.get("/list-raw-files")
async def list_raw_files():
    """
    Listar archivos CSV pendientes en la carpeta raw
    """
    try:
        from pathlib import Path
        
        carpeta_raw = Path(csv_processor.carpeta_csv)
        archivos_csv = []
        
        if carpeta_raw.exists():
            for archivo in sorted(carpeta_raw.glob("*.csv")):
                stat = archivo.stat()
                archivos_csv.append({
                    "filename": archivo.name,
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created_at": stat.st_ctime,
                    "modified_at": stat.st_mtime
                })
        
        return {
            "status": "success",
            "carpeta": str(carpeta_raw),
            "total_archivos": len(archivos_csv),
            "archivos": archivos_csv
        }
        
    except Exception as e:
        logger.error(f"Error listando archivos raw: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listando archivos: {str(e)}"
        )

# Endpoints para File Watcher
@router.get("/file-watcher/status")
async def get_file_watcher_status_endpoint():
    """
    Obtener el estado del file watcher
    """
    try:
        status = get_file_watcher_status()
        
        return {
            "status": "active" if status["is_running"] else "inactive",
            "is_running": status["is_running"],
            "watch_folder": status["watch_folder"],
            "poll_interval": status.get("poll_interval", 2.0),
            "queue_pending": status.get("queue_pending", 0),
            "processing": status.get("processing", 0),
            "processed_count": status.get("processed_count", 0),
            "message": "File watcher está monitoreando archivos" if status["is_running"] else "File watcher no está activo"
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del file watcher: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estado: {str(e)}"
        )

@router.post("/file-watcher/start")
async def start_file_watcher_endpoint():
    """
    Iniciar el file watcher manualmente
    """
    try:
        if start_file_watcher():
            return {
                "status": "success",
                "message": "File watcher iniciado correctamente"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="No se pudo iniciar el file watcher"
            )
            
    except Exception as e:
        logger.error(f"Error iniciando file watcher: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error iniciando file watcher: {str(e)}"
        )

@router.post("/file-watcher/stop")
async def stop_file_watcher_endpoint():
    """
    Detener el file watcher manualmente
    """
    try:
        stop_file_watcher()
        return {
            "status": "success",
            "message": "File watcher detenido correctamente"
        }
        
    except Exception as e:
        logger.error(f"Error deteniendo file watcher: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deteniendo file watcher: {str(e)}"
        )
