"""
Módulo: servicios.py

Define la clase abstracta Servicio y los tres servicios especializados que
ofrece Software FJ:
    - ReservaSala: reserva de salas de reuniones.
    - AlquilerEquipo: alquiler de equipos con unidades limitadas.
    - Asesoria: asesorías especializadas.

Cada servicio sobrescribe (polimorfismo) los métodos para calcular el
costo, describirse y validar sus parámetros. La clase base ofrece un
cálculo de costo "sobrecargado": admite variantes con impuesto por
defecto, impuesto personalizado, sin impuesto, con descuento porcentual,
con descuento en puntos o con cupón.
"""

import math  # Funciones matemáticas (verificar que un número sea finito)
from abc import abstractmethod  # Decorador para declarar métodos abstractos
from functools import singledispatchmethod  # Sobrecarga de métodos según el tipo del argumento

from .entidad import Entidad  # Clase abstracta base
from .excepciones import (  # Excepciones personalizadas que usa este módulo
    CalculoInconsistenteError,
    ParametroFaltanteError,
    ReservaInvalidaError,
    ServicioInvalidoError,
    ServicioNoDisponibleError,
)


def formatear_moneda(valor: float) -> str:
    """Convierte un número en texto de moneda colombiana, por ejemplo 120000 -> $120.000."""
    return "$" + f"{valor:,.0f}".replace(",", ".")  # Separador de miles con punto


class Servicio(Entidad):  # Servicio hereda de Entidad y sigue siendo abstracta
    """Clase abstracta que representa cualquier servicio ofrecido por Software FJ."""

    PREFIJO = "SRV"  # Identificadores SRV-001, SRV-002...
    TIPO = "Servicio"  # Nombre del tipo; cada clase hija lo cambia
    IVA = 0.19  # Impuesto por defecto (19 %)
    IMPUESTO_MAXIMO = 0.50  # Tasa de impuesto máxima aceptada (50 %)
    DESCUENTO_MAXIMO = 0.50  # Descuento máximo permitido (50 %)
    CUPONES = {"FJ10": 0.10, "FJ20": 0.20, "BIENVENIDA": 0.15}  # Cupones válidos y su porcentaje
    DURACION_MINIMA = 0.5  # Duración mínima en horas (cada hija la ajusta)
    DURACION_MAXIMA = 8.0  # Duración máxima en horas (cada hija la ajusta)

    def __init__(self, nombre: str, tarifa_hora: float) -> None:
        """Valida los datos comunes a todos los servicios."""
        self._nombre = self._validar_texto(nombre, "nombre del servicio")  # Nombre obligatorio
        self._tarifa_hora = self._validar_numero_positivo(tarifa_hora, "tarifa por hora")  # Tarifa mayor que cero
        self._disponible = True  # Todo servicio nuevo inicia disponible
        self._motivo_no_disponible = ""  # Sin motivo de indisponibilidad
        super().__init__()  # Asigna id y fecha solo cuando todo es válido

    # ------------------------------------------------------------------
    # Validaciones reutilizables por las clases hijas
    # ------------------------------------------------------------------
    @staticmethod
    def _validar_texto(valor: object, campo: str) -> str:
        """Verifica que un texto obligatorio exista y no esté vacío."""
        if valor is None or (isinstance(valor, str) and not valor.strip()):  # Ausente o vacío
            raise ParametroFaltanteError(f"El campo '{campo}' es obligatorio.")  # Falta el parámetro
        if not isinstance(valor, str):  # Tipo incorrecto
            raise ServicioInvalidoError(f"El campo '{campo}' debe ser texto; se recibió {type(valor).__name__}.")  # Tipo inválido
        return " ".join(valor.split())  # Devuelve el texto sin espacios sobrantes

    @staticmethod
    def _validar_numero_positivo(valor: object, campo: str) -> float:
        """Verifica que el valor sea un número finito mayor que cero."""
        if valor is None:  # El dato no fue enviado
            raise ParametroFaltanteError(f"El campo '{campo}' es obligatorio.")  # Falta el parámetro
        if isinstance(valor, bool):  # True/False no son valores numéricos válidos aquí
            raise ServicioInvalidoError(f"El campo '{campo}' no puede ser un valor booleano.")  # Tipo inválido
        try:  # Intenta convertir el valor a número
            numero = float(valor)  # Convierte texto o enteros a número decimal
        except (TypeError, ValueError) as error:  # El valor no es convertible a número
            raise ServicioInvalidoError(f"El campo '{campo}' debe ser numérico; se recibió '{valor}'.") from error  # Encadena la causa
        if not math.isfinite(numero) or numero <= 0:  # Rechaza infinito, NaN, cero y negativos
            raise ServicioInvalidoError(f"El campo '{campo}' debe ser mayor que cero; se recibió {valor}.")  # Valor fuera de rango
        return numero  # Devuelve el número validado

    @staticmethod
    def _validar_entero(valor: object, campo: str, minimo: int, maximo: int) -> int:
        """Verifica que el valor sea un número entero dentro de [minimo, maximo]."""
        if valor is None:  # El dato no fue enviado
            raise ParametroFaltanteError(f"El campo '{campo}' es obligatorio.")  # Falta el parámetro
        if isinstance(valor, bool):  # True/False no son cantidades válidas
            raise ServicioInvalidoError(f"El campo '{campo}' no puede ser un valor booleano.")  # Tipo inválido
        try:  # Intenta convertir el valor a número
            numero = float(valor)  # Primero a decimal para detectar valores como 2.5
        except (TypeError, ValueError) as error:  # El valor no es convertible a número
            raise ServicioInvalidoError(f"El campo '{campo}' debe ser un número entero; se recibió '{valor}'.") from error  # Encadena la causa
        if not numero.is_integer() or not (minimo <= numero <= maximo):  # Debe ser entero y estar en el rango
            raise ServicioInvalidoError(f"El campo '{campo}' debe ser un entero entre {minimo} y {maximo}; se recibió {valor}.")  # Fuera de rango
        return int(numero)  # Devuelve el entero validado

    def _normalizar_duracion(self, duracion: object) -> float:
        """Convierte la duración a horas y verifica que esté en el rango del servicio."""
        if duracion is None:  # La duración no fue enviada
            raise ParametroFaltanteError("La duración de la reserva es obligatoria.")  # Falta el parámetro
        if isinstance(duracion, bool):  # True/False no son duraciones válidas
            raise ReservaInvalidaError("La duración no puede ser un valor booleano.")  # Tipo inválido
        try:  # Intenta convertir la duración a número
            horas = float(duracion)  # Acepta enteros, decimales o texto numérico
        except (TypeError, ValueError) as error:  # La duración no es numérica
            raise ReservaInvalidaError(f"La duración debe ser numérica; se recibió '{duracion}'.") from error  # Encadena la causa
        if not math.isfinite(horas) or not (self.DURACION_MINIMA <= horas <= self.DURACION_MAXIMA):  # Fuera del rango del servicio
            raise ReservaInvalidaError(  # Duración no permitida para este tipo de servicio
                f"Duración de {horas:g} h no permitida para {self.TIPO}: "
                f"debe estar entre {self.DURACION_MINIMA:g} y {self.DURACION_MAXIMA:g} h."
            )
        return horas  # Devuelve la duración validada

    # ------------------------------------------------------------------
    # Propiedades (encapsulación)
    # ------------------------------------------------------------------
    @property
    def nombre(self) -> str:  # Lectura del nombre del servicio
        """Nombre comercial del servicio."""
        return self._nombre  # Devuelve el nombre

    @property
    def tarifa_hora(self) -> float:  # Lectura de la tarifa
        """Tarifa por hora del servicio."""
        return self._tarifa_hora  # Devuelve la tarifa

    @property
    def tipo(self) -> str:  # Lectura del tipo de servicio
        """Tipo de servicio (Sala, Equipo, Asesoría)."""
        return self.TIPO  # Devuelve el tipo definido en la clase concreta

    @property
    def disponible(self) -> bool:  # Lectura del estado de disponibilidad
        """Indica si el servicio puede reservarse."""
        return self._disponible  # Devuelve True o False

    def _texto_estado(self) -> str:
        """Texto corto con el estado de disponibilidad para las descripciones."""
        return "Disponible" if self._disponible else f"NO disponible ({self._motivo_no_disponible})"  # Estado legible

    # ------------------------------------------------------------------
    # Disponibilidad
    # ------------------------------------------------------------------
    def marcar_no_disponible(self, motivo: str = "mantenimiento") -> None:
        """Deja el servicio fuera de uso indicando el motivo."""
        self._disponible = False  # El servicio ya no se puede reservar
        self._motivo_no_disponible = motivo or "sin motivo"  # Guarda el motivo para informarlo

    def marcar_disponible(self) -> None:
        """Vuelve a habilitar el servicio."""
        self._disponible = True  # El servicio se puede reservar de nuevo
        self._motivo_no_disponible = ""  # Se borra el motivo anterior

    def verificar_disponibilidad(self) -> None:
        """Lanza ServicioNoDisponibleError si el servicio no puede reservarse."""
        if not self._disponible:  # El servicio está deshabilitado
            raise ServicioNoDisponibleError(f"El servicio '{self._nombre}' no está disponible: {self._motivo_no_disponible}.")  # Informa el motivo

    def reservar_recurso(self) -> None:
        """Ocupa el recurso al confirmar una reserva. Por defecto solo verifica la disponibilidad."""
        self.verificar_disponibilidad()  # Las clases hijas pueden ampliar este comportamiento

    def liberar_recurso(self) -> None:
        """Libera el recurso al cancelar una reserva. Por defecto no hace nada."""
        return None  # Las clases con recursos limitados lo sobrescriben

    # ------------------------------------------------------------------
    # Métodos abstractos: cada servicio los implementa a su manera
    # ------------------------------------------------------------------
    @abstractmethod
    def validar_parametros(self, duracion: object) -> float:
        """Valida los parámetros de una reserva para este servicio y devuelve la duración en horas."""

    @abstractmethod
    def calcular_costo(self, duracion: object) -> float:
        """Calcula el costo base (sin impuestos ni descuentos) para la duración indicada."""

    @abstractmethod
    def describir(self) -> str:
        """Descripción legible del servicio."""

    def validar(self) -> None:
        """Revalida los datos comunes del servicio (las hijas amplían esta validación)."""
        self._validar_texto(self._nombre, "nombre del servicio")  # Revalida el nombre
        self._validar_numero_positivo(self._tarifa_hora, "tarifa por hora")  # Revalida la tarifa

    # ------------------------------------------------------------------
    # Métodos sobrecargados para el cálculo de descuentos y costos
    # ------------------------------------------------------------------
    @singledispatchmethod
    def calcular_descuento(self, descuento: object) -> float:
        """
        Convierte un descuento en un porcentaje entre 0 y DESCUENTO_MAXIMO.

        Variantes (sobrecarga por tipo):
            - float: fracción directa, por ejemplo 0.15 = 15 %.
            - int: puntos porcentuales, por ejemplo 10 = 10 %.
            - str: código de cupón, por ejemplo "FJ10".
            - None: sin descuento.
        """
        raise CalculoInconsistenteError(f"Tipo de descuento no soportado: {type(descuento).__name__}.")  # Tipo no previsto

    @calcular_descuento.register
    def _(self, descuento: float) -> float:  # Variante 1: fracción decimal
        if not math.isfinite(descuento) or not (0 <= descuento <= self.DESCUENTO_MAXIMO):  # Fuera del rango permitido
            raise CalculoInconsistenteError(  # Un descuento así produciría un costo incoherente
                f"Descuento de {descuento:.0%} fuera de rango: debe estar entre 0% y {self.DESCUENTO_MAXIMO:.0%}."
            )
        return descuento  # Devuelve la fracción validada

    @calcular_descuento.register
    def _(self, descuento: bool) -> float:  # Los booleanos se rechazan (bool hereda de int)
        raise CalculoInconsistenteError("El descuento no puede ser un valor booleano.")  # Tipo inválido

    @calcular_descuento.register
    def _(self, descuento: int) -> float:  # Variante 2: puntos porcentuales
        return self.calcular_descuento(descuento / 100)  # Convierte 10 en 0.10 y reutiliza la variante float

    @calcular_descuento.register
    def _(self, descuento: str) -> float:  # Variante 3: código de cupón
        codigo = descuento.strip().upper()  # Normaliza el código (sin espacios, en mayúsculas)
        if codigo not in self.CUPONES:  # El cupón no existe
            raise CalculoInconsistenteError(f"El cupón '{descuento}' no es válido.")  # Cupón desconocido
        return self.CUPONES[codigo]  # Devuelve el porcentaje del cupón

    @calcular_descuento.register
    def _(self, descuento: None) -> float:  # Variante 4: sin descuento
        return 0.0  # Cero por ciento

    def _validar_impuesto(self, impuesto: object) -> float:
        """Devuelve la tasa de impuesto a aplicar: IVA si es None, o la tasa indicada si es válida."""
        if impuesto is None:  # No se indicó impuesto
            return self.IVA  # Se usa el IVA por defecto
        if isinstance(impuesto, bool):  # True/False no son tasas válidas
            raise CalculoInconsistenteError("El impuesto no puede ser un valor booleano.")  # Tipo inválido
        try:  # Intenta convertir la tasa a número
            tasa = float(impuesto)  # Acepta enteros, decimales o texto numérico
        except (TypeError, ValueError) as error:  # La tasa no es numérica
            raise CalculoInconsistenteError(f"El impuesto debe ser numérico; se recibió '{impuesto}'.") from error  # Encadena la causa
        if not math.isfinite(tasa) or not (0 <= tasa <= self.IMPUESTO_MAXIMO):  # Fuera del rango permitido
            raise CalculoInconsistenteError(f"Impuesto de {tasa:.0%} fuera de rango (0% a {self.IMPUESTO_MAXIMO:.0%}).")  # Tasa incoherente
        return tasa  # Devuelve la tasa validada

    def cotizar(self, duracion: object, impuesto: float | None = None, descuento: object = None) -> dict:
        """
        Devuelve el desglose completo del costo de una reserva.

        :param duracion: horas a reservar.
        :param impuesto: tasa de impuesto (None = IVA por defecto, 0 = sin impuesto).
        :param descuento: fracción, puntos porcentuales o cupón (ver calcular_descuento).
        :return: diccionario con base, descuento, impuesto y total.
        """
        costo_base = self.calcular_costo(duracion)  # Costo propio de cada servicio (polimorfismo)
        porcentaje = self.calcular_descuento(descuento)  # Porcentaje según el tipo de descuento (sobrecarga)
        tasa = self._validar_impuesto(impuesto)  # Tasa de impuesto a aplicar
        valor_descuento = costo_base * porcentaje  # Valor monetario del descuento
        subtotal = costo_base - valor_descuento  # Costo después del descuento
        valor_impuesto = subtotal * tasa  # Valor monetario del impuesto
        total = subtotal + valor_impuesto  # Costo final
        if not math.isfinite(total) or total <= 0:  # Verificación final de coherencia
            raise CalculoInconsistenteError(f"El costo calculado ({total}) no es coherente.")  # Resultado inválido
        return {  # Desglose redondeado a dos decimales
            "base": round(costo_base, 2),
            "descuento": round(valor_descuento, 2),
            "impuesto": round(valor_impuesto, 2),
            "total": round(total, 2),
        }

    def calcular_costo_total(self, duracion: object, impuesto: float | None = None, descuento: object = None) -> float:
        """
        Costo final de una reserva. Método "sobrecargado" mediante parámetros opcionales:
            calcular_costo_total(3)                    -> con IVA por defecto
            calcular_costo_total(3, impuesto=0)        -> sin impuesto
            calcular_costo_total(3, impuesto=0.08)     -> con impuesto personalizado
            calcular_costo_total(3, descuento=0.1)     -> con 10 % de descuento
            calcular_costo_total(3, descuento="FJ20")  -> con cupón
        """
        return self.cotizar(duracion, impuesto, descuento)["total"]  # Reutiliza el desglose y devuelve solo el total


class ReservaSala(Servicio):  # Servicio especializado 1
    """Reserva de salas de reuniones por bloques de media hora."""

    TIPO = "Reserva de sala"  # Nombre del tipo de servicio
    DURACION_MINIMA = 0.5  # Mínimo media hora
    DURACION_MAXIMA = 8.0  # Máximo una jornada de 8 horas
    CAPACIDAD_GRANDE = 20  # A partir de esta capacidad se cobra recargo
    RECARGO_SALA_GRANDE = 0.10  # Recargo del 10 % para salas grandes
    COSTO_PROYECTOR = 15000.0  # Valor fijo por uso de proyector

    def __init__(self, nombre: str, tarifa_hora: float, capacidad: int, incluye_proyector: bool = False) -> None:
        """Crea una sala validando su capacidad (2 a 50 personas)."""
        self._capacidad = self._validar_entero(capacidad, "capacidad", 2, 50)  # Capacidad entre 2 y 50
        self._incluye_proyector = bool(incluye_proyector)  # Indica si la sala tiene proyector
        super().__init__(nombre, tarifa_hora)  # Valida los datos comunes y asigna el id

    @property
    def capacidad(self) -> int:  # Lectura de la capacidad
        """Número máximo de personas."""
        return self._capacidad  # Devuelve la capacidad

    def validar_parametros(self, duracion: object) -> float:  # Sobrescribe el método abstracto
        """La sala se reserva en bloques de 30 minutos."""
        horas = self._normalizar_duracion(duracion)  # Valida tipo y rango de la duración
        if (horas * 2) % 1 != 0:  # Verifica que sea múltiplo de media hora
            raise ReservaInvalidaError(f"Las salas se reservan en bloques de 30 minutos; {horas:g} h no es válido.")  # Bloque incorrecto
        return horas  # Devuelve la duración validada

    def calcular_costo(self, duracion: object) -> float:  # Sobrescribe el método abstracto
        """Tarifa por hora, más recargo si la sala es grande, más el proyector si aplica."""
        horas = self.validar_parametros(duracion)  # Valida la duración antes de calcular
        costo = self._tarifa_hora * horas  # Costo por tiempo de uso
        if self._capacidad >= self.CAPACIDAD_GRANDE:  # Sala grande
            costo *= 1 + self.RECARGO_SALA_GRANDE  # Aplica el recargo
        if self._incluye_proyector:  # La sala incluye proyector
            costo += self.COSTO_PROYECTOR  # Suma el valor fijo del proyector
        return costo  # Devuelve el costo base

    def validar(self) -> None:  # Amplía la validación de la clase base
        super().validar()  # Revalida nombre y tarifa
        self._validar_entero(self._capacidad, "capacidad", 2, 50)  # Revalida la capacidad

    def describir(self) -> str:  # Sobrescribe el método abstracto
        proyector = "con proyector" if self._incluye_proyector else "sin proyector"  # Texto del proyector
        return (  # Descripción propia de una sala
            f"[Sala] {self.id} {self._nombre} | {self._capacidad} personas, {proyector} | "
            f"{formatear_moneda(self._tarifa_hora)}/h | {self._texto_estado()}"
        )


class AlquilerEquipo(Servicio):  # Servicio especializado 2
    """Alquiler de equipos por horas completas, con un número limitado de unidades."""

    TIPO = "Alquiler de equipo"  # Nombre del tipo de servicio
    DURACION_MINIMA = 1.0  # Mínimo una hora
    DURACION_MAXIMA = 72.0  # Máximo tres días
    SEGURO = 0.05  # Seguro obligatorio del 5 % sobre el valor del alquiler

    def __init__(self, nombre: str, tarifa_hora: float, tipo_equipo: str, unidades: int) -> None:
        """Crea el servicio validando el tipo de equipo y las unidades disponibles (1 a 100)."""
        self._tipo_equipo = self._validar_texto(tipo_equipo, "tipo de equipo")  # Tipo obligatorio
        self._unidades_totales = self._validar_entero(unidades, "unidades", 1, 100)  # Unidades entre 1 y 100
        self._unidades_disponibles = self._unidades_totales  # Al inicio todas las unidades están libres
        super().__init__(nombre, tarifa_hora)  # Valida los datos comunes y asigna el id

    @property
    def unidades_disponibles(self) -> int:  # Lectura de las unidades libres
        """Unidades que aún pueden alquilarse."""
        return self._unidades_disponibles  # Devuelve las unidades libres

    def verificar_disponibilidad(self) -> None:  # Amplía la verificación de la clase base
        super().verificar_disponibilidad()  # Revisa primero si el servicio está habilitado
        if self._unidades_disponibles == 0:  # No quedan unidades libres
            raise ServicioNoDisponibleError(f"No quedan unidades disponibles de '{self._nombre}'.")  # Sin stock

    def reservar_recurso(self) -> None:  # Sobrescribe: ocupa una unidad
        self.verificar_disponibilidad()  # Verifica que haya una unidad libre
        self._unidades_disponibles -= 1  # Descuenta una unidad

    def liberar_recurso(self) -> None:  # Sobrescribe: devuelve una unidad
        if self._unidades_disponibles < self._unidades_totales:  # Evita superar el total de unidades
            self._unidades_disponibles += 1  # Devuelve una unidad

    def validar_parametros(self, duracion: object) -> float:  # Sobrescribe el método abstracto
        """El equipo se alquila por horas completas."""
        horas = self._normalizar_duracion(duracion)  # Valida tipo y rango de la duración
        if not horas.is_integer():  # Verifica que sean horas enteras
            raise ReservaInvalidaError(f"Los equipos se alquilan por horas completas; {horas:g} h no es válido.")  # Duración incorrecta
        return horas  # Devuelve la duración validada

    def calcular_costo(self, duracion: object) -> float:  # Sobrescribe el método abstracto
        """Tarifa por hora más el seguro obligatorio."""
        horas = self.validar_parametros(duracion)  # Valida la duración antes de calcular
        return self._tarifa_hora * horas * (1 + self.SEGURO)  # Alquiler más seguro

    def validar(self) -> None:  # Amplía la validación de la clase base
        super().validar()  # Revalida nombre y tarifa
        if not (0 <= self._unidades_disponibles <= self._unidades_totales):  # Las unidades deben ser coherentes
            raise ServicioInvalidoError(f"Unidades inconsistentes en '{self._nombre}'.")  # Estado incoherente

    def describir(self) -> str:  # Sobrescribe el método abstracto
        return (  # Descripción propia de un alquiler de equipo
            f"[Equipo] {self.id} {self._nombre} ({self._tipo_equipo}) | "
            f"Unidades libres: {self._unidades_disponibles}/{self._unidades_totales} | "
            f"{formatear_moneda(self._tarifa_hora)}/h + seguro {self.SEGURO:.0%} | {self._texto_estado()}"
        )


class Asesoria(Servicio):  # Servicio especializado 3
    """Asesoría especializada con un consultor asignado."""

    TIPO = "Asesoría especializada"  # Nombre del tipo de servicio
    DURACION_MINIMA = 1.0  # Mínimo una hora
    DURACION_MAXIMA = 6.0  # Máximo seis horas por sesión
    HORAS_PAQUETE = 3.0  # Desde esta duración se aplica el descuento por paquete
    DESCUENTO_PAQUETE = 0.10  # Descuento del 10 % por paquete
    ESPECIALIDADES = ("Desarrollo de software", "Bases de datos", "Ciberseguridad", "Arquitectura en la nube")  # Áreas ofrecidas

    def __init__(self, nombre: str, tarifa_hora: float, especialidad: str, consultor: str) -> None:
        """Crea la asesoría validando que la especialidad exista y que haya un consultor."""
        self._especialidad = self._validar_especialidad(especialidad)  # Especialidad de la lista permitida
        self._consultor = self._validar_texto(consultor, "consultor")  # Consultor obligatorio
        super().__init__(nombre, tarifa_hora)  # Valida los datos comunes y asigna el id

    @classmethod
    def _validar_especialidad(cls, valor: object) -> str:
        """Verifica que la especialidad sea una de las ofrecidas (sin importar mayúsculas)."""
        texto = cls._validar_texto(valor, "especialidad")  # Verifica que exista
        for especialidad in cls.ESPECIALIDADES:  # Recorre las especialidades permitidas
            if especialidad.lower() == texto.lower():  # Compara sin importar mayúsculas
                return especialidad  # Devuelve el nombre oficial
        raise ServicioInvalidoError(  # La especialidad no está en la lista
            f"Especialidad '{texto}' no ofrecida. Opciones: {', '.join(cls.ESPECIALIDADES)}."
        )

    def validar_parametros(self, duracion: object) -> float:  # Sobrescribe el método abstracto
        """Las asesorías se programan en bloques de 30 minutos, entre 1 y 6 horas."""
        horas = self._normalizar_duracion(duracion)  # Valida tipo y rango de la duración
        if (horas * 2) % 1 != 0:  # Verifica que sea múltiplo de media hora
            raise ReservaInvalidaError(f"Las asesorías se programan en bloques de 30 minutos; {horas:g} h no es válido.")  # Bloque incorrecto
        return horas  # Devuelve la duración validada

    def calcular_costo(self, duracion: object) -> float:  # Sobrescribe el método abstracto
        """Tarifa por hora, con descuento por paquete desde 3 horas."""
        horas = self.validar_parametros(duracion)  # Valida la duración antes de calcular
        costo = self._tarifa_hora * horas  # Costo por tiempo de asesoría
        if horas >= self.HORAS_PAQUETE:  # Aplica a sesiones largas
            costo *= 1 - self.DESCUENTO_PAQUETE  # Descuento por paquete
        return costo  # Devuelve el costo base

    def validar(self) -> None:  # Amplía la validación de la clase base
        super().validar()  # Revalida nombre y tarifa
        self._validar_especialidad(self._especialidad)  # Revalida la especialidad
        self._validar_texto(self._consultor, "consultor")  # Revalida el consultor

    def describir(self) -> str:  # Sobrescribe el método abstracto
        return (  # Descripción propia de una asesoría
            f"[Asesoría] {self.id} {self._nombre} | {self._especialidad} con {self._consultor} | "
            f"{formatear_moneda(self._tarifa_hora)}/h | {self._texto_estado()}"
        )
