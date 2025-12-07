"""
Worker to view and edit PDF metadata
"""
from .celery_app import celery_app
import os
import pikepdf
import json


@celery_app.task(name="edit_metadata", bind=True)
def edit_metadata(self, job_id: str, input_path: str, params: dict = None) -> dict:
    """
    View and edit PDF metadata
    
    Args:
        job_id: Unique job identifier
        input_path: Path to input PDF
        params: dict with optional metadata fields:
            - title: Document title
            - author: Document author
            - subject: Document subject
            - keywords: Document keywords
            - creator: Application that created the original PDF
            - producer: Application that produced the PDF
            - action: 'get' to retrieve metadata, 'set' to update metadata (default 'set')
    
    Returns:
        dict with file_path and/or metadata
    """
    if params is None:
        params = {}
    
    action = params.get("action", "set")
    output_dir = os.path.dirname(input_path)
    
    try:
        with pikepdf.open(input_path) as pdf:
            # Get current metadata
            current_metadata = {}
            if pdf.metadata:
                current_metadata = {
                    "title": str(pdf.metadata.get("/Title", "")),
                    "author": str(pdf.metadata.get("/Author", "")),
                    "subject": str(pdf.metadata.get("/Subject", "")),
                    "keywords": str(pdf.metadata.get("/Keywords", "")),
                    "creator": str(pdf.metadata.get("/Creator", "")),
                    "producer": str(pdf.metadata.get("/Producer", "")),
                }
            
            if action == "get":
                # Just return current metadata
                return {"metadata": current_metadata, "file_path": input_path}
            
            elif action == "set":
                # Update metadata
                metadata_updates = {
                    "/Title": params.get("title"),
                    "/Author": params.get("author"),
                    "/Subject": params.get("subject"),
                    "/Keywords": params.get("keywords"),
                    "/Creator": params.get("creator"),
                    "/Producer": params.get("producer"),
                }
                
                # Remove None values and apply updates
                for key, value in metadata_updates.items():
                    if value is not None:
                        pdf.metadata[key] = value
                
                output_path = os.path.join(output_dir, "metadata_edited.pdf")
                pdf.save(output_path)
                
                return {"file_path": output_path, "metadata": metadata_updates}
        
        return {"status": "success"}
    
    except Exception as e:
        raise Exception(f"Metadata operation failed: {str(e)}")
