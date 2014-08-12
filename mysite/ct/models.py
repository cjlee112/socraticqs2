from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.core.urlresolvers import reverse
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
# Concept and associated info

class Concept(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    addedBy = models.ForeignKey(User)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    def __unicode__(self):
        return self.title
    @classmethod
    def get_from_sourceDB(klass, sourceID, user, sourceDB='wikipedia'):
        lesson = Lesson.get_from_sourceDB(sourceID, user, sourceDB)
        try:
            return lesson.lessonlink_set.filter(relationship=
                                    LessonLink.DEFINES)[0].concept, lesson
        except IndexError:
            pass
        concept = klass(title=lesson.title, addedBy=user,
                        description=lesson.text + ' (%s)' % sourceDB)
        concept.save()
        ll = LessonLink(concept=concept, lesson=lesson, addedBy=user,
                    relationship=LessonLink.DEFINES)
        ll.save()
        return concept, lesson
    def __unicode__(self):
        return self.title
            

class ConceptLink(models.Model):
    DEPENDS = 'depends'
    MOTIVATES = 'motiv'
    REL_CHOICES = (
        (DEPENDS, 'Depends on'),
        (MOTIVATES, 'Motivates'),
    )
    fromConcept = models.ForeignKey(Concept, related_name='relatedTo')
    toConcept = models.ForeignKey(Concept, related_name='relatedFrom')
    relationship = models.CharField(max_length=10, choices=REL_CHOICES,
                                    default=DEPENDS)
    addedBy = models.ForeignKey(User)
    atime = models.DateTimeField('time submitted', default=timezone.now)

class Lesson(models.Model):
    READING = 'reading'
    DATA = 'data'
    LECTURE = 'lecture'
    SLIDES = 'slides'
    EXERCISE = 'exercise'
    CASESTUDY = 'case'
    PROJECT = 'project'
    ENCYCLOPEDIA = 'e-pedia'
    FORUM = 'forum'
    VIDEO = 'video'
    AUDIO = 'audio'
    IMAGE = 'image'
    DATABASE = 'db'
    SOFTWARE = 'software'
    KIND_CHOICES = (
        (READING, READING),
        (DATA, DATA),
        (LECTURE, LECTURE),
        (SLIDES, SLIDES),
        (EXERCISE, EXERCISE),
        (CASESTUDY, 'Case Study'),
        (PROJECT, PROJECT),
        (ENCYCLOPEDIA, 'Encyclopedia'),
        (FORUM, FORUM),
        (VIDEO, VIDEO),
        (AUDIO, AUDIO),
        (IMAGE, IMAGE),
        (DATABASE, 'Database'),
        (SOFTWARE, SOFTWARE),
    )
    _sourceDBdict = import_sourcedb_plugins()
    title = models.CharField(max_length=100)
    text = models.TextField(null=True)
    url = models.CharField(max_length=256, null=True)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES,
                            default=READING)
    sourceDB = models.CharField(max_length=32, null=True)
    sourceID = models.CharField(max_length=100, null=True)
    addedBy = models.ForeignKey(User)
    atime = models.DateTimeField('time submitted', default=timezone.now)

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
        lesson.save()
        lesson._sourceDBdata = data
        return lesson

    @classmethod
    def search_sourceDB(klass, query, sourceDB='wikipedia', **kwargs):
        dataClass = klass._sourceDBdict[sourceDB]
        return dataClass.search(query, **kwargs)

    def __unicode__(self):
        return self.title
    def get_url(self):
        if self.sourceDB:
            return self.url
        else:
            return reverse('ct:lesson', args=(self.id,))
        
    
class LessonLink(models.Model):
    DEFINES = 'defines'
    DERIVES = 'derives'
    DEPENDS = 'depends'
    MOTIVATES = 'motiv'
    ILLUSTRATES = 'illust'
    REL_CHOICES = (
        (DEFINES, 'Defines'),
        (DERIVES, 'Derives'),
        (DEPENDS, 'Depends on'),
        (MOTIVATES, 'Motivates'),
        (ILLUSTRATES, 'Illustrates'),
    )
    concept = models.ForeignKey(Concept)
    lesson = models.ForeignKey(Lesson, null=True)
    question = models.ForeignKey('Question', null=True)
    relationship = models.CharField(max_length=10, choices=REL_CHOICES,
                                    default=DEFINES)
    addedBy = models.ForeignKey(User)
    atime = models.DateTimeField('time submitted', default=timezone.now)

class CommonError(models.Model):
    'a conceptual error spanning many questions on the same concept'
    concept = models.ForeignKey(Concept)
    synopsis = models.TextField() # "Some people thought..."
    disproof = models.TextField(null=True) # formal statement of why CE is wrong
    prescription = models.TextField(null=True) # what to change to apply concept right
    dangerzone = models.TextField(null=True) # warnings of when people make this CE
    atime = models.DateTimeField('time submitted', default=timezone.now)
    author = models.ForeignKey(User)
    def __unicode__(self):
        return self.synopsis

class CounterExample(models.Model):
    'clear example that shows a CommonError must be wrong'
    commonError = models.ForeignKey(CommonError)
    intro = models.TextField() # succinctly define the example case
    hint = models.TextField() # question that points directly to the mismatch
    conclusion = models.TextField() # states how CE obviously wrong on this example
    atime = models.DateTimeField('time submitted', default=timezone.now)
    author = models.ForeignKey(User)

class ConceptTerm(models.Model):
    'word, picture or equation that helps students add concept to their "language"'
    TERM = 'term'
    PICTURE = 'pict'
    EQUATION = 'eq'
    KIND_CHOICES = (
        (TERM, 'Vocabulary Term'),
        (PICTURE, 'Picture'),
        (EQUATION, 'Equation'),
    )
    kind = models.CharField(max_length=10, choices=KIND_CHOICES,
                            default=TERM)
    name = models.CharField(max_length=100)
    concept = models.ForeignKey(Concept)
    description = models.TextField()
    atime = models.DateTimeField('time submitted', default=timezone.now)
    author = models.ForeignKey(User)
    


###################################################
# Question and associated info

class Question(models.Model):
    '''a challenge-response learning exercise designed to reveal
    conceptual errors'''
    PUBLIC = 'public'
    INSTRUCTOR_ONLY = 'instr'
    CONCEPT_INVENTORY = 'CI'
    PRIVATE = 'private'
    ACCESS_CHOICES = (
        (PUBLIC, 'Public'),
        (INSTRUCTOR_ONLY, 'By instructors only'),
        (CONCEPT_INVENTORY, 'For concept inventory only'),
        (PRIVATE, 'By author only'),
    )
    title = models.CharField(max_length=200)
    qtext = models.TextField()
    answer = models.TextField()
    access = models.CharField(max_length=10, choices=ACCESS_CHOICES, 
                              default=PUBLIC)
    concept = models.ForeignKey(Concept, null=True)
    author = models.ForeignKey(User)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    def __unicode__(self):
        return self.title

class StudyList(models.Model):
    'list of questions of interest to each user'
    question = models.ForeignKey(Question)
    user = models.ForeignKey(User)
    def __unicode__(self):
        return self.question.title
    
class ErrorModel(models.Model):
    'a specific kind of error on a question, or a generic error'
    question = models.ForeignKey(Question, blank=True, null=True)
    commonError = models.ForeignKey(CommonError, blank=False, null=True)
    description = models.TextField()
    isAbort = models.BooleanField(default=False)
    isFail = models.BooleanField(default=False)
    alwaysAsk = models.BooleanField(default=False)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    author = models.ForeignKey(User)

    @classmethod
    def get_generic(klass):
        'get all error models marked as alwaysAsk'
        return klass.objects.filter(alwaysAsk=True)
    
    def __unicode__(self):
        return self.description


class Response(models.Model):
    'answer entered by a student in response to a question'
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
    NEED_HELP_STATUS = 'help'
    NEED_REVIEW_STATUS = 'review'
    DONE_STATUS = 'done'
    STATUS_CHOICES = (
        (NEED_HELP_STATUS, 'Still confused, need help'),
        (NEED_REVIEW_STATUS, 'OK, but need further review and practice'),
        (DONE_STATUS, 'Solidly'),
    )
    question = models.ForeignKey(Question)
    courseQuestion = models.ForeignKey('CourseQuestion', null=True)
    atext = models.TextField()
    confidence = models.CharField(max_length=10, choices=CONF_CHOICES, 
                                  blank=False, null=False)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    selfeval = models.CharField(max_length=10, choices=EVAL_CHOICES, 
                                blank=False, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, 
                              blank=False, null=True)
    author = models.ForeignKey(User)
    def __unicode__(self):
        return 'answer by ' + self.author.username

class StudentError(models.Model):
    'identification of a specific error model made by a student'
    response = models.ForeignKey(Response)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    errorModel = models.ForeignKey(ErrorModel, blank=True, null=True)
    author = models.ForeignKey(User)
    def __unicode__(self):
        return 'eval by ' + self.author.username

class Remediation(models.Model):
    errorModel = models.ForeignKey(ErrorModel)
    title = models.CharField(max_length=200)
    advice = models.TextField() # how to use the reccd materials
    lessons = models.ManyToManyField(Lesson, null=True) # what materials to use
    atime = models.DateTimeField('time submitted', default=timezone.now)
    author = models.ForeignKey(User)
    def __unicode__(self):
        return 'advice by ' + self.author.username




#######################################
# Course and membership info

class Course(models.Model):
    'a traditional (multi-concept) course'
    PUBLIC = 'public'
    INSTRUCTOR_ONLY = 'instr'
    CONCEPT_INVENTORY = 'CI'
    PRIVATE = 'private'
    ACCESS_CHOICES = (
        (PUBLIC, 'Public'),
        (INSTRUCTOR_ONLY, 'By instructors only'),
        (PRIVATE, 'By author only'),
    )
    title = models.CharField(max_length=200)
    liveCourselet = models.ForeignKey('Courselet', related_name='+', null=True)
    access = models.CharField(max_length=10, choices=ACCESS_CHOICES, 
                              default=PUBLIC)
    addedBy = models.ForeignKey(User)
    atime = models.DateTimeField('time submitted', default=timezone.now)
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


class Courselet(models.Model):
    'a unit of exercises performed together, e.g. one lecture'
    title = models.CharField(max_length=200)
    course = models.ForeignKey(Course)
    liveCourseQuestion = models.ForeignKey('CourseQuestion',
                                           related_name='+', null=True)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)
    def __unicode__(self):
        return self.title

class CourseQuestion(models.Model):
    'an exercise (posing one question) in a courselet'
    START_STAGE = 0
    RESPONSE_STAGE = 1
    ASSESSMENT_STAGE = 2
    DONE_STAGE = 3
    courselet = models.ForeignKey(Courselet)
    question = models.ForeignKey(Question)
    order = models.IntegerField(null=True)
    liveStage = models.IntegerField(null=True)
    startTime = models.DateTimeField('time started', null=True)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)

    def iswait(self, stage):
        'should student wait until instructor advances live session?'
        return self.liveStage == stage  # wait for instructor to advance

    def get_user_stage(self, user):
        try:
            r = self.response_set.filter(author=user)[0]
        except IndexError:
            return self.START_STAGE, None
        if r.selfeval is None:
            return self.RESPONSE_STAGE, r
        else:
            return self.ASSESSMENT_STAGE, r
    def start_user_session(self, user):
        LiveUser.start_user_session(self, user)
    def livestart(self, end=False):
        if end:
            self.liveStage = self.DONE_STAGE
            self.courselet.liveCourseQuestion = None
        else:
            self.liveStage = self.RESPONSE_STAGE
            self.courselet.liveCourseQuestion = self
            self.courselet.course.liveCourselet = self.courselet
            self.courselet.course.save()
        self.save()
        self.courselet.save()
    def __unicode__(self):
        return self.question.title
        
class LiveUser(models.Model):
    'user logged in to a live exercise'
    courseQuestion = models.ForeignKey(CourseQuestion)
    user = models.ForeignKey(User, unique=True)

    @classmethod
    def start_user_session(klass, courseQuestion, user):
        'record user as logged in to this live courseQuestion'
        try:
            o = klass.objects.get(user=user)
            o.courseQuestion = courseQuestion
        except ObjectDoesNotExist:
            o = klass(courseQuestion=courseQuestion, user=user)
        o.save()
        return o

class CourseLesson(models.Model):
    'non-Question materials to display in a courselet'
    courselet = models.ForeignKey(Courselet)
    lesson = models.ForeignKey(Lesson)
    order = models.IntegerField(null=True)
    intro = models.TextField(null=True)
    conclusion = models.TextField(null=True)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)


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
    

######################################################################
# CURRENTLY UNUSED
    
class Glossary(models.Model):
    title = models.CharField(max_length=200)
    explanation = models.TextField()
    def __unicode__(self):
        return 'glossary: %s' % self.title
    

class Vocabulary(models.Model):
    glossary = models.ForeignKey(Glossary)
    term = models.CharField(max_length=100)
    definition = models.TextField()
    atime = models.DateTimeField('time submitted')
    author = models.ForeignKey(User)
    def __unicode__(self):
        return 'def: %s (%s)' % (self.term, self.author.username)


class ConceptPicture(models.Model):
    glossary = models.ForeignKey(Glossary)
    title = models.CharField(max_length=200)
    terms = models.CharField(max_length=200)
    explanation = models.TextField()
    atime = models.DateTimeField('time submitted')
    author = models.ForeignKey(User)
    def __unicode__(self):
        return 'pic: %s (%s)' % (self.title, self.author.username)

class ConceptEquation(models.Model):
    glossary = models.ForeignKey(Glossary)
    title = models.CharField(max_length=200)
    terms = models.CharField(max_length=200)
    math = models.TextField()
    explanation = models.TextField()
    atime = models.DateTimeField('time submitted')
    author = models.ForeignKey(User)
    def __unicode__(self):
        return 'equation: %s (%s)' % (self.title, self.author.username)


