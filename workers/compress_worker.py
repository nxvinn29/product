import os
import subprocess
from .celery_app import celery_app

@celery_app.task(name="compress_pdf")
def compress_pdf(job_id: str, input_path: str, params: dict):
    """
    Compress PDF using Ghostscript.
    Params:
      - level: 'low' | 'medium' | 'high'
    """
    level = params.get("level", "medium")
    
    # Map levels to Ghostscript PDFSETTINGS
    # /screen (72 dpi) - lowest quality, smallest size (High compression)
    # /ebook (150 dpi) - medium quality (Medium compression)
    # /printer (300 dpi) - high quality (Low compression)
    settings_map = {
        "high": "/screen",   # High compression = low quality
        "medium": "/ebook",
        "low": "/printer"    # Low compression = high quality
    }
    gs_setting = settings_map.get(level, "/ebook")
    
    output_path = f"/data/{job_id}_compressed.pdf"
    
    try:
        # ghostscript command
        # gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH -sOutputFile=output.pdf input.pdf
        mode = params.get("mode", "reduce") # 'reduce' or 'increase'
        target_kb = params.get("target_kb")
        target_size = int(target_kb) * 1024 if target_kb else None

        final_output = output_path

        if mode == "increase":
            # KB INCREASER WORKFLOW: Expand file data safely.
            # 1. Copy input to output first (to preserve original)
            import shutil
            shutil.copy2(input_path, final_output)
            
            if target_size:
                current_size = os.path.getsize(final_output)
                if current_size < target_size:
                    # Append null bytes to reach target size
                    padding = target_size - current_size
                    with open(final_output, "ab") as f:
                        f.write(b'\0' * padding)
        
        else:
            # KB REDUCER WORKFLOW: Compress to target size.
            
            # Strategy:
            # If target_kb is set, we try increasingly aggressive settings until we fit.
            # Levels: /printer (low comp), /ebook (med), /screen (high)
            
            candidates = []
            if target_size:
                levels_to_try = ["/printer", "/ebook", "/screen"]
            else:
                 # Default to medium if no target
                 levels_to_try = ["/ebook"]

            
            for idx, setting in enumerate(levels_to_try):
                # We use a temporary output for each attempt
                temp_output = f"/data/{job_id}_try_{idx}.pdf"
                
                cmd = [
                    "gs",
                    "-sDEVICE=pdfwrite",
                    "-dCompatibilityLevel=1.4",
                    f"-dPDFSETTINGS={setting}",
                    "-dNOPAUSE",
                    "-dQUIET",
                    "-dBATCH",
                    f"-sOutputFile={temp_output}",
                    input_path
                ]
                subprocess.run(cmd, check=True)
                
                size = os.path.getsize(temp_output)
                candidates.append((size, temp_output))
                
                # If we met the target, stop here
                if target_size and size <= target_size:
                    final_output = temp_output
                    break
            
            # If we finished loop and none met target...
            if target_size:
                best_candidate = min(candidates, key=lambda x: x[0])
                current_best_output = best_candidate[1]
                
                if best_candidate[0] > target_size:
                     # FORCE MODE: Aggressive downsampling
                     force_output = f"/data/{job_id}_force.pdf"
                     cmd_force = [
                        "gs",
                        "-sDEVICE=pdfwrite",
                        "-dCompatibilityLevel=1.4",
                        "-dPDFSETTINGS=/screen",
                        "-dColorImageDownsampleType=/Bicubic",
                        "-dColorImageResolution=72",
                        "-dGrayImageDownsampleType=/Bicubic",
                        "-dGrayImageResolution=72",
                        "-dNOPAUSE", "-dQUIET", "-dBATCH",
                        f"-sOutputFile={force_output}",
                        input_path
                     ]
                     try:
                        subprocess.run(cmd_force, check=True)
                        if os.path.getsize(force_output) < best_candidate[0]:
                            current_best_output = force_output
                     except:
                        pass

                # NUCLEAR MODE: Rasterize if still failing
                if os.path.getsize(current_best_output) > target_size:
                    nuclear_output = f"/data/{job_id}_nuclear.pdf"
                    try:
                        img_dir = f"/data/{job_id}_nuclear_imgs"
                        os.makedirs(img_dir, exist_ok=True)
                        subprocess.run([
                            "pdftoppm", "-jpeg", "-r", "72", input_path, 
                            os.path.join(img_dir, "page")
                        ], check=True)
                        subprocess.run(
                            f"convert {img_dir}/page-*.jpg -quality 30 -compress jpeg {nuclear_output}", 
                            shell=True, check=True
                        )
                        if os.path.getsize(nuclear_output) < os.path.getsize(current_best_output):
                            current_best_output = nuclear_output
                    except:
                        pass
                
                final_output = current_best_output
            else:
                final_output = candidates[0][1]

        # Rename successful file to expected output path if needed, or just return the path
        # But our main.py expects to download `output_path` (or we return the new path)
        # We will return the new path in the dict.

        
        # Calculate stats
        original_size = os.path.getsize(input_path)
        compressed_size = os.path.getsize(final_output)
        
        return {
            "file_path": final_output,
            "original_size": original_size,
            "compressed_size": compressed_size
        }
    
    except subprocess.CalledProcessError as e:
        raise Exception(f"Ghostscript failed: {e}")
    except Exception as exc:
        raise exc
