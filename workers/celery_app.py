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
    ]
)

# Auto-discover tasks (optional if we use include)
celery_app.autodiscover_tasks(["workers"], force=True)
