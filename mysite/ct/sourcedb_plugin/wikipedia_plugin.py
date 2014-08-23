import wikipedia

class LessonDoc(object):
    sourceDB = 'wikipedia'
    def __init__(self, sourceID):
        try:
            self._data = wikipedia.page(sourceID)
        except (wikipedia.exceptions.DisambiguationError,
                wikipedia.exceptions.PageError), e:
            raise KeyError(str(e))
        self.sourceID = sourceID
        self.title = sourceID
        self.description = self._data.summary
        self.url = self._data.url

    @classmethod
    def search(klass, query, max_results=10):
        'return list of [(title, sourceID, url)]'
        return [(s, s, 'http://en.wikipedia.org/wiki/' + '_'.join(s.split()))
                for s in wikipedia.search(query, max_results)]

