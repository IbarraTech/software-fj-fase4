"""
Módulo: cliente.py

Define la clase Cliente con sus datos personales encapsulados (atributos
privados) y validaciones estrictas en cada propiedad.
"""

import re  # Expresiones regulares para validar formatos de texto

from .entidad import Entidad  # Clase abstracta base
from .excepciones import ClienteInvalidoError, ParametroFaltanteError  # Errores propios del cliente

PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü]+( [A-Za-zÁÉÍÓÚáéíóúÑñÜü]+)+$")  # Al menos nombre y apellido, solo letras
PATRON_DOCUMENTO = re.compile(r"^\d{6,12}$")  # Entre 6 y 12 dígitos
PATRON_EMAIL = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")  # usuario@dominio.ext
PATRON_TELEFONO = re.compile(r"^\d{7,10}$")  # Entre 7 y 10 dígitos


class Cliente(Entidad):  # Cliente hereda de la clase abstracta Entidad
    """Cliente de Software FJ con datos personales protegidos."""

    PREFIJO = "CLI"  # Los identificadores de clientes serán CLI-001, CLI-002...

    def __init__(self, nombre: str, documento: str | int, email: str, telefono: str | None = None) -> None:
        """
        Crea un cliente validando cada dato antes de aceptarlo.

        :raises ParametroFaltanteError: si falta un dato obligatorio.
        :raises ClienteInvalidoError: si un dato tiene un formato incorrecto.
        """
        self.__documento = self._validar_documento(documento)  # El documento no tiene setter: no cambia después
        self.nombre = nombre  # Usa el setter, que valida el nombre
        self.email = email  # Usa el setter, que valida el correo
        self.telefono = telefono  # Usa el setter, que valida el teléfono (opcional)
        super().__init__()  # Asigna id y fecha solo cuando todos los datos son válidos

    # ------------------------------------------------------------------
    # Validaciones (métodos estáticos reutilizables)
    # ------------------------------------------------------------------
    @staticmethod
    def _texto_obligatorio(valor: object, campo: str) -> str:
        """Comprueba que el valor exista y sea texto; devuelve el texto sin espacios sobrantes."""
        if valor is None:  # El dato no fue enviado
            raise ParametroFaltanteError(f"El campo '{campo}' del cliente es obligatorio.")  # Falta el parámetro
        if not isinstance(valor, str):  # El dato llegó con un tipo incorrecto
            raise ClienteInvalidoError(f"El campo '{campo}' debe ser texto; se recibió {type(valor).__name__}.")  # Tipo inválido
        texto = valor.strip()  # Elimina espacios al inicio y al final
        if not texto:  # Llegó una cadena vacía o solo con espacios
            raise ParametroFaltanteError(f"El campo '{campo}' del cliente no puede estar vacío.")  # Parámetro vacío
        return texto  # Devuelve el texto limpio

    @classmethod
    def _validar_nombre(cls, valor: object) -> str:
        """Valida que el nombre tenga al menos nombre y apellido y solo letras."""
        nombre = cls._texto_obligatorio(valor, "nombre")  # Primero verifica que exista
        nombre = " ".join(nombre.split())  # Reduce espacios internos repetidos a uno solo
        if not PATRON_NOMBRE.match(nombre) or len(nombre) > 60:  # Revisa formato y longitud máxima
            raise ClienteInvalidoError(f"Nombre inválido: '{nombre}'. Use nombre y apellido, solo letras (máx. 60).")  # Formato incorrecto
        return nombre.title()  # Devuelve el nombre con mayúscula inicial en cada palabra

    @classmethod
    def _validar_documento(cls, valor: object) -> str:
        """Valida que el documento sea numérico, de 6 a 12 dígitos."""
        if isinstance(valor, int) and not isinstance(valor, bool):  # Acepta el documento como número entero
            valor = str(valor)  # Lo convierte a texto para validarlo igual que una cadena
        documento = cls._texto_obligatorio(valor, "documento")  # Verifica que exista
        if not PATRON_DOCUMENTO.match(documento):  # Revisa que solo tenga dígitos y la longitud correcta
            raise ClienteInvalidoError(f"Documento inválido: '{documento}'. Debe tener entre 6 y 12 dígitos.")  # Formato incorrecto
        return documento  # Devuelve el documento validado

    @classmethod
    def _validar_email(cls, valor: object) -> str:
        """Valida que el correo tenga el formato usuario@dominio.ext."""
        email = cls._texto_obligatorio(valor, "email").lower()  # Verifica que exista y lo pasa a minúsculas
        if not PATRON_EMAIL.match(email):  # Revisa el formato del correo
            raise ClienteInvalidoError(f"Correo electrónico inválido: '{email}'.")  # Formato incorrecto
        return email  # Devuelve el correo validado

    @staticmethod
    def _validar_telefono(valor: object) -> str | None:
        """Valida el teléfono (opcional): si se envía, debe tener entre 7 y 10 dígitos."""
        if valor is None or (isinstance(valor, str) and not valor.strip()):  # El teléfono es opcional
            return None  # Sin teléfono registrado
        telefono = str(valor).strip()  # Convierte a texto (por si llega como número)
        if not PATRON_TELEFONO.match(telefono):  # Revisa que solo tenga dígitos y la longitud correcta
            raise ClienteInvalidoError(f"Teléfono inválido: '{telefono}'. Debe tener entre 7 y 10 dígitos.")  # Formato incorrecto
        return telefono  # Devuelve el teléfono validado

    # ------------------------------------------------------------------
    # Propiedades: acceso controlado a los atributos privados
    # ------------------------------------------------------------------
    @property
    def nombre(self) -> str:  # Lectura del nombre
        """Nombre completo del cliente."""
        return self.__nombre  # Devuelve el atributo privado

    @nombre.setter
    def nombre(self, valor: str) -> None:  # Escritura del nombre con validación
        self.__nombre = self._validar_nombre(valor)  # Solo se guarda si es válido

    @property
    def documento(self) -> str:  # Solo lectura: el documento identifica al cliente y no cambia
        """Número de documento del cliente."""
        return self.__documento  # Devuelve el atributo privado

    @property
    def documento_protegido(self) -> str:  # Versión enmascarada para mostrar en pantalla y en logs
        """Documento con los primeros dígitos ocultos (protección de datos personales)."""
        return "*" * (len(self.__documento) - 4) + self.__documento[-4:]  # Solo deja ver los últimos 4 dígitos

    @property
    def email(self) -> str:  # Lectura del correo
        """Correo electrónico del cliente."""
        return self.__email  # Devuelve el atributo privado

    @email.setter
    def email(self, valor: str) -> None:  # Escritura del correo con validación
        self.__email = self._validar_email(valor)  # Solo se guarda si es válido

    @property
    def telefono(self) -> str | None:  # Lectura del teléfono
        """Teléfono del cliente (puede ser None)."""
        return self.__telefono  # Devuelve el atributo privado

    @telefono.setter
    def telefono(self, valor: str | None) -> None:  # Escritura del teléfono con validación
        self.__telefono = self._validar_telefono(valor)  # Solo se guarda si es válido

    # ------------------------------------------------------------------
    # Implementación de los métodos abstractos de Entidad
    # ------------------------------------------------------------------
    def validar(self) -> None:
        """Vuelve a comprobar todos los datos del cliente (por ejemplo, antes de una reserva)."""
        self._validar_nombre(self.__nombre)  # Revalida el nombre
        self._validar_documento(self.__documento)  # Revalida el documento
        self._validar_email(self.__email)  # Revalida el correo
        self._validar_telefono(self.__telefono)  # Revalida el teléfono

    def describir(self) -> str:
        """Descripción del cliente sin exponer el documento completo."""
        telefono = self.__telefono or "sin teléfono"  # Texto alternativo si no hay teléfono
        return f"Cliente {self.id}: {self.__nombre} | Doc: {self.documento_protegido} | {self.__email} | {telefono}"  # Resumen
