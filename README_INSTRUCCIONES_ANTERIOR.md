# Guía de despliegue — Asistente Virtual del IES

Costo total: **$0**. Necesitás una cuenta de Google y (para la opción en la nube) una cuenta de GitHub.

---

## Paso 1 · Crear la planilla (Google Sheets)

1. Entrá a [sheets.google.com](https://sheets.google.com) y creá una planilla nueva (ej. "Bot IES").
2. Renombrá la primera pestaña como **`Menu`** y cargá estos encabezados en la fila 1, en este orden:

   `id` · `padre_id` · `opcion` · `titulo` · `respuesta` · `link_url` · `link_texto` · `activo`

3. Cargá un ejemplo:

   | id | padre_id | opcion | titulo | respuesta | link_url | link_texto | activo |
   |---|---|---|---|---|---|---|---|
   | 1 | | 1 | Trámites administrativos | Elegí el trámite: | | | |
   | 1.1 | 1 | 1 | Modelos de Notas | Descargá el modelo que necesites: | *(link de Drive)* | Nota de equivalencias | |
   | 2 | | 2 | Calendario académico | Las inscripciones abren en marzo. | | | |

   - `padre_id` vacío = aparece en el menú principal.
   - `opcion` es el número que escribe el alumno (único dentro del mismo nivel).
   - Para varios links en una fila, separalos con `|` (tanto en `link_url` como en `link_texto`).
   - `activo` = `NO` oculta la fila sin borrarla.
   - (Recomendado) agregá una columna **`palabras_clave`** con las formas en que los alumnos nombran esa opción, separadas por comas (ej. en *Calendario académico*: `fechas, mesas, finales, cuando rindo`). Mejora mucho las búsquedas por texto.
   - (Opcional) agregá una columna **`icono`** con un emoji (ej. 📋) para elegir el ícono del botón. Si no la usás, el bot elige uno según el título (trámites, notas, calendario, etc.).

4. (Opcional) Creá una segunda pestaña **`Config`** con las columnas `clave` y `valor`:

   | clave | valor |
   |---|---|
   | nombre_ies | IES N° XX "Nombre del Instituto" |
   | descripcion | Texto breve de presentación del instituto. |
   | mensaje_bienvenida | ¡Hola! 👋 ¿En qué puedo ayudarte? |
   | mensaje_error | No entendí esa opción. Escribí solo el número. |

   Claves opcionales extra (si no las cargás, simplemente no aparecen): `mensaje_sugerencias`, `mensaje_despedida`, `mensaje_ayuda`, y datos de contacto que se muestran en la barra lateral: `direccion`, `horarios`, `telefono`, `email`, `sitio_web`.

5. Copiá el **ID de la planilla** desde la URL:
   `https://docs.google.com/spreadsheets/d/`**`ESTE_ES_EL_ID`**`/edit`

### Links de descarga desde Google Drive

1. Subí el archivo (ej. el modelo de nota en Word) a Drive.
2. Clic derecho → **Compartir** → Acceso general: **"Cualquier persona con el enlace" → Lector**.
3. Copiá el enlace. Tiene esta forma: `https://drive.google.com/file/d/`**`ID_ARCHIVO`**`/view?usp=sharing`
4. Para que **descargue directo**, pegá en `link_url` este formato:
   `https://drive.google.com/uc?export=download&id=ID_ARCHIVO`

---

## Paso 2 · Obtener el JSON de Google (cuenta de servicio)

La cuenta de servicio es un "usuario robot" que le permite al bot leer tu planilla.

1. Entrá a [console.cloud.google.com](https://console.cloud.google.com) y creá un proyecto (ej. `bot-ies`).
2. Menú **APIs y servicios → Biblioteca** → buscá **Google Sheets API** → **Habilitar**.
   (Si más adelante ves un error 403, habilitá también **Google Drive API**.)
3. **APIs y servicios → Credenciales → Crear credenciales → Cuenta de servicio**. Poné un nombre y terminá el asistente (no hace falta asignar roles).
4. Entrá a la cuenta creada → pestaña **Claves → Agregar clave → Crear clave nueva → JSON**. Se descarga un archivo `.json`.
5. Abrilo y copiá el valor de **`client_email`** (algo como `bot@bot-ies.iam.gserviceaccount.com`).
6. Volvé a tu planilla → **Compartir** → pegá ese email → permiso **Lector**.

> ⚠️ El JSON es una **contraseña**. No lo subas a GitHub, no lo mandes por chat ni lo pongas en la imagen Docker.

---

## Opción A · Correr con Docker (local o servidor propio)

Requisitos: Docker y Docker Compose instalados.

1. Poné en una misma carpeta: `app.py`, la carpeta **`ies_bot/`** (completa), `logo_ies11_round.png`, `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `.dockerignore`.
   (Con Docker no necesitás `config.toml`: el tema claro ya va en el `Dockerfile`. Ese archivo, como `.streamlit/config.toml`, solo hace falta en Streamlit Cloud o para correr sin Docker.)
2. Copiá el JSON descargado a esa carpeta con el nombre **`credentials.json`**.
   En Linux/macOS, asegurate de que sea legible por el contenedor:
   ```bash
   chmod 644 credentials.json
   ```
3. Creá un archivo **`.env`** (en la misma carpeta) con el ID de la planilla:
   ```env
   SHEET_ID=ESTE_ES_EL_ID
   # DEBUG=1   # descomentar solo para diagnosticar errores
   ```
4. Levantá el servicio:
   ```bash
   docker compose up --build -d
   ```
5. Abrí **http://localhost:8501**.

Comandos útiles:

```bash
docker compose logs -f      # ver logs en vivo
docker compose restart      # reiniciar
docker compose down         # detener y eliminar el contenedor
docker compose up --build -d   # reconstruir tras cambiar app.py
```

Sin Compose (equivalente):

```bash
docker build -t chatbot-ies .
docker run -d -p 8501:8501 -e SHEET_ID=ESTE_ES_EL_ID \
  -v "$(pwd)/credentials.json:/app/credentials.json:ro" chatbot-ies
```

Para correr **sin Docker** o ejecutar los **tests**, ver la sección «Estructura del proyecto y cómo ejecutarlo» más abajo.

---

## Opción B · Streamlit Community Cloud (gratis, desde GitHub)

1. **Subí el código a GitHub** (repositorio público o privado) con estos archivos: `app.py`, la carpeta `ies_bot/`, `logo_ies11_round.png`, `requirements.txt` y `.streamlit/config.toml` (este último fija el tema claro; el resto es opcional).
   Creá un `.gitignore` con:
   ```
   credentials.json
   .env
   .streamlit/secrets.toml
   ```
2. Entrá a [share.streamlit.io](https://share.streamlit.io) e iniciá sesión con GitHub.
3. **Create app** → elegí el repositorio, la rama (`main`) y el archivo principal **`app.py`**.
4. Antes de desplegar, abrí **Advanced settings**:
   - **Python version:** 3.11 (la misma que usa el `Dockerfile`).
   - **Secrets:** pegá lo siguiente, reemplazando con los datos de tu JSON.
     El `sheet_id` va **arriba**, antes de la sección `[gcp_service_account]`:

   ```toml
   sheet_id = "ESTE_ES_EL_ID"

   [gcp_service_account]
   type = "service_account"
   project_id = "..."
   private_key_id = "..."
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "bot@bot-ies.iam.gserviceaccount.com"
   client_id = "..."
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "..."
   ```
   Copiá los valores tal cual figuran en el JSON (la `private_key` conserva los `\n`).
5. Clic en **Deploy**. En 1–3 minutos tendrás una URL pública del tipo `https://tu-app.streamlit.app`.

Notas del plan gratuito: la app se "duerme" tras un período sin visitas y se reactiva al entrar; los recursos son limitados.

---

## Estructura del proyecto y cómo ejecutarlo

### Qué hay en cada lugar

El código ya no está en un único archivo: `app.py` quedó mínimo y toda la aplicación vive en la carpeta `ies_bot/`.

```
proyecto/
├── app.py                 ← lo que ejecuta Streamlit (no hace falta tocarlo)
├── ies_bot/               ← el código, dividido por responsabilidad
│   ├── config.py          ·  textos por defecto, umbrales, sinónimos, ajustes
│   ├── bot.py             ·  cómo entiende y responde el bot (menú numérico + búsqueda)
│   ├── ia.py              ·  cómo consulta a Gemini (prompt, límites, respaldo)
│   ├── privacidad.py      ·  quita DNI/teléfonos/correos antes de enviar a la IA
│   ├── datos.py           ·  lee la planilla de Google Sheets
│   ├── gemini.py          ·  crea el cliente de Gemini
│   ├── estilos.py         ·  colores y diseño (CSS)
│   └── ui.py              ·  la pantalla (chat, botones, cabecera)
├── tests/                 ← pruebas automáticas (no van a la imagen de Docker)
├── logo_ies11_round.png · requirements.txt · Dockerfile · docker-compose.yml · .dockerignore
├── .env                   ← SHEET_ID y claves (solo Docker; NO se sube a GitHub)
└── credentials.json       ← clave de Google (NO se sube a GitHub)
```

**Regla práctica:** `app.py` y la carpeta `ies_bot/` **siempre viajan juntos**. Si copiás uno sin el otro, la app falla con
`ModuleNotFoundError: No module named 'ies_bot'`.

### Variables de configuración

Se cargan en el archivo `.env` (Docker) o en *Secrets* (Streamlit Cloud, con los nombres en minúsculas, ej. `gemini_api_key`).

| Variable | Obligatoria | Para qué sirve |
|---|---|---|
| `SHEET_ID` | Sí | ID de la planilla de Google Sheets. |
| `DEBUG` | No | `1` muestra errores técnicos y el botón «Actualizar contenido». En producción dejalo en `0`. |
| `GEMINI_API_KEY` | No | Clave de Google AI Studio. Sin ella el bot funciona igual, solo que sin IA. |
| `GEMINI_MODEL` | No | Modelo(s) de Gemini separados por coma. Vacío = lista por defecto con respaldo automático. |
| `LLM_RPM` / `LLM_RPD` | No | Consultas a la IA por minuto / por día de toda la app (def. 4 y 200). |
| `LLM_MAX_POR_SESION` | No | Consultas con IA por alumno (def. 10). |

Ejemplo de `.env` (sin comillas ni espacios alrededor del `=`):

```env
SHEET_ID=ESTE_ES_EL_ID
DEBUG=0
GEMINI_API_KEY=tu_clave_de_gemini
```

### Opción 1 · Con Docker (Windows, recomendada)

Requisitos: **Docker Desktop** abierto y funcionando. Todos los comandos se escriben en **PowerShell**, parado en la carpeta del proyecto.

```powershell
cd C:\ruta\a\tu\proyecto

# Primera vez, y SIEMPRE que cambies código (app.py, ies_bot/…) o el Dockerfile:
docker compose up --build -d

# Abrir el bot:  http://localhost:8501

docker compose logs -f                  # ver logs en vivo (Ctrl+C para salir)
docker compose restart                  # reiniciar sin reconstruir
docker compose up -d --force-recreate   # aplicar cambios hechos SOLO en .env
docker compose down                     # detener y eliminar el contenedor
```

Importante: el código se copia **dentro de la imagen** al construirla. Si editás un archivo de `ies_bot/` y no ves el cambio, te falta
`docker compose up --build -d`. En cambio, los cambios en la **planilla** se ven solos en hasta 5 minutos, sin reconstruir nada.

Verificar que la clave de Gemini llegó al contenedor (sin mostrarla):

```powershell
docker compose exec chatbot-ies sh -c 'test -n "$GEMINI_API_KEY" && echo "clave presente" || echo "clave VACIA"'
```

### Opción 2 · Sin Docker (para desarrollar y probar rápido)

Requisitos: Python 3.11 instalado. En **PowerShell**, dentro de la carpeta del proyecto:

```powershell
# Una sola vez: entorno virtual e instalación de dependencias
py -m venv .venv
.\.venv\Scripts\Activate.ps1          # si da error de permisos:  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt

# Cada vez que abras una terminal nueva (el .env NO se lee fuera de Docker):
.\.venv\Scripts\Activate.ps1
$env:SHEET_ID = "ESTE_ES_EL_ID"
$env:GCP_CREDENTIALS_FILE = "credentials.json"
$env:GEMINI_API_KEY = "tu_clave_de_gemini"      # opcional
$env:DEBUG = "1"                                 # opcional

streamlit run app.py                             # se abre en http://localhost:8501
```

En esta modalidad los cambios en `ies_bot/` se recargan al guardar el archivo (Streamlit muestra «Rerun»; elegí «Always rerun»).
Para no escribir las variables cada vez, podés crear `.streamlit\secrets.toml` (está en `.gitignore`):

```toml
sheet_id = "ESTE_ES_EL_ID"
gemini_api_key = "tu_clave_de_gemini"
```

### Correr los tests

No necesitan internet, ni Streamlit, ni credenciales, ni clave de Gemini. Con el entorno virtual activado (o con cualquier Python 3.9+):

```powershell
python -m unittest discover -s tests -v
```

Si todo está bien termina en `OK`. Conviene correrlos **antes de reconstruir la imagen** cuando cambies algo en `bot.py`, `ia.py` o `config.py`.

### Dónde cambiar cada cosa

| Quiero cambiar… | Archivo |
|---|---|
| Un mensaje del bot, un umbral de búsqueda, la lista de sinónimos o el modelo de Gemini por defecto | `ies_bot/config.py` |
| Cómo entiende un saludo, un atajo o una búsqueda | `ies_bot/bot.py` (+ un test en `tests/test_bot.py`) |
| El prompt de la IA o sus límites | `ies_bot/ia.py` (+ un test en `tests/test_ia.py`) |
| Colores, tipografías, espacios | `ies_bot/estilos.py` |
| Cómo se ve u ordena la pantalla | `ies_bot/ui.py` |
| Opciones, respuestas y links | La planilla de Google Sheets (no el código) |

---

## Mantenimiento diario

- **Editar contenido:** modificá la planilla. Los cambios se ven en el bot en **hasta 5 minutos** (caché).
- **Agregar una opción:** nueva fila con `id` único, `padre_id` y `opcion`.
- **Reemplazar un archivo:** conviene actualizar el contenido del mismo archivo en Drive (Administrar versiones) para no cambiar el link.
- **Ver el menú sin esperar los 5 minutos:** iniciá con `DEBUG=1` y usá el botón "Actualizar contenido" del panel lateral.
- **Cambiar código:** con Docker, `docker compose up --build -d`; sin Docker alcanza con guardar el archivo.

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| "No podemos acceder a la información" | Planilla no compartida, ID incorrecto o API sin habilitar | Activá `DEBUG=1` para ver el error; verificá el paso 2.6 y el `sheet_id`. |
| Error 403 / `APIError` | Falta habilitar la API | Habilitá Google Sheets API (y Drive API si persiste). |
| `WorksheetNotFound` | La pestaña no se llama `Menu` | Renombrala (respetá mayúscula) o definí `HOJA_MENU`. |
| `PermissionError` leyendo `credentials.json` | Permisos del archivo montado | `chmod 644 credentials.json`. |
| El menú aparece vacío | Todas las filas con `activo=NO` o sin `id`/`titulo` | Revisá la planilla. |
| Una opción no aparece | `padre_id` no coincide con ningún `id` | Corregí el `padre_id`. |
| Link no descarga | Archivo no compartido o URL mal armada | Compartilo como "Cualquier persona con el enlace" y usá el formato `uc?export=download&id=`. |
| `ModuleNotFoundError: No module named 'ies_bot'` | Falta la carpeta `ies_bot/` junto a `app.py`, o el `Dockerfile` no la copia | Copiá la carpeta completa; en Docker verificá que el `Dockerfile` tenga `COPY ies_bot ./ies_bot` y que `.dockerignore` no la excluya. |
| Cambié código y no se ve el cambio (Docker) | La imagen se construyó antes del cambio | `docker compose up --build -d`. |
| La IA no responde y siempre aparece el menú | Clave ausente/inválida, cuota agotada o modelo retirado | Con `DEBUG=1` se ve el motivo; verificá `GEMINI_API_KEY` (comando de la sección Docker) y los modelos disponibles en Google AI Studio. |

## Cómo usa el alumno el bot

Toca el **botón** de la opción que le interesa o escribe su **número**. También puede escribir una consulta con sus palabras (ej. "equivalencias"): el bot le sugiere las opciones que coinciden. Si escribe *contacto*, *dirección*, *horarios* o *teléfono*, el bot responde con los datos cargados en `Config`. Con *ayuda* ve las instrucciones. Si no entiende dos veces seguidas, le muestra cómo comunicarse con el Instituto. Con **0** o el botón *Menú principal* vuelve al inicio y con **#** o *Volver* retrocede un nivel. Los archivos se descargan con los botones azules de la respuesta.
