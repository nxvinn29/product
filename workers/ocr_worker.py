import os
import pytesseract
from pdf2image import convert_from_path

def ocr_pdf(job_id, input_path, params=None):
    """
    Convert PDF to images, then OCR each image to text (or searchable PDF).
    For MVP, let's process each page and create a text file or a searchable PDF.
    
    If params['output_format'] == 'text':
        Return full text string or path to .txt file.
    Else:
        Return path to searchable PDF (using pytesseract.image_to_pdf_or_hocr).
    """
    if params is None:
        params = {}
    
    output_format = params.get('output_format', 'pdf') # 'pdf' or 'text'
    lang = params.get('lang', 'eng')
    
    # Generate output path
    base_dir = os.path.dirname(input_path)
    if output_format == 'text':
        output_filename = f"{os.path.basename(input_path)}_ocr.txt"
    else:
        output_filename = f"{os.path.basename(input_path)}_searchable.pdf"
        
    output_path = os.path.join(base_dir, output_filename)
    
    try:
        # 1. Convert PDF pages to images
        # 500 dpi is good for OCR, but slow. 300 is standard.
        images = convert_from_path(input_path, dpi=300)
        
        if output_format == 'text':
            full_text = []
            for img in images:
                text = pytesseract.image_to_string(img, lang=lang)
                full_text.append(text)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(full_text))
                
        else:
            # Create searchable PDF
            # simple loop: get pdf data for each page and merge?
            # Or use pytesseract to get PDF bytes for the whole image list? 
            # pytesseract supports image-to-pdf.
            # But we have multiple images (pages).
            # We need to process each page and merge them.
            
            from PyPDF2 import PdfMerger # Or we can use our merge_worker logic if available, or just PdfMerger
            # But we only have pikepdf installed in requirements? (Let's check).
            # requirements has `pikepdf`. We can use pikepdf to merge.
            # But pytesseract output is bytes.
            
            import pikepdf
            import io
            
            pdf = pikepdf.new()
            
            for img in images:
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf', lang=lang)
                with pikepdf.open(io.BytesIO(pdf_bytes)) as page_pdf:
                    pdf.pages.extend(page_pdf.pages)
            
            pdf.save(output_path)
            
        return {"file_path": output_path}

    except Exception as e:
        raise RuntimeError(f"OCR failed: {str(e)}")
