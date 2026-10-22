# -*- coding: utf-8 -*-
"""Capa de datos: lectura de la planilla de Google Sheets con caché de 5 minutos.

Es el ÚNICO módulo que habla con Google. Devuelve estructuras simples (dicts y listas) aptas para el
caché de Streamlit, nunca objetos de gspread. El acceso es de solo lectura a propósito."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple

import gspread
import streamlit as st

from .config import CACHE_TTL_SEGUNDOS, ID_RAIZ, SCOPES
import threading
import logging

# Esta línea puede que ya la tengas arriba, si no la tenés, agregala
logger = logging.getLogger(__name__)

def _cargar_credenciales() -> Dict[str, Any]:
    """
    Obtiene el JSON de la cuenta de servicio de Google. Orden de búsqueda:
        1) st.secrets["gcp_service_account"]   → Streamlit Community Cloud
        2) Variable GCP_SERVICE_ACCOUNT_JSON   → JSON completo en una variable de entorno
        3) Archivo (GCP_CREDENTIALS_FILE, por defecto ./credentials.json) → Docker (volumen)
    """
    try:
        if "gcp_service_account" in st.secrets:
            return dict(st.secrets["gcp_service_account"])
    except Exception:
        pass

    crudo = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
    if crudo:
        return json.loads(crudo)

    ruta = os.environ.get("GCP_CREDENTIALS_FILE", "credentials.json")
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as archivo:
            return json.load(archivo)

    raise RuntimeError(
        "No se encontraron credenciales de Google. Definí 'gcp_service_account' en "
        "secrets, la variable GCP_SERVICE_ACCOUNT_JSON o montá credentials.json."
    )


@st.cache_resource(show_spinner=False)
def obtener_cliente() -> gspread.Client:
    """Crea UN solo cliente gspread por proceso (se reutiliza entre sesiones)."""
    return gspread.service_account_from_dict(_cargar_credenciales(), scopes=SCOPES)


def _normalizar_fila(fila: Dict[str, Any]) -> Dict[str, str]:
    """Encabezados en minúsculas y todos los valores como texto sin espacios sobrantes."""
    return {str(k).strip().lower(): str(v).strip() for k, v in fila.items()}


def _parsear_links(urls: str, textos: str) -> List[Tuple[str, str]]:
    """
    Convierte las columnas link_url / link_texto en pares (texto, url).
    Admite VARIOS links por fila separándolos con '|'. Solo se aceptan http(s).
    """
    lista_urls = [u.strip() for u in urls.split("|") if u.strip()]
    lista_textos = [t.strip() for t in textos.split("|")]
    links: List[Tuple[str, str]] = []
    for i, url in enumerate(lista_urls):
        if not url.lower().startswith(("http://", "https://")):
            continue  # Descarta valores raros (p. ej. "javascript:...")
        texto = lista_textos[i] if i < len(lista_textos) and lista_textos[i] else "Descargar archivo"
        # Evita que espacios o paréntesis rompan la sintaxis Markdown [texto](url).
        url_segura = url.replace(" ", "%20").replace("(", "%28").replace(")", "%29")
        texto_seguro = texto.replace("[", "(").replace("]", ")")
        links.append((texto_seguro, url_segura))
    return links


@st.cache_data(ttl=CACHE_TTL_SEGUNDOS, show_spinner="Cargando información institucional…")
def cargar_datos(sheet_id: str, hoja_menu: str, hoja_config: str) -> Dict[str, Any]:
    """
    Lee la planilla y devuelve datos simples (dicts/listas) aptos para el caché.
    Con ttl=300 la API de Google se consulta como máximo una vez cada 5 minutos,
    sin importar cuántos alumnos usen el bot en simultáneo.
    """
    libro = obtener_cliente().open_by_key(sheet_id)

    # numericise_ignore=["all"] evita que "01" se convierta en 1 o "1.0" en float.
    filas_menu = libro.worksheet(hoja_menu).get_all_records(numericise_ignore=["all"])

    try:
        filas_config = libro.worksheet(hoja_config).get_all_records(numericise_ignore=["all"])
    except gspread.WorksheetNotFound:
        filas_config = []  # La pestaña Config es opcional.

    nodos: List[Dict[str, Any]] = []
    for fila in filas_menu:
        f = _normalizar_fila(fila)
        if not f.get("id") or not f.get("titulo"):
            continue  # Fila vacía o incompleta
        if f.get("activo", "si").lower() in {"no", "n", "false", "0"}:
            continue  # Permite ocultar opciones sin borrarlas
        padre = f.get("padre_id", "")
        nodos.append({
            "id": f["id"],
            "padre_id": ID_RAIZ if padre.upper() in {"", "ROOT", "RAIZ"} else padre,
            "opcion": f.get("opcion", ""),
            "titulo": f["titulo"],
            "icono": f.get("icono", "")[:4],
            "palabras_clave": f.get("palabras_clave", ""),   # Sinónimos propios de esa opción
            "respuesta": f.get("respuesta", "").replace("\r", ""),
            "links": _parsear_links(f.get("link_url", ""), f.get("link_texto", "")),
        })

    config: Dict[str, str] = {}
    for fila in filas_config:
        f = _normalizar_fila(fila)
        if f.get("clave") and f.get("valor"):
            config[f["clave"].lower()] = f["valor"]

    return {"config": config, "nodos": nodos}

def guardar_log_en_background(sheet_id: str, fila: list) -> None:
    """Escribe una fila en la pestaña 'Logs_Bot' sin frenar el chat principal."""
    def _guardar():
        try:
            cliente = obtener_cliente()
            doc = cliente.open_by_key(sheet_id)
            hoja = doc.worksheet("Logs_Bot")
            hoja.append_row(fila)
        except Exception as exc:
            logger.error("No se pudo guardar el log en Sheets: %s", exc)

    # Lanza el proceso en segundo plano (fire and forget)
    hilo = threading.Thread(target=_guardar)
    hilo.start()
    
def actualizar_feedback_en_background(sheet_id: str, id_sesion: str, texto_respuesta: str, feedback: str) -> None:
    """Busca la pregunta original en Sheets y actualiza la columna H con el feedback."""
    def _actualizar():
        try:
            cliente = obtener_cliente()
            doc = cliente.open_by_key(sheet_id)
            hoja = doc.worksheet("Logs_Bot")
            registros = hoja.get_all_values()
            
            # Buscamos de abajo hacia arriba (desde lo más reciente)
            for i in range(len(registros) - 1, 0, -1):
                fila = registros[i]
                # fila[1] es id_sesion, fila[6] es respuesta_bot
                if len(fila) >= 7 and fila[1] == id_sesion and fila[6] == texto_respuesta:
                    hoja.update_cell(i + 1, 8, feedback)  # Columna 8 es la H
                    break
        except Exception as exc:
            logger.error("Error al actualizar feedback en Sheets: %s", exc)

    hilo = threading.Thread(target=_actualizar)
    hilo.start()