"""
Worker to add watermarks to PDF
Supports both text and image watermarks
"""
from .celery_app import celery_app
import os
import pikepdf
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_path
import io


@celery_app.task(name="add_watermark", bind=True)
def add_watermark(self, job_id: str, input_path: str, params: dict = None) -> dict:
    """
    Add watermark to PDF (text or image)
    
    Args:
        job_id: Unique job identifier
        input_path: Path to input PDF
        params: dict with keys:
            - watermark_type: 'text' or 'image' (required)
            - text: Text for watermark (if type is 'text')
            - image_path: Path to watermark image (if type is 'image')
            - opacity: Opacity 0-1 (default 0.3)
            - position: 'center', 'topleft', 'topright', 'bottomleft', 'bottomright' (default 'center')
            - rotation: Rotation angle in degrees (default 45)
            - font_size: Font size for text watermark (default 60)
    
    Returns:
        dict with file_path to output PDF
    """
    if params is None:
        params = {}
    
    output_dir = os.path.dirname(input_path)
    output_path = os.path.join(output_dir, "watermarked.pdf")
    
    try:
        watermark_type = params.get("watermark_type", "text")
        opacity = params.get("opacity", 0.3)
        position = params.get("position", "center")
        rotation = params.get("rotation", 45)
        
        # Convert PDF to images
        images = convert_from_path(input_path, dpi=150)
        watermarked_images = []
        
        for image in images:
            watermarked_img = image.copy()
            
            if watermark_type == "text":
                text = params.get("text", "WATERMARK")
                font_size = params.get("font_size", 60)
                
                # Create watermark text on transparent layer
                watermark = Image.new('RGBA', watermarked_img.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(watermark)
                
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                # Get text bbox
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Calculate position
                if position == "center":
                    x = (watermarked_img.width - text_width) // 2
                    y = (watermarked_img.height - text_height) // 2
                elif position == "topleft":
                    x, y = 20, 20
                elif position == "topright":
                    x = watermarked_img.width - text_width - 20
                    y = 20
                elif position == "bottomleft":
                    x = 20
                    y = watermarked_img.height - text_height - 20
                elif position == "bottomright":
                    x = watermarked_img.width - text_width - 20
                    y = watermarked_img.height - text_height - 20
                else:
                    x = (watermarked_img.width - text_width) // 2
                    y = (watermarked_img.height - text_height) // 2
                
                # Draw text with opacity
                alpha = int(255 * opacity)
                draw.text((x, y), text, font=font, fill=(128, 128, 128, alpha))
                
                # Rotate if needed
                if rotation != 0:
                    watermark = watermark.rotate(rotation, expand=True)
                
                # Composite watermark onto image
                if watermarked_img.mode != 'RGBA':
                    watermarked_img = watermarked_img.convert('RGBA')
                watermarked_img = Image.alpha_composite(watermarked_img, watermark)
                watermarked_img = watermarked_img.convert('RGB')
            
            elif watermark_type == "image":
                image_path = params.get("image_path")
                if image_path and os.path.exists(image_path):
                    watermark_img = Image.open(image_path).convert('RGBA')
                    
                    # Resize watermark to fit
                    max_width = watermarked_img.width // 3
                    max_height = watermarked_img.height // 3
                    watermark_img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    
                    # Adjust opacity
                    alpha = watermark_img.split()[3]
                    alpha = alpha.point(lambda p: int(p * opacity))
                    watermark_img.putalpha(alpha)
                    
                    # Calculate position
                    if position == "center":
                        x = (watermarked_img.width - watermark_img.width) // 2
                        y = (watermarked_img.height - watermark_img.height) // 2
                    elif position == "topleft":
                        x, y = 20, 20
                    elif position == "topright":
                        x = watermarked_img.width - watermark_img.width - 20
                        y = 20
                    elif position == "bottomleft":
                        x = 20
                        y = watermarked_img.height - watermark_img.height - 20
                    elif position == "bottomright":
                        x = watermarked_img.width - watermark_img.width - 20
                        y = watermarked_img.height - watermark_img.height - 20
                    else:
                        x = (watermarked_img.width - watermark_img.width) // 2
                        y = (watermarked_img.height - watermark_img.height) // 2
                    
                    if watermarked_img.mode != 'RGBA':
                        watermarked_img = watermarked_img.convert('RGBA')
                    watermarked_img.paste(watermark_img, (x, y), watermark_img)
                    watermarked_img = watermarked_img.convert('RGB')
            
            watermarked_images.append(watermarked_img)
        
        # Save as PDF
        if watermarked_images:
            watermarked_images[0].save(
                output_path,
                save_all=True,
                append_images=watermarked_images[1:] if len(watermarked_images) > 1 else []
            )
        
        return {"file_path": output_path}
    
    except Exception as e:
        raise Exception(f"Watermark operation failed: {str(e)}")
