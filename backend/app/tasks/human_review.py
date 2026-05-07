from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def submit_human_review(self, session_id: str, user_id: str, query: str, context: str):
    """
    Submit a difficult customer query for human review.

    In production, this would:
    1. Push to a review queue (database table or external system)
    2. Notify available human agents via WebSocket/push
    3. Handle timeout escalation if no agent responds
    """
    # Placeholder: log the review request
    import logging
    logger = logging.getLogger("human_review")
    logger.info(
        f"Human review requested: session={session_id}, user={user_id}, query={query[:100]}..."
    )
    return {
        "session_id": session_id,
        "status": "queued",
    }


@celery_app.task(bind=True)
def process_review_result(self, session_id: str, result: dict | None = None):
    """
    Process the result of a human review.
    Called when a human agent resolves the query.
    """
    import logging
    logger = logging.getLogger("human_review")
    logger.info(f"Review completed: session={session_id}, result={result}")
    return {"session_id": session_id, "status": "completed"}
