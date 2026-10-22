# -*- coding: utf-8 -*-
"""
Punto de entrada de Streamlit. Se ejecuta con:  streamlit run app.py

Este archivo es a propósito mínimo: toda la aplicación vive en el paquete `ies_bot/`
(ver README_AI.md para el mapa de módulos). Streamlit vuelve a ejecutar este script en cada
interacción del alumno; los módulos ya importados quedan en memoria, así que es barato.
"""
from ies_bot.ui import main

main()
