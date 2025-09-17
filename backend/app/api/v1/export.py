from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.models.recway import (
    Segmento, Geometria, Muestra, IndicesSegmento, 
    HuecoSegmento, IndicesMuestra, HuecoMuestra
)
from typing import Optional, List, Dict, Any
import logging
import json
import gzip
import io
from datetime import datetime

router = APIRouter(prefix="/api/export")
logger = logging.getLogger(__name__)

def _safe_format_date_static(date_value) -> Optional[str]:
    """Función estática para formatear fechas de forma segura"""
    if not date_value:
        return None
    
    try:
        if isinstance(date_value, str):
            return date_value
        elif hasattr(date_value, 'isoformat'):
            return date_value.isoformat()
        else:
            return str(date_value)
    except Exception as e:
        logger.warning(f"Error formateando fecha {date_value}: {e}")
        return None

class RecWayDataExtractor:
    """Extractor de datos optimizado para formato JSON original"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def convert_segmento_to_original_format(self, segmento: Segmento) -> Dict[str, Any]:
        """
        Convierte un segmento de BD al formato JSON original exacto
        """
        try:
            # Obtener geometrías ordenadas
            geometrias = self.db.query(Geometria).filter(
                Geometria.id_segmento_seleccionado == segmento.id_segmento
            ).order_by(Geometria.orden).all()
            
            # Obtener muestras ordenadas por fecha
            muestras = self.db.query(Muestra).filter(
                Muestra.id_segmento_seleccionado == segmento.id_segmento
            ).order_by(Muestra.fecha_muestra).all()
            
            # Estructura base del segmento en formato original
            segmento_json = {
                "numero": 0,  # Secuencial, se asignará después
                "id": int(segmento.id_original) if segmento.id_original and segmento.id_original.isdigit() else 0,
                "nombre": segmento.nombre or "",
                "longitud": float(segmento.longitud) if segmento.longitud else 0.0,
                "tipo": segmento.tipo or "",
                "latitud_origen": float(segmento.nodo_inicial_y) if segmento.nodo_inicial_y else 0.0,
                "latitud_destino": float(segmento.nodo_final_y) if segmento.nodo_final_y else 0.0,
                "longitud_origen": float(segmento.nodo_inicial_x) if segmento.nodo_inicial_x else 0.0,
                "longitud_destino": float(segmento.nodo_final_x) if segmento.nodo_final_x else 0.0,
                "geometria": [],
                "fecha": self._safe_format_date(segmento.ultima_fecha_muestra),
                "muestras": []
            }
            
            # Agregar geometrías
            for geom in geometrias:
                segmento_json["geometria"].append({
                    "orden": geom.orden,
                    "longitud": float(geom.coordenada_x),
                    "latitud": float(geom.coordenada_y)
                })
            
            # Procesar muestras
            for muestra in muestras:
                muestra_json = {
                    "fecha": self._safe_format_date(muestra.fecha_muestra),
                    "tipo_dispositivo": muestra.tipo_dispositivo or "",
                    "identificador_dispositivo": muestra.identificador_dispositivo or "",
                    "indices": {},
                    "huecos": []
                }
                
                # Obtener índices de muestra
                indices_muestra = self.db.query(IndicesMuestra).filter(
                    IndicesMuestra.id_muestra == muestra.id_muestra
                ).first()
                
                if indices_muestra:
                    muestra_json["indices"] = {
                        "iri": float(indices_muestra.iri_estandar) if indices_muestra.iri_estandar else 0.0,
                        "iri_modificado": float(indices_muestra.iri_modificado) if indices_muestra.iri_modificado else 0.0,
                        "nota_general": float(indices_muestra.nota_general) if indices_muestra.nota_general else 0.0
                    }
                
                # Obtener huecos de muestra
                huecos_muestra = self.db.query(HuecoMuestra).filter(
                    HuecoMuestra.id_muestra_seleccionada == muestra.id_muestra
                ).all()
                
                for hueco in huecos_muestra:
                    muestra_json["huecos"].append({
                        "latitud": float(hueco.latitud) if hueco.latitud else 0.0,
                        "longitud": float(hueco.longitud) if hueco.longitud else 0.0,
                        "magnitud": float(hueco.magnitud) if hueco.magnitud else 0.0,
                        "velocidad": float(hueco.velocidad) if hueco.velocidad else 0.0
                    })
                
                segmento_json["muestras"].append(muestra_json)
            
            return segmento_json
            
        except Exception as e:
            logger.error(f"Error convirtiendo segmento {segmento.id_segmento}: {e}")
            raise
    
    def _safe_format_date(self, date_value) -> Optional[str]:
        """Formatea fechas de forma segura"""
        if not date_value:
            return None
        
        try:
            if isinstance(date_value, str):
                return date_value
            elif hasattr(date_value, 'isoformat'):
                return date_value.isoformat()
            else:
                return str(date_value)
        except Exception as e:
            logger.warning(f"Error formateando fecha {date_value}: {e}")
            return None

# Endpoints principales de exportación

@router.get("/all-data")
async def export_all_data(
    format_compressed: bool = Query(False, description="Comprimir respuesta con gzip"),
    db: Session = Depends(get_db)
):
    """
    Exporta TODOS los datos en formato JSON original
    """
    try:
        extractor = RecWayDataExtractor(db)
        
        # Obtener todos los segmentos
        segmentos = db.query(Segmento).order_by(Segmento.id_segmento).all()
        
        # Estructura final
        result = {
            "metadata": {
                "total_segmentos": len(segmentos),
                "fecha_exportacion": datetime.now().isoformat(),
                "version": "1.0"
            },
            "segmentos": []
        }
        
        # Convertir cada segmento
        for i, segmento in enumerate(segmentos):
            try:
                segmento_json = extractor.convert_segmento_to_original_format(segmento)
                segmento_json["numero"] = i + 1  # Asignar número secuencial
                result["segmentos"].append(segmento_json)
            except Exception as e:
                logger.error(f"Error procesando segmento {segmento.id_segmento}: {e}")
                continue
        
        # Comprimir si se solicita
        if format_compressed:
            json_data = json.dumps(result, ensure_ascii=False, separators=(',', ':'))
            
            # Crear buffer comprimido
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
                gz_file.write(json_data.encode('utf-8'))
            
            buffer.seek(0)
            
            return StreamingResponse(
                io.BytesIO(buffer.read()),
                media_type="application/gzip",
                headers={
                    "Content-Disposition": "attachment; filename=recway_data_complete.json.gz",
                    "Content-Encoding": "gzip"
                }
            )
        
        return JSONResponse(
            content=result,
            headers={
                "Content-Disposition": "attachment; filename=recway_data_complete.json"
            }
        )
        
    except Exception as e:
        logger.error(f"Error en export_all_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/paginated")
async def export_paginated_data(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de segmento"),
    db: Session = Depends(get_db)
):
    """
    Exporta datos de forma paginada
    """
    try:
        extractor = RecWayDataExtractor(db)
        
        # Query base
        query = db.query(Segmento)
        
        # Filtro por tipo si se especifica
        if tipo:
            query = query.filter(Segmento.tipo == tipo)
        
        # Contar total
        total_items = query.count()
        total_pages = (total_items + page_size - 1) // page_size
        
        # Aplicar paginación
        offset = (page - 1) * page_size
        segmentos = query.order_by(Segmento.id_segmento).offset(offset).limit(page_size).all()
        
        # Estructura de respuesta paginada
        result = {
            "metadata": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "tipo_filtro": tipo
            },
            "segmentos": []
        }
        
        # Convertir segmentos
        for i, segmento in enumerate(segmentos):
            try:
                segmento_json = extractor.convert_segmento_to_original_format(segmento)
                segmento_json["numero"] = offset + i + 1
                result["segmentos"].append(segmento_json)
            except Exception as e:
                logger.error(f"Error procesando segmento {segmento.id_segmento}: {e}")
                continue
        
        return result
        
    except Exception as e:
        logger.error(f"Error en export_paginated_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def export_statistics(db: Session = Depends(get_db)):
    """
    Estadísticas completas de la base de datos
    """
    try:
        stats = {
            "resumen": {
                "total_segmentos": db.query(Segmento).count(),
                "total_geometrias": db.query(Geometria).count(),
                "total_muestras": db.query(Muestra).count(),
                "total_indices_segmento": db.query(IndicesSegmento).count(),
                "total_huecos_segmento": db.query(HuecoSegmento).count(),
                "total_indices_muestra": db.query(IndicesMuestra).count(),
                "total_huecos_muestra": db.query(HuecoMuestra).count()
            },
            "por_tipo": {},
            "fechas": {},
            "dispositivos": {}
        }
        
        # Estadísticas por tipo
        tipos = db.query(Segmento.tipo, func.count(Segmento.id_segmento)).group_by(Segmento.tipo).all()
        for tipo, count in tipos:
            stats["por_tipo"][tipo or "sin_tipo"] = count
        
        # Rango de fechas
        fecha_min = db.query(func.min(Muestra.fecha_muestra)).scalar()
        fecha_max = db.query(func.max(Muestra.fecha_muestra)).scalar()
        
        stats["fechas"] = {
            "fecha_minima": _safe_format_date_static(fecha_min),
            "fecha_maxima": _safe_format_date_static(fecha_max)
        }
        
        # Dispositivos únicos
        dispositivos = db.query(
            Muestra.tipo_dispositivo,
            func.count(func.distinct(Muestra.identificador_dispositivo))
        ).group_by(Muestra.tipo_dispositivo).all()
        
        for tipo_disp, count in dispositivos:
            stats["dispositivos"][tipo_disp or "desconocido"] = count
        
        return stats
        
    except Exception as e:
        logger.error(f"Error en export_statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-type/{tipo}")
async def export_by_type(
    tipo: str,
    format_compressed: bool = Query(False, description="Comprimir respuesta"),
    db: Session = Depends(get_db)
):
    """
    Exporta todos los segmentos de un tipo específico
    """
    try:
        extractor = RecWayDataExtractor(db)
        
        # Obtener segmentos del tipo especificado
        segmentos = db.query(Segmento).filter(
            Segmento.tipo == tipo
        ).order_by(Segmento.id_segmento).all()
        
        if not segmentos:
            raise HTTPException(status_code=404, detail=f"No se encontraron segmentos del tipo '{tipo}'")
        
        # Estructura de respuesta
        result = {
            "metadata": {
                "tipo": tipo,
                "total_segmentos": len(segmentos),
                "fecha_exportacion": datetime.now().isoformat()
            },
            "segmentos": []
        }
        
        # Convertir segmentos
        for i, segmento in enumerate(segmentos):
            try:
                segmento_json = extractor.convert_segmento_to_original_format(segmento)
                segmento_json["numero"] = i + 1
                result["segmentos"].append(segmento_json)
            except Exception as e:
                logger.error(f"Error procesando segmento {segmento.id_segmento}: {e}")
                continue
        
        # Respuesta comprimida o normal
        if format_compressed:
            json_data = json.dumps(result, ensure_ascii=False, separators=(',', ':'))
            
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
                gz_file.write(json_data.encode('utf-8'))
            
            buffer.seek(0)
            
            return StreamingResponse(
                io.BytesIO(buffer.read()),
                media_type="application/gzip",
                headers={
                    "Content-Disposition": f"attachment; filename=recway_data_{tipo}.json.gz",
                    "Content-Encoding": "gzip"
                }
            )
        
        return JSONResponse(
            content=result,
            headers={
                "Content-Disposition": f"attachment; filename=recway_data_{tipo}.json"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en export_by_type: {e}")
        raise HTTPException(status_code=500, detail=str(e))
