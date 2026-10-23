# -*- coding: utf-8 -*-
"""Configuración de la aplicación: constantes, textos por defecto y lectura de ajustes."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

CACHE_TTL_SEGUNDOS = 300          
ID_RAIZ = "ROOT"                  
MAX_MENSAJES_HISTORIAL = 100      
MAX_SUGERENCIAS = 3               
TITULO_PAGINA = "Asistente virtual del IES 11"                       
RUTA_LOGO = Path(__file__).resolve().parent.parent / "logo_ies11_round.png"  
TZ_LOCAL = timezone(timedelta(hours=-3))                              

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

COMANDOS_MENU = {"0", "menu", "inicio", "menu principal", "volver al menu", "empezar", "comenzar", "reiniciar"}
COMANDOS_VOLVER = {"#", "volver", "atras", "volver atras", "anterior"}
COMANDOS_AYUDA = {"ayuda", "help", "?", "como funciona", "como se usa", "instrucciones", "no entiendo"}
PALABRAS_DESPEDIDA = {"gracias", "chau", "chao", "adios", "listo", "perfecto"}
PALABRAS_SALUDO = {"hola", "holaa", "hey", "buenas", "buen", "buenos", "dia", "dias", "tardes",
                   "noches", "que", "tal", "como", "estas", "todo", "todos", "todas", "bien", "a"}

PALABRAS_VACIAS = {"los", "las", "del", "que", "con", "para", "por", "una", "uno", "como",
                   "donde", "cuando", "quiero", "necesito", "saber", "sobre", "mis", "hay",
                   "hola", "buenas", "buen", "buenos", "dias", "tardes", "noches", "queria",
                   "quisiera", "podria", "podrian", "puedo", "favor", "porfa", "tengo", "duda",
                   "algo", "informacion", "info", "queda", "quedan", "instituto", "ies"}

SINONIMOS: Dict[str, Tuple[str, ...]] = {
    "inscribo": ("inscripcion",), "inscriben": ("inscripcion",), "inscribis": ("inscripcion",),
    "anoto": ("inscripcion",), "anotan": ("inscripcion",), "anotas": ("inscripcion",),
    "inscribirme": ("inscripcion",), "inscribir": ("inscripcion",), "inscribirse": ("inscripcion",),
    "anotarme": ("inscripcion",), "anotar": ("inscripcion",), "anotarse": ("inscripcion",),
    "matricularme": ("inscripcion", "matricula"),
    "papeles": ("documentacion", "requisitos"), "documentos": ("documentacion", "requisitos"),
    "fechas": ("calendario",), "fecha": ("calendario",), "cronograma": ("calendario",),
    "rendir": ("examen",), "finales": ("examen",), "final": ("examen",), "parcial": ("examen",),
    "pagar": ("pago", "arancel", "cuota"), "cobran": ("arancel", "cuota"),
    "costo": ("arancel", "cuota"), "precio": ("arancel", "cuota"),
    "pedido": ("nota", "modelo"), "solicitud": ("nota", "modelo"), "carta": ("nota", "modelo"),
    "abandonar": ("baja",), "dejar": ("baja",),
    "materias": ("equivalencias", "carrera"), "estudiar": ("carrera",),
}

INTENCIONES_CONTACTO: Dict[str, Tuple[str, ...]] = {
    "direccion": ("direccion", "ubicacion", "ubicado", "queda", "quedan", "mapa", "llegar", "domicilio"),
    "horarios": ("horario", "horarios", "atienden", "atencion", "abren", "abierto"),
    "telefono": ("telefono", "llamar", "celular", "whatsapp", "tel"),
    "email": ("mail", "email", "correo"),
    "sitio_web": ("web", "pagina", "sitio"),
}
CONTACTO_GENERICO = ("contacto", "contactar", "comunicar", "comunicarme", "secretaria", "hablar", "persona", "alguien")

PUNTAJE_TITULO = 3
PUNTAJE_DIRECTO = 2
FACTOR_GANADOR = 1.5              
FALLOS_PARA_DERIVAR = 2           
OPCIONES_VISIBLES = 8             
MAX_PREGUNTAS_FRECUENTES = 5      

MODELOS_LLM_DEFECTO = "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.5-flash"
LLM_MIN_PALABRAS = 3              
LLM_CANDIDATOS = 4                
LLM_MAX_CONTEXTO = 60000          
LLM_HISTORIAL_MENSAJES = 4        
LLM_MAX_TOKENS_SALIDA = 1024      
LLM_RPM_DEFECTO = 4               
LLM_RPD_DEFECTO = 200             
LLM_MAX_POR_SESION = 10           
AVISO_RESPUESTA_IA = ("✨ Respuesta generada con IA a partir de la información del instituto. "
                      "Confirmá los datos importantes en secretaría.")
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
         "octubre", "noviembre", "diciembre")

ICONOS_POR_PALABRA = (
    (("titulo", "egresad", "diploma"), "🎓"),
    (("software", "programacion", "informatic", "desarrollo"), "💻"),
    (("datos", "inteligencia", "robotic"), "🤖"),
    (("salud", "sanitari", "enfermeri", "medic", "kinesi"), "🩺"),
    (("indumentaria", "textil", "moda", "costura"), "🧵"),
    (("cocina", "gastronom", "aliment", "panader"), "🍳"),
    (("higiene", "seguridad"), "🦺"),
    (("turismo", "viaje", "guia"), "✈️"),
    (("hoteleri", "hotel"), "🏨"),
    (("idioma", "ingles", "frances", "portugues", "traductor"), "🌐"),
    (("deport", "recreacion"), "⚽"),
    (("arte", "musica", "teatro", "danza", "audiovisual"), "🎨"),
    (("docencia", "docente", "pedagog", "educacion", "profesorado"), "🍎"),
    (("agropecuari", "agricol", "rural", "ambiente", "ecolog", "forestal"), "🌱"),
    (("beca", "progresar"), "🎒"),
    (("contab", "economia", "administracion", "finanza", "comercio", "empresa"), "📊"),
    (("derech", "legal", "juridic", "notari"), "⚖️"),
    (("construcc", "arquitect", "obras", "maestro"), "🏗️"),
    (("mecanic", "electr", "industri", "automotor", "soldadura"), "⚙️"),
    (("logistic", "transporte", "aeronaut"), "🚚"),
    (("comunicacion", "periodis", "radio"), "📣"),
    (("campus", "virtual", "sistema", "plataforma", "aula"), "🖥️"),
    (("jornada", "charla", "taller", "evento", "congreso", "capacitacion"), "🎤"),
    (("cooperadora", "asociacion", "graduados"), "🏛️"),
    (("bienestar", "apoyo", "gabinete", "tutoria"), "🤝"),
    (("equivalencia",), "🔁"),
    (("inasisten", "justificacion"), "✍️"),
    (("reincorpor",), "🔙"),
    (("libreta",), "📒"),
    (("cuatrimestre", "semestre"), "📅"),
    (("inscribi", "preinscribi"), "📝"),
    (("contacto", "hablar", "secretaria", "consulta", "atencion"), "💬"),
    (("tramite", "administrativ", "requisito"), "📋"),
    (("nota", "modelo", "document", "certificad", "constancia", "formulario"), "📄"),
    (("calendario", "fecha", "cronograma", "examen", "mesa"), "📅"),
    (("inscripcion", "matricula", "ingreso", "preinscripcion"), "📝"),
    (("carrera", "tecnicatura", "profesorado", "plan"), "🎓"),
    (("beca", "ayuda", "progresar"), "🎒"),
    (("horario", "cursada", "clase"), "🕘"),
    (("biblioteca", "material", "apunte"), "📚"),
    (("pasantia", "practica", "empleo", "trabajo"), "💼"),
    (("pago", "arancel", "cuota"), "💳"),
    (("ubicacion", "direccion", "mapa"), "📍"),
)
ICONO_DEFECTO = "📌"

CAMPOS_CONTACTO: Dict[str, str] = {
    "direccion": "📍", "horarios": "🕘", "telefono": "📞", "email": "✉️", "sitio_web": "🌐",
}
ETIQUETAS_CONTACTO: Dict[str, str] = {
    "direccion": "Dirección", "horarios": "Horarios", "telefono": "Teléfono",
    "email": "Email", "sitio_web": "Sitio web",
}

CONFIG_DEFECTO: Dict[str, str] = {
    "nombre_ies": "Instituto de Educación Superior N° 11",
    "descripcion": (
        "Bienvenido/a al asistente virtual del Instituto. Consultá trámites, "
        "fechas y descargá los modelos de notas de forma rápida."
    ),
    "mensaje_bienvenida": "¡Hola! 👋 Soy el asistente virtual del Instituto. ¿Qué necesitás?",
    "mensaje_error": "No encontré información sobre eso 🤔. Tocá una de las opciones o escribí su número.",
    "mensaje_sugerencias": "No encontré esa opción exacta, pero quizás te sirva alguna de estas 👇",
    "mensaje_ayuda": (
        "Así podés usarme 👇\n\n"
        "- Tocá una **opción** o escribí su **número** (también sirve *opción 2*).\n"
        "- Escribí tu consulta con tus palabras (ej. *equivalencias*, *cómo me inscribo*).\n"
        "- **0** o *menu*: volver al inicio · **#** o *volver*: un nivel atrás."
    ),
    "aviso_ia": ("Si escribís una consulta con tus palabras, puede procesarse con IA (Google Gemini). "
                 "No escribas DNI, teléfono ni otros datos personales."
                 "Si usás el micrófono, el audio se envía a Google para transcribirlo y no se guarda"),
    "mensaje_despedida": "¡De nada! 😊 Si necesitás algo más, tocá una opción o escribí **menu**.",
    "preguntas_frecuentes": ("¿Cómo me inscribo?|¿Cuándo son las mesas de examen?|¿Qué becas hay?|"
                             "¿Cómo pido un certificado?|¿Dónde queda el instituto?"),
    
    # 📌 CARGA POR DEFECTO DE CONTACTO PARA LA BARRA LATERAL
    "direccion": "Alvear 1145, San Salvador de Jujuy",
    "horarios": "Lunes a viernes de 8 a 23 hs",
    "telefono": "3886014588",
}

def leer_ajuste(clave: str, defecto: Optional[str] = None) -> Optional[str]:
    try:
        import streamlit as st
        if clave in st.secrets and str(st.secrets[clave]).strip():
            return str(st.secrets[clave]).strip()
    except Exception:
        pass
    valor = os.environ.get(clave.upper(), "").strip()
    return valor or defecto

def ahora_local() -> datetime:
    return datetime.now(TZ_LOCAL)

def entero(clave: str, defecto: int) -> int:
    try:
        return max(0, int(leer_ajuste(clave, str(defecto)) or defecto))
    except ValueError:
        return defecto

def modelos_llm() -> List[str]:
    crudo = leer_ajuste("gemini_model", MODELOS_LLM_DEFECTO) or MODELOS_LLM_DEFECTO
    return [m.strip() for m in crudo.split(",") if m.strip()]