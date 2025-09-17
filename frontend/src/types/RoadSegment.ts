// Tipos para el sistema de datos de carreteras
export interface RoadSegment {
  numero: number;
  id: number;
  nombre: string | string[];
  longitud: number;
  tipo: string;
  latitud_origen: number;
  latitud_destino: number;
  longitud_origen: number;
  longitud_destino: number;
  geometria: Array<{
    orden: number;
    longitud: number;
    latitud: number;
  }>;
  fecha: string;
  IQR: number;
  iri: number;
  IRI_modificado: number;
  az: number;
  ax: number;
  wx: number;
  huecos: Array<{
    latitud: number;
    longitud: number;
    magnitud: number;
    velocidad: number;
  }>;
  // Campos adicionales para compatibilidad
  qualityScore?: number;
  riskLevel?: 'low' | 'medium' | 'high' | 'critical';
  muestras?: Array<{
    fecha: string;
    tipo_dispositivo: string;
    identificador_dispositivo: string;
    indices: {
      iri: number;
      iri_modificado: number;
      nota_general: number;
    };
    huecos: Array<{
      latitud: number;
      longitud: number;
      magnitud: number;
      velocidad: number;
    }>;
  }>;
}

export interface ApiRoadData {
  metadata: {
    total_segmentos: number;
    fecha_exportacion: string;
    version: string;
  };
  segmentos: Array<{
    numero: number;
    id: number;
    nombre: string;
    longitud: number;
    tipo: string;
    latitud_origen: number;
    latitud_destino: number;
    longitud_origen: number;
    longitud_destino: number;
    geometria: Array<{
      orden: number;
      longitud: number;
      latitud: number;
    }>;
    fecha: string;
    muestras: Array<{
      fecha: string;
      tipo_dispositivo: string;
      identificador_dispositivo: string;
      indices: {
        iri: number;
        iri_modificado: number;
        nota_general: number;
      };
      huecos: Array<{
        latitud: number;
        longitud: number;
        magnitud: number;
        velocidad: number;
      }>;
    }>;
  }>;
}

export interface PaginatedApiResponse {
  metadata: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
    tipo_filtro?: string;
  };
  segmentos: ApiRoadData['segmentos'];
}

export interface ApiStatistics {
  resumen: {
    total_segmentos: number;
    total_geometrias: number;
    total_muestras: number;
    total_indices_segmento: number;
    total_huecos_segmento: number;
    total_indices_muestra: number;
    total_huecos_muestra: number;
  };
  por_tipo: Record<string, number>;
  fechas: {
    fecha_minima: string;
    fecha_maxima: string;
  };
  dispositivos: Record<string, number>;
}
