"""
Utilidades para parsear CSV de RecWay y extraer metadatos
"""
import csv
import re
from typing import List, Dict, Any, Tuple
from datetime import datetime
from io import StringIO
import logging

from app.schemas.recway import CSVMetadata

logger = logging.getLogger(__name__)

class CSVParser:
    """Parser para archivos CSV de RecWay"""
    
    @staticmethod
    def parse_csv_file(file_path: str) -> Tuple[CSVMetadata, List[Dict[str, Any]]]:
        """
        Parsea un archivo CSV completo y extrae metadatos y datos de sensores
        
        Args:
            file_path: Ruta al archivo CSV
            
        Returns:
            Tuple con (metadatos, datos_sensores)
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        return CSVParser.parse_csv_content(content)
    
    @staticmethod
    def parse_csv_content(content: str) -> Tuple[CSVMetadata, List[Dict[str, Any]]]:
        """
        Parsea el contenido de un CSV y extrae metadatos y datos de sensores
        
        Args:
            content: Contenido completo del CSV como string
            
        Returns:
            Tuple con (metadatos, datos_sensores)
        """
        lines = content.strip().split('\n')
        
        # Extraer metadatos del encabezado
        metadata = CSVParser._extract_metadata(lines)
        
        # Encontrar donde empiezan los datos
        data_start_line = None
        for i, line in enumerate(lines):
            if line.startswith('timestamp,'):
                data_start_line = i
                break
        
        if data_start_line is None:
            raise ValueError("No se encontró la línea de encabezado de datos")
        
        # Parsear datos de sensores
        sensor_data = CSVParser._parse_sensor_data(lines[data_start_line:])
        
        return metadata, sensor_data
    
    @staticmethod
    def _extract_metadata(lines: List[str]) -> CSVMetadata:
        """Extrae metadatos del encabezado del CSV"""
        metadata_dict = {}
        
        for line in lines:
            if line.startswith('#') or not line.strip():
                # Extraer información clave-valor del encabezado
                if ':' in line:
                    # Limpiar la línea
                    clean_line = line.replace('#', '').strip()
                    
                    # Patrones específicos para extraer datos
                    patterns = {
                        'device_id': r'Device ID:\s*(.+)',
                        'session_id': r'Session ID:\s*(.+)',
                        'platform': r'Platform:\s*(.+)',
                        'device_model': r'Device Model:\s*(.+)',
                        'manufacturer': r'Manufacturer:\s*(.+)',
                        'brand': r'Brand:\s*(.+)',
                        'os_version': r'OS Version:\s*(.+)',
                        'app_version': r'App Version:\s*(.+)',
                        'company': r'Company:\s*(.+)',
                        'android_id': r'Android ID:\s*(.+)',
                        'battery_info': r'Battery Info:\s*(.+)',
                        'acc_available': r'Accelerometer Available:\s*(.+)',
                        'acc_info': r'Accelerometer Info:\s*(.+)',
                        'gyro_available': r'Gyroscope Available:\s*(.+)',
                        'gyro_info': r'Gyroscope Info:\s*(.+)',
                        'gps_available': r'GPS Available:\s*(.+)',
                        'gps_info': r'GPS Info:\s*(.+)',
                        'export_date': r'Export Date:\s*(.+)',
                        'total_records': r'Total Records:\s*(.+)',
                        'sampling_rate': r'Sampling Rate:\s*(.+)',
                        'recording_duration': r'Recording Duration:\s*(.+)',
                        'average_sample_rate': r'Average Sample Rate:\s*(.+)'
                    }
                    
                    for key, pattern in patterns.items():
                        match = re.search(pattern, clean_line, re.IGNORECASE)
                        if match:
                            value = match.group(1).strip()
                            metadata_dict[key] = value
                            break
        
        # Convertir tipos de datos
        try:
            export_date = datetime.fromisoformat(metadata_dict.get('export_date', '').replace('Z', '+00:00'))
        except:
            export_date = datetime.now()
        
        try:
            total_records = int(metadata_dict.get('total_records', '0'))
        except:
            total_records = 0
        
        try:
            sampling_rate = float(metadata_dict.get('sampling_rate', '0').replace(' Hz', ''))
        except:
            sampling_rate = 0.0
        
        try:
            average_sample_rate = float(metadata_dict.get('average_sample_rate', '0').replace(' Hz', ''))
        except:
            average_sample_rate = 0.0
        
        # Convertir booleanos
        acc_available = metadata_dict.get('acc_available', '').lower() == 'true'
        gyro_available = metadata_dict.get('gyro_available', '').lower() == 'true'
        gps_available = metadata_dict.get('gps_available', '').lower() == 'true'
        
        return CSVMetadata(
            device_id=metadata_dict.get('device_id', ''),
            session_id=metadata_dict.get('session_id', ''),
            platform=metadata_dict.get('platform', ''),
            device_model=metadata_dict.get('device_model', ''),
            manufacturer=metadata_dict.get('manufacturer', ''),
            brand=metadata_dict.get('brand', ''),
            os_version=metadata_dict.get('os_version', ''),
            app_version=metadata_dict.get('app_version', ''),
            company=metadata_dict.get('company', ''),
            android_id=metadata_dict.get('android_id', ''),
            battery_info=metadata_dict.get('battery_info', ''),
            acc_available=acc_available,
            acc_info=metadata_dict.get('acc_info', ''),
            gyro_available=gyro_available,
            gyro_info=metadata_dict.get('gyro_info', ''),
            gps_available=gps_available,
            gps_info=metadata_dict.get('gps_info', ''),
            export_date=export_date,
            total_records=total_records,
            sampling_rate=sampling_rate,
            recording_duration=metadata_dict.get('recording_duration', ''),
            average_sample_rate=average_sample_rate
        )
    
    @staticmethod
    def _parse_sensor_data(data_lines: List[str]) -> List[Dict[str, Any]]:
        """Parsea los datos de sensores del CSV"""
        if not data_lines:
            return []
        
        # Crear un StringIO para usar csv.DictReader
        csv_content = '\n'.join(data_lines)
        csv_file = StringIO(csv_content)
        
        reader = csv.DictReader(csv_file)
        sensor_data = []
        
        for row in reader:
            # Convertir valores numéricos
            processed_row = {}
            for key, value in row.items():
                if value == '' or value is None:
                    processed_row[key] = None
                else:
                    # Intentar convertir a número
                    try:
                        if '.' in value:
                            processed_row[key] = float(value)
                        else:
                            processed_row[key] = int(value)
                    except (ValueError, TypeError):
                        processed_row[key] = value
            
            sensor_data.append(processed_row)
        
        return sensor_data
    
    @staticmethod
    def extract_device_info_simple(csv_content: str) -> Dict[str, str]:
        """
        Extrae información básica del dispositivo de forma rápida
        Útil para identificar archivos sin parsear completo
        """
        lines = csv_content.split('\n')[:50]  # Solo primeras 50 líneas
        
        info = {}
        for line in lines:
            if 'Device ID:' in line:
                info['device_id'] = line.split('Device ID:')[1].strip().replace('#', '').strip()
            elif 'Session ID:' in line:
                info['session_id'] = line.split('Session ID:')[1].strip().replace('#', '').strip()
            elif 'Platform:' in line:
                info['platform'] = line.split('Platform:')[1].strip().replace('#', '').strip()
                
        return info
