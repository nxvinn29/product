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
            # Use pdftoppm (poppler-utils) for high-quality conversion
            # pdftoppm -jpeg -r 150 input.pdf output_dir/page
            try:
                subprocess.run([
                    "pdftoppm",
                    "-jpeg",
                    "-r", "150",
                    input_path,
                    os.path.join(output_dir, "page")
                ], check=True)
            except FileNotFoundError:
                # Fallback to ImageMagick if pdftoppm not found (though it should be)
                subprocess.run([
                    "convert",
                    "-density", "150",
                    input_path,
                    "-quality", "90",
                    os.path.join(output_dir, "page-%d.jpg")
                ], check=True)

            # Zip the resulting images
            import shutil
            # make_archive expects invalid extension, so we give base name
            zip_base_name = f"/data/{job_id}_images"
            shutil.make_archive(zip_base_name, 'zip', output_dir)
            return f"{zip_base_name}.zip"

        # 3. Office -> PDF (Word/Excel -> PDF)
        if target_format == "pdf" and ext in ["docx", "doc", "xlsx", "pptx"]:
            # LibreOffice conversion
            # Note: soffice must be on PATH
            subprocess.run([
                "soffice",
                "--headless",
                "--convert-to", "pdf",
                input_path,
                "--outdir", output_dir
            ], check=True)
            
            # Soffice uses the same basename. Find the resulting PDF.
            # It might handle spaces differently, so finding the only PDF in dir is safer or predicting name.
            # Prediction:
            filename = os.path.basename(input_path)
            base = os.path.splitext(filename)[0]
            expected_output = os.path.join(output_dir, f"{base}.pdf")
            
            if os.path.exists(expected_output):
                return expected_output
            
            # Fallback check
            pdfs = [f for f in os.listdir(output_dir) if f.endswith(".pdf")]
            if pdfs:
                return os.path.join(output_dir, pdfs[0])
            raise Exception("PDF output not found after conversion")

        # 4. PDF -> Word (docx)
        elif target_format == "docx" and ext == "pdf":
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
            expected_output = os.path.join(output_dir, f"{base}.docx")
             
            if os.path.exists(expected_output):
                return expected_output
                
            # Fallback check
            docs = [f for f in os.listdir(output_dir) if f.endswith(".docx")]
            if docs:
                 return os.path.join(output_dir, docs[0])
            raise Exception("Word output not found after conversion")

        raise ValueError(f"Conversion from {ext} to {target_format} not supported")

    except subprocess.CalledProcessError as e:
        print(f"Subprocess failed: {e}")
        raise Exception(f"Conversion process failed: {e}")
    except Exception as exc:
        print(f"Worker exception: {exc}")
        raise exc
