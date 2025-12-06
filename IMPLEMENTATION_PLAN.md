# Implementation Plan: Running PDFsimple

To ensure all functions (Merge, Split, Compress, Convert) work correctly, you must use **Docker**. 
This is because the application relies on external tools like **Ghostscript** (for compression), **LibreOffice** (for conversion), and **Redis** (for task queues) which are pre-installed in the Docker containers but likely missing from your local Windows machine.

## 1. Stop Local Servers
If you are running `npm run dev` or any python scripts manually, **stop them** (Ctrl+C).

## 2. Start the Application with Docker
Open your terminal in `D:\product\pdfsimple` and run:

```powershell
docker compose up --build
```

This command will:
1.  Build the Frontend (Next.js)
2.  Build the Backend (FastAPI)
3.  Build the Workers (Python/Celery)
4.  Start Redis, Postgres, and MinIO.

## 3. Access the Application
Once the command finishes and you see logs indicating services are running:

- **Frontend UI**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)

## Troubleshooting
- If you see `bind: address already in use`, make sure you stopped your local `npm run dev` or other servers.
- If the UI says "Processing..." but nothing happens, check the Docker logs for error messages in the `worker` or `backend` container.
- If usage of `/data` fails on Windows, ensure Docker Desktop has file sharing enabled or `wsl` integration active.

## Code Changes Applied
- **Frontend**: Updated `index.tsx` with a premium, responsive UI.
- **Backend**: Fixed `main.py` syntax errors and implemented task dispatching for all tools.
- **Workers**: Updated `split_worker.py` to zip results for single-file download.

