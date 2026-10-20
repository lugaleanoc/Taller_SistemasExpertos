# Sistema experto: diagnóstico de problemas comunes de un computador

Taller de Sistemas Expertos 2026-2S, Universidad Nacional de Colombia, sede Manizales.

Sistema experto basado en reglas (encadenamiento hacia adelante) que, a partir de los síntomas que indica el usuario, diagnostica problemas comunes de un computador (fallas de Internet, lentitud y problemas de encendido) y entrega una recomendación, mostrando el razonamiento paso a paso. Parte del motor de inferencia entregado en clase.

## Integrantes

- Angie Vanessa Loaiza Quintero
- Sofia Muñoz Buritica
- Luz Amanda Galeano Ceballos

## Requisitos previos y dependencias

- Python 3.
- Tkinter, para la interfaz. Viene incluido con Python en Windows y macOS. En Linux, si falta: `sudo apt install python3-tk`.
- No hay librerías externas: no se necesita `pip install`.

## Instalación

```
git clone https://github.com/lugaleanoc/Taller_SistemasExpertos.git
cd Taller_SistemasExpertos
```

(También se puede descargar el repositorio como ZIP y descomprimirlo.)

## Ejecución

Con interfaz gráfica:

```
python src/interfaz.py
```

1. Presionar **Cargar base de conocimiento** y elegir `diagnostico_pc.txt`.
2. Marcar en la lista los hechos que se cumplen, o presionar **Cargar hechos desde archivo** y elegir uno de `casos/`.
3. Presionar **Iniciar diagnóstico**. A la derecha aparecen el razonamiento paso a paso y la recomendación.

Sin interfaz (desde la terminal):

```
python src/motor_inferencia.py conocimiento/diagnostico_pc.txt casos/caso_lentitud.txt
```

En algunos sistemas el comando es `python3` o `py` en lugar de `python`.

## Cómo cargar las reglas y los hechos

**Reglas** (`diagnostico_pc.txt`): una regla por línea, con cuatro campos separados por `|`:

```
id | antecedentes | consecuentes | recomendación
R16 | ram_insuficiente | recomendar_ampliar_ram | La memoria RAM parece insuficiente para el uso actual. Considerar ampliarla.
```

- Los antecedentes y los consecuentes se separan con comas. Los hechos son palabras sin espacios (se usa `_`).
- La regla se dispara cuando **todos** sus antecedentes están en la memoria de trabajo.
- La recomendación es opcional: si existe, la regla llega a una recomendación; si no, es un paso intermedio.
- Las líneas que empiezan con `#` son comentarios.

**Hechos iniciales** (`casos/*.txt`): un hecho por línea. Las líneas con `#` son comentarios.

```
pc_lento
uso_ram_alto
uso_disco_alto
```

Si un archivo tiene un error (id repetido, hecho con espacios, regla incompleta, archivo inexistente), el sistema muestra un mensaje con el número de línea.

## Ejemplo de uso

Con `casos/caso_lentitud.txt` (`pc_lento`, `uso_ram_alto`, `pocos_programas_abiertos`, `uso_disco_alto`, `disco_hdd`), el sistema dispara 7 reglas en cadena (R07, R11, R08, R12, R15, R17, R16) y llega a tres recomendaciones: actualizar el hardware (R15), cambiar el disco duro por un SSD (R17) y ampliar la memoria RAM (R16).

Otros casos de ejemplo: `caso_sin_internet.txt` y `caso_no_enciende.txt`.

## Estrategia de resolución de conflictos

Cuando varias reglas se pueden aplicar, se elige una con estos criterios, en orden:

1. No repetir reglas ya disparadas.
2. Más antecedentes (especificidad).
3. Hecho más reciente (actualidad).
4. Orden de aparición en el archivo.

La justificación y las referencias están en el documento técnico.

## Estructura de carpetas

```
Taller_SistemaExperto/
├── src/
│   ├── motor_inferencia.py    # carga de archivos y motor de inferencia (sin ventanas)
│   └── interfaz.py            # ventana de Tkinter
├── conocimiento/
│   └── diagnostico_pc.txt     # base de conocimiento (20 reglas)
├── casos/
│   ├── caso_lentitud.txt      # hechos iniciales de ejemplo
│   ├── caso_sin_internet.txt
│   └── caso_no_enciende.txt
├── docs/
│   └── documento_tecnico      # documento técnico (2 a 4 páginas)
└── README.md
```

## Limitaciones conocidas

- Los hechos solo están presentes o ausentes: no hay grados de certeza.
- No detecta hechos contradictorios (por ejemplo, marcar `wifi_conectado` y `wifi_desconectado`).
- Un mismo problema puede dar varias recomendaciones parecidas.
- Los hechos se ingresan antes de ejecutar; el sistema no hace preguntas durante la inferencia.
- Las recomendaciones son orientativas y no reemplazan la revisión de un técnico.

## Uso de IA generativa

Se usó Claude (Anthropic) como apoyo para el código y el documento técnico. Los detalles están en el documento técnico.