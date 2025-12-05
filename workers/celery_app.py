from celery import Celery

celery_app = Celery(
    "pdfsimple",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["workers"], force=True)
