# -*- coding: utf-8 -*-
"""Privacidad: limpieza de datos personales antes de enviar texto a un servicio externo.

Módulo puro y chico a propósito: lo usan tanto `bot` (para armar la consulta que irá a la IA) como
`ia` (para el historial), y tenerlo aparte evita una dependencia circular entre ambos."""
from __future__ import annotations

import re


_RE_CORREO = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_RE_NUMERO_LARGO = re.compile(r"\d[\d .\-]{5,}\d")


def anonimizar_consulta(texto: str, max_chars: int = 300) -> str:
    """Quita correos y números largos (DNI, teléfonos) antes de enviar nada a un servicio externo."""
    texto = _RE_CORREO.sub("[correo]", texto)
    texto = _RE_NUMERO_LARGO.sub(
        lambda m: "[número]" if sum(c.isdigit() for c in m.group()) >= 7 else m.group(), texto
    )
    return texto.strip()[:max_chars]
