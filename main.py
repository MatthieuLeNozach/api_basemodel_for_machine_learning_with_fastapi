import logging

from project import create_app

logger = logging.getLogger(__name__)

app = create_app()
celery = app.celery_app
