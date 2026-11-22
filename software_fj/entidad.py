"""
Módulo: entidad.py

Define la clase abstracta Entidad, que representa cualquier elemento
general del sistema (clientes, servicios y reservas). Aporta un
identificador único, la fecha de creación y obliga a las clases hijas a
implementar los métodos describir() y validar().
"""

from abc import ABC, abstractmethod  # Herramientas para crear clases y métodos abstractos
from datetime import datetime  # Permite registrar la fecha y hora de creación
from itertools import count  # Generador de números consecutivos para los identificadores


class Entidad(ABC):  # Clase abstracta: no se puede instanciar directamente
    """Clase base abstracta de todas las entidades del sistema Software FJ."""

    PREFIJO = "ENT"  # Prefijo del identificador; cada clase hija define el suyo
    _contadores: dict[str, count] = {}  # Un contador independiente por cada prefijo

    def __init__(self) -> None:
        """
        Asigna el identificador y la fecha de creación.

        Las clases hijas llaman a este constructor al FINAL de su propio
        constructor, después de validar todos sus datos. Así, un objeto con
        datos inválidos nunca consume un identificador.
        """
        prefijo = type(self).PREFIJO  # Toma el prefijo de la clase concreta (CLI, SRV, RES...)
        if prefijo not in Entidad._contadores:  # Si es la primera entidad de ese tipo
            Entidad._contadores[prefijo] = count(1)  # Crea su contador iniciando en 1
        numero = next(Entidad._contadores[prefijo])  # Obtiene el siguiente número disponible
        self._id = f"{prefijo}-{numero:03d}"  # Identificador legible, por ejemplo CLI-001
        self._fecha_creacion = datetime.now()  # Momento exacto de creación

    @property
    def id(self) -> str:  # Propiedad de solo lectura: el identificador no se puede modificar
        """Identificador único de la entidad."""
        return self._id  # Devuelve el identificador

    @property
    def fecha_creacion(self) -> datetime:  # Propiedad de solo lectura
        """Fecha y hora en que se creó la entidad."""
        return self._fecha_creacion  # Devuelve la fecha de creación

    @abstractmethod
    def describir(self) -> str:  # Cada entidad debe saber describirse
        """Devuelve una descripción legible de la entidad."""

    @abstractmethod
    def validar(self) -> None:  # Cada entidad debe verificar que su estado sea coherente
        """Verifica que los datos de la entidad sean válidos; lanza una excepción si no lo son."""

    def __str__(self) -> str:  # Representación en texto al usar print() o str()
        return self.describir()  # Reutiliza la descripción polimórfica de cada clase hija
