"""
Módulo: reserva.py

Define la clase Reserva, que integra un cliente, un servicio, una duración
y un estado. Implementa confirmación, cancelación y procesamiento con
manejo de excepciones (try/except/else, try/finally,
try/except/else/finally y encadenamiento).

Ciclo de vida:
    PENDIENTE --confirmar()--> CONFIRMADA --procesar()--> PROCESADA
        |                          |
        +------cancelar()----------+--> CANCELADA
"""

from enum import Enum  # Permite definir un conjunto fijo de estados

from .cliente import Cliente  # Clase del cliente que hace la reserva
from .entidad import Entidad  # Clase abstracta base
from .excepciones import (  # Excepciones personalizadas que usa este módulo
    CalculoInconsistenteError,
    OperacionNoPermitidaError,
    ReservaError,
    ReservaInvalidaError,
    ServicioNoDisponibleError,
)
from .logger_config import obtener_logger  # Logger para registrar los eventos de las reservas
from .servicios import Servicio, formatear_moneda  # Clase base de servicios y formato de moneda

log = obtener_logger("reserva")  # Logger propio de este módulo


class EstadoReserva(Enum):  # Estados posibles de una reserva
    """Estados del ciclo de vida de una reserva."""

    PENDIENTE = "Pendiente"  # Creada pero aún no confirmada
    CONFIRMADA = "Confirmada"  # El recurso quedó apartado
    CANCELADA = "Cancelada"  # Anulada; el recurso se liberó
    PROCESADA = "Procesada"  # Cobrada; ya no admite cambios


class Reserva(Entidad):  # Reserva hereda de la clase abstracta Entidad
    """Reserva de un servicio por parte de un cliente durante cierto número de horas."""

    PREFIJO = "RES"  # Identificadores RES-001, RES-002...

    def __init__(self, cliente: Cliente, servicio: Servicio, duracion: float) -> None:
        """
        Crea una reserva en estado PENDIENTE.

        :raises ReservaInvalidaError: si el cliente, el servicio o la duración no son válidos.
        """
        if not isinstance(cliente, Cliente):  # Debe recibir un objeto Cliente real
            raise ReservaInvalidaError(f"La reserva requiere un Cliente; se recibió {type(cliente).__name__}.")  # Cliente inválido
        if not isinstance(servicio, Servicio):  # Debe recibir un objeto Servicio real
            raise ReservaInvalidaError(f"La reserva requiere un Servicio; se recibió {type(servicio).__name__}.")  # Servicio inválido
        self._duracion = servicio.validar_parametros(duracion)  # Cada servicio valida la duración a su manera (polimorfismo)
        self._cliente = cliente  # Cliente que reserva
        self._servicio = servicio  # Servicio reservado
        self._estado = EstadoReserva.PENDIENTE  # Toda reserva nueva inicia pendiente
        self._desglose: dict | None = None  # Desglose del costo; se llena al procesar
        super().__init__()  # Asigna id y fecha solo cuando todo es válido

    # ------------------------------------------------------------------
    # Propiedades (encapsulación: el estado solo cambia con los métodos)
    # ------------------------------------------------------------------
    @property
    def cliente(self) -> Cliente:  # Lectura del cliente
        """Cliente que hizo la reserva."""
        return self._cliente  # Devuelve el cliente

    @property
    def servicio(self) -> Servicio:  # Lectura del servicio
        """Servicio reservado."""
        return self._servicio  # Devuelve el servicio

    @property
    def duracion(self) -> float:  # Lectura de la duración
        """Duración de la reserva en horas."""
        return self._duracion  # Devuelve la duración

    @property
    def estado(self) -> EstadoReserva:  # Lectura del estado
        """Estado actual de la reserva."""
        return self._estado  # Devuelve el estado

    @property
    def costo_total(self) -> float | None:  # Lectura del total cobrado
        """Total cobrado (None mientras no se procese)."""
        return self._desglose["total"] if self._desglose else None  # Total o None

    # ------------------------------------------------------------------
    # Operaciones del ciclo de vida
    # ------------------------------------------------------------------
    def confirmar(self) -> None:
        """
        Confirma la reserva apartando el recurso del servicio.

        :raises OperacionNoPermitidaError: si la reserva no está pendiente.
        :raises ReservaInvalidaError: si el servicio no está disponible (encadena ServicioNoDisponibleError).
        """
        if self._estado is not EstadoReserva.PENDIENTE:  # Solo se confirma una reserva pendiente
            raise OperacionNoPermitidaError(  # Transición de estado prohibida
                f"No se puede confirmar la reserva {self.id}: está en estado {self._estado.value}."
            )
        try:  # Intenta validar los datos y apartar el recurso
            self._cliente.validar()  # El cliente debe seguir teniendo datos válidos
            self._servicio.reservar_recurso()  # Aparta el recurso (o falla si no hay disponibilidad)
        except ServicioNoDisponibleError as error:  # El servicio no se puede usar
            raise ReservaInvalidaError(  # Se encadena: la reserva falla PORQUE el servicio no está disponible
                f"No se pudo confirmar la reserva {self.id}: el servicio no está disponible."
            ) from error
        else:  # Solo se ejecuta si no hubo ninguna excepción
            self._estado = EstadoReserva.CONFIRMADA  # Cambia el estado a confirmada
            log.info("Reserva %s confirmada (%s, %s h).", self.id, self._servicio.nombre, f"{self._duracion:g}")  # Evento

    def cancelar(self, motivo: str = "solicitud del cliente") -> None:
        """
        Cancela la reserva y, si estaba confirmada, libera el recurso.

        :raises OperacionNoPermitidaError: si la reserva ya fue cancelada o procesada.
        """
        if self._estado in (EstadoReserva.CANCELADA, EstadoReserva.PROCESADA):  # Estados que ya no admiten cancelación
            raise OperacionNoPermitidaError(  # Transición de estado prohibida
                f"No se puede cancelar la reserva {self.id}: está en estado {self._estado.value}."
            )
        estado_anterior = self._estado  # Guarda el estado previo para el log
        try:  # Intenta liberar el recurso si estaba apartado
            if estado_anterior is EstadoReserva.CONFIRMADA:  # Solo una reserva confirmada ocupa un recurso
                self._servicio.liberar_recurso()  # Devuelve el recurso al servicio
        finally:  # Se ejecuta SIEMPRE, incluso si liberar el recurso fallara
            self._estado = EstadoReserva.CANCELADA  # La reserva queda cancelada en cualquier caso
            log.info("Reserva %s cancelada (antes: %s). Motivo: %s.", self.id, estado_anterior.value, motivo)  # Evento

    def procesar(self, impuesto: float | None = None, descuento: object = None) -> float:
        """
        Procesa (cobra) una reserva confirmada.

        :param impuesto: tasa de impuesto (None = IVA por defecto).
        :param descuento: fracción, puntos porcentuales o cupón.
        :return: total cobrado.
        :raises OperacionNoPermitidaError: si la reserva no está confirmada.
        :raises ReservaError: si el cálculo del costo es inconsistente (encadena CalculoInconsistenteError).
        """
        if self._estado is not EstadoReserva.CONFIRMADA:  # Solo se procesa una reserva confirmada
            raise OperacionNoPermitidaError(  # Transición de estado prohibida
                f"No se puede procesar la reserva {self.id}: está en estado {self._estado.value}."
            )
        log.info("Iniciando procesamiento de la reserva %s.", self.id)  # Evento de inicio
        try:  # Intenta calcular el costo final
            desglose = self._servicio.cotizar(self._duracion, impuesto=impuesto, descuento=descuento)  # Cálculo polimórfico
        except CalculoInconsistenteError as error:  # El cálculo no es coherente
            raise ReservaError(f"No se pudo procesar la reserva {self.id}: cálculo de costo inválido.") from error  # Encadena la causa
        else:  # Solo se ejecuta si el cálculo fue correcto
            self._desglose = desglose  # Guarda el desglose del cobro
            self._estado = EstadoReserva.PROCESADA  # Cambia el estado a procesada
            log.info("Reserva %s procesada. Total cobrado: %s.", self.id, formatear_moneda(desglose["total"]))  # Evento
            return desglose["total"]  # Devuelve el total cobrado
        finally:  # Se ejecuta SIEMPRE, haya fallado o no
            log.info("Fin del procesamiento de %s. Estado actual: %s.", self.id, self._estado.value)  # Cierre del intento

    # ------------------------------------------------------------------
    # Implementación de los métodos abstractos de Entidad
    # ------------------------------------------------------------------
    def validar(self) -> None:
        """Verifica que la reserva siga siendo coherente."""
        self._cliente.validar()  # El cliente debe ser válido
        self._servicio.validar()  # El servicio debe ser válido
        self._servicio.validar_parametros(self._duracion)  # La duración debe seguir siendo válida
        if self._estado is EstadoReserva.PROCESADA and not self._desglose:  # Una reserva procesada debe tener costo
            raise ReservaInvalidaError(f"La reserva {self.id} está procesada pero no tiene costo registrado.")  # Estado incoherente

    def describir(self) -> str:
        """Descripción legible de la reserva."""
        total = formatear_moneda(self.costo_total) if self._desglose else "sin cobrar"  # Total o aviso
        return (  # Resumen de la reserva
            f"Reserva {self.id}: {self._cliente.nombre} -> {self._servicio.nombre} "
            f"({self._duracion:g} h) | Estado: {self._estado.value} | Total: {total}"
        )
