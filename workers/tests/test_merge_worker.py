import os
import tempfile
try:
    from workers.merge_worker import merge_pdfs
except ImportError:
    from merge_worker import merge_pdfs


def test_merge_pdfs_creates_output():
    # Create two simple PDF files using pikepdf
    import pikepdf
    tmp_dir = tempfile.mkdtemp()
    pdf1_path = os.path.join(tmp_dir, "a.pdf")
    pdf2_path = os.path.join(tmp_dir, "b.pdf")
    # Create minimal PDFs with one blank page each
    for path in (pdf1_path, pdf2_path):
        pdf = pikepdf.Pdf.new()
        pdf.save(path)
        pdf.close()
    job_id = "testjob"
    output_path = merge_pdfs(job_id, [pdf1_path, pdf2_path])
    assert os.path.exists(output_path)
    # Verify that the merged PDF has 2 pages
    merged = pikepdf.Pdf.open(output_path)
    assert len(merged.pages) == 2
    merged.close()
