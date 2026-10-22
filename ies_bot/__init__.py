# -*- coding: utf-8 -*-
"""
ies_bot — Asistente virtual institucional del IES N° 11 (Jujuy).

Mapa del paquete (de abajo hacia arriba; cada módulo solo importa los de más abajo):

    config      constantes, textos por defecto, ajustes y hora local        (sin Streamlit)
    privacidad  limpieza de datos personales                                (puro)
    bot         árbol numérico, búsqueda con sinónimos, atajos              (puro)
    ia          contexto, prompt, límites y failover de Gemini              (puro)
    datos       lectura de Google Sheets con caché                          (gspread + Streamlit)
    gemini      cliente de Gemini y control de límites cacheados            (Streamlit)
    estilos     CSS de la interfaz
    ui          pantalla de Streamlit: main()

El punto de entrada es `app.py`, en la raíz del proyecto. Ver README_AI.md para el detalle.
"""
