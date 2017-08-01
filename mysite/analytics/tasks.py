from mysite.celery import app

import re
import os
import sys
import json
import uuid
import StringIO
from datetime import datetime
from collections import defaultdict

import unicodecsv as csv
from pandas import DataFrame
from django.conf import settings
from django.core.files import File
from django.contrib.auth.models import User

from ct.models import Response
from .models import CourseReport

@app.task
def report(course_id, user_id):
    report = []
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        user = None

    for obj in Response.objects.filter(
        kind='orct', unitLesson__order__isnull=False, course__id=course_id
    ):
        _id = obj.id
        author_id = obj.author.id
        author_name = obj.author.get_full_name() or obj.author.username
        lti_user = obj.author.lti_auth.first()
        if lti_user:
            lti_identity = lti_user.user_id
        else:
            lti_identity = None
        text = obj.text
        confidence = obj.confidence
        selfeval = obj.selfeval
        status = obj.status
        unitLesson_id = obj.unitLesson.id
        courselet_id = obj.unitLesson.unit.id
        submit_time = obj.atime
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
          submitted_time=str(submit_time.strftime("%d-%m-%Y-%H:%M:%S"))
        )
        report.append(r)
    if report:
        report_dumped_indent = json.dumps(report, indent=4)
        output = StringIO.StringIO()
        output.write(report_dumped_indent)
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
