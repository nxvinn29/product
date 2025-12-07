"""
Worker to rotate PDF pages
"""
from .celery_app import celery_app
import os
import pikepdf


@celery_app.task(name="rotate_pages", bind=True)
def rotate_pages(self, job_id: str, input_path: str, params: dict = None) -> dict:
    """
    Rotate PDF pages
    
    Args:
        job_id: Unique job identifier
        input_path: Path to input PDF
        params: dict with keys:
            - angle: Rotation angle in degrees (90, 180, 270)
            - pages: List of page numbers to rotate, or 'all' for all pages (default 'all')
    
    Returns:
        dict with file_path to output PDF
    """
    if params is None:
        params = {}
    
    output_dir = os.path.dirname(input_path)
    output_path = os.path.join(output_dir, "rotated.pdf")
    
    try:
        angle = params.get("angle", 90)
        pages_param = params.get("pages", "all")
        
        # Validate angle
        if angle not in [90, 180, 270, -90, -180, -270]:
            raise ValueError(f"Invalid angle {angle}. Must be 90, 180, or 270 degrees")
        
        # Normalize angle to pikepdf format (0, 90, 180, 270)
        rotation_map = {
            90: 90,
            180: 180,
            270: 270,
            -90: 270,
            -180: 180,
            -270: 90
        }
        normalized_angle = rotation_map[angle]
        
        with pikepdf.open(input_path) as pdf:
            if pages_param == "all":
                # Rotate all pages
                for page in pdf.pages:
                    page.Rotate = normalized_angle
            else:
                # Rotate specific pages
                if isinstance(pages_param, list):
                    page_numbers = pages_param
                elif isinstance(pages_param, str):
                    # Parse comma-separated or range
                    page_numbers = []
                    for part in pages_param.split(','):
                        if '-' in part:
                            start, end = part.split('-')
                            page_numbers.extend(range(int(start.strip()), int(end.strip()) + 1))
                        else:
                            page_numbers.append(int(part.strip()))
                else:
                    page_numbers = [pages_param]
                
                # Convert to 0-indexed and rotate
                for page_num in page_numbers:
                    if 1 <= page_num <= len(pdf.pages):
                        pdf.pages[page_num - 1].Rotate = normalized_angle
            
            pdf.save(output_path)
        
        return {"file_path": output_path}
    
    except Exception as e:
        raise Exception(f"Rotate pages operation failed: {str(e)}")
