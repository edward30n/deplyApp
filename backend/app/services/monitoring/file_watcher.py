"""
File Watcher integrado con RecWay Database para procesamiento automático completo.
Implementación basada en un hilo de polling (sin watchdog) para reducir complejidad.
Características:
- Polling ligero cada pocos segundos (configurable)
- Detección de nuevos archivos CSV en carpeta raw
- Verifica que el archivo esté "estable" (sin crecer) antes de procesar
- Procesamiento automático: CSV → JSON → Base de Datos
- Manejo seguro de múltiples archivos llegando casi simultáneamente
- Evita reprocesar archivos ya procesados
"""
import os
import time
import threading
import logging
import json
from typing import Dict, Set
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, Future
from app.services.processing.csv_processor import csv_processor
from app.services.data.database_service import RecWayDatabaseService
from app.services.data.parser import CSVParser
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)

class SimpleCSVWatcher:
    """Watcher basado en polling para una carpeta de archivos CSV con ThreadPoolExecutor para concurrencia."""

    def __init__(self, watch_folder: str = None, poll_interval: float = 2.0, stable_seconds: float = 3.0, max_concurrent_files: int = 3):
        from app.core.config import settings
        # Por defecto usa el directorio configurado
        self.watch_folder = Path(watch_folder or settings.CSV_RAW_DIR)
        self.poll_interval = poll_interval
        self.stable_seconds = stable_seconds
        self.max_concurrent_files = max_concurrent_files
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._seen_files: Dict[str, Dict[str, float]] = {}
        # _seen_files[path] = { 'first_seen': t, 'last_size': size, 'last_mtime': mtime, 'last_stable_since': t }
        self._processed: Set[str] = set()
        self._processing: Set[str] = set()
        self._last_cycle_duration: float | None = None
        
        # PARALELO SEGURO: max_workers=3 con UUID para evitar conflictos
        self._executor = ThreadPoolExecutor(
            max_workers=3,  # PARALELO: Máximo 3 archivos simultáneos
            thread_name_prefix="csv-processor"
        )
        self._active_futures: Dict[str, Future] = {}  # file_path -> Future

    def start(self):
        if self.is_running:
            logger.warning("File watcher ya está corriendo")
            return True
        try:
            self.watch_folder.mkdir(parents=True, exist_ok=True)
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, name="csv-watcher", daemon=True)
            self._thread.start()
            logger.info(f"🔍 File watcher (simple) iniciado - monitoreando: {self.watch_folder.resolve()}")
            return True
        except Exception as e:
            logger.error(f"❌ No se pudo iniciar el file watcher: {e}")
            return False

    def stop(self):
        if not self.is_running:
            logger.warning("File watcher no está activo")
            return
        logger.info("🛑 Deteniendo file watcher...")
        self._stop_event.set()
        
        # Cancelar futuros pendientes
        for file_path, future in self._active_futures.items():
            if not future.done():
                logger.info(f"Cancelando procesamiento de {file_path}")
                future.cancel()
        
        # Shutdown del ThreadPoolExecutor (sin timeout para compatibilidad)
        self._executor.shutdown(wait=True)
        
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("🛑 File watcher detenido")

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and not self._stop_event.is_set()

    def _run_loop(self):
        while not self._stop_event.is_set():
            cycle_start = time.time()
            try:
                self._scan_once()
                self._cleanup_completed_futures()  # Limpiar futuros completados
            except Exception as e:
                logger.error(f"Error en ciclo de watcher: {e}")
            self._last_cycle_duration = time.time() - cycle_start
            # Espera respetando el tiempo ya consumido
            remaining = self.poll_interval
            for _ in range(int(remaining * 10)):
                if self._stop_event.is_set():
                    break
                time.sleep(0.1)
                
    def _cleanup_completed_futures(self):
        """Limpia futuros completados del tracking"""
        completed_paths = [
            path for path, future in self._active_futures.items() 
            if future.done()
        ]
        for path in completed_paths:
            self._active_futures.pop(path, None)

    def _scan_once(self):
        if not self.watch_folder.exists():
            return
        now = time.time()
        try:
            current_files = [f for f in self.watch_folder.iterdir() if f.is_file() and f.suffix.lower() == '.csv']
        except Exception as e:
            logger.error(f"No se pudo listar archivos en {self.watch_folder}: {e}")
            return

        with self._lock:
            for file_path in current_files:
                path_str = str(file_path)
                if path_str in self._processed or path_str in self._processing:
                    continue
                try:
                    stat = file_path.stat()
                except FileNotFoundError:
                    continue
                size = stat.st_size
                mtime = stat.st_mtime
                entry = self._seen_files.get(path_str)
                if entry is None:
                    # Nuevo archivo
                    self._seen_files[path_str] = {
                        'first_seen': now,
                        'last_size': size,
                        'last_mtime': mtime,
                        'last_stable_since': now
                    }
                    logger.info(f"Archivo CSV detectado: {path_str}")
                    continue
                # Si cambió tamaño o mtime reiniciamos ventana de estabilidad
                if size != entry['last_size'] or mtime != entry['last_mtime']:
                    entry['last_size'] = size
                    entry['last_mtime'] = mtime
                    entry['last_stable_since'] = now
                    continue
                # Verificar si alcanzó estabilidad
                if (now - entry['last_stable_since']) >= self.stable_seconds:
                    self._processing.add(path_str)
                    # USAR THREADPOOL en lugar de Thread individual
                    future = self._executor.submit(self._process_file_safe, file_path)
                    self._active_futures[path_str] = future
                    
                    # Callback para limpiar cuando termine
                    def cleanup_future(fut, path=path_str):
                        self._active_futures.pop(path, None)
                    future.add_done_callback(cleanup_future)
            # Limpiar entradas de archivos desaparecidos
            existing_set = {str(p) for p in current_files}
            to_remove = [p for p in self._seen_files.keys() if p not in existing_set and p not in self._processing]
            for p in to_remove:
                self._seen_files.pop(p, None)
            # Permitir reprocesar el mismo nombre si ya no está en raw
            processed_to_drop = [p for p in list(self._processed) if p not in existing_set]
            for p in processed_to_drop:
                self._processed.discard(p)

    def _process_file_safe(self, file_path: Path):
        path_str = str(file_path)
        filename = file_path.name
        db = None
        
        try:
            logger.info(f"🔄 Iniciando procesamiento automático completo de: {filename}")
            
            # PASO 1: Verificar que el archivo existe y no está vacío
            if not file_path.exists() or file_path.stat().st_size == 0:
                logger.warning(f"⚠️ Archivo no válido o vacío: {filename}")
                return
            
            # PASO 2: Procesar CSV → JSON
            logger.info(f"📄 Paso 1/3: Procesando CSV → JSON para {filename}")
            csv_result = csv_processor.procesar_archivo_especifico(filename)
            if not csv_result:
                logger.error(f"❌ Error en procesamiento CSV → JSON para: {filename}")
                return
            
            logger.info(f"✅ CSV → JSON completado para {filename}")
            
            # PASO 3: Determinar rutas de archivos
            from app.core.config import settings
            processed_csv_path = Path(settings.CSV_PROCESSED_DIR) / filename
            # El JSON se genera en storage con el patrón: datosNOMBREsave.json
            base_name = filename.replace('.csv', '')
            json_filename = f"datos{base_name}save.json"
            json_path = Path(settings.JSON_STORAGE_DIR) / json_filename
            
            if not processed_csv_path.exists():
                logger.error(f"❌ Archivo CSV procesado no encontrado: {processed_csv_path}")
                return
                
            if not json_path.exists():
                logger.error(f"❌ Archivo JSON no encontrado: {json_path}")
                return
            
            # PASO 4: Almacenar en base de datos
            logger.info(f"💾 Paso 2/3: Almacenando datos en BD para {filename}")
            
            # Inicializar conexión a BD y servicio
            db = SessionLocal()
            recway_service = RecWayDatabaseService(db)
            csv_parser = CSVParser()
            
            # Usuario admin por defecto (ID=1)
            admin_user_id = 1
            
            # Parsear archivos como lo hacemos en los endpoints
            csv_metadata, csv_sensor_data = CSVParser.parse_csv_file(str(processed_csv_path.resolve()))
            
            # Leer JSON con segmentos procesados
            with open(str(json_path.resolve()), 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Convertir JSON a esquemas Pydantic
            from app.schemas.recway import SegmentoFromJSON
            processed_segments = [SegmentoFromJSON(**segment) for segment in json_data]
            
            # Procesar y almacenar datos completos
            db_result = recway_service.process_complete_data(
                csv_metadata=csv_metadata,
                processed_segments=processed_segments,
                csv_sensor_data=csv_sensor_data,
                user_id=admin_user_id
            )
            
            # Confirmar transacción
            db.commit()
            
            logger.info(f"✅ Almacenamiento en BD completado para {filename}")
            logger.info(f"📊 Resultados: {len(db_result.segmentos_creados)} segmentos creados, "
                       f"{len(db_result.muestras_creadas)} muestras, "
                       f"{db_result.registros_sensores_creados} registros de sensores")
            
            # PASO 5: Éxito total
            logger.info(f"🎉 Procesamiento automático COMPLETO para {filename}")
            logger.info(f"⏱️ Tiempo total: {db_result.total_processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Error en procesamiento automático de {filename}: {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
            with self._lock:
                self._processing.discard(path_str)
                self._processed.add(path_str)
                self._seen_files.pop(path_str, None)

    def status(self) -> dict:
        """Estado del file watcher con estadísticas de base de datos"""
        with self._lock:
            base_status = {
                'is_running': self.is_running,
                'watch_folder': str(self.watch_folder.resolve()),
                'poll_interval': self.poll_interval,
                'stable_seconds': self.stable_seconds,
                'queue_pending': len(self._seen_files),
                'processing': len(self._processing),
                'processed_count': len(self._processed),
                'last_cycle_duration': self._last_cycle_duration
            }
            
            # Agregar estadísticas de base de datos
            try:
                # TODO: Implementar get_processing_stats() en RecWayDatabaseService
                # db = SessionLocal()
                # recway_service = RecWayDatabaseService(db)
                # db_stats = recway_service.get_processing_stats()
                # base_status.update({
                #     'database_stats': db_stats
                # })
                # db.close()
                base_status['database_stats'] = {'message': 'Stats not implemented yet'}
            except Exception as e:
                logger.warning(f"No se pudieron obtener estadísticas de BD: {e}")
                base_status['database_stats'] = {'error': str(e)}
            
            return base_status

# Instancia global y funciones de fachada para mantener API previa
_file_watcher = SimpleCSVWatcher()

def start_file_watcher():
    return _file_watcher.start()

def stop_file_watcher():
    return _file_watcher.stop()

def get_file_watcher_status():
    return _file_watcher.status()
