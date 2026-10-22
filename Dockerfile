# Imagen base ligera. Python 3.11: 3.9 ya no recibe soporte y el SDK de Gemini lo va a dejar.
FROM python:3.11-slim

# PYTHONUNBUFFERED: logs en tiempo real | PYTHONDONTWRITEBYTECODE: sin .pyc
# PIP_NO_CACHE_DIR: imagen más chica
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Se copian primero las dependencias para aprovechar la caché de capas de Docker:
# si solo cambia el código, no se reinstalan los paquetes.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Código: el punto de entrada, el paquete ies_bot/ (toda la aplicación) y el logo.
COPY app.py logo_ies11_round.png ./
COPY ies_bot ./ies_bot
# Tema claro de Streamlit (colores del IES 11), por variables de entorno:
# no hace falta la carpeta .streamlit para correr con Docker.
ENV STREAMLIT_THEME_BASE=light \
    STREAMLIT_THEME_PRIMARY_COLOR=#2F7BD9 \
    STREAMLIT_THEME_BACKGROUND_COLOR=#F3F6FB \
    STREAMLIT_THEME_SECONDARY_BACKGROUND_COLOR=#FFFFFF \
    STREAMLIT_THEME_TEXT_COLOR=#1E2A47

# Seguridad: el proceso NO corre como root.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Puerto por defecto de Streamlit.
EXPOSE 8501

# Streamlit expone un endpoint de salud en /_stcore/health.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# address=0.0.0.0 es imprescindible para acceder desde fuera del contenedor.
ENTRYPOINT ["streamlit", "run", "app.py", \
            "--server.port=8501", \
            "--server.address=0.0.0.0", \
            "--server.headless=true", \
            "--browser.gatherUsageStats=false"]