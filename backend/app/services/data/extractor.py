"""
Servicio de extracción de datos RecWay - Export eficiente
Convierte datos de BD al formato JSON original compatible
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, func, desc, asc
from datetime import datetime, timezone
import json
import asyncio
from fastapi.responses import StreamingResponse
import gzip
import io
import logging

from app.models.recway import (
    Segmento, Geometria, IndicesSegmento, HuecoSegmento,
    Muestra, IndicesMuestra, HuecoMuestra,
    FuenteDatosDispositivo, RegistroSensores
)
from app.schemas.recway import SegmentoFromJSON

logger = logging.getLogger(__name__)

class RecWayDataExtractor:
    """Servicio para extraer datos de la BD en formato JSON original"""

    def __init__(self, db: Session):
        self.db = db

    # =================== EXTRACCIÓN BÁSICA ===================

    def extract_segmento_to_json(self, segmento: Segmento) -> Dict[str, Any]:
        """
        Convierte un segmento de BD al formato JSON original
        
        Format compatible con:
        {
            "numero": 0,
            "id": 700925758603426692,
            "nombre": "Avenida Carrera 14",
            "longitud": 46.22384857764475,
            "tipo": "trunk",
            "latitud_origen": 4.6312372,
            "latitud_destino": 4.6316461,
            "longitud_origen": -74.06779505,
            "longitud_destino": -74.0677228,
            "geometria": [...],
            "fecha": "2024-07-22T11:52:15",
            "muestras": [...],
            "indices": {...},
            "huecos": [...]
        }
        """
        # Cargar relaciones necesarias
        geometrias = self.db.query(Geometria).filter(
            Geometria.id_segmento_seleccionado == segmento.id_segmento
        ).order_by(Geometria.orden).all()
        
        muestras = self.db.query(Muestra).filter(
            Muestra.id_segmento_seleccionado == segmento.id_segmento
        ).order_by(Muestra.fecha_muestra).all()
        
        indices = self.db.query(IndicesSegmento).filter(
            IndicesSegmento.id_segmento_seleccionado == segmento.id_segmento
        ).first()
        
        huecos = self.db.query(HuecoSegmento).filter(
            HuecoSegmento.id_segmento_seleccionado == segmento.id_segmento
        ).all()

        # Construir JSON en formato original con encoding seguro
        try:
            segmento_json = {
                "numero": 0,  # Mantener para compatibilidad
                "id": int(segmento.id_original) if segmento.id_original and segmento.id_original.isdigit() else hash(str(segmento.id_original or '')),
                "nombre": str(segmento.nombre or '').encode('utf-8', errors='ignore').decode('utf-8'),
                "longitud": float(segmento.longitud or 0),
                "tipo": str(segmento.tipo or '').encode('utf-8', errors='ignore').decode('utf-8'),
                "latitud_origen": float(segmento.nodo_inicial_y or 0),
                "latitud_destino": float(segmento.nodo_final_y or 0),
                "longitud_origen": float(segmento.nodo_inicial_x or 0),
                "longitud_destino": float(segmento.nodo_final_x or 0),
                "geometria": [
                    {
                        "orden": g.orden,
                        "longitud": float(g.coordenada_x),
                        "latitud": float(g.coordenada_y)
                    }
                    for g in geometrias
                ],
                "fecha": segmento.ultima_fecha_muestra if isinstance(segmento.ultima_fecha_muestra, str) else (
                    segmento.ultima_fecha_muestra.isoformat() if segmento.ultima_fecha_muestra else None
                ),
                "muestras": []
            }
        except Exception as e:
            logger.error(f"Error construyendo JSON base para segmento {segmento.id_segmento}: {e}")
            raise

        # Agregar muestras si existen
        for muestra in muestras:
            muestra_json = {
                "fecha": muestra.fecha_muestra,
                "tipo_dispositivo": muestra.tipo_dispositivo,
                "identificador_dispositivo": muestra.identificador_dispositivo,
                # Campos adicionales que se pueden agregar cuando estén disponibles
            }
            
            # Cargar índices de muestra
            indices_muestra = self.db.query(IndicesMuestra).filter(
                IndicesMuestra.id_muestra == muestra.id_muestra
            ).first()
            
            if indices_muestra:
                muestra_json["indices"] = {
                    "iri": float(indices_muestra.iri_estandar or 0),
                    "iri_modificado": float(indices_muestra.iri_modificado or 0),
                    "nota_general": float(indices_muestra.nota_general or 0)
                }
            
            # Cargar huecos de muestra
            huecos_muestra = self.db.query(HuecoMuestra).filter(
                HuecoMuestra.id_muestra_seleccionada == muestra.id_muestra
            ).all()
            
            muestra_json["huecos"] = [
                {
                    "latitud": float(h.latitud or 0),
                    "longitud": float(h.longitud or 0),
                    "magnitud": float(h.magnitud or 0),
                    "velocidad": float(h.velocidad or 0)
                }
                for h in huecos_muestra
            ]
            
            segmento_json["muestras"].append(muestra_json)

        # Agregar índices de segmento
        if indices:
            segmento_json["indices"] = {
                "iri_estandar": float(indices.iri_estandar or 0),
                "iri_modificado": float(indices.iri_modificado or 0),
                "nota_general": float(indices.nota_general or 0),
                "indice_primero": float(indices.indice_primero or 0),
                "indice_segundo": float(indices.indice_segundo or 0),
                "iri_tercero": float(indices.iri_tercero or 0) if indices.iri_tercero else 0
            }

        # Agregar huecos de segmento
        segmento_json["huecos"] = [
            {
                "latitud": float(h.latitud or 0),
                "longitud": float(h.longitud or 0),
                "magnitud": float(h.magnitud or 0),
                "velocidad": float(h.velocidad or 0),
                "ultima_fecha_muestra": h.ultima_fecha_muestra,
                "error_gps": float(h.error_gps or 0)
            }
            for h in huecos
        ]

        return segmento_json

    # =================== EXTRACCIÓN PAGINADA ===================

    def extract_segmentos_paginated(
        self, 
        page: int = 1, 
        page_size: int = 100,
        user_id: Optional[int] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Extrae segmentos de forma paginada
        """
        try:
            # Query base
            query = self.db.query(Segmento)
            
            # Filtros opcionales
            if user_id:
                query = query.filter(Segmento.created_by_user_id == user_id)
            
            # Comentar filtros de fecha temporalmente para debugging
            # if fecha_desde:
            #     query = query.filter(Segmento.ultima_fecha_muestra >= fecha_desde)
            # if fecha_hasta:
            #     query = query.filter(Segmento.ultima_fecha_muestra <= fecha_hasta)

            # Contar total
            total_items = query.count()
            total_pages = (total_items + page_size - 1) // page_size

            # Aplicar paginación
            offset = (page - 1) * page_size
            segmentos = query.order_by(Segmento.id_segmento).offset(offset).limit(page_size).all()

            # Convertir a JSON
            data = []
            for segmento in segmentos:
                try:
                    segmento_json = self.extract_segmento_to_json(segmento)
                    data.append(segmento_json)
                except Exception as e:
                    logger.error(f"Error extrayendo segmento {segmento.id_segmento}: {e}")
                    continue

            return {
                "data": data,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
        except Exception as e:
            logger.error(f"Error en extract_segmentos_paginated: {e}")
            raise

    # =================== EXTRACCIÓN STREAMING ===================

    async def stream_all_segmentos(
        self,
        user_id: Optional[int] = None,
        chunk_size: int = 50
    ) -> AsyncGenerator[str, None]:
        """
        Stream de todos los segmentos en formato JSON Lines
        Eficiente para grandes volúmenes de datos
        """
        # Query base
        query = self.db.query(Segmento.id_segmento)
        
        if user_id:
            query = query.filter(Segmento.created_by_user_id == user_id)
        
        # Obtener IDs en chunks
        offset = 0
        while True:
            segmento_ids = query.order_by(Segmento.id_segmento).offset(offset).limit(chunk_size).all()
            
            if not segmento_ids:
                break
                
            # Procesar chunk
            for (segmento_id,) in segmento_ids:
                segmento = self.db.query(Segmento).filter(
                    Segmento.id_segmento == segmento_id
                ).first()
                
                if segmento:
                    try:
                        segmento_json = self.extract_segmento_to_json(segmento)
                        # JSON Lines format: una línea por objeto
                        yield json.dumps(segmento_json, ensure_ascii=False) + "\n"
                    except Exception as e:
                        logger.error(f"Error streaming segmento {segmento_id}: {e}")
                        continue
                
                # Yield control para no bloquear
                await asyncio.sleep(0)
            
            offset += chunk_size

    # =================== EXTRACCIÓN CON FILTROS AVANZADOS ===================

    def extract_with_filters(
        self,
        tipo_segmento: Optional[str] = None,
        iri_min: Optional[float] = None,
        iri_max: Optional[float] = None,
        velocidad_min: Optional[float] = None,
        velocidad_max: Optional[float] = None,
        con_huecos: Optional[bool] = None,
        limite: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Extracción con filtros específicos para análisis
        """
        # Query con joins para filtros avanzados
        query = self.db.query(Segmento).join(
            IndicesSegmento, 
            Segmento.id_segmento == IndicesSegmento.id_segmento,
            isouter=True
        )
        
        # Aplicar filtros
        if tipo_segmento:
            query = query.filter(Segmento.tipo == tipo_segmento)
            
        if iri_min is not None:
            query = query.filter(IndicesSegmento.iri_promedio >= iri_min)
            
        if iri_max is not None:
            query = query.filter(IndicesSegmento.iri_promedio <= iri_max)
            
        if velocidad_min is not None:
            query = query.filter(IndicesSegmento.velocidad_promedio >= velocidad_min)
            
        if velocidad_max is not None:
            query = query.filter(IndicesSegmento.velocidad_promedio <= velocidad_max)
            
        if con_huecos is not None:
            if con_huecos:
                # Solo segmentos que tienen huecos
                query = query.join(HuecoSegmento)
            else:
                # Solo segmentos sin huecos
                query = query.outerjoin(HuecoSegmento).filter(HuecoSegmento.id_segmento.is_(None))

        # Limitar resultados
        segmentos = query.limit(limite).all()
        
        # Convertir a JSON
        return [self.extract_segmento_to_json(s) for s in segmentos]

    # =================== EXTRACCIÓN COMPRIMIDA ===================

    def extract_compressed(
        self,
        user_id: Optional[int] = None,
        formato: str = "json"
    ) -> bytes:
        """
        Extrae datos comprimidos con gzip
        Reduce significativamente el tamaño de transferencia
        """
        # Extraer datos
        if user_id:
            result = self.extract_segmentos_paginated(
                page=1, 
                page_size=10000,  # Chunk grande para compresión
                user_id=user_id
            )
            data = result["data"]
        else:
            # Todos los segmentos (usar con cuidado)
            query = self.db.query(Segmento).limit(5000)  # Límite de seguridad
            data = [self.extract_segmento_to_json(s) for s in query.all()]

        # Serializar según formato
        if formato == "json":
            content = json.dumps(data, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"Formato no soportado: {formato}")

        # Comprimir
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
            gz_file.write(content.encode('utf-8'))
        
        return buffer.getvalue()

    # =================== ESTADÍSTICAS DE EXTRACCIÓN ===================

    def get_extraction_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas para planificar extracciones
        """
        query = self.db.query(Segmento)
        
        if user_id:
            query = query.filter(Segmento.created_by_user_id == user_id)

        stats = {
            "total_segmentos": query.count(),
            "total_con_geometria": query.join(Geometria).distinct().count(),
            "total_con_indices": query.join(IndicesSegmento).count(),
            "total_con_huecos": query.join(HuecoSegmento).distinct().count(),
            "fecha_mas_antigua": query.filter(
                Segmento.ultima_fecha_muestra.is_not(None)
            ).order_by(asc(Segmento.ultima_fecha_muestra)).first(),
            "fecha_mas_reciente": query.filter(
                Segmento.ultima_fecha_muestra.is_not(None)
            ).order_by(desc(Segmento.ultima_fecha_muestra)).first(),
            "tipos_segmento": self.db.query(
                Segmento.tipo, 
                func.count(Segmento.id_segmento).label('cantidad')
            ).group_by(Segmento.tipo).all()
        }

        # Procesar fechas para JSON
        if stats["fecha_mas_antigua"] and hasattr(stats["fecha_mas_antigua"], 'ultima_fecha_muestra'):
            fecha = stats["fecha_mas_antigua"].ultima_fecha_muestra
            stats["fecha_mas_antigua"] = fecha if isinstance(fecha, str) else fecha.isoformat()
        else:
            stats["fecha_mas_antigua"] = None
            
        if stats["fecha_mas_reciente"] and hasattr(stats["fecha_mas_reciente"], 'ultima_fecha_muestra'):
            fecha = stats["fecha_mas_reciente"].ultima_fecha_muestra
            stats["fecha_mas_reciente"] = fecha if isinstance(fecha, str) else fecha.isoformat()
        else:
            stats["fecha_mas_reciente"] = None
            
        # Convertir tipos a dict con encoding seguro
        tipos_data = []
        try:
            for tipo, cantidad in stats["tipos_segmento"]:
                if tipo:  # Solo si tipo no es None
                    tipos_data.append((str(tipo), int(cantidad)))
        except Exception as e:
            logger.warning(f"Error procesando tipos de segmento: {e}")
            tipos_data = []
            
        stats["tipos_segmento"] = dict(tipos_data)

        return stats
