import re
import os
import sys
import json
from datetime import datetime
from collections import defaultdict

import unicodecsv as csv
from pandas import DataFrame
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ct.models import Response


class Command(BaseCommand):
    help = 'Get report'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('course_id', type=int)

    def handle(self, *args, **options):
        report = []
        for obj in Response.objects.filter(
            kind='orct', unitLesson__order__isnull=False, course__id=options['course_id']
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
            with open(
                'report_{}.json'.format(datetime.now().strftime("%d-%m-%Y-%H-%M")), 'w'
            ) as f:
                f.write(report_dumped_indent)
            cols = defaultdict(list)
            headers = [
                'author_id',
                'author_name',
                'confidence',
                'id',
                'lti_identity',
                'selfeval',
                'status',
                'text',
                'unitLesson_id',
                'courselet_id',
                'submitted_time'
            ]
            for key_name in headers:
                for i in report:
                    cols[key_name].append(i[key_name])
            df = DataFrame(cols)
            df.to_excel(
                'report_{}.xlsx'.format(datetime.now().strftime("%d-%m-%Y-%H-%M")),
                sheet_name='sheet1',
                index=False
            )
            print('Done')
        else:
            print('Nothing to report')
