from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uuid
import os
import sys
from typing import List

# Add parent directory to path so we can import workers if running locally
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from workers.celery_app import celery_app
except ImportError:
    # Fallback or mock for basic testing if workers module not found
    celery_app = None

# DB Imports
from database import engine, get_db
import models
from sqlalchemy.orm import Session
from fastapi import Depends

# Create tables
models.Base.metadata.create_all(bind=engine)

from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
Instrumentator().instrument(app).expose(app)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple health check
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Placeholder job model
class JobCreate(BaseModel):
    tool: str  # e.g., "merge", "compress"
    params: dict = {}

# In-memory store for demo (replace with DB or Redis in production)
jobs = {}

from fastapi import Form, Request
import json

@app.post("/jobs")
@limiter.limit("10/minute")
async def create_job(
    request: Request,
    tool: str = Form(...),
    params: str = Form("{}"), # JSON string
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    # 1. Calculate size and check quota
    total_size = 0
    # We need to read file size. UploadFile has .size logic only if spooled?
    # Better to read chunks or seek/tell.
    # But we are reading content below anyway.
    
    # Let's get IP
    client_ip = request.client.host
    user = db.query(models.User).filter(models.User.username == client_ip).first()
    if not user:
        user = models.User(username=client_ip)
        db.add(user)
        db.commit()
        db.refresh(user)

    # 2. Check headers or approximate size? 
    # For UploadFile, we can't easily get size without reading.
    # We'll check AFTER reading content (or use content-length if trusted, but better to measure)
    
    job_id = str(uuid.uuid4())
    upload_dir = f"/data/{job_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Parse params
    try:
        job_params = json.loads(params)
    except:
        job_params = {}

    input_paths = []
    job_total_bytes = 0
    
    for file in files:
        path = f"{upload_dir}/{file.filename}"
        with open(path, "wb") as out_file:
            content = await file.read()
            size = len(content)
            job_total_bytes += size
            out_file.write(content)
        input_paths.append(path)
        
    # Check Quota
    if user.usage_bytes + job_total_bytes > user.quota_bytes:
        # Cleanup
        import shutil
        shutil.rmtree(upload_dir)
        return {"status": "failed", "error": "Quota exceeded. Upgrade to Premium."}
    
    # Update Usage
    user.usage_bytes += job_total_bytes
    db.commit()

    # Use 'tool' directly instead of job.tool


    
    if not input_paths:
         jobs[job_id] = {"status": "failed", "error": "No files uploaded"}
         return {"job_id": job_id, "status": "failed"}

    if tool == "merge":
        if celery_app:
            task = celery_app.send_task("merge_pdfs", args=[job_id, input_paths])
            jobs[job_id] = {"status": "queued", "celery_id": task.id}
        else:
            try:
                from workers.merge_worker import merge_pdfs
                output = merge_pdfs(job_id, input_paths)
                jobs[job_id] = {"status": "completed", "output": output}
            except Exception as e:
                jobs[job_id] = {"status": "failed", "error": str(e)}

    elif tool == "split":
         # Use first file for now
         input_path = input_paths[0]
         if celery_app:
            task = celery_app.send_task("split_pdf", args=[job_id, input_path, job_params])
            jobs[job_id] = {"status": "queued", "celery_id": task.id}
         else:
            try:
                from workers.split_worker import split_pdf
                output = split_pdf(job_id, input_path, job_params)
                jobs[job_id] = {"status": "completed", "output": output}
            except Exception as e:
                jobs[job_id] = {"status": "failed", "error": str(e)}

    elif tool == "compress":
         input_path = input_paths[0]
         if celery_app:
            task = celery_app.send_task("compress_pdf", args=[job_id, input_path, job_params])
            jobs[job_id] = {"status": "queued", "celery_id": task.id}
         else:
            try:
                from workers.compress_worker import compress_pdf
                output = compress_pdf(job_id, input_path, job_params)
                jobs[job_id] = {"status": "completed", "output": output}
            except Exception as e:
                jobs[job_id] = {"status": "failed", "error": str(e)}

    elif tool == "convert":
         input_path = input_paths[0]
         if celery_app:
            task = celery_app.send_task("convert_file", args=[job_id, input_path, job_params])
            jobs[job_id] = {"status": "queued", "celery_id": task.id}
         else:
             # Convert requires external tools often not on Windows (LibreOffice, ImageMagick)
             jobs[job_id] = {"status": "failed", "error": "Conversion requires Docker environment"}
    
    elif tool == "ocr":
         input_path = input_paths[0]
         if celery_app:
            task = celery_app.send_task("ocr_pdf", args=[job_id, input_path, job_params])
            jobs[job_id] = {"status": "queued", "celery_id": task.id}
         else:
            try:
                from workers.ocr_worker import ocr_pdf
                output = ocr_pdf(job_id, input_path, job_params)
                jobs[job_id] = {"status": "completed", "output": output}
            except Exception as e:
                jobs[job_id] = {"status": "failed", "error": str(e)}

    elif tool == "pdf_to_pptx":
         input_path = input_paths[0]
         if celery_app:
            task = celery_app.send_task("pdf_to_pptx", args=[job_id, input_path, job_params])
            jobs[job_id] = {"status": "queued", "celery_id": task.id}
         else:
            jobs[job_id] = {"status": "failed", "error": "PDF to PPTX requires Docker environment"}

    elif tool == "pdf_to_xlsx":
         input_path = input_paths[0]
         if celery_app:
            task = celery_app.send_task("pdf_to_xlsx", args=[job_id, input_path, job_params])
            jobs[job_id] = {"status": "queued", "celery_id": task.id}
         else:
            jobs[job_id] = {"status": "failed", "error": "PDF to XLSX requires Docker environment"}

    elif tool == "pdf_to_html":
         input_path = input_paths[0]
         if celery_app:
            task = celery_app.send_task("pdf_to_html", args=[job_id, input_path, job_params])
            jobs[job_id] = {"status": "queued", "celery_id": task.id}
         else:
            jobs[job_id] = {"status": "failed", "error": "PDF to HTML requires Docker environment"}

    elif tool == "images_to_pdf":
         if celery_app:
            task = celery_app.send_task("images_to_pdf", args=[job_id, input_paths, job_params])
            jobs[job_id] = {"status": "queued", "celery_id": task.id}
         else:
            jobs[job_id] = {"status": "failed", "error": "Image to PDF conversion requires Docker environment"}

    elif tool == "watermark":
         input_path = input_paths[0]
         if celery_app:
            task = celery_app.send_task("add_watermark", args=[job_id, input_path, job_params])
            jobs[job_id] = {"status": "queued", "celery_id": task.id}
         else:
            jobs[job_id] = {"status": "failed", "error": "Watermark operation requires Docker environment"}

    elif tool == "page_numbers":
         input_path = input_paths[0]
         if celery_app:
            task = celery_app.send_task("add_page_numbers", args=[job_id, input_path, job_params])
            jobs[job_id] = {"status": "queued", "celery_id": task.id}
         else:
            jobs[job_id] = {"status": "failed", "error": "Page numbers operation requires Docker environment"}

    elif tool == "rotate":
         input_path = input_paths[0]
         if celery_app:
            task = celery_app.send_task("rotate_pages", args=[job_id, input_path, job_params])
            jobs[job_id] = {"status": "queued", "celery_id": task.id}
         else:
            try:
                from workers.rotate_pages_worker import rotate_pages
                output = rotate_pages(job_id, input_path, job_params)
                jobs[job_id] = {"status": "completed", "output": output}
            except Exception as e:
                jobs[job_id] = {"status": "failed", "error": str(e)}

    elif tool == "metadata":
         input_path = input_paths[0]
         if celery_app:
            task = celery_app.send_task("edit_metadata", args=[job_id, input_path, job_params])
            jobs[job_id] = {"status": "queued", "celery_id": task.id}
         else:
            try:
                from workers.metadata_worker import edit_metadata
                output = edit_metadata(job_id, input_path, job_params)
                jobs[job_id] = {"status": "completed", "output": output}
            except Exception as e:
                jobs[job_id] = {"status": "failed", "error": str(e)}

    elif tool == "protect":
         input_path = input_paths[0]
         if celery_app:
            task = celery_app.send_task("protect_pdf", args=[job_id, input_path, job_params])
            jobs[job_id] = {"status": "queued", "celery_id": task.id}
         else:
            try:
                from workers.protect_pdf_worker import protect_pdf
                output = protect_pdf(job_id, input_path, job_params)
                jobs[job_id] = {"status": "completed", "output": output}
            except Exception as e:
                jobs[job_id] = {"status": "failed", "error": str(e)}

    elif tool == "unlock":
         input_path = input_paths[0]
         if celery_app:
            task = celery_app.send_task("unlock_pdf", args=[job_id, input_path, job_params])
            jobs[job_id] = {"status": "queued", "celery_id": task.id}
         else:
            try:
                from workers.unlock_pdf_worker import unlock_pdf
                output = unlock_pdf(job_id, input_path, job_params)
                jobs[job_id] = {"status": "completed", "output": output}
            except Exception as e:
                jobs[job_id] = {"status": "failed", "error": str(e)}

    else:
        jobs[job_id] = {"status": "failed", "error": "Tool not supported"}

    return {"job_id": job_id, "status": jobs[job_id].get("status", "queued")}

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # In a real app, we'd check Celery task status here if it's still queued/processing
    if job.get("celery_id") and celery_app:
        res = celery_app.AsyncResult(job["celery_id"])
        # Check status
        if res.state == 'SUCCESS':
            job["status"] = "completed"
            job["output"] = res.result
        elif res.state == 'FAILURE':
            job["status"] = "failed"
            job["error"] = str(res.result)
        else:
            job["status"] = "processing"
    
    response = {"job_id": job_id, "status": job["status"]}
    if "output" in job:
        response["output"] = job["output"]
    if "error" in job:
        response["error"] = job["error"]
        
    return response

@app.get("/jobs/{job_id}/result")
async def download_result(job_id: str):
    job = jobs.get(job_id)
    if not job or job.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Result not available")
    
    output = job.get("output")
    if isinstance(output, dict):
        result_path = output.get("file_path")
    else:
        result_path = output

    if not result_path or not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(result_path, filename=os.path.basename(result_path))
    return FileResponse(result_path, filename=os.path.basename(result_path))

@app.post("/jobs/batch")
@limiter.limit("5/minute")
async def create_batch_job(
    request: Request,
    tool: str = Form(...),
    params: str = Form("{}"),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    if tool == "merge":
        raise HTTPException(status_code=400, detail="Merge does not support batch mode (it is already a batch op)")

    client_ip = request.client.host
    user = db.query(models.User).filter(models.User.username == client_ip).first()
    if not user:
        user = models.User(username=client_ip)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Pre-read files to check quota? 
    # In batch, calculating total size upfront is harder without reading streams.
    # We will process one by one and abort if quota hit?
    # Or just read all context.
    
    responses = []
    
    try:
        job_params = json.loads(params)
    except:
        job_params = {}

    for file in files:
        # Create job for each file
        job_id = str(uuid.uuid4())
        upload_dir = f"/data/{job_id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        path = f"{upload_dir}/{file.filename}"
        content = await file.read()
        size = len(content)
        
        if user.usage_bytes + size > user.quota_bytes:
            import shutil
            shutil.rmtree(upload_dir)
            # Stop processing further files? or continue others?
            # Usually strict quota stops all.
            # But maybe some succeeded.
            # We'll return error for this one.
            responses.append({"job_id": None, "status": "failed", "error": "Quota exceeded", "filename": file.filename})
            continue
            
        with open(path, "wb") as out_file:
            out_file.write(content)
            
        user.usage_bytes += size
        db.commit() # Commit usage increment immediately
        
        # Dispatch
        if tool == "split":
             if celery_app:
                task = celery_app.send_task("split_pdf", args=[job_id, path, job_params])
                jobs[job_id] = {"status": "queued", "celery_id": task.id}
             else:
                responses.append({"job_id": job_id, "status": "failed", "error": "Celery required"})
                continue

        elif tool == "compress":
             if celery_app:
                task = celery_app.send_task("compress_pdf", args=[job_id, path, job_params])
                jobs[job_id] = {"status": "queued", "celery_id": task.id}
             else:
                 responses.append({"job_id": job_id, "status": "failed", "error": "Celery required"})
                 continue

        elif tool == "ocr":
             if celery_app:
                task = celery_app.send_task("ocr_pdf", args=[job_id, path, job_params])
                jobs[job_id] = {"status": "queued", "celery_id": task.id}
             else:
                 responses.append({"job_id": job_id, "status": "failed", "error": "Celery required"})
                 continue
                 
        elif tool == "convert":
             if celery_app:
                task = celery_app.send_task("convert_file", args=[job_id, path, job_params])
                jobs[job_id] = {"status": "queued", "celery_id": task.id}
             else:
                 responses.append({"job_id": job_id, "status": "failed", "error": "Celery required"})
                 continue

        elif tool == "pdf_to_pptx":
             if celery_app:
                task = celery_app.send_task("pdf_to_pptx", args=[job_id, path, job_params])
                jobs[job_id] = {"status": "queued", "celery_id": task.id}
             else:
                 responses.append({"job_id": job_id, "status": "failed", "error": "Celery required"})
                 continue

        elif tool == "pdf_to_xlsx":
             if celery_app:
                task = celery_app.send_task("pdf_to_xlsx", args=[job_id, path, job_params])
                jobs[job_id] = {"status": "queued", "celery_id": task.id}
             else:
                 responses.append({"job_id": job_id, "status": "failed", "error": "Celery required"})
                 continue

        elif tool == "pdf_to_html":
             if celery_app:
                task = celery_app.send_task("pdf_to_html", args=[job_id, path, job_params])
                jobs[job_id] = {"status": "queued", "celery_id": task.id}
             else:
                 responses.append({"job_id": job_id, "status": "failed", "error": "Celery required"})
                 continue

        elif tool == "watermark":
             if celery_app:
                task = celery_app.send_task("add_watermark", args=[job_id, path, job_params])
                jobs[job_id] = {"status": "queued", "celery_id": task.id}
             else:
                 responses.append({"job_id": job_id, "status": "failed", "error": "Celery required"})
                 continue

        elif tool == "page_numbers":
             if celery_app:
                task = celery_app.send_task("add_page_numbers", args=[job_id, path, job_params])
                jobs[job_id] = {"status": "queued", "celery_id": task.id}
             else:
                 responses.append({"job_id": job_id, "status": "failed", "error": "Celery required"})
                 continue

        elif tool == "rotate":
             if celery_app:
                task = celery_app.send_task("rotate_pages", args=[job_id, path, job_params])
                jobs[job_id] = {"status": "queued", "celery_id": task.id}
             else:
                 responses.append({"job_id": job_id, "status": "failed", "error": "Celery required"})
                 continue

        elif tool == "metadata":
             if celery_app:
                task = celery_app.send_task("edit_metadata", args=[job_id, path, job_params])
                jobs[job_id] = {"status": "queued", "celery_id": task.id}
             else:
                 responses.append({"job_id": job_id, "status": "failed", "error": "Celery required"})
                 continue

        elif tool == "protect":
             if celery_app:
                task = celery_app.send_task("protect_pdf", args=[job_id, path, job_params])
                jobs[job_id] = {"status": "queued", "celery_id": task.id}
             else:
                 responses.append({"job_id": job_id, "status": "failed", "error": "Celery required"})
                 continue

        elif tool == "unlock":
             if celery_app:
                task = celery_app.send_task("unlock_pdf", args=[job_id, path, job_params])
                jobs[job_id] = {"status": "queued", "celery_id": task.id}
             else:
                 responses.append({"job_id": job_id, "status": "failed", "error": "Celery required"})
                 continue
        
        else:
            responses.append({"job_id": job_id, "status": "failed", "error": "Tool not supported"})
            continue
            
        responses.append({"job_id": job_id, "status": "queued", "filename": file.filename})

    return responses
