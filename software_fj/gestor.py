"""
Módulo: gestor.py

Define SistemaGestion, el punto de entrada para operar Software FJ sin
base de datos: guarda clientes, servicios y reservas en listas internas.

Cada operación pública captura las excepciones propias del sistema,
las registra en el log y devuelve un resultado neutro (None o False),
de modo que un error nunca detiene la aplicación. El último error queda
disponible en la propiedad 'ultimo_error' para informarlo al usuario.
"""

from .cliente import Cliente  # Clase de clientes
from .excepciones import (  # Excepciones personalizadas que usa este módulo
    EntidadNoEncontradaError,
    ParametroFaltanteError,
    RegistroDuplicadoError,
    ServicioInvalidoError,
    SoftwareFJError,
)
from .logger_config import obtener_logger, registrar_error  # Registro de eventos y errores
from .reserva import EstadoReserva, Reserva  # Clase de reservas y sus estados
from .servicios import AlquilerEquipo, Asesoria, ReservaSala, Servicio, formatear_moneda  # Servicios disponibles

log = obtener_logger("gestor")  # Logger propio de este módulo


class SistemaGestion:
    """Administra clientes, servicios y reservas en memoria (listas internas)."""

    TIPOS_SERVICIO = {  # Relaciona el nombre corto de cada tipo con su clase
        "sala": ReservaSala,
        "equipo": AlquilerEquipo,
        "asesoria": Asesoria,
    }

    def __init__(self) -> None:
        self._clientes: list[Cliente] = []  # Lista interna de clientes registrados
        self._servicios: list[Servicio] = []  # Lista interna de servicios ofrecidos
        self._reservas: list[Reserva] = []  # Lista interna de reservas
        self._ultimo_error: SoftwareFJError | None = None  # Último error controlado
        log.info("Sistema de gestión Software FJ iniciado (almacenamiento en memoria, sin base de datos).")  # Evento

    # ------------------------------------------------------------------
    # Consultas (devuelven tuplas para que las listas internas no se modifiquen desde fuera)
    # ------------------------------------------------------------------
    @property
    def clientes(self) -> tuple[Cliente, ...]:  # Copia de solo lectura
        """Clientes registrados."""
        return tuple(self._clientes)  # Devuelve una tupla inmutable

    @property
    def servicios(self) -> tuple[Servicio, ...]:  # Copia de solo lectura
        """Servicios registrados."""
        return tuple(self._servicios)  # Devuelve una tupla inmutable

    @property
    def reservas(self) -> tuple[Reserva, ...]:  # Copia de solo lectura
        """Reservas registradas."""
        return tuple(self._reservas)  # Devuelve una tupla inmutable

    @property
    def ultimo_error(self) -> SoftwareFJError | None:  # Último error controlado
        """Último error capturado por una operación (None si la última fue exitosa)."""
        return self._ultimo_error  # Devuelve el error o None

    def _fallo(self, error: SoftwareFJError, contexto: str) -> None:
        """Guarda y registra en el log un error controlado."""
        self._ultimo_error = error  # Lo guarda para que el programa pueda informarlo
        registrar_error(log, error, contexto)  # Lo escribe en el log (con su causa, si existe)

    # ------------------------------------------------------------------
    # Búsquedas internas (lanzan EntidadNoEncontradaError)
    # ------------------------------------------------------------------
    def _buscar_cliente(self, documento: object) -> Cliente:
        """Busca un cliente por documento."""
        documento_texto = str(documento).strip()  # Normaliza el documento a texto
        for cliente in self._clientes:  # Recorre la lista interna
            if cliente.documento == documento_texto:  # Coincide el documento
                return cliente  # Cliente encontrado
        raise EntidadNoEncontradaError(f"No existe un cliente registrado con el documento '{documento_texto}'.")  # No existe

    def _buscar_servicio(self, id_servicio: str) -> Servicio:
        """Busca un servicio por identificador."""
        for servicio in self._servicios:  # Recorre la lista interna
            if servicio.id == id_servicio:  # Coincide el identificador
                return servicio  # Servicio encontrado
        raise EntidadNoEncontradaError(f"No existe el servicio '{id_servicio}'.")  # No existe

    def _buscar_reserva(self, id_reserva: str) -> Reserva:
        """Busca una reserva por identificador."""
        for reserva in self._reservas:  # Recorre la lista interna
            if reserva.id == id_reserva:  # Coincide el identificador
                return reserva  # Reserva encontrada
        raise EntidadNoEncontradaError(f"No existe la reserva '{id_reserva}'.")  # No existe

    # ------------------------------------------------------------------
    # Clientes
    # ------------------------------------------------------------------
    def registrar_cliente(self, nombre: str, documento: str | int, email: str, telefono: str | None = None) -> Cliente | None:
        """Registra un cliente nuevo. Devuelve el cliente o None si los datos son inválidos."""
        try:  # Intenta crear y validar el cliente
            documento_texto = "" if documento is None else str(documento).strip()  # Documento normalizado para comparar
            if any(c.documento == documento_texto for c in self._clientes):  # Ya existe un cliente con ese documento
                raise RegistroDuplicadoError(f"Ya existe un cliente con el documento terminado en {documento_texto[-4:]}.")  # Duplicado
            cliente = Cliente(nombre, documento, email, telefono)  # El constructor valida todos los datos
        except SoftwareFJError as error:  # Cualquier error propio del sistema
            self._fallo(error, "Registro de cliente rechazado")  # Se registra y la aplicación continúa
            return None  # Resultado neutro
        else:  # Solo si el cliente se creó sin errores
            self._clientes.append(cliente)  # Se agrega a la lista interna
            self._ultimo_error = None  # La operación fue exitosa
            log.info("Cliente registrado: %s", cliente.describir())  # Evento (con documento enmascarado)
            return cliente  # Devuelve el cliente creado

    # ------------------------------------------------------------------
    # Servicios
    # ------------------------------------------------------------------
    def crear_servicio(self, tipo: str, **datos: object) -> Servicio | None:
        """
        Crea un servicio del tipo indicado ('sala', 'equipo' o 'asesoria').
        Devuelve el servicio o None si los datos son inválidos.
        """
        try:  # Intenta crear el servicio
            clase = self.TIPOS_SERVICIO.get(str(tipo).strip().lower())  # Busca la clase del tipo solicitado
            if clase is None:  # El tipo no existe
                raise ServicioInvalidoError(  # Tipo de servicio desconocido
                    f"Tipo de servicio '{tipo}' no existe. Opciones: {', '.join(self.TIPOS_SERVICIO)}."
                )
            try:  # Intenta construir el objeto con los datos recibidos
                servicio = clase(**datos)  # El constructor de cada servicio valida sus datos
            except TypeError as error:  # Faltan o sobran parámetros en la llamada
                raise ParametroFaltanteError(  # Se encadena el TypeError original
                    f"Parámetros incompletos o incorrectos para crear un servicio de tipo '{tipo}'."
                ) from error
        except SoftwareFJError as error:  # Cualquier error propio del sistema
            self._fallo(error, f"Creación de servicio '{tipo}' rechazada")  # Se registra y la aplicación continúa
            return None  # Resultado neutro
        else:  # Solo si el servicio se creó sin errores
            self._servicios.append(servicio)  # Se agrega a la lista interna
            self._ultimo_error = None  # La operación fue exitosa
            log.info("Servicio creado: %s", servicio.describir())  # Evento
            return servicio  # Devuelve el servicio creado

    def cambiar_disponibilidad(self, id_servicio: str, disponible: bool, motivo: str = "mantenimiento") -> bool:
        """Habilita o deshabilita un servicio. Devuelve True si se pudo cambiar."""
        try:  # Intenta encontrar el servicio
            servicio = self._buscar_servicio(id_servicio)  # Puede lanzar EntidadNoEncontradaError
        except SoftwareFJError as error:  # El servicio no existe
            self._fallo(error, "Cambio de disponibilidad rechazado")  # Se registra y la aplicación continúa
            return False  # Resultado neutro
        else:  # Solo si el servicio existe
            if disponible:  # Se quiere habilitar
                servicio.marcar_disponible()  # Lo habilita
                log.warning("Servicio %s habilitado nuevamente.", servicio.id)  # Evento relevante
            else:  # Se quiere deshabilitar
                servicio.marcar_no_disponible(motivo)  # Lo deshabilita con el motivo
                log.warning("Servicio %s deshabilitado. Motivo: %s.", servicio.id, motivo)  # Evento relevante
            self._ultimo_error = None  # La operación fue exitosa
            return True  # Cambio realizado

    # ------------------------------------------------------------------
    # Reservas
    # ------------------------------------------------------------------
    def crear_reserva(self, documento_cliente: str | int, id_servicio: str, duracion: float) -> Reserva | None:
        """Crea una reserva pendiente. Devuelve la reserva o None si no es posible."""
        try:  # Intenta localizar al cliente y al servicio y crear la reserva
            cliente = self._buscar_cliente(documento_cliente)  # Puede lanzar EntidadNoEncontradaError
            servicio = self._buscar_servicio(id_servicio)  # Puede lanzar EntidadNoEncontradaError
            reserva = Reserva(cliente, servicio, duracion)  # Valida la duración según el servicio
        except SoftwareFJError as error:  # Cualquier error propio del sistema
            self._fallo(error, "Creación de reserva rechazada")  # Se registra y la aplicación continúa
            return None  # Resultado neutro
        else:  # Solo si la reserva se creó sin errores
            self._reservas.append(reserva)  # Se agrega a la lista interna
            self._ultimo_error = None  # La operación fue exitosa
            log.info("Reserva creada: %s", reserva.describir())  # Evento
            return reserva  # Devuelve la reserva creada

    def confirmar_reserva(self, id_reserva: str) -> bool:
        """Confirma una reserva. Devuelve True si se confirmó."""
        try:  # Intenta confirmar
            self._buscar_reserva(id_reserva).confirmar()  # Puede fallar por estado o disponibilidad
        except SoftwareFJError as error:  # Cualquier error propio del sistema
            self._fallo(error, f"Confirmación de {id_reserva} rechazada")  # Se registra y la aplicación continúa
            return False  # Resultado neutro
        else:  # Solo si se confirmó
            self._ultimo_error = None  # La operación fue exitosa
            return True  # Confirmación exitosa

    def cancelar_reserva(self, id_reserva: str, motivo: str = "solicitud del cliente") -> bool:
        """Cancela una reserva. Devuelve True si se canceló."""
        try:  # Intenta cancelar
            self._buscar_reserva(id_reserva).cancelar(motivo)  # Puede fallar si el estado no lo permite
        except SoftwareFJError as error:  # Cualquier error propio del sistema
            self._fallo(error, f"Cancelación de {id_reserva} rechazada")  # Se registra y la aplicación continúa
            return False  # Resultado neutro
        else:  # Solo si se canceló
            self._ultimo_error = None  # La operación fue exitosa
            return True  # Cancelación exitosa

    def procesar_reserva(self, id_reserva: str, impuesto: float | None = None, descuento: object = None) -> float | None:
        """Procesa (cobra) una reserva confirmada. Devuelve el total o None si falla."""
        try:  # Intenta procesar
            total = self._buscar_reserva(id_reserva).procesar(impuesto=impuesto, descuento=descuento)  # Calcula y cobra
        except SoftwareFJError as error:  # Cualquier error propio del sistema
            self._fallo(error, f"Procesamiento de {id_reserva} rechazado")  # Se registra y la aplicación continúa
            return None  # Resultado neutro
        else:  # Solo si se procesó
            self._ultimo_error = None  # La operación fue exitosa
            return total  # Devuelve el total cobrado

    # ------------------------------------------------------------------
    # Reportes
    # ------------------------------------------------------------------
    def resumen(self) -> dict:
        """Resumen numérico del estado del sistema."""
        procesadas = [r for r in self._reservas if r.estado is EstadoReserva.PROCESADA]  # Reservas cobradas
        return {  # Totales del sistema
            "clientes": len(self._clientes),
            "servicios": len(self._servicios),
            "reservas": len(self._reservas),
            "por_estado": {e.value: sum(r.estado is e for r in self._reservas) for e in EstadoReserva},  # Conteo por estado
            "ingresos": sum(r.costo_total for r in procesadas),  # Suma de lo cobrado
        }

    def ingresos_formateados(self) -> str:
        """Ingresos totales en formato de moneda."""
        return formatear_moneda(self.resumen()["ingresos"])  # Reutiliza el resumen
