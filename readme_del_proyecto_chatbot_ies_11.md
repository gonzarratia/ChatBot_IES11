# 🎓 Portal Web Institucional y Asistente Virtual Híbrido — IES N° 11

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)
![Google Gemini](https://img.shields.io/badge/IA-Google%20Gemini%20API-8E75B2?logo=googlegemini&logoColor=white)
![Google Sheets](https://img.shields.io/badge/Base%20de%20Datos-Google%20Sheets%20API-34A853?logo=googlesheets&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Costo Operativo](https://img.shields.io/badge/Costo%20Operativo-%240%20(Free%20Tier)-success)

> **Trabajo Final Integrador · EDI II - Ciencias de Datos**  
> **Carrera:** Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial  
> **Institución:** Instituto de Educación Superior N° 11 (Alvear 1145, San Salvador de Jujuy, Argentina)

---

## 📋 Descripción del Proyecto

Este proyecto consiste en el diseño, desarrollo, integración y evaluación de un **Portal Web Institucional** para el **IES N° 11** que incorpora un **Asistente Estudiantil Virtual de arquitectura híbrida** y un **sistema de telemetría en tiempo real** enfocado en la mejora continua mediante Ciencia de Datos.

### 🎯 El Problema que Resuelve
1. **Sobrecarga operativa en Secretaría:** Descomprime las consultas repetitivas durante períodos críticos (inscripciones, mesas de examen, pases y equivalencias).
2. **Barrera de "jerga institucional" y horario limitado:** Guía a ingresantes y aspirantes las 24 horas en lenguaje claro y rioplatense sobre conceptos del nivel superior (*regularidad, correlatividades, promoción, condición libre*), fuera del horario presencial de secretaría (lunes a viernes de 08:00 a 23:00 hs).
3. **Administración *Zero-Code*:** Permite al personal administrativo actualizar fechas, requisitos y enlaces directamente desde una planilla de **Google Sheets** sin tocar código.
4. **Auditoría de fallos y Mejora Continua:** Captura cada interacción y calificación del estudiante (`LIKE` / `DISLIKE`) para diagnosticar vacíos de conocimiento (`hubo_fallo = 'SI'`) y perfeccionar las respuestas del bot.

---

## ✨ Características y Arquitectura Principal

* 🌐 **Portal Web + Interfaz Conversacional (Streamlit):** Diseño adaptable a dispositivos móviles y escritorio con identidad institucional, barra lateral con datos de contacto en SVG, preguntas frecuentes (FAQ), migas de pan (*breadcrumbs*) y medidor de cuota de IA.
* ⚡ **Motor de Ruteo Híbrido:**
  * **Navegación Determinística y Búsqueda Léxica (`uso_ia = NO`):** Resuelve clics en tarjetas, comandos numéricos y búsquedas rápidas en **0 segundos** sin consumir cuota de API.
  * **Asesor Conversacional con IA (`uso_ia = SI`):** Atiende consultas abiertas o complejas en modo *streaming* utilizando **Google Gemini API** bajo un enfoque **RAG Ligero** (inyectando únicamente los nodos activos en `<informacion_oficial>`).
* 🛡️ **Blindaje Anti-Alucinación:** Regla estricta en el *prompt* del sistema que prohíbe inventar fechas, requisitos o enlaces. Si el dato no figura en la planilla oficial, el asistente declara explícitamente el desconocimiento, deriva a Secretaría y activa la alerta `hubo_fallo = 'SI'`.
* 📊 **Telemetría Asíncrona y RLHF (*In-Place*):** Guardado en segundo plano (`threading.Thread`) de 8 variables en Google Sheets y captura de retroalimentación humana (`st.feedback`) que actualiza la fila original sin duplicar registros.
* 🔍 **Pipeline de Ciencia de Datos:** Procesamiento con `Pandas`, `NLTK`, `Matplotlib` y `Seaborn` para auditar tasas de fallo, analizar palabras clave no reconocidas (NLP) y proyectar el Dashboard de mejora continua.

---

## 🗄️ Arquitectura de Datos (Google Sheets)

El sistema utiliza una hoja de cálculo en Google Cloud dividida en tres pestañas independientes, leídas con caché inteligente (`@st.cache_data(ttl=300)`):

### 1. Pestaña `Menu` (Base de Conocimiento Jerárquica)
Almacena el árbol de decisión interactivo y el contexto oficial del instituto:
| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | String (PK) | Identificador único del nodo (ej. `ROOT`, `1`, `5.4`). |
| `padre_id` | String (FK) | ID del nodo superior (`ROOT` o vacío para nivel principal). |
| `opcion` | String | Código corto visible para navegación rápida en el chat. |
| `titulo` | String | Nombre de la categoría, carrera o trámite. |
| `palabras_clave` | String | Sinónimos y términos clave para el motor de búsqueda léxica. |
| `respuesta` | Markdown | Texto oficial que se muestra al alumno y alimenta a Gemini. |
| `link_url` | URL | Enlaces a formularios o cartillas (separados por `\|`). |
| `link_texto` | String | Etiqueta de los botones de descarga asociados a `link_url`. |
| `activo` | Booleano | Flag (`si` / `no`) para activar u ocultar nodos sin borrar filas. |

### 2. Pestaña `Config` (Parámetros Globales)
Pares `clave / valor` para personalizar en vivo: `nombre_ies`, `descripcion`, `mensaje_bienvenida`, `direccion`, `horarios`, `telefono`, `email`, `sitio_web`, `preguntas_frecuentes` y `aviso_ia`.

### 3. Pestaña `Logs_Bot` (Dataset de Telemetría — 8 Columnas)
Cada interacción (exceptuando comandos de retorno `0` y `#`) registra una fila con la siguiente estructura:
| Col. | Variable | Tipo | Propósito Analítico |
| :---: | :--- | :--- | :--- |
| **A** | `fecha_hora` | Datetime | Marca temporal (`YYYY-MM-DD HH:MM:SS`) para mapas de calor horarios. |
| **B** | `id_sesion` | String (8 chars) | Hash anónimo (`uuid4()[:8]`) para trazar el recorrido sin datos personales. |
| **C** | `texto_alumno` | String ($\le 200$) | Consulta textual ingresada o tarjeta seleccionada por el estudiante. |
| **D** | `nodo_detectado`| String | ID del nodo consultado (`ROOT` en búsquedas globales). |
| **E** | `uso_ia` | `SI` / `NO` | Distingue respuestas de Google Gemini frente al motor léxico/menú. |
| **F** | `hubo_fallo` | `SI` / `NO` | **Variable crítica:** marca `SI` ante vacío de búsqueda léxica o desconocimiento de IA. |
| **G** | `respuesta_bot` | String ($\le 200$) | Extracto limpio de la respuesta real entregada para auditoría de calidad. |
| **H** | `feedback` | `LIKE` / `DISLIKE` | Valoración del estudiante actualizada *in-place* sobre la misma fila. |

---

## 🛠️ Stack Tecnológico

* **Frontend & Web:** Portal Web Institucional + Python `Streamlit`
* **Motor LLM:** `google-genai` / Google Gemini API
* **Persistencia y Concurrencia:** `gspread`, `google-auth`, `threading`
* **Ciencia de Datos y NLP:** `pandas`, `nltk`, `matplotlib`, `seaborn`
* **Infraestructura:** `Docker` & Entornos Virtuales (`venv`)

---

## 🚀 Instalación y Ejecución Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/gonzarratia/ChatBot_IES11.git
cd ChatBot_IES11
```

### 2. Crear y activar el entorno virtual
```bash
# En Windows (Git Bash / MINGW64)
python -m venv venv
source venv/Scripts/activate

# En Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar las credenciales y variables de entorno
Crea el archivo `.streamlit/secrets.toml` (o configura tus variables de entorno) con tu API Key de Google Gemini, el ID de la planilla de Google Sheets y las credenciales de tu *Service Account* de Google Cloud:

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "TU_API_KEY_DE_GEMINI"
SHEET_ID = "ID_DE_TU_GOOGLE_SHEET"

[gcp_service_account]
type = "service_account"
project_id = "tu-proyecto-gcp"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "tu-service-account@tu-proyecto-gcp.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```
> ⚠️ **Importante:** Asegúrate de que `.streamlit/secrets.toml`, archivos `.env` y credenciales `.json` estén incluidos en tu `.gitignore` para no subir claves privadas a GitHub.

### 5. Ejecutar la aplicación
```bash
streamlit run app.py
```

---

## 🧪 Batería de Pruebas Mínimas (QA)

El MVP se valida mediante 6 casos de prueba estandarizados (detallados en el PRD v2.0):
* **TC-01 (Navegación por menú):** Clic en tarjeta o ingreso numérico $\rightarrow$ Respuesta instantánea (`uso_ia='NO'`, `hubo_fallo='NO'`).
* **TC-02 (Búsqueda léxica sin coincidencia):** Consulta corta sin nodo directo $\rightarrow$ Sugerencias alternativas (`uso_ia='NO'`, `hubo_fallo='SI'`).
* **TC-03 (Consulta conversacional con IA):** Pregunta abierta sobre un trámite cargado $\rightarrow$ Respuesta en viñetas vía *streaming* y botones de descarga (`uso_ia='SI'`, `hubo_fallo='NO'`).
* **TC-04 (Control Anti-Alucinación):** Pregunta sobre un dato no cargado en la planilla $\rightarrow$ Derivación formal a Secretaría (`uso_ia='SI'`, `hubo_fallo='SI'`).
* **TC-05 (Captura de Feedback RLHF):** Clic en 👍/👎 debajo de una respuesta de IA $\rightarrow$ Notificación `st.toast` y actualización de la columna `H` (`LIKE`/`DISLIKE`) sin duplicar filas.
* **TC-06 (Navegación limpia):** Uso de botones `Menú principal` (`0`) o `Volver` (`#`) $\rightarrow$ No genera registros basura en `Logs_Bot`.

---

## 🔒 Ética, Privacidad y Uso Responsable de IA

* **Privacidad por Diseño:** El asistente advierte expresamente en la interfaz no ingresar datos personales sensibles (DNI, teléfono, domicilio) y utiliza identificadores de sesión efímeros y anónimos (`id_sesion` de 8 caracteres).
* **Supervisión Humana (*Human-in-the-Loop*):** El sistema actúa como primer nivel de orientación pública y deriva casos particulares a Secretaría. El equipo directivo y técnico audita periódicamente los registros con `hubo_fallo = 'SI'` o `feedback = 'DISLIKE'` para actualizar la planilla institucional.

---

## 👥 Equipo de Desarrollo

Proyecto desarrollado para la cátedra **EDI II - Ciencias de Datos** del **Instituto de Educación Superior N° 11** (San Salvador de Jujuy):

* **Gonzalo Arratia** — [@gonzarratia](https://github.com/gonzarratia)
* *[Nombre y Apellido Integrante 2]*
* *[Nombre y Apellido Integrante 3]*
* *[Nombre y Apellido Integrante 4]*

---
*Instituto de Educación Superior N° 11 · Alvear 1145, San Salvador de Jujuy, Jujuy, Argentina.*