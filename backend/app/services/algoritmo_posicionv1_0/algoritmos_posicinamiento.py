import numpy as np
import pandas as pd
import os
from shapely.geometry import Point, Polygon
from geopy.distance import geodesic
import osmnx as ox
import networkx as nx
import math
from datetime import datetime


def encontrar_area_latlon(lat1, lon1, lat2, lon2, L):
    """
    Calcula los 4 puntos del rectángulo alrededor del segmento entre (lat1, lon1) y (lat2, lon2),
    expandido lateralmente por L.

    Args:
        lat1, lon1: Punto inicial (latitud, longitud).
        lat2, lon2: Punto final (latitud, longitud).
        L: Ancho lateral en unidades consistentes con lat/lon (aproximadas en grados).

    Returns:
        (lat1a, lon1a, lat1b, lon1b, lat2a, lon2a, lat2b, lon2b): 4 puntos (lat, lon).
    """
    A = lon1 - lon2
    B = lat2 - lat1
    C = A * lat1 + B * lon1
    D1 = B * lat1 - A * lon1
    D2 = B * lat2 - A * lon2
    L_norm = (L**2 * (A**2 + B**2))**0.5
    E1 = C + L_norm
    E2 = C - L_norm

    lat1a = (A * E1 + B * D1) / (A**2 + B**2)
    lon1a = -(A * D1 - B * E1) / (A**2 + B**2)
    lat1b = (A * E2 + B * D1) / (A**2 + B**2)
    lon1b = -(A * D1 - B * E2) / (A**2 + B**2)
    lat2a = (A * E1 + B * D2) / (A**2 + B**2)
    lon2a = -(A * D2 - B * E1) / (A**2 + B**2)
    lat2b = (A * E2 + B * D2) / (A**2 + B**2)
    lon2b = -(A * D2 - B * E2) / (A**2 + B**2)

    return (lat1a, lon1a, lat1b, lon1b, lat2a, lon2a, lat2b, lon2b)

def determinar_area_rectangulo(segmento_coordenadas,L,longitud,latitud):
    """
    Esta función determina si un punto se encuentra en un area de un segmento
    que puede estar hecho de uno o varios puntos, y con una anchura del L, en 
    el caso que se encuentre retorna un 1 y si no un 0.

    Args:
        segmento_coordenadas(array[float]): La longitud de la coordenada en formato decimal.
        L: La latitud de la coordenada en formato decimal.
        aristas_conectadas(Diccionario): el Diccionario de la información de la arista.
        L: longitud del segmento tranversal del segmento

    Returns:
        int: El indice de la arista donde se encuentra el punto.
    """
    #se plantean los vectores donde se almacenan los nodos superiores e inferiores
    nodos_sup = []
    nodos_inf = []
    
    #se añade los primeros puntos 
    nodos_sup.append(np.array(encontrar_area(segmento_coordenadas[0][0],segmento_coordenadas[0][1],segmento_coordenadas[1][0],segmento_coordenadas[1][1],L)[0:2]))
    nodos_inf.append(np.array(encontrar_area(segmento_coordenadas[0][0],segmento_coordenadas[0][1],segmento_coordenadas[1][0],segmento_coordenadas[1][1],L)[2:4]))
    
    #se recorre todos los puntos del segmento para asignar sus anchos
    for i in range(1,len(segmento_coordenadas)-1):
        valores_finales = encontrar_area(segmento_coordenadas[i-1][0],segmento_coordenadas[i-1][1],segmento_coordenadas[i][0],segmento_coordenadas[i][1],L)[4:6]
        valores_iniciales = encontrar_area(segmento_coordenadas[i][0],segmento_coordenadas[i][1],segmento_coordenadas[i+1][0],segmento_coordenadas[i+1][1],L)[0:2]
        nodos_sup.append((np.array(valores_iniciales)+np.array(valores_finales))/2)
        valores_finales = encontrar_area(segmento_coordenadas[i-1][0],segmento_coordenadas[i-1][1],segmento_coordenadas[i][0],segmento_coordenadas[i][1],L)[6:]
        valores_iniciales = encontrar_area(segmento_coordenadas[i][0],segmento_coordenadas[i][1],segmento_coordenadas[i+1][0],segmento_coordenadas[i+1][1],L)[2:4]
        nodos_inf.append((np.array(valores_iniciales)+np.array(valores_finales))/2)
    
    #se asignan los nodos finales
    fin = len(segmento_coordenadas)-1
    nodos_sup.append(np.array(encontrar_area(segmento_coordenadas[fin-1][0],segmento_coordenadas[fin-1][1],segmento_coordenadas[fin][0],segmento_coordenadas[fin][1],L)[4:6]))
    nodos_inf.append(np.array(encontrar_area(segmento_coordenadas[fin-1][0],segmento_coordenadas[fin-1][1],segmento_coordenadas[fin][0],segmento_coordenadas[fin][1],L)[6:]))
    
    #se crea un nuevo vector para guardar una secuencia de los nodos superiorres e inferiores
    nodos_finales = np.concatenate((nodos_sup,nodos_inf[::-1]))
    
    #se convierte en un poligono
    poligono = Polygon(nodos_finales)
    
    #se asigna el punto para buscar 
    punto = Point(longitud,latitud)
    
    #se utiliza la funcion poligono.contains para determinar si el punto se encuentra en el poligono
    if poligono.contains(punto):
        return 1
    else:
        return 0

def generar_poligono_segmento_lonlat(segmento, L):
    """
    Genera un polígono alrededor de un segmento (lista de puntos lon, lat) con un ancho L.
    
    Args:
        segmento (list): Lista [(lon, lat), ...] de puntos del segmento.
        L (float): Ancho lateral en las mismas unidades que lon/lat (grados aprox.).
    
    Returns:
        Polygon: Polígono que rodea el segmento.
    """
    puntos_superior = []
    puntos_inferior = []

    for i in range(len(segmento) - 1):
        lon1, lat1 = segmento[i]
        lon2, lat2 = segmento[i + 1]

        # Vector dirección
        dx = lon2 - lon1
        dy = lat2 - lat1
        longitud = np.hypot(dx, dy)

        if longitud == 0:
            continue  # Ignorar puntos repetidos

        # Vector perpendicular normalizado (cambio signo)
        nx = -dy / longitud
        ny = dx / longitud

        # Punto 1 desplazado
        lon1_sup = lon1 + nx * L
        lat1_sup = lat1 + ny * L
        lon1_inf = lon1 - nx * L
        lat1_inf = lat1 - ny * L

        # Punto 2 desplazado
        lon2_sup = lon2 + nx * L
        lat2_sup = lat2 + ny * L
        lon2_inf = lon2 - nx * L
        lat2_inf = lat2 - ny * L

        if i == 0:
            puntos_superior.append((lon1_sup, lat1_sup))
            puntos_inferior.append((lon1_inf, lat1_inf))

        puntos_superior.append((lon2_sup, lat2_sup))
        puntos_inferior.append((lon2_inf, lat2_inf))

    # Cerrar el polígono correctamente
    puntos_inferior.reverse()
    poligono = Polygon(puntos_superior + puntos_inferior)

    return poligono

def punto_en_poligono(poligono, longitud, latitud):
    """
    Verifica si un punto (longitud, latitud) está dentro del polígono.

    Args:
        poligono (Polygon): Polígono de shapely.
        longitud (float): Longitud del punto.
        latitud (float): Latitud del punto.

    Returns:
        bool: True si el punto está dentro del polígono, False en caso contrario.
    """
    punto = Point(longitud, latitud)
    return poligono.contains(punto)



def obtener_coordenadas_segmento(G, id_segmento, info_segmento):
    """
    Retorna la lista de coordenadas que forman el segmento.

    Parámetros:
    - segmento: diccionario que representa la arista (puede tener 'geometry').
    - G: grafo OSMnx.
    - edge_cercano: tupla con los nodos extremos (u, v).

    Retorno:
    - Listado de coordenadas (lista de tuplas).
    """
    # Condición para ver si el segmento tiene geometría
    if 'geometry' in info_segmento:
        segmento_coordenadas = list(info_segmento['geometry'].coords)
    else:
        nodo_inicial = G.nodes[id_segmento[0]]
        nodo_final = G.nodes[id_segmento[1]]
        segmento_coordenadas = [
            (nodo_inicial['x'], nodo_inicial['y']),
            (nodo_final['x'], nodo_final['y'])
        ]
    return segmento_coordenadas


def proyectar_segmento(segmento_coords, longitud, latitud):
    """
    Proyecta ortogonalmente un punto (longitud, latitud) sobre un segmento de carretera.

    Args:
        segmento_coords (list): Lista de tuplas [(lon, lat), (lon, lat), ...] que representan el segmento.
        longitud (float): Longitud del punto a proyectar.
        latitud (float): Latitud del punto a proyectar.

    Returns:
        tuple: (latitud_proyectada, longitud_proyectada) el punto más cercano sobre el segmento.
    """

    punto = (longitud, latitud)
    distancia_min = float('inf')
    punto_proyectado = None

    # Recorremos cada tramo (par de puntos consecutivos)
    for i in range(len(segmento_coords) - 1):
        p1 = segmento_coords[i]
        p2 = segmento_coords[i + 1]

        # Proyección ortogonal usando fórmula vectorial en coordenadas planas
        x1, y1 = p1
        x2, y2 = p2
        x0, y0 = punto

        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            # p1 y p2 son el mismo punto
            proy_x, proy_y = x1, y1
        else:
            # Parámetro t para proyección sobre el segmento
            t = ((x0 - x1) * dx + (y0 - y1) * dy) / (dx**2 + dy**2)
            t = max(0, min(1, t))  # Limitar t entre 0 y 1

            proy_x = x1 + t * dx
            proy_y = y1 + t * dy

        proy_punto = (proy_y, proy_x)
        distancia = geodesic((latitud, longitud), (proy_y, proy_x)).meters

        if distancia < distancia_min:
            distancia_min = distancia
            punto_proyectado = proy_punto

    return punto_proyectado


def distancia_segmento(segmento_coords, longitud, latitud):
    """
    Proyecta ortogonalmente un punto (longitud, latitud) sobre un segmento de carretera y determinar su distancia.

    Args:
        segmento_coords (list): Lista de tuplas [(lon, lat), (lon, lat), ...] que representan el segmento.
        longitud (float): Longitud del punto a proyectar.
        latitud (float): Latitud del punto a proyectar.

    Returns:
        distancia: float que representa la distancia del punto más cercano sobre el segmento.
    """

    punto = (longitud, latitud)
    distancia_min = float('inf')
    punto_proyectado = None

    # Recorremos cada tramo (par de puntos consecutivos)
    for i in range(len(segmento_coords) - 1):
        p1 = segmento_coords[i]
        p2 = segmento_coords[i + 1]

        # Proyección ortogonal usando fórmula vectorial en coordenadas planas
        x1, y1 = p1
        x2, y2 = p2
        x0, y0 = punto

        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            # p1 y p2 son el mismo punto
            proy_x, proy_y = x1, y1
        else:
            # Parámetro t para proyección sobre el segmento
            t = ((x0 - x1) * dx + (y0 - y1) * dy) / (dx**2 + dy**2)
            t = max(0, min(1, t))  # Limitar t entre 0 y 1

            proy_x = x1 + t * dx
            proy_y = y1 + t * dy

        proy_punto = (proy_y, proy_x)
        distancia = geodesic((latitud, longitud), (proy_y, proy_x)).meters

        if distancia < distancia_min:
            distancia_min = distancia
            punto_proyectado = proy_punto

    return distancia


def cargar_csv_con_metadatos(carpeta, nombre_csv):
    """
    Carga un archivo CSV exportado por RecWay desde una carpeta y nombre de archivo dado.
    Extrae los metadatos desde las líneas iniciales (prefijadas con '#')
    y carga los datos sensoriales en un DataFrame.

    Parámetros:
        carpeta : str
            Ruta a la carpeta que contiene el archivo CSV.
        nombre_csv : str
            Nombre del archivo CSV (con extensión .csv).

    Retorna:
        df : pandas.DataFrame
            Datos medidos en formato tabular.
        metadatos : dict
            Diccionario con metadatos (sin incluir ruta ni archivo).
    """
    ruta_csv = os.path.join(carpeta, nombre_csv)

    if not os.path.isfile(ruta_csv):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_csv}")

    metadatos = {}
    lineas_saltadas = 0

    # Intentar múltiples codificaciones para mayor compatibilidad
    encodings_to_try = ['utf-8', 'latin-1', 'windows-1252', 'iso-8859-1']
    file_content = None
    used_encoding = None
    
    for encoding in encodings_to_try:
        try:
            with open(ruta_csv, 'r', encoding=encoding) as f:
                file_content = f.read()
                used_encoding = encoding
                break
        except UnicodeDecodeError:
            continue
    
    if file_content is None:
        raise ValueError(f"No se pudo leer el archivo {ruta_csv} con ninguna codificación conocida")
    
    # Procesar línea por línea desde el contenido leído
    lines = file_content.splitlines()
    line_index = 0
    
    for linea in lines:
        linea = linea.strip()

        if linea.startswith("timestamp"):
            break

        if linea.startswith("#") and ":" in linea:
            try:
                clave, valor = linea.strip("# ").split(":", 1)
                metadatos[clave.strip()] = valor.strip()
            except ValueError:
                pass

        lineas_saltadas += 1

    # Leer el CSV con la misma codificación encontrada
    df = pd.read_csv(ruta_csv, skiprows=lineas_saltadas, encoding=used_encoding)

    return df, metadatos

def filtrar_muestras_por_velocidad(df, umbral_velocidad):
    """
    Filtra el DataFrame y retorna solo las muestras donde la velocidad GPS
    supera un valor umbral.

    Parámetros:
        df : pandas.DataFrame
            DataFrame con la columna 'gps_speed'.
        umbral_velocidad : float
            Velocidad mínima (en m/s) para conservar la muestra.

    Retorna:
        pandas.DataFrame con las filas que cumplen la condición.
    """
    if 'gps_speed' not in df.columns:
        raise ValueError("El DataFrame no contiene la columna 'gps_speed'.")

    df_filtrado = df[df['gps_speed'] > umbral_velocidad].copy()
    return df_filtrado

#esta función tambien invierte las muestras del GPS
def eliminar_muestras_gps_duplicadas(df):
    """
    Elimina las filas donde la latitud y longitud GPS no cambian respecto a la fila anterior.
    Además, agrega una columna 'index_original' que indica el índice original de cada muestra
    antes de ser filtrada.

    Parámetros:
        df : pandas.DataFrame
            DataFrame con columnas 'gps_lat' y 'gps_lng'.

    Retorna:
        pandas.DataFrame con las muestras duplicadas eliminadas y columna 'index_original'.
    """
    if not {'gps_lat', 'gps_lng'}.issubset(df.columns):
        raise ValueError("El DataFrame debe contener las columnas 'gps_lat' y 'gps_lng'.")

    # Guardar el índice original
    df = df.copy()
    df['index_original'] = df.index

    # Detectar cambios en lat o lng
    cambio_lat = df['gps_lat'] != df['gps_lat'].shift()
    cambio_lng = df['gps_lng'] != df['gps_lng'].shift()
    cambio = cambio_lat | cambio_lng

    # Asegurar conservar la primera fila
    cambio.iloc[0] = True

    # Filtrar y devolver invertido
    df_filtrado = df[cambio].copy()

    return df_filtrado

def confirmar_grafo(latitud, longitud, numero_grafo,carpeta_grafo):
    """
    Confirma si un par de coordenadas está dentro del área de un grafo específico.

    Parámetros:
    - latitud: Coordenada de latitud.
    - longitud: Coordenada de longitud.
    - numero_grafo: Número de grafo a confirmar.

    Devuelve:
    - 1 si el par de coordenadas está dentro del área del grafo, 0 en caso contrario.
    """
    # Ruta del directorio donde se almacenan los archivos de grafos.
    directorio_a_buscar = carpeta_grafo  # Reemplaza con la ruta de tu carpeta

    # Prefijo que se busca en los nombres de archivo.
    prefijo_a_buscar = 'segN' + str(numero_grafo) + 'pos'  # Reemplaza con el prefijo que deseas buscar

    # Busca archivos en el directorio con el prefijo proporcionado.
    archivos_encontrados = buscar_archivos_por_prefijo(directorio_a_buscar, prefijo_a_buscar)

    # Extrae las coordenadas del nombre del archivo.
    posicion_corte = str(archivos_encontrados).find('pos')
    nombre_reducido = (str(archivos_encontrados)[posicion_corte + 3:-10])
    posicion = [-1]
    
    # Encuentra las posiciones de los delimitadores '&' en el nombre del archivo.
    for i in range(len(nombre_reducido)):
        if nombre_reducido[i] == '&':
            posicion.append(i)
    posicion.append(-1)
    
    # Verifica si se encuentran las cinco coordenadas necesarias para definir el área.
    if len(posicion) == 5:
        lat_izquierda = float(nombre_reducido[posicion[0] + 1:posicion[1]])
        lat_derecha = float(nombre_reducido[posicion[1] + 1:posicion[2]])
        lon_izquierda = float(nombre_reducido[posicion[2] + 1:posicion[3]])
        lon_derecha = float(nombre_reducido[posicion[3] + 1:posicion[4]])
    else:
        return 0
    
    # Comprueba si las coordenadas dadas están dentro del área del grafo.
    if ((lat_izquierda > latitud) and (lat_derecha < latitud) and (lon_izquierda < longitud) and (lon_derecha > longitud)):
        return 1
    else:
        return 0
        
def determinar_grafo(latitud, longitud):
    """
    Determina el número de grafo para un par de coordenadas de latitud y longitud.

    Parámetros:
    - latitud: Coordenada de latitud.
    - longitud: Coordenada de longitud.

    Devuelve:
    - Número de grafo asignado basado en la ubicación proporcionada.
    """
    # Coordenadas de referencia para el primer grafo (esquina superior izquierda).
    lat_original = 12.461201  # Latitud (Y)
    lon_original = -79.457520  # Longitud (X)

    # Tamaño de cada celda en términos de latitud y longitud.
    intervalo_lon = 0.309800875
    intervalo_lat = 0.4102147

    # Calcula la posición del grafo en términos de filas (latitud) y columnas (longitud).
    posicion_grafo_y = int(abs(lat_original - latitud) / intervalo_lat)
    posicion_grafo_x = int(abs(lon_original - longitud) / intervalo_lon)

    # Calcula el número de grafo basado en la posición.
    numero_grafo = posicion_grafo_y * 40 + posicion_grafo_x

    return numero_grafo

def buscar_archivos_por_prefijo(directorio, prefijo):
    """
    Busca archivos en un directorio con un prefijo específico.

    Parámetros:
    - directorio: Ruta del directorio en el que se realizará la búsqueda.
    - prefijo: Prefijo que deben tener los archivos buscados.

    Devuelve:
    - Lista de rutas de archivos encontrados que tienen el prefijo dado.
    """
    archivos_encontrados = []

    # Itera sobre todos los archivos en el directorio y sus subdirectorios.
    for root, dirs, files in os.walk(directorio):
        for file in files:
            # Comprueba si el nombre del archivo comienza con el prefijo dado.
            if file.startswith(prefijo):
                archivos_encontrados.append(os.path.join(root, file))

    return archivos_encontrados


def calcular_angulo(p1, p2):
    """
    Calcula el ángulo en grados entre dos puntos geográficos (lat, lon),
    con respecto al norte (0°), en sentido horario.
    
    Parámetros:
    - p1, p2: tuplas (lat, lon)

    Retorna:
    - ángulo en grados entre p1 y p2
    """
    dy = p2[0] - p1[0]
    dx = p2[1] - p1[1]
    angulo_rad = math.atan2(dx, dy)
    angulo_deg = math.degrees(angulo_rad)
    return (angulo_deg + 360) % 360


def obtener_angulos_edge(G, u, v):
    """
    Calcula los ángulos de entrada y salida de una arista (edge) dirigida de u a v.

    Si la arista tiene geometría, usa los primeros y últimos puntos de la línea.
    Si no tiene geometría, calcula el ángulo entre los nodos u y v.

    Parámetros:
    - G: DiGraph de osmnx
    - u: nodo origen
    - v: nodo destino

    Retorna:
    - (angulo_entrada, angulo_salida): en grados [0, 360)
    """
    if not G.has_edge(u, v):
        raise ValueError("La arista no existe en el grafo.")

    edge_data = G.get_edge_data(u, v)[0]  # Primer edge si hay múltiples

    if 'geometry' in edge_data:
        coords = list(edge_data['geometry'].coords)
        if len(coords) >= 2:
            p1 = coords[0][::-1]         # primer punto (lat, lon)
            p2 = coords[1][::-1]         # segundo punto
            p3 = coords[-2][::-1]        # penúltimo punto
            p4 = coords[-1][::-1]        # último punto
        else:
            # Geometría inválida, usar nodos
            p1 = p3 = (G.nodes[u]['y'], G.nodes[u]['x'])
            p2 = p4 = (G.nodes[v]['y'], G.nodes[v]['x'])
    else:
        # Sin geometría: usar nodos directamente
        p1 = p3 = (G.nodes[u]['y'], G.nodes[u]['x'])
        p2 = p4 = (G.nodes[v]['y'], G.nodes[v]['x'])

    angulo_entrada = calcular_angulo(p1, p2)
    angulo_salida = calcular_angulo(p3, p4)
    return angulo_entrada, angulo_salida

def edges_conectados(G, u, v):
    """
    Retorna todos los edges conectados al segmento (u, v),
    incluyendo:
    - Entradas hacia u: (x, u) y (u, x)
    - Salidas desde v: (v, y) y (y, v)
    Excluye siempre el segmento original y su inverso.

    Parámetros:
    - G: DiGraph de osmnx
    - u: nodo de origen del edge base
    - v: nodo de destino del edge base

    Retorna:
    - edges_entrada: lista [(origen, destino, key)] hacia u
    - edges_salida: lista [(origen, destino, key)] desde v
    """
    edges_entrada = []
    edges_salida = []

    # Entradas hacia u
    for predecesor in G.predecessors(u):
        if predecesor != v:
            for key in G[predecesor][u]:
                edges_entrada.append((predecesor, u, key))

    for sucesor in G.successors(u):
        if sucesor != v:
            for key in G[u][sucesor]:
                edges_entrada.append((u, sucesor, key))

    # Salidas desde v
    for sucesor in G.successors(v):
        if sucesor != u:
            for key in G[v][sucesor]:
                edges_salida.append((v, sucesor, key))

    for predecesor in G.predecessors(v):
        if predecesor != u:
            for key in G[predecesor][v]:
                edges_salida.append((predecesor, v, key))

    return edges_entrada, edges_salida

def caminos_hasta_distanciav2(G, u, v, distancia_maxima, key_inicial=0):
    """
    Explora caminos desde (u,v,key_inicial), expandiendo ramas acumulando distancia hasta distancia_maxima.
    Retorna un diccionario {nivel: [(v1, v2, key, length, nueva_distancia, valor)]} sin segmentos repetidos,
    donde 'valor' es 0 o 1 según reglas de dirección.
    """
    from collections import defaultdict, deque, OrderedDict

    niveles_dict = defaultdict(list)
    segmentos_por_nivel = defaultdict(set)

    cola = deque()
    cola.append(([(u, v, key_inicial, 0)], 0))  # camino, distancia
    segmentos_por_nivel[0].add(tuple(sorted((u, v))))
    niveles_dict[0].append((u, v, key_inicial, 0, 0, 0))  # Inicial siempre con valor 0

    while cola:
        camino, distancia_actual = cola.popleft()
        u_actual, v_actual, key_actual, _ = camino[-1]

        adyacentes = edges_conectados(G, u_actual, v_actual)
        siguientes = adyacentes[0] + adyacentes[1]

        for (v1, v2, key) in siguientes:
            segmento_ordenado = tuple(sorted((v1, v2)))
            if any(segmento_ordenado == tuple(sorted((x, y))) for (x, y, k, _) in camino):
                continue  # Evitar ciclos

            length = G[v1][v2][key].get('length', 0)
            nueva_distancia = distancia_actual + length
            nuevo_camino = camino + [(v1, v2, key, length)]
            nivel_nuevo = len(nuevo_camino) - 1

            if segmento_ordenado in segmentos_por_nivel[nivel_nuevo]:
                continue

            # Determinar el valor según origen o destino
            if nivel_nuevo == 1:
                if u in (v1, v2):
                    valor = 0  # Nivel 1 saliendo de u
                elif v in (v1, v2):
                    valor = 1  # Nivel 1 llegando a v
                else:
                    valor = 0  # Fallback
            elif nivel_nuevo >= 2:
                # Revisar primer segmento después del inicial
                primer_v1, primer_v2, _, _ = nuevo_camino[1]
                if u in (primer_v1, primer_v2):
                    valor = 0  # Nivel >=2 que sale desde u
                else:
                    valor = 1  # Nivel >=2 que se origina después del inicial
            else:
                valor = 0  # Nivel 0 inicial

            niveles_dict[nivel_nuevo].append((v1, v2, key, length, nueva_distancia, valor))
            segmentos_por_nivel[nivel_nuevo].add(segmento_ordenado)

            if nueva_distancia < distancia_maxima:
                cola.append((nuevo_camino, nueva_distancia))

    niveles_ordenados = OrderedDict()
    for nivel in sorted(niveles_dict.keys()):
        niveles_ordenados[nivel] = niveles_dict[nivel]

    return dict(niveles_ordenados)


def ajustar_heading_y_filtrar(df):
    """
    Ajusta la columna 'gps_heading' de [0, 360) a [-180, 180) y aplica un filtro promediador de orden 8.

    Args:
        df (pd.DataFrame): DataFrame con columna 'gps_heading'

    Returns:
        pd.DataFrame: DataFrame con nueva columna 'gps_heading_filtrado'
    """
    # Conversión de 0-360 a -180 a 180
    df = df.copy()
    df['gps_heading_180'] = ((df['gps_heading'] + 180) % 360) - 180

    # Filtro promediador de orden 8
    df['gps_heading_filtrado'] = df['gps_heading_180'].rolling(window=18, min_periods=1, center=False).mean()

    return df

def diferencia_angular(angulo1, angulo2):
    """
    Calcula la diferencia mínima en grados entre dos ángulos (0 a 360°).
    
    Args:
        angulo1 (float): Primer ángulo en grados.
        angulo2 (float): Segundo ángulo en grados.
        
    Returns:
        float: Diferencia mínima en grados (0 a 180°).
    """
    diferencia = abs(angulo1 - angulo2) % 360
    if diferencia > 180:
        diferencia = 360 - diferencia
    return diferencia


    
def normalizar_segmento(G, u, v, key):
    """
    Retorna el identificador normalizado de un segmento.

    Si el segmento es unidireccional, retorna (u, v, key) como está.
    Si es bidireccional, retorna (min(u, v), max(u, v), key).

    Parámetros:
        G   : networkx.MultiDiGraph
            Grafo que contiene los segmentos.
        u   : int
            Nodo origen.
        v   : int
            Nodo destino.
        key : int
            Clave del segmento.

    Retorna:
        tuple: Segmento normalizado.

    Lanza:
        KeyError: Si el segmento (u, v, key) no existe en el grafo.
    """
    try:
        edge_data = G[u][v][key]
    except KeyError:
        raise KeyError(f"El segmento ({u}, {v}, {key}) no se encuentra en el grafo.")

    es_oneway = edge_data.get('oneway', False) in [True, 'yes', '1']

    if es_oneway:
        return (u, v, key)
    else:
        return (min(u, v), max(u, v), key)
    

def distancia_euclidiana_acumulada(puntos):
    """
    Calcula la distancia euclidiana acumulada entre una secuencia de puntos 2D.
    Convierte los valores de grados a metros usando un factor aproximado para latitud.

    Parámetros:
        puntos : list[tuple[float, float]]
            Lista de coordenadas (x, y) o (lat, lng).

    Retorna:
        list[float]
            Lista con la distancia acumulada desde el primer punto hasta cada punto.
    """
    acumuladas = [0]
    acumulado = 0
    for i in range(1, len(puntos)):
        x0, y0 = puntos[i-1]
        x1, y1 = puntos[i]
        distancia = np.sqrt((x1 - x0)**2 + (y1 - y0)**2) * 111.32 * 1000  # grados a metros
        acumulado += distancia
        acumuladas.append(acumulado)
    return acumuladas

def punto_en_recta_geografica_simple(lat1, lon1, lat2, lon2, distancia_m, distancia_total_m):
    """
    Calcula un punto sobre la recta entre dos coordenadas geográficas,
    ubicado a una distancia dada desde el primer punto. Usa una conversión
    fija de grados a metros (111.32 km por grado para lat y lon), y recibe
    como parámetro la distancia total entre los dos puntos.

    Parámetros:
        lat1, lon1 : float
            Coordenadas del punto inicial (grados).
        lat2, lon2 : float
            Coordenadas del punto final (grados).
        distancia_m : float
            Distancia desde el punto inicial hasta el punto buscado (en metros).
        distancia_total_m : float
            Distancia total entre lat1/lon1 y lat2/lon2 (en metros).

    Retorna:
        (lat, lon) : tuple[float, float]
            Coordenadas del punto a la distancia indicada sobre la recta.
    """
    if distancia_total_m == 0:
        raise ValueError("La distancia total no puede ser cero.")
    
    # Diferencias en grados
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Fracción recorrida
    t = distancia_m / distancia_total_m

    # Interpolación
    lat_interpolado = lat1 + dlat * t
    lon_interpolado = lon1 + dlon * t

    return lon_interpolado,lat_interpolado 

def hash_segmento(u: int, v: int, key: int) -> int:
    """
    Hash de segmento que es insensible al orden de u y v (para vías bidireccionales).
    """
    u_, v_ = sorted((u, v))  # Ordena los nodos para garantizar consistencia
    h = (u_ * 2654435761) ^ (v_ * 40503) ^ (key * 97)
    return h % (2**64)

def timestamp_a_iso8601(timestamp):
    """
    Convierte un timestamp en milisegundos a una cadena con formato ISO 8601.
    """
    try:
        # Convertir de milisegundos a segundos
        timestamp_segundos = timestamp / 1000
        return datetime.fromtimestamp(timestamp_segundos).isoformat()
    except Exception as e:
        print(f"[ERROR] Timestamp inválido: {timestamp} → {e}")
        return None

def buscar_intervalo(valor, intervalos):
    """
    Busca en qué intervalo se encuentra un valor dado.

    Parámetros:
    - valor (int): el valor a buscar.
    - intervalos (list of tuple): lista de tuplas (inicio, fin).

    Retorna:
    - int: posición (índice) del intervalo donde se encuentra el valor.
    - None: si no se encuentra en ningún intervalo.
    """
    for i, (inicio, fin) in enumerate(intervalos):
        if inicio <= valor <= fin:
            return i
    return None
