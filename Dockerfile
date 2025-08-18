# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=off \
    POETRY_VIRTUALENVS_CREATE=false

# System deps
# Install system deps including dos2unix
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    dos2unix \
 && rm -rf /var/lib/apt/lists/*


# Copy project files into container
COPY . /app
WORKDIR /app

# Convert and make executable
RUN dos2unix docker/wait-for-it.sh && chmod +x docker/wait-for-it.sh

RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir gunicorn whitenoise

# Copy project
COPY . .

# Collect static at build-time to bake into image (optional; also done at runtime)
# RUN python manage.py collectstatic --noinput || true

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Entrypoint handles migrations, collectstatic, then runs gunicorn
CMD ["/bin/bash", "-lc", "./docker/entrypoint.web.sh"]