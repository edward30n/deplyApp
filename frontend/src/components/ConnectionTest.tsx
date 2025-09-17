import React, { useState, useEffect } from 'react';
import { buildApiUrl, API_BASE_URL } from '../config/api';

const ConnectionTest: React.FC = () => {
    const [status, setStatus] = useState<string>('🔄 Probando conexión...');
    const [data, setData] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        testConnection();
    }, []);

    const testConnection = async () => {
        try {
            setStatus('📡 Conectando al backend...');
            
            // Probar endpoint de estadísticas primero
            const response = await fetch(buildApiUrl('/api/export/statistics'));
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const stats = await response.json();
            setData(stats);
            setStatus('✅ ¡Conexión exitosa!');
            setError(null);
            
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : 'Error desconocido';
            setError(errorMsg);
            setStatus('❌ Error de conexión');
            console.error('Error de conexión:', err);
        }
    };

    return (
        <div style={{ 
            padding: '20px', 
            margin: '20px', 
            border: '2px solid #ccc', 
            borderRadius: '8px',
            backgroundColor: '#f9f9f9'
        }}>
            <h3>🔗 Test de Conexión Frontend ↔ Backend</h3>
            
            <div style={{ marginBottom: '15px' }}>
                <strong>Estado:</strong> {status}
            </div>
            
            {error && (
                <div style={{ 
                    color: 'red', 
                    backgroundColor: '#fee', 
                    padding: '10px', 
                    borderRadius: '4px',
                    marginBottom: '15px'
                }}>
                    <strong>Error:</strong> {error}
                </div>
            )}
            
            {data && (
                <div style={{ 
                    backgroundColor: '#efe', 
                    padding: '10px', 
                    borderRadius: '4px',
                    marginBottom: '15px'
                }}>
                    <h4>📊 Datos del Backend:</h4>
                    <ul>
                        <li><strong>Total Segmentos:</strong> {data.resumen?.total_segmentos}</li>
                        <li><strong>Total Muestras:</strong> {data.resumen?.total_muestras}</li>
                        <li><strong>Total Geometrías:</strong> {data.resumen?.total_geometrias}</li>
                        <li><strong>Rango de Fechas:</strong> {data.fechas?.fecha_minima} → {data.fechas?.fecha_maxima}</li>
                    </ul>
                    
                    <h5>Por Tipo de Segmento:</h5>
                    <ul>
                        {Object.entries(data.por_tipo || {}).map(([tipo, count]) => (
                            <li key={tipo}><strong>{tipo}:</strong> {count as number} segmentos</li>
                        ))}
                    </ul>
                </div>
            )}
            
            <button 
                onClick={testConnection}
                style={{
                    padding: '10px 20px',
                    backgroundColor: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                }}
            >
                🔄 Probar Conexión
            </button>
            
            <div style={{ marginTop: '15px', fontSize: '12px', color: '#666' }}>
                <strong>Backend:</strong> {API_BASE_URL}<br/>
                <strong>Frontend:</strong> http://localhost:5174<br/>
                <strong>API Endpoint:</strong> /api/export/statistics
            </div>
        </div>
    );
};

export default ConnectionTest;
