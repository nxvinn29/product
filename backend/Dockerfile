FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 poppler-utils \
    libreoffice-common imagemagick tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and workers code (for shared celery task defs)
COPY backend/ ./backend/
COPY workers/ ./workers/

# Set working directory to backend so uvicorn finds main.py easily OR adjust command
# We keep /app as WORKDIR, and PYTHONPATH needs to include /app
ENV PYTHONPATH=/app

EXPOSE 8000
# main:app is inside backend module now if we did COPY backend/ ./backend/
# So we run uvicorn backend.main:app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
