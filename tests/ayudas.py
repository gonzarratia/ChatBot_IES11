# -*- coding: utf-8 -*-
"""Datos de prueba compartidos por los tests (árbol de ejemplo, config y atajos)."""
import os
import sys

# Permite correr los tests desde cualquier carpeta: agrega la raíz del proyecto al path.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from ies_bot import bot as motor  # noqa: E402
from ies_bot import config  # noqa: E402


def nodo(id, padre, op, titulo, resp="", links=None, claves=""):
    return {"id": id, "padre_id": padre or config.ID_RAIZ, "opcion": op, "titulo": titulo, "icono": "",
            "respuesta": resp, "links": links or [], "palabras_clave": claves}


NODOS = [
    nodo("1", "", "1", "Trámites administrativos", "Elegí el trámite:"),
    nodo("1.1", "1", "1", "Modelos de Notas", "Descargá el modelo que necesites:",
         [("Nota de equivalencias", "https://x/1")]),
    nodo("1.2", "1", "2", "Constancias", "Pedila en secretaría."),
    nodo("2", "", "2", "Calendario académico", "Las inscripciones abren en marzo.", claves="fechas mesas examenes"),
    nodo("3", "", "3", "Becas", "Hay becas Progresar.", claves="ayuda economica"),
]
ARBOL = motor.construir_arbol(NODOS)
CFG = dict(config.CONFIG_DEFECTO)
CFG_CONTACTO = {**CFG, "direccion": "Av. Siempreviva 123", "telefono": "388-123456",
                "horarios": "Lun a Vie 8 a 20"}
R = config.ID_RAIZ


def bot(txt, nodo_actual=R, cfg=CFG, fallos=0, ir_a=None):
    """Atajo: procesa un mensaje contra el árbol de ejemplo."""
    return motor.procesar_mensaje(txt, nodo_actual, ARBOL, cfg, ir_a, fallos)
