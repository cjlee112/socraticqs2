from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Question(models.Model):
    title = models.CharField(max_length=200)
    qtext = models.TextField()
    answer = models.TextField()
    def __unicode__(self):
        return self.title

class ErrorModel(models.Model):
    question = models.ForeignKey(Question, blank=True, null=True)
    description = models.TextField()
    isAbort = models.BooleanField()
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
    atext = models.TextField()
    confidence = models.CharField(max_length=10, choices=CONF_CHOICES, 
                                  default=GUESS)
    atime = models.DateTimeField('time submitted')
    selfeval = models.CharField(max_length=10, choices=EVAL_CHOICES, 
                                default=DIFFERENT, blank=True, null=True)
    requestHelp = models.BooleanField()
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


