from celery import current_app as current_celery_app
from celery.result import AsyncResult
from project.config import settings
import functools
import logging
from celery import shared_task
from celery.utils.log import get_task_logger
from celery.exceptions import MaxRetriesExceededError

logger = get_task_logger(__name__)

def create_celery():
    celery_app = current_celery_app
    celery_app.config_from_object(settings, namespace="CELERY")

    return celery_app


def get_task_info(task_id):
    """
    return task info according to the task_id
    """
    task = AsyncResult(task_id)
    state = task.state

    if state == "FAILURE":
        error = str(task.result)
        response = {
            "state": task.state,
            "error": error,
        }
    else:
        response = {
            "state": task.state,
        }
    return response



@shared_task
def dummy_task():
    return "This is a dummy task."



class custom_celery_task:

    EXCEPTION_BLOCK_LIST = (
        IndexError,
        KeyError,
        TypeError,
        UnicodeDecodeError,
        ValueError,
        MemoryError,
        #ResourceExhaustedError,
    )

    def __init__(self, *args, **kwargs):
        self.task_args = args
        self.task_kwargs = kwargs

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper_func(*args, **kwargs):
            try:
                logger.info(f"Starting task {func.__name__} with args: {args}, kwargs: {kwargs}")
                if self.task_kwargs.get('bind', False):
                    # If bind=True, the first argument is 'self'
                    result = func(args[0], *args[1:], **kwargs)
                else:
                    result = func(*args, **kwargs)
                logger.info(f"Completed task {func.__name__} with result: {result}")
                return result
            except self.EXCEPTION_BLOCK_LIST as e:
                logger.error(f"Task {func.__name__} failed with non-retryable exception: {e}")
                raise
            except Exception as e:
                logger.error(f"Task {func.__name__} failed with exception: {e}")
                countdown = self._get_retry_countdown(task_func)
                raise task_func.retry(exc=e, countdown=countdown)

        task_func = shared_task(*self.task_args, **self.task_kwargs)(wrapper_func)
        return task_func

    def _get_retry_countdown(self, task_func):
        retry_backoff = int(
            max(1.0, float(self.task_kwargs.get('retry_backoff', True)))
        )
        retry_backoff_max = int(
            self.task_kwargs.get('retry_backoff_max', 600)
        )
        retry_jitter = self.task_kwargs.get(
            'retry_jitter', True
        )

        countdown = self.get_exponential_backoff_interval(
            factor=retry_backoff,
            retries=task_func.request.retries,
            maximum=retry_backoff_max,
            full_jitter=retry_jitter
        )

        return countdown

    @staticmethod
    def get_exponential_backoff_interval(factor, retries, maximum, full_jitter):
        """
        Calculate the exponential backoff interval.
        """
        import random
        interval = min(maximum, factor * (2 ** retries))
        if full_jitter:
            interval = random.uniform(0, interval)
        return interval