"""
Worker to protect PDF with password
"""
from .celery_app import celery_app
import os
import pikepdf


@celery_app.task(name="protect_pdf", bind=True)
def protect_pdf(self, job_id: str, input_path: str, params: dict = None) -> dict:
    """
    Protect PDF with password
    
    Args:
        job_id: Unique job identifier
        input_path: Path to input PDF
        params: dict with required keys:
            - password: Password to protect the PDF
            - owner_password: (Optional) Additional owner password for more restrictions
            - permissions: List of permitted operations 
              ('print', 'modify', 'copy', 'add_annotations') - default allow all
    
    Returns:
        dict with file_path to output PDF
    """
    if params is None:
        params = {}
    
    output_dir = os.path.dirname(input_path)
    output_path = os.path.join(output_dir, "protected.pdf")
    
    try:
        user_password = params.get("password", "")
        owner_password = params.get("owner_password", "")
        
        if not user_password and not owner_password:
            raise ValueError("At least one password (user or owner) must be provided")
        
        with pikepdf.open(input_path) as pdf:
            # Set encryption with passwords
            # Pikepdf uses user_password for opening and owner_password for permissions
            encryption_params = {
                "user_password": user_password,
                "owner_password": owner_password or user_password,
                "R": 5,  # Use R=5 for better encryption (AES-256)
            }
            
            pdf.save(output_path, encryption=pikepdf.Encryption(**encryption_params))
        
        return {"file_path": output_path}
    
    except Exception as e:
        raise Exception(f"PDF protection failed: {str(e)}")
