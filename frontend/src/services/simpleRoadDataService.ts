// Versión simplificada del servicio de datos
import { buildApiUrl, apiLog } from '../config/api';

export interface SimpleRoadSegment {
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
}

export class SimpleRoadDataService {
  
  async loadAllRoadData(): Promise<SimpleRoadSegment[]> {
    try {
      const url = buildApiUrl('/api/export/all-data');
      apiLog('🔄 Cargando datos desde API', { url });
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }
      
      const result = await response.json();
      const roadSegments = result.segmentos || [];
      
      console.log(`✅ Cargados ${roadSegments.length} segmentos desde API`);
      
      // Transformar formato API al formato esperado por el frontend
      return roadSegments.map((segment: any) => this.transformSegment(segment));
      
    } catch (error) {
      console.error('❌ Error cargando desde API:', error);
      console.log('🔄 Fallback a archivo local...');
      return this.loadFromLocalFile();
    }
  }
  
  private transformSegment(apiSegment: any): SimpleRoadSegment {
    // Calcular promedios de índices de las muestras
    let avgIRIModificado = 0;
    let avgNotaGeneral = 0;
    
    if (apiSegment.muestras && apiSegment.muestras.length > 0) {
      const iriModValues = apiSegment.muestras
        .map((muestra: any) => muestra.indices?.iri_modificado || 0)
        .filter((iri: number) => iri > 0);
      
      const notaGeneralValues = apiSegment.muestras
        .map((muestra: any) => muestra.indices?.nota_general || 0)
        .filter((nota: number) => nota > 0);
      
      if (iriModValues.length > 0) {
        avgIRIModificado = iriModValues.reduce((sum: number, val: number) => sum + val, 0) / iriModValues.length;
      }
      
      if (notaGeneralValues.length > 0) {
        avgNotaGeneral = notaGeneralValues.reduce((sum: number, val: number) => sum + val, 0) / notaGeneralValues.length;
      }
    }
    
    // Extraer huecos de todas las muestras
    const allHuecos: any[] = [];
    if (apiSegment.muestras) {
      for (const muestra of apiSegment.muestras) {
        if (muestra.huecos) {
          allHuecos.push(...muestra.huecos);
        }
      }
    }
    
    return {
      numero: apiSegment.numero || 0,
      id: apiSegment.id,
      nombre: apiSegment.nombre || '',
      longitud: apiSegment.longitud || 0,
      tipo: apiSegment.tipo || '',
      latitud_origen: apiSegment.latitud_origen || 0,
      latitud_destino: apiSegment.latitud_destino || 0,
      longitud_origen: apiSegment.longitud_origen || 0,
      longitud_destino: apiSegment.longitud_destino || 0,
      geometria: apiSegment.geometria || [],
      fecha: apiSegment.fecha || '',
      IQR: avgNotaGeneral, // IQR = nota_general de la BD
      iri: avgIRIModificado, // IRI = iri_modificado de la BD
      IRI_modificado: avgIRIModificado,
      az: 0, // Valores por defecto
      ax: 0,
      wx: 0,
      huecos: allHuecos
    };
  }
  
  private async loadFromLocalFile(): Promise<SimpleRoadSegment[]> {
    try {
      const response = await import('../data/roadData.json');
      const data = response.default as SimpleRoadSegment[];
      console.log(`📁 Fallback: Cargados ${data.length} segmentos desde archivo local`);
      return data;
    } catch (error) {
      console.error('❌ Error cargando desde archivo local:', error);
      return [];
    }
  }
}

export const simpleRoadDataService = new SimpleRoadDataService();
