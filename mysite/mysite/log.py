"""
Logging methods
"""
import logging

from datetime import datetime

LOGGER = logging.getLogger('ct_debug')


def write_exception_to_log(exception):
    message =  exception.message if exception.message else str(exception)
    LOGGER.error("Time [%s] - Exception class [%s] - Exception message [%s]" %
                    (datetime.now(), exception.__class__, message))
