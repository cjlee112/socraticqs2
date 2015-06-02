from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.db.models import Q, Count, Max
import glob
import json
import ct_util


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
    _sourceDBdict = {}
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

    _cloneAttrs = ('title', 'text', 'data', 'url', 'kind', 'medium', 'access',
                   'sourceDB', 'sourceID', 'concept', 'treeID')

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
            return klass.objects.get(sourceDB=sourceDB, sourceID=sourceID)
        except klass.DoesNotExist:
            pass
        dataClass = klass.get_sourceDB_plugin(sourceDB)
        data = dataClass(sourceID)
        try: # attribute authorship to the sourceDB
            user = User.objects.get(username=sourceDB)
        except User.DoesNotExist:
            pass
        lesson = klass(title=data.title, url=data.url, sourceDB=sourceDB,
                       sourceID=sourceID, addedBy=user, text=data.description,
                       kind=klass.EXPLANATION, commitTime=timezone.now(),
                       changeLog='initial text from %s' % sourceDB)
        if doSave: # not just temporary, but save as permanent record
            lesson.save_root()
        lesson._sourceDBdata = data
        return lesson

    @classmethod
    def search_sourceDB(klass, query, sourceDB='wikipedia', **kwargs):
        'get [(title, sourceID, url)] for query from sourceDB using plugin'
        dataClass = klass.get_sourceDB_plugin(sourceDB)
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
    def is_committed(self):
        'True if already committed'
        return self.commitTime is not None
    def _clone_dict(self):
        'get dict of attrs to clone'
        kwargs = {}
        for attr in self._cloneAttrs: # clone our attributes
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
    LESSON_ROLE = 'lesson'
    RESOURCE_ROLE = 'resource'
    ROLE_CHOICES = (
        (LESSON_ROLE, "Show this lesson to all students as part of the courselet's main lesson sequence"),
        (RESOURCE_ROLE, "Just list this as a follow-up study resource")
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
            try: # use UL from this unit if any
                resultsUL.append(hits[0])
            except IndexError:
                hits = klass.objects.filter(**queryArgs)
                try: # otherwise use any UL matching this sourceID
                    resultsUL.append(hits[0])
                except IndexError: # no UL so just return tuple
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
        return em, self.unitlesson_set.filter(kind=self.RESOLVES)
        ## query = Q(kind=self.RESOLVES,
        ##           lesson__conceptlink__relationship=ConceptLink.RESOLVES,
        ##           lesson__conceptlink__concept=em)
        ## return em, distinct_subset(UnitLesson.objects.filter(query))
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
        if not self.lesson.is_committed(): # to fork it, must commit it!
            name = addedBy.get_full_name()
            if not name:
                name = addedBy.get_username()
            self.lesson.changeLog = 'snapshot for fork by %s' % name
            self.lesson.checkin(commit=True)
        if order == 'APPEND':
            order = unit.next_order()
        if kind == UnitLesson.RESOLVES:
            self.lesson.add_concept_link(parent.lesson.concept,
                                         ConceptLink.RESOLVES, addedBy)
        elif kind is None:
            kind = self.kind
        ul = self.__class__(lesson=self.lesson, addedBy=addedBy, unit=unit,
                            kind=kind, treeID=self.treeID, parent=parent,
                            order=order, branch=self.branch, **kwargs)
        ul.save()
        for child in self.unitlesson_set.all(): # copy children
            child.copy(unit, addedBy, parent=ul, **kwargs)
        return ul
    def save_resolution(self, lesson):
        'save new lesson as resolution for this error model UL'
        if not self.lesson.concept or self.kind != self.MISUNDERSTANDS:
            raise ValueError('not an error model!')
        lesson.save_root(self.lesson.concept,
                         ConceptLink.RESOLVES) # link as resolution
        return self.__class__.create_from_lesson(lesson, self.unit,
                                kind=UnitLesson.RESOLVES, parent=self)
    def copy_resolution(self, ul, addedBy):
        'copy existing UL as resolution for this error model UL'
        try: # already added?
            return self.unitlesson_set.get(treeID=ul.treeID,
                                           kind=UnitLesson.RESOLVES)
        except UnitLesson.DoesNotExist:
            return ul.copy(self.unit, addedBy, self, kind=UnitLesson.RESOLVES)
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
    def get_study_url(self, course_id):
        'return URL for student to read lesson or answer question'
        if self.lesson.kind == Lesson.ORCT_QUESTION:
            path = 'ct:ul_respond'
        else:
            path = 'ct:lesson'
        return reverse(path, args=(course_id, self.unit.pk, self.pk))
    def is_question(self):
        'is this a question?'
        return self.lesson.kind == Lesson.ORCT_QUESTION

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
    def get_study_url(self, path, extension=['tasks']):
        'return URL for next study tasks on this unit'
        from ct.templatetags.ct_extras import get_base_url
        return get_base_url(path, extension)
    def append(self, ul, user):
        'append unitLesson to main lesson sequence'
        if ul.unit == self:
            if ul.order is None: # add to tail
                ul.order = self.unitlesson_set.filter(order__isnull=False).count()
                ul.save()
                self.reorder_exercise()
            return ul
        else: # not in this unit so copy
            return ul.copy(self, user, order='APPEND')
    def __unicode__(self):
        return self.title

    

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
    (NEED_REVIEW_STATUS, 'OK, but need further review and practice'),
    (DONE_STATUS, 'Solidly'),
)
STATUS_TABLE_LABELS = (
    (NEED_HELP_STATUS, 'Still confused, need help'),
    (NEED_REVIEW_STATUS, 'OK, but need review'),
    (DONE_STATUS, 'Solid understanding'),
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
    title = models.CharField(max_length=200, null=True)
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
    activity = models.ForeignKey('ActivityLog', null=True)
    def __unicode__(self):
        return 'answer by ' + self.author.username
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
        if not n: # prevent DivideByZero
            return (), (), 0
        choices = dict(status=STATUS_TABLE_LABELS,
                       confidence=klass.CONF_CHOICES)[tableKey]
        statusTable = CountsTable(title, choices, n, statusDict)
        if simpleTable: # caller only wants statusTable
            return statusTable, n, None
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
    activity = models.ForeignKey('ActivityLog', null=True)
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
            return klass.objects.filter(unit=unit, user=user, **kwargs)[0]
        except IndexError:
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
    'produce tuple of form ("NAME_Response_id", o.pk)'
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

def save_json_data(self, d=None, attr='data', doSave=True):
    'save dict of object refs back to db blob field'
    dictAttr = '_%s_dict' % attr
    if d is None: # save cached data
        d = getattr(self, dictAttr)
    else: # save specified dict
        setattr(self, dictAttr, d) # cache on local object
    if d:
        s = dump_json_id_dict(d)
    else:
        s = None
    setattr(self, attr, s)
    if doSave: # immediately write to db
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
    dictAttr = '_%s_dict' % attr
    try:
        return getattr(self, dictAttr)
    except AttributeError:
        pass
    s = getattr(self, attr)
    if s:
        d = load_json_id_dict(s)
    else:
        d = {}
    setattr(self, dictAttr, d)
    return d

def set_data_attr(self, attr, v):
    '''set a single data attribute
    (must later call save_json_data() to serialize)'''
    d = self.load_json_data()
    d[attr] = v
        
def get_data_attr(self, attr):
    'get a single data attribute from json data'
    d = self.load_json_data()
    return d[attr]
    
def get_plugin(funcName, prefix='ct.fsm_plugin.'):
    'import and call plugin func for this object'
    import importlib
    if not funcName:
        raise ValueError('invalid call_plugin() with no funcName!')
    i = funcName.rindex('.')
    modName = prefix + funcName[:i]
    funcName = funcName[i + 1:]
    mod = importlib.import_module(modName)
    return  getattr(mod, funcName)
    
##################################################################
# activity stack FSM

class FSM(models.Model):
    'Finite State Machine top-level state-graph container'
    name = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True)
    help = models.TextField(null=True)
    startNode = models.ForeignKey('FSMNode', related_name='+', null=True)
    hideTabs = models.BooleanField(default=False)
    hideLinks = models.BooleanField(default=False)
    hideNav = models.BooleanField(default=False)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)
    @classmethod
    def save_graph(klass, fsmData, nodeData, edgeData, username, fsmGroups=(),
                  oldLabel='OLD'):
        '''store FSM specification from node, edge graph
        by renaming any existing
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
                for g in old.fsmgroup_set.all():
                    g.delete()
                ## old.fsmgroup_set.clear() # RelatedManager has no attribute clear
            f = klass(addedBy=user, **fsmData) # create new FSM
            f.save()
            for groupName in fsmGroups:# register in specified groups
                f.fsmgroup_set.create(group=groupName)
            nodes = {}
            for name, nodeDict in nodeData.items(): # save nodes
                node = FSMNode(name=name, fsm=f, addedBy=user, **nodeDict)
                if node.funcName: # make sure plugin imports successfully
                    get_plugin(node.funcName)
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
    def get_node(self, name):
        'get node in this FSM with specified name'
        return self.fsmnode_set.get(name=name)

class FSMGroup(models.Model):
    'groups multiple FSMs into one named UI group'
    fsm = models.ForeignKey(FSM)
    group = models.CharField(max_length=64)

    
class PluginDescriptor(object):
    'self-caching plugin access property'
    def __get__(self, obj, objtype):
        try:
            return obj._pluginData
        except AttributeError:
            if not obj.funcName:
                raise AttributeError('no plugin funcName')
            klass = get_plugin(obj.funcName)
            obj._pluginData = klass()
            return obj._pluginData
    def __set__(self, obj, val):
        raise AttributeError('read only attribute!')
            

    
class FSMNode(models.Model):
    'stores one node of an FSM state-graph'
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
    doLogging = models.BooleanField(default=False)
    load_json_data = load_json_data
    save_json_data = save_json_data
    get_data_attr = get_data_attr
    set_data_attr = set_data_attr
    _plugin = PluginDescriptor() # provide access to plugin code if any
    def event(self, fsmStack, request, eventName, **kwargs):
        'process event using plugin if available, otherwise generic processing'
        if self.funcName: # use plugin to process event
            if eventName:
                func = getattr(self._plugin, eventName + '_event', None)
            else: # let plugin intercept render event
                func = getattr(self._plugin, 'render_event', None)
            if func is not None:
                return func(self, fsmStack, request, **kwargs)
        if eventName == 'start': # default: just return our path
            return self.get_path(fsmStack.state, request, **kwargs)
        elif eventName: # default: call transition with matching name
            return fsmStack.state.transition(fsmStack, request, eventName,
                                             **kwargs)
    def get_path(self, state, request, defaultURL=None, **kwargs):
        'get URL for this page'
        if self.path and self.path.startswith('ct:fsm_'): # serve fsm node view
            return reverse(self.path, kwargs=dict(node_id=self.pk))
        try:
            func = self._plugin.get_path
        except AttributeError: # use self.path with clever reverse()
            if not self.path: # just use default path
                if defaultURL:
                    return defaultURL
                else:
                    raise ValueError('node has no path, and no defaultURL')
            kwargs.update(state.get_all_state_data()) # pass state data too
            return ct_util.reverse_path_args(self.path, request.path, **kwargs)
        else: # use the plugin
            return func(self, state, request, defaultURL=defaultURL, **kwargs)
    def get_help(self, state, request):
        'Get FSM help message for current view, if any'
        try: # use plugin if available
            func = self._plugin.get_help
        except AttributeError: # no plugin, so use default rule
            if state.fsm_on_path(request.path): # on current node view?
                return self.help # use node's help message if any
        else:
            return func(self, state, request)

class FSMDone(ValueError):
    pass
class FSMBadUserError(ValueError):
    'request.user does not match state.user'
    pass
class FSMStackResumeError(ValueError):
    pass

class FSMEdge(models.Model):
    'stores one edge of an FSM state-graph'
    name = models.CharField(max_length=64)
    fromNode = models.ForeignKey(FSMNode, related_name='outgoing')
    toNode = models.ForeignKey(FSMNode, related_name='incoming')
    title = models.CharField(max_length=200)
    description = models.TextField(null=True)
    help = models.TextField(null=True)
    showOption = models.BooleanField(default=False)
    data = models.TextField(null=True)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)
    _funcDict = {}
    load_json_data = load_json_data
    save_json_data = save_json_data
    get_data_attr = get_data_attr
    set_data_attr = set_data_attr
    def transition(self, fsmStack, request, **kwargs):
        'execute edge plugin code if any and return destination node'
        try:
            func = getattr(self.fromNode._plugin, self.name + '_edge')
        except AttributeError: # just return target node
            return self.toNode
        else:
            return func(self, fsmStack, request, **kwargs)

class FSMState(models.Model):
    'stores current state of a running FSM instance'
    user = models.ForeignKey(User)
    fsmNode = models.ForeignKey(FSMNode)
    parentState = models.ForeignKey('FSMState', null=True,
                                    related_name='children')
    linkState = models.ForeignKey('FSMState', null=True,
                                  related_name='linkChildren')
    unitLesson = models.ForeignKey(UnitLesson, null=True)
    title = models.CharField(max_length=200)
    path = models.CharField(max_length=200)
    data = models.TextField(null=True)
    hideTabs = models.BooleanField(default=False)
    hideLinks = models.BooleanField(default=False)
    hideNav = models.BooleanField(default=False)
    isLiveSession = models.BooleanField(default=False)
    atime = models.DateTimeField('time started', default=timezone.now)
    activity = models.ForeignKey('ActivityLog', null=True)
    activityEvent = models.ForeignKey('ActivityEvent', null=True)
    load_json_data = load_json_data
    save_json_data = save_json_data
    get_data_attr = get_data_attr
    set_data_attr = set_data_attr
    def get_all_state_data(self):
        'get dict of all our state data including unitLesson'
        d = self.load_json_data().copy() # copy to avoid side-effects
        if self.unitLesson:
            d['unitLesson'] = self.unitLesson
        return d
    def event(self, fsmStack, request, eventName, unitLesson=False, **kwargs):
        'trigger proper consequences if any for this event, return URL if any'
        if not eventName: # render event
            self.log_entry(request.user)
        elif unitLesson is not False: # store new lesson binding
            self.unitLesson = kwargs['unitLesson'] = unitLesson
            self.save()
        elif eventName.startswith('select_'): # store selected object
            className = eventName[7:]
            attr = className[0].lower() + className[1:]
            self.set_data_attr(attr, kwargs[attr])
            self.save_json_data()
        return self.fsmNode.event(fsmStack, request, eventName, **kwargs)
    def start_fsm(self, fsmStack, request, stateData, **kwargs):
        'initialize new FSM by calling START node and saving state data to db'
        if stateData:
            self.save_json_data(stateData, doSave=False) # cache
        self.path = self.event(fsmStack, request, 'start', **kwargs)
        self.save_json_data(doSave=False) # serialize to json blob
        self.save()
        return self.path
    def transition(self, fsmStack, request, name, **kwargs):
        'execute the specified transition and return destination URL'
        try:
            e = self.fsmNode.outgoing.get(name=name)
        except FSMEdge.DoesNotExist:
            return None # FSM does not handle this event, return control
        if self.activityEvent: # record exit from this node
            self.activityEvent.log_exit_event(name)
            self.activityEvent = None
        self.fsmNode = e.transition(fsmStack, request, **kwargs)
        self.path = self.fsmNode.get_path(self, request, **kwargs)
        self.save()
        return self.path
    def fsm_on_path(self, path):
        'True if we are on same page as current node'
        return self.path == path
    def log_entry(self, user):
        'record entry to this node if fsmNode.doLogging True'
        if not self.fsmNode.doLogging:
            return
        if self.activityEvent and self.activityEvent.nodeName == self.fsmNode.name:
            return
        # NB: should probably extract unitLesson ID from request.path!!
        if self.activity: # record to existing activity
            self.activityEvent = ActivityEvent(activity=self.activity,
                user=user, nodeName=fsmNode.name, unitLesson=self.unitLesson)
            self.activityEvent.save()
        else: # create new activity log
            self.activityEvent = ActivityLog.log_node_entry(self.fsmNode, user,
                                                            self.unitLesson)
            self.activity = self.activityEvent.activity
        self.save()
    @classmethod
    def find_live_sessions(klass, user):
        'get live sessions relevant to this user'
        return klass.objects.filter(isLiveSession=True,
                                    activity__course__role__user=user)

        
class ActivityLog(models.Model):
    'a category of FSM activity to log'    
    fsmName = models.CharField(max_length=64)
    startTime = models.DateTimeField('time created', default=timezone.now)
    endTime = models.DateTimeField('time ended', null=True)
    course = models.ForeignKey(Course, null=True)
    @classmethod
    def get_or_create(klass, name):
        'get log with specified name if it exists, or create it'
        try:
            return klass.objects.get(fsmName=name)
        except klass.DoesNotExist:
            a = klass(fsmName=name)
            a.save()
            return a
    @classmethod
    def log_node_entry(klass, fsmNode, user, unitLesson=None):
        'record entry to this node, creating ActivityLog if needed'
        a = klass.get_or_create(fsmNode.fsm.name)
        ae = ActivityEvent(activity=a, user=user, nodeName=fsmNode.name,
                           unitLesson=unitLesson)
        ae.save()
        return ae

class ActivityEvent(models.Model):
    'log FSM node entry/exit times'
    activity = models.ForeignKey(ActivityLog)
    nodeName = models.CharField(max_length=64)
    user = models.ForeignKey(User)
    unitLesson = models.ForeignKey(UnitLesson, null=True)
    startTime = models.DateTimeField('time created', default=timezone.now)
    endTime = models.DateTimeField('time ended', null=True)
    exitEvent = models.CharField(max_length=64)
    def log_exit_event(self, eventName):
        self.exitEvent = eventName
        self.endTime = timezone.now()
        self.save()

