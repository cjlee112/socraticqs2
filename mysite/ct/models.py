from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

# Create your models here.

class Course(models.Model):
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
    liveUnit = models.ForeignKey('Unit', related_name='+', null=True)
    access = models.CharField(max_length=10, choices=ACCESS_CHOICES, 
                              default=PUBLIC)
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


class Unit(models.Model):
    title = models.CharField(max_length=200)
    course = models.ForeignKey(Course)
    liveUnitQ = models.ForeignKey('UnitQ', related_name='+', null=True)
    def __unicode__(self):
        return self.title

class Question(models.Model):
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
    author = models.ForeignKey(User)
    def __unicode__(self):
        return self.title

class UnitQ(models.Model):
    START_STAGE = 0
    RESPONSE_STAGE = 1
    ASSESSMENT_STAGE = 2
    DONE_STAGE = 3
    unit = models.ForeignKey(Unit)
    question = models.ForeignKey(Question)
    order = models.IntegerField(null=True)
    liveStage = models.IntegerField(null=True)
    startTime = models.DateTimeField('time started', null=True)

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
            self.unit.liveUnitQ = None
        else:
            self.liveStage = self.RESPONSE_STAGE
            self.unit.liveUnitQ = self
            self.unit.course.liveUnit = self.unit
            self.unit.course.save()
        self.save()
        self.unit.save()
    def __unicode__(self):
        return self.question.title
        

class StudyList(models.Model):
    question = models.ForeignKey(Question)
    user = models.ForeignKey(User)
    def __unicode__(self):
        return self.question.title
    
class ErrorModel(models.Model):
    question = models.ForeignKey(Question, blank=True, null=True)
    description = models.TextField()
    isAbort = models.BooleanField(default=False)
    isFail = models.BooleanField(default=False)
    alwaysAsk = models.BooleanField(default=False)
    atime = models.DateTimeField('time submitted')
    author = models.ForeignKey(User)

    @classmethod
    def get_generic(klass):
        'get all error models marked as alwaysAsk'
        return klass.objects.filter(alwaysAsk=True)
    
    def __unicode__(self):
        return self.description

class Response(models.Model):
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
    unitq = models.ForeignKey(UnitQ, null=True)
    atext = models.TextField()
    confidence = models.CharField(max_length=10, choices=CONF_CHOICES, 
                                  blank=False, null=False)
    atime = models.DateTimeField('time submitted')
    selfeval = models.CharField(max_length=10, choices=EVAL_CHOICES, 
                                blank=False, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, 
                              blank=False, null=True)
    author = models.ForeignKey(User)
    def __unicode__(self):
        return 'answer by ' + self.author.username

class StudentError(models.Model):
    response = models.ForeignKey(Response)
    atime = models.DateTimeField('time submitted')
    errorModel = models.ForeignKey(ErrorModel, blank=True, null=True)
    author = models.ForeignKey(User)
    def __unicode__(self):
        return 'eval by ' + self.author.username


class LiveUser(models.Model):
    unitq = models.ForeignKey(UnitQ)
    user = models.ForeignKey(User, unique=True)

    @classmethod
    def start_user_session(klass, unitq, user):
        'record user as logged in to this live UnitQ'
        try:
            o = klass.objects.get(user=user)
            o.unitq = unitq
        except ObjectDoesNotExist:
            o = klass(unitq=unitq, user=user)
        o.save()
        return o

######################################################################
# CURRENTLY UNUSED
    
class Remediation(models.Model):
    errorModel = models.ForeignKey(ErrorModel)
    remediation = models.TextField()
    counterExample = models.TextField()
    atime = models.DateTimeField('time submitted')
    author = models.ForeignKey(User)
    def __unicode__(self):
        return 'advice by ' + self.author.username

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


