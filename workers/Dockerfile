FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 poppler-utils \
    libreoffice-common imagemagick tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (from backend requirements for now, as they share)
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy workers and backend (if needed)
COPY workers/ ./workers/
COPY backend/ ./backend/

ENV PYTHONPATH=/app

# Run celery worker
# workers.celery_app is the module
CMD ["celery", "-A", "workers.celery_app", "worker", "--loglevel=info"]
