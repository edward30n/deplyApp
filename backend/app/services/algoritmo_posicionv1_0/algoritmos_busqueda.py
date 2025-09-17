import os

def buscar_archivos_por_nombre(directorio, texto_en_nombre):
    """
    Busca archivos cuyos nombres contienen una parte específica de texto en un directorio dado.

    Args:
        directorio (str): Ruta del directorio en el que se realizará la búsqueda.
                          Si está vacío, se usa el directorio de trabajo actual.
        texto_en_nombre (str): Texto que se busca en los nombres de los archivos.

    Returns:
        list: Lista de nombres de archivos que contienen el texto (sin ruta completa).
    """
    # Usa el directorio actual si no se proporciona uno
    if not directorio:
        directorio = os.getcwd()

    if not os.path.isdir(directorio):
        raise ValueError(f"La ruta proporcionada no es válida: '{directorio}'")

    archivos_encontrados = []

    for archivo in os.listdir(directorio):
        if texto_en_nombre in archivo:
            archivos_encontrados.append(archivo)  # Solo el nombre, no la ruta completa

    return archivos_encontrados

def mover_archivo(carpeta_origen, carpeta_destino, nombre_archivo):
    """
    Mueve un archivo desde una carpeta de origen a una carpeta de destino.

    Args:
    - carpeta_origen (str): Ruta de la carpeta donde se encuentra el archivo.
    - carpeta_destino (str): Ruta de la carpeta donde se moverá el archivo.
    - nombre_archivo (str): Nombre del archivo que se desea mover.

    Returns:
    - None

    Prints:
    - Mensajes de error en caso de problemas (archivo no encontrado, permisos, etc.).
    """
    origen = os.path.join(carpeta_origen, nombre_archivo)
    destino = os.path.join(carpeta_destino, nombre_archivo)

    try:
        # Crear carpeta de destino si no existe
        os.makedirs(carpeta_destino, exist_ok=True)

        # Mover archivo
        os.rename(origen, destino)
        print(f"Archivo movido a: {destino}")
    except FileNotFoundError:
        print("El archivo de origen no se encuentra.")
    except PermissionError:
        print("No tienes permisos para mover el archivo.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")


