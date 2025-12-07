from celery import Celery

celery_app = Celery(
    "pdfsimple",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=[
        "workers.merge_worker",
        "workers.split_worker",
        "workers.convert_worker",
        "workers.compress_worker",
        "workers.ocr_worker",
        "workers.pdf_to_pptx_worker",
        "workers.pdf_to_xlsx_worker",
        "workers.pdf_to_html_worker",
        "workers.images_to_pdf_worker",
        "workers.watermark_worker",
        "workers.page_numbers_worker",
        "workers.rotate_pages_worker",
        "workers.metadata_worker",
        "workers.protect_pdf_worker",
        "workers.unlock_pdf_worker",
    ]
)

# Auto-discover tasks (optional if we use include)
celery_app.autodiscover_tasks(["workers"], force=True)
