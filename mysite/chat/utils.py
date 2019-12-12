from uuid import uuid4

from django.utils import timezone

from core.common.mongo import c_chat_context


def enroll_generator():
    """
    Generate a random key
    """
    return uuid4().hex


def update_activity(chat_id: int) -> None:
    """
    Update chat context for a currently active thread.
    """
    context = c_chat_context().find_one({"chat_id": chat_id})
    if context and context.get('thread_id'):
        thread_id = context.get('thread_id')
        c_chat_context().update_one(
            {"chat_id": chat_id},
            {"$set": {
                f"activity.{thread_id}": timezone.now()
            }},
        )
