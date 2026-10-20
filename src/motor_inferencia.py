# -*- coding: utf-8 -*-
"""
motor_inferencia.py

Motor de inferencia con encadenamiento hacia adelante (forward chaining).
Parte del motor entregado por el profesor, pero:
  - las reglas y los hechos se leen desde archivos .txt
  - solo cuentan los hechos que el usuario realmente tiene (corrige el error de los valores False)
  - la resolución de conflictos usa 4 criterios (ver elegir_regla)
  - el resultado se guarda paso a paso para poder mostrarlo

Este archivo no usa ventanas: la interfaz está en interfaz.py.
Uso desde la terminal:
    python src/motor_inferencia.py conocimiento/diagnostico_pc.txt casos/caso_lentitud.txt
"""

import sys


# ---------------------------------------------------------------
# 1. LECTURA DE ARCHIVOS
# ---------------------------------------------------------------

def leer_lineas_utiles(ruta):
    """Lee un archivo y devuelve una lista de (numero_de_linea, texto),
    sin líneas vacías ni comentarios (los que empiezan con #)."""
    try:
        # utf-8-sig también funciona si el archivo se guardó con BOM (Bloc de notas)
        with open(ruta, "r", encoding="utf-8-sig") as archivo:
            lineas = archivo.readlines()
    except FileNotFoundError:
        raise ValueError("No se encontró el archivo: " + str(ruta))
    except UnicodeDecodeError:
        raise ValueError("El archivo " + str(ruta) + " debe estar guardado en formato UTF-8.")
    except OSError:
        raise ValueError("No se pudo abrir el archivo: " + str(ruta))

    utiles = []
    numero = 0
    for linea in lineas:
        numero = numero + 1
        texto = linea.strip()
        if texto != "" and not texto.startswith("#"):
            utiles.append((numero, texto))
    return utiles


def limpiar_nombre_hecho(texto, numero_linea):
    """Un hecho es una palabra sin espacios (por ejemplo: pc_lento)."""
    nombre = texto.strip().lower()
    if nombre == "":
        raise ValueError("Línea " + str(numero_linea) + ": hay un hecho vacío.")
    if " " in nombre:
        raise ValueError("Línea " + str(numero_linea) + ": el hecho '" + nombre
                         + "' tiene espacios. Usa guion bajo (_) en lugar de espacios.")
    return nombre


def separar_hechos(texto, numero_linea, nombre_campo):
    """Convierte 'a, b, c' en la lista ['a', 'b', 'c']."""
    if texto.strip() == "":
        raise ValueError("Línea " + str(numero_linea) + ": la regla no tiene " + nombre_campo + ".")
    lista = []
    for pedazo in texto.split(","):
        lista.append(limpiar_nombre_hecho(pedazo, numero_linea))
    return lista


def cargar_reglas(ruta):
    """Carga la base de conocimiento. Cada regla queda como un diccionario:
        {"nombre": "R07", "antecedentes": [...], "consecuentes": [...], "recomendacion": "..."}
    Si hay un error en el archivo, lanza ValueError con un mensaje claro."""
    reglas = []
    nombres_usados = []

    for numero, texto in leer_lineas_utiles(ruta):
        partes = []
        for parte in texto.split("|"):
            partes.append(parte.strip())

        if len(partes) != 3 and len(partes) != 4:
            raise ValueError("Línea " + str(numero) + ": la regla debe tener el formato "
                             "'id | antecedentes | consecuentes | recomendación'.")

        nombre = partes[0]
        if nombre == "":
            raise ValueError("Línea " + str(numero) + ": la regla no tiene id.")
        if nombre in nombres_usados:
            raise ValueError("Línea " + str(numero) + ": el id '" + nombre + "' está repetido.")
        nombres_usados.append(nombre)

        regla = {
            "nombre": nombre,
            "antecedentes": separar_hechos(partes[1], numero, "antecedentes"),
            "consecuentes": separar_hechos(partes[2], numero, "consecuentes"),
            "recomendacion": ""
        }
        if len(partes) == 4:
            regla["recomendacion"] = partes[3]
        reglas.append(regla)

    if len(reglas) == 0:
        raise ValueError("El archivo de conocimiento no tiene ninguna regla.")
    return reglas


def cargar_hechos(ruta):
    """Carga los hechos iniciales (uno por línea). Quita los repetidos."""
    hechos = []
    for numero, texto in leer_lineas_utiles(ruta):
        hecho = limpiar_nombre_hecho(texto, numero)
        if hecho not in hechos:
            hechos.append(hecho)
    if len(hechos) == 0:
        raise ValueError("El archivo de hechos no tiene ningún hecho.")
    return hechos


# ---------------------------------------------------------------
# 2. FUNCIONES DE APOYO
# ---------------------------------------------------------------

def hechos_base(reglas):
    """Hechos que se pueden preguntar al usuario: aparecen como antecedente
    pero ninguna regla los produce (no son consecuente de nadie)."""
    producidos = []
    for regla in reglas:
        for consecuente in regla["consecuentes"]:
            producidos.append(consecuente)

    base = []
    for regla in reglas:
        for antecedente in regla["antecedentes"]:
            if antecedente not in producidos and antecedente not in base:
                base.append(antecedente)
    return base


def hechos_sin_uso(hechos, reglas):
    """Hechos ingresados que no aparecen en ninguna regla (posible error al escribirlos)."""
    usados = []
    for regla in reglas:
        for antecedente in regla["antecedentes"]:
            usados.append(antecedente)

    sin_uso = []
    for hecho in hechos:
        if hecho not in usados:
            sin_uso.append(hecho)
    return sin_uso


# ---------------------------------------------------------------
# 3. MOTOR DE INFERENCIA
# ---------------------------------------------------------------

def buscar_reglas_aplicables(reglas, memoria, disparadas):
    """Conjunto de conflictos: reglas NO disparadas cuyos antecedentes
    están todos en la memoria de trabajo."""
    aplicables = []
    for regla in reglas:
        if regla["nombre"] in disparadas:        # criterio 1: no repetir reglas
            continue
        cumple = True
        for antecedente in regla["antecedentes"]:
            if antecedente not in memoria:
                cumple = False
        if cumple:
            aplicables.append(regla)
    return aplicables


def recencia_de_regla(regla, antiguedad):
    """Qué tan nuevo es el hecho más nuevo que usa la regla.
    antiguedad[hecho] = ciclo en que entró a la memoria (0 = hecho inicial)."""
    mayor = 0
    for antecedente in regla["antecedentes"]:
        if antiguedad[antecedente] > mayor:
            mayor = antiguedad[antecedente]
    return mayor


def elegir_regla(conflicto, antiguedad):
    """Resuelve el conflicto. Devuelve (regla_elegida, razon).
    Orden de criterios:
      1. (ya aplicado antes) no repetir reglas disparadas
      2. más antecedentes (especificidad)
      3. hecho más reciente (actualidad)
      4. orden del archivo (la lista 'conflicto' ya viene en ese orden)"""
    if len(conflicto) == 1:
        return conflicto[0], "es la única regla aplicable"

    # Criterio 2: especificidad
    mayor = 0
    for regla in conflicto:
        if len(regla["antecedentes"]) > mayor:
            mayor = len(regla["antecedentes"])
    candidatas = []
    for regla in conflicto:
        if len(regla["antecedentes"]) == mayor:
            candidatas.append(regla)
    if len(candidatas) == 1:
        return candidatas[0], "tiene más antecedentes (" + str(mayor) + ")"

    # Criterio 3: actualidad
    mas_reciente = 0
    for regla in candidatas:
        if recencia_de_regla(regla, antiguedad) > mas_reciente:
            mas_reciente = recencia_de_regla(regla, antiguedad)
    nuevas_candidatas = []
    for regla in candidatas:
        if recencia_de_regla(regla, antiguedad) == mas_reciente:
            nuevas_candidatas.append(regla)
    if len(nuevas_candidatas) == 1:
        return nuevas_candidatas[0], ("empata en antecedentes, pero usa un hecho más reciente "
                                      "(agregado en el ciclo " + str(mas_reciente) + ")")

    # Criterio 4: orden del archivo
    return nuevas_candidatas[0], "empate en todo; se elige la primera según el orden del archivo"


def ejecutar_inferencia(hechos_iniciales, reglas):
    """Ejecuta el encadenamiento hacia adelante y devuelve un diccionario con
    todo lo ocurrido (pasos, memoria final y recomendaciones)."""
    memoria = list(hechos_iniciales)       # memoria de trabajo
    antiguedad = {}                         # ciclo en que entró cada hecho
    for hecho in memoria:
        antiguedad[hecho] = 0

    disparadas = []                         # nombres de reglas ya disparadas
    pasos = []
    recomendaciones = []
    ciclo = 0

    while True:
        conflicto = buscar_reglas_aplicables(reglas, memoria, disparadas)
        if len(conflicto) == 0:
            break                           # nada más que hacer

        ciclo = ciclo + 1
        regla, razon = elegir_regla(conflicto, antiguedad)
        disparadas.append(regla["nombre"])

        # Agregar los consecuentes a la memoria (sin duplicar hechos)
        nuevos = []
        for consecuente in regla["consecuentes"]:
            if consecuente not in memoria:
                memoria.append(consecuente)
                antiguedad[consecuente] = ciclo
                nuevos.append(consecuente)

        if regla["recomendacion"] != "":
            recomendaciones.append({"regla": regla["nombre"], "texto": regla["recomendacion"]})

        nombres_conflicto = []
        for r in conflicto:
            nombres_conflicto.append(r["nombre"])

        pasos.append({
            "ciclo": ciclo,
            "conflicto": nombres_conflicto,
            "regla": regla,
            "razon": razon,
            "nuevos": nuevos
        })

    return {
        "hechos_iniciales": list(hechos_iniciales),
        "pasos": pasos,
        "memoria_final": memoria,
        "recomendaciones": recomendaciones
    }


# ---------------------------------------------------------------
# 4. TEXTO DEL RESULTADO (lo usan la terminal y la interfaz)
# ---------------------------------------------------------------

def texto_de_pasos(resultado):
    """Explica el razonamiento paso a paso: hechos iniciales, reglas
    elegidas, hechos nuevos y memoria de trabajo final."""
    lineas = []
    lineas.append("HECHOS INICIALES: " + ", ".join(resultado["hechos_iniciales"]))
    lineas.append("")

    for paso in resultado["pasos"]:
        regla = paso["regla"]
        lineas.append("--- Ciclo " + str(paso["ciclo"]) + " ---")
        lineas.append("Conjunto de conflictos: " + ", ".join(paso["conflicto"]))
        lineas.append("Regla elegida: " + regla["nombre"] + " (" + paso["razon"] + ")")
        lineas.append("   SI " + " Y ".join(regla["antecedentes"]))
        lineas.append("   ENTONCES " + ", ".join(regla["consecuentes"]))
        if len(paso["nuevos"]) > 0:
            lineas.append("Hechos nuevos en la memoria: " + ", ".join(paso["nuevos"]))
        else:
            lineas.append("Hechos nuevos en la memoria: ninguno (ya existían)")
        lineas.append("")

    if len(resultado["pasos"]) == 0:
        lineas.append("Ninguna regla se pudo aplicar con estos hechos.")
        lineas.append("")

    lineas.append("MEMORIA DE TRABAJO FINAL: " + ", ".join(resultado["memoria_final"]))
    return "\n".join(lineas)


def texto_de_recomendaciones(resultado):
    """Texto con la recomendación final (una línea por regla que recomienda)."""
    lineas = []
    if len(resultado["recomendaciones"]) == 0:
        lineas.append("No se llegó a ninguna recomendación con los hechos ingresados.")
    else:
        for recomendacion in resultado["recomendaciones"]:
            lineas.append("[" + recomendacion["regla"] + "] " + recomendacion["texto"])
    return "\n".join(lineas)


def texto_del_resultado(resultado):
    """Todo junto (se usa en la terminal)."""
    texto = texto_de_pasos(resultado) + "\n\nRECOMENDACIONES:\n"
    for linea in texto_de_recomendaciones(resultado).split("\n"):
        texto = texto + "   " + linea + "\n"
    return texto.rstrip("\n")


# ---------------------------------------------------------------
# 5. EJECUCIÓN DESDE LA TERMINAL
# ---------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python src/motor_inferencia.py <archivo_de_reglas.txt> <archivo_de_hechos.txt>")
    else:
        try:
            las_reglas = cargar_reglas(sys.argv[1])
            los_hechos = cargar_hechos(sys.argv[2])
            for sospechoso in hechos_sin_uso(los_hechos, las_reglas):
                print("AVISO: el hecho '" + sospechoso + "' no aparece en ninguna regla.")
            print(texto_del_resultado(ejecutar_inferencia(los_hechos, las_reglas)))
        except ValueError as error:
            print("ERROR: " + str(error))
