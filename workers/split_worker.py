import os
import pikepdf
from .celery_app import celery_app

@celery_app.task(name="split_pdf")
def split_pdf(job_id: str, input_path: str, params: dict):
    """
    Split a PDF into multiple files.
    Params:
      - method: 'intervals' | 'extract' (demo: basic page range)
      - pages: '1-3,5' (string spec)
    
    For MVP, we just split every page into a separate PDF if no params,
    or extract specific pages if params provided.
    """
    output_dir = f"/data/{job_id}_split"
    os.makedirs(output_dir, exist_ok=True)
    
    output_files = []
    
    try:
        with pikepdf.Pdf.open(input_path) as pdf:
            # Simple implementation: extract defined pages or all
            # For now, let's just extract all pages as separate files
            for i, page in enumerate(pdf.pages):
                dst = pikepdf.Pdf.new()
                dst.pages.append(page)
                out_name = os.path.join(output_dir, f"page_{i+1}.pdf")
                dst.save(out_name)
                dst.close()
                output_files.append(out_name)
        
        # In a real app, we might zip these if there are many
        # For this MVP, we return the directory path or list
        return output_files
    except Exception as exc:
        raise exc
