"""
Endpoint para procesamiento y almacenamiento de datos RecWay
"""
import json
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import logging

from app.core.config import settings
from app.database.session import get_db
from app.schemas.recway import ProcessingResult, SegmentoFromJSON
from app.services.data.database_service import RecWayDatabaseService
from app.services.data.parser import CSVParser
from app.services.processing.csv_processor import CSVProcessor

logger = logging.getLogger(__name__)

router = APIRouter()

# Usuario base para todas las operaciones (como mencionaste)
DEFAULT_USER_ID = 1  # El admin que está en la base de datos

@router.post("/process-and-store", response_model=ProcessingResult)
async def process_and_store_data(
    csv_file_path: str = None,
    json_file_path: str = None,
    db: Session = Depends(get_db)
):
    """
    Procesa un archivo CSV y su JSON resultado, almacenando todo en la base de datos.
    
    Esta función:
    1. Lee y parsea el CSV para extraer metadatos del dispositivo y datos de sensores
    2. Lee el JSON con los segmentos procesados 
    3. Almacena todo en la base de datos de forma atómica
    4. Calcula promedios de índices y huecos por segmento
    
    Args:
        csv_file_path: Ruta al archivo CSV original
        json_file_path: Ruta al archivo JSON con segmentos procesados
        db: Sesión de base de datos
        
    Returns:
        ProcessingResult con estadísticas del procesamiento
    """
    try:
        # Validar archivos
        if not csv_file_path or not os.path.exists(csv_file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Archivo CSV no encontrado: {csv_file_path}"
            )
        
        if not json_file_path or not os.path.exists(json_file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Archivo JSON no encontrado: {json_file_path}"
            )
        
        logger.info(f"Iniciando procesamiento de archivos: CSV={csv_file_path}, JSON={json_file_path}")
        
        # 1. Parsear CSV para obtener metadatos y datos de sensores
        csv_metadata, sensor_data = CSVParser.parse_csv_file(csv_file_path)
        logger.info(f"CSV parseado: {len(sensor_data)} registros de sensores")
        
        # 2. Leer JSON con segmentos procesados
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Convertir JSON a esquemas Pydantic
        processed_segments = [SegmentoFromJSON(**segment) for segment in json_data]
        logger.info(f"JSON parseado: {len(processed_segments)} segmentos")
        
        # 3. Procesar y almacenar en base de datos
        db_service = RecWayDatabaseService(db)
        result = db_service.process_complete_data(
            csv_metadata=csv_metadata,
            processed_segments=processed_segments,
            csv_sensor_data=sensor_data,
            user_id=DEFAULT_USER_ID
        )
        
        logger.info(f"Procesamiento completado en {result.total_processing_time:.2f}s")
        logger.info(f"Resultados: {len(result.segmentos_creados)} segmentos creados, "
                   f"{len(result.segmentos_actualizados)} actualizados, "
                   f"{len(result.muestras_creadas)} muestras creadas, "
                   f"{result.registros_sensores_creados} registros de sensores")
        
        return result
        
    except Exception as e:
        logger.error(f"Error durante el procesamiento: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante el procesamiento: {str(e)}"
        )


@router.post("/process-csv-complete")
async def process_csv_complete(
    csv_file_path: str,
    db: Session = Depends(get_db)
):
    """
    Procesa un CSV completo: extrae datos, ejecuta algoritmos y almacena en BD.
    
    Esta función ejecuta todo el pipeline:
    1. Parsea el CSV
    2. Ejecuta los algoritmos de procesamiento 
    3. Almacena resultados en base de datos
    
    Args:
        csv_file_path: Ruta al archivo CSV a procesar
        db: Sesión de base de datos
        
    Returns:
        ProcessingResult con estadísticas del procesamiento
    """
    try:
        if not csv_file_path or not os.path.exists(csv_file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Archivo CSV no encontrado: {csv_file_path}"
            )
        
        logger.info(f"Iniciando procesamiento completo de CSV: {csv_file_path}")
        
        # 1. Parsear CSV
        csv_metadata, sensor_data = CSVParser.parse_csv_file(csv_file_path)
        
        # 2. Ejecutar algoritmos de procesamiento
        csv_processor = CSVProcessor()
        json_result = csv_processor.process_csv_file(csv_file_path)
        
        # 3. Convertir resultado a esquemas
        processed_segments = [SegmentoFromJSON(**segment) for segment in json_result]
        
        # 4. Almacenar en base de datos
        db_service = RecWayDatabaseService(db)
        result = db_service.process_complete_data(
            csv_metadata=csv_metadata,
            processed_segments=processed_segments,
            csv_sensor_data=sensor_data,
            user_id=DEFAULT_USER_ID
        )
        
        logger.info(f"Procesamiento completo terminado en {result.total_processing_time:.2f}s")
        
        return result
        
    except Exception as e:
        logger.error(f"Error durante el procesamiento completo: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante el procesamiento completo: {str(e)}"
        )


@router.post("/store-sensor-data")
async def store_sensor_data_only(
    csv_file_path: str,
    db: Session = Depends(get_db)
):
    """
    Almacena solo los datos de sensores de un CSV en la tabla registro_sensores.
    
    Útil cuando ya se procesaron los segmentos pero se quieren almacenar 
    los datos de sensores por separado.
    
    Args:
        csv_file_path: Ruta al archivo CSV
        db: Sesión de base de datos
        
    Returns:
        Información sobre los datos almacenados
    """
    try:
        if not csv_file_path or not os.path.exists(csv_file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Archivo CSV no encontrado: {csv_file_path}"
            )
        
        # Parsear CSV
        csv_metadata, sensor_data = CSVParser.parse_csv_file(csv_file_path)
        
        # Crear/obtener fuente de datos
        db_service = RecWayDatabaseService(db)
        fuente = db_service.create_fuente_datos_dispositivo(csv_metadata, DEFAULT_USER_ID)
        
        # Almacenar datos de sensores
        registros_creados = db_service.create_registro_sensores_bulk(sensor_data, fuente.id_fuente)
        
        db.commit()
        
        return {
            "fuente_datos_id": fuente.id_fuente,
            "registros_sensores_creados": registros_creados,
            "device_info": {
                "device_id": csv_metadata.device_id,
                "platform": csv_metadata.platform,
                "total_records": csv_metadata.total_records
            }
        }
        
    except Exception as e:
        logger.error(f"Error almacenando datos de sensores: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error almacenando datos de sensores: {str(e)}"
        )


@router.get("/processing-stats")
async def get_processing_stats(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas generales del procesamiento de datos.
    
    Returns:
        Estadísticas de la base de datos RecWay
    """
    try:
        from app.models.recway import Segmento, Muestra, FuenteDatosDispositivo, RegistroSensores
        
        # Contar registros
        total_segmentos = db.query(Segmento).count()
        total_muestras = db.query(Muestra).count()
        total_fuentes = db.query(FuenteDatosDispositivo).count()
        total_registros_sensores = db.query(RegistroSensores).count()
        
        # Estadísticas adicionales
        segmentos_con_muestras = db.query(Segmento).filter(Segmento.cantidad_muestras > 0).count()
        
        return {
            "total_segmentos": total_segmentos,
            "total_muestras": total_muestras,
            "total_fuentes_datos": total_fuentes,
            "total_registros_sensores": total_registros_sensores,
            "segmentos_con_muestras": segmentos_con_muestras,
            "promedio_muestras_por_segmento": total_muestras / max(total_segmentos, 1)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )
