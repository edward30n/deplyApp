from fastapi import APIRouter, HTTPException
from app.services.processing.csv_processor import csv_processor
import os

router = APIRouter()

@router.post("/force-process-all")
async def force_process_all():
    """Fuerza el procesamiento de todos los archivos en la carpeta raw"""
    try:
        result = csv_processor.procesar_archivos_pendientes()
        return {
            "message": "Procesamiento forzado completado",
            "results": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en procesamiento: {str(e)}")

@router.post("/force-process/{filename}")
async def force_process_file(filename: str):
    """Fuerza el procesamiento de un archivo específico"""
    try:
        # Verificar que el archivo existe
        file_path = os.path.join(csv_processor.carpeta_csv, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Archivo {filename} no encontrado")
        
        result = csv_processor.procesar_archivo_especifico(filename)
        return {
            "message": f"Procesamiento de {filename} completado",
            "result": result
        }
    except ValueError as e:
        # Error específico del algoritmo (como "La arista no existe en el grafo")
        return {
            "message": f"Procesamiento de {filename} completado con advertencias",
            "warning": str(e),
            "status": "partial_success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en procesamiento: {str(e)}")

@router.get("/list-pending")
async def list_pending_files():
    """Lista archivos pendientes de procesar"""
    try:
        files = os.listdir(csv_processor.carpeta_csv)
        csv_files = [f for f in files if f.endswith('.csv')]
        return {
            "pending_files": csv_files,
            "count": len(csv_files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando archivos: {str(e)}")
