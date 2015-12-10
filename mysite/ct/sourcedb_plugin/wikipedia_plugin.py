import wikipedia

class LessonDoc(object):
    sourceDB = 'wikipedia'

    def __init__(self, sourceID):
        try:
            self._data = wikipedia.page(sourceID)
            self.description = self._data.summary
            self.url = self._data.url
            self.sourceID = sourceID
            self.title = sourceID
        except wikipedia.exceptions.PageError as e:
            raise KeyError(str(e))
        except wikipedia.exceptions.DisambiguationError as e:
            print e
            self.list_of_search = [item for item in getattr(e, 'options')]


    @classmethod
    def search(klass, query, max_results=10):
        'return list of [(title, sourceID, url)]'
        return [(s, s, 'http://en.wikipedia.org/wiki/' + '_'.join(s.split()))
                for s in wikipedia.search(query, max_results)]

