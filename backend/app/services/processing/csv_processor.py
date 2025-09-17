"""
CSV Processor wrapper que usa la nueva lógica (algoritmo_posicionv1_0)
=====================================================================

- Toma los CSV de `backend/uploads/csv/raw`
- Ejecuta el procesamiento con `algoritmo_posicionv1_0/main_procesamiento.py`
- Guarda JSON rápido en `backend/uploads/json/output`
- Guarda JSON histórico nombrado por archivo en `backend/uploads/json/storage`
- Mueve CSV procesados a `backend/uploads/csv/processed`

Mantiene la API de la clase anterior para no romper endpoints existentes.
"""

import json
import sys
from pathlib import Path
from typing import List

from app.core.config import settings


class CSVProcessor:
    def __init__(self):
        # Base backend (.. / .. / .. desde este archivo)
        self._backend_base: Path = Path(__file__).resolve().parents[2]

        # Directorios locales (siguiendo mapeo a futuros contenedores Azure)
        self._csv_raw = Path(settings.CSV_RAW_DIR)
        self._csv_processed = Path(settings.CSV_PROCESSED_DIR)
        self._json_output = Path(settings.JSON_OUTPUT_DIR)
        self._json_storage = Path(settings.JSON_STORAGE_DIR)

        # Carpeta de grafos (.pkl y balltree/mids) para la nueva lógica
        self._graphs_dir = Path(settings.GRAPHS_DIR)

        # Prefijo por defecto de archivos del app móvil
        self._prefijo = "RecWay_"

        # Asegurar estructura local
        for d in [self._csv_raw, self._csv_processed, self._json_output, self._json_storage]:
            d.mkdir(parents=True, exist_ok=True)

        # Preparar import dinámico del nuevo paquete (lazy)
        self._main = None
        self._busqueda = None

    def _ensure_algo_import(self):
        if self._main is not None and self._busqueda is not None:
            return
        try:
            import importlib
            # Import using the full package path
            self._main = importlib.import_module("app.services.algoritmo_posicionv1_0.main_procesamiento")  # type: ignore
            self._busqueda = importlib.import_module("app.services.algoritmo_posicionv1_0.algoritmos_busqueda")  # type: ignore
        except ImportError as e:
            msg = str(e)
            if "morlet2" in msg or "scipy.signal" in msg:
                raise RuntimeError(
                    "Dependencia SciPy incompleta: falta scipy.signal.morlet2. "
                    "Actualiza SciPy en tu entorno: 'pip install --upgrade "
                    "\"scipy>=1.12,<2\"''."
                ) from e
            if "geopy" in msg:
                raise RuntimeError(
                    "Falta geopy. Instálalo con: 'pip install geopy>=2.3' o 'pip install -r requirements.txt'."
                ) from e
            raise

    def procesar_archivos_pendientes(self) -> List[str]:
        """Procesa todos los CSV con el prefijo en la carpeta raw.
        Retorna la lista de archivos procesados.
        """
        self._ensure_algo_import()
        archivos = self.buscar_archivos_por_nombre(str(self._csv_raw), self._prefijo)
        for nombre in archivos:
            self.procesar_archivo_especifico(nombre)
        return archivos

    def procesar_archivo_especifico(self, nombre_archivo: str):
        """Procesa un CSV específico usando la nueva lógica.
        - Ejecuta main.procesar_archivos
        - Carga el JSON histórico correspondiente y lo retorna (lista de segmentos)
        """
        csv_path = self._csv_raw / nombre_archivo
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV no encontrado en raw: {csv_path}")

        # Cargar módulos de algoritmos si hace falta
        self._ensure_algo_import()

        # Ejecutar el procesamiento con rutas mapeadas
        # Nota: el main guarda 2 archivos:
        #  - output/datos{contador}.json (rápido)
        #  - storage/datos{<nombre_csv>}save.json (histórico y único)
        self._main.procesar_archivos(
            dato=nombre_archivo,
            carpeta_csv=str(self._csv_raw),
            carpeta_archivos_json=str(self._json_output),
            carpeta_almacenamiento_json=str(self._json_storage),
            carpeta_almacenamiento_csv=str(self._csv_processed),
            umbral=3.0,
            carpeta_grafos=str(self._graphs_dir),
        )

        # Buscar el JSON histórico por nombre determinístico
        base = nombre_archivo[:-4] if nombre_archivo.lower().endswith(".csv") else nombre_archivo
        hist_json = self._json_storage / f"datos{base}save.json"
        if hist_json.exists():
            try:
                with open(hist_json, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                # Fallback: devolver None si no se pudo leer
                return None

        # Fallback: intentar el último JSON en output
        candidates = sorted(self._json_output.glob("datos*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            try:
                with open(candidates[0], "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None

        return None

    def process_csv_file(self, csv_file_path: str):
        """Compatibilidad: procesa un CSV por ruta absoluta.
        Copia el archivo a la carpeta raw con el nombre original y reutiliza
        procesar_archivo_especifico para mantener un solo flujo.
        """
        src = Path(csv_file_path)
        if not src.exists():
            raise FileNotFoundError(f"CSV no encontrado: {src}")
        # Normalizamos: copiar a raw si no está ya en raw
        dest = self._csv_raw / src.name
        if src.resolve() != dest.resolve():
            dest.write_bytes(src.read_bytes())
        return self.procesar_archivo_especifico(src.name)

    def buscar_archivos_por_nombre(self, carpeta: str, prefijo: str) -> List[str]:
        """Devuelve la lista de archivos con prefijo en la carpeta dada."""
        self._ensure_algo_import()
        try:
            return self._busqueda.buscar_archivos_por_nombre(carpeta, prefijo)
        except Exception:
            # Fallback simple si falla el módulo de búsqueda
            p = Path(carpeta)
            return [f.name for f in p.glob(f"{prefijo}*.csv")]

    @property
    def carpeta_csv(self) -> str:
        return str(self._csv_raw)

    @property
    def carpeta_almacenamiento_csv(self) -> str:
        return str(self._csv_processed)

    @property
    def prefijo_busqueda(self) -> str:
        return self._prefijo

    @property
    def carpeta_archivos_json(self) -> str:
        # Conservamos compat pero preferimos usar almacenamiento histórico
        return str(self._json_output)

    @property
    def carpeta_almacenamiento_json(self) -> str:
        return str(self._json_storage)


csv_processor = CSVProcessor()
