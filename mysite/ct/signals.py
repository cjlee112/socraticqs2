"""
Django signals for the app.
"""
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.sites.models import Site

from models import Response

from core.common.mongo import c_milestone_orct
from core.common.utils import send_email, suspendingreceiver


def middle_numbers(lst):
    """
    Fetch one or two middle numbers of a list.
    """
    n = len(lst)
    if n <= 2:
        return [None]
    if n % 2 == 0:
        return [lst[n / 2 - 1], lst[n / 2]]
    else:
        return [lst[n // 2]]


@suspendingreceiver(post_save, sender=Response)
def run_courselet_notif_flow(sender, instance, **kwargs):
    # TODO: add check that Response has a text, as an obj can be created before a student submits
    # TODO: exclude self eval submits other than response submit

    if getattr(instance, 'ORCT_RESPONSE', None) and not getattr(instance, 'is_test', None) \
            and not getattr(instance, 'is_preview', None):
        course = getattr(instance, 'course', None)
        student = getattr(instance, 'author', None)
        instructors = course.get_users(role="prof")
        student_id = student.id if student else None

        # Exclude instructors, e.g. the ones submitting in preview mode
        for instructor in instructors:
            if student_id == instructor.id:
                return

        unit_lesson = getattr(instance, 'unitLesson', None)
        unit_lesson_id = unit_lesson.id if unit_lesson else None  # it's a thread
        lesson = getattr(instance, 'lesson', None)

        # Define if it's a milestone question (either first, middle, or last)
        milestone = None
        questions = unit_lesson.unit.all_orct()
        for i, orct in enumerate(questions):
            if orct.id == unit_lesson_id:
                if i == 0:
                    milestone = "first"
                elif i == len(questions) - 1:
                    milestone = "last"
                elif orct in middle_numbers(questions):
                    milestone = "middle"  # TODO consider returning a single number

        # If milestone, store the record
        if milestone:
            course_id = course.id if course else None

            to_save = {
                "milestone": milestone,
                "lesson_title": lesson.title if lesson else None,
                "lesson_id": lesson.id if lesson else None,
                "unit_lesson_id": unit_lesson_id,
                "course_title": course.title if course else None,
                "course_id": course_id,
                "student_username": student.username if student else None,
                "student_id": student_id,
                # "datetime": datetime.datetime.now()  # TODO: consider changing to UTC (and making it a timestamp)
            }
            criteria = {
                "milestone": milestone,
                "lesson_id": lesson.id if lesson else None
            }
            # Do not store if such `student_id`-`lesson_id` row is already present
            milestone_orct_answers_cursor = c_milestone_orct(use_secondary=False).find(criteria)
            initial_milestone_orct_answers_number = milestone_orct_answers_cursor.count()
            milestone_orct_answers = (a for a in milestone_orct_answers_cursor)

            already_exists = False
            for answer in milestone_orct_answers:
                if answer.get("student_id") == student_id:
                    already_exists = True
                    break

            if not already_exists:
                c_milestone_orct(use_secondary=False).save(to_save)
                milestone_orct_answers_number = initial_milestone_orct_answers_number + 1

                # If N students responded to a milestone question, send an email.
                # The threshold holds for each milestone separately.
                if milestone_orct_answers_number == settings.MILESTONE_ORCT_NUMBER:
                    send_email(
                        context_data={
                            "milestone": milestone,
                            "students_number": milestone_orct_answers_number,
                            "course_title": course.title if course else None,
                            "lesson_title": lesson.title if lesson else None,
                            "current_site": Site.objects.get_current(),
                            "course_id": course_id,
                            "unit_lesson_id": unit_lesson_id,
                            "courselet_pk": unit_lesson.unit.id if unit_lesson.unit else None
                        },
                        from_email=settings.EMAIL_FROM,
                        to_email=[instructor.email for instructor in instructors],
                        template_subject="ct/email/milestone_ortc_notify_subject",
                        template_text="ct/email/milestone_ortc_notify_text"
                    )
