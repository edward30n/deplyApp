import numpy as np
import pandas as pd
from scipy.signal import resample, resample_poly, cwt, find_peaks, filtfilt
from scipy.ndimage import maximum_filter, generate_binary_structure
import matplotlib.pyplot as plt

# Compatibilidad: algunos entornos SciPy 3.12+ no exponen morlet2 correctamente
try:
    from scipy.signal import morlet2  # type: ignore
except Exception:
    # Fallback aproximado de morlet2 para permitir pruebas locales
    def morlet2(M, s, w: float = 5.0, complete: bool = False):  # type: ignore
        t = np.linspace(- (M - 1) / 2.0, (M - 1) / 2.0, M)
        wave = (np.pi ** (-0.25)) * np.exp(1j * w * t / s) * np.exp(-0.5 * (t / s) ** 2)
        if complete:
            wave = wave - wave.mean()
        return wave


def reflejar_indices_por_umbral(arreglo, fs, m):
    """
    Encuentra para cada columna (1:m/2) el índice donde el arreglo decreciente
    cae por debajo de fs*1.55/col y luego refleja los valores obtenidos alrededor del centro.

    Parámetros:
        arreglo : ndarray (1D)
            Vector decreciente de longitud n.
        fs : float
            Frecuencia de muestreo.
        m : int
            Longitud del vector de salida.

    Retorna:
        resultado : ndarray (1D)
            Vector de longitud m con reflejo central de los índices obtenidos.
    """
    arreglo = np.asarray(arreglo)
    n = arreglo.shape[0]
    mitad = m // 2

    if m % 2 == 0:
        centros = np.arange(1, mitad + 1)  # 1 a mitad (inclusive)
    else:
        centros = np.arange(1, mitad + 2)  # 1 a mitad+1 (inclusive)

    # Calculamos los umbrales para cada posición
    umbrales = fs * 1.55 / centros

    # Expandimos arreglo para comparar todos los umbrales a la vez
    comp = arreglo[:, None] < umbrales  # Shape: (n, len(centros))

    # Buscamos la primera ocurrencia donde arreglo < umbral en cada columna
    idxs = np.argmax(comp, axis=0)
    idxs[~np.any(comp, axis=0)] = n + 1  # Si ningún valor cumple la condición

    resultado = np.zeros(m, dtype=int)
    resultado[:len(idxs)] = idxs

    # Reflejar el resultado
    if m % 2 == 0:
        resultado[mitad:] = resultado[:mitad][::-1]
    else:
        resultado[mitad+1:] = resultado[:mitad][::-1]

    return resultado

def poner_ceros_por_fila(M, limites):
    """
    Pone en cero las posiciones de cada columna desde un índice fila dado hasta el final.

    Parámetros:
        M : ndarray (n x m)
            Matriz de entrada.
        limites : ndarray (m,)
            Vector que indica desde qué fila en adelante se deben poner en cero
            los valores de cada columna.

    Retorna:
        M_filtrada : ndarray (n x m)
            Matriz con ceros aplicados por columna según el límite.
    """
    M = np.asarray(M)
    limites = np.asarray(limites)
    n, m = M.shape

    # Crear una matriz de índices de fila por columna (n x m)
    filas = np.arange(n).reshape(-1, 1)  # shape (n, 1)
    limites_expand = limites.reshape(1, -1)  # shape (1, m)

    # Crear máscara: True donde fila < límite (es decir, mantener el valor)
    mascara = filas < limites_expand

    # Aplicar la máscara
    M_filtrada = M * mascara

    return M_filtrada

def encontrar_maximos_locales(M, n):
    """
    Encuentra los n máximos locales más altos en una matriz 2D.

    Parámetros:
        M : ndarray (2D)
            Matriz de entrada.
        n : int
            Número de máximos locales que se desean retornar.

    Retorna:
        posiciones : ndarray (n x 3)
            Cada fila contiene [fila, columna, valor_del_pico]
    """
    M = np.asarray(M)
    
    # Crear una estructura de vecindad para considerar 8 vecinos
    estructura = generate_binary_structure(2, 2)

    # Encontrar máximos locales: el valor debe ser igual al máximo en su vecindad
    local_max = (maximum_filter(M, footprint=estructura, mode='constant') == M)

    # Ignorar los ceros si M tiene valores planos o borde
    local_max[M == 0] = False

    # Obtener índices de máximos locales
    coords = np.argwhere(local_max)
    
    # Obtener valores en esas posiciones
    valores = M[local_max]

    # Si se piden más picos que los disponibles, ajustar
    n = min(n, len(valores))

    # Ordenar y tomar los n mayores
    indices_top = np.argsort(valores)[-n:][::-1]  # top n descendente

    # Posiciones y valores
    posiciones = np.hstack((coords[indices_top], valores[indices_top, np.newaxis]))

    return posiciones

def filtrar_por_umbral(tabla, umbral):
    """
    Filtra las filas de una matriz numérica (n x 3) con base en la tercera columna.

    Parámetros:
        tabla : ndarray
            Matriz numérica (n x 3).
        umbral : float
            Umbral para comparar con la tercera columna.

    Retorna:
        tabla_filtrada : ndarray
            Submatriz con filas cuyo valor en la columna 3 es > umbral.
    """
    tabla = np.asarray(tabla)

    # Validar forma
    if tabla.ndim != 2 or tabla.shape[1] != 3:
        raise ValueError("La matriz debe tener exactamente 3 columnas.")

    # Filtrar filas donde la tercera columna es mayor al umbral
    idx = tabla[:, 2] > umbral
    tabla_filtrada = tabla[idx, :]

    return tabla_filtrada

def mapear_indices(matriz, arreglo1, arreglo2):
    """
    MAPEAR_INDICES Reemplaza los dos primeros elementos de cada fila de una matriz
    utilizando dos arreglos de mapeo (lookup).

    Parámetros:
        matriz   - ndarray de forma (n, 3), con índices enteros en las dos primeras columnas.
        arreglo1 - ndarray o lista, usado para mapear los índices de la primera columna.
        arreglo2 - ndarray o lista, usado para mapear los índices de la segunda columna.

    Retorna:
        salida   - ndarray de forma (n, 3), con los dos primeros elementos mapeados.
    """

    matriz = np.asarray(matriz)
    arreglo1 = np.asarray(arreglo1)
    arreglo2 = np.asarray(arreglo2)

    if matriz.shape[1] != 3:
        raise ValueError("La matriz debe tener exactamente 3 columnas.")

    salida = matriz.copy()
    salida[:, 0] = arreglo1[matriz[:, 0].astype(int)]
    salida[:, 1] = arreglo2[matriz[:, 1].astype(int)]

    return salida

def determinar_hueco(puntos, umbral_tiempo):
    """
    Filtra una colección de puntos del giroscopio eliminando registros con tiempos cercanos
    (menores al umbral_tiempo) al primero seleccionado, priorizando los primeros en aparecer.

    Parámetros:
        puntos : ndarray de forma (n, 3) con columnas [frecuencia, tiempo, valor]
        umbral_tiempo : float, tiempo mínimo de separación entre puntos seleccionados

    Retorna:
        lista_dict : lista de diccionarios con claves 'frecuencia', 'tiempo', 'valor'
    """
    df = pd.DataFrame(puntos, columns=["frecuencia", "tiempo", "valor"])
    df = df.sort_values("tiempo").reset_index(drop=True)

    seleccionados = []
    tiempos = df["tiempo"].to_numpy()
    descartados = np.zeros(len(df), dtype=bool)

    for i in range(len(df)):
        if not descartados[i]:
            seleccionados.append(i)
            # Marcar como descartados todos los posteriores dentro del umbral
            diferencia_tiempo = tiempos - tiempos[i]
            descartados |= (diferencia_tiempo >= 0) & (diferencia_tiempo < umbral_tiempo)

    df_filtrado = df.iloc[seleccionados]
    return df_filtrado.to_dict(orient='records')

def encontar_huecos_segmento(vector,fs,frecuencia_menor,frecuencia_mayor,umbral_magnitud,umbral_tiempo,factor_velocidad):
    #variables de ajuse de la wavelet para parecerse a la de matlab
    constante = 0.4652830842
    exponente = -0.069314718
    w = 6
    
    #se realizan variables de uso general
    cantidad_puntos = len(vector) #tamaño de la muestra

    #se normaliza con el valor promedio de la señal
    vector = vector/(np.median(np.abs(vector)*factor_velocidad))
    frecuencia_minima = fs/cantidad_puntos #frecuencia mas pequeña que se puede medir
    tiempo_total = cantidad_puntos*(1/fs) #tiempo total de la muestra
    tamano_conteo = int((np.log(frecuencia_minima*(10/3)/(fs*constante))/exponente)+1) #tamaño del arreglo de tiempo
    
    #se generan arreglos simples para luego operarlos como x de la diferentes funciones
    arreglo_recorrido = np.arange(1,tamano_conteo+1)
    
    #se evalua el arreglo de x para obtener la frecuencia
    frecuencia = constante*fs*np.exp(exponente*arreglo_recorrido)
    
    #se evalua el arreglo de x para obtener la anchura necesaria para la wavelet
    widths = w*fs/(2*np.pi*frecuencia)
    
    #se evalua el arreglo de x para conocer la caida de la energía 
    caida_energia = np.exp((exponente/2)*arreglo_recorrido)
    
    #se calcula la wavelet
    cwt_result = cwt(vector, morlet2, widths, w=w)
    
    #se aplica la caida de energía para conservar la energía de la señal
    new_cwt = np.abs(cwt_result)*caida_energia[:,np.newaxis]
    
    #se generan los arreglos para formar el COI
    referencia_recorte = reflejar_indices_por_umbral(frecuencia,fs,cantidad_puntos)
    
    #se aplica el COI a la wavelet
    cwt_filtrada = poner_ceros_por_fila(new_cwt,referencia_recorte)
    
    vector_diferencia_minimo = np.abs(frecuencia_menor - frecuencia)
    vector_diferencia_maximo = np.abs(frecuencia_mayor - frecuencia)
    indice_minimo = np.argmin(vector_diferencia_minimo) + 1
    indice_maximo = np.argmin(vector_diferencia_maximo)
    
    cwt_recortada =cwt_filtrada[indice_maximo:indice_minimo,:]
    maximos_locales = encontrar_maximos_locales(np.abs(cwt_recortada),20)
    maximos_locales_filtrado = filtrar_por_umbral(maximos_locales, umbral_magnitud)
    tiempo = np.linspace(0,tiempo_total,cantidad_puntos)
    puntos = mapear_indices(maximos_locales_filtrado,frecuencia,tiempo)
    huecos_detectados = determinar_hueco(puntos,umbral_tiempo)
    return huecos_detectados

def determinar_hueco(puntos, umbral_tiempo):
    """
    Filtra una colección de puntos del giroscopio eliminando registros con tiempos cercanos
    (menores al umbral_tiempo) al primero seleccionado, priorizando los primeros en aparecer.

    Parámetros:
        puntos : ndarray de forma (n, 3) con columnas [frecuencia, tiempo, valor]
        umbral_tiempo : float, tiempo mínimo de separación entre puntos seleccionados

    Retorna:
        lista_dict : lista de diccionarios con claves 'frecuencia', 'tiempo', 'valor'
    """
    df = pd.DataFrame(puntos, columns=["frecuencia", "tiempo", "valor"])
    df = df.sort_values("tiempo").reset_index(drop=True)

    seleccionados = []
    tiempos = df["tiempo"].to_numpy()
    descartados = np.zeros(len(df), dtype=bool)

    for i in range(len(df)):
        if not descartados[i]:
            seleccionados.append(i)
            # Marcar como descartados todos los posteriores dentro del umbral
            diferencia_tiempo = tiempos - tiempos[i]
            descartados |= (diferencia_tiempo >= 0) & (diferencia_tiempo < umbral_tiempo)

    df_filtrado = df.iloc[seleccionados]
    return df_filtrado.to_dict(orient='records')

def encontrar_segmentos_continuos(arr):
    if not arr:
        return []

    segmentos = []
    inicio = fin = arr[0]

    for num in arr[1:]:
        if num == fin + 1:
            # Sigue el segmento
            fin = num
        else:
            # Segmento terminado
            segmentos.append((inicio, fin))
            inicio = fin = num

    # Agrega el último segmento
    segmentos.append((inicio, fin))

    return segmentos

