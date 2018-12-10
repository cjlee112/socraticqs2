
from django.core.management.base import BaseCommand

from ct.models import Course, Role, UnitLesson, Unit, Lesson, Response
from ctms.models import Invite
from chat.models import Chat, EnrollUnitCode
from accounts.models import Instructor
from core.common.utils import update_onboarding_step, get_onboarding_percentage
from core.common import onboarding
from django.conf import settings


class Command(BaseCommand):
    help = 'Onboarding preprocessing'

    def handle(self, *args, **options):
        for instructor in Instructor.objects.all():

            try:
                course = Course.objects.get(id=settings.ONBOARDING_INTRODUCTION_COURSE_ID)
            except Course.DoesNotExist:
                print("Onboarding course is not provided")
                return

            chat_exists = Chat.objects.filter(
                user=instructor.user,
                enroll_code__courseUnit__course=course,
                progress__gte=70
            ).exists()
            if chat_exists:
                update_onboarding_step(onboarding.STEP_2, instructor.user_id)

            # if instructor has created create_course

            if Course.objects.filter(addedBy=instructor.user).exists():
                update_onboarding_step(onboarding.STEP_3, instructor.user_id)

            # if instructor has created a create_courselet

            if Unit.objects.filter(addedBy=instructor.user).exists():
                update_onboarding_step(onboarding.STEP_4, instructor.user_id)

            # if instructor has created a create_thread

            if Lesson.objects.filter(addedBy=instructor.user).exists():
                update_onboarding_step(onboarding.STEP_5, instructor.user_id)

            # if he has created invite_somebody
            if Invite.objects.filter(instructor=instructor).exists():
                update_onboarding_step(onboarding.STEP_8, instructor.user_id)

            enroll_unit_code_exists = EnrollUnitCode.objects.filter(
                courseUnit__course__addedBy=instructor.user,
                isPreview=True,
                isLive=False,
                isTest=False
            ).exists()
            if enroll_unit_code_exists:
                update_onboarding_step(onboarding.STEP_6, instructor.user_id)

            print("Instructor {} passed onboarding at {}%".format(
                instructor.user.username, get_onboarding_percentage(instructor.user.id))
            )
