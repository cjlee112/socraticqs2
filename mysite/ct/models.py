import re
import time
import logging
import operator
from dateutil import tz
from copy import deepcopy
from datetime import timedelta, datetime
from functools import reduce

from django.db.models.query import QuerySet  # Needed for typechecking.
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.urls import reverse
from django.db import models
from django.db.models import Q, Count, Max
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.models import Site

from core.tasks import faq_notify_instructors, faq_notify_students
from core.common import onboarding
from core.common.mongo import c_chat_context
from core.common.utils import update_onboarding_step, create_intercom_event
from ct.templatetags.ct_extras import md2html


def percent_validator(value):
    if not 0 <= value <= 100:
        raise ValidationError(
            _('%(value)s is not a persent. Value should be range 0-100'),
            params={'value': value},
        )


not_only_spaces_validator = RegexValidator(
    regex=r'^\s+?$',
    inverse_match=True,
    message='This field can not consist of only spaces'
)


def copy_model_instance(inst, **kwargs):
    n_inst = deepcopy(inst)
    n_inst.id = None
    if kwargs:
        for k, v in list(kwargs.items()):
            setattr(n_inst, k, v)
    n_inst.save()
    return n_inst


class SubKindMixin(object):
    kind = None
    sub_kind = None

    MULTIPLE_CHOICES = 'choices'
    NUMBERS = 'numbers'
    EQUATION = 'equation'
    CANVAS = 'canvas'

    def is_canvas(self):
        try:
            unit_lesson = self.unitlesson_set.first()
            return unit_lesson.sub_kind == self.CANVAS
        except AttributeError:
            pass
        return self.sub_kind == self.CANVAS

    def get_canvas_html(self, *args, **kwargs):
        raise NotImplementedError

    def get_html(self, *args, **kwargs):
        """
        Returns html by response type
        """
        if self.is_canvas():
            return self.get_canvas_html(*args, **kwargs)
        else:
            return None


########################################################
# Concept ID and graph -- not version controlled

class Concept(models.Model):
    title = models.CharField(max_length=200)
    addedBy = models.ForeignKey(User, on_delete=models.CASCADE)
    approvedBy = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE,
                                   related_name='approvedConcepts')
    isError = models.BooleanField(default=False)
    isAbort = models.BooleanField(default=False)
    isFail = models.BooleanField(default=False)
    isPuzzled = models.BooleanField(default=False)
    alwaysAsk = models.BooleanField(default=False)
    atime = models.DateTimeField('time submitted', default=timezone.now)

    def __str__(self):
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
        lesson = Lesson(title=title, text=text, addedBy=user,
                        commitTime=timezone.now(), changeLog='initial commit')
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
            try:  # get one lesson representing this error model
                lesson = Lesson.objects.filter(concept=cg.fromConcept)[0]
            except IndexError:
                pass
            else:
                l.append(UnitLesson.create_from_lesson(lesson, parent.unit,
                                                       kind=UnitLesson.MISUNDERSTANDS, parent=parent))
        return l

    def get_url(self, basePath, forceDefault=False, subpath=None,
                isTeach=True):
        objID = unit_id = None
        try:
            unit_id = int(basePath.split('/')[-2])
        except (IndexError, TypeError):
            pass
        for ul in UnitLesson.objects.filter(lesson__concept=self):
            if objID is None or ul.unit_id == unit_id:  # in this unit!
                objID = ul.pk
        if self.isError:  # default settings
            head = 'errors'
            tail = ''
        else:
            head = 'concepts'
            tail = 'lessons/'
        if subpath:  # apply non-default subpath
            tail = subpath + '/'
        elif subpath == '':
            tail = ''
        try:
            return '%s%s/%d/%s' % (basePath, head, objID, tail)
        except TypeError:
            logging.error(
                "Concept.get_url method were not able to build path correctly. "
                "Will return '#' instead. Concept id {}".format(self.id)
            )
            return "#"

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
                    cl.unitLesson = ul  # add attribute to keep this info
                    d[t] = cl
        l = list(d.values())
        l.sort(key=lambda x: x.relationship)
        return l


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
    fromConcept = models.ForeignKey(Concept, related_name='relatedTo', on_delete=models.CASCADE)
    toConcept = models.ForeignKey(Concept, related_name='relatedFrom', on_delete=models.CASCADE)
    relationship = models.CharField(max_length=10, choices=REL_CHOICES,
                                    default=DEPENDS)
    addedBy = models.ForeignKey(User, on_delete=models.CASCADE)
    approvedBy = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE,
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
DEFAULT_FSM = 'chat'
TRIAL_FSM = 'chat_trial'


class Lesson(models.Model, SubKindMixin):
    BASE_EXPLANATION = 'base'  # focused on one concept, as intro for ORCT
    EXPLANATION = 'explanation'  # conventional textbook or lecture explanation

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
    NOT_CORRECT_CHOICE = '()'
    CORRECT_CHOICE = '(*)'

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
    SUB_KIND_CHOICES = (
        (SubKindMixin.MULTIPLE_CHOICES, 'Multiple Choices Question'),
        (SubKindMixin.NUMBERS, 'Numbers'),
        (SubKindMixin.EQUATION, 'Equation'),
        (SubKindMixin.CANVAS, 'Canvas'),
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
    _sourceDBdict = {}
    title = models.CharField(max_length=200, validators=[not_only_spaces_validator])
    text = models.TextField(null=True, blank=True)
    attachment = models.FileField(null=True, blank=True, upload_to='questions')

    data = models.TextField(null=True, blank=True)  # JSON DATA
    url = models.CharField(max_length=256, null=True, blank=True)
    kind = models.CharField(max_length=50, choices=KIND_CHOICES,
                            default=BASE_EXPLANATION)
    sub_kind = models.CharField(max_length=50, choices=SUB_KIND_CHOICES, blank=True, null=True)
    # lessons with sub kind numbers
    number_value = models.FloatField(default=0)
    number_max_value = models.FloatField(default=0)
    number_min_value = models.FloatField(default=0)
    # end numbers

    enable_auto_grading = models.BooleanField(default=False)

    medium = models.CharField(max_length=10, choices=MEDIA_CHOICES,
                              default=READING)
    access = models.CharField(max_length=10, choices=ACCESS_CHOICES,
                              default=PUBLIC_ACCESS)
    sourceDB = models.CharField(max_length=32, null=True, blank=True)
    sourceID = models.CharField(max_length=100, null=True, blank=True)
    addedBy = models.ForeignKey(User, on_delete=models.CASCADE)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    concept = models.ForeignKey(Concept, null=True, blank=True, on_delete=models.CASCADE)  # concept definition
    treeID = models.IntegerField(null=True, blank=True)  # VCS METADATA
    parent = models.ForeignKey('Lesson', null=True, blank=True, on_delete=models.CASCADE,
                               related_name='children')
    mergeParent = models.ForeignKey('Lesson', null=True, blank=True, on_delete=models.CASCADE,
                                    related_name='mergeChildren')
    changeLog = models.TextField(null=True, blank=True)
    commitTime = models.DateTimeField('time committed', null=True, blank=True)
    add_unit_aborts = models.BooleanField(default=False)
    mc_simplified = models.BooleanField(default=False)

    _cloneAttrs = ('title', 'text', 'data', 'url', 'kind', 'medium', 'access',
                   'sourceDB', 'sourceID', 'concept', 'treeID',
                   'attachment',
                   'number_value', 'number_min_value', 'number_max_value',
                   'enable_auto_grading',
                   )

    def save(self):
        if self.kind == Lesson.EXPLANATION:
            self.sub_kind = None
        try:
            return super().save()
        except Exception as e:
            print(e)

    def get_choices(self, with_description=False):
        """Parse self.text and try to find choices.

        () - empty parenthes - for not correct answer
        (*) - for correct answer
        :return: list of choices
        """
        choices = []
        choice_description = []
        choice_index = -1  # To start with index 0 of choice
        if '[choices]' in self.text:
            listed = self.text.split('\r\n')
            for i in range(listed.index('[choices]') + 1, len(listed)):
                if listed[i].startswith(self.CORRECT_CHOICE) or listed[i].startswith(self.NOT_CORRECT_CHOICE):
                    choices.append(listed[i])
                    choice_index += 1
                elif with_description:
                    desc = md2html(listed[i]) if '.. math::' in listed[i] else listed[i]
                    choice_description.append((choice_index, desc))
        if with_description:
            # The structure of choices with description - [(choice, description), (choice, description)]
            _choices = []
            for ind, choice in enumerate(choices):
                choice_desc = ''
                for desc_index, desc in choice_description:
                    if desc_index == ind and desc:
                        choice_desc += desc + '\r\n'
                _choices.append((choice, choice_desc))
            return enumerate(_choices)
        return enumerate(choices)

    def get_choice_title(self, index):
        for idx, choice in self.get_choices():
            if index == idx:
                splitted_title = re.split('^\(\**\) *', choice)
                return splitted_title[1] if len(splitted_title) > 1 else splitted_title[0]

    def get_choice_description(self, index):
        for idx, (choice, description) in self.get_choices(with_description=True):
            if index == idx:
                return description

    def get_choices_wrap_text(self):
        return self.text.split('[choices]')[0]

    def get_correct_choices(self):
        """Return only correct choices from list of choices

        :return: correct choices.
        """
        return [(i, choice) for i, choice in self.get_choices() if choice.startswith(self.CORRECT_CHOICE)]

    def get_canvas_html(self, disabled=False):
        """
        Returns container for drawing
        """
        is_answer = self.kind == 'answer'
        if is_answer:
            background_image = self.unitlesson_set.first().parent.lesson.attachment
            svg_image = self.attachment
        else:
            background_image = self.attachment
            svg_image = None
        return render_to_string('ct/lesson/sub_kind_canvas.html', context={
            'lesson': self,
            'disabled': self.kind == 'answer' or disabled,
            'background_image': background_image,
            'svg_image': svg_image,
        })

    @classmethod
    def get_sourceDB_plugin(klass, sourceDB):
        try:
            return klass._sourceDBdict[sourceDB]
        except KeyError:
            import importlib
            mod = importlib.import_module('ct.sourcedb_plugin.%s_plugin'
                                          % sourceDB)
            dataClass = mod.LessonDoc
            klass._sourceDBdict[sourceDB] = dataClass
            return dataClass

    @classmethod
    def get_from_sourceDB(klass, sourceID, user, sourceDB='wikipedia',
                          doSave=True):
        'get or create Lesson linked to sourceDB:sourceID external ref'
        try:
            return klass.objects.filter(sourceDB=sourceDB, sourceID=sourceID) \
                .order_by('-atime')[0]  # get most recent version
        except IndexError:
            pass
        dataClass = klass.get_sourceDB_plugin(sourceDB)
        data = dataClass(sourceID)
        try:  # attribute authorship to the sourceDB
            user = User.objects.get(username=sourceDB)
        except User.DoesNotExist:
            pass
        lesson = klass(title=data.title, url=data.url, sourceDB=sourceDB,
                       sourceID=sourceID, addedBy=user, text=data.description,
                       kind=klass.EXPLANATION, commitTime=timezone.now(),
                       changeLog='initial text from %s' % sourceDB)
        if doSave:  # not just temporary, but save as permanent record
            lesson.save_root()
        lesson._sourceDBdata = data
        return lesson

    @classmethod
    def search_sourceDB(klass, query, sourceDB='wikipedia', **kwargs):
        'get [(title, sourceID, url)] for query from sourceDB using plugin'
        dataClass = klass.get_sourceDB_plugin(sourceDB)
        return dataClass.search(query, **kwargs)

    # @classmethod
    # def create_from_concept(klass, concept, **kwargs):
    #     'create lesson for initial concept definition'
    #     if concept.isError:
    #         kwargs['kind'] = klass.ERROR_MODEL
    #     lesson = klass(title=concept.title, text=concept.description,
    #                    addedBy=concept.addedBy, concept=concept, **kwargs)
    #     lesson.save_root()
    #     return lesson
    def save_root(self, concept=None, relationship=None):
        'create root commit by initializing treeID'
        if self.treeID is None:  # no tree ID, so save as root commit
            self.save()
            self.treeID = self.pk
        self.save()
        if concept:
            if relationship is None:
                relationship = DEFAULT_RELATION_MAP[self.kind]
            self.conceptlink_set.create(concept=concept,
                                        addedBy=self.addedBy, relationship=relationship)

    def save_as_error_model(self, concept, questionUL, errorModel=None):
        """Save this new lesson as an error model for the specified
        concept and question.  It does this by creating an error model
        concept and creating a child UnitLesson linking it to the
        questionUL."""
        self.kind = self.ERROR_MODEL
        if errorModel is None:
            em = concept.create_error_model(title=self.title,
                                            addedBy=self.addedBy)
        self.concept = em
        self.save_root()
        return UnitLesson.create_from_lesson(self, questionUL.unit,
                                             parent=questionUL)

    def is_committed(self):
        'True if already committed'
        return self.commitTime is not None

    def _clone_dict(self):
        'get dict of attrs to clone'
        kwargs = {}
        for attr in self._cloneAttrs:  # clone our attributes
            kwargs[attr] = getattr(self, attr)
        return kwargs

    def checkout(self, addedBy):
        '''prepare to update.  If this required cloning, returns the
        cloned Lesson object; caller must save()!!.  Otherwise returns None'''
        if not self.is_committed() and (self.addedBy != addedBy or
                                        self.response_set.count() > 0):
            # do not mix edits from different people, or lose response snapshot
            self.checkin(commit=True)
        if self.is_committed():
            kwargs = self._clone_dict()
            return self.__class__(parent=self, addedBy=addedBy, **kwargs)

    def checkin(self, commit, doSave=True, copyLinks=False):
        '''finish checkout process by saving cloned links,
        permanent commit etc. as required'''
        if commit:
            if self.parent and not self.parent.is_committed():
                self.parent.checkin(commit=True)
            self.commitTime = timezone.now()
        if commit or doSave:
            self.save()
        if copyLinks:
            for cl in self.parent.conceptlink_set.all():
                cl.copy(self)

    def add_concept_link(self, concept, relationship, addedBy):
        'add concept link if not already present'
        if self.conceptlink_set.filter(concept=concept,
                                       relationship=relationship).count() == 0:
            return self.conceptlink_set.create(concept=concept, addedBy=addedBy,
                                               relationship=relationship)

    def __str__(self):
        return self.title
    # def get_url(self):
    #     if self.sourceDB:
    #         return self.url
    #     else:
    #         return reverse('ct:lesson', args=(self.id,))
    def natural_key(self):
        """
        Support method for ct.serializers.

        Returns id, title and text fields instead of pk.
        """
        return (self.id, self.title, self.text)


def distinct_subset(inlist, distinct_func=lambda x: x.treeID):
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
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    relationship = models.CharField(max_length=10, choices=REL_CHOICES,
                                    default=DEFINES)
    addedBy = models.ForeignKey(User, on_delete=models.CASCADE)
    atime = models.DateTimeField('time submitted', default=timezone.now)

    def copy(self, lesson):
        'copy this conceptlink to a new lesson'
        cl = self.__class__(concept=self.concept, lesson=lesson,
                            relationship=self.relationship,
                            addedBy=self.addedBy, atime=self.atime)
        cl.save()
        return cl

    def annotate_ul(self, unit):
        '''add unitLesson as TEMPORARY attribute, within the specified unit.
        Note this attribute is NOT stored in the database!!'''
        try:
            self.unitLesson = UnitLesson.objects.filter(unit=unit,
                                                        lesson=self.lesson)[0]
        except IndexError:
            raise UnitLesson.DoesNotExist('unitLesson not in this unit')


DEFAULT_RELATION_MAP = {
    Lesson.BASE_EXPLANATION: ConceptLink.DEFINES,
    Lesson.EXPLANATION: ConceptLink.DEFINES,
    Lesson.ORCT_QUESTION: ConceptLink.TESTS,
    Lesson.CONCEPT_INVENTORY_QUESTION: ConceptLink.TESTS,
    Lesson.EXERCISE: ConceptLink.TESTS,
    Lesson.PROJECT: ConceptLink.TESTS,
    Lesson.PRACTICE_EXAM: ConceptLink.TESTS,

    Lesson.ANSWER: ConceptLink.ILLUSTRATES,
    Lesson.ERROR_MODEL: ConceptLink.DEFINES,

    Lesson.DATA: ConceptLink.ILLUSTRATES,
    Lesson.CASESTUDY: ConceptLink.ILLUSTRATES,
    Lesson.ENCYCLOPEDIA: ConceptLink.DEFINES,
    Lesson.FAQ_QUESTION: ConceptLink.COMMENTS,
    Lesson.FORUM: ConceptLink.COMMENTS,
}


class StudyList(models.Model):
    'list of materials of interest to each user'
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.lesson.title


############################################################
# unit lesson repo and graph

IS_ERROR = 0
IS_CONCEPT = 1
IS_LESSON = 2


class UnitLesson(models.Model):
    'pointer to a Lesson as part of a Unit branch'
    _headURL = 'lessons'
    _tasksPath = {IS_ERROR: 'faq', IS_CONCEPT: 'faq', IS_LESSON: 'tasks'}
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
    LESSON_ROLE = 'lesson'
    RESOURCE_ROLE = 'resource'
    ROLE_CHOICES = (
        (LESSON_ROLE, "Show this thread to all students as part of the courselet's main lesson sequence"),
        (RESOURCE_ROLE, "Just list this as a follow-up study resource")
    )
    unit = models.ForeignKey('Unit', on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES,
                            default=COMPONENT)
    lesson = models.ForeignKey(Lesson, null=True, blank=True, on_delete=models.CASCADE)
    parent = models.ForeignKey('UnitLesson', null=True, blank=True, on_delete=models.CASCADE)
    order = models.IntegerField(null=True, blank=True)
    atime = models.DateTimeField('time added', default=timezone.now)
    addedBy = models.ForeignKey(User, on_delete=models.CASCADE)
    treeID = models.IntegerField()  # VCS METADATA
    branch = models.CharField(max_length=32, default='master')

    # @classmethod
    # def create_from_concept(klass, concept, unit=None, ulArgs={}, **kwargs):
    #     'create lesson for initial concept definition'
    #     lesson = Lesson.create_from_concept(concept, **kwargs)
    #     return klass.create_from_lesson(lesson, unit, **ulArgs)

    @property
    def text(self):
        return self.lesson.text

    @property
    def sub_kind(self):
        """Initially sub_kind is present only in answers."""
        sub_kind = None
        if not self.lesson.sub_kind:
            if self.kind == self.COMPONENT:
                answer = self.get_answers().first()
                if answer and answer.sub_kind:
                    sub_kind = answer.sub_kind

            if self.kind == self.ANSWERS:
                sub_kind = self.parent.lesson.sub_kind
        else:
            sub_kind = self.lesson.sub_kind
        return sub_kind

    @sub_kind.setter
    def sub_kind(self, val):
        l = self.lesson
        l.sub_kind = val
        l.save()

    def __str__(self):
        return f"UnitLesson: {self.lesson.title}"

    @classmethod
    def create_from_lesson(klass, lesson, unit, order=None, kind=None,
                           addAnswer=False, **kwargs):
        if not kind:
            kindMap = {Lesson.ANSWER: klass.ANSWERS,
                       Lesson.ERROR_MODEL: klass.MISUNDERSTANDS}
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
        if searchType == 'lesson':  # exclude questions
            kwargs['kind'] = klass.COMPONENT
            excludeArgs = excludeArgs.copy()
            excludeArgs['lesson__kind'] = Lesson.ORCT_QUESTION
        elif searchType == 'question':
            kwargs['kind'] = klass.COMPONENT
            kwargs['lesson__kind'] = Lesson.ORCT_QUESTION
        elif searchType == IS_LESSON:  # anything but answer, error etc.
            kwargs['kind'] = klass.COMPONENT
        elif searchType == IS_ERROR:
            kwargs['lesson__concept__isnull'] = False
            kwargs['kind'] = klass.MISUNDERSTANDS
        else:  # search for regular concepts (not an error)
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

    @classmethod
    def search_sourceDB(klass, query, sourceDB='wikipedia', unit=None,
                        **kwargs):
        'get sourceDB search results, represented by existing ULs if any'
        resultsUL = []
        results = []
        for t in Lesson.search_sourceDB(query, sourceDB, **kwargs):
            queryArgs = dict(lesson__sourceDB=sourceDB, lesson__sourceID=t[1])
            hits = ()
            if unit:
                hits = klass.objects.filter(unit=unit, **queryArgs)
            try:  # use UL from this unit if any
                resultsUL.append(hits[0])
            except IndexError:
                hits = klass.objects.filter(**queryArgs)
                try:  # otherwise use any UL matching this sourceID
                    resultsUL.append(hits[0])
                except IndexError:  # no UL so just return tuple
                    results.append(t)
        return resultsUL, results

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
        'get list of resolution UL for this error UL'
        em = self.lesson.concept
        return em, list(self.unitlesson_set.filter(kind=self.RESOLVES))
        # query = Q(kind=self.RESOLVES,
        #           lesson__conceptlink__relationship=ConceptLink.RESOLVES,
        #           lesson__conceptlink__concept=em)
        # return em, distinct_subset(UnitLesson.objects.filter(query))

    def get_new_inquiries(self):
        return self.response_set.filter(kind=Response.STUDENT_QUESTION,
                                        needsEval=True)

    def get_alternative_defs(self, **kwargs):
        return distinct_subset(self.__class__.objects
                               .filter(lesson__concept=self.lesson.concept)
                               .exclude(treeID=self.treeID))

    def get_next_lesson(self):
        if self.order is not None:
            return self.unit.unitlesson_set.get(order=self.order + 1)
        else:
            raise self.__class__.DoesNotExist

    def checkout(self, addedBy):
        'get lesson object we can update (which may be a new object)'
        lesson = self.lesson.checkout(addedBy)
        if lesson:
            return lesson
        else:
            return self.lesson

    def checkin(self, lesson, commit=None, doSave=True):
        '''finalize update of checked-out lesson, committing if requested.
        If lesson != self.lesson, save it as self.lesson.'''
        newLesson = (lesson != self.lesson)
        if commit is None and lesson.changeLog:
            commit = True
        lesson.checkin(commit, doSave, newLesson)
        if newLesson:
            self.lesson = lesson
            self.save()

    def copy(self, unit, addedBy, parent=None, order=None, kind=None, **kwargs):
        'copy self and children to new unit'
        if not self.lesson.is_committed():  # to fork it, must commit it!
            name = addedBy.get_full_name()
            if not name:
                name = addedBy.get_username()
            self.lesson.changeLog = 'snapshot for fork by %s' % name
            self.lesson.checkin(commit=True)
        if order == 'APPEND':
            order = unit.next_order()
        elif order is None:
            order = self.order

        if kind == UnitLesson.RESOLVES:
            self.lesson.add_concept_link(parent.lesson.concept,
                                         ConceptLink.RESOLVES, addedBy)
        elif kind is None:
            kind = self.kind
        ul = copy_model_instance(self, lesson=self.lesson, addedBy=addedBy, unit=unit,
                                 kind=kind, treeID=self.treeID, parent=parent,
                                 order=order, branch=self.branch, **kwargs)
        ul.save()
        for child in self.unitlesson_set.all():  # copy children
            child.copy(unit, addedBy, parent=ul, **kwargs)
        return ul

    def save_resolution(self, lesson):
        'save new lesson as resolution for this error model UL'
        if not self.lesson.concept or self.kind != self.MISUNDERSTANDS:
            raise ValueError('not an error model!')
        lesson.save_root(self.lesson.concept,
                         ConceptLink.RESOLVES)  # link as resolution
        return self.__class__.create_from_lesson(lesson, self.unit,
                                                 kind=UnitLesson.RESOLVES, parent=self,
                                                 addAnswer=True)

    def copy_resolution(self, ul, addedBy):
        'copy existing UL as resolution for this error model UL'
        try:  # already added?
            return self.unitlesson_set.get(treeID=ul.treeID,
                                           kind=UnitLesson.RESOLVES)
        except UnitLesson.DoesNotExist:
            return ul.copy(self.unit, addedBy, self, kind=UnitLesson.RESOLVES)

    def get_url(self, basePath, forceDefault=False, subpath=None,
                isTeach=True):
        'get URL path for this UL'
        pathDict = {IS_ERROR: ('errors', ''),
                    IS_CONCEPT: ('concepts', 'lessons/'),
                    IS_LESSON: ('lessons', ''), }
        if forceDefault:
            head, tail = pathDict[IS_LESSON]
        else:
            head, tail = pathDict[self.get_type()]
        if subpath:  # apply non-default subpath
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

    def get_study_url(self, course_id):
        'return URL for student to read lesson or answer question'
        if self.lesson.kind == Lesson.ORCT_QUESTION:
            path = 'ct:ul_respond'
        else:
            path = 'ct:lesson'
        return reverse(path, args=(course_id, self.unit.pk, self.pk))

    def is_question(self):
        'is this a question?'
        return self.lesson.kind in [Lesson.ORCT_QUESTION, Lesson.MULTIPLE_CHOICES]

    def question_faq_updates(self, last_access_time: datetime, user: User) -> 'QuerySet[Response]':
        """
        Count new Question FAQ updates.

        Params:
        :last_access_time: timezone aware datetime object
        :user: current chat User
        """
        return Response.objects.filter(
            kind=Response.STUDENT_QUESTION,
            atime__gt=last_access_time,
            unitLesson__id=self.id).exclude(author=user)

    def answer_faq_updates(self, last_access_time: datetime, user: User) -> 'QuerySet[Response]':
        """
        Count new Answer FAQ updates.

        Params:
        :last_access_time: timezone aware datetime object
        :user: current chat User
        """
        answer = self.get_answers().first()

        return Response.objects.filter(
            kind=Response.STUDENT_QUESTION,
            atime__gt=last_access_time,
            unitLesson__id=answer.id).exclude(author=user) if answer else Response.objects.none()

    def question_faq_comment_updates(self, last_access_time: datetime, user: User) -> 'QuerySet[Response]':
        """
        Count Question FAQ updates.

        Params:
        :last_access_time: timezone aware datetime object
        :user: current chat User
        """
        return Response.objects.filter(
            kind=Response.COMMENT,
            atime__gt=last_access_time,
            unitLesson__id=self.id).exclude(author=user)

    def answer_faq_comment_updates(self, last_access_time: datetime, user: User) -> 'QuerySet[Response]':
        """
        Count Answer FAQ updates.

        Params:
        :last_access_time: timezone aware datetime object
        :user: current chat User
        """
        answer = self.get_answers().first()

        if not answer:
            return Response.objects.none()

        tracked_faqs = answer.response_set.filter(
            Q(
                kind=Response.STUDENT_QUESTION, inquirycount__addedBy=user
            ) | Q(author=user, kind=Response.STUDENT_QUESTION))

        return Response.objects.filter(
            kind=Response.COMMENT,
            atime__gt=last_access_time,
            parent__in=tracked_faqs,
            unitLesson__id=answer.id).exclude(author=user)

    def em_updates(self, last_access_time: datetime) -> 'QuerySet[UnitLesson]':
        """
        Count all new EMs.

        Params:

        :last_access_time: timezone aware datetime object
        """
        return self.unitlesson_set.filter(
            kind=self.MISUNDERSTANDS, atime__gt=last_access_time
        )

    def em_resolutions(
            self, last_access_time: datetime,
            error_models: '[UnitLesson]' = None) -> '{UnitLesson: [QuerySet[UnitLesson]]}':
        """
        Collect new EMs resolutions.

        :last_access_time: timezone aware datetime object
        :error_models: misconceptions Student fall into
        """
        def get_new_resolutions(em: UnitLesson) -> 'QuerySet[UnitLesson]':
            return em.unitlesson_set.filter(
                kind=self.RESOLVES, atime__gt=last_access_time)

        thread_ems = error_models or self.get_errors()

        return [
            {
                'em_id': em.id,
                'em_title': em.lesson.title,
                'em_text': em.lesson.text,
                'resolutions': [
                    {
                        'id': resolution.id,
                        'title': resolution.lesson.title,
                        'text': resolution.lesson.text
                    } for resolution in get_new_resolutions(em)
                ]
            } for em in thread_ems if get_new_resolutions(em).exists()
        ]

    def faq_answers(
            self, last_access_time: datetime, user: User,
            faqs: '[Response]' = None) -> '{Response: [QuerySet[Response]]}':
        """
        Collect new FAQs comments in form of dictionary.

        Params:
        :last_access_time: timezone aware datetime object
        :faqs: all FAQs Student intereested in
        :user: current user
        """
        tracked_faqs = faqs or self.response_set.filter(kind=Response.COMMENT)

        return [
            {
                'faq_id': faq.id,
                'faq_title': faq.title,
                'faq_text': faq.text,
                'answers': [
                    {
                        'id': answer.id,
                        'title': answer.title,
                        'text': answer.text
                    } for answer in faq.response_set.filter(
                        kind=Response.COMMENT, atime__gt=last_access_time).exclude(author=user)
                ]
            } for faq in tracked_faqs if faq.response_set.filter(
                kind=Response.COMMENT, atime__gt=last_access_time).exclude(author=user).exists()
        ]

    def new_ems(self, last_access_time: datetime) -> '[{}]':
        """
        Collect new EMs based on last access time.

        Params:
        :last_access_time: timezone aware datetime object
        """
        return [
            {
                'em_id': em.id,
                'em_title': em.lesson.title
            } for em in self.em_updates(last_access_time)
        ]

    def new_faqs(self, last_access_time: datetime, user: User) -> '[{}]':
        """
        Collect new FAQ based on last access time.

        Params:
        :last_access_time: timezone aware datetime object
        :user: current user
        """
        return [
            {
                'faq_id': faq.id,
                'faq_title': faq.title,
                'faq_text': faq.text
            } for faq in self.answer_faq_updates(last_access_time, user)
        ]

    def em_resolutions_updates(
            self, last_access_time: datetime,
            error_models: '[UnitLesson]' = None) -> '{UnitLesson: [QuerySet[UnitLesson]]}':
        """
        Count new resolution for all EMs for a given Thread.

        Params:
        :last_access_time: timezone aware datetime object
        :error_models: misconceptions Student fall into
        """
        def get_new_resolutions(em: UnitLesson) -> 'QuerySet[UnitLesson]':
            return em.unitlesson_set.filter(
                kind=self.RESOLVES, atime__gt=last_access_time)

        thread_ems = error_models or self.get_errors()
        return [get_new_resolutions(em) for em in thread_ems]

    def em_resolutions_updates_count(self, last_access_time: datetime) -> int:
        """
        Incapsulates counting logic.
        """
        return reduce(operator.add, [emr.count() for emr in self.em_resolutions_updates(last_access_time)], 0)

    def updates_count(self, chat) -> int:
        """
        Currently Thread updates count.
        """
        context = c_chat_context().find_one({"chat_id": chat.id})
        last_access_time = context.get('activity', {}).get(f"{self.id}") if context else None

        tz_aware_datetime = (
            last_access_time.replace(tzinfo=tz.tzutc()) if last_access_time else
            chat.last_modify_timestamp.replace(tzinfo=tz.tzutc()))
        user = chat.user

        return reduce(operator.add, [
            self.answer_faq_updates(tz_aware_datetime, user).count(),
            self.em_resolutions_updates_count(tz_aware_datetime),
            self.em_updates(tz_aware_datetime).count(),
            self.answer_faq_comment_updates(tz_aware_datetime, user).count(),
        ], 0) if tz_aware_datetime else 0


def reorder_exercise(self, old=0, new=0, l=()):
    """
    Renumber exercises to move an exercise from old -> new position

    Can be used to reorder all list of Lesson's(UnitLesson's).
    """
    if not l:
        l = self.get_exercises()
    if not l:  # no lessons, so nothing to do
        return l
    ex = l[old]  # select desired exercise by old position
    l = l[:old] + l[old + 1:]  # exclude this exercise
    l = l[:new] + [ex] + l[new:]  # insert ex in new position
    for i, ex in enumerate(l):
        if i != ex.order:  # order changed, have to update
            ex.order = i
            ex.save()
    return l  # hand back the reordered list


class Unit(models.Model):
    """
    A container of exercises performed together.
    """
    ALLOWED_FIELDS = (
        'exam_name',
        'follow_up_assessment_date',
        'follow_up_assessment_grade',
        'question_parts',
        'average_score',
        'graded_assessment_value',
        'graded_assessment_datetime',
        'courselet_deadline',
        'courselet_days',
        'error_resolution_days',
        'courselet_completion_credit',
        'late_completion_penalty'
    )
    COURSELET = 'unit'
    LIVE_SESSION = 'live'
    RESOLUTION = 'resol'
    KIND_CHOICES = (
        (COURSELET, 'Courselet'),
        (LIVE_SESSION, 'Live session'),
        (RESOLUTION, 'Resolutions for an error model'),
    )
    PRACTICE = 'practice'
    PREREQ = 'prereq'
    MISSIN_TRAINING = 'mission'
    IN_CLASS = 'in_class'
    BP_CHOICES = (
        (PRACTICE, 'Practice-exam'),
        (PREREQ, 'Prereq inventory'),
        (MISSIN_TRAINING, 'Mission training'),
        (IN_CLASS, 'In-class'),
    )
    title = models.CharField(
        blank=True,
        max_length=200,
        help_text='Your students will see this, so give your courselet a descriptive name.',
        validators=[not_only_spaces_validator]
    )
    kind = models.CharField(max_length=10, choices=KIND_CHOICES,
                            default=COURSELET)
    atime = models.DateTimeField('time created', default=timezone.now)
    addedBy = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    img_url = models.URLField(blank=True)
    small_img_url = models.URLField(blank=True)
    is_show_will_learn = models.BooleanField(default=False)
    exam_name = models.CharField(max_length=30, blank=True, default='Midterm 1')
    follow_up_assessment_date = models.DateField(blank=True, null=True)
    follow_up_assessment_grade = models.IntegerField(default=15, blank=True, null=True, validators=[percent_validator])
    question_parts = models.IntegerField(blank=True, null=True, validators=[percent_validator])
    average_score = models.IntegerField(blank=True, null=True, validators=[percent_validator])
    graded_assessment_value = models.IntegerField(default=15, blank=True, null=True, validators=[percent_validator])
    graded_assessment_datetime = models.DateField(blank=True, null=True)
    courselet_deadline = models.DateField(blank=True, null=True)
    courselet_days = models.IntegerField(blank=True, null=True, help_text="2")
    error_resolution_days = models.IntegerField(blank=True, null=True)
    courselet_completion_credit = models.IntegerField(default=5, blank=True, null=True, validators=[percent_validator])
    late_completion_penalty = models.IntegerField(default=50, blank=True, null=True, validators=[percent_validator])

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

    def all_orct(self):
        """
        Return all ORCT objects.
        """
        return self.unitlesson_set.filter(order__isnull=False,
                                          lesson__kind=Lesson.ORCT_QUESTION)

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

    def get_related_concepts(self):
        'get dict of concepts linked to lessons in this unit'
        d = {}

        for ul in self.unitlesson_set.filter(lesson__concept__isnull=False,
                                             kind=UnitLesson.COMPONENT):
            cl = ConceptLink(lesson=ul.lesson, concept=ul.lesson.concept)
            cl.unitLesson = ul
            d[cl.concept] = [cl]

        # TODO need to decide how to remove Concepts correctly
        for cld in ConceptLink.objects.filter(
            lesson__unitlesson__unit=self,
            concept__isError=False,
            lesson__unitlesson__kind=UnitLesson.COMPONENT,
            concept__lesson__unitlesson__isnull=False
        ).values('concept', 'relationship', 'lesson__unitlesson'):
            concept = Concept.objects.get(pk=cld['concept'])
            ul = UnitLesson.objects.get(pk=cld['lesson__unitlesson'])
            cl = ConceptLink(concept=concept,
                             relationship=cld['relationship'])
            cl.unitLesson = ul
            d.setdefault(cl.concept, []).append(cl)
        return d

    def get_exercises(self, _filter=None):
        'ordered list of lessons for this courselet'
        _filter = _filter or {}
        return list(self.unitlesson_set.filter(order__isnull=False, **_filter)
                    .order_by('order'))

    reorder_exercise = reorder_exercise

    def get_aborts(self):
        'get query set with errors + generic ABORT, FAIL errors'
        aborts = list(self.unitlesson_set
                      .filter(kind=UnitLesson.MISUNDERSTANDS, parent__isnull=True))
        if not aborts:  # need to add ABORTs etc. to this unit
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
                               .filter(lesson__kind=Lesson.ORCT_QUESTION, **kwargs)
                               .exclude(unitlesson__kind=UnitLesson.MISUNDERSTANDS))

    def get_resoless_uls(self, **kwargs):
        return distinct_subset(
            self.unitlesson_set.filter(
                Q(
                    unitlesson__kind=UnitLesson.MISUNDERSTANDS,
                    **kwargs
                ) & ~Q(
                    unitlesson__lesson__concept__conceptlink__relationship=ConceptLink.RESOLVES
                )))

    def get_unanswered_uls(self, user=None, **kwargs):
        if user:
            kwargs['response__author'] = user
        return distinct_subset(self.unitlesson_set
                               .filter(kind=UnitLesson.COMPONENT, order__isnull=False,
                                       lesson__kind=Lesson.ORCT_QUESTION)
                               .exclude(response__kind=Response.ORCT_RESPONSE, **kwargs))

    def get_selfeval_uls(self, user=None, **kwargs):
        if user:
            kwargs['response__author'] = user
        else:  # ensure it finds Response
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
                               .filter(
                                   response__studenterror__status__in=[NEED_HELP_STATUS, NEED_REVIEW_STATUS],
                                   **kwargs))

    def get_study_url(self, path, extension=['tasks']):
        'return URL for next study tasks on this unit'
        from ct.templatetags.ct_extras import get_base_url
        return get_base_url(path, extension)

    def append(self, ul, user):
        'append unitLesson to main lesson sequence'
        if ul.unit == self:
            if ul.order is None:  # add to tail
                ul.order = self.unitlesson_set.filter(order__isnull=False).count()
                ul.save()
                self.reorder_exercise()
            return ul
        else:  # not in this unit so copy
            return ul.copy(self, user, order='APPEND')

    def apply_from(self, data: dict, commit=False):
        assert isinstance(data, dict)
        assert hasattr(self, 'ALLOWED_FIELDS')
        for key, value in data.items():
            setattr(self, key, value) if key in self.ALLOWED_FIELDS else None
        self.save() if commit else None
        return self

    @property
    def scheduled(self):
        return (
            self.graded_assessment_datetime and self.courselet_deadline and self.error_resolution_days and
            self.graded_assessment_datetime > self.courselet_deadline
        )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.courselet_deadline and self.graded_assessment_datetime and self.error_resolution_days:
            self.courselet_deadline = self.graded_assessment_datetime - timedelta(self.error_resolution_days)
        super().save(*args, **kwargs)


############################################################
# student response and error data

def fmt_count(c, n):
    return '%.0f%% (%d)' % (c * 100. / n, c)


class CountsTable(object):
    'simple holder for one row of pretty-printed counts w/ headings & title'

    def __init__(self, title, choices, n, countDict):
        self.title = title
        self.headings = []
        counts = []
        for k, heading in choices:
            self.headings.append(heading)
            counts.append(countDict.get(k, 0))
        self.headings.append('(not yet)')
        total = sum(counts)
        if total > 0:
            counts.append(n - total)
            self.data = [fmt_count(i, n) for i in counts]
        else:
            self.data = ()

    def __len__(self):
        return len(self.data)


NEED_HELP_STATUS = 'help'
NEED_REVIEW_STATUS = 'review'
DONE_STATUS = 'done'
STATUS_CHOICES = (
    (NEED_HELP_STATUS, 'Still confused, need help'),
    (NEED_REVIEW_STATUS, 'OK, but flag this for me to review'),
    (DONE_STATUS, 'Solidly'),
)
STATUS_TABLE_LABELS = (
    (NEED_HELP_STATUS, 'Still confused, need help'),
    (NEED_REVIEW_STATUS, 'OK, but need review'),
    (DONE_STATUS, 'Solid understanding'),
)


class ResponseManager(models.Manager):
    '''
    Manager for Response model which will return by default Response's with field is_test equals to False
    To get test responses (marked with flag is_test=True) you should use method test_responses,
    which will return only test responses.
    '''

    # return ONLY valuable responses
    def get_queryset(self, **kwargs):
        return super().get_queryset().filter(
            is_preview=False, **kwargs
        )

    def get_all_responses_queryset(self, **kwargs):
        """Return new queryset to filter all responses, not only valuable."""
        return self._queryset_class(model=self.model, using=self._db, hints=self._hints)

    def all_all(self):
        """Return all responses."""
        return self.get_all_responses_queryset().all()

    def filter_all(self, **kwargs):
        """Filter all responses."""
        return self.get_all_responses_queryset().filter(**kwargs)

    def test_responses(self, **kwargs):
        '''
        Return only test responses marked with flag is_test=True
        :return:
        '''
        return super().get_queryset().filter(is_test=True, **kwargs)

    def preview_responses(self, **kwargs):
        '''
        Return only test responses marked with flag is_test=True
        :return:
        '''
        return super().get_queryset().filter(is_preview=True, **kwargs)


class Response(models.Model, SubKindMixin):
    'answer entered by a student in response to a question'
    ORCT_RESPONSE = 'orct'
    STUDENT_QUESTION = 'sq'
    COMMENT = 'comment'

    KIND_CHOICES = (
        (ORCT_RESPONSE, 'ORCT response'),
        (STUDENT_QUESTION, 'Question about a lesson'),
        (COMMENT, 'Reply comment'),
    )

    # new interactions
    SUB_KIND_CHOICES = (
        (SubKindMixin.MULTIPLE_CHOICES, 'Multiple Choices response'),
        (SubKindMixin.NUMBERS, 'Numbers response'),
        (SubKindMixin.EQUATION, 'Equation response'),
        (SubKindMixin.CANVAS, 'Canvas response'),
    )
    CORRECT = 'correct'
    CLOSE = 'close'
    DIFFERENT = 'different'
    EVAL_CHOICES = (
        (DIFFERENT, 'Different'),
        (CLOSE, 'Close'),
        (CORRECT, 'Essentially the same'),
    )
    GUESS = 'guess'  # chosen for sort order g < n < s
    UNSURE = 'notsure'
    SURE = 'sure'
    CONF_CHOICES = (
        (GUESS, 'Just guessing'),
        (UNSURE, 'Not quite sure'),
        (SURE, 'Pretty sure'),
    )
    SELFEVAL_STEP = 'assess'
    CLASSIFY_STEP = 'errors'
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)  # exact version this applies to
    unitLesson = models.ForeignKey(UnitLesson, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES,
                            default=ORCT_RESPONSE)

    # test, preview flags
    is_test = models.BooleanField(default=False)
    is_preview = models.BooleanField(default=False)

    sub_kind = models.CharField(max_length=10, choices=SUB_KIND_CHOICES, blank=True, null=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    text = models.TextField()
    attachment = models.FileField(null=True, blank=True, upload_to='answers')

    confidence = models.CharField(max_length=10, choices=CONF_CHOICES,
                                  blank=False, null=False)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    selfeval = models.CharField(max_length=10, choices=EVAL_CHOICES,
                                blank=False, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES,
                              blank=False, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    needsEval = models.BooleanField(default=False)
    parent = models.ForeignKey('Response', null=True, blank=True, on_delete=models.CASCADE)  # reply-to
    activity = models.ForeignKey('fsm.ActivityLog', null=True, blank=True, on_delete=models.CASCADE)
    faq_notified = models.BooleanField(blank=True, null=True, default=False)
    is_locked = models.BooleanField(default=False)
    is_trial = models.BooleanField(default=False)

    objects = ResponseManager()

    def __str__(self):
        return 'answer by ' + self.author.username

    @property
    def faq_affected_studets(self):
        """
        Return all affected user.
        """
        return self.inquirycount_set.count() + 1

    @property
    def completed_faq(self):
        """
        Determine a completed state for the FAQ.

        FAQ must have the text.
        """
        return self.kind == self.STUDENT_QUESTION and self.title and self.text

    def notify_instructors(self):
        """
        Notify all Instructors with a newly created FAQ and new Inquiry.
        """
        # Do not send notifications about test or preview FAQs
        if self.is_preview or self.is_test:
            return
        if self.completed_faq and not self.faq_notified and self.faq_affected_studets >= self.course.faq_threshold:
            # TODO change to general logic when EMs faq notification will be implemented
            url = reverse(
                'ct:ul_thread',
                kwargs={
                    'course_id': self.course.id,
                    'unit_id': self.unitLesson.unit.id,
                    'ul_id': self.unitLesson.id,
                    'resp_id': self.id
                }
            )
            domain = 'https://{0}'.format(Site.objects.get_current().domain)
            faq_notify_instructors.delay(
                faq_link=domain + url,
                faq_title=self.title.strip(),
                faq_text=self.text,
                course_title=self.course.title,
                courselet_title=self.unitLesson.unit.title.strip(),
                instructors=[i.email for i in self.course.instructors if i.email])
            # TODO move to the task
            self.faq_notified = True
            self.save()

    def notify_students(self):
        """
        Notify Students with a new FAQ comment.
        """
        # Do not send notifications about test or preview FAQs
        if self.is_preview or self.is_test:
            return
        if self.kind == self.COMMENT:
            url = reverse(
                'ct:ul_thread_student',
                kwargs={
                    'course_id': self.course.id,
                    'unit_id': self.unitLesson.unit.id,
                    'ul_id': self.unitLesson.id,
                    'resp_id': self.parent.id
                }
            )
            domain = 'https://{0}'.format(Site.objects.get_current().domain)
            faq_notify_students.delay(
                faq_link=domain + url,
                faq_title=self.title.strip(),
                faq_text=self.text,
                course_title=self.course.title,
                courselet_title=self.unitLesson.unit.title,
                parent_faq_title=self.parent.title.strip(),
                students=[self.parent.author.email] + [i.addedBy.email for i in
                                                       self.parent.inquirycount_set.all() if i.addedBy.email]
            )

    def get_canvas_html(self):
        """
        Returns container for drawing
        """
        return render_to_string('ct/lesson/response_sub_kind_canvas.html', context={
            'response': self,
            'canvas': self.attachment,
        })

    @classmethod
    def get_counts(klass, query, fmt_count=fmt_count, n=0, tableKey='status',
                   simpleTable=False,
                   title='Student Status for Understanding This Lesson'):
        'generate display tables for Response data'
        querySet = klass.objects.filter(query)
        statusDict = {}
        for d in querySet.values(tableKey).annotate(dcount=Count(tableKey)):
            statusDict[d[tableKey]] = d['dcount']
        if not n:
            n = querySet.count()
        if not n:  # prevent DivideByZero
            return (), (), 0
        choices = dict(status=STATUS_TABLE_LABELS,
                       confidence=klass.CONF_CHOICES)[tableKey]
        statusTable = CountsTable(title, choices, n, statusDict)
        if simpleTable:  # caller only wants statusTable
            return statusTable, n, None
        evalDict = {}
        for d in querySet.values('confidence', 'selfeval') \
                .annotate(dcount=Count('confidence')):
            evalDict[d['confidence'], d['selfeval']] = d['dcount']
        l = []
        for conf, label in klass.CONF_CHOICES:
            l.append((label, [fmt_count(evalDict.get((conf, selfeval), 0), n)
                              for selfeval, _ in klass.EVAL_CHOICES]))
        return statusTable, l, n

    @classmethod
    def get_novel_errors(klass, unitLesson=None, query=None,
                         selfeval=DIFFERENT, **kwargs):
        'get wrong responses with no StudentError classification'
        if not query:
            if not unitLesson:
                raise ValueError('no query and no unitLesson?!?')
            query = Q(unitLesson=unitLesson)
        return klass.objects.filter(query & Q(selfeval=selfeval, studenterror__isnull=True), **kwargs)

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

    def show_my_choices(self):
        if self.sub_kind != 'choices':
            raise ValueError('Response.sub_kind should be choices to call this function')

        available_choices = dict(self.lesson.get_choices())
        split_selected_choices = self.text.split('[selected_choices] ')
        if len(split_selected_choices) > 1:
            selected_choices = split_selected_choices[1]
            return "\r\n".join([
                available_choices.get(int(i), "")
                for i in selected_choices
                if str.isdigit(i)
            ])
        return ""


EVAL_TO_STATUS_MAP = {
    Response.DIFFERENT: NEED_HELP_STATUS,
    Response.CLOSE: NEED_REVIEW_STATUS,
    Response.CORRECT: DONE_STATUS
}


class StudentError(models.Model):
    'identification of a specific error model made by a student'
    response = models.ForeignKey(Response, on_delete=models.CASCADE)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    errorModel = models.ForeignKey(UnitLesson, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES,
                              blank=False, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.ForeignKey('fsm.ActivityLog', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return 'eval by ' + self.author.username

    @classmethod
    def get_counts(klass, query, n, fmt_count=fmt_count):
        'generate display table for StudentError data'
        querySet = klass.objects.filter(query)
        l = []
        for d in querySet.values('errorModel') \
                .annotate(c=Count('errorModel')):
            l.append((UnitLesson.objects.get(pk=d['errorModel']), d['c']))
        l.sort(key=lambda x: x[1], reverse=True)
        return [(t[0], fmt_count(t[1], n)) for t in l]

    @classmethod
    def get_ul_errors(klass, ul, **kwargs):
        'get StudentErrors for a specific question'
        return klass.objects.filter(response__unitLesson=ul, **kwargs)


def errormodel_table(target, n, fmt='%d (%.0f%%)', includeAll=False, attr=''):
    if n == 0:  # prevent div by zero error
        n = 1
    kwargs = {'kind': Lesson.MISUNDERSTANDS, 'parent': target}
    l = []
    for em in UnitLesson.objects.filter(**kwargs):
        kwargs = {'errorModel': em}
        nse = StudentError.objects.filter(**kwargs).count()
        if nse > 0 or includeAll:
            l.append((em, nse))
    l.sort(key=lambda x: x[1], reverse=True)
    fmt_count = lambda c: fmt % (c, c * 100. / n)
    return [(t[0], fmt_count(t[1])) for t in l]


class InquiryCount(models.Model):
    'record users who have the same question'
    response = models.ForeignKey(Response, on_delete=models.CASCADE)
    addedBy = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES,
                              blank=False, null=True)
    atime = models.DateTimeField('time submitted', default=timezone.now)

    def __str__(self):
        return '{} {} {}'.format(self.response.title, self.addedBy, self.status)


class Liked(models.Model):
    'record users who found UnitLesson showed them something they were missing'
    unitLesson = models.ForeignKey(UnitLesson, on_delete=models.CASCADE)
    addedBy = models.ForeignKey(User, on_delete=models.CASCADE)
    atime = models.DateTimeField('time submitted', default=timezone.now)

    class Meta:
        verbose_name_plural = 'Likes'


class FAQ(models.Model):
    'link a student inquiry to a follow-up lesson'
    response = models.ForeignKey(Response, on_delete=models.CASCADE)
    unitLesson = models.ForeignKey(UnitLesson, on_delete=models.CASCADE)
    addedBy = models.ForeignKey(User, on_delete=models.CASCADE)
    atime = models.DateTimeField('time submitted', default=timezone.now)


#######################################
# Course and membership info

class Course(models.Model):
    """
    Top-level (enrollment) container.
    """
    ALLOWED_FIELDS = ('students_number', 'misconceptions_per_day')
    ACCESS_CHOICES = (
        (PUBLIC_ACCESS, 'Public'),
        (INSTRUCTOR_ENROLLED, 'By instructors only'),
        (PRIVATE_ACCESS, 'By author only'),
    )
    FSM_CHOICES = (
        (DEFAULT_FSM, 'Default FSM flow'),
        (TRIAL_FSM, 'Trial FSM flow - ABORTS before Student answer'),
    )
    title = models.CharField(
        max_length=200,
        validators=[not_only_spaces_validator]
    )
    description = models.TextField()
    access = models.CharField(max_length=10, choices=ACCESS_CHOICES,
                              default=PUBLIC_ACCESS)
    enrollCode = models.CharField(max_length=64, null=True, blank=True)
    lockout = models.CharField(max_length=200, null=True, blank=True)
    addedBy = models.ForeignKey(User, on_delete=models.CASCADE)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    faq_threshold = models.PositiveIntegerField(blank=False, null=False, default=1)

    copied_from = models.ForeignKey('Course', blank=True, null=True, on_delete=models.CASCADE)
    trial = models.BooleanField(default=False)
    FSM_flow = models.CharField(max_length=10, choices=FSM_CHOICES,
                                default=DEFAULT_FSM)
    students_number = models.PositiveIntegerField(blank=True, null=True, default=200)
    misconceptions_per_day = models.PositiveIntegerField(blank=True, null=True, default=5)
    best_practice1 = models.ForeignKey('ctms.BestPractice1', blank=True, null=True, on_delete=models.CASCADE)

    def deep_clone(self, **options):
        publish = options.get('publish', False)
        with_students = options.get('with_students', False)
        asis = options.get('asis', False)
        title = self.title.split('copied')[0] + " copied {}".format(
            timezone.now().astimezone(timezone.get_default_timezone())
        )

        new_course = copy_model_instance(
            self,
            atime=timezone.now(),
            title=title,
            copied_from=self
        )
        for cu in self.courseunit_set.all():
            # deal with Unit
            n_unit = copy_model_instance(cu.unit, atime=timezone.now())
            # deal with CourseUnit
            n_cu_kw = dict(
                course=new_course,
                unit=n_unit,
                atime=timezone.now(),
                releaseTime=timezone.now()
            )
            if not publish:
                n_cu_kw['releaseTime'] = None
            if asis:
                # if copy as is - remove release time from kw. it will be the same as in source obj.
                del n_cu_kw['releaseTime']

            n_cu = copy_model_instance(cu, **n_cu_kw)

            uls = list(cu.unit.get_exercises())
            # copy exercises and error models
            for ul in uls:
                n_ul = ul.copy(unit=n_unit, addedBy=ul.addedBy)

            # copy resources
            for ul in list(cu.unit.unitlesson_set.filter(kind=UnitLesson.COMPONENT, order__isnull=True)):
                n_ul = ul.copy(unit=n_unit, addedBy=ul.addedBy)
                n_unit.reorder_exercise()
        roles_to_copy = [
                            r[0] for r in Role.ROLE_CHOICES
                            if r[0] != Role.ENROLLED
                        ] + ([Role.ENROLLED] if with_students else [])
        for role in self.role_set.filter(role__in=roles_to_copy):
            n_role = copy_model_instance(role, course=new_course, atime=timezone.now())
        return new_course

    def create_unit(self, title, description=None, img_url=None, small_img_url=None, author=None):
        if author is None:
            author = self.addedBy
        unit = Unit(
            title=title,
            addedBy=author,
            description=description,
            img_url=img_url,
            small_img_url=small_img_url
        )
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
        if publishedOnly:  # only those already released
            return list(self.courseunit_set
                        .filter(releaseTime__isnull=False,
                                releaseTime__lt=timezone.now()).order_by('order'))
        else:
            return list(self.courseunit_set.all().order_by('order'))

    reorder_course_unit = reorder_exercise

    def get_users(self, role=None):
        if not role:
            role = Role.INSTRUCTOR
        return User.objects.filter(role__role=role, role__course=self)

    @property
    def instructors(self):
        return self.get_users(role=Role.INSTRUCTOR)

    @property
    def students(self):
        return self.get_users(role=Role.ENROLLED)

    def apply_from(self, data: dict, commit=False):
        assert isinstance(data, dict)
        for key, value in data.items():
            setattr(self, key, value) if key in self.ALLOWED_FIELDS else None
        self.save() if commit else None
        return self

    def __str__(self):
        return self.title


class CourseUnit(models.Model):
    '''list of units in a course'''
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    order = models.IntegerField()
    addedBy = models.ForeignKey(User, on_delete=models.CASCADE)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    releaseTime = models.DateTimeField('time released', null=True, blank=True)

    def is_published(self):
        return self.releaseTime and self.releaseTime < timezone.now()

    def __str__(self):
        return "Course - {}, Unit - {}".format(self.course.title, self.unit.title)

    def get_responses(self):
        return Response.objects.filter(
            unitLesson__unit=self.unit,
            kind=Response.ORCT_RESPONSE,
            course=self.course,
        )


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
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    trial_mode = models.NullBooleanField()

    class Meta:
        unique_together = ('role', 'course', 'user')


class UnitStatus(models.Model):
    'records what user has completed in a unit lesson sequence'
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    startTime = models.DateTimeField('time started', default=timezone.now)
    endTime = models.DateTimeField('time ended', null=True)
    order = models.IntegerField(default=0)  # index of current UL

    @classmethod
    def get_or_none(klass, unit, user, latest=False, **kwargs):
        try:
            query = klass.objects.filter(unit=unit, user=user, **kwargs)
            if latest:
                query = query.order_by('-startTime')
            return query[0]
        except IndexError:
            return None

    @classmethod
    def is_done(klass, unit, user):
        return klass.get_or_none(unit, user, endTime__isnull=False)

    def get_lesson(self):
        'get the current lesson'
        return self.unit.unitlesson_set.get(order=self.order)

    def get_next_lesson(self):
        return self.unit.unitlesson_set.filter(order=self.order + 1).first()

    def set_lesson(self, ul):
        'advance to specified lesson, but prevent skipping on first run'
        if ul.order > self.order:
            if not self.endTime and ul.order > self.order + 1:
                return self.start_next_lesson()  # prevent skipping ahead
            self.order = ul.order
            self.save()
        return ul

    def done(self):
        'reset to start of sequence, and set endTime if not already'
        self.order = 0  # reset in case user wants to repeat
        if not self.endTime:
            self.endTime = timezone.now()  # mark as done
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


@receiver(post_save, sender=Course)
def onboarding_course_created(sender, instance, **kwargs):
    update_onboarding_step(onboarding.STEP_3, instance.addedBy.id)


@receiver(post_save, sender=Unit)
def onboarding_unit_created(sender, instance, **kwargs):
    update_onboarding_step(onboarding.STEP_4, instance.addedBy.id)


@receiver(post_save, sender=Lesson)
def onboarding_lesson_created(sender, instance, created, **kwargs):
    if instance.kind in (Lesson.ANSWER, Lesson.BASE_EXPLANATION, Lesson.EXPLANATION):
        update_onboarding_step(onboarding.STEP_5, instance.addedBy.id)
    if created and instance.kind == Lesson.ORCT_QUESTION:
        orct_count = Lesson.objects.filter(addedBy=instance.addedBy, kind=Lesson.ORCT_QUESTION).count()
        create_intercom_event(
            event_name='orct-created',
            created_at=int(time.mktime(time.localtime())),
            email=instance.addedBy.email,
            metadata={'ORCT written': orct_count}
        )
