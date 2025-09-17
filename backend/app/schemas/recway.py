"""
Esquemas Pydantic para RecWay - Validación de datos
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# =================== ESQUEMAS BASE ===================

class GeometriaBase(BaseModel):
    orden: int
    coordenada_x: float = Field(..., alias="longitud")  # longitud
    coordenada_y: float = Field(..., alias="latitud")   # latitud

class GeometriaCreate(GeometriaBase):
    pass

class GeometriaResponse(GeometriaBase):
    id_geometria: int
    id_segmento_seleccionado: int

    class Config:
        from_attributes = True


class HuecoBase(BaseModel):
    latitud: float
    longitud: float
    magnitud: float
    velocidad: float

class HuecoMuestraCreate(HuecoBase):
    pass

class HuecoMuestraResponse(HuecoBase):
    id_hueco_muestra: int
    id_muestra_seleccionada: int

    class Config:
        from_attributes = True


class HuecoSegmentoCreate(HuecoBase):
    ultima_fecha_muestra: Optional[str] = None
    error_gps: Optional[float] = None

class HuecoSegmentoResponse(HuecoSegmentoCreate):
    id_hueco_segmento: int
    id_segmento_seleccionado: int

    class Config:
        from_attributes = True


class IndicesBase(BaseModel):
    nota_general: float = Field(..., alias="IQR")        # IQR
    iri_modificado: float = Field(..., alias="IRI_modificado")  # IRI_modificado
    iri_estandar: float = Field(..., alias="iri")        # iri
    indice_primero: float = Field(..., alias="az")       # az
    indice_segundo: float = Field(..., alias="ax")       # ax
    iri_tercero: Optional[float] = Field(None, alias="wx")  # wx

class IndicesMuestraCreate(IndicesBase):
    pass

class IndicesMuestraResponse(IndicesBase):
    id_indice_muestra: int
    id_muestra: int

    class Config:
        from_attributes = True


class IndicesSegmentoCreate(IndicesBase):
    pass

class IndicesSegmentoResponse(IndicesBase):
    id_indice_segmento: int
    id_segmento_seleccionado: int

    class Config:
        from_attributes = True


# =================== ESQUEMAS PRINCIPALES ===================

class MuestraCreate(BaseModel):
    tipo_dispositivo: Optional[str] = None
    identificador_dispositivo: Optional[str] = None
    fecha_muestra: Optional[str] = None
    id_segmento_seleccionado: int
    created_by_user_id: int

class MuestraResponse(MuestraCreate):
    id_muestra: int
    indices_muestra: List[IndicesMuestraResponse] = []
    huecos_muestra: List[HuecoMuestraResponse] = []

    class Config:
        from_attributes = True


class SegmentoCreate(BaseModel):
    nombre: str
    tipo: Optional[str] = None
    nodo_inicial_x: float = Field(..., alias="longitud_origen")
    nodo_final_x: float = Field(..., alias="longitud_destino")
    nodo_inicial_y: float = Field(..., alias="latitud_origen")
    nodo_final_y: float = Field(..., alias="latitud_destino")
    cantidad_muestras: int = 0
    ultima_fecha_muestra: Optional[str] = None
    longitud: float
    oneway: Optional[bool] = None
    surface: Optional[int] = None
    width: Optional[float] = None
    error_gps: Optional[float] = None
    created_by_user_id: int

class SegmentoResponse(SegmentoCreate):
    id_segmento: int
    created_at: datetime
    geometrias: List[GeometriaResponse] = []
    indices_segmento: List[IndicesSegmentoResponse] = []
    huecos_segmento: List[HuecoSegmentoResponse] = []
    muestras: List[MuestraResponse] = []

    class Config:
        from_attributes = True


# =================== ESQUEMAS DEL CSV Y DISPOSITIVO ===================

class CSVMetadata(BaseModel):
    """Metadatos extraídos del encabezado del CSV"""
    device_id: str
    session_id: str
    platform: str
    device_model: str
    manufacturer: str
    brand: str
    os_version: str
    app_version: str
    company: str
    android_id: str
    battery_info: str
    acc_available: bool
    acc_info: str
    gyro_available: bool
    gyro_info: str
    gps_available: bool
    gps_info: str
    export_date: datetime
    total_records: int
    sampling_rate: float
    recording_duration: str
    average_sample_rate: float

class FuenteDatosDispositivoCreate(BaseModel):
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    platform: Optional[str] = None
    device_model: Optional[str] = None
    manufacturer: Optional[str] = None
    brand: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    company: Optional[str] = None
    android_id: Optional[str] = None
    battery_info: Optional[str] = None
    acc_available: Optional[bool] = None
    acc_info: Optional[str] = None
    gyro_available: Optional[bool] = None
    gyro_info: Optional[str] = None
    gps_available: Optional[bool] = None
    gps_info: Optional[str] = None
    export_date: Optional[datetime] = None
    total_records: Optional[int] = None
    sampling_rate: Optional[float] = None
    recording_duration: Optional[str] = None
    average_sample_rate: Optional[float] = None
    created_by_user_id: int

class FuenteDatosDispositivoResponse(FuenteDatosDispositivoCreate):
    id_fuente: int

    class Config:
        from_attributes = True


class RegistroSensoresCreate(BaseModel):
    timestamp: int
    acc_x: Optional[float] = None
    acc_y: Optional[float] = None
    acc_z: Optional[float] = None
    acc_magnitude: Optional[float] = None
    gyro_x: Optional[float] = None
    gyro_y: Optional[float] = None
    gyro_z: Optional[float] = None
    gyro_magnitude: Optional[float] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    gps_accuracy: Optional[float] = None
    gps_speed: Optional[float] = None
    gps_speed_accuracy: Optional[float] = None
    gps_altitude: Optional[float] = None
    gps_altitude_accuracy: Optional[float] = None
    gps_heading: Optional[float] = None
    gps_heading_accuracy: Optional[float] = None
    gps_timestamp: Optional[int] = None
    gps_provider: Optional[str] = None
    device_orientation: Optional[float] = None
    sample_rate: Optional[float] = None
    gps_changed: bool = False
    id_fuente: int

class RegistroSensoresResponse(RegistroSensoresCreate):
    id_registro: int

    class Config:
        from_attributes = True


# =================== ESQUEMAS COMPUESTOS ===================

class SegmentoFromJSON(BaseModel):
    """Esquema para un segmento extraído del JSON de procesamiento"""
    numero: int
    id: int
    nombre: Union[str, List[str]]  # Puede ser string o lista de strings
    longitud: float
    tipo: str
    latitud_origen: float
    latitud_destino: float
    longitud_origen: float
    longitud_destino: float
    geometria: List[Dict[str, Any]]
    fecha: str
    IQR: float
    iri: float
    IRI_modificado: float
    az: float
    ax: float
    wx: float
    huecos: List[Dict[str, Any]]
    
    @field_validator('nombre')
    @classmethod
    def validate_nombre(cls, v):
        """Convierte lista de nombres en un string único"""
        if isinstance(v, list):
            return " / ".join(v)  # Unir con " / " si es lista
        return v


class ProcessingDataBundle(BaseModel):
    """Bundle completo de datos para procesamiento"""
    csv_metadata: CSVMetadata
    processed_segments: List[SegmentoFromJSON]
    csv_sensor_data: List[Dict[str, Any]]  # Datos de sensores del CSV


class ProcessingResult(BaseModel):
    """Resultado del procesamiento y almacenamiento"""
    fuente_datos_id: int
    segmentos_creados: List[int]  # IDs de segmentos creados
    segmentos_actualizados: List[int]  # IDs de segmentos actualizados
    muestras_creadas: List[int]  # IDs de muestras creadas
    registros_sensores_creados: int  # Cantidad de registros de sensores creados
    total_processing_time: float  # Tiempo total de procesamiento en segundos
