"""
Logging methods
"""
import os
from datetime import datetime

from django.conf import settings

filename = settings.LOG_FILE
full_path = os.path.dirname(__file__) + '/../../logs/'+filename


def write_exception_to_log(exception):
    message =  exception.message if exception.message else str(exception)
    with open(full_path, "a") as log_file:
        log_file.write("Time [%s] - Exception class [%s] - Exception message [%s] \n" %
                       (datetime.now(), exception.__class__, message))
