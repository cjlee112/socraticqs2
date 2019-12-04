"""
Django signals for the app.
"""
import logging

from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.sites.models import Site

from .models import Response, UnitLesson
from .ct_util import get_middle_indexes

from core.common.mongo import c_milestone_orct
from core.common.utils import send_email, suspending_receiver

log = logging.getLogger(__name__)


@suspending_receiver(post_save, sender=Response)
def run_courselet_notif_flow(sender, instance, **kwargs):
    # TODO: add check that Response has a text, as an obj can be created before a student submits
    # TODO: exclude self eval submissions other than a response submission (e.g. "just guessing")

    if (instance.kind == Response.ORCT_RESPONSE and not
            (instance.unitLesson.kind == UnitLesson.RESOLVES or
             instance.is_test or instance.is_preview or not instance.unitLesson.order)):
        course = instance.course
        course_id = course.id if course else None
        instructors = course.get_users(role="prof")
        lesson = instance.lesson
        lesson_id = lesson.id if lesson else None
        student = instance.author
        student_id = student.id if student else None
        unit_lesson = instance.unitLesson
        unit_lesson_id = unit_lesson.id if unit_lesson else None  # it's a thread

        # Exclude instructors, e.g. the ones submitting in preview mode
        for instructor in instructors:
            if student_id == instructor.id:
                return

        # Define if it's a milestone question (either first, middle, or last)
        milestone = None
        questions = unit_lesson.unit.all_orct()
        i = [_[0] for _ in questions.values_list('id')].index(unit_lesson_id)
        if i == 0:
            milestone = "first"
        elif i == len(questions) - 1:
            milestone = "last"
        elif i in get_middle_indexes(questions):
            milestone = "middle"  # TODO consider returning a single number

        # If milestone, store the record
        if milestone:
            to_save = {
                "milestone": milestone,
                "lesson_title": lesson.title if lesson else None,
                "lesson_id": lesson_id,
                "unit_lesson_id": unit_lesson_id,
                "course_title": course.title if course else None,
                "course_id": course_id,
                "student_username": student.username if student else None,
                "student_id": student_id,
                # "datetime": datetime.datetime.now()  # TODO: consider changing to UTC (and making it a timestamp)
            }
            # Do not store if such `student_id`-`lesson_id` row is already present
            milestone_orct_answers_cursor = c_milestone_orct(use_secondary=False).find({
                "milestone": milestone,
                "lesson_id": lesson_id
            })
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
                    context_data = {
                        "milestone": milestone,
                        "students_number": milestone_orct_answers_number,
                        "course_title": course.title if course else None,
                        "lesson_title": lesson.title if lesson else None,
                        "current_site": Site.objects.get_current(),
                        "course_id": course_id,
                        "unit_lesson_id": unit_lesson_id,
                        "courselet_pk": unit_lesson.unit.id if unit_lesson.unit else None
                    }  # pragma: no cover
                    log.info("""Courselet notification with data:
                        Course title - {course_title},
                        Lesson title - {lesson_title},
                        Students number - {students_number},
                        Unit lesson id - {unit_lesson_id},
                        Course id - {course_id},
                        Milestone - {milestone}
                        """.format(**context_data))  # pragma: no cover
                    send_email(
                        context_data=context_data,
                        from_email=settings.EMAIL_FROM,
                        to_email=[instructor.email for instructor in instructors],
                        template_subject="ct/email/milestone_ortc_notify_subject",
                        template_text="ct/email/milestone_ortc_notify_text"
                    )
