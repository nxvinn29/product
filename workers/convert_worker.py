import os
import subprocess
from .celery_app import celery_app

@celery_app.task(name="convert_file")
def convert_file(job_id: str, input_path: str, params: dict):
    """
    Convert file format.
    Params:
      - target_format: 'pdf' | 'docx' | 'jpg'
    """
    target_format = params.get("target_format")
    if not target_format:
        raise ValueError("target_format is required")
        
    output_dir = f"/data/{job_id}_convert"
    os.makedirs(output_dir, exist_ok=True)
    
    # Check input extension
    _, ext = os.path.splitext(input_path)
    ext = ext.lower().replace(".", "")
    
    try:
        # 1. Image -> PDF
        if target_format == "pdf" and ext in ["jpg", "jpeg", "png"]:
            output_path = os.path.join(output_dir, "converted.pdf")
            # Use ImageMagick: convert input.jpg output.pdf
            subprocess.run(["convert", input_path, output_path], check=True)
            return output_path
            
        # 2. PDF -> Image (JPG)
        elif target_format == "jpg" and ext == "pdf":
            # Use ImageMagick or pdftoppm. 
            # Ghostscript: gs -sDEVICE=jpeg -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -r150 -o output-%d.jpg input.pdf
            # This creates multiple files. We'll zip them or just return directory?
            # For simple MVP, let's just return the first page or zip?
            # Let's return the directory path if multiple, or expected output path.
            # Our backend expects a single result file path usually.
            # Let's start with single file output logic or create a zip.
            # Simplified: Use convert to make one long jpg? No that's huge.
            # Let's assume we return a ZIP of images.
            # TODO: Add zip logic. For now, let's convert page 1 only as preview or use basic.
            pass

        # 3. Office -> PDF (Word/Excel -> PDF)
        if target_format == "pdf" and ext in ["docx", "doc", "xlsx", "pptx"]:
            # LibreOffice headless
            # soffice --headless --convert-to pdf input.docx --outdir /tmp/...
            subprocess.run([
                "soffice",
                "--headless",
                "--convert-to", "pdf",
                input_path,
                "--outdir", output_dir
            ], check=True)
            
            # LibreOffice keeps filename but changes extension
            # input name: foo.docx -> foo.pdf
            filename = os.path.basename(input_path)
            base = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{base}.pdf")
            return output_path

        # 4. PDF -> Word (docx)
        elif target_format == "docx" and ext == "pdf":
             # LibreOffice supports PDF import? Yes but results vary.
             # soffice --infilter="writer_pdf_import" --convert-to docx input.pdf
            subprocess.run([
                "soffice",
                "--headless",
                "--infilter=writer_pdf_import",
                "--convert-to", "docx",
                input_path,
                "--outdir", output_dir
            ], check=True)
            
            filename = os.path.basename(input_path)
            base = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{base}.docx")
            return output_path

        raise ValueError(f"Conversion from {ext} to {target_format} not supported or NotImplemented")

    except subprocess.CalledProcessError as e:
        raise Exception(f"Conversion failed: {e}")
    except Exception as exc:
        raise exc
