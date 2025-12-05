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

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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

from fastapi import Form
import json

@app.post("/jobs")
async def create_job(
    tool: str = Form(...),
    params: str = Form("{}"), # JSON string
    files: List[UploadFile] = File(...)
):
    job_id = str(uuid.uuid4())
    upload_dir = f"/data/{job_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Parse params
    try:
        job_params = json.loads(params)
    except:
        job_params = {}

    input_paths = []
    for file in files:
        path = f"{upload_dir}/{file.filename}"
        with open(path, "wb") as out_file:
            content = await file.read()
            out_file.write(content)
        input_paths.append(path)

    # Use 'tool' directly instead of job.tool


    if tool == "merge":
@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # In a real app, we'd check Celery task status here if it's still queued/processing
    if job.get("celery_id") and celery_app:
        res = celery_app.AsyncResult(job["celery_id"])
        if res.ready():
            job["status"] = "completed" if res.successful() else "failed"
            if res.successful():
                job["output"] = res.result
    
    return {"job_id": job_id, "status": job["status"]}

@app.get("/jobs/{job_id}/result")
async def download_result(job_id: str):
    job = jobs.get(job_id)
    if not job or job.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Result not available")
    result_path = job.get("output")
    if not result_path or not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(result_path, filename=os.path.basename(result_path))
