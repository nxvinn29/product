import os
import subprocess
from .celery_app import celery_app

@celery_app.task(name="compress_pdf")
def compress_pdf(job_id: str, input_path: str, params: dict):
    """
    Compress PDF using Ghostscript.
    Params:
      - level: 'low' | 'medium' | 'high'
    """
    level = params.get("level", "medium")
    
    # Map levels to Ghostscript PDFSETTINGS
    # /screen (72 dpi) - lowest quality, smallest size (High compression)
    # /ebook (150 dpi) - medium quality (Medium compression)
    # /printer (300 dpi) - high quality (Low compression)
    settings_map = {
        "high": "/screen",   # High compression = low quality
        "medium": "/ebook",
        "low": "/printer"    # Low compression = high quality
    }
    gs_setting = settings_map.get(level, "/ebook")
    
    output_path = f"/data/{job_id}_compressed.pdf"
    
    try:
        # ghostscript command
        # gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH -sOutputFile=output.pdf input.pdf
        cmd = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS={gs_setting}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_path}",
            input_path
        ]
        
        subprocess.run(cmd, check=True)
        return output_path
    
    except subprocess.CalledProcessError as e:
        raise Exception(f"Ghostscript failed: {e}")
    except Exception as exc:
        raise exc
