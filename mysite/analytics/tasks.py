import pytz
from pytz.exceptions import UnknownTimeZoneError
from accounts.models import Profile
from mysite import celery_app

import json
import uuid
from io import BytesIO

from django.conf import settings
from django.core.files import File
from django.contrib.auth.models import User
from django.db.models import Q

from ct.models import Response
from .models import CourseReport


@celery_app.task
def report(course_id, user_id):
    report = []
    user = User.objects.filter(id=user_id).first()

    lesson_responses = {}
    last_resps = []

    q = Response.objects.filter(
        Q(kind='orct') | Q(sub_kind='choices'), unitLesson__order__isnull=False, course__id=course_id
    )

    for obj in q:
        ul_resps = lesson_responses.setdefault(obj.unitLesson, {})
        user_resps = ul_resps.setdefault(obj.author, [])
        user_resps.append(obj)

    for _, user_resps in list(lesson_responses.items()):
        for _, respss in list(user_resps.items()):
            if respss:
                last_resps.append(sorted(respss, key=lambda o: o.atime)[0])

    for obj in last_resps:
        _id = obj.id
        author_id = obj.author.id
        author_name = obj.author.get_full_name() or obj.author.username
        lti_user = obj.author.lti_auth.first()
        if lti_user:
            lti_identity = lti_user.user_id
        else:
            lti_identity = None
        if obj.sub_kind == 'choices':
            text = obj.show_my_choices()
        else:
            text = obj.text
        confidence = obj.confidence
        selfeval = obj.selfeval
        status = obj.status
        unitLesson_id = obj.unitLesson.id
        courselet_id = obj.unitLesson.unit.id
        submit_time = obj.atime
        is_trial = obj.is_trial

        try:
            u_tz = obj.author.profile.timezone or settings.TIME_ZONE
        except Profile.DoesNotExist:
            u_tz = settings.TIME_ZONE

        try:
            user_tz = pytz.timezone(u_tz)
        except UnknownTimeZoneError as e:
            user_tz = pytz.timezone(settings.TIME_ZONE)
            print("User has incorrect time zone in Profile. Will use default TZ.")

        localized_ts = submit_time.astimezone(user_tz).strftime("%d-%m-%Y-%H:%M:%SZ%z")

        r = dict(
          id=_id,
          author_id=author_id,
          author_name=author_name,
          lti_identity=lti_identity,
          text=text,
          confidence=confidence,
          selfeval=selfeval,
          status=status,
          unitLesson_id=unitLesson_id,
          courselet_id=courselet_id,
          submitted_time=localized_ts,
          is_trial=is_trial
        )
        report.append(r)
    if report:
        report_dumped_indent = json.dumps(report, indent=4)
        output = BytesIO()
        output.write(report_dumped_indent.encode())
        try:
            file_instance = File(
              file=output,
              name="{}.json".format(uuid.uuid4().hex)
            )
            course_report = CourseReport(
                course_id=course_id,
                response_report=file_instance,
                addedBy=user
            )
            course_report.save()
        finally:
            output.close()
        print('Done')
    else:
        print('Nothing to report')
