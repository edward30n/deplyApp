"""
Modelos SQLAlchemy para RecWay - Sistema de análisis de datos viales
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, BigInteger, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class Segmento(Base):
    """Tabla principal de segmentos viales"""
    __tablename__ = "segmento"

    id_segmento = Column(BigInteger, primary_key=True, autoincrement=True)
    id_original = Column(String(50), nullable=False, unique=True)  # ID original del JSON
    nombre = Column(String(50), nullable=False)
    tipo = Column(String(50))
    nodo_inicial_x = Column(Float, nullable=False)  # longitud_origen
    nodo_final_x = Column(Float, nullable=False)    # longitud_destino  
    nodo_inicial_y = Column(Float, nullable=False)  # latitud_origen
    nodo_final_y = Column(Float, nullable=False)    # latitud_destino
    cantidad_muestras = Column(Integer, nullable=False, default=0)
    ultima_fecha_muestra = Column(String(30))
    longitud = Column(Float, nullable=False)
    oneway = Column(Boolean)
    surface = Column(Integer)
    width = Column(Float)
    error_gps = Column(Float)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())

    # Relaciones
    geometrias = relationship("Geometria", back_populates="segmento", cascade="all, delete-orphan")
    indices_segmento = relationship("IndicesSegmento", back_populates="segmento", cascade="all, delete-orphan")
    huecos_segmento = relationship("HuecoSegmento", back_populates="segmento", cascade="all, delete-orphan")
    muestras = relationship("Muestra", back_populates="segmento", cascade="all, delete-orphan")
    # created_by = relationship("User", foreign_keys=[created_by_user_id])  # Comentado temporalmente


class Geometria(Base):
    """Geometría de los segmentos"""
    __tablename__ = "geometria"

    id_geometria = Column(BigInteger, primary_key=True, autoincrement=True)
    orden = Column(Integer, nullable=False)
    coordenada_x = Column(Float, nullable=False)  # longitud
    coordenada_y = Column(Float, nullable=False)  # latitud
    id_segmento_seleccionado = Column(BigInteger, ForeignKey("segmento.id_segmento", ondelete="CASCADE"), nullable=False)

    # Relaciones
    segmento = relationship("Segmento", back_populates="geometrias")


class IndicesSegmento(Base):
    """Índices calculados del segmento"""
    __tablename__ = "indicessegmento"

    id_indice_segmento = Column(BigInteger, primary_key=True, autoincrement=True)
    nota_general = Column(Float, nullable=False)     # IQR
    iri_modificado = Column(Float, nullable=False)   # IRI_modificado
    iri_estandar = Column(Float, nullable=False)     # iri
    indice_primero = Column(Float, nullable=False)   # az
    indice_segundo = Column(Float, nullable=False)   # ax
    iri_tercero = Column(Float)                      # wx
    id_segmento_seleccionado = Column(BigInteger, ForeignKey("segmento.id_segmento", ondelete="CASCADE"), nullable=False)

    # Relaciones
    segmento = relationship("Segmento", back_populates="indices_segmento")


class HuecoSegmento(Base):
    """Huecos asociados al segmento (promedio de todas las muestras)"""
    __tablename__ = "huecosegmento"

    id_hueco_segmento = Column(BigInteger, primary_key=True, autoincrement=True)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    magnitud = Column(Float, nullable=False)
    velocidad = Column(Float, nullable=False)
    ultima_fecha_muestra = Column(String(30))
    error_gps = Column(Float)
    id_segmento_seleccionado = Column(BigInteger, ForeignKey("segmento.id_segmento", ondelete="CASCADE"), nullable=False)

    # Relaciones
    segmento = relationship("Segmento", back_populates="huecos_segmento")


class Muestra(Base):
    """Muestras individuales de grabaciones"""
    __tablename__ = "muestra"

    id_muestra = Column(BigInteger, primary_key=True, autoincrement=True)
    tipo_dispositivo = Column(String(30))           # platform del CSV
    identificador_dispositivo = Column(String(60))  # device_id del CSV
    fecha_muestra = Column(String(40))              # fecha del JSON
    id_segmento_seleccionado = Column(BigInteger, ForeignKey("segmento.id_segmento", ondelete="CASCADE"), nullable=False)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id"))

    # Relaciones
    segmento = relationship("Segmento", back_populates="muestras")
    indices_muestra = relationship("IndicesMuestra", back_populates="muestra", cascade="all, delete-orphan")
    huecos_muestra = relationship("HuecoMuestra", back_populates="muestra", cascade="all, delete-orphan")
    # created_by = relationship("User", foreign_keys=[created_by_user_id])  # Comentado temporalmente


class IndicesMuestra(Base):
    """Índices calculados por muestra individual"""
    __tablename__ = "indices_muestra"

    id_indice_muestra = Column(BigInteger, primary_key=True, autoincrement=True)
    nota_general = Column(Float, nullable=False)     # IQR del JSON
    iri_modificado = Column(Float, nullable=False)   # IRI_modificado del JSON
    iri_estandar = Column(Float, nullable=False)     # iri del JSON
    indice_primero = Column(Float, nullable=False)   # az del JSON
    indice_segundo = Column(Float, nullable=False)   # ax del JSON
    iri_tercero = Column(Float)                      # wx del JSON
    id_muestra = Column(BigInteger, ForeignKey("muestra.id_muestra", ondelete="CASCADE"), nullable=False)

    # Relaciones
    muestra = relationship("Muestra", back_populates="indices_muestra")


class HuecoMuestra(Base):
    """Huecos individualizados por muestra"""
    __tablename__ = "huecomuestra"

    id_hueco_muestra = Column(BigInteger, primary_key=True, autoincrement=True)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    magnitud = Column(Float, nullable=False)
    velocidad = Column(Float, nullable=False)
    id_muestra_seleccionada = Column(BigInteger, ForeignKey("muestra.id_muestra", ondelete="CASCADE"), nullable=False)

    # Relaciones
    muestra = relationship("Muestra", back_populates="huecos_muestra")


class FuenteDatosDispositivo(Base):
    """Metainformación del dispositivo que envía la información"""
    __tablename__ = "fuente_datos_dispositivo"

    id_fuente = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(String(100))
    session_id = Column(String(100))
    platform = Column(String(50))
    device_model = Column(String(100))
    manufacturer = Column(String(100))
    brand = Column(String(100))
    os_version = Column(String(50))
    app_version = Column(String(100))
    company = Column(String(100))
    android_id = Column(String(100))
    battery_info = Column(String(100))
    acc_available = Column(Boolean)
    acc_info = Column(String(100))
    gyro_available = Column(Boolean)
    gyro_info = Column(String(100))
    gps_available = Column(Boolean)
    gps_info = Column(String(100))
    export_date = Column(DateTime)
    total_records = Column(Integer)
    sampling_rate = Column(Float)
    recording_duration = Column(String(20))
    average_sample_rate = Column(Float)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id"))

    # Relaciones
    registros_sensores = relationship("RegistroSensores", back_populates="fuente", cascade="all, delete-orphan")
    # created_by = relationship("User", foreign_keys=[created_by_user_id])  # Comentado temporalmente


class RegistroSensores(Base):
    """Registro detallado de cada muestra de sensor"""
    __tablename__ = "registro_sensores"

    id_registro = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(BigInteger, nullable=False)
    acc_x = Column(Float)
    acc_y = Column(Float)
    acc_z = Column(Float)
    acc_magnitude = Column(Float)
    gyro_x = Column(Float)
    gyro_y = Column(Float)
    gyro_z = Column(Float)
    gyro_magnitude = Column(Float)
    gps_lat = Column(Float)
    gps_lng = Column(Float)
    gps_accuracy = Column(Float)
    gps_speed = Column(Float)
    gps_speed_accuracy = Column(Float)
    gps_altitude = Column(Float)
    gps_altitude_accuracy = Column(Float)
    gps_heading = Column(Float)
    gps_heading_accuracy = Column(Float)
    gps_timestamp = Column(BigInteger)
    gps_provider = Column(String(50))
    device_orientation = Column(Float)
    sample_rate = Column(Float)
    gps_changed = Column(Boolean, default=False)
    id_fuente = Column(BigInteger, ForeignKey("fuente_datos_dispositivo.id_fuente", ondelete="CASCADE"), nullable=False)

    # Relaciones
    fuente = relationship("FuenteDatosDispositivo", back_populates="registros_sensores")
