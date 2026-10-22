# README_AI.md — Contexto técnico para asistentes de IA

> Documento pensado para que un LLM/agente de código entienda el proyecto y pueda extenderlo sin romperlo.
> Para despliegue humano ver `README_INSTRUCCIONES.md`.

## 1. Propósito y restricciones

MVP de web institucional con chatbot para un Instituto de Educación Superior (IES).

- **Stack único:** Streamlit (UI + lógica). Sin backend separado, sin base de datos propia.
- **Costo $0:** Streamlit Community Cloud o Docker local; datos en Google Sheets; archivos en Google Drive.
- **Python 3.9+** (la imagen actual usa `python:3.11-slim`, pero se mantiene sintaxis compatible con 3.9). `from __future__ import annotations` activo en todos los módulos.
- **Bot Híbrido:** Combina un árbol de decisiones numérico, búsqueda léxica y RAG (Retrieval-Augmented Generation) con Google Gemini. Aplica una **Regla de 3 palabras**: consultas cortas van por búsqueda rápida, consultas largas disparan la síntesis del LLM.

## 2. Archivos

```
proyecto/
├── app.py                    # Punto de entrada de Streamlit (mínimo: importa ies_bot.ui y llama a main())
├── ies_bot/                  # TODO el código de la aplicación (paquete de Python)
│   ├── __init__.py           #   mapa del paquete
│   ├── config.py             #   constantes, textos por defecto, leer_ajuste(), ahora_local()
│   ├── privacidad.py         #   anonimizar_consulta()
│   ├── bot.py                #   árbol numérico, búsqueda con sinónimos, atajos, procesar_mensaje()
│   ├── ia.py                 #   contexto, prompt, ControlLLM, generar_stream() (failover de modelos)
│   ├── datos.py              #   lectura de Google Sheets + caché de 5 min
│   ├── gemini.py             #   cliente de Gemini y ControlLLM cacheados (st.cache_resource)
│   ├── estilos.py            #   CSS de la interfaz (tokens de diseño en :root)
│   └── ui.py                 #   pantalla de Streamlit: main()
├── tests/
│   ├── ayudas.py             #   árbol/config de ejemplo compartidos por los tests
│   ├── test_bot.py           #   bot.py
│   ├── test_ia.py            #   ia.py y privacidad.py
│   └── test_config.py        #   config.py + regla "las capas puras no importan Streamlit"
├── logo_ies11_round.png      # Logo (ícono de pestaña, avatar, cabecera). Opcional: sin él se usa 🎓
├── .streamlit/config.toml    # Tema claro fijo (solo para correr sin Docker o en Streamlit Cloud)
├── requirements.txt          # streamlit, gspread, pillow, google-auth, google-genai
├── Dockerfile / docker-compose.yml / .dockerignore
├── .env                      # SHEET_ID, GEMINI_API_KEY, … (NO se sube a git ni a la imagen)
└── credentials.json          # Cuenta de servicio de Google (NO se sube a git ni a la imagen)
```

## 3. Arquitectura: módulos y dependencias

Cada módulo solo puede importar los de capas **inferiores**:

| Capa | Módulo | Responsabilidad | ¿Usa Streamlit? |
|---|---|---|---|
| 4 · Pantalla | `ui` | `main()`, UI, scroll JS hack (`setTimeout`), extracción de fuentes | Sí |
| 4 · Pantalla | `estilos` | CSS (constante `ESTILOS`) | No |
| 3 · Integración | `datos` | Lee Google Sheets (único módulo que habla con Google) | Sí (caché) |
| 3 · Integración | `gemini` | Crea UN cliente de Gemini y UN `ControlLLM` | Sí (caché) |
| 2 · Lógica pura | `bot` | `procesar_mensaje()`; ruteo híbrido (>2 palabras = LLM) | **No** |
| 2 · Lógica pura | `ia` | Prompt, formateo en viñetas, inyección de etiquetas `[[fuentes: ID]]` | **No** |
| 1 · Base | `privacidad` | Quita correos y números largos | **No** |
| 1 · Base | `config` | Constantes y ajustes | No |

**Detalles técnicos de la arquitectura actual:**
- **UI Hack (Scroll):** Streamlit fuerza el scroll hacia abajo durante el streaming de Gemini. `ui.py` inyecta un `setTimeout` de 500ms en JS para hacer un `scrollIntoView(start)` una vez finalizado el mensaje, mejorando drásticamente la UX.
- **Fuentes Ocultas:** `ia.py` le exige al LLM que termine sus respuestas con `[[fuentes: ID]]`. En `ui.py`, la función `separar_fuentes()` recorta este texto antes de renderizarlo y extrae los IDs para dibujar botones de descarga precisos sin ensuciar la interfaz.
- **Ruteo Inteligente:** `bot.py` evalúa la longitud del `texto_normalizado`. Si tiene 3 palabras o más, asume intención conversacional y delega la respuesta a Gemini usando los mejores candidatos de la búsqueda léxica como contexto.

Dependencias permitidas: `ui` → todos · `datos` → `config` · `gemini` → `config`, `ia` · `ia` → `bot`, `privacidad`, `config` ·
`bot` → `privacidad`, `config` · `privacidad` y `config` → nada del paquete.

```
Google Sheets ──gspread──► datos.cargar_datos()  [@st.cache_data ttl=300]
                                   │  dict {"config":…, "nodos":[…]}
                                   ▼
                       bot.construir_arbol() → Arbol(por_id, hijos)
                                   │
st.chat_input ─texto─► bot.procesar_mensaje(texto, nodo_actual, arbol, config, ir_a, fallos, llm_disponible)
                                   │  Respuesta(texto, nodo, links, sugerencias, fallo, usar_llm, consulta_llm, candidatos)
                                   ▼
        ¿usar_llm?  no ─► ui guarda la respuesta y dibuja
                    sí ─► ia.construir_prompt_sistema() + ia.generar_stream(cliente de gemini.py)
                          ├─ responde ─► texto en vivo + fuentes + botones de descarga
                          └─ falla / sin cuota ─► RESPALDO: sugerencias o mensaje_error de la Respuesta
```

**Invariantes (los verifica `tests/test_config.py`):**
1. `config`, `privacidad`, `bot` e `ia` **no importan Streamlit ni gspread**. Se prueban sin tenerlos instalados.
2. `st.*` solo aparece en `ui`, `datos` y `gemini`; `session_state` solo en `ui`.
3. La IA es un **respaldo**: un resultado claro de la búsqueda nunca va a Gemini, y si Gemini falla el alumno ve el menú, nunca un error.

**¿Dónde toco para…?**

| Quiero… | Archivo | Test |
|---|---|---|
| Cambiar un texto por defecto, un umbral, la lista de sinónimos o los modelos de Gemini | `config.py` | — |
| Agregar una regla de conversación o un atajo (saludos, contacto, ayuda…) | `bot.py` | `test_bot.py` |
| Cambiar el prompt de la IA, los límites o el failover | `ia.py` (y `config.py` para números) | `test_ia.py` |
| Cambiar colores, tipografías, espacios | `estilos.py` | — |
| Cambiar cómo se ordena o se ve la pantalla | `ui.py` | — |
| Agregar una columna a la planilla | `datos.py` (+ §5 de este documento) | — |
| Cambiar la clave o el modelo en producción | `.env` (`GEMINI_API_KEY`, `GEMINI_MODEL`) | — |

Ajustes que lee `config.leer_ajuste()` (en `st.secrets` van en **minúsculas**; como variable de entorno, en MAYÚSCULAS):
`sheet_id` (obligatorio), `hoja_menu` (def. `Menu`), `hoja_config` (def. `Config`), `debug`, `gemini_api_key`,
`gemini_model`, `llm_rpm`, `llm_rpd`, `llm_max_por_sesion`.

Detalles por módulo:
- **`datos.py`** — `obtener_cliente()` (`@st.cache_resource`) crea un cliente gspread con scope **solo lectura**. `cargar_datos()` (`@st.cache_data(ttl=300)`) devuelve estructuras serializables (dicts/listas). Credenciales: `st.secrets["gcp_service_account"]` → `GCP_SERVICE_ACCOUNT_JSON` → archivo `credentials.json`.
- **`bot.py`** — incluye `puntuar_opciones()`/`buscar_opciones()` (palabras clave con sinónimos sobre `palabras_clave`, títulos, textos de links y respuestas; bonus por cubrir todas las palabras y por coincidir con el título de un ancestro; tolera plurales y tipeos leves), atajos de contacto/ayuda y `ruta_nodo()` (migas de pan).
- **`ia.py`** — con ~100 filas se envía **toda** la planilla como contexto (más simple y preciso que recuperar fragmentos); si crece, `construir_contexto()` manda primero los candidatos de la búsqueda hasta llenar `LLM_MAX_CONTEXTO`. `ControlLLM` limita consultas por minuto/día para toda la app (la cuota gratuita es de la clave, no de la sesión).
- **`ui.py`** — cabecera completa solo en la bienvenida y barra compacta después; auto-scroll a la última pregunta; botones con `on_click=_encolar` (dejan la acción en `session_state.pendiente`, que `main()` procesa al inicio del rerun, antes de dibujar, así las opciones siempre corresponden al nivel actual); descargas como `<a>` HTML (sin `st.link_button`, para evitar IDs duplicados).

## 4. Manejo de estado (`st.session_state`)

Streamlit re-ejecuta `app.py` completo en cada interacción; el estado por pestaña del navegador vive en `st.session_state` y se pierde al recargar la página.

| Clave | Tipo | Significado |
|---|---|---|
| `mensajes` | `List[{"role": "user"\|"assistant", "content": str, "links": list, "ia": bool}]` | Historial mostrado. Tope: `MAX_MENSAJES_HISTORIAL` (100). |
| `nodo_actual` | `str` | `id` del nivel del árbol donde está el alumno (`"ROOT"` = menú principal). |
| `sugerencias` | `List[(id, título)]` | Coincidencias ofrecidas tras un texto libre. |
| `pendiente` | `dict` | Acción de un botón (`texto`, `mostrar`, `ir_a`) a procesar en el próximo rerun. |
| `animar` | `bool` | Si el último mensaje del bot se muestra con efecto de escritura. |
| `fallos` | `int` | Mensajes seguidos que el bot no entendió (`Respuesta.fallo`). Al llegar a `FALLOS_PARA_DERIVAR` (2) se agrega el contacto. Vuelve a 0 con cualquier respuesta entendida. |
| `fuentes` | `List[(id, título)]` | Secciones de las que salió la última respuesta de la IA (se ofrecen como botones). |
| `consultas_llm` | `int` | Consultas con IA ya respondidas en esta sesión (tope: `llm_max_por_sesion`, def. 10). |

Flujo por interacción (al inicio de cada ejecución de `ui.main()`):
1. Si `mensajes` no existe → se inicializa con el mensaje de bienvenida.
2. Se toma la entrada: texto de `st.chat_input` o la acción `pendiente` dejada por un botón.
3. Si hay entrada → `procesar_mensaje()` → se guardan el mensaje del alumno y la `Respuesta` del bot, y se actualizan `nodo_actual`, `sugerencias` y `animar`.
4. Recién entonces se dibuja el historial y las opciones del nivel actual (así los botones nunca quedan desfasados).

Orden de reglas en `procesar_mensaje()` (gana la primera que aplica): `ir_a` (botón de sugerencia) · `0`/`menu`/saludos (también compuestos: "hola, buen día") → raíz · `#`/`volver`/`atrás` → nivel superior · `ayuda`/`?` → instrucciones · `gracias`/`chau` (mensajes cortos) → despedida · `N`/`opción N` → opción N del nivel actual · `1.1` (id con puntos) → salto directo · número inexistente → aviso con las opciones válidas · texto libre → búsqueda con sinónimos: un único resultado o uno claramente mejor (≥1,5× el segundo) se abre directo; varios parecidos → sugerencias; sin opción propia en el menú, "contacto/dirección/horarios/teléfono/mail" responde con los datos de `Config`; nada → `mensaje_error` (+ derivación desde el 2.º fallo).
Comportamiento: opción con hijos → desciende; opción sin hijos (hoja) → muestra respuesta + botones de descarga y **permanece** en el nivel. Una sugerencia que apunta a una hoja deja al alumno en el nivel de su padre.

Caché: `cargar_datos` es **global** (compartida por todas las sesiones); `session_state` es **por sesión**. No guardar datos personales en el caché.

## 5. Estructura del Google Sheets (El "Cerebro")

La pestaña `Menu` soporta estructuras complejas y detalladas. 

**Mejores prácticas actuales de carga de datos:**
- **Modularidad de Carreras:** En lugar de textos gigantes, las carreras se dividen en sub-nodos: "Materias y Plan de Estudios", "Correlatividades y Prácticas", "Conocimientos previos" y "Requisitos Técnicos".
- **Tonos y Estilos:** Las celdas `respuesta` usan Markdown avanzado (viñetas, negritas) y un tono empático ("¡Hola! Te cuento que...").
- **Orientador Vocacional / Diccionario:** Nodos especiales que aprovechan el razonamiento de Gemini para sugerir carreras según intereses o explicar jerga ("Regularizar", "Correlativa").

### Pestaña `Menu` (obligatoria) — una fila por nodo del árbol

| Columna | Obligatoria | Descripción |
|---|---|---|
| `id` | Sí | Identificador único (ej. `1`, `1.1`, `modelos_notas`). Sin repetir. |
| `padre_id` | No | `id` del nodo padre. Vacío o `ROOT` = menú principal. |
| `opcion` | Sí | Número que el alumno escribe (`1`, `2`, …), único entre hermanos. |
| `titulo` | Sí | Texto de la opción en el menú. |
| `respuesta` | No | Texto Markdown mostrado al elegirla (saltos de línea permitidos). |
| `link_url` | No | URL(s) `http(s)` de Drive. Varias separadas por `\|`. |
| `link_texto` | No | Texto visible de cada link, separados por `\|` en el mismo orden. |
| `activo` | No | `NO` oculta la fila. Vacío = activa. |
| `icono` | No | Emoji del botón de la opción. Vacío = automático por palabra clave (`icono_nodo()`). |
| `palabras_clave` | No | Sinónimos o formas de preguntar de esa opción (ej. `fechas, mesas, finales`). Pesan más que el título en la búsqueda. |

Ejemplo:

| id | padre_id | opcion | titulo | respuesta | link_url | link_texto | activo |
|---|---|---|---|---|---|---|---|
| 1 | | 1 | Trámites administrativos | Elegí el trámite: | | | |
| 1.1 | 1 | 1 | Modelos de Notas | Descargá el modelo que necesites: | https://drive.google.com/uc?export=download&id=AAA\|https://drive.google.com/uc?export=download&id=BBB | Nota de equivalencias\|Nota de examen libre | |
| 2 | | 2 | Calendario académico | Las inscripciones abren en marzo. | | | |

### Pestaña `Config` (opcional) — columnas `clave`, `valor`

Claves reconocidas: `nombre_ies`, `descripcion`, `mensaje_bienvenida`, `mensaje_error`, `mensaje_sugerencias`, `mensaje_despedida`, `mensaje_ayuda`; y opcionales de contacto (barra lateral): `direccion`, `horarios`, `telefono`, `email`, `sitio_web`. Los valores vacíos usan `CONFIG_DEFECTO` de `app.py`.

### Reglas de integridad
- `id` único; `padre_id` debe referenciar un `id` existente (si no, el nodo queda inalcanzable).
- Evitar encabezados duplicados o columnas sin encabezado (`get_all_records` falla).
- Solo se aceptan links que empiecen con `http://` o `https://`.

## 6. Convenciones para modificar el código

- Mantener comentarios y mensajes al usuario en **español rioplatense**, claros y breves.
- No leer Sheets fuera de `datos.cargar_datos()`; nunca agregar llamadas a la red dentro de `bot.procesar_mensaje()`.
- Respetar la tabla de capas de §3: un módulo no importa hacia arriba. Constantes y números "ajustables" van en `config.py`, no esparcidos.
- Si se agrega un módulo nuevo, sumarlo al mapa de `ies_bot/__init__.py` y a las tablas de §2 y §3.
- No escribir en el Sheets (el scope es de solo lectura a propósito).
- Todo cambio en `bot.procesar_mensaje()` / `bot.puntuar_opciones()` debe acompañarse de un test en `tests/test_bot.py`; todo cambio en `ia.py` o `privacidad.py`, en `tests/test_ia.py`. Correr todo con `python -m unittest discover -s tests -v`. Los sinónimos genéricos viven en `SINONIMOS` (`config.py`); el vocabulario propio de cada instituto va en la columna `palabras_clave`, no en el código.
- Secretos solo en `st.secrets` / variables de entorno. Nunca en el repo ni en la imagen.
- Los errores técnicos solo se muestran con `DEBUG=1`.

## 7. Roadmap — Fase 2: LLM / RAG en el mismo código

> **Estado actual:** ya está implementada una versión simplificada, sin RAG: con ~100 filas se envía toda la planilla en el prompt (`ia.construir_contexto`), con failover entre modelos de Gemini, límites compartidos, anonimización y respaldo al menú. El resto de esta sección queda como guía por si la planilla crece y hace falta recuperar fragmentos.

**Objetivo:** que el alumno pueda escribir preguntas libres ("¿cómo pido equivalencias?") y el bot responda con información de la planilla, conservando el menú numérico como camino rápido y de respaldo.

### 7.1 Punto de enganche
En `procesar_mensaje()`, la rama final "texto libre sin coincidencias" (hoy, tras fallar `buscar_opciones()`, devuelve `mensaje_error`) pasa a:

```python
# Pseudocódigo — dentro de procesar_mensaje(), antes de devolver el error
if not es_numero_o_comando(t) and llm_habilitado():
    return responder_con_rag(texto, historial, base_conocimiento), nodo_actual
```

Como el LLM es lento y soporta streaming, conviene mover esa rama a `main()` y usar `st.write_stream(...)` dentro de `st.chat_message("assistant")`; `procesar_mensaje()` seguiría resolviendo solo el árbol numérico.

### 7.2 Base de conocimiento (misma fuente: Google Sheets)
- Nueva pestaña `Conocimiento` con columnas `id`, `titulo`, `texto`, `fuente_url`, `activo`.
- Cargarla en una función `cargar_conocimiento()` con `@st.cache_data(ttl=300)`.
- Opcional: indexar también `respuesta` de la pestaña `Menu`, así el RAG reutiliza lo ya cargado.

### 7.3 Recuperación (retrieval) sin infraestructura extra
1. Fragmentar `texto` en chunks de ~300–500 palabras.
2. Calcular embeddings con un modelo liviano (ONNX, p. ej. `fastembed`) o con la API del proveedor. **Evitar `torch`/`sentence-transformers`**: el plan gratuito de Streamlit Cloud tiene poca RAM.
3. Guardar la matriz en memoria con `@st.cache_resource` (índice compartido, se reconstruye al cambiar un hash del contenido).
4. Búsqueda top-k por similitud coseno con `numpy` (cientos de chunks no necesitan una base vectorial).
5. Alternativa mínima viable: BM25/TF-IDF (`rank_bm25` o `scikit-learn`) sin embeddings.

### 7.4 Generación
- Proveedor desacoplado detrás de una interfaz mínima: `generar(prompt_sistema, mensajes) -> Iterator[str]`. Elegir un proveedor con **capa gratuita** (verificar límites vigentes, cambian seguido) y guardar la clave en `st.secrets["llm_api_key"]`.
- Prompt de sistema: responder **solo** con el contexto recuperado, en español, breve; si no hay respuesta, decir que no lo sabe y derivar al menú o a secretaría; incluir siempre el link de descarga si el chunk tiene `fuente_url`.
- Enviar solo los últimos N turnos de `st.session_state.mensajes` (ventana corta) para controlar costo y latencia.

### 7.5 Estado nuevo en `session_state`
- `consultas_llm: int` → contador por sesión para limitar abuso (ej. 20 por sesión).
- (Opcional) `ultimo_contexto` → chunks usados, útil para depuración con `DEBUG=1`.

### 7.6 Salvaguardas
- **Fallback:** si falla el LLM/timeout, mostrar el menú numérico, nunca un error crudo.
- **Alucinaciones:** no inventar fechas ni requisitos; preferir "consultá en secretaría".
- **Privacidad:** advertir que no se ingresen datos personales (DNI, etc.); no registrar el contenido de las consultas.
- **Inyección de prompt:** el contenido de la planilla y del usuario se trata como datos, no como instrucciones.

### 7.7 Dependencias previstas
`numpy`, `fastembed` (o `rank_bm25`), SDK del proveedor elegido. Actualizar `requirements.txt` y revisar que la imagen siga siendo liviana.

### 7.8 Orden de implementación sugerido
1. Pestaña `Conocimiento` + `cargar_conocimiento()`.
2. Recuperación (TF-IDF primero) con tests unitarios.
3. Rama LLM con streaming y fallback al menú.
4. Límite de consultas y logging sin datos personales.
5. Mejorar la recuperación con embeddings si la calidad lo requiere.

## 8. Deuda Técnica y Roadmap (Fase 3: Ciencia de Datos)

**Objetivo:** Implementar telemetría y analítica de uso para extraer métricas clave (picos de demanda, vacíos de conocimiento, efectividad del LLM).

**Restricción Crítica (Por qué NO usar Google Sheets para Logs):**
Aunque es tentador escribir los logs en una pestaña del mismo Google Sheets, hacerlo en producción generará cuellos de botella (bloqueos por cuota de la API de Google, latencia de 1-2 segundos extra por respuesta y riesgo de corromper la base de conocimiento).

**Plan de Acción (Próxima Iteración):**
1. **Almacenamiento Local:** Implementar escritura asíncrona de logs en un archivo `registros.csv` o base de datos `SQLite` montada en un volumen de Docker.
2. **Estructura del Log:** `[timestamp, id_sesion_anonimo, texto_alumno, nodo_detectado, uso_ia_bool, tokens_usados]`.
3. **Comando Admin:** Crear un atajo secreto en `bot.py` (ej: `/descargar_logs`) que devuelva el archivo local mediante un botón de descarga en la UI, solo visible para administradores.
4. **Análisis Externo:** Usar ese dataset offline con Pandas/Python para NLP (frecuencia de consultas no resueltas) y Series Temporales.