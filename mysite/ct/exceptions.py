# coding=utf-8


class CommonDisambiguationError(Exception):
    def __init__(self, options):
        self.options = options

    def __str__(self):
        return "There are more than one articles for that query"
