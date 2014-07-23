from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Course(models.Model):
    title = models.CharField(max_length=200)
    liveUnit = models.ForeignKey('Unit', related_name='+', null=True)

class Role(models.Model):
    INSTRUCTOR = 'prof'
    TA = 'TA'
    STUDENT = 'student'
    ROLE_CHOICES = (
        (INSTRUCTOR, 'Instructor'),
        (TA, 'Teaching Assistant'),
        (STUDENT, 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, 
                            default=STUDENT)
    course = models.ForeignKey(Course)
    user = models.ForeignKey(User)


class Unit(models.Model):
    title = models.CharField(max_length=200)
    course = models.ForeignKey(Course)
    liveUnitQ = models.ForeignKey('UnitQ', related_name='+', null=True)

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
    ASK_STAGE = 1
    ASSESS_STAGE = 2
    unit = models.ForeignKey(Unit)
    question = models.ForeignKey(Question)
    order = models.IntegerField(null=True)
    liveStage = models.IntegerField(null=True)
    startTime = models.DateTimeField('time started', null=True)

class StudyList(models.Model):
    question = models.ForeignKey(Question)
    user = models.ForeignKey(User)
    
class ErrorModel(models.Model):
    question = models.ForeignKey(Question, blank=True, null=True)
    description = models.TextField()
    isAbort = models.BooleanField(default=False)
    def __unicode__(self):
        return self.description

class Response(models.Model):
    CORRECT = 'correct'
    CLOSE = 'close'
    DIFFERENT = 'different'
    EVAL_CHOICES = (
        (CORRECT, 'Essentially the same'),
        (CLOSE, 'Close'),
        (DIFFERENT, 'Different'),
    )
    GUESS = 'guess'
    UNSURE = 'unsure'
    SURE = 'sure'
    CONF_CHOICES = (
        (GUESS, 'Just guessing'), 
        (UNSURE, 'Not quite sure'),
        (SURE, 'Pretty sure'),
    )
    question = models.ForeignKey(Question)
    unitq = models.ForeignKey(UnitQ, null=True)
    atext = models.TextField()
    confidence = models.CharField(max_length=10, choices=CONF_CHOICES, 
                                  default=GUESS)
    atime = models.DateTimeField('time submitted')
    selfeval = models.CharField(max_length=10, choices=EVAL_CHOICES, 
                                default=DIFFERENT, blank=True, null=True)
    requestHelp = models.BooleanField(default=False)
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


