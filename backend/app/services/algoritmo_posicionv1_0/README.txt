VERSION 1.0

------------------------------------------------------------
🚀 Ejecución del script

python script.py --carpeta_csv ./datos_csv --prefijo RecWay_ --carpeta_json ./json_salida --carpeta_csv_guardar ./csv_procesados --carpeta_json_guardar ./json_historial --carpeta_grafos ./grafos --workers 4 --umbral_velocidad 2.5

------------------------------------------------------------
⚙️ Parámetros configurables

--carpeta_csv            Carpeta con CSVs a procesar
--prefijo                Prefijo de archivos CSV
--carpeta_json           Carpeta de salida de JSON
--carpeta_csv_guardar    Carpeta donde se mueven los CSV procesados
--carpeta_json_guardar   Carpeta donde se guardan historial de JSON
--carpeta_grafos         Carpeta de grafos 
--workers                Cantidad de nucleos para el proceso en paralelo
--umbral_velocidad       Umbral de velocidad (m/s) para segmentarl

------------------------------------------------------------
📌 Nota
Los valores predeterminados de los parámetros se pueden cambiar en la línea 672 del main_procesamiento.py.
