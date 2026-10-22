¡Excelente! En el mensaje anterior te había pasado una versión un poco "resumida", pero teniendo acá el documento original completo que armaste, vamos a actualizarlo **conservando todo el detalle técnico impecable que ya tenías** (como los pasos de GitHub, Docker y la cuenta de servicio) e inyectándole las nuevas funcionalidades de la IA y las mejores prácticas para cargar el Excel.

Acá tenés el documento completo y definitivo. Podés copiar todo este bloque y reemplazar tu archivo `README_INSTRUCCIONES.md`:

```markdown
# Guía de despliegue — Asistente Virtual del IES

Costo total: **$0**. Necesitás una cuenta de Google y (para la opción en la nube) una cuenta de GitHub.

---

## Paso 1 · Crear y Gestionar la planilla (El "Cerebro" del Bot)

El bot saca toda su inteligencia y respuestas de un archivo de Google Sheets. 

1. Entrá a [sheets.google.com](https://sheets.google.com) y creá una planilla nueva (ej. "Bot IES").
2. Renombrá la primera pestaña como **`Menu`** y cargá estos encabezados en la fila 1, en este orden:

   `id` · `padre_id` · `opcion` · `titulo` · `respuesta` · `link_url` · `link_texto` · `activo` · `palabras_clave`

3. Cargá un ejemplo básico:

   | id | padre_id | opcion | titulo | respuesta | link_url | link_texto | activo | palabras_clave |
   |---|---|---|---|---|---|---|---|---|
   | 1 | | 1 | Trámites administrativos | Elegí el trámite: | | | | tramites, gestiones |
   | 1.1 | 1 | 1 | Modelos de Notas | Descargá el modelo: | *(link)* | Equivalencias | | nota, modelo, pedir |

   - `padre_id` vacío = aparece en el menú principal.
   - `opcion` es el número que escribe el alumno (único dentro del mismo nivel).
   - Para varios links en una fila, separalos con `|` (tanto en `link_url` como en `link_texto`).
   - `activo` = `NO` oculta la fila sin borrarla.
   - **`palabras_clave`** (Muy importante): Poné las formas en que los alumnos nombran esa opción, separadas por comas (ej. *fechas, mesas, finales, cuando rindo*).

### 💡 Mejores Prácticas de Carga (Para aprovechar la Inteligencia Artificial)

Para que el bot funcione como un verdadero "Asesor Estudiantil", te sugerimos estructurar la información así:

- **Estructura Modular de Carreras:** No pongas todo el plan de estudios en una sola celda gigante. Dividí la información creando "filas hijas". Por ejemplo:
  - `5.1`: Enfermería (Resumen y salida laboral)
  - `5.1.1`: Materias por Año
  - `5.1.2`: Correlativas y Prácticas
  - `5.1.3`: Conocimientos previos para ingresar (Clave para bajar la ansiedad del estudiante).
- **Diccionario del Ingresante:** Creá filas para explicar la jerga institucional (ej. qué es "Quedar Libre" o "Regularizar").
- **Tono y Estilo:** Redactá las respuestas tratando de "vos", arrancando con un *"¡Hola! Te cuento que..."*. Usá guiones para listas y asteriscos para **negritas**. La Inteligencia Artificial del bot imitará este estilo al responder.

### Links de descarga desde Google Drive

1. Subí el archivo (ej. el modelo de nota en Word) a Drive.
2. Clic derecho → **Compartir** → Acceso general: **"Cualquier persona con el enlace" → Lector**.
3. Copiá el enlace. Tiene esta forma: `https://drive.google.com/file/d/`**`ID_ARCHIVO`**`/view?usp=sharing`
4. Para que **descargue directo**, pegá en `link_url` este formato:
   `https://drive.google.com/uc?export=download&id=ID_ARCHIVO`
   *(Tip: Si es un Google Doc, podés cambiar `/edit` por `/copy` en la URL original para forzar a que el alumno se haga una copia en su cuenta).*

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
2. Copiá el JSON descargado a esa carpeta con el nombre **`credentials.json`**.
   En Linux/macOS, asegurate de que sea legible por el contenedor:
   ```bash
   chmod 644 credentials.json

```

3. Creá un archivo **`.env`** (en la misma carpeta) con el ID de la planilla y tu clave de IA:
```env
SHEET_ID=ESTE_ES_EL_ID
GEMINI_API_KEY=tu_clave_de_google_ai_studio
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
docker compose up --build -d   # reconstruir tras cambiar código Python

```

---

## Opción B · Streamlit Community Cloud (gratis, desde GitHub)

1. **Subí el código a GitHub** (repositorio público o privado) con estos archivos: `app.py`, la carpeta `ies_bot/`, `logo_ies11_round.png`, `requirements.txt` y `.streamlit/config.toml` (fija el tema claro).
Creá un `.gitignore` con:
```
credentials.json
.env
.streamlit/secrets.toml

```


2. Entrá a [share.streamlit.io](https://share.streamlit.io) e iniciá sesión con GitHub.
3. **Create app** → elegí el repositorio, la rama (`main`) y el archivo principal **`app.py`**.
4. Antes de desplegar, abrí **Advanced settings**:
* **Python version:** 3.11
* **Secrets:** pegá lo siguiente, reemplazando con los datos de tu JSON y sumando tu clave de Gemini:


```toml
sheet_id = "ESTE_ES_EL_ID"
gemini_api_key = "TU_CLAVE_DE_GEMINI"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "bot@bot-ies.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)"
token_uri = "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"
auth_provider_x509_cert_url = "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)"
client_x509_cert_url = "..."

```


5. Clic en **Deploy**. En 1–3 minutos tendrás una URL pública.

---

## Estructura del proyecto y cómo ejecutarlo (Sin Docker)

El código ya no está en un único archivo: `app.py` quedó mínimo y toda la aplicación vive en la carpeta `ies_bot/`.

**Regla práctica:** `app.py` y la carpeta `ies_bot/` **siempre viajan juntos**. Si copiás uno sin el otro, la app falla con `ModuleNotFoundError`.

### Correr sin Docker (para desarrollar y probar rápido)

Requisitos: Python 3.11 instalado. En **PowerShell**, dentro de la carpeta del proyecto:

```powershell
# Una sola vez: entorno virtual e instalación de dependencias
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Cada vez que abras una terminal nueva:
.\.venv\Scripts\Activate.ps1
$env:SHEET_ID = "ESTE_ES_EL_ID"
$env:GCP_CREDENTIALS_FILE = "credentials.json"
$env:GEMINI_API_KEY = "tu_clave_de_gemini"
$env:DEBUG = "1"

streamlit run app.py

```

### Correr los tests

Con el entorno virtual activado:

```powershell
python -m unittest discover -s tests -v

```

---

## Mantenimiento diario

* **Editar contenido:** modificá la planilla. Los cambios se ven en el bot en **hasta 5 minutos** (caché). No hace falta reiniciar nada.
* **Ver el menú sin esperar los 5 minutos:** iniciá con `DEBUG=1` en el `.env` y usá el botón "Actualizar contenido" del panel lateral.
* **Cambiar código:** con Docker, `docker compose up --build -d`; sin Docker alcanza con guardar el archivo Python.

## Solución de problemas

| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| "No podemos acceder a la información" | Planilla no compartida o API sin habilitar | Activá `DEBUG=1` para ver el error; verificá el paso 2.6 y el `sheet_id`. |
| El texto sale cortado o "salta" hacia abajo | Streamlit scrollea en conexiones lentas | El bot ya incluye un "auto-scroll" invisible en Javascript que acomoda la pantalla tras 0.5 segundos. |
| El menú aparece vacío | Todas las filas con `activo=NO` | Revisá la planilla o asegurate de que los `padre_id` coincidan. |
| Link no descarga | Archivo no compartido o URL mal armada | Compartilo como "Cualquier persona" y usá el formato `uc?export=download&id=`. |
| La IA no responde o tira el menú clásico | Clave ausente/inválida o cuota agotada | Verificá que la variable `GEMINI_API_KEY` esté bien configurada en el `.env` o en Secrets. |

## Cómo usa el alumno el bot (Ruteo Híbrido)

El bot cuenta con un sistema inteligente para decidir cómo responder (Regla de las 3 palabras):

1. **Navegación Rápida:** Si el alumno toca un **botón**, escribe un **número**, o escribe 1 o 2 palabras clave (ej. "mesas", "equivalencias", "horarios"), el bot usa el buscador ultrarrápido y le muestra el menú tradicional al instante.
2. **Atención con IA:** Si el alumno escribe una **consulta conversacional larga** (ej. *"Hola, no sé qué estudiar, me gustan las computadoras"* o *"¿Qué materias tiene enfermería en primer año?"*), el bot se da cuenta, intercepta el mensaje, lee la información de la planilla y le redacta una respuesta empática y personalizada usando Inteligencia Artificial, ofreciéndole los links de descarga al final si corresponde.
3. **Respaldo:** Con **0** o el botón *Menú principal* vuelve al inicio y con **#** o *Volver* retrocede un nivel. Si la IA falla o se queda sin cuota, el bot nunca se cuelga: automáticamente vuelve a mostrar el menú de opciones clásico.
