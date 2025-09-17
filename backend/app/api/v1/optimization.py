from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.database.session import get_db
from app.models.recway import Segmento, Geometria, Muestra
from typing import Optional, Generator, Dict, Any
import logging
import json
import asyncio
from datetime import datetime

router = APIRouter(prefix="/api/export/optimized")
logger = logging.getLogger(__name__)

@router.get("/viewport")
async def export_segments_in_viewport(
    min_lat: float = Query(..., description="Latitud mínima del viewport"),
    max_lat: float = Query(..., description="Latitud máxima del viewport"),
    min_lng: float = Query(..., description="Longitud mínima del viewport"),
    max_lng: float = Query(..., description="Longitud máxima del viewport"),
    max_segments: int = Query(200, le=500, description="Máximo segmentos a retornar"),
    db: Session = Depends(get_db)
):
    """
    Exporta solo segmentos dentro del viewport visible del mapa
    Optimizado para cargas rápidas en interfaces web
    """
    try:
        # Query optimizada con filtro geográfico
        query = db.query(Segmento).filter(
            and_(
                Segmento.nodo_inicial_y >= min_lat,
                Segmento.nodo_inicial_y <= max_lat,
                Segmento.nodo_inicial_x >= min_lng,
                Segmento.nodo_inicial_x <= max_lng
            )
        ).limit(max_segments)
        
        segmentos = query.all()
        
        # Respuesta ligera solo con datos esenciales
        result = {
            "viewport": {
                "min_lat": min_lat, "max_lat": max_lat,
                "min_lng": min_lng, "max_lng": max_lng
            },
            "segments_found": len(segmentos),
            "segments": []
        }
        
        for segmento in segmentos:
            # Solo datos esenciales para el mapa
            segment_data = {
                "id": segmento.id_segmento,
                "name": segmento.nombre,
                "type": segmento.tipo,
                "start_lat": float(segmento.nodo_inicial_y),
                "start_lng": float(segmento.nodo_inicial_x),
                "end_lat": float(segmento.nodo_final_y),
                "end_lng": float(segmento.nodo_final_x),
                "length": float(segmento.longitud) if segmento.longitud else 0,
                "sample_count": segmento.cantidad_muestras,
                "last_update": segmento.ultima_fecha_muestra
            }
            result["segments"].append(segment_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error en viewport export: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/streaming")
async def export_segments_streaming(
    chunk_size: int = Query(50, le=100, description="Tamaño de chunk"),
    total_only: bool = Query(False, description="Solo retornar total de segmentos"),
    db: Session = Depends(get_db)
):
    """
    Exporta segmentos en chunks para streaming
    Ideal para datasets grandes sin bloquear la UI
    """
    try:
        if total_only:
            total = db.query(Segmento).count()
            return {"total_segments": total, "chunk_size": chunk_size}
        
        def generate_chunks() -> Generator[str, None, None]:
            yield '{"chunks": ['
            
            offset = 0
            first_chunk = True
            
            while True:
                # Obtener chunk
                segmentos = db.query(Segmento).offset(offset).limit(chunk_size).all()
                
                if not segmentos:
                    break
                
                # Preparar chunk data
                chunk_data = {
                    "chunk_number": (offset // chunk_size) + 1,
                    "offset": offset,
                    "count": len(segmentos),
                    "segments": []
                }
                
                for segmento in segmentos:
                    chunk_data["segments"].append({
                        "id": segmento.id_segmento,
                        "name": segmento.nombre,
                        "type": segmento.tipo,
                        "coordinates": [
                            float(segmento.nodo_inicial_x), float(segmento.nodo_inicial_y),
                            float(segmento.nodo_final_x), float(segmento.nodo_final_y)
                        ],
                        "length": float(segmento.longitud) if segmento.longitud else 0
                    })
                
                # Enviar chunk
                if not first_chunk:
                    yield ","
                else:
                    first_chunk = False
                
                yield json.dumps(chunk_data)
                
                offset += chunk_size
                
                # Pequeña pausa para no saturar
                import time
                time.sleep(0.01)
            
            yield ']}'
        
        return StreamingResponse(
            generate_chunks(),
            media_type="application/json",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
        
    except Exception as e:
        logger.error(f"Error en streaming export: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/light")
async def export_segments_light(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, le=200),
    include_geometry: bool = Query(False, description="Incluir geometría detallada"),
    include_samples: bool = Query(False, description="Incluir muestras"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo"),
    db: Session = Depends(get_db)
):
    """
    Exportación ligera optimizada para rendimiento
    Solo datos esenciales, geometría y muestras opcionales
    """
    try:
        # Query base optimizada
        query = db.query(Segmento)
        
        if tipo:
            query = query.filter(Segmento.tipo == tipo)
        
        # Paginación
        total_items = query.count()
        offset = (page - 1) * page_size
        segmentos = query.offset(offset).limit(page_size).all()
        
        result = {
            "metadata": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": (total_items + page_size - 1) // page_size,
                "include_geometry": include_geometry,
                "include_samples": include_samples
            },
            "segments": []
        }
        
        for segmento in segmentos:
            segment_data = {
                "id": segmento.id_segmento,
                "original_id": segmento.id_original,
                "name": segmento.nombre,
                "type": segmento.tipo,
                "length": float(segmento.longitud) if segmento.longitud else 0,
                "bounds": {
                    "start": [float(segmento.nodo_inicial_x), float(segmento.nodo_inicial_y)],
                    "end": [float(segmento.nodo_final_x), float(segmento.nodo_final_y)]
                },
                "sample_count": segmento.cantidad_muestras,
                "last_update": segmento.ultima_fecha_muestra
            }
            
            # Geometría opcional (más pesada)
            if include_geometry:
                geometrias = db.query(Geometria).filter(
                    Geometria.id_segmento_seleccionado == segmento.id_segmento
                ).order_by(Geometria.orden).all()
                
                segment_data["geometry"] = [
                    [float(g.coordenada_x), float(g.coordenada_y), g.orden]
                    for g in geometrias
                ]
            
            # Muestras opcionales (mucho más pesadas)
            if include_samples:
                muestras = db.query(Muestra).filter(
                    Muestra.id_segmento_seleccionado == segmento.id_segmento
                ).order_by(Muestra.fecha_muestra).limit(5).all()  # Solo últimas 5
                
                segment_data["recent_samples"] = [
                    {
                        "date": m.fecha_muestra,
                        "device": m.tipo_dispositivo,
                        "device_id": m.identificador_dispositivo
                    }
                    for m in muestras
                ]
            
            result["segments"].append(segment_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error en light export: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bulk/{segment_ids}")
async def export_segments_bulk(
    segment_ids: str,  # "1,2,3,4,5"
    include_full_data: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Exporta múltiples segmentos específicos por sus IDs
    Útil para cargar detalles de segmentos seleccionados
    """
    try:
        # Parsear IDs
        try:
            ids = [int(id_str.strip()) for id_str in segment_ids.split(',') if id_str.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="IDs inválidos")
        
        if len(ids) > 50:
            raise HTTPException(status_code=400, detail="Máximo 50 segmentos por request")
        
        # Query optimizada con IN
        segmentos = db.query(Segmento).filter(Segmento.id_segmento.in_(ids)).all()
        
        if not segmentos:
            return {"segments": [], "found_count": 0}
        
        result = {
            "requested_ids": ids,
            "found_count": len(segmentos),
            "segments": []
        }
        
        for segmento in segmentos:
            if include_full_data:
                # Datos completos (usar extractor existente)
                from app.services.data.extractor import RecWayDataExtractor
                extractor = RecWayDataExtractor(db)
                segment_data = extractor.convert_segmento_to_original_format(segmento)
            else:
                # Datos básicos
                segment_data = {
                    "id": segmento.id_segmento,
                    "name": segmento.nombre,
                    "type": segmento.tipo,
                    "length": float(segmento.longitud) if segmento.longitud else 0
                }
            
            result["segments"].append(segment_data)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en bulk export: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-stats")
async def get_performance_stats(db: Session = Depends(get_db)):
    """
    Estadísticas de rendimiento del sistema
    """
    try:
        stats = {
            "database": {
                "total_segments": db.query(Segmento).count(),
                "total_geometries": db.query(Geometria).count(),
                "total_samples": db.query(Muestra).count(),
            },
            "performance_tips": {
                "viewport_loading": "Use /viewport para cargas rápidas del mapa",
                "streaming": "Use /streaming para datasets grandes (>1000 segmentos)",
                "light_mode": "Use /light sin geometría para listados rápidos",
                "bulk_loading": "Use /bulk para detalles de segmentos específicos"
            },
            "recommended_limits": {
                "viewport_max": 200,
                "streaming_chunk": 50,
                "light_page_size": 100,
                "bulk_max_ids": 50
            }
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error en performance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
