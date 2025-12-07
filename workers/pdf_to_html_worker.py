"""
Worker to convert PDF to HTML
Uses pdfplumber to extract text and basic structure
"""
from .celery_app import celery_app
import os
import pdfplumber
from pdf2image import convert_from_path


@celery_app.task(name="pdf_to_html", bind=True)
def pdf_to_html(self, job_id: str, input_path: str, params: dict = None) -> dict:
    """
    Convert PDF to HTML
    Can produce text-based or image-based HTML
    
    Args:
        job_id: Unique job identifier
        input_path: Path to input PDF
        params: dict with optional keys:
            - mode: 'text' or 'images' (default 'text')
            - dpi: DPI for image conversion (default 150, only for 'images' mode)
    
    Returns:
        dict with file_path to output .html file
    """
    if params is None:
        params = {}
    
    output_dir = os.path.dirname(input_path)
    output_path = os.path.join(output_dir, "output.html")
    
    try:
        mode = params.get("mode", "text")
        dpi = params.get("dpi", 150)
        
        html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Document</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .page { margin-bottom: 40px; page-break-after: always; border: 1px solid #ddd; padding: 20px; }
        .page img { max-width: 100%; height: auto; }
        .text-content { white-space: pre-wrap; word-wrap: break-word; }
        h1 { color: #333; }
    </style>
</head>
<body>
"""
        
        if mode == "images":
            # Convert each page to image and embed
            images = convert_from_path(input_path, dpi=dpi)
            
            for idx, image in enumerate(images, 1):
                # Save image
                img_path = os.path.join(output_dir, f"page_{idx}.png")
                image.save(img_path, "PNG")
                
                # Get relative path for HTML
                rel_img_path = f"page_{idx}.png"
                html_content += f'<div class="page"><h1>Page {idx}</h1><img src="{rel_img_path}" alt="Page {idx}"></div>\n'
        
        else:  # text mode
            with pdfplumber.open(input_path) as pdf:
                for page_idx, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    
                    # Extract tables if any
                    tables = page.extract_tables()
                    
                    html_content += f'<div class="page"><h1>Page {page_idx}</h1>'
                    
                    if text:
                        html_content += f'<div class="text-content">{text}</div>'
                    
                    if tables:
                        html_content += '<table border="1" cellpadding="5" cellspacing="0">\n'
                        for row in tables[0]:  # Use first table
                            html_content += '<tr>'
                            for cell in row:
                                html_content += f'<td>{cell or ""}</td>'
                            html_content += '</tr>\n'
                        html_content += '</table>\n'
                    
                    html_content += '</div>\n'
        
        html_content += """</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return {"file_path": output_path}
    
    except Exception as e:
        raise Exception(f"PDF to HTML conversion failed: {str(e)}")
