# Software FJ – Sistema Integral de Gestión de Clientes, Servicios y Reservas

Proyecto del curso **Programación (213023) – UNAD**, Fase 4: *Componente práctico – Prácticas simuladas*.

Sistema **orientado a objetos y sin base de datos** que gestiona los clientes, los servicios (reserva de salas, alquiler de equipos y asesorías especializadas) y las reservas de la empresa Software FJ. Aplica abstracción, herencia, polimorfismo, encapsulación y **manejo avanzado de excepciones**: la aplicación sigue funcionando aunque se presenten errores, y cada evento y error queda registrado en un archivo de logs.

## Requisitos

- Python 3.10 o superior (probado con Python 3.15).
- No necesita librerías externas: solo usa la biblioteca estándar (`abc`, `logging`, `functools`, `enum`, `re`, `pathlib`).

## Ejecución

```bash
python main.py
```

El programa ejecuta 25 simulaciones, muestra el resultado de cada una y el estado final del sistema, y escribe el registro en `logs/software_fj.log` (el archivo se reinicia en cada ejecución). En el repositorio se incluye el log de una ejecución como evidencia.

## Estructura del proyecto

```
software-fj/
├── main.py                    # Programa principal: 25 simulaciones de operaciones completas
├── logs/
│   └── software_fj.log        # Registro de eventos y errores (evidencia de ejecución)
└── software_fj/
    ├── __init__.py
    ├── excepciones.py         # Jerarquía de excepciones personalizadas
    ├── logger_config.py       # Configuración de logging y registro de errores encadenados
    ├── entidad.py             # Clase abstracta Entidad
    ├── cliente.py             # Clase Cliente (encapsulación y validaciones)
    ├── servicios.py           # Clase abstracta Servicio + ReservaSala, AlquilerEquipo, Asesoria
    ├── reserva.py             # Clase Reserva y sus estados
    └── gestor.py              # SistemaGestion: listas internas de clientes, servicios y reservas
```

## Diseño de clases

```
Entidad (abstracta)                  describir(), validar(), id, fecha_creacion
├── Cliente                          datos personales privados + propiedades con validación
├── Servicio (abstracta)             calcular_costo(), validar_parametros(), describir()
│   ├── ReservaSala                  bloques de 30 min, recargo por sala grande, proyector
│   ├── AlquilerEquipo               horas completas, seguro del 5 %, unidades limitadas
│   └── Asesoria                     especialidades, descuento por paquete desde 3 h
└── Reserva                          cliente + servicio + duración + estado
                                     confirmar(), cancelar(), procesar()

SistemaGestion                       listas internas (_clientes, _servicios, _reservas)
```

Ciclo de vida de una reserva:

```
PENDIENTE --confirmar()--> CONFIRMADA --procesar()--> PROCESADA
    |                          |
    +-------cancelar()---------+--> CANCELADA
```

## Cómo se cumple cada requisito

| Requisito | Dónde está |
|---|---|
| Clase abstracta para entidades generales | `Entidad` en `entidad.py` |
| Cliente con validaciones y encapsulación | `Cliente` en `cliente.py`: atributos `__nombre`, `__documento`, `__email`, `__telefono`; propiedades con validación; documento enmascarado |
| Clase abstracta Servicio y tres servicios derivados | `Servicio`, `ReservaSala`, `AlquilerEquipo` y `Asesoria` en `servicios.py` |
| Polimorfismo y métodos sobrescritos | `calcular_costo`, `validar_parametros`, `describir`, `validar`, `verificar_disponibilidad`, `reservar_recurso`, `liberar_recurso` |
| Reserva con confirmación, cancelación y procesamiento | `Reserva` en `reserva.py` |
| Métodos sobrecargados | `calcular_descuento` con `@singledispatchmethod` (float, int, cupón `str`, `None`); `calcular_costo_total` y `cotizar` con parámetros opcionales de impuesto y descuento |
| Listas internas, sin base de datos | `SistemaGestion` en `gestor.py` |
| Excepciones personalizadas | `excepciones.py`: 12 clases con código de error por familia |
| `try/except` | Todas las operaciones de `SistemaGestion` |
| `try/except/else` | `SistemaGestion.registrar_cliente`, `crear_servicio`, `crear_reserva`…; `Reserva.confirmar` |
| `try/finally` | `Reserva.cancelar` (la reserva queda cancelada aunque falle la liberación); `Simulador.servicio_en_mantenimiento` |
| `try/except/else/finally` | `Reserva.procesar`; `Simulador.ejecutar` |
| Encadenamiento (`raise ... from ...`) | `ValueError`/`TypeError` → `ServicioInvalidoError` o `ReservaInvalidaError`; `TypeError` → `ParametroFaltanteError`; `ServicioNoDisponibleError` → `ReservaInvalidaError`; `CalculoInconsistenteError` → `ReservaError` |
| Archivo de logs | `logger_config.py` → `logs/software_fj.log`. `registrar_error` también escribe la causa original de los errores encadenados |
| Al menos 10 operaciones completas | `main.py`: 25 simulaciones |
| La aplicación nunca se detiene | El gestor devuelve `None`/`False` ante errores propios; `Simulador.ejecutar` y `main()` capturan cualquier error no previsto |

## Jerarquía de excepciones

```
SoftwareFJError (SFJ-000)
├── DatosInvalidosError (SFJ-100)
│   ├── ClienteInvalidoError (SFJ-101)
│   ├── ParametroFaltanteError (SFJ-102)
│   ├── ServicioInvalidoError (SFJ-103)
│   └── RegistroDuplicadoError (SFJ-104)
├── ServicioNoDisponibleError (SFJ-200)
├── ReservaError (SFJ-300)
│   ├── ReservaInvalidaError (SFJ-301)
│   └── OperacionNoPermitidaError (SFJ-302)
├── CalculoInconsistenteError (SFJ-400)
└── EntidadNoEncontradaError (SFJ-500)
```

## Simulaciones incluidas

| # | Operación | Resultado esperado |
|---|---|---|
| 1–2 | Registrar clientes válidos | Éxito |
| 3 | Cliente con correo inválido | Rechazo (`ClienteInvalidoError`) |
| 4 | Cliente sin nombre | Rechazo (`ParametroFaltanteError`) |
| 5 | Cliente con documento duplicado | Rechazo (`RegistroDuplicadoError`) |
| 6–8 | Crear sala, equipo y asesoría válidos | Éxito |
| 9 | Sala con tarifa negativa | Rechazo (`ServicioInvalidoError`) |
| 10 | Sala con capacidad "veinte" | Rechazo encadenado (`ValueError` → `ServicioInvalidoError`) |
| 11 | Asesoría sin consultor | Rechazo encadenado (`TypeError` → `ParametroFaltanteError`) |
| 12 | Tipo de servicio inexistente | Rechazo (`ServicioInvalidoError`) |
| 13 | Reserva completa de sala con IVA | Éxito |
| 14 | Reserva completa de asesoría con cupón | Éxito |
| 15 | Reserva de 12 h en sala | Rechazo (`ReservaInvalidaError`) |
| 16 | Reserva con cliente no registrado | Rechazo (`EntidadNoEncontradaError`) |
| 17 | Alquilar la única unidad del equipo | Éxito |
| 18 | Alquilar el equipo sin unidades | Rechazo encadenado (`ServicioNoDisponibleError` → `ReservaInvalidaError`) |
| 19 | Reservar una sala en mantenimiento | Rechazo encadenado |
| 20 | Procesar con 80 % de descuento | Rechazo encadenado (`CalculoInconsistenteError` → `ReservaError`) |
| 21 | Cancelar una reserva confirmada (libera la unidad) | Éxito |
| 22 | Confirmar y procesar la reserva que había quedado pendiente | Éxito |
| 23 | Cancelar una reserva procesada | Rechazo (`OperacionNoPermitidaError`) |
| 24 | Confirmar una reserva cancelada | Rechazo (`OperacionNoPermitidaError`) |
| 25 | Error de programación simulado (`KeyError`) | Capturado por la red de seguridad, registrado con traceback |

Resultado de la ejecución: **10 operaciones exitosas, 14 rechazos controlados y 1 error inesperado controlado; 25/25 con el resultado esperado.**

## Flujo de trabajo en GitHub

Cada módulo se desarrolló en su propia rama, con un issue asignado y un pull request que lo cierra:

| Issue | Rama | Pull request |
|---|---|---|
| #1 Excepciones y logs | `feature/excepciones-logs` | #6 |
| #2 Entidad y Cliente | `feature/entidad-cliente` | #7 |
| #3 Servicios | `feature/servicios` | #8 |
| #4 Reserva y gestor | `feature/reservas-gestor` | #9 |
| #5 Simulaciones y documentación | `feature/simulaciones-docs` | #10 |

## Autor

Oscar Ibarra Cardona – Ingeniería de Sistemas, UNAD.
