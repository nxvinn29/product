FROM python:3.11-slim

WORKDIR /app

# System dependencies
# We need full libreoffice support for conversions, and default-jre for some filters.
# ImageMagick policy often disables PDF, so we need to enable it.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 poppler-utils \
    libreoffice-writer libreoffice-calc libreoffice-impress default-jre \
    imagemagick tesseract-ocr ghostscript zip \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy to allow PDF operations
RUN sed -i 's/<policy domain="coder" rights="none" pattern="PDF" \/>/<policy domain="coder" rights="read|write" pattern="PDF" \/>/g' /etc/ImageMagick-6/policy.xml || true

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
