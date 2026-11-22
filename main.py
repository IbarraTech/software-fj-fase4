"""
main.py - Programa principal de Software FJ.

Ejecuta una secuencia de simulaciones completas (válidas e inválidas) sobre
el Sistema Integral de Gestión de Clientes, Servicios y Reservas, para
demostrar que la aplicación sigue funcionando aunque ocurran errores.

Ejecución:
    python main.py

Todos los eventos y errores quedan registrados en logs/software_fj.log
"""

from collections.abc import Callable  # Tipo para anotar funciones que se pasan como parámetro

from software_fj.excepciones import SoftwareFJError  # Excepción base del sistema
from software_fj.gestor import SistemaGestion  # Gestor con las listas internas
from software_fj.logger_config import ARCHIVO_LOG, configurar_logging, obtener_logger  # Configuración de logs
from software_fj.servicios import formatear_moneda  # Formato de moneda colombiana

log = obtener_logger("main")  # Logger propio del programa principal

Resultado = tuple[bool, str]  # Cada simulación devuelve (¿la operación se realizó?, detalle)


class Simulador:
    """Ejecuta y cuenta las simulaciones sin permitir que un error detenga el programa."""

    def __init__(self) -> None:
        self.sistema = SistemaGestion()  # Sistema sobre el que se hacen las operaciones
        self.numero = 0  # Número de la simulación actual
        self.conteo = {"exito": 0, "rechazo": 0, "inesperado": 0}  # Resultados obtenidos
        self.coinciden = 0  # Simulaciones cuyo resultado fue el esperado
        self.servicios: dict = {}  # Servicios creados, por nombre corto
        self.reservas: dict = {}  # Reservas creadas, por nombre corto

    def detalle_error(self) -> str:
        """Texto con el último error controlado y, si existe, su causa encadenada."""
        error = self.sistema.ultimo_error  # Último error guardado por el gestor
        if error is None:  # No hubo error
            return "sin error"  # Texto neutro
        texto = str(error)  # Mensaje del error con su código
        if error.__cause__ is not None:  # El error fue encadenado con 'raise ... from ...'
            texto += f"\n      Causa original: {type(error.__cause__).__name__}: {error.__cause__}"  # Agrega la causa
        return texto  # Devuelve el detalle completo

    def ejecutar(self, descripcion: str, esperado: str, operacion: Callable[[], Resultado]) -> None:
        """
        Ejecuta una simulación protegida.

        :param descripcion: qué se intenta hacer.
        :param esperado: 'exito', 'rechazo' o 'inesperado'.
        :param operacion: función sin parámetros que devuelve (realizada, detalle).
        """
        self.numero += 1  # Avanza el número de simulación
        print(f"\n[{self.numero:02d}] {descripcion}")  # Encabezado en pantalla
        log.info("===== Simulación %02d: %s =====", self.numero, descripcion)  # Encabezado en el log
        obtenido = "inesperado"  # Valor por defecto si ocurre un error no previsto
        try:  # Ejecuta la operación
            realizada, detalle = operacion()  # Corre la simulación
        except SoftwareFJError as error:  # Error propio que escapó del gestor (no debería ocurrir)
            log.error("Error del sistema no controlado en la simulación %02d: %s", self.numero, error)  # Se registra
            print(f"    [ERROR DEL SISTEMA CONTROLADO] {error}")  # Se informa sin detener el programa
        except Exception as error:  # Red de seguridad: cualquier error no previsto
            log.exception("Error inesperado en la simulación %02d", self.numero)  # Se registra con el traceback completo
            print(f"    [ERROR INESPERADO CONTROLADO] {type(error).__name__}: {error}")  # Se informa sin detener el programa
        else:  # La operación terminó sin excepciones
            obtenido = "exito" if realizada else "rechazo"  # Clasifica el resultado
            etiqueta = "[OK]" if realizada else "[RECHAZADA - ERROR CONTROLADO]"  # Etiqueta para la pantalla
            print(f"    {etiqueta} {detalle}")  # Muestra el resultado
        finally:  # Se ejecuta siempre, haya error o no
            self.conteo[obtenido] += 1  # Suma el resultado obtenido
            if obtenido == esperado:  # El sistema se comportó como se esperaba
                self.coinciden += 1  # Cuenta la coincidencia
            log.info("===== Fin de la simulación %02d (resultado: %s) =====", self.numero, obtenido)  # Cierre en el log

    # ------------------------------------------------------------------
    # Operaciones simuladas
    # ------------------------------------------------------------------
    def registrar_cliente(self, *datos: object) -> Resultado:
        """Intenta registrar un cliente y describe el resultado."""
        cliente = self.sistema.registrar_cliente(*datos)  # Delegación al gestor
        if cliente is None:  # El registro fue rechazado
            return False, self.detalle_error()  # Informa el motivo
        return True, cliente.describir()  # Informa el cliente creado

    def crear_servicio(self, clave: str, tipo: str, **datos: object) -> Resultado:
        """Intenta crear un servicio y lo guarda con un nombre corto."""
        servicio = self.sistema.crear_servicio(tipo, **datos)  # Delegación al gestor
        if servicio is None:  # La creación fue rechazada
            return False, self.detalle_error()  # Informa el motivo
        self.servicios[clave] = servicio  # Guarda la referencia para usarla después
        return True, servicio.describir()  # Informa el servicio creado

    def reserva_completa(self, clave: str, documento: str, servicio: str, horas: object, **cobro: object) -> Resultado:
        """Crea, confirma y procesa una reserva (operación completa)."""
        reserva = self.sistema.crear_reserva(documento, self.servicios[servicio].id, horas)  # Paso 1: crear
        if reserva is None:  # No se pudo crear
            return False, self.detalle_error()  # Informa el motivo
        self.reservas[clave] = reserva  # Guarda la referencia
        if not self.sistema.confirmar_reserva(reserva.id):  # Paso 2: confirmar
            return False, f"{reserva.id} quedó {reserva.estado.value}: {self.detalle_error()}"  # Informa el motivo
        total = self.sistema.procesar_reserva(reserva.id, **cobro)  # Paso 3: procesar (cobrar)
        if total is None:  # No se pudo procesar
            return False, f"{reserva.id} quedó {reserva.estado.value}: {self.detalle_error()}"  # Informa el motivo
        return True, f"{reserva.describir()}\n      Desglose: {self.texto_desglose(reserva)}"  # Informa el cobro

    @staticmethod
    def texto_desglose(reserva) -> str:
        """Desglose del cobro en formato legible."""
        d = reserva.desglose  # Diccionario con base, descuento, impuesto y total
        return (  # Texto del desglose
            f"base {formatear_moneda(d['base'])} - descuento {formatear_moneda(d['descuento'])} "
            f"+ impuesto {formatear_moneda(d['impuesto'])} = {formatear_moneda(d['total'])}"
        )

    def crear_y_confirmar(self, clave: str, documento: str, servicio: str, horas: object) -> Resultado:
        """Crea y confirma una reserva sin procesarla."""
        reserva = self.sistema.crear_reserva(documento, self.servicios[servicio].id, horas)  # Paso 1: crear
        if reserva is None:  # No se pudo crear
            return False, self.detalle_error()  # Informa el motivo
        self.reservas[clave] = reserva  # Guarda la referencia
        if not self.sistema.confirmar_reserva(reserva.id):  # Paso 2: confirmar
            return False, f"{reserva.id} quedó {reserva.estado.value}: {self.detalle_error()}"  # Informa el motivo
        return True, f"{reserva.describir()} | {self.servicios[servicio].describir()}"  # Informa la reserva y el stock

    def servicio_en_mantenimiento(self) -> Resultado:
        """Deshabilita la sala, intenta reservarla y la vuelve a habilitar."""
        sala = self.servicios["sala"]  # Sala creada anteriormente
        self.sistema.cambiar_disponibilidad(sala.id, False, "mantenimiento del aire acondicionado")  # La deshabilita
        try:  # Intenta reservar mientras está en mantenimiento
            realizada, detalle = self.crear_y_confirmar("sala_luis", "79856412", "sala", 2)  # Debe fallar
            if not realizada and "sala_luis" in self.reservas:  # Quedó una reserva pendiente sin confirmar
                self.sistema.cancelar_reserva(self.reservas["sala_luis"].id, "servicio en mantenimiento")  # Se cancela
            return realizada, detalle  # Devuelve el resultado del intento
        finally:  # Se ejecuta siempre: la sala se habilita de nuevo pase lo que pase
            self.sistema.cambiar_disponibilidad(sala.id, True)  # Vuelve a habilitarla

    def procesar(self, clave: str, **cobro: object) -> Resultado:
        """Intenta procesar una reserva existente."""
        reserva = self.reservas[clave]  # Reserva creada anteriormente
        total = self.sistema.procesar_reserva(reserva.id, **cobro)  # Delegación al gestor
        if total is None:  # No se pudo procesar
            return False, f"{self.detalle_error()}\n      La reserva sigue en estado: {reserva.estado.value}"  # Motivo y estado
        return True, reserva.describir()  # Informa el cobro

    def cancelar(self, clave: str, motivo: str) -> Resultado:
        """Intenta cancelar una reserva existente."""
        reserva = self.reservas[clave]  # Reserva creada anteriormente
        if not self.sistema.cancelar_reserva(reserva.id, motivo):  # Delegación al gestor
            return False, self.detalle_error()  # Informa el motivo
        return True, f"{reserva.describir()} | {reserva.servicio.describir()}"  # Informa la cancelación

    def confirmar(self, clave: str) -> Resultado:
        """Intenta confirmar una reserva existente."""
        reserva = self.reservas[clave]  # Reserva creada anteriormente
        if not self.sistema.confirmar_reserva(reserva.id):  # Delegación al gestor
            return False, self.detalle_error()  # Informa el motivo
        return True, reserva.describir()  # Informa la confirmación

    def recuperar_reserva_pendiente(self) -> Resultado:
        """Después de liberar el equipo, confirma y procesa la reserva que había quedado pendiente."""
        realizada, detalle = self.confirmar("equipo_luis")  # Ahora sí hay una unidad libre
        if not realizada:  # Si aun así falla, se informa
            return False, detalle  # Motivo del fallo
        return self.procesar("equipo_luis", impuesto=0, descuento=5)  # Cobro sin impuesto y con 5 puntos de descuento

    def reporte_externo(self) -> Resultado:
        """Simula un fallo de programación: se pide un dato que el resumen no tiene."""
        resumen = self.sistema.resumen()  # Resumen real del sistema
        return True, f"Ingresos en dólares: {resumen['ingresos_usd']}"  # KeyError: la clave no existe


def ejecutar_simulaciones(sim: Simulador) -> None:
    """Define y ejecuta las simulaciones en orden."""
    # --- Clientes -------------------------------------------------------
    sim.ejecutar("Registrar cliente válido (Ana María Gómez)", "exito",
                 lambda: sim.registrar_cliente("ana maría gómez", "1020304050", "Ana.Gomez@correo.com", "3001234567"))
    sim.ejecutar("Registrar cliente válido (Luis Fernando Rojas, sin teléfono)", "exito",
                 lambda: sim.registrar_cliente("Luis Fernando Rojas", 79856412, "luis.rojas@empresa.co"))
    sim.ejecutar("Registrar cliente con correo inválido", "rechazo",
                 lambda: sim.registrar_cliente("Carlos Pérez", "52147896", "carlos.perez#correo"))
    sim.ejecutar("Registrar cliente sin nombre (parámetro faltante)", "rechazo",
                 lambda: sim.registrar_cliente("   ", "63258741", "sin.nombre@correo.com"))
    sim.ejecutar("Registrar cliente con documento duplicado", "rechazo",
                 lambda: sim.registrar_cliente("Ana Gómez Duplicada", "1020304050", "otra@correo.com"))

    # --- Servicios ------------------------------------------------------
    sim.ejecutar("Crear servicio válido: sala de reuniones", "exito",
                 lambda: sim.crear_servicio("sala", "sala", nombre="Sala Andes", tarifa_hora=45000,
                                            capacidad=12, incluye_proyector=True))
    sim.ejecutar("Crear servicio válido: alquiler de equipo (1 unidad)", "exito",
                 lambda: sim.crear_servicio("equipo", "equipo", nombre="Portátil de alto rendimiento",
                                            tarifa_hora=9000, tipo_equipo="Portátil", unidades=1))
    sim.ejecutar("Crear servicio válido: asesoría especializada", "exito",
                 lambda: sim.crear_servicio("asesoria", "asesoria", nombre="Asesoría en bases de datos",
                                            tarifa_hora=120000, especialidad="bases de datos", consultor="Laura Méndez"))
    sim.ejecutar("Crear sala con tarifa negativa", "rechazo",
                 lambda: sim.crear_servicio("sala_mala", "sala", nombre="Sala Caribe", tarifa_hora=-20000, capacidad=8))
    sim.ejecutar("Crear sala con capacidad no numérica (excepción encadenada)", "rechazo",
                 lambda: sim.crear_servicio("sala_mala", "sala", nombre="Sala Pacífico", tarifa_hora=30000, capacidad="veinte"))
    sim.ejecutar("Crear asesoría sin consultor (parámetro faltante, excepción encadenada)", "rechazo",
                 lambda: sim.crear_servicio("asesoria_mala", "asesoria", nombre="Asesoría Cloud",
                                            tarifa_hora=150000, especialidad="Arquitectura en la nube"))
    sim.ejecutar("Crear servicio de un tipo inexistente", "rechazo",
                 lambda: sim.crear_servicio("catering", "catering", nombre="Refrigerios", tarifa_hora=10000))

    # --- Reservas -------------------------------------------------------
    sim.ejecutar("Reserva completa: Ana reserva la sala 3 h (IVA por defecto)", "exito",
                 lambda: sim.reserva_completa("sala_ana", "1020304050", "sala", 3))
    sim.ejecutar("Reserva completa: Luis toma asesoría 3 h con cupón FJ10", "exito",
                 lambda: sim.reserva_completa("asesoria_luis", "79856412", "asesoria", 3, descuento="FJ10"))
    sim.ejecutar("Reservar la sala por 12 h (duración fuera de rango)", "rechazo",
                 lambda: sim.reserva_completa("sala_larga", "1020304050", "sala", 12))
    sim.ejecutar("Reservar con un cliente no registrado", "rechazo",
                 lambda: sim.reserva_completa("fantasma", "99999999", "asesoria", 2))
    sim.ejecutar("Ana alquila la única unidad del portátil por 4 h", "exito",
                 lambda: sim.crear_y_confirmar("equipo_ana", "1020304050", "equipo", 4))
    sim.ejecutar("Luis intenta alquilar el portátil sin unidades libres (servicio no disponible)", "rechazo",
                 lambda: sim.crear_y_confirmar("equipo_luis", "79856412", "equipo", 2))
    sim.ejecutar("Reservar la sala mientras está en mantenimiento", "rechazo",
                 sim.servicio_en_mantenimiento)
    sim.ejecutar("Procesar el alquiler de Ana con 80 % de descuento (cálculo inconsistente)", "rechazo",
                 lambda: sim.procesar("equipo_ana", descuento=0.8))
    sim.ejecutar("Ana cancela su alquiler confirmado (se libera la unidad)", "exito",
                 lambda: sim.cancelar("equipo_ana", "cambio de planes"))
    sim.ejecutar("Luis recupera su reserva pendiente: confirmar y procesar", "exito",
                 sim.recuperar_reserva_pendiente)
    sim.ejecutar("Cancelar una reserva ya procesada (operación no permitida)", "rechazo",
                 lambda: sim.cancelar("sala_ana", "ya no la necesita"))
    sim.ejecutar("Confirmar una reserva cancelada (operación no permitida)", "rechazo",
                 lambda: sim.confirmar("equipo_ana"))
    sim.ejecutar("Generar un reporte con un dato inexistente (error de programación simulado)", "inesperado",
                 sim.reporte_externo)


def imprimir_resumen(sim: Simulador) -> None:
    """Muestra el estado final del sistema y las estadísticas de la ejecución."""
    sistema = sim.sistema  # Sistema con los datos finales
    print("\n" + "=" * 78)  # Separador
    print("ESTADO FINAL DEL SISTEMA")  # Título
    print("=" * 78)  # Separador
    print("\nClientes registrados:")  # Sección de clientes
    for cliente in sistema.clientes:  # Recorre los clientes
        print(f"  - {cliente}")  # __str__ usa describir()
    print("\nServicios ofrecidos:")  # Sección de servicios
    for servicio in sistema.servicios:  # Recorre los servicios (cada uno se describe a su manera)
        print(f"  - {servicio}")  # Polimorfismo: describir() de cada clase hija
    print("\nReservas:")  # Sección de reservas
    for reserva in sistema.reservas:  # Recorre las reservas
        print(f"  - {reserva}")  # __str__ usa describir()
    resumen = sistema.resumen()  # Totales del sistema
    estados = ", ".join(f"{estado}: {cantidad}" for estado, cantidad in resumen["por_estado"].items())  # Conteo por estado
    print(f"\nReservas por estado -> {estados}")  # Muestra el conteo
    print(f"Ingresos totales: {sistema.ingresos_formateados()}")  # Muestra lo cobrado
    print("\n" + "-" * 78)  # Separador
    print(f"Simulaciones ejecutadas: {sim.numero}")  # Total de simulaciones
    print(f"  Operaciones exitosas:             {sim.conteo['exito']}")  # Exitosas
    print(f"  Operaciones rechazadas (control): {sim.conteo['rechazo']}")  # Rechazadas por validación
    print(f"  Errores inesperados controlados:  {sim.conteo['inesperado']}")  # Capturadas por la red de seguridad
    print(f"  Resultado igual al esperado:      {sim.coinciden}/{sim.numero}")  # Verificación del comportamiento
    print(f"\nEl programa terminó sin interrupciones. Log: {ARCHIVO_LOG}")  # Mensaje final


def main() -> None:
    """Punto de entrada del programa."""
    configurar_logging(reiniciar=True)  # Inicia un archivo de logs limpio en cada ejecución
    log.info("Inicio de la ejecución de simulaciones de Software FJ.")  # Evento de inicio
    print("SOFTWARE FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas")  # Título en pantalla
    sim = Simulador()  # Crea el simulador (y el sistema)
    try:  # Ejecuta todas las simulaciones
        ejecutar_simulaciones(sim)  # Corre la secuencia completa
        imprimir_resumen(sim)  # Muestra el estado final
    except Exception:  # Última barrera: nada debe cerrar el programa de forma abrupta
        log.critical("Fallo crítico no previsto en el programa principal.", exc_info=True)  # Se registra con traceback
        print("Ocurrió un fallo crítico. Revise el archivo de logs.")  # Aviso al usuario
    finally:  # Se ejecuta siempre
        log.info("Fin de la ejecución. Simulaciones: %d | Resultados: %s", sim.numero, sim.conteo)  # Evento de cierre


if __name__ == "__main__":  # Solo se ejecuta cuando el archivo se corre directamente
    main()  # Inicia el programa
