"""
Worker to unlock/remove password from PDF
"""
from .celery_app import celery_app
import os
import pikepdf


@celery_app.task(name="unlock_pdf", bind=True)
def unlock_pdf(self, job_id: str, input_path: str, params: dict = None) -> dict:
    """
    Unlock/remove password from PDF
    
    Args:
        job_id: Unique job identifier
        input_path: Path to input PDF
        params: dict with required key:
            - password: Password to unlock the PDF
    
    Returns:
        dict with file_path to unprotected PDF
    """
    if params is None:
        params = {}
    
    output_dir = os.path.dirname(input_path)
    output_path = os.path.join(output_dir, "unlocked.pdf")
    
    try:
        password = params.get("password", "")
        
        # Open PDF with password
        with pikepdf.open(input_path, password=password) as pdf:
            # Save without encryption
            pdf.save(output_path)
        
        return {"file_path": output_path}
    
    except pikepdf.PasswordError:
        raise Exception(f"Incorrect password or password-protected PDF is corrupted")
    except Exception as e:
        raise Exception(f"PDF unlock failed: {str(e)}")
