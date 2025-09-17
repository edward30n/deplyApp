"""
Servicio de base de datos para RecWay - Operaciones CRUD y lógica de negocio
CONCURRENCY SAFE: Implementa UPSERT patterns y manejo de race conditions
"""
import statistics
import time
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
import logging

from app.models.recway import (
    Segmento, Geometria, IndicesSegmento, HuecoSegmento,
    Muestra, IndicesMuestra, HuecoMuestra,
    FuenteDatosDispositivo, RegistroSensores
)
from app.schemas.recway import (
    SegmentoCreate, GeometriaCreate, IndicesSegmentoCreate, HuecoSegmentoCreate,
    MuestraCreate, IndicesMuestraCreate, HuecoMuestraCreate,
    FuenteDatosDispositivoCreate, RegistroSensoresCreate,
    SegmentoFromJSON, CSVMetadata, ProcessingResult
)

logger = logging.getLogger(__name__)

class RecWayDatabaseService:
    """Servicio principal para operaciones de base de datos de RecWay"""

    def __init__(self, db: Session):
        self.db = db

    # =================== SEGMENTOS ===================

    def get_segmento_by_original_id(self, id_original: str) -> Optional[Segmento]:
        """Obtiene un segmento por su ID original del JSON"""
        return self.db.query(Segmento).filter(Segmento.id_original == id_original).first()

    def create_or_get_segmento_safe(self, segmento_data: SegmentoFromJSON, user_id: int) -> Tuple[Segmento, bool]:
        """
        Crea o obtiene un segmento de forma thread-safe usando UPSERT pattern.
        
        Returns:
            Tuple[Segmento, bool]: (segmento, was_created)
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Intentar obtener primero
                segmento = self.get_segmento_by_original_id(str(segmento_data.id))
                if segmento:
                    logger.debug(f"Segmento {segmento_data.id} already exists - usando existente")
                    return segmento, False  # Existente, no creado
                
                # Si no existe, intentar crear
                logger.info(f"Creando nuevo segmento {segmento_data.id} (attempt {attempt + 1})")
                segmento = self.create_segmento(segmento_data, user_id)
                self.db.commit()
                return segmento, True  # Creado exitosamente
                
            except IntegrityError as e:
                # Otro hilo creó el segmento entre nuestro check y create
                logger.warning(f"IntegrityError en segmento {segmento_data.id}, attempt {attempt + 1}: {e}")
                self.db.rollback()
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    sleep_time = 0.1 * (2 ** attempt)
                    time.sleep(sleep_time)
                    continue
                else:
                    # Final attempt - solo obtener
                    segmento = self.get_segmento_by_original_id(str(segmento_data.id))
                    if segmento:
                        logger.info(f"Segmento {segmento_data.id} obtenido después de race condition")
                        return segmento, False
                    else:
                        logger.error(f"No se pudo crear ni obtener segmento {segmento_data.id}")
                        raise Exception(f"Failed to create or get segmento {segmento_data.id} after {max_retries} retries")
            
            except Exception as e:
                logger.error(f"Error inesperado creando segmento {segmento_data.id}: {e}")
                self.db.rollback()
                raise
                
        raise Exception(f"Failed to create/get segmento {segmento_data.id} after {max_retries} retries")

    def create_segmento(self, segmento_data: SegmentoFromJSON, user_id: int) -> Segmento:
        """Crea un nuevo segmento con su geometría"""
        # Crear el segmento
        segmento = Segmento(
            id_original=str(segmento_data.id),  # ID original del JSON como string
            nombre=segmento_data.nombre,
            tipo=segmento_data.tipo,
            nodo_inicial_x=segmento_data.longitud_origen,
            nodo_final_x=segmento_data.longitud_destino,
            nodo_inicial_y=segmento_data.latitud_origen,
            nodo_final_y=segmento_data.latitud_destino,
            cantidad_muestras=1,  # Primera muestra
            ultima_fecha_muestra=segmento_data.fecha,
            longitud=segmento_data.longitud,
            created_by_user_id=user_id
        )
        
        self.db.add(segmento)
        self.db.flush()  # Para obtener el ID
        
        # Crear geometría
        for geom_data in segmento_data.geometria:
            geometria = Geometria(
                orden=geom_data["orden"],
                coordenada_x=geom_data["longitud"],
                coordenada_y=geom_data["latitud"],
                id_segmento_seleccionado=segmento.id_segmento
            )
            self.db.add(geometria)
        
        # Crear índices iniciales
        indices = IndicesSegmento(
            nota_general=segmento_data.IQR,
            iri_modificado=segmento_data.IRI_modificado,
            iri_estandar=segmento_data.iri,
            indice_primero=segmento_data.az,
            indice_segundo=segmento_data.ax,
            iri_tercero=segmento_data.wx,
            id_segmento_seleccionado=segmento.id_segmento
        )
        self.db.add(indices)
        
        # Crear huecos si existen
        if segmento_data.huecos:
            for hueco_data in segmento_data.huecos:
                hueco = HuecoSegmento(
                    latitud=hueco_data["latitud"],
                    longitud=hueco_data["longitud"],
                    magnitud=hueco_data["magnitud"],
                    velocidad=hueco_data["velocidad"],
                    ultima_fecha_muestra=segmento_data.fecha,
                    id_segmento_seleccionado=segmento.id_segmento
                )
                self.db.add(hueco)
        
        return segmento

    def update_segmento_counters(self, segmento_id: int, nueva_fecha: str):
        """Actualiza contadores y fecha del segmento"""
        segmento = self.db.query(Segmento).filter(Segmento.id_segmento == segmento_id).first()
        if segmento:
            segmento.cantidad_muestras += 1
            segmento.ultima_fecha_muestra = nueva_fecha

    def recalculate_segmento_indices(self, segmento_id: int):
        """Recalcula los índices del segmento basado en el promedio de sus muestras"""
        # Obtener todas las muestras del segmento
        muestras = self.db.query(Muestra).filter(
            Muestra.id_segmento_seleccionado == segmento_id
        ).all()
        
        if not muestras:
            return
        
        # Obtener todos los índices de las muestras
        indices_muestras = []
        for muestra in muestras:
            indices = self.db.query(IndicesMuestra).filter(
                IndicesMuestra.id_muestra == muestra.id_muestra
            ).first()
            if indices:
                indices_muestras.append(indices)
        
        if not indices_muestras:
            return
        
        # Calcular promedios
        nota_general_promedio = statistics.mean([i.nota_general for i in indices_muestras])
        iri_modificado_promedio = statistics.mean([i.iri_modificado for i in indices_muestras])
        iri_estandar_promedio = statistics.mean([i.iri_estandar for i in indices_muestras])
        indice_primero_promedio = statistics.mean([i.indice_primero for i in indices_muestras])
        indice_segundo_promedio = statistics.mean([i.indice_segundo for i in indices_muestras])
        iri_tercero_promedio = statistics.mean([i.iri_tercero for i in indices_muestras if i.iri_tercero is not None])
        
        # Actualizar índices del segmento
        indices_segmento = self.db.query(IndicesSegmento).filter(
            IndicesSegmento.id_segmento_seleccionado == segmento_id
        ).first()
        
        if indices_segmento:
            indices_segmento.nota_general = nota_general_promedio
            indices_segmento.iri_modificado = iri_modificado_promedio
            indices_segmento.iri_estandar = iri_estandar_promedio
            indices_segmento.indice_primero = indice_primero_promedio
            indices_segmento.indice_segundo = indice_segundo_promedio
            indices_segmento.iri_tercero = iri_tercero_promedio

    def recalculate_segmento_huecos(self, segmento_id: int):
        """Recalcula los huecos del segmento basado en el promedio de sus muestras"""
        # Primero eliminar huecos existentes del segmento
        self.db.query(HuecoSegmento).filter(
            HuecoSegmento.id_segmento_seleccionado == segmento_id
        ).delete()
        
        # Obtener todos los huecos de las muestras del segmento
        muestras = self.db.query(Muestra).filter(
            Muestra.id_segmento_seleccionado == segmento_id
        ).all()
        
        all_huecos = []
        ultima_fecha = None
        
        for muestra in muestras:
            huecos_muestra = self.db.query(HuecoMuestra).filter(
                HuecoMuestra.id_muestra_seleccionada == muestra.id_muestra
            ).all()
            all_huecos.extend(huecos_muestra)
            if muestra.fecha_muestra:
                ultima_fecha = muestra.fecha_muestra
        
        if not all_huecos:
            return
        
        # Agrupar huecos por posición aproximada (tolerancia de 0.0001 grados)
        grouped_huecos = {}
        tolerance = 0.0001
        
        for hueco in all_huecos:
            key = None
            for existing_key in grouped_huecos.keys():
                lat_diff = abs(existing_key[0] - hueco.latitud)
                lng_diff = abs(existing_key[1] - hueco.longitud)
                if lat_diff < tolerance and lng_diff < tolerance:
                    key = existing_key
                    break
            
            if key is None:
                key = (hueco.latitud, hueco.longitud)
                grouped_huecos[key] = []
            
            grouped_huecos[key].append(hueco)
        
        # Crear huecos promedio para el segmento
        for (lat, lng), huecos_grupo in grouped_huecos.items():
            magnitud_promedio = statistics.mean([h.magnitud for h in huecos_grupo])
            velocidad_promedio = statistics.mean([h.velocidad for h in huecos_grupo])
            
            hueco_segmento = HuecoSegmento(
                latitud=lat,
                longitud=lng,
                magnitud=magnitud_promedio,
                velocidad=velocidad_promedio,
                ultima_fecha_muestra=ultima_fecha,
                id_segmento_seleccionado=segmento_id
            )
            self.db.add(hueco_segmento)

    # =================== MUESTRAS ===================

    def create_muestra(self, segmento_data: SegmentoFromJSON, metadata: CSVMetadata, user_id: int, segmento_id: int) -> Muestra:
        """Crea una nueva muestra con sus índices y huecos"""
        # Crear la muestra
        muestra = Muestra(
            tipo_dispositivo=metadata.platform,
            identificador_dispositivo=metadata.device_id,
            fecha_muestra=segmento_data.fecha,
            id_segmento_seleccionado=segmento_id,  # Usar el ID de la BD, no el del JSON
            created_by_user_id=user_id
        )
        
        self.db.add(muestra)
        self.db.flush()  # Para obtener el ID
        
        # Crear índices de la muestra
        indices = IndicesMuestra(
            nota_general=segmento_data.IQR,
            iri_modificado=segmento_data.IRI_modificado,
            iri_estandar=segmento_data.iri,
            indice_primero=segmento_data.az,
            indice_segundo=segmento_data.ax,
            iri_tercero=segmento_data.wx,
            id_muestra=muestra.id_muestra
        )
        self.db.add(indices)
        
        # Crear huecos de la muestra
        if segmento_data.huecos:
            for hueco_data in segmento_data.huecos:
                hueco = HuecoMuestra(
                    latitud=hueco_data["latitud"],
                    longitud=hueco_data["longitud"],
                    magnitud=hueco_data["magnitud"],
                    velocidad=hueco_data["velocidad"],
                    id_muestra_seleccionada=muestra.id_muestra
                )
                self.db.add(hueco)
        
        return muestra

    # =================== DISPOSITIVOS Y SENSORES ===================

    def create_fuente_datos_dispositivo(self, metadata: CSVMetadata, user_id: int) -> FuenteDatosDispositivo:
        """Crea una nueva fuente de datos del dispositivo"""
        fuente = FuenteDatosDispositivo(
            device_id=metadata.device_id,
            session_id=metadata.session_id,
            platform=metadata.platform,
            device_model=metadata.device_model,
            manufacturer=metadata.manufacturer,
            brand=metadata.brand,
            os_version=metadata.os_version,
            app_version=metadata.app_version,
            company=metadata.company,
            android_id=metadata.android_id,
            battery_info=metadata.battery_info,
            acc_available=metadata.acc_available,
            acc_info=metadata.acc_info,
            gyro_available=metadata.gyro_available,
            gyro_info=metadata.gyro_info,
            gps_available=metadata.gps_available,
            gps_info=metadata.gps_info,
            export_date=metadata.export_date,
            total_records=metadata.total_records,
            sampling_rate=metadata.sampling_rate,
            recording_duration=metadata.recording_duration,
            average_sample_rate=metadata.average_sample_rate,
            created_by_user_id=user_id
        )
        
        self.db.add(fuente)
        self.db.flush()
        return fuente

    def create_registro_sensores_bulk(self, sensor_data: List[Dict[str, Any]], fuente_id: int) -> int:
        """Crea registros de sensores en lote para mejor rendimiento"""
        registros = []
        
        for row in sensor_data:
            # Calcular magnitudes si no están presentes
            acc_magnitude = None
            gyro_magnitude = None
            
            if all(k in row for k in ['acc_x', 'acc_y', 'acc_z']):
                if all(row[k] is not None for k in ['acc_x', 'acc_y', 'acc_z']):
                    acc_magnitude = (row['acc_x']**2 + row['acc_y']**2 + row['acc_z']**2)**0.5
            
            if all(k in row for k in ['gyro_x', 'gyro_y', 'gyro_z']):
                if all(row[k] is not None for k in ['gyro_x', 'gyro_y', 'gyro_z']):
                    gyro_magnitude = (row['gyro_x']**2 + row['gyro_y']**2 + row['gyro_z']**2)**0.5
            
            registro = RegistroSensores(
                timestamp=int(row['timestamp']),
                acc_x=row.get('acc_x'),
                acc_y=row.get('acc_y'),
                acc_z=row.get('acc_z'),
                acc_magnitude=acc_magnitude,
                gyro_x=row.get('gyro_x'),
                gyro_y=row.get('gyro_y'),
                gyro_z=row.get('gyro_z'),
                gyro_magnitude=gyro_magnitude,
                gps_lat=row.get('gps_lat'),
                gps_lng=row.get('gps_lng'),
                gps_accuracy=row.get('gps_accuracy'),
                gps_speed=row.get('gps_speed'),
                gps_altitude=row.get('gps_altitude'),
                gps_heading=row.get('gps_heading'),
                id_fuente=fuente_id
            )
            registros.append(registro)
        
        # Insertar en lotes para mejor rendimiento
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(registros), batch_size):
            batch = registros[i:i + batch_size]
            self.db.add_all(batch)
            total_inserted += len(batch)
        
        return total_inserted

    # =================== OPERACIONES PRINCIPALES ===================

    def process_complete_data(self, 
                            csv_metadata: CSVMetadata, 
                            processed_segments: List[SegmentoFromJSON],
                            csv_sensor_data: List[Dict[str, Any]],
                            user_id: int) -> ProcessingResult:
        """
        Procesa un conjunto completo de datos: segmentos, muestras y sensores
        Esta es la función principal que orquesta todo el procesamiento
        """
        start_time = datetime.now()
        
        # 1. Crear fuente de datos del dispositivo
        fuente = self.create_fuente_datos_dispositivo(csv_metadata, user_id)
        
        # 2. Procesar cada segmento
        segmentos_creados = []
        segmentos_actualizados = []
        muestras_creadas = []
        
        for segmento_data in processed_segments:
            # USAR MÉTODO THREAD-SAFE para crear/obtener segmento
            segmento, was_created = self.create_or_get_segmento_safe(segmento_data, user_id)
            
            if was_created:
                # Segmento creado: agregarlo a la lista
                segmentos_creados.append(segmento.id_segmento)
            else:
                # Segmento existía: actualizar contadores
                self.update_segmento_counters(segmento.id_segmento, segmento_data.fecha)
                segmentos_actualizados.append(segmento.id_segmento)
            
            # Crear muestra (siempre) - usar el ID del segmento en BD
            nueva_muestra = self.create_muestra(segmento_data, csv_metadata, user_id, segmento.id_segmento)
            muestras_creadas.append(nueva_muestra.id_muestra)
            
            # Recalcular índices y huecos del segmento
            self.recalculate_segmento_indices(segmento.id_segmento)
            self.recalculate_segmento_huecos(segmento.id_segmento)
        
        # 3. Crear registros de sensores
        registros_creados = self.create_registro_sensores_bulk(csv_sensor_data, fuente.id_fuente)
        
        # 4. Commit de toda la transacción
        self.db.commit()
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        return ProcessingResult(
            fuente_datos_id=fuente.id_fuente,
            segmentos_creados=segmentos_creados,
            segmentos_actualizados=segmentos_actualizados,
            muestras_creadas=muestras_creadas,
            registros_sensores_creados=registros_creados,
            total_processing_time=processing_time
        )
