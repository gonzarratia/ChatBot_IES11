# -*- coding: utf-8 -*-
"""IA (Gemini) como respaldo para preguntas libres. PURA: el cliente real se inyecta desde afuera.

Contiene todo lo que se puede probar sin red: armado del contexto y del prompt, separación de las
fuentes citadas, límites compartidos (`ControlLLM`) y el failover entre modelos (`generar_stream`).
El cliente de Gemini se crea en `gemini.py` y se pasa por parámetro. Tests: `tests/test_ia.py`."""
from __future__ import annotations

import logging
import re
import threading
import time
from collections import deque
from datetime import date
from typing import Any, Dict, Iterator, List, Optional, Tuple

from .bot import Arbol, ruta_nodo
from .config import (
    ID_RAIZ, LLM_HISTORIAL_MENSAJES, LLM_MAX_CONTEXTO, LLM_MAX_TOKENS_SALIDA,
    LLM_RPD_DEFECTO, LLM_RPM_DEFECTO, MESES,
)
from .privacidad import anonimizar_consulta

logger = logging.getLogger(__name__)


# Principios:
#   · El menú y la búsqueda responden primero (gratis, exactos y con los links de descarga).
#   · La IA responde SOLO con la información oficial de la planilla y siempre cita sus fuentes.
#   · Si la IA falla (sin cuota, sin internet, modelo retirado), el alumno ve el menú, nunca un error.
#   · No se envían ni se registran datos personales (ver anonimizar_consulta).

_RE_FUENTES = re.compile(r"\[{1,2}\s*fuentes?\s*:\s*([^\]]*)\]{1,2}", re.IGNORECASE)
_RE_INICIO_MARCADOR = re.compile(r"\[{1,2}\s*fuentes?\s*:", re.IGNORECASE)


def separar_fuentes(texto: str) -> Tuple[str, List[str]]:
    """Separa la respuesta del marcador final `[[fuentes: 13.6, 1.4]]` → (texto limpio, ['13.6', '1.4'])."""
    ids: List[str] = []
    for m in _RE_FUENTES.finditer(texto):
        for pieza in re.split(r"[,;\s]+", m.group(1).strip()):
            pieza = re.sub(r"^id:", "", pieza.strip(), flags=re.IGNORECASE).strip(" .")
            if pieza and pieza.lower() != "ninguna" and pieza not in ids:
                ids.append(pieza)
    return _RE_FUENTES.sub("", texto).rstrip(), ids


def ocultar_marcador(texto: str) -> str:
    """Para mostrar el texto en vivo sin que se vea el marcador de fuentes (ni su comienzo)."""
    corte = texto.find("[[")
    m = _RE_INICIO_MARCADOR.search(texto)
    if m and (corte < 0 or m.start() < corte):
        corte = m.start()
    visible = texto[:corte] if corte >= 0 else texto
    return re.sub(r"\s*\[+$", "", visible).rstrip()      # También un "[" suelto al final del fragmento


def _recorrer_nodos(arbol: Arbol) -> List[Dict[str, Any]]:
    """Todos los nodos en el orden del menú (profundidad primero)."""
    orden: List[Dict[str, Any]] = []
    visto = set()

    def visitar(padre: str) -> None:
        for nodo in arbol.hijos.get(padre, []):
            if nodo["id"] in visto:
                continue
            visto.add(nodo["id"])
            orden.append(nodo)
            visitar(nodo["id"])

    visitar(ID_RAIZ)
    return orden


def _nodo_informativo(nodo: Dict[str, Any], arbol: Arbol) -> bool:
    """Descarta menús contenedores sin contenido propio ('Elegí el trámite:')."""
    texto = nodo["respuesta"].strip()
    if not texto and not nodo["links"]:
        return False
    return not (arbol.hijos.get(nodo["id"]) and len(texto) < 60 and not nodo["links"])


def _bloque_nodo(nodo: Dict[str, Any], arbol: Arbol) -> str:
    ruta = " > ".join(ruta_nodo(nodo["id"], arbol)[1:])
    partes = [f"[id:{nodo['id']}] {ruta}"]
    if nodo["respuesta"].strip():
        partes.append(nodo["respuesta"].strip()[:2500])
    if nodo["links"]:
        partes.append("Archivos para descargar: " + ", ".join(t for t, _ in nodo["links"]))
    return "\n".join(partes)


def construir_contexto(arbol: Arbol, candidatos: List[str], max_chars: int = LLM_MAX_CONTEXTO) -> str:
    """
    Información oficial que se le da al modelo. Con ~100 filas entra TODA la base (más simple y
    más preciso que recuperar fragmentos). Si la planilla crece más que `max_chars`, se envían
    primero los candidatos de la búsqueda y después el resto hasta llenar el tope.
    """
    primeros = [arbol.por_id[i] for i in candidatos if i in arbol.por_id]
    ids_primeros = {n["id"] for n in primeros}
    resto = [n for n in _recorrer_nodos(arbol) if n["id"] not in ids_primeros]
    bloques: List[str] = []
    total = 0
    for nodo in primeros + resto:
        if not _nodo_informativo(nodo, arbol):
            continue
        bloque = _bloque_nodo(nodo, arbol)
        if total + len(bloque) > max_chars:
            break
        bloques.append(bloque)
        total += len(bloque) + 2
    return "\n\n".join(bloques)


def construir_prompt_sistema(
    config: Dict[str, str], arbol: Arbol, candidatos: List[str], hoy: date,
    max_chars: int = LLM_MAX_CONTEXTO,
) -> str:
    """Instrucciones + información oficial. La pregunta del alumno viaja aparte, como dato."""
    fecha = f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"
    return (
        f"Sos el asesor estudiantil virtual de {config.get('nombre_ies', 'un instituto de educación superior')}. "
        "Tu objetivo es ayudar, orientar y resolver las dudas de los alumnos y aspirantes usando "
        "EXCLUSIVAMENTE la información oficial que figura entre <informacion_oficial> y </informacion_oficial>.\n\n"
        f"La fecha de hoy es {fecha}.\n\n"
        "REGLAS DE RESPUESTA:\n"
        "1. Tono y Estilo: Respondé en español rioplatense (tratá de vos), con un tono muy empático, "
        "amigable y motivador. Queremos que el alumno sienta que habla con alguien del instituto dispuesto a ayudar.\n"
        "2. Explicación Natural (PROHIBIDO COPIAR Y PEGAR): Leé la información oficial, entendela y "
        "EXPLICALA con tus propias palabras. Adaptá tu respuesta exactamente a lo que preguntó el alumno. "
        "No repitas los párrafos institucionales largos de forma literal.\n"
        "3. Estructura Visual: Si la respuesta incluye pasos, requisitos, materias o salidas laborales, "
        "organizalos obligatoriamente usando viñetas (bullet points) cortas. Usá **negrita** para "
        "resaltar conceptos clave o fechas importantes.\n"
        "4. CERO INVENCIONES (Anti-Alucinación): No inventes fechas, requisitos, montos ni datos. "
        "Si el estudiante pregunta algo que no está explícitamente en la <informacion_oficial>, "
        "DEBES RESPONDER EXACTAMENTE ESTO: 'No tengo esa información en mi base de datos. Por favor, acercate a Secretaría para consultarlo.'\n"
        "5. NO DEDUZCAS NI ASUMAS: Si preguntan por 'pasantías' y vos solo tenés 'Prácticas Profesionalizantes', "
        "podés mencionarlas, pero debes aclarar que NO tenés información sobre pasantías.\n"
        "6. Control de Fechas: Si el alumno pregunta por un evento o fecha que ya pasó respecto al día de hoy, "
        "aclarale amablemente que esa fecha ya expiró.\n"
        "7. Descargas: Si la información incluye archivos para descargar, mencioná que debajo de tu mensaje "
        "aparecerá un botón para descargarlo. NUNCA escribas URLs en tu texto.\n"
        "8. Cierre: No pidas ni repitas datos personales. Sé directo y útil.\n"
        "9. Citas: Al final de todo, en una línea nueva, escribí exactamente [[fuentes: ID1, ID2]] con los id "
        "(los valores que figuran como [id:...]) de las secciones que usaste. Máximo 3. "
        "Si no usaste ninguna, escribí [[fuentes: ninguna]].\n\n"
        "<informacion_oficial>\n"
        
        f"{construir_contexto(arbol, candidatos, max_chars)}\n"
        "</informacion_oficial>"
    )


def historial_para_llm(
    mensajes: List[Dict[str, Any]], n: int = LLM_HISTORIAL_MENSAJES, max_chars: int = 500
) -> List[Dict[str, Any]]:
    """Últimos mensajes en el formato de Gemini (roles user/model), anonimizados y acortados."""
    salida: List[Dict[str, Any]] = []
    for m in mensajes[-n:]:
        texto = anonimizar_consulta(str(m.get("content", "")), max_chars)
        if not texto:
            continue
        rol = "user" if m.get("role") == "user" else "model"
        if not salida and rol == "model":        # La conversación debe empezar con el alumno
            continue
        salida.append({"role": rol, "parts": [{"text": texto}]})
    return salida


class ControlLLM:
    """
    Límites COMPARTIDOS por todos los alumnos (la cuota gratuita es de la clave, no de la sesión)
    y memoria de modelos que fallaron. Seguro entre hilos; el reloj es inyectable para los tests.
    """

    def __init__(self, por_minuto: int = LLM_RPM_DEFECTO, por_dia: int = LLM_RPD_DEFECTO) -> None:
        self.por_minuto, self.por_dia = por_minuto, por_dia
        self._marcas: "deque[float]" = deque()
        self._pausa_hasta = 0.0
        self._modelos_malos: Dict[str, float] = {}
        self._lock = threading.Lock()

    def reservar(self, ahora: Optional[float] = None) -> Tuple[bool, str]:
        """Pide permiso para UNA consulta. Devuelve (ok, motivo): 'pausa' | 'minuto' | 'dia'."""
        ahora = time.time() if ahora is None else ahora
        with self._lock:
            while self._marcas and ahora - self._marcas[0] > 86400:
                self._marcas.popleft()
            if ahora < self._pausa_hasta:
                return False, "pausa"
            if len(self._marcas) >= self.por_dia:
                return False, "dia"
            if sum(1 for t in self._marcas if ahora - t <= 60) >= self.por_minuto:
                return False, "minuto"
            self._marcas.append(ahora)
            return True, ""

    def bloquear(self, segundos: float, ahora: Optional[float] = None) -> None:
        """Pausa global (p. ej. Google respondió 429 en todos los modelos)."""
        ahora = time.time() if ahora is None else ahora
        with self._lock:
            self._pausa_hasta = max(self._pausa_hasta, ahora + segundos)

    def penalizar(self, modelo: str, segundos: float, ahora: Optional[float] = None) -> None:
        ahora = time.time() if ahora is None else ahora
        with self._lock:
            self._modelos_malos[modelo] = ahora + segundos

    def modelos_activos(self, modelos: List[str], ahora: Optional[float] = None) -> List[str]:
        ahora = time.time() if ahora is None else ahora
        with self._lock:
            return [m for m in modelos if self._modelos_malos.get(m, 0.0) <= ahora]

    def uso(self, ahora: Optional[float] = None) -> Tuple[int, int]:
        """(consultas en el último minuto, consultas en las últimas 24 h)."""
        ahora = time.time() if ahora is None else ahora
        with self._lock:
            return (sum(1 for t in self._marcas if ahora - t <= 60),
                    sum(1 for t in self._marcas if ahora - t <= 86400))


class LLMNoDisponible(Exception):
    """Ningún modelo pudo responder (sin cuota, sin conexión, clave inválida, respuesta bloqueada)."""


def _codigo_error(exc: Exception) -> Optional[int]:
    for atributo in ("code", "status_code"):
        valor = getattr(exc, atributo, None)
        if isinstance(valor, int):
            return valor
    m = re.search(r"\b([45]\d\d)\b", str(exc))
    return int(m.group(1)) if m else None


def _texto_de_fragmento(fragmento: Any) -> str:
    try:
        return getattr(fragmento, "text", None) or ""
    except Exception:     # Fragmentos bloqueados por seguridad pueden lanzar al leer .text
        return ""


def generar_stream(
    sistema: str, pregunta: str, historial: List[Dict[str, Any]], cliente: Any,
    modelos: List[str], control: Optional[ControlLLM] = None,
) -> Iterator[str]:
    """
    Genera la respuesta en fragmentos de texto probando los modelos en orden.
    · Un modelo que falla ANTES de emitir texto se descarta un rato (404 retirado: 1 h; 429 cuota:
      90 s; otros: 30 s) y se prueba el siguiente.
    · Un error DESPUÉS de emitir texto se propaga: la UI conserva lo ya mostrado.
    · Si nada funciona se lanza LLMNoDisponible (la UI vuelve al menú).
    `cliente` es un google.genai.Client (o cualquier objeto con .models.generate_content_stream).
    """
    candidatos = control.modelos_activos(modelos) if control else list(modelos)
    contenidos = list(historial) + [{"role": "user", "parts": [{"text": pregunta}]}]
    config = {
        "system_instruction": sistema,
        "temperature": 0.55,
        "max_output_tokens": LLM_MAX_TOKENS_SALIDA,
    }
    ultimo: Optional[Exception] = None
    for modelo in candidatos:
        emitio = False
        try:
            for fragmento in cliente.models.generate_content_stream(
                model=modelo, contents=contenidos, config=config
            ):
                texto = _texto_de_fragmento(fragmento)
                if texto:
                    emitio = True
                    yield texto
            if emitio:
                return
            ultimo = LLMNoDisponible(f"{modelo}: respuesta vacía (¿bloqueada por seguridad?)")
            logger.warning("Gemini: respuesta vacía con %s", modelo)
        except Exception as exc:    # noqa: BLE001 — cualquier error de red/API se maneja igual
            if emitio:
                raise
            ultimo = exc
            codigo = _codigo_error(exc)
            logger.warning("Gemini: %s con %s (código %s)", type(exc).__name__, modelo, codigo)
            if codigo in (401, 403):             # Clave inválida o sin permiso: no sirve probar otro
                if control:
                    control.bloquear(300)
                break
            if control:
                control.penalizar(modelo, 3600 if codigo == 404 else 90 if codigo == 429 else 30)
    if control and _codigo_error(ultimo or Exception()) == 429:
        control.bloquear(60)
    raise LLMNoDisponible(str(ultimo) if ultimo else "no hay modelos disponibles")
