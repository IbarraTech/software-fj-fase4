"""
Módulo: excepciones.py

Define la jerarquía de excepciones personalizadas del sistema Software FJ.
Todas heredan de SoftwareFJError, lo que permite capturar cualquier error
propio del sistema con un único bloque except, o capturar errores
específicos cuando se necesita un tratamiento particular.

Jerarquía:
    SoftwareFJError
    ├── DatosInvalidosError
    │   ├── ClienteInvalidoError
    │   ├── ParametroFaltanteError
    │   ├── ServicioInvalidoError
    │   └── RegistroDuplicadoError
    ├── ServicioNoDisponibleError
    ├── ReservaError
    │   ├── ReservaInvalidaError
    │   └── OperacionNoPermitidaError
    ├── CalculoInconsistenteError
    └── EntidadNoEncontradaError
"""


class SoftwareFJError(Exception):  # Excepción base de la que heredan todas las del sistema
    """Excepción base del sistema Software FJ."""

    codigo_por_defecto = "SFJ-000"  # Código que identifica el tipo de error en el log

    def __init__(self, mensaje: str, codigo: str | None = None):  # Recibe el mensaje y, opcionalmente, un código
        super().__init__(mensaje)  # Inicializa la clase Exception con el mensaje
        self.mensaje = mensaje  # Guarda el mensaje para consultarlo después
        self.codigo = codigo or self.codigo_por_defecto  # Usa el código recibido o el de la clase

    def __str__(self) -> str:  # Define cómo se muestra la excepción como texto
        return f"[{self.codigo}] {self.mensaje}"  # Formato: [CÓDIGO] mensaje


# ----------------------------------------------------------------------
# Errores de datos de entrada
# ----------------------------------------------------------------------
class DatosInvalidosError(SoftwareFJError):  # Agrupa los errores causados por datos incorrectos
    """Se lanza cuando un dato recibido no cumple las reglas de validación."""

    codigo_por_defecto = "SFJ-100"  # Familia 100: datos inválidos


class ClienteInvalidoError(DatosInvalidosError):  # Error en los datos de un cliente
    """Se lanza cuando un dato del cliente (nombre, documento, correo, teléfono) es inválido."""

    codigo_por_defecto = "SFJ-101"  # Código propio de cliente inválido


class ParametroFaltanteError(DatosInvalidosError):  # Error por un dato obligatorio ausente
    """Se lanza cuando falta un parámetro obligatorio o llega vacío."""

    codigo_por_defecto = "SFJ-102"  # Código propio de parámetro faltante


class ServicioInvalidoError(DatosInvalidosError):  # Error al crear o configurar un servicio
    """Se lanza cuando los datos para crear un servicio son incorrectos."""

    codigo_por_defecto = "SFJ-103"  # Código propio de servicio inválido


class RegistroDuplicadoError(DatosInvalidosError):  # Error por intentar registrar algo repetido
    """Se lanza cuando se intenta registrar una entidad que ya existe."""

    codigo_por_defecto = "SFJ-104"  # Código propio de registro duplicado


# ----------------------------------------------------------------------
# Errores de disponibilidad
# ----------------------------------------------------------------------
class ServicioNoDisponibleError(SoftwareFJError):  # Error cuando un servicio no puede usarse
    """Se lanza cuando el servicio está en mantenimiento o sin unidades disponibles."""

    codigo_por_defecto = "SFJ-200"  # Familia 200: disponibilidad


# ----------------------------------------------------------------------
# Errores de reservas
# ----------------------------------------------------------------------
class ReservaError(SoftwareFJError):  # Agrupa los errores relacionados con reservas
    """Error general en el ciclo de vida de una reserva."""

    codigo_por_defecto = "SFJ-300"  # Familia 300: reservas


class ReservaInvalidaError(ReservaError):  # Error por una reserva mal planteada
    """Se lanza cuando una reserva no puede crearse o confirmarse (duración, cliente o servicio incorrectos)."""

    codigo_por_defecto = "SFJ-301"  # Código propio de reserva inválida


class OperacionNoPermitidaError(ReservaError):  # Error por una transición de estado prohibida
    """Se lanza cuando se intenta una operación que el estado actual de la reserva no permite."""

    codigo_por_defecto = "SFJ-302"  # Código propio de operación no permitida


# ----------------------------------------------------------------------
# Errores de cálculo y búsqueda
# ----------------------------------------------------------------------
class CalculoInconsistenteError(SoftwareFJError):  # Error en el cálculo de costos
    """Se lanza cuando un cálculo produce o recibe valores incoherentes (descuentos o impuestos fuera de rango)."""

    codigo_por_defecto = "SFJ-400"  # Familia 400: cálculos


class EntidadNoEncontradaError(SoftwareFJError):  # Error cuando no existe lo que se busca
    """Se lanza cuando se busca un cliente, servicio o reserva que no está registrado."""

    codigo_por_defecto = "SFJ-500"  # Familia 500: búsquedas
