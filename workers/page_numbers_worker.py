"""
Worker to add page numbers to PDF
"""
from .celery_app import celery_app
import os
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont


@celery_app.task(name="add_page_numbers", bind=True)
def add_page_numbers(self, job_id: str, input_path: str, params: dict = None) -> dict:
    """
    Add page numbers to PDF
    
    Args:
        job_id: Unique job identifier
        input_path: Path to input PDF
        params: dict with optional keys:
            - position: 'top', 'bottom', 'topright', 'topleft', 'bottomright', 'bottomleft' (default 'bottomright')
            - font_size: Font size (default 20)
            - format: 'Page {number}', '{number}', '{number}/{total}' etc (default '{number}')
            - start_from: Starting page number (default 1)
    
    Returns:
        dict with file_path to output PDF
    """
    if params is None:
        params = {}
    
    output_dir = os.path.dirname(input_path)
    output_path = os.path.join(output_dir, "numbered.pdf")
    
    try:
        position = params.get("position", "bottomright")
        font_size = params.get("font_size", 20)
        format_str = params.get("format", "{number}")
        start_from = params.get("start_from", 1)
        
        # Convert PDF to images
        images = convert_from_path(input_path, dpi=150)
        numbered_images = []
        total_pages = len(images)
        
        for idx, image in enumerate(images, start=start_from):
            numbered_img = image.copy()
            draw = ImageDraw.Draw(numbered_img)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Format page number
            page_num = idx
            page_text = format_str.replace("{number}", str(page_num)).replace("{total}", str(total_pages))
            
            # Get text size
            bbox = draw.textbbox((0, 0), page_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate position with margin
            margin = 20
            
            if position == "top":
                x = (numbered_img.width - text_width) // 2
                y = margin
            elif position == "bottom":
                x = (numbered_img.width - text_width) // 2
                y = numbered_img.height - text_height - margin
            elif position == "topright":
                x = numbered_img.width - text_width - margin
                y = margin
            elif position == "topleft":
                x = margin
                y = margin
            elif position == "bottomright":
                x = numbered_img.width - text_width - margin
                y = numbered_img.height - text_height - margin
            elif position == "bottomleft":
                x = margin
                y = numbered_img.height - text_height - margin
            else:
                x = numbered_img.width - text_width - margin
                y = numbered_img.height - text_height - margin
            
            # Draw page number
            draw.text((x, y), page_text, font=font, fill=(0, 0, 0))
            numbered_images.append(numbered_img)
        
        # Save as PDF
        if numbered_images:
            numbered_images[0].save(
                output_path,
                save_all=True,
                append_images=numbered_images[1:] if len(numbered_images) > 1 else []
            )
        
        return {"file_path": output_path}
    
    except Exception as e:
        raise Exception(f"Add page numbers operation failed: {str(e)}")
