# -*- coding: utf-8 -*-
"""Interfaz de Streamlit: cabecera, chat, botones de respuesta rápida y manejo de `session_state`."""
from __future__ import annotations
import streamlit.components.v1 as components
import base64
import html
import io
import json
import logging
import re
import time
from dataclasses import replace
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple
import uuid
from .datos import cargar_datos, guardar_log_en_background

import streamlit as st

from .bot import (
    Arbol, Respuesta, auditar_nodos, construir_arbol, icono_nodo, normalizar_texto, procesar_mensaje,
)
from .config import (
    AVISO_RESPUESTA_IA, CAMPOS_CONTACTO, COMANDOS_MENU, COMANDOS_VOLVER, CONFIG_DEFECTO, ID_RAIZ, LLM_MAX_POR_SESION,
    MAX_MENSAJES_HISTORIAL, MAX_PREGUNTAS_FRECUENTES, OPCIONES_VISIBLES, RUTA_LOGO, TITULO_PAGINA,
    ahora_local, entero, leer_ajuste, modelos_llm,
)
from .datos import cargar_datos
from .estilos import ESTILOS
from .gemini import obtener_cliente_llm, obtener_control_llm
from .ia import (
    construir_prompt_sistema, generar_stream, historial_para_llm, ocultar_marcador,
    separar_fuentes,
)

logger = logging.getLogger(__name__)

MODO_DEBUG = (leer_ajuste("debug", "0") or "0").strip().lower() in {"1", "true", "si", "yes"}

# 📌 NUEVO: CSS para achicar los botones de Like/Dislike estilo Gemini
ESTILO_FEEDBACK = """
<style>
/* Apuntar específicamente al componente st.feedback */
div[data-testid="stFeedback"] {
    transform: scale(0.7); /* Achica los botones al 70% de su tamaño original */
    transform-origin: left center; /* Mantiene la alineación a la izquierda */
    margin-top: -10px; /* Sube un poquito los botones para pegarlos a la respuesta */
    margin-bottom: -15px; /* Quita el espacio vacío de abajo */
    opacity: 0.6; /* Los hace un poco transparentes para que sean sutiles */
    transition: opacity 0.2s ease;
}
/* Al pasar el mouse por encima, vuelven a estar 100% opacos */
div[data-testid="stFeedback"]:hover {
    opacity: 1.0; 
}
</style>
"""
@lru_cache(maxsize=1)
def _logo_base64() -> Optional[str]:
    try:
        from PIL import Image
        imagen = Image.open(RUTA_LOGO).convert("RGBA")
        imagen.thumbnail((190, 190))
        buffer = io.BytesIO()
        imagen.save(buffer, format="PNG", optimize=True)
        return base64.b64encode(buffer.getvalue()).decode("ascii")
    except Exception:
        return None

def _icono_pagina() -> Any:
    try:
        from PIL import Image
        return Image.open(RUTA_LOGO)
    except Exception:
        return "🎓"

def _avatar_bot() -> str:
    return str(RUTA_LOGO) if RUTA_LOGO.exists() else "🎓"

def _html_burbuja_usuario(texto: str, nuevo: bool = False) -> str:
    seguro = html.escape(texto).replace("\n", "<br>")
    clase = "fila-usuario nuevo" if nuevo else "fila-usuario"
    return f'<div class="{clase}"><div class="burbuja-usuario">{seguro}</div></div>'

def _html_acciones(links: List[Tuple[str, str]]) -> str:
    botones = "".join(
        f'<a class="btn-descarga" href="{html.escape(url, quote=True)}" target="_blank" '
        f'rel="noopener noreferrer">📎 {html.escape(texto)}</a>'
        for texto, url in links
    )
    return f'<div class="acciones">{botones}</div>' if botones else ""

def _escribiendo(texto: str):
    partes = re.split(r"(\s+)", texto)
    pausa = min(0.02, 1.2 / max(len(partes), 1))
    for parte in partes:
        yield parte
        time.sleep(pausa)

def _mostrar_error_conexion(exc: Exception) -> None:
    logger.exception("Fallo al leer Google Sheets")
    st.markdown(
        '<div class="aviso-error"><b>No pudimos cargar la información del Instituto.</b><br>'
        "Suele resolverse en unos minutos. Si sigue igual, comunicate con el Instituto.</div>",
        unsafe_allow_html=True,
    )
    st.button("Reintentar", key="reintentar", type="primary", on_click=cargar_datos.clear, use_container_width=True)


def _cabecera(config: Dict[str, str], compacta: bool = False, llm_ok: bool = False) -> None:
    nombre = html.escape(config["nombre_ies"])
    logo = _logo_base64()
    if compacta:
        imagen = f'<img src="data:image/png;base64,{logo}" alt="">' if logo else "<span>🎓</span>"
        distintivo = '<span class="barra-ia">✨ Con IA</span>' if llm_ok else ""
        st.markdown(
            f'<div class="barra">{imagen}<div class="barra-texto"><div class="barra-nombre">{nombre}</div>'
            f'<div class="barra-estado"><span class="punto"></span>Asistente virtual · en línea</div></div>'
            f'{distintivo}</div>',
            unsafe_allow_html=True,
        )
        return
    imagen = (
        f'<img class="hero-logo" src="data:image/png;base64,{logo}" alt="Logo de {nombre}">'
        if logo else '<div class="hero-logo hero-logo-emoji">🎓</div>'
    )
    pistas = ["⚡ Respuestas al instante", "📎 Descargas directas", "💬 Escribí o tocá una opción"]
    if llm_ok:
        pistas.append("✨ Con inteligencia artificial")
    pistas_html = "".join(f"<span>{p}</span>" for p in pistas)
    st.markdown(
        f'<div class="hero"><div class="hero-marco">{imagen}</div><div class="hero-texto">'
        f'<span class="hero-chip">Asistente virtual</span><h1>{nombre}</h1>'
        f'<p>{html.escape(config["descripcion"])}</p>'
        f'<div class="hero-pistas">{pistas_html}</div></div></div>',
        unsafe_allow_html=True,
    )

def _ejecutar_js(codigo_html: str) -> None:
    marcado = "<!--__ies-->" + codigo_html
    if hasattr(st, "iframe"):
        st.iframe(marcado, height=1)
    else:
        from streamlit.components.v1 import html as componente_html
        componente_html(marcado, height=0)

def _scroll_a_ultima_consulta() -> None:
    try:
        _ejecutar_js(
            """
            <script>
            (function(){
                // El secreto está en el setTimeout: esperamos a que Streamlit termine su auto-scroll agresivo
                setTimeout(function(){
                    try {
                        var d = window.parent.document;
                        // Seleccionamos todos los mensajes del chat en la pantalla
                        var mensajes = d.querySelectorAll('[data-testid="stChatMessage"]');
                        if(mensajes.length > 0){
                            // Agarramos el último (que siempre es la respuesta terminada de la IA) 
                            // y deslizamos suavemente hasta su inicio (start)
                            mensajes[mensajes.length - 1].scrollIntoView({behavior: 'smooth', block: 'start'});
                        }
                    } catch(e) {}
                }, 500); // 500 milisegundos de retraso son suficientes para ganarle a Streamlit
            })();
            </script>
            """
        )
    except Exception:
        logger.debug("No se pudo agregar el auto-scroll", exc_info=True)

_JS_BOTON_BAJAR = """
(function(){
  if (window.__iesBajar) { return; }
  window.__iesBajar = true;
  var b = document.createElement('button');
  b.id = 'ies-bajar'; b.type = 'button'; b.textContent = '\u2193 Ver opciones';
  b.setAttribute('aria-label', 'Ir a las opciones');
  document.body.appendChild(b);
  function ancla(){ return document.getElementById('ies-opciones'); }
  function actualizar(){
    var a = ancla();
    if (!a) { b.classList.remove('visible'); return; }
    var panel = document.querySelector('.block-container');
    if (panel) { var r = panel.getBoundingClientRect(); b.style.left = (r.left + r.width / 2) + 'px'; }
    b.classList.toggle('visible', a.getBoundingClientRect().top > window.innerHeight - 150);
  }
  b.addEventListener('click', function(){
    var a = ancla(); if (a) { a.scrollIntoView({behavior: 'smooth', block: 'start'}); }
  });
  document.addEventListener('scroll', actualizar, true);
  window.addEventListener('resize', actualizar);
  setInterval(actualizar, 400);
})();
"""

def _instalar_boton_bajar() -> None:
    try:
        _ejecutar_js(
            "<script>(function(){try{var d=window.parent.document;"
            "if(d.getElementById('ies-bajar-js')){return;}"
            "var s=d.createElement('script');s.id='ies-bajar-js';"
            f"s.textContent={json.dumps(_JS_BOTON_BAJAR)};d.head.appendChild(s);"
            "}catch(e){}})();</script>"
        )
    except Exception:
        pass

# Íconos de contacto: SVG de trazo (heredan el color del CSS) en vez de emojis multicolores.
_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true">{}</svg>'
ICONOS_FICHA = {
    "direccion": _SVG.format('<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>'),
    "horarios": _SVG.format('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'),
    "telefono": _SVG.format('<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>'),
    "email": _SVG.format('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>'),
    "sitio_web": _SVG.format('<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>'),
}

def _html_ficha(icono: str, valor: str) -> str:
    texto = html.escape(valor)
    if valor.lower().startswith(("http://", "https://")):
        texto = f'<a href="{html.escape(valor, quote=True)}" target="_blank" rel="noopener noreferrer">{texto}</a>'
    elif re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor):
        texto = f'<a href="mailto:{html.escape(valor, quote=True)}">{texto}</a>'
    return f'<div class="ficha"><span>{icono}</span><span>{texto}</span></div>'

def _barra_lateral(config: Dict[str, str], llm_ok: bool = False, max_sesion: int = 0) -> None:
    with st.sidebar:
        logo = _logo_base64()
        imagen = f'<img src="data:image/png;base64,{logo}" alt="">' if logo else ""
        st.markdown(
            f'<div class="lateral-cabecera">{imagen}'
            f'<div class="lateral-nombre">{html.escape(config["nombre_ies"])}</div></div>',
            unsafe_allow_html=True,
        )
        fichas = "".join(
            _html_ficha(ICONOS_FICHA.get(clave, icono), config[clave]) for clave, icono in CAMPOS_CONTACTO.items() if config.get(clave)
        )
        if fichas:
            st.markdown(f'<div class="lateral-titulo">Contacto</div>{fichas}', unsafe_allow_html=True)
        if llm_ok:
            restantes = max(0, max_sesion - st.session_state.get("consultas_llm", 0))
            porcentaje = round(100 * restantes / max_sesion) if max_sesion else 0
            st.markdown(
                '<div class="lateral-uso"><div class="uso-fila"><span>✨ Consultas con IA</span>'
                f'<b>{restantes} de {max_sesion}</b></div>'
                f'<div class="uso-barra"><i style="width:{porcentaje}%"></i></div></div>'
                f'<div class="lateral-nota"><span>🔒</span><span>{html.escape(config["aviso_ia"])}</span></div>',
                unsafe_allow_html=True,
            )
        st.divider()

        if st.button("Limpiar conversación", key="reiniciar", use_container_width=True):
            # 1. Guardamos el consumo actual de IA y el ID de sesión antes de limpiar
            usadas = st.session_state.get("consultas_llm", 0)
            id_actual = st.session_state.get("id_sesion")
            
            # 2. Limpiamos la pantalla y el estado de navegación
            st.session_state.clear()
            
            # 3. Restauramos el contador de tokens y el ID para que no se reseteen
            st.session_state.consultas_llm = usadas
            if id_actual:
                st.session_state.id_sesion = id_actual
            st.rerun()

def _encolar(texto: str, mostrar: Optional[str] = None, ir_a: Optional[str] = None) -> None:
    st.session_state.pendiente = {"texto": texto, "mostrar": mostrar or texto, "ir_a": ir_a}

def _html_tarjeta(icono: str, numero: str, titulo: str) -> str:
    if numero:
        # Badge numérico moderno sin emoji
        indicador = f'<span class="tarjeta-badge">{html.escape(numero)}</span>'
    else:
        # Ícono minimalista sin emoji para sugerencias y fuentes
        simbolo = "↗" if icono == "fte" else "→"
        indicador = f'<span class="tarjeta-badge tarjeta-badge-sutil">{simbolo}</span>'
    return (
        f'<div class="tarjeta">{indicador}'
        f'<span class="tarjeta-titulo">{html.escape(titulo)}</span>'
        f'<span class="tarjeta-flecha">›</span></div>'
    )

def _grilla_tarjetas(tarjetas: List[Tuple[str, str, str, str, tuple]], por_fila: int = 2) -> None:
    for i in range(0, len(tarjetas), por_fila):
        fila = tarjetas[i:i + por_fila]
        for columna, (clave, icono, numero, titulo, args) in zip(st.columns(por_fila), fila):
            with columna:
                with st.container(key=f"tarjeta_{clave}"):
                    st.markdown(_html_tarjeta(icono, numero, titulo), unsafe_allow_html=True)
                    st.button(f"{numero}. {titulo}" if numero else titulo, key=clave, on_click=_encolar, args=args, use_container_width=True)

def _alternar_ver_todas(nodo_id: str) -> None:
    abiertos = set(st.session_state.get("ver_todas", set()))
    abiertos.symmetric_difference_update({nodo_id})
    st.session_state.ver_todas = abiertos

def _cadena_nodos(nodo_actual: str, arbol: Arbol) -> List[Dict[str, Any]]:
    cadena: List[Dict[str, Any]] = []
    visto = set()
    actual = nodo_actual
    while actual != ID_RAIZ and actual in arbol.por_id and actual not in visto:
        visto.add(actual)
        cadena.append(arbol.por_id[actual])
        actual = arbol.por_id[actual]["padre_id"]
    return cadena[::-1]

def _dibujar_migas(nodo_actual: str, arbol: Arbol) -> None:
    cadena = _cadena_nodos(nodo_actual, arbol)
    with st.container(key="migas"):
        st.button("Inicio", key="miga_inicio", on_click=_encolar, args=("0", "Inicio"), use_container_width=True)
        for nodo in cadena[:-1]:
            st.button(nodo["titulo"], key=f"miga_{nodo['id']}", on_click=_encolar, args=(nodo["titulo"], nodo["titulo"], nodo["id"]), use_container_width=True)
        if cadena:
            st.markdown(f'<span class="miga-actual">{html.escape(cadena[-1]["titulo"])}</span>', unsafe_allow_html=True)

def _preguntas_frecuentes(config: Dict[str, str]) -> List[str]:
    crudo = (config.get("preguntas_frecuentes") or "").strip()
    if crudo.lower() in {"no", "-", "ninguna", "ninguno"}:
        return []
    return [p.strip()[:80] for p in crudo.split("|") if p.strip()][:MAX_PREGUNTAS_FRECUENTES]

def _dibujar_preguntas_frecuentes(preguntas: List[str]) -> None:
    if not preguntas:
        return
    st.markdown('<div class="guia guia-faq">¿Preferís preguntar? Probá con una de estas:</div>', unsafe_allow_html=True)
    with st.container(key="faq"):
        for i, pregunta in enumerate(preguntas):
            st.button(pregunta, key=f"faq_{i}", on_click=_encolar, args=(pregunta, pregunta, None), use_container_width=True)
            
'''def _dibujar_opciones(
    arbol: Arbol, nodo_actual: str, sugerencias: List[Tuple[str, str]],
    fuentes: Optional[List[Tuple[str, str]]] = None, hay_contacto: bool = False,
    preguntas: Optional[List[str]] = None,
) -> None:
    fuentes = fuentes or []
    st.markdown('<div id="ies-opciones"></div>', unsafe_allow_html=True)
    if fuentes:
        st.markdown('<div class="guia">Para ver el detalle oficial:</div>', unsafe_allow_html=True)
        _grilla_tarjetas([(f"fte_{i}", "📄", "", t, (t, t, i)) for i, t in fuentes], por_fila=1)
    elif sugerencias:
        st.markdown('<div class="guia">Tocá la opción que estabas buscando.</div>', unsafe_allow_html=True)
        _grilla_tarjetas([(f"sug_{i}", "💡", "", t, (t, t, i)) for i, t in sugerencias], por_fila=1)
    else:
        if nodo_actual == ID_RAIZ:
            st.markdown('<div class="guia">Tocá una opción o escribí tu consulta.</div>', unsafe_allow_html=True)
        else:
            _dibujar_migas(nodo_actual, arbol)
        opciones = arbol.hijos.get(nodo_actual, [])
        largo = len(opciones) > OPCIONES_VISIBLES
        desplegado = nodo_actual in st.session_state.get("ver_todas", set())
        visibles = opciones if (desplegado or not largo) else opciones[:OPCIONES_VISIBLES]
        _grilla_tarjetas([
            (f"op_{i}_{h['id']}", icono_nodo(h), h["opcion"], h["titulo"],
             (h["opcion"], f"{h['opcion']}. {h['titulo']}", None))
            for i, h in enumerate(visibles)
        ])
        if largo:
            etiqueta = ("▲  Ver menos" if desplegado else f"▼  Ver las {len(opciones) - OPCIONES_VISIBLES} opciones restantes")
            st.button(etiqueta, key=f"vermas_{nodo_actual}", on_click=_alternar_ver_todas, args=(nodo_actual,), use_container_width=True)
        if nodo_actual == ID_RAIZ:
            _dibujar_preguntas_frecuentes(preguntas or [])

    navegacion: List[Tuple[str, str, tuple]] = []
    if nodo_actual != ID_RAIZ:
        navegacion.append(("nav_volver", "← Volver", ("#", "Volver")))
    if nodo_actual != ID_RAIZ or sugerencias or fuentes:
        navegacion.append(("nav_menu", "🏠 Menú principal", ("0", "Menú principal")))
    if navegacion:
        pesos = {"nav_volver": 1.1, "nav_menu": 1.8}
        anchos = [pesos[clave] for clave, _e, _a in navegacion]
        columnas = st.columns(anchos + [max(0.5, 6 - sum(anchos))])
        for columna, (clave, etiqueta, args) in zip(columnas, navegacion):
            columna.button(etiqueta, key=clave, type="primary", on_click=_encolar, args=args, use_container_width=True)'''
def _dibujar_opciones_en_burbuja(
    arbol: Arbol, nodo_actual: str, preguntas: Optional[List[str]] = None
) -> None:
    """Dibuja las opciones adentro de la burbuja, corta el bucle en hojas finales y ubica las migas abajo."""
    # 📌 FIX BUCLE: Si acabamos de mostrar una respuesta final (nodo hoja), no mostramos más tarjetas
    if st.session_state.get("en_respuesta_final", False):
        st.caption("💡 _Llegaste al final de esta consulta. Podés usar los botones de abajo para volver al inicio o escribir otra duda._")
        return

    opciones = arbol.hijos.get(nodo_actual, [])
    if not opciones:
        return

    st.markdown('<div id="ies-opciones"></div>', unsafe_allow_html=True)
    if nodo_actual == ID_RAIZ:
        st.markdown('<div class="guia">Tocá una opción o escribí tu consulta:</div>', unsafe_allow_html=True)

    # 📌 CAMBIO: Reducimos a 4 las opciones visibles por defecto (en lugar de 8)
    limite_visibles = 4
    largo = len(opciones) > limite_visibles
    desplegado = nodo_actual in st.session_state.get("ver_todas", set())
    visibles = opciones if (desplegado or not largo) else opciones[:limite_visibles]
    
    _grilla_tarjetas([
        (f"op_{idx}_{h['id']}", icono_nodo(h), h["opcion"], h["titulo"],
         (h["opcion"], f"{h['opcion']}. {h['titulo']}", h["id"]))
        for idx, h in enumerate(visibles)
    ])
    
    if largo:
        restantes = len(opciones) - limite_visibles
        etiqueta = ("▲  Ver menos" if desplegado else f"▼  Ver las {restantes} opciones restantes")
        st.button(etiqueta, key=f"vermas_{nodo_actual}", on_click=_alternar_ver_todas, args=(nodo_actual,), use_container_width=True)
        
    # 📌 CAMBIO: Ubicamos "Inicio › Trámites administrativos" DEBAJO de las opciones
    if nodo_actual != ID_RAIZ:
        _dibujar_migas(nodo_actual, arbol)
        
    if nodo_actual == ID_RAIZ:
        _dibujar_preguntas_frecuentes(preguntas or [])


def _dibujar_pie_externo(
    nodo_actual: str, sugerencias: List[Tuple[str, str]], fuentes: Optional[List[Tuple[str, str]]] = None
) -> None:
    fuentes = fuentes or []
    
    if fuentes:
        st.markdown('<div id="ies-opciones"></div>', unsafe_allow_html=True)
        st.markdown('<div class="guia">Para ver el detalle oficial:</div>', unsafe_allow_html=True)
        _grilla_tarjetas([
            (f"fte_{idx}_{id_nodo}", "fte", "", titulo, (titulo, titulo, id_nodo))
            for idx, (id_nodo, titulo) in enumerate(fuentes)
        ], por_fila=1)
    elif sugerencias:
        st.markdown('<div id="ies-opciones"></div>', unsafe_allow_html=True)
        st.markdown('<div class="guia">Tocá la opción que estabas buscando:</div>', unsafe_allow_html=True)
        _grilla_tarjetas([
            (f"sug_{idx}_{id_nodo}", "sug", "", titulo, (titulo, titulo, id_nodo))
            for idx, (id_nodo, titulo) in enumerate(sugerencias)
        ], por_fila=1)

    en_final = st.session_state.get("en_respuesta_final", False)
    navegacion: List[Tuple[str, str, tuple]] = []
    if nodo_actual != ID_RAIZ or en_final:
        navegacion.append(("nav_volver", "← Volver", ("#", "Volver", None)))
    if nodo_actual != ID_RAIZ or sugerencias or fuentes or en_final:
        navegacion.append(("nav_menu", "Menú principal", ("0", "Menú principal", None)))
        
    if navegacion:
        pesos = {"nav_volver": 1.1, "nav_menu": 1.5}
        anchos = [pesos[clave] for clave, _e, _a in navegacion]
        columnas = st.columns(anchos + [max(0.5, 6 - sum(anchos))])
        for columna, (clave, etiqueta, args) in zip(columnas, navegacion):
            columna.button(etiqueta, key=clave, type="primary", on_click=_encolar, args=args, use_container_width=True)

'''def _dibujar_historial(animar_ultimo: bool, nuevos: int = 0) -> None:
    mensajes = st.session_state.mensajes
    for i, msg in enumerate(mensajes):
        es_nuevo = nuevos > 0 and i >= len(mensajes) - nuevos
        
        if msg["role"] == "divider":
            st.markdown(f'<div class="divisor-nav">{html.escape(msg["content"])}</div>', unsafe_allow_html=True)
            continue
            
        if msg["role"] == "user":
            st.markdown(_html_burbuja_usuario(msg["content"], es_nuevo), unsafe_allow_html=True)
            continue
            
        with st.chat_message("assistant", avatar=_avatar_bot()):
            if es_nuevo:
                st.markdown('<span class="marca-nuevo"></span>', unsafe_allow_html=True)
            if animar_ultimo and i == len(mensajes) - 1:
                st.write_stream(_escribiendo(msg["content"]))
            else:
                st.markdown(msg["content"])
            acciones = _html_acciones(msg.get("links", []))
            if acciones:
                st.markdown(acciones, unsafe_allow_html=True)
            if msg.get("ia"):
                st.caption(AVISO_RESPUESTA_IA)
                
            # 📌 LÓGICA DE FEEDBACK SEGURA (Quitar un nivel de sangría)
            key_feedback = f"feedback_{i}_{st.session_state.id_sesion}"
                
                # Definir una función de callback que se ejecutará cuando el usuario haga clic
            def on_feedback_change(index=i, k=key_feedback):
                valoracion = st.session_state[k]
                if valoracion is not None and not st.session_state.mensajes[index].get("feedback_enviado"):
                    tipo_feedback = "LIKE" if valoracion == 1 else "DISLIKE"
                    texto_respuesta = st.session_state.mensajes[index]["content"].replace("\n", " ")[:200]
                    
                    from .datos import actualizar_feedback_en_background
                    actualizar_feedback_en_background(
                        leer_ajuste("sheet_id"), 
                        st.session_state.id_sesion, 
                        texto_respuesta, 
                        tipo_feedback
                    )
                    st.session_state.mensajes[index]["feedback_enviado"] = True
                    st.toast("¡Gracias por tu opinión! Nos ayuda a mejorar el bot.")

                # Renderizar el componente st.feedback vinculándolo a la función callback
                st.feedback("thumbs", key=key_feedback, on_change=on_feedback_change)
'''
def _dibujar_historial(
    animar_ultimo: bool, nuevos: int = 0, arbol: Optional[Arbol] = None,
    preguntas: Optional[List[str]] = None, mostrar_menu_interno: bool = False
) -> None:
    mensajes = st.session_state.mensajes
    for i, msg in enumerate(mensajes):
        es_nuevo = nuevos > 0 and i >= len(mensajes) - nuevos
        es_ultimo = (i == len(mensajes) - 1)
        
        if msg["role"] == "divider":
            st.markdown(f'<div class="divisor-nav">{html.escape(msg["content"])}</div>', unsafe_allow_html=True)
            continue
            
        if msg["role"] == "user":
            st.markdown(_html_burbuja_usuario(msg["content"], es_nuevo), unsafe_allow_html=True)
            continue
            
        with st.chat_message("assistant", avatar=_avatar_bot()):
            if es_nuevo:
                st.markdown('<span class="marca-nuevo"></span>', unsafe_allow_html=True)
            if animar_ultimo and es_ultimo:
                st.write_stream(_escribiendo(msg["content"]))
            else:
                st.markdown(msg["content"])
            acciones = _html_acciones(msg.get("links", []))
            if acciones:
                st.markdown(acciones, unsafe_allow_html=True)
            if msg.get("ia"):
                st.caption(AVISO_RESPUESTA_IA)
                
                key_feedback = f"feedback_{i}_{st.session_state.id_sesion}"
                def on_feedback_change(index=i, k=key_feedback):
                    valoracion = st.session_state[k]
                    if valoracion is not None and not st.session_state.mensajes[index].get("feedback_enviado"):
                        tipo_feedback = "LIKE" if valoracion == 1 else "DISLIKE"
                        texto_respuesta = st.session_state.mensajes[index]["content"].replace("\n", " ")[:200]
                        
                        from .datos import actualizar_feedback_en_background
                        actualizar_feedback_en_background(
                            leer_ajuste("sheet_id"), 
                            st.session_state.id_sesion, 
                            texto_respuesta, 
                            tipo_feedback
                        )
                        st.session_state.mensajes[index]["feedback_enviado"] = True
                        st.toast("¡Gracias por tu opinión! Nos ayuda a mejorar el bot.")

                st.feedback("thumbs", key=key_feedback, on_change=on_feedback_change)

            # 📌 NUEVO: Si es el último mensaje del bot y estamos navegando el menú,
            # dibujamos las opciones ADENTRO de esta misma burbuja blanca
            if es_ultimo and mostrar_menu_interno and arbol is not None and not msg.get("ia"):
                _dibujar_opciones_en_burbuja(arbol, st.session_state.nodo_actual, preguntas)


def _guardar_respuesta(resp: Respuesta, ia: bool = False, fuentes: Optional[List[Tuple[str, str]]] = None,
                       animar: bool = True, omitir_mensaje: bool = False) -> None:
    ss = st.session_state
    if not omitir_mensaje:
        ss.mensajes.append({"role": "assistant", "content": resp.texto, "links": resp.links, "ia": ia})
    ss.mensajes = ss.mensajes[-MAX_MENSAJES_HISTORIAL:]
    ss.nodo_actual = resp.nodo
    ss.sugerencias = resp.sugerencias
    ss.fuentes = fuentes or []
    ss.fallos = ss.get("fallos", 0) + 1 if resp.fallo else 0
    ss.animar = animar


def _atender_con_ia(resp: Respuesta, historial: List[Dict[str, Any]], arbol: Arbol,
                    config: Dict[str, str], max_sesion: int, sheet_id: str) -> None:
    control = obtener_control_llm()
    aviso = ""
    if st.session_state.get("consultas_llm", 0) >= max_sesion:
        aviso = "Llegaste al límite de consultas con IA de esta sesión. Seguí con las opciones del menú 👇"
    else:
        permitido, _motivo = control.reservar()
        if not permitido:
            aviso = "Ahora estoy recibiendo muchas consultas 😅. Probá de nuevo en un minuto o usá las opciones 👇"

    texto, ids, error = "", [], None
    with st.chat_message("assistant", avatar=_avatar_bot()):
        hueco = st.empty()
        if not aviso:
            hueco.markdown('<div class="escribiendo">Buscando en la información del instituto<i></i><i></i><i></i></div>', unsafe_allow_html=True)
            sistema = construir_prompt_sistema(config, arbol, resp.candidatos, ahora_local().date())
            crudo = ""
            try:
                for trozo in generar_stream(sistema, resp.consulta_llm, historial,
                                            obtener_cliente_llm(), modelos_llm(), control):
                    crudo += trozo
                    hueco.markdown(ocultar_marcador(crudo) + " ▌")
            except Exception as exc:
                error = exc
            texto, ids = separar_fuentes(crudo)

        if texto.strip():
            if error is not None:
                texto += "\n\n_(La respuesta se cortó. Si necesitás más detalle, consultá en secretaría o usá el menú.)_"
            fuentes = [(i, arbol.por_id[i]["titulo"]) for i in ids if i in arbol.por_id][:3]
            links: List[Tuple[str, str]] = []
            for i, _titulo in fuentes:
                links += [l for l in arbol.por_id[i]["links"] if l not in links]
            hueco.markdown(texto)
            if links:
                st.markdown(_html_acciones(links[:4]), unsafe_allow_html=True)
            # 👇 AGREGAR ESTO ACÁ PARA LA RESPUESTA EN VIVO
            indice = len(st.session_state.mensajes) # Índice que tendrá este mensaje
            key_feedback = f"feedback_{indice}_{st.session_state.id_sesion}"
            
            def on_feedback_change_ia(idx=indice, k=key_feedback):
                valoracion = st.session_state.get(k)
                if valoracion is not None and not st.session_state.mensajes[idx].get("feedback_enviado"):
                    tipo = "LIKE" if valoracion == 1 else "DISLIKE"
                    texto_resp = st.session_state.mensajes[idx]["content"].replace("\n", " ")[:200]
                    from .datos import actualizar_feedback_en_background
                    actualizar_feedback_en_background(
                        leer_ajuste("sheet_id"), st.session_state.id_sesion, texto_resp, tipo
                    )
                    st.session_state.mensajes[idx]["feedback_enviado"] = True
                    st.toast("¡Gracias por tu opinión!")

            st.feedback("thumbs", key=key_feedback, on_change=on_feedback_change_ia)
            # 👆 FIN DE LO NUEVO

            # 📌 GUARDADO ÚNICO Y REAL: Lo guardamos acá cuando el texto ya está completo
            if sheet_id:
                texto_limpio = texto.replace("\n", " ")
                
                # OJO: La frase tiene que estar TODA en minúsculas para que coincida con .lower()
                fallo_ia = "no tengo esa información" in texto_limpio.lower()
                
                fila_log = [
                    ahora_local().strftime("%Y-%m-%d %H:%M:%S"),
                    st.session_state.id_sesion,
                    resp.consulta_llm,
                    resp.nodo,
                    "SI",
                    "SI" if fallo_ia else "NO", 
                    texto_limpio[:200],
                    ""
                ]
                guardar_log_en_background(sheet_id, fila_log)

            st.session_state.consultas_llm = st.session_state.get("consultas_llm", 0) + 1
            _guardar_respuesta(replace(resp, texto=texto, links=links[:4], sugerencias=[], fallo=False,
                                       usar_llm=False), ia=True, fuentes=fuentes, animar=False)
        else:
            respaldo = resp.texto + (f"\n\n{aviso}" if aviso else "")
            hueco.markdown(respaldo)
            _guardar_respuesta(replace(resp, texto=respaldo, usar_llm=False), animar=False)
            

def main() -> None:
    st.set_page_config(page_title=TITULO_PAGINA, page_icon=_icono_pagina(), layout="centered")
    st.markdown(ESTILOS, unsafe_allow_html=True)

    # 📌 NUEVO: Inyectar el CSS de los pulgares chiquitos
    st.markdown("""
        <style>
        /* 1. Pulgares de feedback estilo Gemini */
        div[data-testid="stFeedback"] {
            transform: scale(0.8); 
            transform-origin: left top; 
            margin-top: 5px;
            margin-bottom: -5px; 
            padding-left: 5px;
            opacity: 0.6; 
            transition: opacity 0.2s ease;
        }
        div[data-testid="stFeedback"]:hover {
            opacity: 1.0; 
        }

        /* 2. Tarjetas de opciones modernas, compactas y con acento lateral */
        .tarjeta {
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
            padding: 11px 15px !important;
            min-height: 50px !important;
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-left: 3.5px solid #1e40af !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
            transition: all 0.18s ease !important;
        }
        div[class*="st-key-tarjeta_"]:hover .tarjeta {
            background: #f8fafc !important;
            border-color: #cbd5e1 !important;
            border-left-color: #2563eb !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 10px rgba(37, 99, 235, 0.08) !important;
        }

        /* 3. Badge numérico limpio (reemplaza el cuadrado grande con emoji) */
        .tarjeta-badge {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-width: 26px !important;
            height: 26px !important;
            padding: 0 6px !important;
            border-radius: 7px !important;
            background: #eff6ff !important;
            color: #1d4ed8 !important;
            font-size: 0.82rem !important;
            font-weight: 700 !important;
            flex-shrink: 0 !important;
        }
        .tarjeta-badge-sutil {
            background: #f1f5f9 !important;
            color: #475569 !important;
            font-weight: 600 !important;
        }
        div[class*="st-key-tarjeta_"]:hover .tarjeta-badge {
            background: #2563eb !important;
            color: #ffffff !important;
        }

        /* 4. Texto y flecha derecha de cada opción */
        .tarjeta-titulo {
            font-size: 0.92rem !important;
            font-weight: 600 !important;
            color: #1e293b !important;
            line-height: 1.3 !important;
            flex: 1 !important;
        }
        .tarjeta-flecha {
            font-size: 1.15rem !important;
            color: #94a3b8 !important;
            transition: transform 0.18s ease, color 0.18s ease !important;
        }
        div[class*="st-key-tarjeta_"]:hover .tarjeta-flecha {
            transform: translateX(3px) !important;
            color: #2563eb !important;
        }

        /* 5. Botón desplegable 'Ver las X opciones restantes' más sutil */
        div[class*="st-key-vermas_"] button {
            background: #f8fafc !important;
            border: 1px dashed #cbd5e1 !important;
            color: #334155 !important;
            border-radius: 9px !important;
            padding: 6px 14px !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            margin-top: 4px !important;
        }
        div[class*="st-key-vermas_"] button:hover {
            background: #eff6ff !important;
            border-color: #93c5fd !important;
            color: #1d4ed8 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    sheet_id = leer_ajuste("sheet_id")
    if not sheet_id:
        st.error("Falta configurar `sheet_id` (secrets o variable de entorno SHEET_ID).")
        st.stop()

    try:
        datos = cargar_datos(
            sheet_id,
            leer_ajuste("hoja_menu", "Menu"),
            leer_ajuste("hoja_config", "Config"),
        )
    except Exception as exc:
        _mostrar_error_conexion(exc)
        st.stop()

    config = {**CONFIG_DEFECTO, **{k: v for k, v in datos["config"].items() if v}}
    arbol = construir_arbol(datos["nodos"])

    llm_ok = obtener_cliente_llm() is not None
    max_sesion = entero("llm_max_por_sesion", LLM_MAX_POR_SESION)
    hay_contacto = any(config.get(c) for c in CAMPOS_CONTACTO)

    _barra_lateral(config, llm_ok, max_sesion)

    if not arbol.hijos.get(ID_RAIZ):
        _cabecera(config)
        st.warning("El menú todavía no tiene opciones cargadas en la planilla.")
        st.stop()

    if "mensajes" not in st.session_state:
        st.session_state.id_sesion = str(uuid.uuid4())[:8]  # <-- NUEVO: ID único de 8 caracteres
        st.session_state.nodo_actual = ID_RAIZ
        st.session_state.sugerencias = []
        st.session_state.fuentes = []
        st.session_state.animar = False
        st.session_state.fallos = 0
        st.session_state.consultas_llm = 0
        st.session_state.mensajes = [
            {"role": "assistant", "content": config["mensaje_bienvenida"], "links": [], "ia": False}
        ]

    # 📌 TEXTO FIJO: Evita el bug de Streamlit de "tragar" el primer Enter
    escrito = st.chat_input("Escribí tu consulta o el número de una opción…", max_chars=200)

    pendiente = st.session_state.pop("pendiente", None)
    if escrito:
        pendiente = {"texto": escrito, "mostrar": escrito, "ir_a": None}
    hubo_entrada = bool(pendiente)

    tarea_ia = None
    if pendiente:
        t_norm = normalizar_texto(pendiente["texto"])
        es_nav = t_norm in COMANDOS_MENU or t_norm in COMANDOS_VOLVER
        
        historial = historial_para_llm(st.session_state.mensajes)
        resp = procesar_mensaje(
            pendiente["texto"], st.session_state.nodo_actual, arbol, config,
            pendiente.get("ir_a"), st.session_state.get("fallos", 0), llm_disponible=llm_ok,
        )
        
        # 📌 NUEVO: Disparar el logeo a Google Sheets
        # 📌 Disparar el logeo a Google Sheets
        # 📌 GUARDADO ÚNICO Y REAL: Lo guardamos acá cuando el texto ya está completo
        # 📌 GUARDADO ÚNICO Y REAL (Para navegación sin IA)
        id_sheet = leer_ajuste("sheet_id")
        if id_sheet and not es_nav:
            if not resp.usar_llm:
                texto_respuesta = resp.texto.replace("\n", " ")
                
                # Detectamos si es un fallo léxico (porque dice "no encontré" o tira sugerencias)
                fallo_lexico = resp.fallo or ("no encontré" in texto_respuesta.lower()) or (len(resp.sugerencias) > 0)
                
                fila_log = [
                    ahora_local().strftime("%Y-%m-%d %H:%M:%S"),
                    st.session_state.id_sesion,
                    pendiente["texto"],
                    resp.nodo,
                    "NO",
                    "SI" if fallo_lexico else "NO",  # <-- Ahora SÍ va a marcar el error
                    texto_respuesta[:200],
                    ""
                ]
                guardar_log_en_background(id_sheet, fila_log)

        '''# Cuando toca Volver o Menú principal, mostramos el divisor y abrimos la burbuja con sus opciones adentro
        if es_nav:
            etiqueta = "— Menú principal —" if t_norm in COMANDOS_MENU else "— Volver —"
            st.session_state.mensajes.append({"role": "divider", "content": etiqueta})
            _guardar_respuesta(resp, animar=False, omitir_mensaje=False)
        else:
            st.session_state.mensajes.append({"role": "user", "content": pendiente["mostrar"]})
            if resp.usar_llm:
                tarea_ia = (resp, historial)
            else:
                _guardar_respuesta(resp)'''
                
        # 📌 NUEVO: Detectamos si el alumno llegó a una respuesta final (nodo hoja sin hijos)
        id_destino = pendiente.get("ir_a")
        if es_nav:
            st.session_state.en_respuesta_final = False
        elif id_destino and id_destino in arbol.por_id:
            # Si fue a un nodo específico (desde tarjeta, sugerencia o fuente), vemos si ese nodo tiene sub-opciones
            tiene_subopciones = len(arbol.hijos.get(id_destino, [])) > 0
            st.session_state.en_respuesta_final = not tiene_subopciones
        else:
            # Si escribió un número (ej. "1" o "8"), verificamos si la opción elegida era una hoja o si resp.nodo cambió
            hijos_actuales = arbol.hijos.get(st.session_state.nodo_actual, [])
            nodo_elegido = next((h for h in hijos_actuales if normalizar_texto(h["opcion"]) == t_norm or normalizar_texto(h["titulo"]) == t_norm), None)
            if nodo_elegido:
                tiene_subopciones = len(arbol.hijos.get(nodo_elegido["id"], [])) > 0
                st.session_state.en_respuesta_final = not tiene_subopciones
            else:
                # Si fue por búsqueda y el nodo devuelto no tiene hijos (o dio un texto directo sin cambiar a otra rama con hijos)
                st.session_state.en_respuesta_final = (
                    not resp.usar_llm 
                    and not resp.sugerencias 
                    and not resp.fallo 
                    and resp.nodo == st.session_state.nodo_actual 
                    and st.session_state.nodo_actual != ID_RAIZ
                )

        if es_nav:
            etiqueta = "— Menú principal —" if t_norm in COMANDOS_MENU else "— Volver —"
            st.session_state.mensajes.append({"role": "divider", "content": etiqueta})
            _guardar_respuesta(resp, animar=False, omitir_mensaje=False)
        else:
            st.session_state.mensajes.append({"role": "user", "content": pendiente["mostrar"]})
            if resp.usar_llm:
                tarea_ia = (resp, historial)
            else:
                _guardar_respuesta(resp)

    nodo_actual = st.session_state.nodo_actual
    if nodo_actual != ID_RAIZ and nodo_actual not in arbol.por_id:
        nodo_actual = st.session_state.nodo_actual = ID_RAIZ

    _cabecera(config, compacta=len(st.session_state.mensajes) > 1, llm_ok=llm_ok)

    # Mostramos las opciones adentro de la burbuja si no hay IA corriendo ni sugerencias/fuentes externas
    hay_externos = bool(st.session_state.sugerencias or st.session_state.get("fuentes"))
    mostrar_interno = (tarea_ia is None) and (not hay_externos)

    nuevos = (1 if tarea_ia else 2) if hubo_entrada else 0
    _dibujar_historial(
        st.session_state.animar, nuevos, arbol=arbol,
        preguntas=_preguntas_frecuentes(config), mostrar_menu_interno=mostrar_interno
    )
    st.session_state.animar = False
    
    if tarea_ia:
        _atender_con_ia(tarea_ia[0], tarea_ia[1], arbol, config, max_sesion, sheet_id)
        nodo_actual = st.session_state.nodo_actual
        
    # Afuera de la burbuja solo quedan las citas de IA ("Para ver el detalle oficial"), sugerencias y los botones Volver/Inicio
    _dibujar_pie_externo(nodo_actual, st.session_state.sugerencias, st.session_state.get("fuentes", []))
    
    if hubo_entrada:
        _scroll_a_ultima_consulta()
    _instalar_boton_bajar()

if __name__ == "__main__":
    main()