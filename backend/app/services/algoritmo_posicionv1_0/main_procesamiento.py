#se traen todas las librerias necesarias
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from filterpy.kalman import KalmanFilter
import osmnx as ox
import networkx as nx
import math
from . import algoritmos_posicinamiento as ap
from . import algoritmos_busqueda as ab
from . import algoritmos_senales as algs
import json
from scipy.signal import filtfilt,firwin,lfilter,welch
from scipy.signal import resample
from sklearn.neighbors import BallTree
import joblib
import time
import pickle
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import traceback

#variables base
EARTH_R = 6371000.0

#clase con los datos de procesamiento 
class DatosProcesamiento:
    def __init__(self):
        # Variables globales o de contexto
        self.G = None
        self.tree = None
        self.mids = None
        self.ids = None
        self.latitud = None
        self.longitud = None
        self.numero_grafo = None
        self.G_exist = False
        self.carpeta_grafos = None
        self.carpeta_grafos_comprimidos = None
        self.L = 0.0003
        self.id_edge = None
        self.info_edge = None
        self.coordenadas_segmento = None
        self.coordenadas_subsegmento = None
        self.longitud_subsegmento = None
        self.posicion_subsegmento = None
        self.segmento_encontrado = False
        self.primera_muestra = False
        self.velocidad = None
        self.heading = None
        self.cambio_segmento = False #variable que indica cuando se cambio el segmento
        self.indice_subsegmento = 0
        self.segmento_maximo = 100
        
###############################################################
#-----------------SUB FUNCIONES MAIN -------------------------#

#se extraen los puntos GPS del mapa
def adquirir_latitud_longitud(df_gps,datos,index_GPS):
    
    datos.latitud = df_gps['gps_lat'].iloc[index_GPS]
    datos.longitud = df_gps['gps_lng'].iloc[index_GPS]
    datos.velocidad = df_gps['gps_speed'].iloc[index_GPS]
    datos.heading = df_gps['gps_heading'].iloc[index_GPS]


def procesamiento_mapa_simple(datos):
    num_grafo = ap.determinar_grafo(datos.latitud, datos.longitud)
    if datos.numero_grafo != num_grafo:
    
        grafo_nombre = ap.buscar_archivos_por_prefijo(datos.carpeta_grafos, 'segN' + str(num_grafo) + 'pos')
        datos.numero_grafo = num_grafo
        with open(str(grafo_nombre[0]), "rb") as f:
            datos.G = pickle.load(f)

        datos.G_exist = True
        datos.tree = joblib.load(datos.carpeta_grafos_comprimidos + '/balltree_model_N' + str(num_grafo) + ".pkl")
        datos_comprimidos_grafo = pd.read_csv(datos.carpeta_grafos_comprimidos + '/mids_ids_N' + str(num_grafo) + ".csv")
        datos.mids = datos_comprimidos_grafo[["lat_rad", "lon_rad"]].to_numpy().tolist()
        datos.ids = list(zip(datos_comprimidos_grafo["u"], datos_comprimidos_grafo["v"], datos_comprimidos_grafo["k"]))


def ubicar_muestra_grafov2(datos):
    datos.segmento_encontrado = False
    
    if not datos.primera_muestra:

        latr, lonr = math.radians(datos.latitud), math.radians(datos.longitud)
        _, idxs = datos.tree.query([[latr, lonr]], k=32)
        
        cands = [datos.ids[i] for i in idxs[0]]

        G_cands = nx.MultiDiGraph()
        G_cands.graph["crs"] = datos.G.graph.get("crs", "EPSG:4326")  

        for (u, v, k) in cands:
            if (u, v, k) in datos.G.edges:
                # Copiamos la información de la arista desde el grafo original
                edge_data = datos.G.edges[(u, v, k)]
                G_cands.add_edge(u, v, key=k, **edge_data)
                # asegurarnos de incluir también los nodos
                if u in datos.G.nodes:
                    G_cands.add_node(u, **datos.G.nodes[u])
                if v in datos.G.nodes:
                    G_cands.add_node(v, **datos.G.nodes[v])

        datos.id_edge = ox.nearest_edges(G_cands, X=datos.longitud, Y=datos.latitud)
        datos.info_edge = datos.G.edges[datos.id_edge]
        datos.coordenadas_segmento = ap.obtener_coordenadas_segmento(datos.G,datos.id_edge,datos.info_edge)
        datos.primera_muestra = True
        datos.segmento_encontrado = True
        datos.cambio_segmento = True


        
    #después de la primera muestra se determina el recorrido a partir de ese punto
    else:

        #ahora se determina si el segmento se encuentra dentro del edge actual o en caso contrario cambio
        
        #para ello se utiliza la función para extraer las coordenadas del segmento
        datos.coordenadas_segmento = ap.obtener_coordenadas_segmento(datos.G,datos.id_edge,datos.info_edge)
        
        #ahora se analiza con la funión para determinar el area
        poligono = ap.generar_poligono_segmento_lonlat(datos.coordenadas_segmento,datos.L)
        
        #mirar si el punto se encuentra dentro del poligono
        point_in_edge = ap.punto_en_poligono(poligono,datos.longitud,datos.latitud)
        
        
        if not point_in_edge:
            #como se comprobo que no se encontraba adentro se va a cambiar el segmento
            datos.cambio_segmento = True

            #como el segmento no esta dentro, se extrae los segmentos cercanos
            segmentos_anexos = ap.caminos_hasta_distanciav2(datos.G,datos.id_edge[0],datos.id_edge[1],50)

            
                
            #información del segmento base
            angulos_segmento_original = ap.obtener_angulos_edge(datos.G,datos.id_edge[0],datos.id_edge[1])
            posibilidades_segmento = []
            
            for i in range(1,len(segmentos_anexos)):
                for j in range(len(segmentos_anexos[i])):
    
                    id_segmento = (segmentos_anexos[i][j][0],segmentos_anexos[i][j][1],0)
                    info_segmento = datos.G.edges[id_segmento]
                    
                    #para ello se utiliza la función para extraer las coordenadas del segmento
                    coordenadas_edge = ap.obtener_coordenadas_segmento(datos.G,id_segmento,info_segmento)
                    #if( datos.variable_basura_borrar_porfavor == 20 or datos.variable_basura_borrar_porfavor == 53):
                    #    print(coordenadas_edge)
                    #ahora se analiza con la funión para determinar el area
                    poligono = ap.generar_poligono_segmento_lonlat(coordenadas_edge,datos.L)
                    
                    #mirar si el punto se encuentra dentro del poligono
                    point_in_edge = ap.punto_en_poligono(poligono,datos.longitud,datos.latitud)

                    if(point_in_edge):
                        #se guarda la información del segmento si se cumplen las condiciones
                        datos.segmento_encontrado = True
                        registro = {
                            'nivel':i,
                            'id': id_segmento,
                            'info': info_segmento,
                            'coordenadas': coordenadas_edge,
                            'distancia': ap.distancia_segmento(coordenadas_edge,datos.longitud,datos.latitud),
                            'direccion': ap.obtener_angulos_edge(datos.G,id_segmento[0],id_segmento[1]),
                            'nodo_origen': segmentos_anexos[i][j][5]
                            
                        }
                        posibilidades_segmento.append(registro)

            #después de recorrer todas las areas se va a realizar los filtros pertinentes 

            #se va a cambiar la escala de los diversos
            mayor_peso = 0
            if(len(posibilidades_segmento) > 0):
                for i in range(len(posibilidades_segmento)):
                    
                    #se determina el peso por el nivel del segmento
                    peso_nivel = 1/posibilidades_segmento[i]['nivel']

                    #se determina el peso por la distancia del punto al segmento
                    peso_distancia = 1-(posibilidades_segmento[i]['distancia']/300)
    
                    #se filtra si se analiza con la dirección del segmento de salida o de entrada
                    if(posibilidades_segmento[i]['nodo_origen']):
                        diferencia_angulo = ap.diferencia_angular(posibilidades_segmento[i]['direccion'][0],angulos_segmento_original[1])    
                    else:
                        diferencia_angulo = ap.diferencia_angular(posibilidades_segmento[i]['direccion'][0],angulos_segmento_original[0])

                    #solamente se va a dar peso en caso que el segmento tenga unica dirección
                    
                    
                    peso_direccion = 1-(diferencia_angulo/180)

                    angulo_180 = posibilidades_segmento[i]['direccion'][0]
                    
                    peso_angulo = 1-(abs(ap.diferencia_angular(angulo_180,datos.heading))/180)


                
                    peso_final = 0.8*peso_direccion+0.3*peso_nivel+0.1*peso_distancia+0.6*peso_angulo
                    

                    if(peso_final > mayor_peso):
                        mayor_peso = peso_final
                        datos.id_edge = posibilidades_segmento[i]['id']
                        datos.info_edge = posibilidades_segmento[i]['info']
                        datos.coordenadas_segmento = posibilidades_segmento[i]['coordenadas']
                        datos.segmento_encontrado = True    

        #en caso que el segmento este adentro del anterior no se cambian los datos de la estructura        
        else:
            datos.segmento_encontrado = True
            datos.cambio_segmento = False
            
        #en caso que todos los proceso fueron incapaces de encontrar un segmento se utiliza la función pesada
        if not datos.segmento_encontrado:
            #trabajando aca 
            #
            
            latr, lonr = math.radians(datos.latitud), math.radians(datos.longitud)
            radio_m = 300
            radio_rad = radio_m / EARTH_R
            idxs = datos.tree.query_radius([[latr, lonr]], r=radio_rad)[0]
            if len(idxs) == 0:
                _, idxs = datos.tree.query([[latr, lonr]], k=32)
                idxs = idxs[0]

            cands = [datos.ids[i] for i in idxs]
            G_cands = nx.MultiDiGraph()
            G_cands.graph["crs"] = datos.G.graph.get("crs", "EPSG:4326")  

            for (u, v, k) in cands:
                if (u, v, k) in datos.G.edges:
                    # Copiamos la información de la arista desde el grafo original
                    edge_data = datos.G.edges[(u, v, k)]
                    G_cands.add_edge(u, v, key=k, **edge_data)
                    # asegurarnos de incluir también los nodos
                    if u in datos.G.nodes:
                        G_cands.add_node(u, **datos.G.nodes[u])
                    if v in datos.G.nodes:
                        G_cands.add_node(v, **datos.G.nodes[v])
            
            segmento = ox.nearest_edges(G_cands, X=datos.longitud, Y=datos.latitud)
            datos.id_edge = segmento
            datos.info_edge = datos.G.edges[datos.id_edge]
            datos.coordenadas_segmento = ap.obtener_coordenadas_segmento(datos.G,datos.id_edge,datos.info_edge)
            datos.primera_muestra = True
            datos.segmento_encontrado = True
            
    #se guarda el registro del punto dentro del segmento



def colocar_puntos_grafo(datos,latitud,longitud):
    resultado = ap.proyectar_segmento(datos.coordenadas_segmento,latitud,longitud)
    return resultado

def segmentar_grafo(datos):
        
    #se comprueba si el segmento es superior a los 60 metros
    if(datos.info_edge['length'] > datos.segmento_maximo):

        #en caso que si se especifa las divisiones y el tamaño de esas divisiones
        cantidad_divisiones = int(datos.info_edge['length']/datos.segmento_maximo)
        
        posicion = 1

        #se determina el arreglo de distancia acumulada de los segmentos 
        distancia_acumulada = ap.distancia_euclidiana_acumulada(datos.coordenadas_segmento)

        datos.longitud_subsegmento = distancia_acumulada[-1]/(cantidad_divisiones+1)

        lista_total = []
        lista_base = []
        lista_base.append(datos.coordenadas_segmento[0])

        #se recorre todo el arreglo para separar el segmento en las partes 
        for i in range(1,len(distancia_acumulada)):

            punto_cortado = datos.coordenadas_segmento[i]
            while distancia_acumulada[i] > (datos.longitud_subsegmento*posicion):
                longitud_faltante = (datos.longitud_subsegmento*posicion) - distancia_acumulada[i-1]
                punto_cortado = ap.punto_en_recta_geografica_simple(datos.coordenadas_segmento[i-1][1],\
                                                                    datos.coordenadas_segmento[i-1][0],\
                                                                    datos.coordenadas_segmento[i][1],\
                                                                    datos.coordenadas_segmento[i][0],\
                                                                    longitud_faltante,
                                                                    distancia_acumulada[i] - distancia_acumulada[i-1])
                
                lista_base.append(punto_cortado)
                lista_total.append(lista_base)
                lista_base = []
                lista_base.append(punto_cortado)
                punto_cortado = datos.coordenadas_segmento[i]
                posicion += 1

            lista_base.append(punto_cortado)

        lista_total.append(lista_base)
        #al final del ciclo se genero una lista llamada lista total donde en cada posicion se encuentra otra lista con los segmentos
        #cortados

        #ahora se recorre esa lista y se mira en cual parte se encuentra el punto analizado

        for i in range(len(lista_total)):
            #ahora se analiza con la funión para determinar el area
            poligono = ap.generar_poligono_segmento_lonlat(lista_total[i],datos.L)
            
            #mirar si el punto se encuentra dentro del poligono
            point_in_edge = ap.punto_en_poligono(poligono,datos.longitud,datos.latitud)

            if(point_in_edge):
                #cuando se encuentra se almacena toda la información y se genera su hash
                if(datos.posicion_subsegmento != i):
                    datos.cambio_segmento = True
                datos.posicion_subsegmento = i
                datos.coordenadas_subsegmento = lista_total[i]
                break
            

    else:
        #si el segmento no supera los 60 metros se realiza el hash de manera normal
        datos.coordenadas_subsegmento = datos.coordenadas_segmento
        datos.longitud_subsegmento = datos.info_edge['length']
        datos.posicion_subsegmento = 0


#se recorren la lista que tiene todas las condiciones
def procesar_archivos(dato,carpeta_csv,
                      carpeta_archivos_json,
                      carpeta_almacenamiento_json,
                      carpeta_almacenamiento_csv,
                      umbral,
                      carpeta_grafos):

    inicio = time.time()

    contador_json = 1 
    #se extrae la metadata del dispositivo y su dataframe de los datos
    df,metadatos =  ap.cargar_csv_con_metadatos(carpeta_csv,dato)
    frecuencia_muestreo = int(metadatos["Sampling Rate Configured"][0:2])
    giroscopio_habilitado = False
    if(metadatos["Gyroscope Available"] == 'true'):
        giroscopio_habilitado = True

    df = df.iloc[::-1].reset_index(drop=True)
    
    df_gps = ap.eliminar_muestras_gps_duplicadas(df)

    df_gps = ap.ajustar_heading_y_filtrar(df_gps)

    ######por ahora se deshabilita el filtro de velocidad para poder utilizar la muestra

    df_gps = df_gps.reset_index(drop=True)

    #df_gps = ap.filtrar_muestras_por_velocidad(df_gps,umbral)

    
    recortes_velocidad = algs.encontrar_segmentos_continuos(df_gps.index.tolist())


    
    indice_segmento_previo = 0
    indice_anterior = 0
    #se crea la estructura base para manejar el grafo
    datos_mapa = DatosProcesamiento()
    datos_mapa.carpeta_grafos = carpeta_grafos
    datos_mapa.carpeta_grafos_comprimidos = carpeta_grafos
    lista_recortes = []

    f_muestreo = 25

    if frecuencia_muestreo != f_muestreo:
        muestras_25hz = int((len(df)/frecuencia_muestreo)*f_muestreo)

        ax = resample(df['acc_x'].to_numpy(),muestras_25hz)
        az = resample(df['acc_z'].to_numpy(),muestras_25hz)
        wx = resample(df['gyro_x'].to_numpy(),muestras_25hz)
        wy = resample(df['gyro_y'].to_numpy(),muestras_25hz)
    else:

        ax = df['acc_x'].to_numpy()
        az = df['acc_z'].to_numpy()
        wx = df['gyro_x'].to_numpy()
        wy = df['gyro_y'].to_numpy()

    senal_pura_ax = ax - np.mean(ax)
    senal_pura_wy = wy - np.mean(wy)
    senal_pura_az  = az - np.mean(az)
    senal_pura_wx = wx - np.mean(wx)

    tiempo_muestra = 6
    
    cantidad_segmentos_analizados = int(len(ax)/(tiempo_muestra*f_muestreo))
    longitud_recorte = int(len(ax)/cantidad_segmentos_analizados)
    listado_huecos = []

    print("tiempo de preparación:",time.time()-inicio)
    
    for i in range(1,cantidad_segmentos_analizados+1):
        
        senal_recortada_acelerometro = senal_pura_ax[longitud_recorte*(i-1):longitud_recorte*i]
        huecos_acelerometro = algs.encontar_huecos_segmento(senal_recortada_acelerometro,25,1,10,3,2,1)
        if(giroscopio_habilitado):
            senal_recortada_giroscopio = senal_pura_wy[longitud_recorte*(i-1):longitud_recorte*i]
            huecos_giroscopio = algs.encontar_huecos_segmento(senal_recortada_giroscopio,25,1,10,3,2,1)

            for j in range(len(huecos_giroscopio)):
                huecos_acelerometro = [d for d in huecos_acelerometro if abs(d["tiempo"] - huecos_giroscopio[j]['tiempo']) >= 2]
            
            for j in range(len(huecos_acelerometro)):
                huecos_giroscopio.append(huecos_acelerometro[j])
            
            #criterios de decisión para los huecos del giroscopio

            diccionario_hueco ={#se debe aqui añadir un filtro para separar y clasificar los huecos de ambas para encontar valores iguales
                "huecos":huecos_giroscopio
            }
        else:
            diccionario_hueco ={#se debe aqui añadir un filtro para separar y clasificar los huecos de ambas para encontar valores iguales
                "huecos":huecos_acelerometro
            }
        
        listado_huecos.append(diccionario_hueco)

    print("tiempo de encontrar huecos:",time.time()-inicio)

    for i in range(len(df_gps)):
        
        adquirir_latitud_longitud(df_gps,datos_mapa,i)
        procesamiento_mapa_simple(datos_mapa)
        ubicar_muestra_grafov2(datos_mapa)
        segmentar_grafo(datos_mapa)


        

        #se guarda la información en caso que se cambie el segmento
        if datos_mapa.cambio_segmento:
      
            hash_segmento = ap.hash_segmento(datos_mapa.id_edge[0],datos_mapa.id_edge[1],(datos_mapa.posicion_subsegmento*1000)+datos_mapa.id_edge[2])
            #se recorta de acuerdo a los segmentos de velocidad 

            index_intervalo = ap.buscar_intervalo(df_gps.index[i],recortes_velocidad)
            if(indice_segmento_previo < recortes_velocidad[index_intervalo][0]):
                indice_anterior = recortes_velocidad[index_intervalo][0]
            else:
                indice_anterior = indice_segmento_previo
            
            indice_segmento_previo = df_gps.index[i]

            indice_inicio_original = df_gps['index_original'].loc[indice_anterior]
            indice_final_original = df_gps['index_original'].iloc[i]

            #condición de minimas muestas para las muestras del segmento
            if((indice_final_original - indice_inicio_original) > (64*(frecuencia_muestreo/f_muestreo))):

                df_base_recortado = df.iloc[indice_inicio_original:indice_final_original]

                prom_velocidad = np.mean(df_base_recortado['gps_speed'].to_numpy())
                
            
                if prom_velocidad > 5:
                    multiplicacion_velocidad = (0.8453153406199 + 0.5658028957503j) * np.exp(-10 * np.pi * 1j / (prom_velocidad)) + (-0.5661842683643 - 1.9824881204756j)
                else:
                    multiplicacion_velocidad = 1

                index_inicio = int((indice_inicio_original/frecuencia_muestreo)*f_muestreo)
                index_final = int((indice_final_original/frecuencia_muestreo)*f_muestreo)

                ax_recortado = senal_pura_ax[index_inicio:index_final] - np.mean(senal_pura_ax[index_inicio:index_final])
                wx_recortado = senal_pura_wx[index_inicio:index_final] - np.mean(senal_pura_wx[index_inicio:index_final])
                az_recortado = senal_pura_az[index_inicio:index_final] - np.mean(senal_pura_az[index_inicio:index_final])

                tiempo_segmento = (1/f_muestreo)*len(wx_recortado)

                #se realiza la conversión de la PWELCH de los indices 
                fvec, psd_az = welch(az_recortado,window="hamming",nperseg=64,noverlap=32,nfft=64,fs=f_muestreo,detrend=False)
                psd_az_ajustada = psd_az*(fvec[1]-fvec[0])*(8*(len(az_recortado)**2))            


                #ajuste de indice az hasta 3 hz
                vector_diferencia_maximo = np.abs(3 - fvec)
                indice_superior = np.argmin(vector_diferencia_maximo) + 1
                energia_az = np.sum(psd_az_ajustada[0:indice_superior])
                
                indice_az = energia_az/(tiempo_segmento*datos_mapa.longitud_subsegmento*np.abs(multiplicacion_velocidad))
                
      
                #se ajusta el indice si se acerca a los indices
                if indice_az < 2:
                    indice_az = 2
                if indice_az > 512:
                    indice_az = -(1 / (indice_az**2)) + 600

                indice_az_ajustado = -0.0666 * (np.log2(indice_az) ** 2) + 0.0835 * (np.log2(indice_az)) + 4.91

                indice_ax = (100*np.sum(ax_recortado**2))/(len(ax_recortado)*datos_mapa.longitud_subsegmento)

                if indice_ax > 0.36:
                    indice_ax = (-0.0072/indice_ax) + 0.38

                indice_ax_ajustado = -11.679*indice_ax + 4.4797
                
                numerator = (np.pi**2 * fvec**2)
                denominator = (3*np.pi**4 * fvec**4 / 3265 - 69*np.pi**3 * 1j * fvec**3 / 3265 - 145159*np.pi**2 * fvec**2 / 130600 + 3*np.pi * 1j * fvec + 633/40)
                resultado = np.abs(numerator / denominator)
                
                iri_desescalado = np.abs(np.sqrt(np.sum((resultado**2 * psd_az_ajustada) * (2*np.pi*fvec*1j)**4) / np.abs(multiplicacion_velocidad)) / (10000 * datos_mapa.longitud_subsegmento))
                iri_escala_humana = 5.2*(-(1./(1+np.exp(-0.8*(iri_desescalado-4))))+1)

                #se realiza el analisis de tiempo para ver si hay huecos en el segmento.
                if(giroscopio_habilitado):
                    #se realiza la conversión de la PWELCH de los indices wx
                    fvec_wx, psd_wx = welch(wx_recortado,window="hamming",nperseg=64,noverlap=32,nfft=64,fs=f_muestreo,detrend=False) 
                    psd_wx_ajustada = psd_wx*(fvec_wx[1]-fvec_wx[0])*(8*(len(wx_recortado)**2))
                    vector_diferencia_maximo = np.abs(6 - fvec_wx)
                    indice_superior = np.argmin(vector_diferencia_maximo) + 1
                    energia_wx =  np.sum(psd_wx_ajustada[0:indice_superior])    
                    indice_wx = energia_wx/(tiempo_segmento*datos_mapa.longitud_subsegmento)

                    
                    #se ajusta el indice 
                    if indice_wx > 8.57:
                        indice_wx = -(1 / (indice_wx**3)) + 8.815
                    
                    indice_wx_ajustado = -0.0021*(np.log2(indice_wx)**3) - 0.0675*(np.log2(indice_wx)**2) - 0.6786*(np.log2(indice_wx)) + 2.8683

                    

                    ibf = (indice_ax_ajustado+indice_wx_ajustado+indice_az_ajustado)/3
                else:
                    ibf = (indice_ax_ajustado+indice_az_ajustado)/2
                    indice_wx_ajustado = np.nan
                    indice_wx = np.nan

                iqr = ((1 - 0.5 * (1 / ((0.5 * ibf**2) + 1))) * iri_escala_humana) + 0.5 * (ibf * (1 / ((0.5 * ibf**2) + 1)))
                
                posicion_segmento_inicial = int(index_inicio/longitud_recorte)
                posicion_segmento_final = int(index_final/longitud_recorte)

                listado_huecos_segmento = []
                for j in range(posicion_segmento_inicial,posicion_segmento_final):
                    segmento_hueco_analizado = listado_huecos[j]
                    for k in range(len(segmento_hueco_analizado['huecos'])):
                        numero_muestra = int(segmento_hueco_analizado['huecos'][k]['tiempo']*f_muestreo) + (j*f_muestreo*tiempo_muestra)
                        if(index_inicio < numero_muestra and numero_muestra < index_final):
                            latitud_hueco_bruto = df['gps_lat'].iloc[numero_muestra]
                            longitud_hueco_bruto = df['gps_lng'].iloc[numero_muestra]
                            velocidad_hueco = df['gps_speed'].iloc[numero_muestra]
                            (latitud_hueco,longitud_hueco) = colocar_puntos_grafo(datos_mapa,latitud_hueco_bruto,longitud_hueco_bruto)
                            hueco = {
                                "latitud":latitud_hueco,
                                "longitud":longitud_hueco,
                                "magnitud" : segmento_hueco_analizado['huecos'][k]['valor'],
                                "velocidad" : velocidad_hueco
                            }
                            listado_huecos_segmento.append(hueco)

                if 'name' in datos_mapa.info_edge:
                    nombre = datos_mapa.info_edge['name']
                else:
                    nombre = "Undefined"
                segmento = {
                    "id" : hash_segmento,
                    "nombre": nombre,
                    "tipo_via": datos_mapa.info_edge["highway"],
                    "longitud_via" : datos_mapa.longitud_subsegmento,
                    "punto_inicial" : i,
                    "tiempo" : ap.timestamp_a_iso8601(int(df_gps['timestamp'].iloc[i])),
                    "coordenadas_segmento" : datos_mapa.coordenadas_subsegmento,
                    "huecos":listado_huecos_segmento,
                    "az": indice_az,
                    "az_ajustado": indice_az_ajustado,
                    "wx": indice_wx,
                    "wx_ajustado":indice_wx_ajustado,
                    "iri" :iri_desescalado,
                    "iri_ajustado": iri_escala_humana,
                    "ax": indice_ax,
                    "ax_ajustado": indice_ax_ajustado,
                    "IQR": iqr
                }
                lista_recortes.append(segmento)
    #en lista recortes se va a encontrar todos los segmentos que se especificaron en el recorrido

    print("tiempo de segmentar y encontrar indices:",time.time()-inicio)
    #importante como esta es una versión prototipo para el sistema se tiene que tomar en cuenta que el recorte de velocidad
    #puede recortar segmentos tomar en cuenta para el sistema final.

    resultado_json = []
    for i in range(len(lista_recortes)):
        lista_geometria = []
        for j in range(len(lista_recortes[i]["coordenadas_segmento"])):
            puntos = {
                "orden": j,
                "longitud": lista_recortes[i]["coordenadas_segmento"][j][0],
                "latitud": lista_recortes[i]["coordenadas_segmento"][j][1]
            }
            lista_geometria.append(puntos)

        datos_obtenidos = {
            "numero" : i,
            "id" : lista_recortes[i]["id"],
            "nombre" : lista_recortes[i]["nombre"],
            "longitud" : lista_recortes[i]["longitud_via"],
            "tipo" : lista_recortes[i]["tipo_via"],
            "latitud_origen" : lista_geometria[0]["latitud"],
            "latitud_destino" : lista_geometria[-1]["latitud"],
            "longitud_origen" : lista_geometria[0]["longitud"],
            "longitud_destino" : lista_geometria[-1]["longitud"],
            "geometria" : lista_geometria,
            "fecha" : lista_recortes[i]["tiempo"],
            "IQR" : lista_recortes[i]["IQR"],
            "iri" : lista_recortes[i]["iri"],
            "IRI_modificado" : lista_recortes[i]["iri_ajustado"],
            "az" : lista_recortes[i]["az_ajustado"],
            "ax" : lista_recortes[i]["ax_ajustado"],
            "wx" : lista_recortes[i]["wx_ajustado"],
            "huecos" : lista_recortes[i]['huecos']
        }

        resultado_json.append(datos_obtenidos)

    if(len (resultado_json) > 0):
        print("guardando los datos")
        # Usar carpeta actual si está vacía
        if carpeta_archivos_json == "":
            carpeta = "."
        else:
            carpeta = carpeta_archivos_json

        # Crear carpeta si no existe
        os.makedirs(carpeta, exist_ok=True)

        # Construir ruta del archivo
        ruta_archivo = os.path.join(carpeta, 'datos' + str(contador_json) + '.json')

        # Guardar el archivo
        with open(ruta_archivo, 'w', encoding='utf-8') as archivo:
            json.dump(resultado_json, archivo, indent=2)

        # Usar carpeta actual si está vacía
        if carpeta_almacenamiento_json == "":
            carpeta = "."
        else:
            carpeta = carpeta_almacenamiento_json

        # Crear carpeta si no existe
        os.makedirs(carpeta, exist_ok=True)

        # Construir ruta del archivo
        ruta_archivo = os.path.join(carpeta, 'datos' + dato[:-4] + 'save.json')
        with open(ruta_archivo, 'w', encoding='utf-8') as archivo:
            json.dump(resultado_json, archivo, indent=2)
        contador_json +=1

        ab.mover_archivo(carpeta_csv,carpeta_almacenamiento_csv,dato)
    
    return 0,0
    
###############################################################
#-----------------       MAIN        -------------------------#


def main():
    ap_entrada = argparse.ArgumentParser(description="Pipeline híbrido ultra-optimizado")
    ap_entrada.add_argument("--carpeta_csv", default="", help="Carpeta con CSVs a procesar")
    ap_entrada.add_argument("--prefijo", default="RecWay_", help="Prefijo de archivos CSV a procesar")
    ap_entrada.add_argument("--carpeta_json", default="guardarjson", help="Carpeta de JSON de salida rápida")
    ap_entrada.add_argument("--carpeta_csv_guardar", default="guardar", help="Carpeta para mover CSV procesados")
    ap_entrada.add_argument("--carpeta_json_guardar", default="guardarjson_hist", help="Carpeta historial de JSON")
    ap_entrada.add_argument("--carpeta_grafos", default="D:\Documentos\proyecto_empresa\desarrollo algoritmo posicionamiento\prototipov8\grafos_archivos6", help="Carpeta de grafos .graphml")
    ap_entrada.add_argument("--workers", type=int, default=max(1, os.cpu_count() - 1), help="Procesos en paralelo")
    ap_entrada.add_argument("--umbral_velocidad", type=float, default=3.0, help="Umbral de velocidad (m/s)")

    args = ap_entrada.parse_args()

    carpeta_csv = args.carpeta_csv or "."
    prefijo_busqueda  = args.prefijo
    carpeta_archivos_json = args.carpeta_json
    carpeta_almacenamiento_json = args.carpeta_json_guardar
    carpeta_almacenamiento_csv = args.carpeta_csv_guardar
    workers = max(1, int(args.workers))
    umbral = float(args.umbral_velocidad)
    carpeta_grafo = args.carpeta_grafos

    #se extrae la lista de los archivos que cumplen con las condiciones del prefijo
    archivos = ab.buscar_archivos_por_nombre(carpeta_csv,prefijo_busqueda)

    try:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [
                ex.submit(
                    procesar_archivos,
                    archivo, carpeta_csv, carpeta_archivos_json, carpeta_almacenamiento_json,
                    carpeta_almacenamiento_csv, umbral, carpeta_grafo
                )
                for archivo in archivos
            ]
            total_seg = 0
            archivos_procesados = 0
            for fut in as_completed(futs):
                try:
                    ruta, n = fut.result()
                    total_seg += n
                    archivos_procesados += 1
                    print(f"   📋 Progreso: {archivos_procesados}/{len(archivos)} archivos completados")
                except Exception as e:
                    print("⚠️  Tarea fallida:")
                    traceback.print_exception(type(e), e, e.__traceback__)

    except KeyboardInterrupt:
        print(f"\n🛑 Interrumpido por el usuario")    
    
    

if __name__ == "__main__":
    main()