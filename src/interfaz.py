# -*- coding: utf-8 -*-
"""
interfaz.py

Ventana sencilla (Tkinter) para usar el sistema experto sin la terminal.
Pasos para usarla:
  1. Cargar la base de conocimiento (archivo .txt con las reglas).
  2. Marcar los hechos iniciales en la lista, o cargarlos desde un archivo .txt.
  3. Presionar "Iniciar diagnóstico".

Toda la lógica de inferencia está en motor_inferencia.py; aquí solo hay ventana y botones.
Ejecutar:   python src/interfaz.py
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from motor_inferencia import (cargar_reglas, cargar_hechos, hechos_base, hechos_sin_uso,
                              ejecutar_inferencia, texto_de_pasos, texto_de_recomendaciones)

# Datos que la ventana necesita recordar entre un botón y otro
estado = {
    "reglas": [],   # reglas cargadas del archivo de conocimiento
    "base": [],     # hechos que se muestran en la lista (hechos base)
    "extra": []     # hechos cargados desde archivo que no están en la lista
}

CARPETA_PROYECTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


# ---------------------------------------------------------------
# FUNCIONES DE APOYO
# ---------------------------------------------------------------

def nombre_legible(hecho):
    """pc_lento  ->  pc lento  (solo para mostrarlo en la lista)"""
    return hecho.replace("_", " ")


def escribir_en_caja(caja, texto):
    """Reemplaza el contenido de un cuadro de texto (que el usuario no puede editar)."""
    caja.config(state="normal")
    caja.delete("1.0", tk.END)
    caja.insert(tk.END, texto)
    caja.config(state="disabled")


def hechos_del_usuario():
    """Hechos marcados en la lista + hechos extra cargados desde archivo."""
    hechos = []
    for posicion in lista_hechos.curselection():
        hechos.append(estado["base"][posicion])
    for hecho in estado["extra"]:
        if hecho not in hechos:
            hechos.append(hecho)
    return hechos


# ---------------------------------------------------------------
# BOTONES
# ---------------------------------------------------------------

def boton_cargar_reglas():
    ruta = filedialog.askopenfilename(
        title="Elegir base de conocimiento",
        initialdir=os.path.join(CARPETA_PROYECTO, "conocimiento"),
        filetypes=[("Archivos de texto", "*.txt")])
    if ruta == "":
        return   # el usuario canceló

    try:
        reglas = cargar_reglas(ruta)
    except ValueError as error:
        messagebox.showerror("Error al cargar las reglas", str(error))
        return

    estado["reglas"] = reglas
    estado["base"] = hechos_base(reglas)
    estado["extra"] = []

    # Llenar la lista con los hechos base
    lista_hechos.delete(0, tk.END)
    for hecho in estado["base"]:
        lista_hechos.insert(tk.END, nombre_legible(hecho))

    escribir_en_caja(caja_pasos, "")
    escribir_en_caja(caja_recomendacion, "")
    texto_archivo_reglas.set(os.path.basename(ruta) + " (" + str(len(reglas)) + " reglas)")
    texto_estado.set("Base de conocimiento cargada. Ahora marca los hechos que se cumplen.")


def boton_cargar_hechos():
    if len(estado["reglas"]) == 0:
        messagebox.showerror("Falta la base de conocimiento",
                             "Primero carga la base de conocimiento.")
        return

    ruta = filedialog.askopenfilename(
        title="Elegir archivo de hechos",
        initialdir=os.path.join(CARPETA_PROYECTO, "casos"),
        filetypes=[("Archivos de texto", "*.txt")])
    if ruta == "":
        return

    try:
        hechos = cargar_hechos(ruta)
    except ValueError as error:
        messagebox.showerror("Error al cargar los hechos", str(error))
        return

    # Marcar en la lista los hechos que coinciden; los demás quedan como "extra"
    lista_hechos.selection_clear(0, tk.END)
    estado["extra"] = []
    for hecho in hechos:
        if hecho in estado["base"]:
            lista_hechos.selection_set(estado["base"].index(hecho))
        else:
            estado["extra"].append(hecho)

    texto_estado.set("Se cargaron " + str(len(hechos)) + " hechos desde " + os.path.basename(ruta) + ".")

    sin_uso = hechos_sin_uso(hechos, estado["reglas"])
    if len(sin_uso) > 0:
        messagebox.showwarning("Aviso", "Estos hechos no aparecen en ninguna regla "
                               "(revisa que estén bien escritos):\n\n" + "\n".join(sin_uso))


def boton_diagnosticar():
    if len(estado["reglas"]) == 0:
        messagebox.showerror("Falta la base de conocimiento",
                             "Primero carga la base de conocimiento.")
        return

    hechos = hechos_del_usuario()
    if len(hechos) == 0:
        messagebox.showwarning("Faltan hechos",
                               "Marca al menos un hecho en la lista o carga un archivo de hechos.")
        return

    resultado = ejecutar_inferencia(hechos, estado["reglas"])
    escribir_en_caja(caja_pasos, texto_de_pasos(resultado))
    escribir_en_caja(caja_recomendacion, texto_de_recomendaciones(resultado))
    texto_estado.set("Diagnóstico terminado: " + str(len(resultado["pasos"])) + " reglas disparadas.")


def boton_limpiar():
    lista_hechos.selection_clear(0, tk.END)
    estado["extra"] = []
    escribir_en_caja(caja_pasos, "")
    escribir_en_caja(caja_recomendacion, "")
    texto_estado.set("Listo para un nuevo caso.")


# ---------------------------------------------------------------
# CONSTRUCCIÓN DE LA VENTANA
# ---------------------------------------------------------------

if __name__ == "__main__":
    ventana = tk.Tk()
    ventana.title("Sistema experto: diagnóstico de problemas de un computador")
    ventana.geometry("1000x680")

    texto_archivo_reglas = tk.StringVar()
    texto_archivo_reglas.set("Ninguna base de conocimiento cargada")
    texto_estado = tk.StringVar()
    texto_estado.set("Primero carga la base de conocimiento.")

    # Parte de arriba: botón para cargar las reglas
    marco_superior = tk.Frame(ventana)
    marco_superior.pack(fill="x", padx=10, pady=8)
    tk.Button(marco_superior, text="1. Cargar base de conocimiento",
              command=boton_cargar_reglas).pack(side="left")
    tk.Label(marco_superior, textvariable=texto_archivo_reglas).pack(side="left", padx=10)

    marco_central = tk.Frame(ventana)
    marco_central.pack(fill="both", expand=True, padx=10)

    # Columna izquierda: lista de hechos y botones
    marco_izquierdo = tk.LabelFrame(marco_central, text="2. Hechos iniciales (clic en los que se cumplen)")
    marco_izquierdo.pack(side="left", fill="y", padx=(0, 10))

    marco_lista = tk.Frame(marco_izquierdo)
    marco_lista.pack(fill="both", expand=True, padx=5, pady=5)
    barra = tk.Scrollbar(marco_lista)
    lista_hechos = tk.Listbox(marco_lista, selectmode=tk.MULTIPLE, exportselection=False,
                              width=38, yscrollcommand=barra.set)
    barra.config(command=lista_hechos.yview)
    barra.pack(side="right", fill="y")
    lista_hechos.pack(side="left", fill="both", expand=True)

    tk.Button(marco_izquierdo, text="Cargar hechos desde archivo (opcional)",
              command=boton_cargar_hechos).pack(fill="x", padx=5, pady=2)
    tk.Button(marco_izquierdo, text="3. Iniciar diagnóstico",
              command=boton_diagnosticar).pack(fill="x", padx=5, pady=2)
    tk.Button(marco_izquierdo, text="Limpiar",
              command=boton_limpiar).pack(fill="x", padx=5, pady=(2, 5))

    # Columna derecha: razonamiento y recomendación
    marco_derecho = tk.Frame(marco_central)
    marco_derecho.pack(side="left", fill="both", expand=True)

    marco_pasos = tk.LabelFrame(marco_derecho, text="Razonamiento paso a paso")
    marco_pasos.pack(fill="both", expand=True)
    caja_pasos = scrolledtext.ScrolledText(marco_pasos, wrap="word", font="TkFixedFont",
                                           state="disabled")
    caja_pasos.pack(fill="both", expand=True, padx=5, pady=5)

    marco_recomendacion = tk.LabelFrame(marco_derecho, text="Recomendación del sistema")
    marco_recomendacion.pack(fill="x", pady=(8, 0))
    caja_recomendacion = scrolledtext.ScrolledText(marco_recomendacion, wrap="word", height=8,
                                                   state="disabled")
    caja_recomendacion.pack(fill="x", padx=5, pady=5)

    # Parte de abajo: mensajes para el usuario
    tk.Label(ventana, textvariable=texto_estado, anchor="w").pack(fill="x", padx=10, pady=6)

    ventana.mainloop()
