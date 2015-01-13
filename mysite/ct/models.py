from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.db.models import Q, Count, Max
import glob
import json


def import_plugin(path):
    if path.endswith('.py'):
        path = path[:-3]
    modname = '.'.join(path.split('/'))
    try:
        mod = __import__(modname, globals(), locals(), ['LessonDoc'])
    except ImportError:
        raise ImportError('plugin %s not found, or missing LessonDoc class!' % modname)
    return mod.LessonDoc

def import_sourcedb_plugins(pattern='sourcedb_plugin/[a-z]*.py'):
    i = __file__.rfind('/')
    if i >= 0:
        pattern = __file__[:i + 1] + pattern
    d = {}
    for path in glob.glob(pattern):
        klass = import_plugin(path[i + 1:])
        d[klass.sourceDB] = klass
    return d



########################################################
# Concept ID and graph -- not version controlled

class Concept(models.Model):
    title = models.CharField(max_length=100)
    addedBy = models.ForeignKey(User)
    approvedBy = models.ForeignKey(User, null=True,
                                   related_name='approvedConcepts')
    isError = models.BooleanField(default=False)
    isAbort = models.BooleanField(default=False)
    isFail = models.BooleanField(default=False)
    isPuzzled = models.BooleanField(default=False)
    alwaysAsk = models.BooleanField(default=False)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    def __unicode__(self):
        return self.title
    @classmethod
    def get_from_sourceDB(klass, sourceID, user, sourceDB='wikipedia'):
        lesson = Lesson.get_from_sourceDB(sourceID, user, sourceDB)
        if lesson.concept:
            return lesson.concept, lesson
        concept = klass(title=lesson.title, addedBy=user)
        concept.save()
        lesson.concept = concept
        lesson.save()
        return concept, lesson
    @classmethod
    def search_text(klass, s):
        'search Concept title'
        return klass.objects.filter(title__icontains=s).distinct()
    @classmethod
    def new_concept(klass, title, text, unit, user, isError=False):
        'add a new concept with associated Lesson, UnitLesson'
        lesson = Lesson(title=title, text=text, addedBy=user)
        concept = klass(title=title, addedBy=user)
        if isError:
            concept.isError = True
            lesson.kind = lesson.ERROR_MODEL
        concept.save()
        lesson.concept = concept
        lesson.save_root()
        UnitLesson.create_from_lesson(lesson, unit)
        return concept
    def create_error_model(self, addedBy, **kwargs):
        'create a new error model for this concept'
        em = self.__class__(isError=True, addedBy=addedBy, **kwargs)
        em.save()
        em.relatedTo.create(toConcept=self, addedBy=addedBy,
                            relationship=ConceptGraph.MISUNDERSTANDS)
        return em
    def copy_error_models(self, parent):
        'add to parent one UnitLesson for each error RE: this concept'
        l = []
        for cg in self.relatedFrom \
                    .filter(relationship=ConceptGraph.MISUNDERSTANDS):
            try: # get one lesson representing this error model
                lesson = Lesson.objects.filter(concept=cg.fromConcept)[0]
            except IndexError:
                pass
            else:
                l.append(UnitLesson.create_from_lesson(lesson, parent.unit,
                            kind=UnitLesson.MISUNDERSTANDS, parent=parent))
        return l
    def get_url(self, basePath, forceDefault=False, subpath=None,
                isTeach=True):
        objID = UnitLesson.objects.filter(lesson__concept=self)[0].pk
        if self.isError: # default settings
            head = 'errors'
            tail = ''
        else:
            head = 'concepts'
            tail = 'lessons/'
        if subpath: # apply non-default subpath
            tail = subpath + '/'
        elif subpath == '':
            tail = ''
        return '%s%s/%d/%s' % (basePath, head, objID, tail)
    def get_error_tests(self, **kwargs):
        'get questions that test this error model'
        return distinct_subset(UnitLesson.objects
            .filter(kind=UnitLesson.COMPONENT,
                    unitlesson__kind=UnitLesson.MISUNDERSTANDS,
                    unitlesson__lesson__concept=self, **kwargs))
    def get_conceptlinks(self, unit):
        'get list of conceptLinks deduped on (treeID, relationship)'
        d = {}
        for cl in ConceptLink.objects.filter(concept=self):
            for ul in UnitLesson.objects.filter(lesson=cl.lesson):
                t = (ul.treeID, cl.relationship)
                if t not in d or ul.unit == unit:
                    cl.unitLesson = ul # add attribute to keep this info
                    d[t] = cl
        l = d.values()
        l.sort(lambda x,y:cmp(x.relationship, y.relationship))
        return l
    def __unicode__(self):
        return self.title
            

class ConceptGraph(models.Model):
    DEPENDS = 'depends'
    MOTIVATES = 'motiv'
    MISUNDERSTANDS = 'errmod'
    VIOLATES = 'violates'
    CONTAINS = 'contains'
    TESTS = 'tests'
    CONFLICTS = 'conflicts'
    PROVES = 'proves'
    DISPROVES = 'dispro'
    REL_CHOICES = (
        (DEPENDS, 'Depends on'),
        (MOTIVATES, 'Motivates'),
        (MISUNDERSTANDS, 'misunderstands'),
        (VIOLATES, 'Violates'),
        (CONTAINS, 'Contains'),
        (TESTS, 'Tests'),
        (CONFLICTS, 'Conflicts with'),
        (PROVES, 'Proves'),
        (DISPROVES, 'Disproves'),
    )
    fromConcept = models.ForeignKey(Concept, related_name='relatedTo')
    toConcept = models.ForeignKey(Concept, related_name='relatedFrom')
    relationship = models.CharField(max_length=10, choices=REL_CHOICES,
                                    default=DEPENDS)
    addedBy = models.ForeignKey(User)
    approvedBy = models.ForeignKey(User, null=True,
                                   related_name='approvedConceptEdges')
    atime = models.DateTimeField('time submitted', default=timezone.now)

########################################################
# version-controlled teaching material

PUBLIC_ACCESS = 'public'
INSTRUCTOR_ENROLLED = 'enroll'
FINAL_EXAM_ONLY = 'exam'
PRIVATE_ACCESS = 'private'
ACCESS_CHOICES = (
    (PUBLIC_ACCESS, 'Public'),
    (INSTRUCTOR_ENROLLED, 'By instructors only'),
    (FINAL_EXAM_ONLY, 'Protected exam only'),
    (PRIVATE_ACCESS, 'By author only'),
)


class Lesson(models.Model):
    BASE_EXPLANATION = 'base' # focused on one concept, as intro for ORCT
    EXPLANATION = 'explanation' # conventional textbook or lecture explanation

    ORCT_QUESTION = 'orct'
    CONCEPT_INVENTORY_QUESTION = 'mcct'
    EXERCISE = 'exercise'
    PROJECT = 'project'
    PRACTICE_EXAM = 'practice'
    
    ANSWER = 'answer'
    ERROR_MODEL = 'errmod'

    DATA = 'data'
    CASESTUDY = 'case'
    ENCYCLOPEDIA = 'e-pedia'
    FAQ_QUESTION = 'faq'
    FORUM = 'forum'
    # MEDIA CHOICES
    READING = 'reading'
    LECTURE = 'lecture'
    SLIDES = 'slides'
    VIDEO = 'video'
    AUDIO = 'audio'
    IMAGE = 'image'
    DATABASE = 'db'
    SOFTWARE = 'software'
    KIND_CHOICES = (
        (BASE_EXPLANATION, 'brief definition and explanation'),
        (EXPLANATION, 'long explanation'),
        (ORCT_QUESTION, 'Open Response Concept Test question'),
        (CONCEPT_INVENTORY_QUESTION, 'Concept Inventory Test question'),
        (EXERCISE, EXERCISE),
        (PROJECT, PROJECT),
        (PRACTICE_EXAM, 'practice exam question'),
        (ANSWER, ANSWER),
        (ERROR_MODEL, 'error model'),
        (DATA, DATA),
        (CASESTUDY, 'Case Study'),
        (ENCYCLOPEDIA, 'Encyclopedia'),
        (FAQ_QUESTION, 'frequently asked question'),
        (FORUM, FORUM),
    )
    MEDIA_CHOICES = (
        (READING, READING),
        (LECTURE, LECTURE),
        (SLIDES, SLIDES),
        (VIDEO, VIDEO),
        (AUDIO, AUDIO),
        (IMAGE, IMAGE),
        (DATABASE, 'Database'),
        (SOFTWARE, SOFTWARE),
    )
    _sourceDBdict = import_sourcedb_plugins()
    title = models.CharField(max_length=100)
    text = models.TextField(null=True)
    data = models.TextField(null=True) # JSON DATA
    url = models.CharField(max_length=256, null=True)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES,
                            default=BASE_EXPLANATION)
    medium = models.CharField(max_length=10, choices=MEDIA_CHOICES,
                              default=READING)
    access = models.CharField(max_length=10, choices=ACCESS_CHOICES,
                              default=PUBLIC_ACCESS)
    sourceDB = models.CharField(max_length=32, null=True)
    sourceID = models.CharField(max_length=100, null=True)
    addedBy = models.ForeignKey(User)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    concept = models.ForeignKey(Concept, null=True) # concept definition
    treeID = models.IntegerField(null=True) # VCS METADATA
    parent = models.ForeignKey('Lesson', null=True,
                               related_name='children')
    mergeParent = models.ForeignKey('Lesson', null=True,
                                    related_name='mergeChildren')
    changeLog = models.TextField(null=True)
    commitTime = models.DateTimeField('time committed', null=True)

    @classmethod
    def get_from_sourceDB(klass, sourceID, user, sourceDB='wikipedia'):
        try:
            return klass.objects.get(sourceDB=sourceDB, sourceID=sourceID)
        except klass.DoesNotExist:
            pass
        dataClass = klass._sourceDBdict[sourceDB]
        data = dataClass(sourceID)
        try: # attribute authorship to the sourceDB
            user = User.objects.get(username=sourceDB)
        except User.DoesNotExist:
            pass
        lesson = klass(title=data.title, url=data.url, sourceDB=sourceDB,
                       sourceID=sourceID, addedBy=user, text=data.description,
                       kind=klass.EXPLANATION)
        lesson.save_root()
        lesson._sourceDBdata = data
        return lesson

    @classmethod
    def search_sourceDB(klass, query, sourceDB='wikipedia', **kwargs):
        dataClass = klass._sourceDBdict[sourceDB]
        return dataClass.search(query, **kwargs)

    ## @classmethod
    ## def create_from_concept(klass, concept, **kwargs):
    ##     'create lesson for initial concept definition'
    ##     if concept.isError:
    ##         kwargs['kind'] = klass.ERROR_MODEL
    ##     lesson = klass(title=concept.title, text=concept.description,
    ##                    addedBy=concept.addedBy, concept=concept, **kwargs)
    ##     lesson.save_root()
    ##     return lesson
    def save_root(self, concept=None, relationship=None):
        'create root commit by initializing treeID'
        if self.treeID is None: # no tree ID, so save as root commit
            self.save()
            self.treeID = self.pk
        self.save()
        if concept:
            if relationship is None:
                relationship = DEFAULT_RELATION_MAP[self.kind]
            self.conceptlink_set.create(concept=concept,
                        addedBy=self.addedBy, relationship=relationship)
    def __unicode__(self):
        return self.title
    ## def get_url(self):
    ##     if self.sourceDB:
    ##         return self.url
    ##     else:
    ##         return reverse('ct:lesson', args=(self.id,))

def distinct_subset(inlist, distinct_func=lambda x:x.treeID):
    'eliminate duplicate treeIDs from the input list'
    s = set()
    outlist = []
    for o in inlist:
        k = distinct_func(o)
        if k not in s:
            s.add(k)
            outlist.append(o)
    return outlist
            
    
class ConceptLink(models.Model):
    DEFINES = 'defines'
    TESTS = 'tests'
    RESOLVES = 'resol'
    DERIVES = 'derives'
    PROVES = 'proves'
    ASSUMES = 'assumes'
    MOTIVATES = 'motiv'
    ILLUSTRATES = 'illust'
    INTRODUCES = 'intro'
    COMMENTS = 'comment'
    WARNS = 'warns'
    REL_CHOICES = (
        (DEFINES, 'Defines'),
        (TESTS, 'Tests understanding of'),
        (RESOLVES, 'Helps students resolve'),
        (DERIVES, 'Derives'),
        (PROVES, 'Proves'),
        (ASSUMES, 'Assumes'),
        (MOTIVATES, 'Motivates'),
        (ILLUSTRATES, 'Illustrates'),
        (INTRODUCES, 'Introduces'),
        (COMMENTS, 'Comments on'),
        (WARNS, 'Warns about'),
    )
    concept = models.ForeignKey(Concept)
    lesson = models.ForeignKey(Lesson)
    relationship = models.CharField(max_length=10, choices=REL_CHOICES,
                                    default=DEFINES)
    addedBy = models.ForeignKey(User)
    atime = models.DateTimeField('time submitted', default=timezone.now)

DEFAULT_RELATION_MAP = {
    Lesson.BASE_EXPLANATION:ConceptLink.DEFINES,
    Lesson.EXPLANATION:ConceptLink.DEFINES,
    Lesson.ORCT_QUESTION:ConceptLink.TESTS,
    Lesson.CONCEPT_INVENTORY_QUESTION:ConceptLink.TESTS,
    Lesson.EXERCISE:ConceptLink.TESTS,
    Lesson.PROJECT:ConceptLink.TESTS,
    Lesson.PRACTICE_EXAM:ConceptLink.TESTS,
    
    Lesson.ANSWER:ConceptLink.ILLUSTRATES,
    Lesson.ERROR_MODEL:ConceptLink.DEFINES,

    Lesson.DATA:ConceptLink.ILLUSTRATES,
    Lesson.CASESTUDY:ConceptLink.ILLUSTRATES,
    Lesson.ENCYCLOPEDIA:ConceptLink.DEFINES,
    Lesson.FAQ_QUESTION:ConceptLink.COMMENTS,
    Lesson.FORUM:ConceptLink.COMMENTS,
}

    
class StudyList(models.Model):
    'list of materials of interest to each user'
    lesson = models.ForeignKey(Lesson)
    user = models.ForeignKey(User)
    def __unicode__(self):
        return self.lesson.title

############################################################
# unit lesson repo and graph

IS_ERROR = 0
IS_CONCEPT = 1
IS_LESSON = 2

class UnitLesson(models.Model):
    'pointer to a Lesson as part of a Unit branch'
    _headURL = 'lessons'
    _tasksPath = {IS_ERROR:'faq', IS_CONCEPT:'faq', IS_LESSON:'tasks'}
    COMPONENT = 'part'
    ANSWERS = 'answers'
    MISUNDERSTANDS = 'errmod'
    RESOLVES = 'resol'
    PRETEST_POSTTEST = 'pretest'
    SUBUNIT = 'subunit'
    KIND_CHOICES = (
        (COMPONENT, 'Included in this courselet'),
        (ANSWERS, 'Answer for a question'),
        (MISUNDERSTANDS, 'Common error for a question'),
        (RESOLVES, 'Resolution for an error'),
        (PRETEST_POSTTEST, 'Pre-test/Post-test for this courselet'),
        (SUBUNIT, 'Container for this courselet'),
    )
    unit = models.ForeignKey('Unit')
    kind = models.CharField(max_length=10, choices=KIND_CHOICES,
                            default=COMPONENT)
    lesson = models.ForeignKey(Lesson, null=True)
    parent = models.ForeignKey('UnitLesson', null=True)
    order = models.IntegerField(null=True)
    atime = models.DateTimeField('time added', default=timezone.now)
    addedBy = models.ForeignKey(User)
    treeID = models.IntegerField() # VCS METADATA
    branch = models.CharField(max_length=32, default='master')
    ## @classmethod
    ## def create_from_concept(klass, concept, unit=None, ulArgs={}, **kwargs):
    ##     'create lesson for initial concept definition'
    ##     lesson = Lesson.create_from_concept(concept, **kwargs)
    ##     return klass.create_from_lesson(lesson, unit, **ulArgs)
    @classmethod
    def create_from_lesson(klass, lesson, unit, order=None, kind=None,
                           addAnswer=False, **kwargs):
        if not kind:
            kindMap = {Lesson.ANSWER:klass.ANSWERS,
                    Lesson.ERROR_MODEL:klass.MISUNDERSTANDS}
            kind = kindMap.get(lesson.kind, klass.COMPONENT)
        if order == 'APPEND':
            order = unit.next_order()
        ul = klass(unit=unit, lesson=lesson, addedBy=lesson.addedBy,
                   treeID=lesson.treeID, order=order, kind=kind, **kwargs)
        ul.save()
        if addAnswer and lesson.kind == Lesson.ORCT_QUESTION:
            answer = Lesson(title='Answer', text='write an answer',
                            addedBy=lesson.addedBy, kind=Lesson.ANSWER)
            answer.save_root()
            ul._answer = klass.create_from_lesson(answer, unit,
                        kind=klass.ANSWERS, parent=ul)
        return ul
    @classmethod
    def search_text(klass, s, searchType=IS_LESSON, dedupe=True,
                    excludeArgs={}, **kwargs):
        'search lessons, concepts or errors for title and text'
        if searchType == 'lesson': # exclude questions
            kwargs['kind'] = klass.COMPONENT
            excludeArgs = excludeArgs.copy()
            excludeArgs['lesson__kind'] = Lesson.ORCT_QUESTION
        elif searchType == 'question':
            kwargs['kind'] = klass.COMPONENT
            kwargs['lesson__kind'] = Lesson.ORCT_QUESTION
        elif searchType == IS_LESSON: # anything but answer, error etc.
            kwargs['kind'] = klass.COMPONENT
        elif searchType == IS_ERROR:
            kwargs['lesson__concept__isnull'] = False
            kwargs['kind'] = klass.MISUNDERSTANDS
        else: # search for regular concepts (not an error)
            kwargs['lesson__concept__isnull'] = False
            kwargs['lesson__concept__isError'] = False
        out = klass.objects.filter((Q(lesson__title__icontains=s) |
                                    Q(lesson__text__icontains=s)) &
                                   Q(**kwargs)).distinct()
        if excludeArgs:
            out = out.exclude(**excludeArgs)
        if dedupe:
            out = distinct_subset(out)
        return out
    def get_answers(self):
        'get query set with answer(s) if any'
        return self.unitlesson_set.filter(kind=self.ANSWERS)
    def get_errors(self):
        'get query set with errors if any'
        return self.unitlesson_set.filter(kind=self.MISUNDERSTANDS)
    def get_linked_concepts(self):
        'get all concept links (including errors) to this lesson'
        return self.lesson.conceptlink_set.all()
    def get_concepts(self):
        'get all concepts (not errors) linked to this lesson'
        return Concept.objects.filter(conceptlink__lesson=self.lesson,
                                      isError=False)
    def get_em_resolutions(self):
        'get deduped list of resolution UL for this error UL'
        em = self.lesson.concept
        query = Q(kind=self.RESOLVES,
                  lesson__conceptlink__relationship=ConceptLink.RESOLVES,
                  lesson__conceptlink__concept=em)
        return em, distinct_subset(UnitLesson.objects.filter(query))
    def get_new_inquiries(self):
        return self.response_set.filter(kind=Response.STUDENT_QUESTION,
                                        needsEval=True)
    def get_alternative_defs(self, **kwargs):
        return distinct_subset(self.__class__.objects
            .filter(lesson__concept=self.lesson.concept)
            .exclude(treeID=self.treeID))
    def get_next_lesson(self):
        return self.unit.unitlesson_set.get(order=self.order + 1)
    def copy(self, unit, addedBy, parent=None, order=None, **kwargs):
        'copy self and children to new unit'
        if order == 'APPEND':
            order = unit.next_order()
        ul = self.__class__(lesson=self.lesson, addedBy=addedBy, unit=unit,
                            kind=self.kind, treeID=self.treeID,
                            parent=parent, order=order, **kwargs)
        ul.save()
        for child in self.unitlesson_set.all(): # copy children
            child.copy(unit, addedBy, parent=ul, **kwargs)
        return ul
    def get_url(self, basePath, forceDefault=False, subpath=None,
                isTeach=True):
        'get URL path for this UL'
        pathDict = {IS_ERROR:('errors', ''),
                    IS_CONCEPT:('concepts', 'lessons/'),
                    IS_LESSON:('lessons', ''),}
        if forceDefault:
            head, tail = pathDict[IS_LESSON]
        else:
            head, tail = pathDict[self.get_type()]
        if subpath: # apply non-default subpath
            tail = subpath + '/'
        elif subpath == '':
            tail = ''
        return '%s%s/%d/%s' % (basePath, head, self.pk, tail)
    def get_type(self):
        'return classification as error model, concept, or regular lesson'
        if self.lesson.concept:
            if self.kind == self.MISUNDERSTANDS:
                return IS_ERROR
            else:
                return IS_CONCEPT
        return IS_LESSON

def reorder_exercise(self, old=0, new=0, l=()):
    'renumber exercises to move an exercise from old -> new position'
    if not l:
        l = self.get_exercises()
    if not l: # no lessons, so nothing to do
        return l
    ex = l[old] # select desired exercise by old position
    l = l[:old] + l[old + 1:] # exclude this exercise
    l = l[:new] + [ex] + l[new:] # insert ex in new position
    for i, ex in enumerate(l):
        if i != ex.order: # order changed, have to update
            ex.order = i
            ex.save()
    return l # hand back the reordered list

    
class Unit(models.Model):
    'a container of exercises performed together'
    COURSELET = 'unit'
    LIVE_SESSION = 'live'
    RESOLUTION = 'resol'
    KIND_CHOICES = (
        (COURSELET, 'Courselet'),
        (LIVE_SESSION, 'Live session'),
        (RESOLUTION, 'Resolutions for an error model'),
    )
    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES,
                            default=COURSELET)
    atime = models.DateTimeField('time created', default=timezone.now)
    addedBy = models.ForeignKey(User)
    def next_order(self):
        'get next order value for appending new UnitLesson.order'
        n = self.unitlesson_set.all().aggregate(n=Max('order'))['n']
        if n is None:
            return 0
        else:
            return n + 1
    def no_lessons(self):
        return not self.unitlesson_set.filter(order__isnull=False).count()
    def no_orct(self):
        return not self.unitlesson_set.filter(order__isnull=False,
                        lesson__kind=Lesson.ORCT_QUESTION).count()
    def create_lesson(self, title, text, author=None, **kwargs):
        if author is None:
            author = self.addedBy
        lesson = Lesson(title=title, text=text, addedBy=author, **kwargs)
        lesson.save()
        n = self.unitlesson_set.filter(order__isnull=False).count()
        ul = UnitLesson(unit=self, lesson=lesson, addedBy=author,
                        treeID=lesson.pk, order=n)
        ul.save()
        lesson.treeID = lesson.pk
        lesson.save()
        return lesson
    def get_main_concepts(self):
        'get dict of concepts linked to main lesson sequence of this unit'
        d = {}
        for ul in self.unitlesson_set.filter(lesson__concept__isnull=False,
                kind=UnitLesson.COMPONENT, order__isnull=False):
            cl = ConceptLink(lesson=ul.lesson, concept=ul.lesson.concept)
            cl.unitLesson = ul
            d[cl.concept] = [cl]
        for cld in ConceptLink.objects.filter(lesson__unitlesson__unit=self,
            lesson__unitlesson__kind=UnitLesson.COMPONENT,
            lesson__unitlesson__order__isnull=False) \
            .values('concept', 'relationship', 'lesson__unitlesson'):
            concept = Concept.objects.get(pk=cld['concept'])
            ul = UnitLesson.objects.get(pk=cld['lesson__unitlesson'])
            cl = ConceptLink(concept=concept,
                             relationship=cld['relationship'])
            cl.unitLesson = ul
            d.setdefault(cl.concept, []).append(cl)
        return d
    def get_exercises(self):
        'ordered list of lessons for this courselet'
        return  list(self.unitlesson_set.filter(order__isnull=False)
                     .order_by('order'))
    reorder_exercise = reorder_exercise
    def get_aborts(self):
        'get query set with errors + generic ABORT, FAIL errors'
        aborts = list(self.unitlesson_set
            .filter(kind=UnitLesson.MISUNDERSTANDS, parent__isnull=True))
        if not aborts: # need to add ABORTs etc. to this unit
            aborts = []
            for errorLesson in distinct_subset(Lesson.objects
                .filter(kind=Lesson.ERROR_MODEL, concept__alwaysAsk=True)):
                em = self.unitlesson_set.create(lesson=errorLesson,
                        kind=UnitLesson.MISUNDERSTANDS,
                        addedBy=errorLesson.addedBy,
                        treeID=errorLesson.treeID)
                aborts.append(em)
        return aborts
    def get_new_inquiry_uls(self, **kwargs):
        return distinct_subset(self.unitlesson_set
            .filter(response__kind=Response.STUDENT_QUESTION,
                    response__needsEval=True, **kwargs))
    def get_errorless_uls(self, **kwargs):
        return distinct_subset(self.unitlesson_set
            .filter(lesson__kind=Lesson.ORCT_QUESTION,  **kwargs)
            .exclude(unitlesson__kind=UnitLesson.MISUNDERSTANDS))
    def get_resoless_uls(self, **kwargs):
        return distinct_subset(self.unitlesson_set
            .filter(Q(unitlesson__kind=UnitLesson.MISUNDERSTANDS, **kwargs)
            & ~Q(unitlesson__lesson__concept__conceptlink__relationship=
                 ConceptLink.RESOLVES)))
    def get_unanswered_uls(self, user=None, **kwargs):
        if user:
            kwargs['response__author'] = user
        return distinct_subset(self.unitlesson_set
          .filter(lesson__kind=Lesson.ORCT_QUESTION)
          .exclude(response__kind=Response.ORCT_RESPONSE, **kwargs))
    def get_selfeval_uls(self, user=None, **kwargs):
        if user:
            kwargs['response__author'] = user
        else: # ensure it finds Response
            kwargs['response__isnull'] = False
        return distinct_subset(self.unitlesson_set
            .filter(response__selfeval__isnull=True,
                    response__kind=Response.ORCT_RESPONSE, **kwargs))
    def get_serrorless_uls(self, user=None, **kwargs):
        if user:
            kwargs['response__author'] = user
        return distinct_subset(self.unitlesson_set
            .filter((Q(response__selfeval=Response.DIFFERENT) |
                     Q(response__status=NEED_HELP_STATUS)) &
                    Q(response__studenterror__isnull=True, **kwargs)))
    def get_unresolved_uls(self, user=None, **kwargs):
        'get ORCT with errors not yet DONE_STATUS'
        if user:
            kwargs['response__author'] = user
        return distinct_subset(self.unitlesson_set
            .filter(response__studenterror__status__in=
                    [NEED_HELP_STATUS, NEED_REVIEW_STATUS], **kwargs))
    def __unicode__(self):
        return self.title

    

############################################################
# student response and error data

def fmt_count(c, n):
    return '%.0f%% (%d)' % (c * 100. / n, c)

NEED_HELP_STATUS = 'help'
NEED_REVIEW_STATUS = 'review'
DONE_STATUS = 'done'
STATUS_CHOICES = (
    (NEED_HELP_STATUS, 'Still confused, need help'),
    (NEED_REVIEW_STATUS, 'OK, but need further review and practice'),
    (DONE_STATUS, 'Solidly'),
)

        
class Response(models.Model):
    'answer entered by a student in response to a question'
    ORCT_RESPONSE = 'orct'
    STUDENT_QUESTION = 'sq'
    COMMENT = 'comment'
    KIND_CHOICES = (
        (ORCT_RESPONSE, 'ORCT response'),
        (STUDENT_QUESTION, 'Question about a lesson'),
        (COMMENT, 'Reply comment'),
    )
    CORRECT = 'correct'
    CLOSE = 'close'
    DIFFERENT = 'different'
    EVAL_CHOICES = (
        (DIFFERENT, 'Different'),
        (CLOSE, 'Close'),
        (CORRECT, 'Essentially the same'),
    )
    GUESS = 'guess' # chosen for sort order g < n < s
    UNSURE = 'notsure'
    SURE = 'sure'
    CONF_CHOICES = (
        (GUESS, 'Just guessing'), 
        (UNSURE, 'Not quite sure'),
        (SURE, 'Pretty sure'),
    )
    SELFEVAL_STEP = 'assess'
    CLASSIFY_STEP = 'errors'
    lesson = models.ForeignKey(Lesson) # exact version this applies to
    unitLesson = models.ForeignKey(UnitLesson)
    course = models.ForeignKey('Course')
    kind = models.CharField(max_length=10, choices=KIND_CHOICES,
                            default=ORCT_RESPONSE)
    text = models.TextField()
    confidence = models.CharField(max_length=10, choices=CONF_CHOICES, 
                                  blank=False, null=False)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    selfeval = models.CharField(max_length=10, choices=EVAL_CHOICES, 
                                blank=False, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, 
                              blank=False, null=True)
    author = models.ForeignKey(User)
    needsEval = models.BooleanField(default=False)
    parent = models.ForeignKey('Response', null=True) # reply-to
    def __unicode__(self):
        return 'answer by ' + self.author.username
    @classmethod
    def get_counts(klass, query, fmt_count=fmt_count):
        'generate display tables for Response data'
        querySet = klass.objects.filter(query)
        statusDict = {}
        for d in querySet.values('status').annotate(dcount=Count('status')):
            statusDict[d['status']] = d['dcount']
        n = querySet.count()
        if not n: # prevent DivideByZero
            return (), (), 0
        statusTable = [statusDict.get(k, 0) for k,_ in STATUS_CHOICES]
        nStatus = sum(statusTable)
        if nStatus > 0: # construct table to display
            statusTable.append(n - nStatus)
            statusTable = [fmt_count(i, n) for i in statusTable]
        else: # no data
            statusTable = ()
        evalDict = {}
        for d in querySet.values('confidence', 'selfeval') \
          .annotate(dcount=Count('confidence')):
            evalDict[d['confidence'],d['selfeval']] = d['dcount']
        l = []
        for conf,label in klass.CONF_CHOICES:
            l.append((label, [fmt_count(evalDict.get((conf,selfeval), 0), n)
                              for selfeval,_ in klass.EVAL_CHOICES]))
        return statusTable, l, n
    @classmethod
    def get_novel_errors(klass, unitLesson=None, query=None,
                         selfeval=DIFFERENT, **kwargs):
        'get wrong responses with no StudentError classification'
        if not query:
            if not unitLesson:
                raise ValueError('no query and no unitLesson?!?')
            query = Q(unitLesson=unitLesson)
        return klass.objects.filter(query &
                    Q(selfeval=selfeval, studenterror__isnull=True, **kwargs))
    def get_url(self, basePath, forceDefault=False, subpath=None,
                isTeach=True):
        'URL for this response'
        if subpath:
            tail = subpath + '/'
        else:
            tail = ''
        return '%slessons/%d/responses/%d/%s' % (basePath, self.unitLesson_id,
                                                 self.pk, tail)
    def get_next_step(self):
        'indicate what task student should do next'
        if not self.selfeval:
            return self.SELFEVAL_STEP, 'self-assess your answer'
        if self.selfeval == self.DIFFERENT or self.status == NEED_HELP_STATUS:
            if self.studenterror_set.count() == 0:
                return self.CLASSIFY_STEP, 'classify your error(s)'

        

class StudentError(models.Model):
    'identification of a specific error model made by a student'
    response = models.ForeignKey(Response)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    errorModel = models.ForeignKey(UnitLesson)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, 
                              blank=False, null=True)
    author = models.ForeignKey(User)
    def __unicode__(self):
        return 'eval by ' + self.author.username
    @classmethod
    def get_counts(klass, query, n, fmt_count=fmt_count):
        'generate display table for StudentError data'
        querySet = klass.objects.filter(query)
        l = []
        for d in querySet.values('errorModel') \
          .annotate(c=Count('errorModel')):
            l.append((UnitLesson.objects.get(pk=d['errorModel']), d['c']))
        l.sort(lambda x,y:cmp(x[1], y[1]), reverse=True)
        return [(t[0],fmt_count(t[1], n)) for t in l]
    @classmethod
    def get_ul_errors(klass, ul, **kwargs):
        'get StudentErrors for a specific question'
        return klass.objects.filter(response__unitLesson=ul, **kwargs)

def errormodel_table(target, n, fmt='%d (%.0f%%)', includeAll=False, attr=''):
    if n == 0: # prevent div by zero error
        n = 1
    kwargs = {'kind':Lesson.MISUNDERSTANDS, 'parent':target}
    l = []
    for em in UnitLesson.objects.filter(**kwargs):
        kwargs = {'errorModel':em}
        nse = StudentError.objects.filter(**kwargs).count()
        if nse > 0 or includeAll:
            l.append((em, nse))
    l.sort(lambda x,y:cmp(x[1], y[1]), reverse=True)
    fmt_count = lambda c: fmt % (c, c * 100. / n)
    return [(t[0],fmt_count(t[1])) for t in l]

class InquiryCount(models.Model):
    'record users who have the same question'
    response = models.ForeignKey(Response)
    addedBy = models.ForeignKey(User)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    
class Liked(models.Model):
    'record users who found UnitLesson showed them something they were missing'
    unitLesson = models.ForeignKey(UnitLesson)
    addedBy = models.ForeignKey(User)
    atime = models.DateTimeField('time submitted', default=timezone.now)

class FAQ(models.Model):
    'link a student inquiry to a follow-up lesson'
    response = models.ForeignKey(Response)
    unitLesson = models.ForeignKey(UnitLesson)
    addedBy = models.ForeignKey(User)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    

#######################################
# Course and membership info

class Course(models.Model):
    'top-level (enrollment) container'
    ACCESS_CHOICES = (
        (PUBLIC_ACCESS, 'Public'),
        (INSTRUCTOR_ENROLLED, 'By instructors only'),
        (PRIVATE_ACCESS, 'By author only'),
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    access = models.CharField(max_length=10, choices=ACCESS_CHOICES, 
                              default=PUBLIC_ACCESS)
    enrollCode = models.CharField(max_length=64, null=True)
    lockout = models.CharField(max_length=200, null=True)
    addedBy = models.ForeignKey(User)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    def create_unit(self, title, author=None):
        if author is None:
            author = self.addedBy
        unit = Unit(title=title, addedBy=author)
        unit.save()
        cu = CourseUnit(unit=unit, course=self, addedBy=author,
                        order=CourseUnit.objects.filter(course=self).count())
        cu.save()
        return unit
        
    def get_user_role(self, user, justOne=True, raiseError=True):
        'return role(s) of specified user in this course'
        l = [r.role for r in self.role_set.filter(user=user)]
        if (raiseError or justOne) and not l:
            raise KeyError('user not in this class')
        if justOne:
            return l[0]
        else:
            return l
    def get_course_units(self, publishedOnly=True):
        'ordered list of cunits for this course'
        if publishedOnly: # only those already released
            return  list(self.courseunit_set
                .filter(releaseTime__isnull=False,
                        releaseTime__lt=timezone.now()).order_by('order'))
        else:
            return  list(self.courseunit_set.all().order_by('order'))
    reorder_course_unit = reorder_exercise
    def get_users(self, role=None):
        if not role:
            role = Role.INSTRUCTOR
        return User.objects.filter(role__role=role, role__course=self)
    def __unicode__(self):
        return self.title

class CourseUnit(models.Model):
    'list of units in a course'
    unit = models.ForeignKey(Unit)
    course = models.ForeignKey(Course)
    order = models.IntegerField()
    addedBy = models.ForeignKey(User)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    releaseTime = models.DateTimeField('time released', null=True)
    def is_published(self):
        return self.releaseTime and self.releaseTime < timezone.now()
    
class Role(models.Model):
    'membership of a user in a course'
    INSTRUCTOR = 'prof'
    TA = 'TA'
    ENROLLED = 'student'
    SELFSTUDY = 'self'
    ROLE_CHOICES = (
        (INSTRUCTOR, 'Instructor'),
        (TA, 'Teaching Assistant'),
        (ENROLLED, 'Enrolled Student'),
        (SELFSTUDY, 'Self-study'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, 
                            default=ENROLLED)
    course = models.ForeignKey(Course)
    user = models.ForeignKey(User)
    atime = models.DateTimeField('time submitted', default=timezone.now)

class UnitStatus(models.Model):
    'records what user has completed in a unit lesson sequence'
    unit = models.ForeignKey(Unit)
    user = models.ForeignKey(User)
    startTime = models.DateTimeField('time started', default=timezone.now)
    endTime = models.DateTimeField('time ended', null=True)
    order = models.IntegerField(default=0) # index of current UL
    @classmethod
    def get_or_none(klass, unit, user, **kwargs):
        try:
            return klass.objects.get(unit=unit, user=user, **kwargs)
        except UnitStatus.DoesNotExist:
            return None
    @classmethod
    def is_done(klass, unit, user):
        return klass.get_or_none(unit, user, endTime__isnull=False)
    def get_lesson(self):
        'get the current lesson'
        return self.unit.unitlesson_set.get(order=self.order)
    def set_lesson(self, ul):
        'advance to specified lesson, but prevent skipping on first run'
        if ul.order > self.order:
            if not self.endTime and ul.order > self.order + 1:
                return self.start_next_lesson() # prevent skipping ahead
            self.order = ul.order
            self.save()
        return ul
    def done(self):
        'reset to start of sequence, and set endTime if not already'
        self.order = 0 # reset in case user wants to repeat
        if not self.endTime:
            self.endTime = timezone.now() # mark as done
            self.save()
            return True        
        self.save()
    def start_next_lesson(self):
        'advance to the next lesson, if any, else return None'
        self.order += 1
        try:
            ul = self.get_lesson()
            self.save()
            return ul
        except UnitLesson.DoesNotExist:
            self.done()
            return None


##################################################################
# json blob utility functions

def dump_json_id(o, name=None):
    l = []
    if name:
        l.append(name)
    name = '_'.join(l + [o.__class__.__name__, 'id'])
    return (name, o.pk)

def dump_json_id_dict(d):
    'get json representation of dict of db objects'
    data = {}
    for k, v in d.items():
        if v.__class__.__name__ in klassNameDict: # save db object id
            name, pk = dump_json_id(v, k)
            data[name] = pk
        else: # just copy literal value, assuming JSON can serialize it
            data[k] = v
    return json.dumps(data)

def save_json_data(self, d, attr='data'):
    'save dict of object refs back to db blob field'
    if d:
        s = dump_json_id_dict(d)
    else:
        s = None
    setattr(self, attr, s)
    self.save()
        
# index of types that can be saved in json blobs
klassNameDict = dict(
    Concept=Concept, ConceptGraph=ConceptGraph,
    Lesson=Lesson, ConceptLink=ConceptLink,
    UnitLesson=UnitLesson, Unit=Unit,
    Response=Response, StudentError=StudentError, 
    Course=Course, CourseUnit=CourseUnit, Role=Role, UnitStatus=UnitStatus,
    )


def load_json_id(name, pk):
    'get the specified object as (label, obj) tuple'
    l = name.split('_')
    klassName = l[-2]
    o = klassNameDict[klassName].objects.get(pk=pk)
    return (l[0], o)

def load_json_id_dict(s):
    'get dict of db objects from json blob representation'
    data = json.loads(s)
    d = {}
    for k, v in data.items():
        if k.endswith('_id'): # retrieve db object
            name, obj = load_json_id(k, v)
            d[name] = obj
        else: # just copy literal value
            d[k] = v
    return d

def load_json_data(self, attr='data'):
    'get dict of db objects from json blob field'
    s = getattr(self, attr)
    if s:
        return load_json_id_dict(s)
    else:
        return {}

##################################################################
# activity stack FSM

class FSM(models.Model):
    name = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True)
    help = models.TextField(null=True)
    startNode = models.ForeignKey('FSMNode', related_name='+', null=True)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)
    @classmethod
    def load_graph(klass, fsmData, nodeData, edgeData, username,
                  oldLabel='OLD'):
        '''load FSM specification from node, edge graph by renaming any existing
        FSM with the same name, and creating new FSM.
        Note that ongoing activities
        using the old FSM will continue to work (following the old FSM spec),
        but any new activities will be created using the new FSM spec
        (since they request it by name).'''
        user = User.objects.get(username=username)
        name = fsmData['name']
        oldName = name + oldLabel
        with transaction.atomic(): # rollback if db error occurs
            try: # delete nameOLD FSM if any
                old = klass.objects.get(name=oldName)
            except klass.DoesNotExist:
                pass
            else:
                old.delete()
            try: # rename current to nameOLD
                old = klass.objects.get(name=name)
            except klass.DoesNotExist:
                pass
            else:
                old.name = oldName
                old.save()
            f = klass(addedBy=user, **fsmData) # create new FSM
            f.save()
            nodes = {}
            for name, nodeDict in nodeData.items(): # save nodes
                node = FSMNode(name=name, fsm=f, addedBy=user, **nodeDict)
                node.save()
                nodes[name] = node
                if name == 'START':
                    f.startNode = node
                    f.save()
            for edgeDict in edgeData: # save edges
                edgeDict = edgeDict.copy() # don't modify input dict!
                edgeDict['fromNode'] = nodes[edgeDict['fromNode']]
                edgeDict['toNode'] = nodes[edgeDict['toNode']]
                e = FSMEdge(addedBy=user, **edgeDict)
                e.save()
        return f

class FSMNode(models.Model):
    fsm = models.ForeignKey(FSM)
    name = models.CharField(max_length=64)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True)
    help = models.TextField(null=True)
    path = models.CharField(max_length=200, null=True)
    data = models.TextField(null=True)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)
    funcName = models.CharField(max_length=200, null=True)
    load_json_data = load_json_data
    save_json_data = save_json_data
    def get_path(self, **kwargs):
        return reverse(self.path, kwargs=kwargs)

class FSMDone(ValueError):
    pass

class FSMEdge(models.Model):
    name = models.CharField(max_length=64)
    fromNode = models.ForeignKey(FSMNode, related_name='outgoing')
    toNode = models.ForeignKey(FSMNode, related_name='incoming')
    funcName = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True)
    help = models.TextField(null=True)
    data = models.TextField(null=True)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)
    _funcDict = {}
    load_json_data = load_json_data
    save_json_data = save_json_data
    def get_path(self, **kwargs):
        if self.funcName:
            try:
                func = self._funcDict[self.funcName]
            except KeyError:
                modname, funcname = self.funcName.split('.')
                mod = __import__('fsm_plugin.' + modname, globals(),
                                 locals(), [funcname])
                func = self._funcDict[self.funcName] = getattr(mod, funcname)
            try:
                kwargs = func(self.fromNode, self.toNode, self.data, **kwargs)
            except ValueError:
                return
        if not self.toNode:
            raise FSMDone()
        return self.toNode.get_path(**kwargs)

class FSMState(models.Model):
    user = models.ForeignKey(User)
    fsmNode = models.ForeignKey(FSMNode)
    parentState = models.ForeignKey('FSMState', null=True,
                                    related_name='children')
    linkState = models.ForeignKey('FSMState', null=True,
                                  related_name='linkChildren')
    unitLesson = models.ForeignKey(UnitLesson, null=True)
    path = models.CharField(max_length=200)
    data = models.TextField(null=True)
    isModal = models.BooleanField(default=False)
    atime = models.DateTimeField('time started', default=timezone.now)
    load_json_data = load_json_data
    save_json_data = save_json_data
    def transition(self, name='next', **kwargs):
        try:
            edge = FSMEdge.objects.get(fromNode=self.fsmNode,
                                              name=name)
        except FSMEdge.DoesNotExist:
            raise
        path = edge.get_path(**kwargs)
        if path:
            self.fsmNode = edge.toNode
            self.save()
            return path

        
##################################################################
# discussion

## class Comment(models.Model):
##     QUESTION = 'q'
##     ANSWER = 'a'
##     COMMENT = 'c'
##     ISSUE_REPORT = 'i'
##     PULL_REQUEST = 'p'
##     KIND_CHOICES = (
##         (QUESTION, 'Question'),
##         (ANSWER, 'Answer'),
##         (COMMENT, 'Comment'),
##         (ISSUE_REPORT, 'Issue Report'),
##         (PULL_REQUEST, 'Pull Request'),
##     )
##     HIDDEN = 0
##     CLOSED = 1
##     OPEN = 2
##     kind = models.CharField(max_length=2, choices=KIND_CHOICES,
##                             default=COMMENT)
##     status = models.IntegerField(default=OPEN)
##     title = models.TextField(null=True)
##     text = models.TextField()
##     thread = models.ForeignKey('self', null=True)
##     atime = models.DateTimeField('time submitted')
##     author = models.ForeignKey(User)
##     concept = models.ForeignKey(Concept, null=True)
##     lesson = models.ForeignKey(Lesson, null=True)
##     commonError = models.ForeignKey(Lesson, null=True)
##     question = models.ForeignKey(Lesson, null=True)
##     errorModel = models.ForeignKey(Lesson, null=True)
##     remediation = models.ForeignKey(Lesson, null=True)
##     counterExample = models.ForeignKey(Lesson, null=True)
##     course = models.ForeignKey(Lesson, null=True)
##     conceptTerm = models.ForeignKey(Lesson, null=True)
    

