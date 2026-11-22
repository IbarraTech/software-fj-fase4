"""
Módulo: logger_config.py

Configura el registro de eventos y errores del sistema en el archivo
logs/software_fj.log usando el módulo estándar logging de Python.
"""

import logging  # Módulo estándar de Python para registrar eventos
from pathlib import Path  # Permite manejar rutas de archivos de forma segura

CARPETA_LOGS = Path(__file__).resolve().parent.parent / "logs"  # Carpeta logs/ en la raíz del proyecto
ARCHIVO_LOG = CARPETA_LOGS / "software_fj.log"  # Ruta completa del archivo de logs
NOMBRE_RAIZ = "software_fj"  # Nombre del logger principal del sistema
FORMATO = "%(asctime)s | %(levelname)-8s | %(name)-24s | %(message)s"  # Fecha | nivel | módulo | mensaje
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"  # Formato de la fecha en cada línea del log


def configurar_logging(reiniciar: bool = False, nivel: int = logging.INFO) -> logging.Logger:
    """
    Configura el logger principal que escribe en el archivo de logs.

    :param reiniciar: si es True, borra el contenido anterior del archivo al iniciar.
    :param nivel: nivel mínimo de los mensajes que se registran.
    :return: el logger principal del sistema.
    """
    logger = logging.getLogger(NOMBRE_RAIZ)  # Obtiene (o crea) el logger principal
    if logger.handlers:  # Si ya estaba configurado, no se agregan manejadores repetidos
        return logger  # Devuelve el logger existente para evitar líneas duplicadas
    try:  # Intenta crear la carpeta y el archivo de logs
        CARPETA_LOGS.mkdir(parents=True, exist_ok=True)  # Crea la carpeta logs/ si no existe
        modo = "w" if reiniciar else "a"  # "w" sobrescribe el archivo, "a" agrega al final
        manejador = logging.FileHandler(ARCHIVO_LOG, mode=modo, encoding="utf-8")  # Escribe en el archivo
    except OSError as error:  # Si no se puede escribir en disco (permisos, disco lleno...)
        manejador = logging.StreamHandler()  # Se usa la consola para que el sistema no se detenga
        print(f"Aviso: no se pudo crear el archivo de logs ({error}). Se usará la consola.")  # Informa al usuario
    manejador.setFormatter(logging.Formatter(FORMATO, datefmt=FORMATO_FECHA))  # Aplica el formato de las líneas
    logger.addHandler(manejador)  # Conecta el manejador al logger
    logger.setLevel(nivel)  # Define el nivel mínimo de registro
    logger.propagate = False  # Evita que los mensajes se repitan en el logger raíz de Python
    return logger  # Devuelve el logger configurado


def obtener_logger(nombre_modulo: str) -> logging.Logger:
    """Devuelve un logger hijo para un módulo específico (por ejemplo, software_fj.cliente)."""
    return logging.getLogger(f"{NOMBRE_RAIZ}.{nombre_modulo}")  # El hijo hereda el manejador del principal


def registrar_error(logger: logging.Logger, error: BaseException, contexto: str) -> None:
    """
    Registra un error en el log incluyendo, si existe, la excepción original
    que lo causó (encadenamiento con 'raise ... from ...').

    :param logger: logger donde se escribe el mensaje.
    :param error: excepción capturada.
    :param contexto: descripción breve de la operación que falló.
    """
    causa = error.__cause__  # Excepción original guardada por 'raise ... from ...'
    if causa is not None:  # Si el error fue encadenado, se registra también su causa
        logger.error("%s -> %s | Causa original: %s: %s", contexto, error, type(causa).__name__, causa)  # Error y causa
    else:  # Si no hay causa encadenada
        logger.error("%s -> %s", contexto, error)  # Solo se registra el error
