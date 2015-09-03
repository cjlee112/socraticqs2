import json
from ct.models import *
from django.contrib.auth.models import User
from django.utils import dateparse, timezone
from datetime import datetime
import codecs


def store_errors(q, concept, parentUL, conceptIDdict=None):
    'store error models associated with question'
    errorModels = []
    courseletsMap = q.get('courseletsMapError', ())
    if conceptIDdict is None:
        conceptIDdict = {}
    for i, e in enumerate(q.get('error', ())):
        em = emUL = saveMapping = None
        try:
            mapID = courseletsMap[i]
        except IndexError:
            pass
        else:
            ulID = conceptIDdict.get(mapID, None)
            if ulID is None:
                saveMapping = True
                print 'WARNING: %s not found in conceptIDdict; treating as new error model' % mapID
            else:
                if isinstance(ulID, int): # just add existing EM to this question
                    ul = UnitLesson.objects.get(pk=ulID)
                    emUL = UnitLesson.create_from_lesson(ul.lesson, unit,
                                                        parent=parentUL)
                else: # add new EMLesson to existing EM
                    try:
                        if not ulID.startswith('fork:'):
                            raise ValueError
                        ul = UnitLesson.objects.get(pk=int(ulID[5:]))
                    except ValueError:
                        raise ValueError('bad conceptIDdict ID value %s: should be int or "fork:INT"'
                                        % ulID)
                    em = ul.lesson.concept # link to existing error model
                if not ul.lesson.concept or not ul.lesson.concept.isError:
                    raise ValueError('%s: not a valid error model'
                                    % ul.lesson.title)
        if not emUL: # create new error model lesson
            emLesson = Lesson(title='(rename this)', addedBy=parentUL.addedBy,
                              text=e)
            emUL = emLesson.save_as_error_model(concept, parentUL, em)
            if saveMapping: # allow other questions to fork this EM
                conceptIDdict[mapID] = 'fork:%d' % emUL.pk
        errorModels.append(emUL)
    return errorModels

def get_or_create_user(username, email='unknown'):
    'get user object with specified username, create it if necessary'
    try:
        u = User.objects.get(username=username)
    except User.DoesNotExist:
        u = User.objects.create_user(username, email, None, 
                                 first_name='Student', last_name=username)
        u.save()
    return u

def store_response_errors(r, errorModels, response, genericErrors,
                          genericIndex):
    'store all student errors associated with a response'
    for se in r['errors']:
        error_id = se['error_id']
        if isinstance(error_id, int):
            emUL = errorModels[error_id]
        else: # look up generic error model
            i = genericIndex[error_id]
            emUL = genericErrors[i]
        studentError = StudentError(response=response, atime=response.atime,
                                   errorModel=emUL, author=response.author)
        studentError.save()

def store_response(r, course, parentUL, errorModels, genericErrors,
                   genericIndex, tzinfo=timezone.get_default_timezone()):
    'load response w/ username, confidence, selfeval, errors'
    user = get_or_create_user(r['username'])
    confidence = Response.CONF_CHOICES[r['confidence']][0]
    atime = dateparse.parse_datetime(r['submit_time'])
    atime = timezone.make_aware(atime, tzinfo)
    response = Response(unitLesson=parentUL, lesson=parentUL.lesson,
                        text=r['answer'], course=course, author=user,
                        confidence=confidence, atime=atime)
    if 'selfeval' in r:
        response.selfeval = r['selfeval']
    response.save()
    store_response_errors(r, errorModels, response, genericErrors,
                          genericIndex)
    return response


def add_concept_resource(conceptID, unit, conceptIDdict=()):
    'get concept by courseletsConcept:ID or wikipedia ID, add to unit'
    if conceptID.startswith('courseletsConcept:'):
        ulID = int(conceptID[18:])
    elif conceptID in conceptIDdict:
        ulID = conceptIDdict[conceptID]
    else:
        ulID = None
    if ulID is not None:
        ul = UnitLesson.objects.get(pk=ulID)
        lesson = ul.lesson
        concept = lesson.concept
        if not concept:
            raise ValueError('%s does not link to a concept!' % conceptID)
    else:
        concept, lesson = Concept.get_from_sourceDB(conceptID, unit.addedBy)
    if unit.unitlesson_set.filter(lesson__concept=concept).count() <= 0:
        UnitLesson.create_from_lesson(lesson, unit) # attach as unit resource
    return concept

def store_new_question(q, unit, concept,
                       tzinfo=timezone.get_default_timezone(),
                       kind=Lesson.ORCT_QUESTION):
    'create new lessons for question, answer, and add to this unit'
    lesson = Lesson(title=q['title'], text=q['text'], addedBy=unit.addedBy,
                    kind=kind)
    if 'date_added' in q:
        d = dateparse.parse_date(q['date_added'])
        atime = datetime(d.year, d.month, d.day)
        lesson.atime = timezone.make_aware(atime, tzinfo)
    lesson.save_root(concept)
    unitLesson = UnitLesson.create_from_lesson(lesson, unit, order='APPEND',
                                               addAnswer=True)
    answer = unitLesson._answer.lesson # get auto-created record
    answer.title = q['title'] + ' Answer' # update answer text
    answer.text = q['answer']
    answer.save()
    return unitLesson


def store_question(q, course, unit, genericErrors, genericIndex,
                   conceptIDdict=(), **kwargs):
    'store question linked to concept, error models, answer, responses'
    conceptID = q['tests'][0] # link to first concept
    concept = add_concept_resource(conceptID, unit, conceptIDdict)
    unitLesson = store_new_question(q, unit, concept, **kwargs)
    errorModels = store_errors(q, concept, unitLesson, conceptIDdict)
    for r in q.get('responses', ()):
        store_response(r, course, unitLesson, errorModels, genericErrors,
                       genericIndex)
    print 'saved %s: %d error models, %d responses' \
      % (unitLesson.lesson.title, len(errorModels),
         len(q.get('responses', ())))
    return unitLesson

def index_generic_errors(unit):
    'extract generic error models and construct phrase index'
    genericErrors = unit.get_aborts()
    l = []
    for i, ul in enumerate(genericErrors):
        l.append((i, ul.lesson.title))
    genericIndex = PhraseIndex(l)
    return genericErrors, genericIndex

    
def load_orct_data(infile='orctmerge.json', course=None, unit=None,
                   courseID=None, unitID=None, conceptIDfile=None):
    'load ORCT questions, responses etc into this unit'
    if course is None:
        course = Course.objects.get(pk=courseID)
    if unit is None:
        unit = Unit.objects.get(pk=unitID)
    genericErrors, genericIndex = index_generic_errors(unit)
    orctData = load_json(infile)
    if conceptIDfile:
        conceptIDdict = load_json(conceptIDfile)
    else:
        conceptIDdict = {}
    for q in orctData:
        if q.get('kind', 'SKIP') == 'question':
            store_question(q, course, unit, genericErrors, genericIndex,
                           conceptIDdict)

def load_json(infile):
    with codecs.open(infile, 'r', encoding='utf-8') as ifile:
        data = json.load(ifile)
    return data

class PhraseIndex(object):
    def __init__(self, t, nword=2):
        'construct phrase index for list of entries of the form [(id, text),]'
        self.nword = nword
        d = {}
        self.sizes = {}
        for i, text in t:
            n, l = self.get_phrases(text)
            self.sizes[i] = n # save numbers of phrases
            for j in range(n): # index all phrases in this text
                phrase = tuple(l[j:j + nword])
                try:
                    d[phrase].append(i)
                except KeyError:
                    d[phrase] = [i]
        self.d = d

    def get_phrases(self, text):
        'split into words, handling case < nword gracefully'
        l = text.split()
        if len(l) > self.nword:
            return len(l) - self.nword + 1, l
        else: # handle short phrases gracefully to allow matching
            return 1, l

    def __getitem__(self, text):
        'find entry with highest phrase match fraction'
        n, l = self.get_phrases(text)
        counts = {}
        for j in range(n):
            phrase = tuple(l[j:j + self.nword])
            for i in self.d.get(phrase, ()):
                counts[i] = counts.get(i, 0)  + 1
        if not counts:
            raise KeyError
        l = []
        for i, c in counts.items(): # compute match fractions
            l.append((c / float(self.sizes[i]), i))
        l.sort()
        return l[-1][1] # return id with highest match fraction

