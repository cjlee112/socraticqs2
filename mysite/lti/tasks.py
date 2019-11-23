from mysite import celery_app
from lti.models import GradedLaunch
from lti.outcomes import send_score_update


@celery_app.task
def send_outcome(score, assignment_id):
    assignment = GradedLaunch.objects.get(id=assignment_id)
    send_score_update(assignment, score)
