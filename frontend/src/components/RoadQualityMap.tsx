import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { simpleRoadDataService } from '../services/simpleRoadDataService';

interface RoadSegment {
  numero: number;
  id: number;
  nombre: string | string[]; // Puede ser string o array de strings
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

interface RoadQualityMapProps {
  height?: string;
  width?: string;
}

const RoadQualityMap: React.FC<RoadQualityMapProps> = ({ 
  height = "500px", 
  width = "100%" 
}) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);
  const holesLayerGroupRef = useRef<L.LayerGroup | null>(null);
  const currentTileLayerRef = useRef<L.TileLayer | null>(null); // Referencia para la capa de tiles actual
  const [roadData, setRoadData] = useState<RoadSegment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedSegment, setSelectedSegment] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);
  const [analysisMode, setAnalysisMode] = useState<'segments' | 'holes'>('segments'); // Nuevo estado para el modo de análisis
  const [holeVisualizationMode, setHoleVisualizationMode] = useState<'circles' | 'segments'>('circles'); // Modo de visualización de huecos
  const [mapLayer, setMapLayer] = useState<'osm' | 'satellite' | 'terrain' | 'roads' | 'transport' | 'dark' | 'light'>('osm'); // Tipo de capa de mapa
  const [isFullscreen, setIsFullscreen] = useState(false); // Estado para pantalla completa
  const [holeStats, setHoleStats] = useState({
    total: 0,
    minMagnitud: 0,
    maxMagnitud: 0,
    avgMagnitud: 0,
    minVelocidad: 0,
    maxVelocidad: 0
  });
  const [stats, setStats] = useState({
    total: 0,
    minIQR: 0,
    maxIQR: 0,
    avgIQR: 0
  });

  // Función para normalizar nombre (string o array)
  const getNombreSegmento = (nombre: string | string[]): string => {
    if (Array.isArray(nombre)) {
      return nombre.join(' / ');
    }
    return nombre;
  };

  // Función para obtener la configuración de las capas de mapa
  const getMapLayerConfig = (layerType: string) => {
    const configs = {
      osm: {
        url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attribution: '© OpenStreetMap contributors',
        name: 'OpenStreetMap',
        maxZoom: 19
      },
      satellite: {
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attribution: '© Esri, Maxar, Earthstar Geographics',
        name: 'Satélite',
        maxZoom: 18
      },
      terrain: {
        url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        attribution: '© OpenTopoMap (CC-BY-SA)',
        name: 'Topográfico',
        maxZoom: 17
      },
      roads: {
        url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attribution: '© OpenStreetMap contributors',
        name: 'Vías y Carreteras',
        maxZoom: 19,
        description: 'Mapa optimizado para visualizar vías y carreteras'
      },
      transport: {
        url: 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
        attribution: '© OpenStreetMap contributors, Tiles courtesy of Humanitarian OpenStreetMap Team',
        name: 'Transporte',
        maxZoom: 18,
        description: 'Mapa especializado en infraestructura de transporte'
      },
      dark: {
        url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        attribution: '© CARTO',
        name: 'Oscuro',
        maxZoom: 19
      },
      light: {
        url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        attribution: '© CARTO',
        name: 'Claro',
        maxZoom: 19
      }
    };
    return configs[layerType as keyof typeof configs] || configs.osm;
  };

  // Función para obtener color basado en magnitud del hueco
  const getHoleColorByMagnitude = (magnitude: number, minMag: number, maxMag: number): string => {
    // Normalizar la magnitud entre 0 y 1
    const normalized = maxMag > minMag ? (magnitude - minMag) / (maxMag - minMag) : 0;
    
    // Escala de color: Verde (magnitud baja) -> Amarillo -> Naranja -> Rojo (magnitud alta)
    if (normalized <= 0.25) {
      // Verde a amarillo-verde
      const intensity = normalized * 4;
      return `rgb(${Math.floor(100 * intensity)}, 255, ${Math.floor(100 * (1 - intensity))})`;
    } else if (normalized <= 0.5) {
      // Amarillo-verde a amarillo
      const intensity = (normalized - 0.25) * 4;
      return `rgb(${Math.floor(100 + 155 * intensity)}, 255, 0)`;
    } else if (normalized <= 0.75) {
      // Amarillo a naranja
      const intensity = (normalized - 0.5) * 4;
      return `rgb(255, ${Math.floor(255 - 100 * intensity)}, 0)`;
    } else {
      // Naranja a rojo
      const intensity = (normalized - 0.75) * 4;
      return `rgb(255, ${Math.floor(155 - 155 * intensity)}, 0)`;
    }
  };

  // Función para obtener el tamaño del marcador según la magnitud
  const getHoleSize = (magnitude: number, minMag: number, maxMag: number): number => {
    const normalized = maxMag > minMag ? (magnitude - minMag) / (maxMag - minMag) : 0;
    return 4 + (normalized * 12); // Tamaño entre 4 y 16 píxeles
  };

  // Función para obtener la severidad del hueco
  const getHoleSeverity = (magnitude: number): string => {
    if (magnitude < 1) return 'Muy Leve';
    if (magnitude < 2) return 'Leve';
    if (magnitude < 3) return 'Moderado';
    if (magnitude < 4) return 'Severo';
    return 'Muy Severo';
  };

  // Función para obtener color de segmento basado en huecos
  const getSegmentColorByHoles = (segment: RoadSegment): string => {
    const holes = segment.huecos || [];
    
    if (holes.length === 0) {
      // Sin huecos - verde claro
      return '#22c55e';
    }
    
    // Calcular densidad de huecos por kilómetro
    const holesDensity = holes.length / (segment.longitud / 1000);
    
    // Calcular severidad promedio
    const avgMagnitude = holes.reduce((sum, hole) => sum + hole.magnitud, 0) / holes.length;
    
    // Factores combinados: densidad + severidad
    const densityFactor = Math.min(holesDensity / 10, 1); // Normalizar densidad (máx 10 huecos/km)
    const severityFactor = Math.min(avgMagnitude / 5, 1); // Normalizar severidad (máx 5)
    
    // Combinar factores (70% severidad, 30% densidad)
    const combinedFactor = (severityFactor * 0.7) + (densityFactor * 0.3);
    
    // Escala de color basada en factor combinado
    if (combinedFactor <= 0.2) {
      // Verde claro - pocos huecos leves
      return '#84cc16';
    } else if (combinedFactor <= 0.4) {
      // Amarillo - huecos moderados o pocos severos
      return '#eab308';
    } else if (combinedFactor <= 0.6) {
      // Naranja - bastantes huecos o moderadamente severos
      return '#f97316';
    } else if (combinedFactor <= 0.8) {
      // Rojo claro - muchos huecos o severos
      return '#ef4444';
    } else {
      // Rojo oscuro - alta densidad y alta severidad
      return '#dc2626';
    }
  };

  // Función para obtener información de huecos de un segmento para el modal
  const getSegmentHoleInfo = (segment: RoadSegment) => {
    const holes = segment.huecos || [];
    
    if (holes.length === 0) {
      return {
        holeCount: 0,
        avgMagnitude: 0,
        maxMagnitude: 0,
        minMagnitude: 0,
        severityDistribution: {},
        density: 0,
        avgVelocity: 0
      };
    }
    
    const magnitudes = holes.map(h => h.magnitud);
    const velocities = holes.map(h => h.velocidad);
    
    const severityDistribution = holes.reduce((acc, hole) => {
      const severity = getHoleSeverity(hole.magnitud);
      acc[severity] = (acc[severity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    return {
      holeCount: holes.length,
      avgMagnitude: magnitudes.reduce((sum, mag) => sum + mag, 0) / magnitudes.length,
      maxMagnitude: Math.max(...magnitudes),
      minMagnitude: Math.min(...magnitudes),
      severityDistribution,
      density: holes.length / (segment.longitud / 1000), // huecos por km
      avgVelocity: velocities.reduce((sum, vel) => sum + vel, 0) / velocities.length
    };
  };

  // Función para agrupar huecos cercanos basado en el zoom
  const groupNearbyHoles = (holes: any[], zoomLevel: number) => {
    // En zoom alto (16+) no agrupar, mostrar todos individualmente
    if (zoomLevel >= 16) {
      return holes.map(hole => ({ ...hole, isGrouped: false }));
    }

    // Distancia de agrupación basada en el zoom
    let groupDistance: number;
    if (zoomLevel <= 10) {
      groupDistance = 0.01;     // Zoom bajo - grupos grandes
    } else if (zoomLevel <= 12) {
      groupDistance = 0.006;    // Zoom medio - grupos medianos
    } else if (zoomLevel <= 14) {
      groupDistance = 0.003;    // Zoom medio-alto - grupos pequeños
    } else {
      groupDistance = 0.001;    // Zoom alto - grupos mínimos
    }

    const grouped: any[] = [];
    const used = new Set<number>();

    holes.forEach((hole, index) => {
      if (used.has(index)) return;

      // Buscar huecos cercanos
      const nearbyHoles = [hole];
      
      for (let i = index + 1; i < holes.length; i++) {
        if (used.has(i)) continue;

        const otherHole = holes[i];
        
        // Calcular distancia euclidiana
        const distance = Math.sqrt(
          Math.pow(hole.latitud - otherHole.latitud, 2) + 
          Math.pow(hole.longitud - otherHole.longitud, 2)
        );

        if (distance <= groupDistance) {
          nearbyHoles.push(otherHole);
          used.add(i);
        }
      }

      used.add(index);

      if (nearbyHoles.length > 1) {
        // Calcular estadísticas del grupo
        const magnitudes = nearbyHoles.map(h => h.magnitud);
        const velocidades = nearbyHoles.map(h => h.velocidad);
        
        const avgMagnitud = magnitudes.reduce((sum, mag) => sum + mag, 0) / magnitudes.length;
        const maxMagnitud = Math.max(...magnitudes);
        const minMagnitud = Math.min(...magnitudes);
        const avgVelocidad = velocidades.reduce((sum, vel) => sum + vel, 0) / velocidades.length;
        
        // Calcular centro geográfico del grupo
        const centerLat = nearbyHoles.reduce((sum, h) => sum + h.latitud, 0) / nearbyHoles.length;
        const centerLng = nearbyHoles.reduce((sum, h) => sum + h.longitud, 0) / nearbyHoles.length;

        // Crear grupo de huecos
        grouped.push({
          latitud: centerLat,
          longitud: centerLng,
          magnitud: avgMagnitud, // Magnitud promedio para el color
          velocidad: avgVelocidad,
          isGrouped: true,
          holeCount: nearbyHoles.length,
          maxMagnitud,
          minMagnitud,
          avgMagnitud,
          avgVelocidad,
          originalHoles: nearbyHoles,
          roadSegment: hole.roadSegment,
          roadName: hole.roadName,
          severity: getHoleSeverity(avgMagnitud)
        });
      } else {
        // Mantener hueco individual
        grouped.push({
          ...hole,
          isGrouped: false
        });
      }
    });

    return grouped;
  };

  // Función para cambiar la capa de mapa
  const changeMapLayer = (newLayerType: string) => {
    if (!mapInstanceRef.current) return;
    
    // Remover la capa actual
    if (currentTileLayerRef.current) {
      mapInstanceRef.current.removeLayer(currentTileLayerRef.current);
    }
    
    // Obtener configuración de la nueva capa
    const layerConfig = getMapLayerConfig(newLayerType);
    
    // Crear y agregar la nueva capa
    const newTileLayer = L.tileLayer(layerConfig.url, {
      attribution: layerConfig.attribution,
      maxZoom: layerConfig.maxZoom,
      minZoom: 3
    });
    
    newTileLayer.addTo(mapInstanceRef.current);
    currentTileLayerRef.current = newTileLayer;
    
    setMapLayer(newLayerType as 'osm' | 'satellite' | 'terrain' | 'roads' | 'transport' | 'dark' | 'light');
  };

  // Función para manejar pantalla completa
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
    
    // Redimensionar el mapa después de un breve delay para asegurar que el DOM se actualice
    setTimeout(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    }, 100);
  };

  // Función para manejar la tecla Escape en pantalla completa
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false);
        setTimeout(() => {
          if (mapInstanceRef.current) {
            mapInstanceRef.current.invalidateSize();
          }
        }, 100);
      }
    };

    if (isFullscreen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isFullscreen]);
  
  const getColorByIQR = (iqr: number, minIQR: number, maxIQR: number): string => {
    // Normalizar el valor entre 0 y 1, donde 5 es el valor óptimo (verde)
    // Calcular qué tan cerca está del valor ideal (5)
    const distanceFrom5 = Math.abs(iqr - 5);
    const maxDistance = Math.max(Math.abs(minIQR - 5), Math.abs(maxIQR - 5));
    
    // Normalizar: 0 = muy cerca de 5 (verde), 1 = muy lejos de 5 (rojo)
    const normalized = maxDistance > 0 ? distanceFrom5 / maxDistance : 0;
    
    // Escala de color: Verde (cerca de 5) -> Amarillo -> Naranja -> Rojo (lejos de 5)
    if (normalized <= 0.25) {
      // Verde intenso (muy cerca de IQR 5 = excelente)
      const intensity = normalized * 4;
      return `rgb(${Math.floor(50 * intensity)}, ${200 + Math.floor(55 * (1 - intensity))}, ${Math.floor(50 * intensity)})`;
    } else if (normalized <= 0.5) {
      // Verde a amarillo
      const intensity = (normalized - 0.25) * 4;
      const red = Math.floor(50 + 205 * intensity);
      const green = 255;
      const blue = Math.floor(50 * (1 - intensity));
      return `rgb(${red}, ${green}, ${blue})`;
    } else if (normalized <= 0.75) {
      // Amarillo a naranja
      const intensity = (normalized - 0.5) * 4;
      const red = 255;
      const green = Math.floor(255 - 100 * intensity);
      return `rgb(${red}, ${green}, 0)`;
    } else {
      // Naranja a rojo (muy lejos de 5)
      const intensity = (normalized - 0.75) * 4;
      const red = 255;
      const green = Math.floor(155 * (1 - intensity));
      return `rgb(${red}, ${green}, 0)`;
    }
  };

  // Función para agrupar segmentos cercanos y promediar valores - MEJORADO con peso por longitud
  const groupNearbySegments = (data: RoadSegment[], zoomLevel: number): Array<RoadSegment | {
    numero: number;
    nombre: string;
    geometria: Array<{orden: number; longitud: number; latitud: number}>;
    IQR: number;
    longitud: number;
    isGrouped: boolean;
    segmentCount: number;
    originalSegments: RoadSegment[];
  }> => {
    // NIVELES DE ZOOM EXTENDIDOS - En zoom máximo (18+) NO agrupar
    if (zoomLevel >= 18) {
      // Zoom máximo - NO AGRUPACIÓN, mostrar todos los segmentos individuales
      return data;
    }
    
    // Distancia mínima para agrupar (en grados) - más niveles granulares
    let groupDistance: number;
    if (zoomLevel <= 6) {
      groupDistance = 0.05;     // Zoom muy bajo - grupos muy grandes
    } else if (zoomLevel <= 8) {
      groupDistance = 0.03;     // Zoom bajo - grupos grandes  
    } else if (zoomLevel <= 10) {
      groupDistance = 0.02;     // Zoom medio-bajo - grupos medianos-grandes
    } else if (zoomLevel <= 12) {
      groupDistance = 0.015;    // Zoom medio - grupos medianos
    } else if (zoomLevel <= 14) {
      groupDistance = 0.01;     // Zoom medio-alto - grupos pequeños
    } else if (zoomLevel <= 16) {
      groupDistance = 0.005;    // Zoom alto - grupos muy pequeños
    } else {
      groupDistance = 0.002;    // Zoom muy alto - grupos mínimos
    }
    
    const grouped: any[] = [];
    const used = new Set<number>();
    
    data.forEach((segment, index) => {
      if (used.has(index)) return;
      
      // Buscar segmentos cercanos
      const nearbySegments = [segment];
      const centerLat = segment.geometria[0]?.latitud || segment.latitud_origen;
      const centerLng = segment.geometria[0]?.longitud || segment.longitud_origen;
      
      for (let i = index + 1; i < data.length; i++) {
        if (used.has(i)) continue;
        
        const otherSegment = data[i];
        const otherLat = otherSegment.geometria[0]?.latitud || otherSegment.latitud_origen;
        const otherLng = otherSegment.geometria[0]?.longitud || otherSegment.longitud_origen;
        
        // Calcular distancia euclidiana simple
        const distance = Math.sqrt(
          Math.pow(centerLat - otherLat, 2) + Math.pow(centerLng - otherLng, 2)
        );
        
        if (distance <= groupDistance) {
          nearbySegments.push(otherSegment);
          used.add(i);
        }
      }
      
      used.add(index);
      
      if (nearbySegments.length > 1) {
        // PROMEDIO PONDERADO POR LONGITUD - segmentos más largos tienen más peso
        const totalLength = nearbySegments.reduce((sum, seg) => sum + seg.longitud, 0);
        
        // Calcular IQR promedio ponderado por la longitud de cada segmento
        const weightedIQR = nearbySegments.reduce((sum, seg) => {
          const weight = seg.longitud / totalLength; // Peso proporcional a la longitud
          return sum + (seg.IQR * weight);
        }, 0);
        
        // COMBINAR GEOMETRÍAS - unir todas las trayectorias de los segmentos
        const combinedGeometry: Array<{orden: number; longitud: number; latitud: number}> = [];
        let currentOrder = 0;
        
        // Ordenar segmentos por proximidad geográfica para crear una trayectoria coherente
        const sortedSegments = [...nearbySegments].sort((a, b) => {
          const aStart = a.geometria[0] || { latitud: a.latitud_origen, longitud: a.longitud_origen };
          const bStart = b.geometria[0] || { latitud: b.latitud_origen, longitud: b.longitud_origen };
          return aStart.latitud - bStart.latitud || aStart.longitud - bStart.longitud;
        });
        
        // Agregar todos los puntos de geometría de todos los segmentos
        sortedSegments.forEach((seg) => {
          seg.geometria.forEach((point) => {
            combinedGeometry.push({
              orden: currentOrder++,
              longitud: point.longitud,
              latitud: point.latitud
            });
          });
        });
        
        grouped.push({
          numero: segment.numero,
          nombre: `${nearbySegments.length} segmentos agrupados (${totalLength.toFixed(0)}m)`,
          geometria: combinedGeometry, // TRAYECTORIA COMPLETA COMBINADA
          IQR: weightedIQR, // IQR ponderado por longitud - ESTE DETERMINA EL COLOR
          longitud: totalLength, // Longitud total de todos los segmentos
          isGrouped: true,
          segmentCount: nearbySegments.length,
          originalSegments: nearbySegments
        });
      } else {
        // Mantener segmento individual
        grouped.push(segment);
      }
    });
    
    return grouped;
  };

  // Función para obtener el grosor de línea adaptativo al zoom - EXTENDIDO para más niveles
  const getLineWeight = (zoomLevel: number): number => {
    if (zoomLevel <= 4) return 2;     // Zoom mundial - líneas muy delgadas
    if (zoomLevel <= 6) return 3;     // Zoom continental - líneas delgadas
    if (zoomLevel <= 8) return 4;     // Zoom país - líneas finas
    if (zoomLevel <= 10) return 6;    // Zoom región - líneas normales
    if (zoomLevel <= 12) return 8;    // Zoom ciudad - líneas medias
    if (zoomLevel <= 14) return 12;   // Zoom distrito - líneas gruesas
    if (zoomLevel <= 16) return 16;   // Zoom barrio - líneas muy gruesas
    if (zoomLevel <= 18) return 20;   // Zoom calle - líneas súper gruesas
    return 24;                        // Zoom máximo - líneas ultra gruesas
  };

  // Función para obtener la opacidad basada en el zoom - EXTENDIDO para más niveles
  const getLineOpacity = (zoomLevel: number): number => {
    if (zoomLevel <= 4) return 1.0;     // Zoom mundial - totalmente opaco
    if (zoomLevel <= 6) return 0.95;    // Zoom continental - casi totalmente opaco
    if (zoomLevel <= 8) return 0.9;     // Zoom país - muy opaco
    if (zoomLevel <= 10) return 0.85;   // Zoom región - opaco
    if (zoomLevel <= 12) return 0.8;    // Zoom ciudad - semi-opaco
    if (zoomLevel <= 14) return 0.75;   // Zoom distrito - menos opaco
    if (zoomLevel <= 16) return 0.7;    // Zoom barrio - translúcido
    return 0.65;                        // Zoom máximo - más translúcido
  };

  // Función para cargar datos reales desde la API
  const loadRoadData = async () => {
    try {
      setIsLoading(true);
      
      console.log('🔄 Cargando datos desde API en tiempo real...');
      
      // Cargar datos desde la API (con fallback al archivo local)
      const data: RoadSegment[] = await simpleRoadDataService.loadAllRoadData();
      
      console.log(`✅ Cargados ${data.length} segmentos desde API`);
      
      // Calcular estadísticas de segmentos
      const iqrValues = data.map(road => road.IQR || 0);
      const minIQR = Math.min(...iqrValues);
      const maxIQR = Math.max(...iqrValues);
      const avgIQR = iqrValues.reduce((sum, val) => sum + val, 0) / iqrValues.length;
      
      setStats({
        total: data.length,
        minIQR: Number(minIQR.toFixed(3)),
        maxIQR: Number(maxIQR.toFixed(3)),
        avgIQR: Number(avgIQR.toFixed(3))
      });

      // Calcular estadísticas de huecos
      const allHoles = data.flatMap(road => road.huecos || []);
      if (allHoles.length > 0) {
        const magnitudes = allHoles.map(hole => hole.magnitud);
        const velocidades = allHoles.map(hole => hole.velocidad);
        
        setHoleStats({
          total: allHoles.length,
          minMagnitud: Number(Math.min(...magnitudes).toFixed(3)),
          maxMagnitud: Number(Math.max(...magnitudes).toFixed(3)),
          avgMagnitud: Number((magnitudes.reduce((sum, val) => sum + val, 0) / magnitudes.length).toFixed(3)),
          minVelocidad: Number(Math.min(...velocidades).toFixed(3)),
          maxVelocidad: Number(Math.max(...velocidades).toFixed(3))
        });
      }
      
      setRoadData(data);
    } catch (error) {
      console.error('Error loading road data:', error);
      // Fallback a datos de ejemplo si no se puede cargar el archivo
      setRoadData([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadRoadData();
  }, []);

  useEffect(() => {
    if (!mapRef.current || roadData.length === 0 || isLoading) return;

    // Limpiar mapa existente
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
    }

    // Calcular bounds del mapa basado en todos los datos
    const allLats = roadData.flatMap(road => 
      road.geometria.map(point => point.latitud)
    );
    const allLngs = roadData.flatMap(road => 
      road.geometria.map(point => point.longitud)
    );
    
    const bounds = L.latLngBounds(
      [Math.min(...allLats), Math.min(...allLngs)],
      [Math.max(...allLats), Math.max(...allLngs)]
    );

    // Crear mapa con vista inicial que muestre toda Colombia
    const map = L.map(mapRef.current, {
      // Configuraciones básicas para popups
      closePopupOnClick: false, // No cerrar popups al hacer clic en el mapa
      maxBoundsViscosity: 0.3,  // Permitir movimiento fuera de los límites
      wheelPxPerZoomLevel: 60,  // Control de zoom más suave
      zoomAnimation: true,      // Habilitar animaciones de zoom
      markerZoomAnimation: true // Habilitar animaciones de marcadores
    }).fitBounds(bounds, { padding: [50, 50] }); // Padding más generoso
    mapInstanceRef.current = map;

    // Agregar capa de tiles inicial
    const initialLayerConfig = getMapLayerConfig(mapLayer);
    const tileLayer = L.tileLayer(initialLayerConfig.url, {
      attribution: initialLayerConfig.attribution,
      maxZoom: initialLayerConfig.maxZoom,
      minZoom: 3
    });
    tileLayer.addTo(map);
    currentTileLayerRef.current = tileLayer;

    // Crear grupo de capas para los segmentos y huecos
    const layerGroup = L.layerGroup().addTo(map);
    layerGroupRef.current = layerGroup;
    
    const holesLayerGroup = L.layerGroup().addTo(map);
    holesLayerGroupRef.current = holesLayerGroup;

    // Función para renderizar huecos en el mapa
    const renderHoles = () => {
      if (!holesLayerGroupRef.current || analysisMode !== 'holes') return;
      
      holesLayerGroupRef.current.clearLayers();
      const currentZoom = map.getZoom();
      
      if (holeVisualizationMode === 'segments') {
        // Modo de visualización por segmentos con información de huecos
        const weight = getLineWeight(currentZoom);
        const opacity = getLineOpacity(currentZoom);
        
        // Determinar cuántos segmentos mostrar basado en el zoom
        let dataToShow = roadData;
        if (currentZoom <= 4) {
          dataToShow = roadData.filter((_, index) => index % 50 === 0);
        } else if (currentZoom <= 6) {
          dataToShow = roadData.filter((_, index) => index % 25 === 0);
        } else if (currentZoom <= 8) {
          dataToShow = roadData.filter((_, index) => index % 15 === 0);
        } else if (currentZoom <= 10) {
          dataToShow = roadData.filter((_, index) => index % 10 === 0);
        } else if (currentZoom <= 12) {
          dataToShow = roadData.filter((_, index) => index % 5 === 0);
        } else if (currentZoom <= 14) {
          dataToShow = roadData.filter((_, index) => index % 3 === 0);
        } else if (currentZoom <= 16) {
          dataToShow = roadData.filter((_, index) => index % 2 === 0);
        }
        
        dataToShow.forEach((road: RoadSegment) => {
          const color = getSegmentColorByHoles(road);
          
          // Crear línea desde geometría
          const latlngs: [number, number][] = road.geometria
            .sort((a: any, b: any) => a.orden - b.orden)
            .map((point: any) => [point.latitud, point.longitud]);
          
          if (latlngs.length < 2) return; // Saltar si no hay suficientes puntos
          
          const polyline = L.polyline(latlngs, {
            color: color,
            weight: weight,
            opacity: opacity,
            className: 'hole-segment'
          });
          
          // Click handler para modal con información de huecos del segmento
          polyline.on('click', function(e) {
            L.DomEvent.stopPropagation(e);
            
            const holeInfo = getSegmentHoleInfo(road);
            
            setSelectedSegment({
              ...road,
              isHole: true,
              isSegmentView: true, // Para distinguir en el modal
              holeInfo: holeInfo
            });
            setShowModal(true);
          });
          
          holesLayerGroupRef.current?.addLayer(polyline);
        });
        
        console.log(`Renderizados ${dataToShow.length} segmentos con información de huecos en zoom ${currentZoom}`);
        
      } else {
        // Modo de visualización por círculos (modo original)
        // Solo mostrar huecos en zoom medio-alto y alto para evitar saturación
        if (currentZoom < 10) return;
        
        // Obtener todos los huecos de los segmentos visibles
        const allHoles = roadData.flatMap(road => 
          (road.huecos || []).map(hole => ({
            ...hole,
            roadSegment: road.numero,
            roadName: getNombreSegmento(road.nombre)
          }))
        );
        
        // Aplicar filtrado por zoom antes de agrupar
        let holesToProcess = allHoles;
        if (currentZoom < 12) {
          // Mostrar solo 1 de cada 8 huecos para evitar saturación en zoom bajo
          holesToProcess = allHoles.filter((_, index) => index % 8 === 0);
        } else if (currentZoom < 14) {
          // Mostrar 1 de cada 4 huecos
          holesToProcess = allHoles.filter((_, index) => index % 4 === 0);
        } else if (currentZoom < 16) {
          // Mostrar 1 de cada 2 huecos
          holesToProcess = allHoles.filter((_, index) => index % 2 === 0);
        }
        
        // Agrupar huecos según el nivel de zoom
        const groupedHoles = groupNearbyHoles(holesToProcess, currentZoom);
        
        groupedHoles.forEach((hole: any) => {
          const color = getHoleColorByMagnitude(hole.magnitud, holeStats.minMagnitud, holeStats.maxMagnitud);
          
          // Tamaño adaptativo: grupos más grandes tienen marcadores más grandes
          let size: number;
          if (hole.isGrouped) {
            // Tamaño basado en el número de huecos agrupados (6-20 píxeles)
            size = Math.min(6 + (hole.holeCount * 1.5), 20);
          } else {
            // Tamaño normal para huecos individuales
            size = getHoleSize(hole.magnitud, holeStats.minMagnitud, holeStats.maxMagnitud);
          }
          
          // Crear marcador circular para el hueco o grupo
          const circle = L.circleMarker([hole.latitud, hole.longitud], {
            radius: size,
            fillColor: color,
            color: hole.isGrouped ? '#333' : '#fff', // Borde más oscuro para grupos
            weight: hole.isGrouped ? 3 : 2,
            opacity: 0.9,
            fillOpacity: hole.isGrouped ? 0.8 : 0.6,
            className: hole.isGrouped ? 'hole-group-marker' : 'hole-marker'
          });
          
          // Agregar texto en el centro para grupos
          if (hole.isGrouped && currentZoom >= 11) {
            const fontSize = Math.max(Math.min(size * 0.8, 16), 10); // Tamaño mínimo de 10px
            const textIcon = L.divIcon({
              html: `<div style="color: white; font-weight: bold; font-size: ${fontSize}px; text-align: center; line-height: ${size * 2}px; text-shadow: 2px 2px 2px rgba(0,0,0,0.9); cursor: pointer; user-select: none; border-radius: 50%; display: flex; align-items: center; justify-content: center; width: 100%; height: 100%;">${hole.holeCount}</div>`,
              className: 'hole-count-label',
              iconSize: [size * 2, size * 2],
              iconAnchor: [size, size]
            });
            
            const textMarker = L.marker([hole.latitud, hole.longitud], { icon: textIcon });
            
            // Agregar evento de clic al texto también
            textMarker.on('click', function(e) {
              L.DomEvent.stopPropagation(e);
              
              setSelectedSegment({
                isHole: true,
                isGrouped: hole.isGrouped,
                magnitud: hole.magnitud,
                velocidad: hole.velocidad,
                latitud: hole.latitud,
                longitud: hole.longitud,
                roadSegment: hole.roadSegment,
                roadName: hole.roadName,
                severity: hole.severity,
                // Datos adicionales para grupos
                holeCount: hole.holeCount,
                maxMagnitud: hole.maxMagnitud,
                minMagnitud: hole.minMagnitud,
                avgMagnitud: hole.avgMagnitud,
                avgVelocidad: hole.avgVelocidad,
                originalHoles: hole.originalHoles
              });
              setShowModal(true);
            });
            
            holesLayerGroupRef.current?.addLayer(textMarker);
          }
          
          // Agregar evento de clic para mostrar información del hueco o grupo
          circle.on('click', function(e) {
            L.DomEvent.stopPropagation(e);
            
            setSelectedSegment({
              isHole: true,
              isGrouped: hole.isGrouped,
              magnitud: hole.magnitud,
              velocidad: hole.velocidad,
              latitud: hole.latitud,
              longitud: hole.longitud,
              roadSegment: hole.roadSegment,
              roadName: hole.roadName,
              severity: hole.severity,
              // Datos adicionales para grupos
              holeCount: hole.holeCount,
              maxMagnitud: hole.maxMagnitud,
              minMagnitud: hole.minMagnitud,
              avgMagnitud: hole.avgMagnitud,
              avgVelocidad: hole.avgVelocidad,
              originalHoles: hole.originalHoles
            });
            setShowModal(true);
          });
          
          holesLayerGroupRef.current?.addLayer(circle);
        });
        
        console.log(`Renderizados ${groupedHoles.length} elementos de huecos (${groupedHoles.filter(h => h.isGrouped).length} grupos) en zoom ${currentZoom}`);
      }
    };

    // Función para renderizar segmentos según el zoom
    const renderRoadSegments = () => {
      if (!layerGroupRef.current || analysisMode !== 'segments') return;
      
      layerGroupRef.current.clearLayers();
      const currentZoom = map.getZoom();
      const weight = getLineWeight(currentZoom);
      const opacity = getLineOpacity(currentZoom);
      
      // Determinar cuántos segmentos mostrar basado en el zoom - EXTENDIDO con más niveles
      let dataToShow = roadData;
      if (currentZoom <= 4) {
        // Zoom mundial - mostrar muy pocos segmentos (1 de cada 50)
        dataToShow = roadData.filter((_, index) => index % 50 === 0);
      } else if (currentZoom <= 6) {
        // Zoom continental - mostrar pocos segmentos (1 de cada 25)
        dataToShow = roadData.filter((_, index) => index % 25 === 0);
      } else if (currentZoom <= 8) {
        // Zoom país - mostrar algunos segmentos (1 de cada 15)
        dataToShow = roadData.filter((_, index) => index % 15 === 0);
      } else if (currentZoom <= 10) {
        // Zoom región - mostrar más segmentos (1 de cada 10)
        dataToShow = roadData.filter((_, index) => index % 10 === 0);
      } else if (currentZoom <= 12) {
        // Zoom ciudad - mostrar bastantes segmentos (1 de cada 5)
        dataToShow = roadData.filter((_, index) => index % 5 === 0);
      } else if (currentZoom <= 14) {
        // Zoom distrito - mostrar muchos segmentos (1 de cada 3)
        dataToShow = roadData.filter((_, index) => index % 3 === 0);
      } else if (currentZoom <= 16) {
        // Zoom barrio - mostrar casi todos (1 de cada 2)
        dataToShow = roadData.filter((_, index) => index % 2 === 0);
      }
      // Zoom 16+ (calle/edificio) - mostrar todos los segmentos
      
      // Agrupar segmentos cercanos si el zoom es bajo (NO agrupar en zoom máximo 18+)
      const processedData = groupNearbySegments(dataToShow, currentZoom);
      
      processedData.forEach((road: any) => {
        const color = getColorByIQR(road.IQR, stats.minIQR, stats.maxIQR);
        
        // Crear línea desde geometría
        const latlngs: [number, number][] = road.geometria
          .sort((a: any, b: any) => a.orden - b.orden)
          .map((point: any) => [point.latitud, point.longitud]);
        
        if (latlngs.length < 2) return; // Saltar si no hay suficientes puntos
        
        // Ajustar grosor si es un grupo - hacer más gruesas las agrupaciones
        const adjustedWeight = road.isGrouped ? weight + 4 : weight;
        
        const polyline = L.polyline(latlngs, {
          color: color,
          weight: adjustedWeight,
          opacity: opacity,
          className: 'road-segment'
        });
        
        // En lugar de popup, usar click handler para modal
        polyline.on('click', function(e) {
          // Detener la propagación del evento
          L.DomEvent.stopPropagation(e);
          
          // Abrir modal con información del segmento
          setSelectedSegment(road);
          setShowModal(true);
        });
        
        layerGroupRef.current?.addLayer(polyline);
      });
      
      console.log(`Renderizados ${processedData.length} elementos en zoom ${currentZoom}`);
    };

    // Renderizar según el modo de análisis seleccionado
    const renderCurrentMode = () => {
      if (analysisMode === 'segments') {
        renderRoadSegments();
        // Limpiar huecos cuando se está en modo segmentos
        if (holesLayerGroupRef.current) {
          holesLayerGroupRef.current.clearLayers();
        }
      } else if (analysisMode === 'holes') {
        renderHoles();
        // Limpiar segmentos cuando se está en modo huecos
        if (layerGroupRef.current) {
          layerGroupRef.current.clearLayers();
        }
      }
    };

    // Renderizar modo inicial
    renderCurrentMode();

    // Actualizar cuando cambie el zoom
    map.on('zoomend', renderCurrentMode);
    map.on('moveend', renderCurrentMode);

    // Cleanup
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [roadData, isLoading, stats, analysisMode, holeVisualizationMode, holeStats]);

  if (isLoading) {
    return (
      <div className="w-full">
        <div className="mb-4 p-4 bg-white rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Cargando Análisis de Carreteras...
          </h3>
          <div className="animate-pulse flex space-x-4">
            <div className="flex-1 space-y-2 py-1">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
        </div>
        <div 
          className="rounded-lg shadow-lg border border-gray-200 bg-gray-100 flex items-center justify-center"
          style={{ height, width }}
        >
          <div className="text-gray-500">Cargando mapa...</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`w-full ${isFullscreen ? 'fixed inset-0 z-50 bg-white' : ''}`}>
      <div className={`${isFullscreen ? 'h-full flex flex-col' : ''}`}>
        <div className={`${isFullscreen ? 'flex-shrink-0' : 'mb-4'} p-4 bg-white rounded-lg shadow-sm border`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Análisis de Calidad de Carreteras
            </h3>
            
            <div className="flex items-center space-x-3">
              {/* Selector de capas de mapa */}
              <div className="relative">
                <select
                  value={mapLayer}
                  onChange={(e) => changeMapLayer(e.target.value)}
                  className="bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  title="Seleccionar tipo de mapa"
                >
                  <option value="osm">{getMapLayerConfig('osm').name}</option>
                  <option value="satellite">{getMapLayerConfig('satellite').name}</option>
                  <option value="terrain">{getMapLayerConfig('terrain').name}</option>
                  <option value="roads">{getMapLayerConfig('roads').name}</option>
                  <option value="transport">{getMapLayerConfig('transport').name}</option>
                  <option value="dark">{getMapLayerConfig('dark').name}</option>
                  <option value="light">{getMapLayerConfig('light').name}</option>
                </select>
              </div>
              
              {/* Botón de pantalla completa */}
              <button
              onClick={toggleFullscreen}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isFullscreen 
                  ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                  : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
              }`}
              title={isFullscreen ? 'Salir de pantalla completa (Esc)' : 'Pantalla completa'}
            >
              {isFullscreen ? (
                <span className="flex items-center space-x-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <span>Cerrar</span>
                </span>
              ) : (
                <span className="flex items-center space-x-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                  </svg>
                  <span>Pantalla Completa</span>
                </span>
              )}
            </button>
            </div>
          </div>
        
        {/* Pestañas de modo de análisis */}
        <div className="flex mb-4 border-b">
          <button
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              analysisMode === 'segments'
                ? 'border-blue-500 text-blue-600 bg-blue-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setAnalysisMode('segments')}
          >
            Análisis de Segmentos (IQR)
          </button>
          <button
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              analysisMode === 'holes'
                ? 'border-orange-500 text-orange-600 bg-orange-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setAnalysisMode('holes')}
          >
            Análisis de Huecos
          </button>
        </div>
        
        {/* Contenido dinámico basado en el modo de análisis */}
        {analysisMode === 'segments' ? (
          // Modo de análisis de segmentos
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{stats.total}</div>
                <div className="text-sm text-gray-600">Segmentos</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{stats.minIQR}</div>
                <div className="text-sm text-gray-600">IQR Mínimo</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{stats.maxIQR}</div>
                <div className="text-sm text-gray-600">IQR Máximo</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">{stats.avgIQR}</div>
                <div className="text-sm text-gray-600">IQR Promedio</div>
              </div>
            </div>
            
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>Haz zoom para ver más detalles de los segmentos</span>
              <div className="flex items-center space-x-4">
                <div className="flex items-center">
                  <div className="w-4 h-2 bg-green-500 mr-2"></div>
                  <span>Excelente (IQR ~5)</span>
                </div>
                <div className="flex items-center">
                  <div className="w-4 h-2 bg-yellow-500 mr-2"></div>
                  <span>Bueno</span>
                </div>
                <div className="flex items-center">
                  <div className="w-4 h-2 bg-orange-500 mr-2"></div>
                  <span>Regular</span>
                </div>
                <div className="flex items-center">
                  <div className="w-4 h-2 bg-red-500 mr-2"></div>
                  <span>Malo (lejos de 5)</span>
                </div>
              </div>
            </div>
          </>
        ) : (
          // Modo de análisis de huecos
          <>
            {holeStats.total > 0 ? (
              <>
                {/* Selector de modo de visualización de huecos */}
                <div className="mb-4 p-3 bg-gray-50 rounded-lg border">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Modo de Visualización:</h4>
                  <div className="flex space-x-2">
                    <button
                      className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                        holeVisualizationMode === 'circles'
                          ? 'bg-orange-500 text-white'
                          : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => setHoleVisualizationMode('circles')}
                    >
                      Círculos Individuales
                    </button>
                    <button
                      className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                        holeVisualizationMode === 'segments'
                          ? 'bg-orange-500 text-white'
                          : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => setHoleVisualizationMode('segments')}
                    >
                      Segmentos por Densidad
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    {holeVisualizationMode === 'circles' 
                      ? 'Muestra cada hueco como un círculo coloreado por severidad'
                      : 'Muestra segmentos de carretera coloreados por densidad y severidad de huecos'
                    }
                  </p>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">{holeStats.total}</div>
                    <div className="text-sm text-gray-600">Huecos Detectados</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">{holeStats.maxMagnitud}</div>
                    <div className="text-sm text-gray-600">Magnitud Máxima</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-600">{holeStats.avgMagnitud}</div>
                    <div className="text-sm text-gray-600">Magnitud Promedio</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{holeStats.minMagnitud}</div>
                    <div className="text-sm text-gray-600">Magnitud Mínima</div>
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <span>
                    {holeVisualizationMode === 'circles' 
                      ? 'Haz zoom para ver más huecos (visible desde zoom 10)'
                      : 'Segmentos coloreados por densidad y severidad de huecos'
                    }
                  </span>
                  <div className="flex items-center space-x-3">
                    {holeVisualizationMode === 'circles' ? (
                      // Leyenda para modo círculos
                      <>
                        <div className="flex items-center">
                          <div className="w-3 h-3 bg-green-400 rounded-full mr-1"></div>
                          <span className="text-xs">Leve (&lt;2)</span>
                        </div>
                        <div className="flex items-center">
                          <div className="w-3 h-3 bg-yellow-400 rounded-full mr-1"></div>
                          <span className="text-xs">Moderado (2-3)</span>
                        </div>
                        <div className="flex items-center">
                          <div className="w-3 h-3 bg-orange-500 rounded-full mr-1"></div>
                          <span className="text-xs">Severo (3-4)</span>
                        </div>
                        <div className="flex items-center">
                          <div className="w-3 h-3 bg-red-600 rounded-full mr-1"></div>
                          <span className="text-xs">Muy Severo (&gt;4)</span>
                        </div>
                      </>
                    ) : (
                      // Leyenda para modo segmentos
                      <>
                        <div className="flex items-center">
                          <div className="w-4 h-2 bg-green-500 mr-2"></div>
                          <span className="text-xs">Sin huecos / Pocos leves</span>
                        </div>
                        <div className="flex items-center">
                          <div className="w-4 h-2 bg-yellow-500 mr-2"></div>
                          <span className="text-xs">Huecos moderados</span>
                        </div>
                        <div className="flex items-center">
                          <div className="w-4 h-2 bg-orange-500 mr-2"></div>
                          <span className="text-xs">Bastantes huecos</span>
                        </div>
                        <div className="flex items-center">
                          <div className="w-4 h-2 bg-red-600 mr-2"></div>
                          <span className="text-xs">Alta densidad/severidad</span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <div className="text-gray-500">No se encontraron huecos en los datos cargados</div>
              </div>
            )}
          </>
        )}
      </div>
      
      <div 
        ref={mapRef} 
        style={{ height: isFullscreen ? 'calc(100vh - 200px)' : height, width }}
        className="rounded-lg shadow-lg border border-gray-200"
      />

      {/* Modal para información del segmento */}
      {showModal && selectedSegment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center" style={{ zIndex: 10000 }} onClick={() => setShowModal(false)}>
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-96 overflow-y-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {selectedSegment.isHole ? 
                  selectedSegment.isSegmentView ?
                    `Análisis de Huecos - ${getNombreSegmento(selectedSegment.nombre)}` :
                  selectedSegment.isGrouped ?
                    `Zona con ${selectedSegment.holeCount} Huecos - ${selectedSegment.roadName}` :
                    `Hueco Detectado - ${selectedSegment.roadName}` : 
                  getNombreSegmento(selectedSegment.nombre)
                }
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-600 text-xl"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-3">
              {selectedSegment.isHole ? (
                // Información para huecos
                <>
                  {selectedSegment.isSegmentView ? (
                    // Información para segmento con análisis de huecos
                    <>
                      <div className="border-b pb-3">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm text-gray-600">
                              <strong>Segmento:</strong> #{selectedSegment.numero}
                            </p>
                            <p className="text-sm text-gray-600">
                              <strong>Longitud:</strong> {selectedSegment.longitud.toFixed(1)}m
                            </p>
                            <p className="text-sm text-gray-600">
                              <strong>Huecos Detectados:</strong> 
                              <span className="ml-1 font-medium text-orange-600">
                                {selectedSegment.holeInfo.holeCount}
                              </span>
                            </p>
                            <p className="text-sm text-gray-600">
                              <strong>Densidad:</strong> {selectedSegment.holeInfo.density.toFixed(1)} huecos/km
                            </p>
                          </div>
                          <div>
                            {selectedSegment.holeInfo.holeCount > 0 ? (
                              <>
                                <p className="text-sm text-gray-600">
                                  <strong>Severidad Promedio:</strong> 
                                  <span className="ml-1 font-medium" style={{ 
                                    color: getHoleColorByMagnitude(selectedSegment.holeInfo.avgMagnitude, holeStats.minMagnitud, holeStats.maxMagnitud) 
                                  }}>
                                    {getHoleSeverity(selectedSegment.holeInfo.avgMagnitude)}
                                  </span>
                                </p>
                                <p className="text-sm text-gray-600">
                                  <strong>Magnitud Promedio:</strong> {selectedSegment.holeInfo.avgMagnitude.toFixed(3)}
                                </p>
                                <p className="text-sm text-gray-600">
                                  <strong>Magnitud Máxima:</strong> 
                                  <span className="ml-1 font-medium text-red-600">
                                    {selectedSegment.holeInfo.maxMagnitude.toFixed(3)}
                                  </span>
                                </p>
                                <p className="text-sm text-gray-600">
                                  <strong>Velocidad Promedio:</strong> {selectedSegment.holeInfo.avgVelocity.toFixed(1)} km/h
                                </p>
                              </>
                            ) : (
                              <p className="text-sm text-green-600 font-medium">
                                ✅ Segmento sin huecos detectados
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      {selectedSegment.holeInfo.holeCount > 0 && (
                        <>
                          <div className="bg-orange-50 p-3 rounded-lg">
                            <h4 className="text-sm font-medium text-orange-800 mb-1">Análisis del Segmento</h4>
                            <p className="text-xs text-orange-700">
                              {selectedSegment.holeInfo.density > 5 ?
                                `🚨 Alta densidad de huecos (${selectedSegment.holeInfo.density.toFixed(1)}/km). Segmento prioritario para mantenimiento.` :
                              selectedSegment.holeInfo.density > 2 ?
                                `⚠️ Densidad moderada de huecos (${selectedSegment.holeInfo.density.toFixed(1)}/km). Requiere atención programada.` :
                                `ℹ️ Baja densidad de huecos (${selectedSegment.holeInfo.density.toFixed(1)}/km). Monitoreo recomendado.`
                              }
                            </p>
                            {selectedSegment.holeInfo.maxMagnitude > 3 && (
                              <p className="text-xs text-red-700 mt-1">
                                ⚠️ Contiene huecos severos que requieren atención inmediata.
                              </p>
                            )}
                          </div>
                          
                          <div className="mt-3">
                            <h4 className="text-sm font-medium text-gray-700 mb-2">Distribución de Severidad:</h4>
                            <div className="grid grid-cols-2 gap-2 text-xs">
                              {Object.entries(selectedSegment.holeInfo.severityDistribution).map(([severity, count]) => (
                                <div key={severity} className="flex justify-between bg-gray-50 rounded px-2 py-1">
                                  <span>{severity}:</span>
                                  <span className="font-medium">{count as number}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                          
                          <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                            <div className="text-center bg-red-50 rounded p-2">
                              <div className="font-medium text-red-600">{selectedSegment.holeInfo.maxMagnitude.toFixed(2)}</div>
                              <div className="text-gray-500">Peor Hueco</div>
                            </div>
                            <div className="text-center bg-yellow-50 rounded p-2">
                              <div className="font-medium text-yellow-600">{selectedSegment.holeInfo.avgMagnitude.toFixed(2)}</div>
                              <div className="text-gray-500">Promedio</div>
                            </div>
                            <div className="text-center bg-green-50 rounded p-2">
                              <div className="font-medium text-green-600">{selectedSegment.holeInfo.minMagnitude.toFixed(2)}</div>
                              <div className="text-gray-500">Mejor</div>
                            </div>
                          </div>
                        </>
                      )}
                    </>
                  ) : selectedSegment.isGrouped ? (
                    // Información para grupos de huecos
                    <>
                      <div className="border-b pb-3">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm text-gray-600">
                              <strong>Huecos Agrupados:</strong> {selectedSegment.holeCount}
                            </p>
                            <p className="text-sm text-gray-600">
                              <strong>Severidad Promedio:</strong> 
                              <span className="ml-1 font-medium" style={{ 
                                color: getHoleColorByMagnitude(selectedSegment.avgMagnitud, holeStats.minMagnitud, holeStats.maxMagnitud) 
                              }}>
                                {selectedSegment.severity}
                              </span>
                            </p>
                            <p className="text-sm text-gray-600">
                              <strong>Magnitud Promedio:</strong> {selectedSegment.avgMagnitud?.toFixed(3)}
                            </p>
                            <p className="text-sm text-gray-600">
                              <strong>Velocidad Promedio:</strong> {selectedSegment.avgVelocidad?.toFixed(1)} km/h
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">
                              <strong>Magnitud Máxima:</strong> 
                              <span className="ml-1 font-medium text-red-600">
                                {selectedSegment.maxMagnitud?.toFixed(3)}
                              </span>
                            </p>
                            <p className="text-sm text-gray-600">
                              <strong>Magnitud Mínima:</strong> 
                              <span className="ml-1 font-medium text-green-600">
                                {selectedSegment.minMagnitud?.toFixed(3)}
                              </span>
                            </p>
                            <p className="text-sm text-gray-600">
                              <strong>Centro del Grupo:</strong>
                            </p>
                            <p className="text-xs text-gray-500">
                              {selectedSegment.latitud.toFixed(6)}, {selectedSegment.longitud.toFixed(6)}
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      <div className="bg-orange-50 p-3 rounded-lg">
                        <h4 className="text-sm font-medium text-orange-800 mb-1">Análisis de la Zona</h4>
                        <p className="text-xs text-orange-700">
                          Esta zona concentra <strong>{selectedSegment.holeCount} huecos</strong> con severidad promedio <strong>{selectedSegment.severity}</strong>.
                          {selectedSegment.maxMagnitud > 3 ? 
                            " ⚠️ Contiene huecos severos que requieren atención prioritaria." :
                          selectedSegment.avgMagnitud > 2 ? 
                            " Zona con deterioro moderado que requiere mantenimiento." :
                            " Zona con deterioro leve pero que debe ser monitoreada."
                          }
                        </p>
                        <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                          <div className="text-center bg-white rounded p-1">
                            <div className="font-medium text-red-600">{selectedSegment.maxMagnitud?.toFixed(2)}</div>
                            <div className="text-gray-500">Peor</div>
                          </div>
                          <div className="text-center bg-white rounded p-1">
                            <div className="font-medium text-yellow-600">{selectedSegment.avgMagnitud?.toFixed(2)}</div>
                            <div className="text-gray-500">Promedio</div>
                          </div>
                          <div className="text-center bg-white rounded p-1">
                            <div className="font-medium text-green-600">{selectedSegment.minMagnitud?.toFixed(2)}</div>
                            <div className="text-gray-500">Mejor</div>
                          </div>
                        </div>
                      </div>
                      
                      {selectedSegment.originalHoles && (
                        <div className="mt-3">
                          <h4 className="text-sm font-medium text-gray-700 mb-2">
                            Distribución de Severidad:
                          </h4>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            {(() => {
                              const severityCounts = {
                                'Muy Leve': 0, 'Leve': 0, 'Moderado': 0, 'Severo': 0, 'Muy Severo': 0
                              };
                              selectedSegment.originalHoles.forEach((hole: any) => {
                                const severity = getHoleSeverity(hole.magnitud);
                                severityCounts[severity as keyof typeof severityCounts]++;
                              });
                              
                              return Object.entries(severityCounts)
                                .filter(([_, count]) => count > 0)
                                .map(([severity, count]) => (
                                  <div key={severity} className="flex justify-between bg-gray-50 rounded px-2 py-1">
                                    <span>{severity}:</span>
                                    <span className="font-medium">{count}</span>
                                  </div>
                                ));
                            })()}
                          </div>
                          <p className="text-xs text-gray-400 mt-2">
                            Haz más zoom para ver huecos individuales
                          </p>
                        </div>
                      )}
                    </>
                  ) : (
                    // Información para huecos individuales
                    <>
                      <div className="border-b pb-3">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm text-gray-600">
                              <strong>Severidad:</strong> 
                              <span className="ml-1 font-medium" style={{ 
                                color: getHoleColorByMagnitude(selectedSegment.magnitud, holeStats.minMagnitud, holeStats.maxMagnitud) 
                              }}>
                                {selectedSegment.severity}
                              </span>
                            </p>
                            <p className="text-sm text-gray-600">
                              <strong>Magnitud:</strong> {selectedSegment.magnitud.toFixed(3)}
                            </p>
                            <p className="text-sm text-gray-600">
                              <strong>Velocidad:</strong> {selectedSegment.velocidad.toFixed(3)} km/h
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">
                              <strong>Segmento:</strong> #{selectedSegment.roadSegment}
                            </p>
                            <p className="text-sm text-gray-600">
                              <strong>Latitud:</strong> {selectedSegment.latitud.toFixed(6)}
                            </p>
                            <p className="text-sm text-gray-600">
                              <strong>Longitud:</strong> {selectedSegment.longitud.toFixed(6)}
                            </p>
                          </div>
                        </div>
                      </div>
                      <div className="bg-yellow-50 p-3 rounded-lg">
                        <h4 className="text-sm font-medium text-yellow-800 mb-1">Análisis del Hueco</h4>
                        <p className="text-xs text-yellow-700">
                          {selectedSegment.magnitud < 1 ? 
                            "Hueco muy leve. Impacto mínimo en la comodidad de conducción." :
                          selectedSegment.magnitud < 2 ? 
                            "Hueco leve. Puede causar pequeñas molestias al conducir." :
                          selectedSegment.magnitud < 3 ? 
                            "Hueco moderado. Requiere atención para evitar daños menores al vehículo." :
                          selectedSegment.magnitud < 4 ? 
                            "Hueco severo. Puede causar daños significativos al vehículo y afectar la seguridad." :
                            "Hueco muy severo. Alto riesgo de daños graves al vehículo y peligro para la seguridad vial."
                          }
                        </p>
                        <p className="text-xs text-yellow-600 mt-1">
                          Velocidad promedio en la zona: {selectedSegment.velocidad.toFixed(1)} km/h
                        </p>
                      </div>
                    </>
                  )}
                </>
              ) : selectedSegment.isGrouped ? (
                // Información para segmentos agrupados
                <>
                  <div className="border-b pb-3">
                    <p className="text-sm text-gray-600">
                      <strong>Segmentos agrupados:</strong> {selectedSegment.segmentCount}
                    </p>
                    <p className="text-sm text-gray-600">
                      <strong>IQR Ponderado:</strong> {selectedSegment.IQR.toFixed(3)}
                    </p>
                    <p className="text-sm text-gray-600">
                      <strong>Longitud Total:</strong> {selectedSegment.longitud?.toFixed(1) || 'N/A'}m
                    </p>
                    <p className="text-sm text-gray-600">
                      <strong>Estado Ponderado:</strong> 
                      <span className="ml-1 font-medium" style={{ color: getColorByIQR(selectedSegment.IQR, stats.minIQR, stats.maxIQR) }}>
                        {selectedSegment.IQR < 1 ? 'Muy Malo' : 
                         selectedSegment.IQR < 2 ? 'Malo' :
                         selectedSegment.IQR < 3 ? 'Regular' : 
                         selectedSegment.IQR < 4 ? 'Bueno' : 
                         selectedSegment.IQR < 5 ? 'Muy Bueno' : 'Excelente'}
                      </span>
                    </p>
                  </div>
                  <p className="text-xs text-gray-500">
                    IQR calculado con promedio ponderado por longitud. Haz zoom para ver segmentos individuales.
                  </p>
                  {selectedSegment.originalSegments && (
                    <div className="mt-3">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Segmentos incluidos:</h4>
                      <div className="max-h-32 overflow-y-auto space-y-1">
                        {selectedSegment.originalSegments.slice(0, 5).map((seg: any, idx: number) => (
                          <p key={idx} className="text-xs text-gray-500">
                            • {getNombreSegmento(seg.nombre)} (IQR: {seg.IQR.toFixed(2)}, {seg.longitud.toFixed(0)}m)
                          </p>
                        ))}
                        {selectedSegment.originalSegments.length > 5 && (
                          <p className="text-xs text-gray-400">
                            ... y {selectedSegment.originalSegments.length - 5} más
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                // Información para segmentos individuales
                <>
                  <div className="grid grid-cols-2 gap-4 border-b pb-3">
                    <div>
                      <p className="text-sm text-gray-600">
                        <strong>Segmento:</strong> {selectedSegment.numero}
                      </p>
                      <p className="text-sm text-gray-600">
                        <strong>Tipo:</strong> {selectedSegment.tipo}
                      </p>
                      <p className="text-sm text-gray-600">
                        <strong>Longitud:</strong> {selectedSegment.longitud.toFixed(1)}m
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">
                        <strong>IQR:</strong> {selectedSegment.IQR.toFixed(3)}
                      </p>
                      <p className="text-sm text-gray-600">
                        <strong>IRI:</strong> {selectedSegment.iri?.toFixed(3) || 'N/A'}
                      </p>
                      <p className="text-sm text-gray-600">
                        <strong>Estado:</strong> 
                        <span className="ml-1 font-medium" style={{ color: getColorByIQR(selectedSegment.IQR, stats.minIQR, stats.maxIQR) }}>
                          {selectedSegment.IQR < 1 ? 'Muy Malo' : 
                           selectedSegment.IQR < 2 ? 'Malo' :
                           selectedSegment.IQR < 3 ? 'Regular' : 
                           selectedSegment.IQR < 4 ? 'Bueno' : 
                           selectedSegment.IQR < 5 ? 'Muy Bueno' : 'Excelente'}
                        </span>
                      </p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <p className="text-xs text-gray-500">
                      <strong>Fecha:</strong> {selectedSegment.fecha ? new Date(selectedSegment.fecha).toLocaleDateString() : 'N/A'}
                    </p>
                    {selectedSegment.huecos && selectedSegment.huecos.length > 0 && (
                      <p className="text-xs text-gray-500">
                        <strong>Huecos detectados:</strong> {selectedSegment.huecos.length}
                      </p>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
};

export default RoadQualityMap;
