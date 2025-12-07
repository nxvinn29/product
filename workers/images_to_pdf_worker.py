"""
Worker to convert images to PDF
Supports PNG, TIFF, GIF, and JPG formats
"""
from .celery_app import celery_app
import os
from PIL import Image
import io


@celery_app.task(name="images_to_pdf", bind=True)
def images_to_pdf(self, job_id: str, input_paths: list, params: dict = None) -> dict:
    """
    Convert multiple images to a single PDF
    Supports PNG, TIFF, GIF, JPG
    
    Args:
        job_id: Unique job identifier
        input_paths: List of paths to input images
        params: dict with optional keys:
            - orientation: 'portrait' or 'landscape' (default 'auto')
            - page_size: 'A4', 'Letter', 'A3' etc (default 'A4')
    
    Returns:
        dict with file_path to output .pdf file
    """
    if params is None:
        params = {}
    
    output_dir = os.path.dirname(input_paths[0]) if input_paths else "/data"
    output_path = os.path.join(output_dir, "output.pdf")
    
    try:
        orientation = params.get("orientation", "auto")
        
        if not input_paths:
            raise ValueError("No input images provided")
        
        # Open all images
        images = []
        for img_path in input_paths:
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"Image file not found: {img_path}")
            
            img = Image.open(img_path)
            
            # Convert RGBA to RGB if needed (PDF doesn't support transparency well)
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            images.append(img)
        
        # Save as PDF
        if images:
            images[0].save(
                output_path,
                save_all=True,
                append_images=images[1:] if len(images) > 1 else []
            )
        
        return {"file_path": output_path}
    
    except Exception as e:
        raise Exception(f"Images to PDF conversion failed: {str(e)}")
