# -*- coding: utf-8 -*-
"""Clientes cacheados de la IA: el cliente de Gemini y el control de límites compartido.

Se separan de `ia.py` porque dependen de Streamlit (`st.cache_resource`): un único cliente y un único
`ControlLLM` por proceso, compartidos entre todas las sesiones de alumnos."""
from __future__ import annotations

import logging
from typing import Any

import streamlit as st

from .config import LLM_RPD_DEFECTO, LLM_RPM_DEFECTO, entero, leer_ajuste
from .ia import ControlLLM

logger = logging.getLogger(__name__)


@st.cache_resource(show_spinner=False)
def obtener_cliente_llm() -> Any:
    """Cliente de Gemini (SDK `google-genai`) o None si falta la clave o el paquete: la IA se apaga sola."""
    clave = leer_ajuste("gemini_api_key")
    if not clave:
        return None
    try:
        from google import genai
    except ImportError:
        logger.warning("Falta instalar `google-genai`: la IA queda desactivada.")
        return None
    try:
        return genai.Client(api_key=clave, http_options={"timeout": 30000})   # 30 s por consulta
    except Exception:
        logger.exception("No se pudo crear el cliente de Gemini; la IA queda desactivada.")
        return None


@st.cache_resource(show_spinner=False)
def obtener_control_llm() -> ControlLLM:
    """Un único control para TODAS las sesiones: los límites cuidan la cuota de la clave."""
    return ControlLLM(entero("llm_rpm", LLM_RPM_DEFECTO), entero("llm_rpd", LLM_RPD_DEFECTO))
