import type { RoadSegment } from '../types/RoadSegment';
import { buildApiUrl } from '../config/api';

/**
 * Servicio optimizado para manejar miles de segmentos eficientemente
 */

export class OptimizedRoadDataService {
  private cache = new Map<string, any>();
  private loadingPromises = new Map<string, Promise<any>>();
  
  /**
   * Carga datos con paginación virtual para grandes datasets
   */
  async loadRoadDataWithVirtualPagination(
    viewport: { minLat: number; maxLat: number; minLng: number; maxLng: number },
    pageSize: number = 100
  ): Promise<RoadSegment[]> {
    const cacheKey = `viewport_${JSON.stringify(viewport)}_${pageSize}`;
    
    if (this.cache.has(cacheKey)) {
      console.log('📋 Datos cargados desde caché');
      return this.cache.get(cacheKey);
    }
    
    if (this.loadingPromises.has(cacheKey)) {
      console.log('⏳ Esperando carga en progreso...');
      return this.loadingPromises.get(cacheKey);
    }
    
    const loadPromise = this.performViewportLoad(viewport, pageSize);
    this.loadingPromises.set(cacheKey, loadPromise);
    
    try {
      const result = await loadPromise;
      this.cache.set(cacheKey, result);
      return result;
    } finally {
      this.loadingPromises.delete(cacheKey);
    }
  }
  
  private async performViewportLoad(
    _viewport: { minLat: number; maxLat: number; minLng: number; maxLng: number },
    pageSize: number
  ): Promise<RoadSegment[]> {
    // TODO: Implementar filtro por viewport en el backend
    // Por ahora, usar paginación estándar
    return this.loadPaginatedData(1, pageSize);
  }
  
  /**
   * Carga con streaming para datasets grandes
   */
  async loadRoadDataWithStreaming(
    onProgress?: (loaded: number, total: number) => void,
    onChunk?: (chunk: RoadSegment[]) => void
  ): Promise<RoadSegment[]> {
    try {
      // 1. Obtener estadísticas para saber el total
      const stats = await this.getStatistics();
      const totalSegments = stats.resumen.total_segmentos;
      
      console.log(`🚀 Iniciando carga streaming de ${totalSegments} segmentos`);
      
      const chunkSize = 50; // Cargar de 50 en 50
      const totalPages = Math.ceil(totalSegments / chunkSize);
      let allSegments: RoadSegment[] = [];
      
      // 2. Cargar por chunks
      for (let page = 1; page <= totalPages; page++) {
        const url = buildApiUrl(`/api/export/paginated?page=${page}&page_size=${chunkSize}`);
        const response = await fetch(url);
        
        if (!response.ok) {
          throw new Error(`Error en página ${page}: ${response.status}`);
        }
        
        const result = await response.json();
        const chunkSegments = result.segmentos.map(this.transformApiSegment);
        
        allSegments = allSegments.concat(chunkSegments);
        
        // Notificar progreso
        const loaded = page * chunkSize;
        onProgress?.(Math.min(loaded, totalSegments), totalSegments);
        onChunk?.(chunkSegments);
        
        console.log(`📄 Cargada página ${page}/${totalPages} (${chunkSegments.length} segmentos)`);
        
        // Pequeña pausa para no bloquear UI
        await this.delay(10);
      }
      
      console.log(`✅ Streaming completado: ${allSegments.length} segmentos`);
      return allSegments;
      
    } catch (error) {
      console.error('❌ Error en streaming:', error);
      throw error;
    }
  }
  
  /**
   * Carga lazy por demanda según viewport del mapa
   */
  async loadSegmentsInViewport(
    bounds: { north: number; south: number; east: number; west: number },
    zoom: number
  ): Promise<RoadSegment[]> {
    // Determinar densidad según zoom
    const maxSegments = zoom > 10 ? 200 : 50;
    
    // Por ahora, cargar muestra representativa
    const url = buildApiUrl(`/api/export/paginated?page=1&page_size=${maxSegments}`);
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Error cargando viewport: ${response.status}`);
    }
    
    const result = await response.json();
    
    // Filtrar por bounds (temporal - idealmente esto se hace en backend)
    const segmentsInBounds = result.segmentos
      .map(this.transformApiSegment)
      .filter((segment: RoadSegment) => this.isSegmentInBounds(segment, bounds));
    
    console.log(`🗺️ Cargados ${segmentsInBounds.length} segmentos en viewport`);
    return segmentsInBounds;
  }
  
  /**
   * Carga inteligente con caché y invalidación
   */
  async loadWithSmartCache(
    key: string,
    loader: () => Promise<any>,
    ttlMs: number = 5 * 60 * 1000 // 5 minutos
  ): Promise<any> {
    const cached = this.cache.get(key);
    
    if (cached && (Date.now() - cached.timestamp) < ttlMs) {
      console.log(`📋 Cache hit para ${key}`);
      return cached.data;
    }
    
    console.log(`🔄 Cache miss para ${key}, cargando...`);
    const data = await loader();
    
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
    
    return data;
  }
  
  /**
   * Obtiene estadísticas del dataset
   */
  async getStatistics() {
    return this.loadWithSmartCache('statistics', async () => {
      const url = buildApiUrl('/api/export/statistics');
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Error stats: ${response.status}`);
      return response.json();
    });
  }
  
  /**
   * Carga paginada estándar
   */
  async loadPaginatedData(page: number, pageSize: number): Promise<RoadSegment[]> {
    const url = buildApiUrl(`/api/export/paginated?page=${page}&page_size=${pageSize}`);
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Error paginación: ${response.status}`);
    }
    
    const result = await response.json();
    return result.segmentos.map(this.transformApiSegment);
  }
  
  // Utilidades
  private transformApiSegment = (apiSegment: any): RoadSegment => {
    return {
      numero: apiSegment.numero || 0,
      id: Number(apiSegment.id) || 0,
      nombre: apiSegment.nombre || '',
      longitud: apiSegment.longitud || 0,
      tipo: apiSegment.tipo || '',
      latitud_origen: apiSegment.latitud_origen || 0,
      latitud_destino: apiSegment.latitud_destino || 0,
      longitud_origen: apiSegment.longitud_origen || 0,
      longitud_destino: apiSegment.longitud_destino || 0,
      geometria: apiSegment.geometria?.map((point: any) => ({
        orden: point.orden || 0,
        longitud: point.longitud || 0,
        latitud: point.latitud || 0
      })) || [],
      fecha: apiSegment.fecha || '',
      IQR: 0, // Se calculará si es necesario
      iri: this.calculateAverageIRI(apiSegment),
      IRI_modificado: 0,
      az: 0,
      ax: 0,
      wx: 0,
      huecos: this.extractHoles(apiSegment),
      qualityScore: this.calculateQualityScore(apiSegment),
      muestras: apiSegment.muestras?.map((muestra: any) => ({
        fecha: muestra.fecha || '',
        tipo_dispositivo: muestra.tipo_dispositivo || '',
        identificador_dispositivo: muestra.identificador_dispositivo || '',
        indices: {
          iri: muestra.indices?.iri || 0,
          iri_modificado: muestra.indices?.iri_modificado || 0,
          nota_general: muestra.indices?.nota_general || 0
        },
        huecos: muestra.huecos?.map((hueco: any) => ({
          latitud: hueco.latitud || 0,
          longitud: hueco.longitud || 0,
          magnitud: hueco.magnitud || 0,
          velocidad: hueco.velocidad || 0
        })) || []
      })) || []
    };
  };
  
  private calculateAverageIRI(segment: any): number {
    const muestras = segment.muestras || [];
    if (muestras.length === 0) return 0;
    
    const iriSum = muestras.reduce((sum: number, muestra: any) => {
      const iri = muestra.indices?.iri || 0;
      return sum + iri;
    }, 0);
    
    return iriSum / muestras.length;
  }
  
  private extractHoles(segment: any): Array<{latitud: number; longitud: number; magnitud: number; velocidad: number}> {
    const allHoles: any[] = [];
    const muestras = segment.muestras || [];
    
    muestras.forEach((muestra: any) => {
      if (muestra.huecos) {
        allHoles.push(...muestra.huecos);
      }
    });
    
    return allHoles.map((hueco: any) => ({
      latitud: hueco.latitud || 0,
      longitud: hueco.longitud || 0,
      magnitud: hueco.magnitud || 0,
      velocidad: hueco.velocidad || 0
    }));
  }
  
  private calculateQualityScore(segment: any): number {
    // Calcular score promedio basado en IRI
    const muestras = segment.muestras || [];
    if (muestras.length === 0) return 0;
    
    const iriSum = muestras.reduce((sum: number, muestra: any) => {
      const iri = muestra.indices?.iri || 0;
      return sum + iri;
    }, 0);
    
    const avgIri = iriSum / muestras.length;
    
    // Convertir IRI a score (0-10, donde 10 es mejor)
    return Math.max(0, Math.min(10, 10 - avgIri));
  }
  
  private isSegmentInBounds(segment: RoadSegment, bounds: any): boolean {
    const lat = segment.latitud_origen;
    const lng = segment.longitud_origen;
    
    return lat >= bounds.south && lat <= bounds.north && 
           lng >= bounds.west && lng <= bounds.east;
  }
  
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  // Limpiar caché cuando sea necesario
  clearCache(): void {
    this.cache.clear();
    console.log('🧹 Caché limpiado');
  }
}

// Singleton
export const optimizedRoadDataService = new OptimizedRoadDataService();
