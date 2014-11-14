from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.db.models import Q, Count
import glob
from datetime import timedelta


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
    description = models.TextField()
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
        try:
            return lesson.conceptlink_set.filter(relationship=
                                    ConceptLink.IS)[0].concept, lesson
        except IndexError:
            pass
        concept = klass(title=lesson.title, addedBy=user,
                        description=lesson.text + ' (%s)' % sourceDB)
        concept.save()
        cl = ConceptLink(concept=concept, lesson=lesson, addedBy=user,
                         relationship=ConceptLink.IS)
        cl.save()
        return concept, lesson
    @classmethod
    def search_text(klass, s):
        'search Concept title and description'
        return klass.objects.filter(Q(title__icontains=s) |
                                    Q(description__icontains=s)).distinct()
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
        lesson = klass(title=data.title, url=data.url, sourceDB=sourceDB,
                       sourceID=sourceID, addedBy=user, text=data.description)
        lesson.save_root()
        lesson._sourceDBdata = data
        return lesson

    @classmethod
    def search_sourceDB(klass, query, sourceDB='wikipedia', **kwargs):
        dataClass = klass._sourceDBdict[sourceDB]
        return dataClass.search(query, **kwargs)

    @classmethod
    def search_text(klass, s, noDup=True):
        'search Lesson title and text'
        out = klass.objects.filter(Q(title__icontains=s) |
                                   Q(text__icontains=s)).distinct()
        if noDup:
            out = distinct_subset(out)
        return out
    @classmethod
    def create_from_concept(klass, concept, **kwargs):
        'create lesson for initial concept definition'
        if concept.isError:
            kwargs['kind'] = ERROR_MODEL
        lesson = klass(title=concept.title, text=concept.description,
                       addedBy=concept.addedBy, **kwargs)
        lesson.save_root(concept, ConceptLink.IS)
        return lesson
    def save_root(self, concept=None, relationship=None):
        'create root commit by initializing treeID'
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
    def get_url(self):
        if self.sourceDB:
            return self.url
        else:
            return reverse('ct:lesson', args=(self.id,))

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
    IS = 'is'
    DEFINES = 'defines'
    INFORMAL_DEFINITION = 'informal'
    FORMAL_DEFINITION = 'formaldef'
    TESTS = 'tests'
    DERIVES = 'derives'
    PROVES = 'proves'
    ASSUMES = 'assumes'
    MOTIVATES = 'motiv'
    ILLUSTRATES = 'illust'
    INTRODUCES = 'intro'
    COMMENTS = 'comment'
    WARNS = 'warns'
    REL_CHOICES = (
        (IS, 'Represents (unique ID for)'),
        (DEFINES, 'Defines'),
        (INFORMAL_DEFINITION, 'Intuitively defines'),
        (FORMAL_DEFINITION, 'Formally defines'),
        (TESTS, 'Tests understanding of'),
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
    Lesson.BASE_EXPLANATION:ConceptLink.IS,
    Lesson.EXPLANATION:ConceptLink.DEFINES,
    Lesson.ORCT_QUESTION:ConceptLink.TESTS,
    Lesson.CONCEPT_INVENTORY_QUESTION:ConceptLink.TESTS,
    Lesson.EXERCISE:ConceptLink.TESTS,
    Lesson.PROJECT:ConceptLink.TESTS,
    Lesson.PRACTICE_EXAM:ConceptLink.TESTS,
    
    Lesson.ANSWER:ConceptLink.ILLUSTRATES,
    Lesson.ERROR_MODEL:ConceptLink.IS,

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

class UnitLesson(models.Model):
    'pointer to a Lesson as part of a Unit branch'
    COMPONENT = 'part'
    ANSWERS = 'answers'
    MISUNDERSTANDS = 'errmod'
    PRETEST_POSTTEST = 'pretest'
    SUBUNIT = 'subunit'
    KIND_CHOICES = (
        (COMPONENT, 'Included in this courselet'),
        (ANSWERS, 'Answer for a question'),
        (MISUNDERSTANDS, 'Common error for a question'),
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
    @classmethod
    def create_from_concept(klass, concept, unit=None, ulArgs={}, **kwargs):
        'create lesson for initial concept definition'
        lesson = Lesson.create_from_concept(concept, **kwargs)
        return klass.create_from_lesson(lesson, unit, **ulArgs)
    @classmethod
    def create_from_lesson(klass, lesson, unit, **kwargs):
        kindMap = {Lesson.ANSWER:klass.ANSWERS,
                   Lesson.ERROR_MODEL:klass.MISUNDERSTANDS}
        kwargs['kind'] = kindMap.get(lesson.kind, klass.COMPONENT)
        ul = klass(unit=unit, lesson=lesson, addedBy=lesson.addedBy,
                   treeID=lesson.treeID, **kwargs)
        ul.save()
        return ul
    @classmethod
    def search_text(klass, s, noDup=True):
        'search Lesson title and text'
        out = klass.objects.filter(Q(lesson__title__icontains=s) |
                                   Q(lesson__text__icontains=s)).distinct()
        if noDup:
            out = distinct_subset(out)
        return out
    def get_answer(self):
        'get query set with answer(s) if any'
        return self.unitlesson_set.filter(kind=self.ANSWERS)

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
    def get_exercises(self):
        'ordered list of lessons for this courselet'
        l = list(self.unitlesson_set.filter(order__isnull=False))
        l.sort(lambda x,y:cmp(x.order, y.order))
        return l
    def reorder_exercise(self, old, new):
        'renumber exercises to move an exercise from old -> new position'
        l = self.get_exercises()
        ex = l[old] # select desired exercise by old position
        l = l[:old] + l[old + 1:] # exclude this exercise
        l = l[:new] + [ex] + l[new:] # insert ex in new position
        for i, ex in enumerate(l):
            if i != ex.order: # order changed, have to update
                ex.order = i
                ex.save()
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
    lesson = models.ForeignKey(Lesson) # exact version this applies to
    unitLesson = models.ForeignKey(UnitLesson, null=True)
    course = models.ForeignKey('Course', null=True)
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
        n = querySet.count() or 1 # prevent DivideByZero
        statusTable = [fmt_count(statusDict.get(k, 0), n)
                       for k,_ in STATUS_CHOICES] \
                       + [fmt_count(n - sum(statusDict.values()), n)]
        evalDict = {}
        for d in querySet.values('confidence', 'selfeval') \
          .annotate(dcount=Count('confidence')):
            evalDict[d['confidence'],d['selfeval']] = d['dcount']
        l = []
        for conf,label in klass.CONF_CHOICES:
            l.append((label, [fmt_count(evalDict.get((conf,selfeval), 0), n)
                              for selfeval,_ in klass.EVAL_CHOICES]))
        return statusTable, l, n

class StudentError(models.Model):
    'identification of a specific error model made by a student'
    response = models.ForeignKey(Response)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    errorModel = models.ForeignKey(UnitLesson, blank=True, null=True)
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
    def __unicode__(self):
        return self.title

class CourseUnit(models.Model):
    'list of units in a course'
    unit = models.ForeignKey(Unit)
    course = models.ForeignKey(Course)
    order = models.IntegerField()
    addedBy = models.ForeignKey(User)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    
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



##############################################################
# time utilities

timeUnits = (('seconds', timedelta(minutes=1), lambda t:int(t.seconds)),
             ('minutes', timedelta(hours=1), lambda t:int(t.seconds / 60)),
             ('hours', timedelta(1), lambda t:int(t.seconds / 3600)),
             ('days', timedelta(7), lambda t:t.days))

monthStrings = ('Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'Jun.', 'Jul.',
                'Aug.', 'Sep.', 'Oct.', 'Nov.', 'Dec.')

def display_datetime(dt):
    'get string that sidesteps timezone issues thus: 27 minutes ago'
    def singularize(i, s):
        if i == 1:
            return s[:-1]
        return s
    diff = timezone.now() - dt
    for unit, td, f in timeUnits:
        if diff < td:
            n = f(diff)
            return '%d %s ago' % (n, singularize(n, unit))
    return '%s %d, %d' % (monthStrings[dt.month - 1], dt.day, dt.year)


##################################################################
# activity stack FSM

class FSM(models.Model):
    name = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True)
    help = models.TextField(null=True)
    startNode = models.ForeignKey('FSMNode', related_name='+')
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)

class FSMNode(models.Model):
    fsm = models.ForeignKey(FSM)
    name = models.CharField(max_length=64)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True)
    help = models.TextField(null=True)
    path = models.CharField(max_length=200)
    data = models.TextField(null=True)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)
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
    data = models.TextField(null=True)
    isModal = models.BooleanField(default=False)
    atime = models.DateTimeField('time started', default=timezone.now)
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
    

