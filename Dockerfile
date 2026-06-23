# Imagen mínima para Cloud Run. Las API keys NUNCA se hornean acá: van por
# Secret Manager e inyectadas como env vars en runtime (ver docs/deploy.md).
FROM python:3.12-slim

WORKDIR /app

# Instala el paquete (deps incluidas) desde el código fuente.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# Config no-secreta (router.yaml). Los secretos no se copian (ver .dockerignore).
COPY config ./config

ENV HOST=0.0.0.0 \
    PORT=8080 \
    LINTERNA_ROUTER_CONFIG=/app/config/router.yaml \
    LINTERNA_CACHE_DIR=/tmp/linterna-cache

EXPOSE 8080
CMD ["python", "-m", "linterna.web"]
