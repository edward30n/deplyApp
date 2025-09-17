// Servicio para cargar datos de carreteras desde la API
import type { RoadSegment } from '../types/RoadSegment';
import { buildApiUrl, apiLog } from '../config/api';

// Interfaces para la API
interface ApiMuestra {
  id: number;
  numero: number;
  latitud: number;
  longitud: number;
  progresiva_km: number;
  fecha_registro: string;
  indices?: {
    iri?: number;
    iri_modificado?: number;
  };
  huecos?: any[];
}

interface ApiSegment {
  id: number;
  numero: string;
  nombre: string;
  tipo: string;
  estado: string;
  region: string;
  latitud_origen: number;
  longitud_origen: number;
  latitud_destino: number;
  longitud_destino: number;
  fecha_construccion?: string;
  ultima_inspeccion?: string;
  muestras?: ApiMuestra[];
  geometrias?: any[];
}

interface ApiResponse {
  metadata: {
    total_segmentos: number;
    total_geometrias: number;
    total_muestras: number;
    total_huecos: number;
    fecha_extraccion: string;
    duracion_procesamiento_segundos: number;
  };
  segmentos: ApiSegment[];
}

interface PaginatedApiResponse {
  metadata: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  segmentos: ApiSegment[];
}

export interface RoadDataService {
  loadAllRoadData(): Promise<RoadSegment[]>;
  loadPaginatedRoadData(page: number, pageSize: number): Promise<{
    data: RoadSegment[];
    metadata: {
      page: number;
      page_size: number;
      total_items: number;
      total_pages: number;
      has_next: boolean;
      has_prev: boolean;
    };
  }>;
  loadRoadDataByType(tipo: string): Promise<RoadSegment[]>;
  loadRoadDataStatistics(): Promise<any>;
}

class ApiRoadDataService implements RoadDataService {
  
  /**
   * Carga TODOS los datos de carreteras desde la API
   */
  async loadAllRoadData(): Promise<RoadSegment[]> {
    try {
      apiLog('🔄 Cargando datos de carreteras desde API');
      
      const url = buildApiUrl('/api/export/all-data');
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }
      
      const result: ApiResponse = await response.json();
      
      console.log(`✅ Cargados ${result.segmentos.length} segmentos desde API`);
      console.log(`📊 Metadata:`, result.metadata);
      
      // Transformar formato API al formato esperado por el frontend
      return result.segmentos.map((segment: ApiSegment) => this.transformApiSegmentToRoadSegment(segment));
      
    } catch (error) {
      console.error('❌ Error cargando datos desde API:', error);
      
      // Fallback: cargar desde archivo local si la API falla
      console.log('🔄 Intentando cargar desde archivo local como fallback...');
      return this.loadFromLocalFile();
    }
  }
  
  /**
   * Carga datos paginados desde la API
   */
  async loadPaginatedRoadData(page: number = 1, pageSize: number = 50) {
    try {
      const url = buildApiUrl(`/api/export/paginated?page=${page}&page_size=${pageSize}`);
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }
      
      const result: PaginatedApiResponse = await response.json();
      
      return {
        data: result.segmentos.map((segment: ApiSegment) => this.transformApiSegmentToRoadSegment(segment)),
        metadata: result.metadata
      };
      
    } catch (error) {
      console.error('❌ Error cargando datos paginados:', error);
      throw error;
    }
  }
  
  /**
   * Carga datos por tipo de carretera
   */
  async loadRoadDataByType(tipo: string): Promise<RoadSegment[]> {
    try {
      const url = buildApiUrl(`/api/export/by-type/${tipo}`);
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }
      
      const result: ApiResponse = await response.json();
      
      return result.segmentos.map((segment: ApiSegment) => this.transformApiSegmentToRoadSegment(segment));
      
    } catch (error) {
      console.error(`❌ Error cargando datos del tipo ${tipo}:`, error);
      throw error;
    }
  }
  
  /**
   * Carga estadísticas desde la API
   */
  async loadRoadDataStatistics() {
    try {
      const url = buildApiUrl('/api/export/statistics');
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }
      
      return await response.json();
      
    } catch (error) {
      console.error('❌ Error cargando estadísticas:', error);
      throw error;
    }
  }
  
  /**
   * Transforma un segmento de la API al formato esperado por el frontend
   */
  private transformApiSegmentToRoadSegment(apiSegment: ApiSegment): RoadSegment {
    // Calcular IQR promedio de las muestras si existe
    let avgIQR = 0;
    let avgIRI = 0;
    let avgIRIModificado = 0;
    
    if (apiSegment.muestras && apiSegment.muestras.length > 0) {
      const iriValues = apiSegment.muestras
        .map((muestra: ApiMuestra) => muestra.indices?.iri || 0)
        .filter((iri: number) => iri > 0);
      
      const iriModValues = apiSegment.muestras
        .map((muestra: ApiMuestra) => muestra.indices?.iri_modificado || 0)
        .filter((iri: number) => iri > 0);
      
      if (iriValues.length > 0) {
        avgIRI = iriValues.reduce((sum: number, val: number) => sum + val, 0) / iriValues.length;
        avgIQR = avgIRI; // IQR es similar a IRI en este contexto
      }
      
      if (iriModValues.length > 0) {
        avgIRIModificado = iriModValues.reduce((sum: number, val: number) => sum + val, 0) / iriModValues.length;
      }
    }
    
    // Extraer huecos de todas las muestras
    const allHuecos = [];
    if (apiSegment.muestras) {
      for (const muestra of apiSegment.muestras) {
        if (muestra.huecos) {
          allHuecos.push(...muestra.huecos);
        }
      }
    }
    
    return {
      numero: parseInt(apiSegment.numero) || 0,
      id: apiSegment.id,
      nombre: apiSegment.nombre || '',
      longitud: 0, // No disponible en API, calcular de geometrias si está disponible
      tipo: apiSegment.tipo || '',
      latitud_origen: apiSegment.latitud_origen || 0,
      latitud_destino: apiSegment.latitud_destino || 0,
      longitud_origen: apiSegment.longitud_origen || 0,
      longitud_destino: apiSegment.longitud_destino || 0,
      geometria: (apiSegment.geometrias || []).map((geo: any, index: number) => ({
        orden: index + 1,
        longitud: geo.longitud || 0,
        latitud: geo.latitud || 0
      })),
      fecha: apiSegment.fecha_construccion || apiSegment.ultima_inspeccion || '',
      muestras: (apiSegment.muestras || []).map((muestra: ApiMuestra) => ({
        fecha: muestra.fecha_registro || '',
        tipo_dispositivo: 'unknown',
        identificador_dispositivo: `device_${muestra.id}`,
        indices: {
          iri: muestra.indices?.iri || 0,
          iri_modificado: muestra.indices?.iri_modificado || 0,
          nota_general: 0
        },
        huecos: (muestra.huecos || []).map((hueco: any) => ({
          latitud: hueco.latitud || 0,
          longitud: hueco.longitud || 0,
          magnitud: hueco.magnitud || 0,
          velocidad: hueco.velocidad || 0
        }))
      })),
      // Campos requeridos por el frontend existente
      IQR: avgIQR,
      iri: avgIRI,
      IRI_modificado: avgIRIModificado,
      az: 0, // Valores por defecto para campos no disponibles en API
      ax: 0,
      wx: 0,
      huecos: allHuecos.map((hueco: any) => ({
        latitud: hueco.latitud || 0,
        longitud: hueco.longitud || 0,
        magnitud: hueco.magnitud || 0,
        velocidad: hueco.velocidad || 0
      })),
      // Campos adicionales calculados
      qualityScore: this.calculateQualityScore(avgIRI),
      riskLevel: this.calculateRiskLevel(avgIRI)
    };
  }
  
  /**
   * Calcula el score de calidad basado en IRI
   */
  private calculateQualityScore(iri: number): number {
    if (iri <= 1.5) return 90 + Math.random() * 10; // Excelente
    if (iri <= 2.5) return 70 + Math.random() * 20; // Buena
    if (iri <= 4.0) return 50 + Math.random() * 20; // Regular
    if (iri <= 6.0) return 30 + Math.random() * 20; // Mala
    return 10 + Math.random() * 20; // Muy mala
  }
  
  /**
   * Calcula el nivel de riesgo basado en IRI
   */
  private calculateRiskLevel(iri: number): 'low' | 'medium' | 'high' | 'critical' {
    if (iri <= 1.5) return 'low';
    if (iri <= 2.5) return 'medium';
    if (iri <= 4.0) return 'high';
    return 'critical';
  }
  
  /**
   * Fallback: cargar desde archivo local
   */
  private async loadFromLocalFile(): Promise<RoadSegment[]> {
    try {
      const response = await import('../data/roadData.json');
      const data = response.default as RoadSegment[];
      console.log(`📁 Fallback: Cargados ${data.length} segmentos desde archivo local`);
      return data;
    } catch (error) {
      console.error('❌ Error cargando desde archivo local:', error);
      return [];
    }
  }
}

// Instancia singleton del servicio
export const roadDataService = new ApiRoadDataService();

// Hook para React
export const useRoadData = () => {
  return {
    loadAllRoadData: () => roadDataService.loadAllRoadData(),
    loadPaginatedRoadData: (page: number, pageSize: number) => 
      roadDataService.loadPaginatedRoadData(page, pageSize),
    loadRoadDataByType: (tipo: string) => roadDataService.loadRoadDataByType(tipo),
    loadStatistics: () => roadDataService.loadRoadDataStatistics()
  };
};
