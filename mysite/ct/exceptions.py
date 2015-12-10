# coding=utf-8


class SearchDbDisambiguationError(Exception):
    def __init__(self, options):
        self.options = options

    def __unicode__(self):
        return "There are more than ome articles for that query"
