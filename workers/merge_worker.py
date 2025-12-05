import os
import pikepdf
from .celery_app import celery_app

@celery_app.task(name="merge_pdfs")
def merge_pdfs(job_id: str, input_paths: list):
    """
    Merge a list of PDF file paths into a single PDF.
    Stores the result in /tmp/{job_id}_merged.pdf and returns the path.
    """
    output_path = f"/data/{job_id}_merged.pdf"
    try:
        pdf_writer = pikepdf.Pdf.new()
        for pdf_path in input_paths:
            # Open each PDF and append its pages
            with pikepdf.Pdf.open(pdf_path) as pdf_reader:
                pdf_writer.pages.extend(pdf_reader.pages)
        
        pdf_writer.save(output_path)
        pdf_writer.close()
        return output_path
    except Exception as exc:
        raise exc
