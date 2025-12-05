# PDFsimple

**PDFsimple** – a modern, free‑tier, open‑source online PDF toolkit.

## Overview
- **MVP tools**: merge, split, compress, PDF ↔ Word, JPG ↔ PDF.
- **Frontend**: Next.js with Tailwind CSS (premium UI).
- **Backend**: FastAPI (Python) with JWT auth.
- **Workers**: Celery + Redis, using free‑tier libraries (pikepdf, LibreOffice, ImageMagick, Tesseract).
- **Storage**: MinIO (S3‑compatible) – self‑hosted, no paid API calls.
- **Database**: PostgreSQL.

## Quick start (local development)
```bash
# clone repo
git clone <repo-url>
cd pdfsimple
# start all services
docker compose up --build
```

The UI will be available at `http://localhost:3000`.

## License
MIT – feel free to fork and extend.
