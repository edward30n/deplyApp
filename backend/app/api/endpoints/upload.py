"""Endpoint simple para subir CSV y colocarlo en uploads/csv/raw"""
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from pathlib import Path
import shutil
import sys
import traceback
from typing import Optional, List

router = APIRouter()

# Base real del backend (sube cuatro niveles hasta la carpeta backend)
BACKEND_BASE = Path(__file__).resolve().parent.parent.parent.parent  # .../backend
RAW_DIR = BACKEND_BASE / "uploads" / "csv" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload-csv")
async def upload_csv_file(background_tasks: BackgroundTasks, file: UploadFile = File(...), sync: bool = False):
    print("[UPLOAD] Inicio subida archivo:", file.filename)
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .csv")
    target_path = RAW_DIR / file.filename
    # Evitar sobreescritura añadiendo sufijo si existe
    counter = 1
    base = target_path.stem
    ext = target_path.suffix
    while target_path.exists():
        target_path = RAW_DIR / f"{base}_{counter}{ext}"
        counter += 1
    try:
        with open(target_path, 'wb') as out:
            shutil.copyfileobj(file.file, out)
        print(f"[UPLOAD] Guardado en {target_path}")
    except Exception as e:
        print("[UPLOAD][ERROR] Falló guardado:", e)
        raise HTTPException(status_code=500, detail=f"Error guardando archivo: {e}")

    def run_process(nombre):
        try:
            print("[PROCESS] Iniciando procesamiento de:", nombre)
            services_dir = Path(__file__).resolve().parent.parent.parent / 'services'
            if str(services_dir) not in sys.path:
                sys.path.insert(0, str(services_dir))
                print("[PROCESS] Añadido services al sys.path")
            from app.services.processing.csv_processor import csv_processor
            resultado = csv_processor.procesar_archivo_especifico(Path(nombre).name)
            print("[PROCESS] Resultado segmentos:", len(resultado) if isinstance(resultado, list) else resultado)
        except Exception as e:
            print("[PROCESS][ERROR]", e)
            traceback.print_exc()

    if sync:
        run_process(target_path)
        return {"message": "Archivo subido y procesado (sync)", "filename": target_path.name, "path": str(target_path)}
    else:
        background_tasks.add_task(run_process, target_path)
        return {"message": "Archivo subido", "filename": target_path.name, "path": str(target_path)}


@router.post("/upload-multiple-csv")
async def upload_multiple_csv_files(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...), sync: bool = False):
    """
    Subir múltiples archivos CSV simultáneamente
    """
    print(f"[UPLOAD-MULTIPLE] Inicio subida de {len(files)} archivos")
    
    if not files:
        raise HTTPException(status_code=400, detail="No se enviaron archivos")
    
    uploaded_files = []
    errors = []
    
    # Función para procesar un archivo específico
    def run_process_single(file_path, filename):
        try:
            print(f"[PROCESS-MULTIPLE] Iniciando procesamiento de: {filename}")
            services_dir = Path(__file__).resolve().parent.parent.parent / 'services'
            if str(services_dir) not in sys.path:
                sys.path.insert(0, str(services_dir))
                print(f"[PROCESS-MULTIPLE] Añadido services al sys.path para {filename}")
            from app.services.processing.csv_processor import csv_processor
            resultado = csv_processor.procesar_archivo_especifico(Path(file_path).name)
            print(f"[PROCESS-MULTIPLE] Resultado segmentos para {filename}:", len(resultado) if isinstance(resultado, list) else resultado)
        except Exception as e:
            print(f"[PROCESS-MULTIPLE][ERROR] {filename}:", e)
            traceback.print_exc()
    
    # Procesar cada archivo
    for file in files:
        try:
            # Validar extensión
            if not file.filename.lower().endswith('.csv'):
                errors.append(f"Archivo {file.filename}: Solo se permiten archivos .csv")
                continue
            
            # Determinar path de destino
            target_path = RAW_DIR / file.filename
            counter = 1
            base = target_path.stem
            ext = target_path.suffix
            while target_path.exists():
                target_path = RAW_DIR / f"{base}_{counter}{ext}"
                counter += 1
            
            # Guardar archivo
            with open(target_path, 'wb') as out:
                shutil.copyfileobj(file.file, out)
            
            print(f"[UPLOAD-MULTIPLE] Guardado: {target_path}")
            
            uploaded_files.append({
                "original_filename": file.filename,
                "saved_filename": target_path.name,
                "path": str(target_path),
                "status": "uploaded"
            })
            
            # Procesar archivo
            if sync:
                run_process_single(target_path, file.filename)
                uploaded_files[-1]["status"] = "processed"
            else:
                background_tasks.add_task(run_process_single, target_path, file.filename)
                uploaded_files[-1]["status"] = "processing_queued"
                
        except Exception as e:
            error_msg = f"Error guardando {file.filename}: {str(e)}"
            print(f"[UPLOAD-MULTIPLE][ERROR] {error_msg}")
            errors.append(error_msg)
    
    # Preparar respuesta
    response = {
        "total_files": len(files),
        "uploaded_successfully": len(uploaded_files),
        "errors": len(errors),
        "uploaded_files": uploaded_files,
        "processing_mode": "sync" if sync else "async"
    }
    
    if errors:
        response["error_details"] = errors
    
    print(f"[UPLOAD-MULTIPLE] Completado: {len(uploaded_files)} exitosos, {len(errors)} errores")
    
    return response
