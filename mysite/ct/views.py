from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Q
import json
from ct.models import *
from ct.forms import *
from ct.templatetags.ct_extras import md2html, get_base_url, get_object_url, is_teacher_url, display_datetime, get_path_type
from ct.fsm import FSMStack


###########################################################
# WelcomeMat refactored utilities

def check_instructor_auth(course, request):
    'return 403 if not course instructor, else None'
    role = course.get_user_role(request.user)
    if role != Role.INSTRUCTOR:
        return HttpResponse("Only the instructor can access this",
                            status_code=403)

def make_tabs(path, current, tabs, tail=4, **kwargs):
    path = get_base_url(path, tail=tail, **kwargs)
    outTabs = []
    for label in tabs:
        try:
            i = label.index(':')
        except ValueError:
            tail = label.lower() + '/' # default, just use label
        else: # use specified URL tail
            tail = label[i + 1:]
            label = label[:i]
        labels = label.split(',')
        label = labels[0]
        if current in labels:
            tail = '#%sTabDiv' % current
            outTabs.append((label, tail))
        else:
            outTabs.append((label, path + tail))
    return outTabs

def concept_tabs(path, current, unitLesson,
                 tabs=('Home,Study:', 'Lessons', 'Concepts', 'Errors', 'FAQ', 'Edit'),
                 **kwargs):
    if not is_teacher_url(path):
        tabs = ('Study:', 'Lessons', 'FAQ')
    if unitLesson.order is not None:
        tabs = tabs[:1] + ('Tasks',) + tabs[1:]
    return make_tabs(path, current, tabs, **kwargs)

def error_tabs(path, current, unitLesson,
               tabs=('Resolutions:', 'Resources', 'FAQ', 'Edit'), **kwargs):
    if not is_teacher_url(path):
        tabs = ('Resolutions:', 'Resources', 'FAQ')
    outTabs = make_tabs(path, current, tabs, **kwargs)
    if unitLesson.parent:
        outTabs.append(make_tab(path, current, 'Question',
                            get_object_url(path, unitLesson.parent)))
    return outTabs


def make_tab(path, current, label, url):
    'use #LABELTabDiv or URL depending on whether current matches label'
    if current == label:
        return (label,'#%sTabDiv' % label)
    else:
        return (label, url)


def filter_tabs(tabs, filterLabels):
    return [t for t in tabs if t[0] in filterLabels]
    
def lesson_tabs(path, current, unitLesson,
                 tabs=('Home:', 'Tasks', 'Concepts', 'Errors', 'FAQ', 'Edit'),
                 answerTabs=('Home', 'FAQ', 'Edit'), **kwargs):
    if not is_teacher_url(path):
        tabs = ('Study:', 'Tasks', 'Concepts', 'Errors', 'FAQ')
    outTabs = make_tabs(path, current, tabs, **kwargs)
    if unitLesson.kind == UnitLesson.ANSWERS and unitLesson.parent:
        outTabs = filter_tabs(outTabs, answerTabs)
        outTabs.append(make_tab(path, current, 'Question', get_base_url(path,
                    ['lessons', str(unitLesson.parent.pk)])))
    else:
        a = unitLesson.get_answers().all()
        if a:
            outTabs.append(make_tab(path, current, 'Answer',
                get_base_url(path, ['lessons', str(a[0].pk)])))
    return outTabs

def auto_tabs(path, current, unitLesson, **kwargs):
    tabFuncs = {'errors':error_tabs,
                   'concepts':concept_tabs,
                   'lessons':lesson_tabs}
    currentType = get_path_type(path)
    return tabFuncs[currentType](path, current, unitLesson, **kwargs)
    

    
def unit_tabs(path, current,
              tabs=('Tasks:', 'Concepts', 'Lessons', 'Resources', 'Edit'), **kwargs):
    return make_tabs(path, current, tabs, tail=2, **kwargs)
    
def unit_tabs_student(path, current,
              tabs=('Study:', 'Tasks', 'Lessons', 'Concepts'), **kwargs):
    return make_tabs(path, current, tabs, tail=2, **kwargs)
    
def course_tabs(path, current, tabs=('Home:', 'Edit'), **kwargs):
    return make_tabs(path, current, tabs, tail=2, baseToken='courses',
                     **kwargs)
    

class PageData(object):
    'generic holder for page UI elements such as tabs'
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)
    def fsm_redirect(self, request, eventName=None, defaultURL=None,
                     addNextButton=False, fsmStack=None, **kwargs):
        'check whether fsm intercepts this event and returns redirect'
        if fsmStack is None:
            fsmStack = FSMStack(request)
        if not fsmStack.state: # no FSM running, so nothing to do
            return defaultURL and HttpResponseRedirect(defaultURL)
        if not eventName and addNextButton: # must supply Next form
            if request.method == 'POST':
                eventName = 'next' # tell FSM this is next event
            else:
                self.nextForm = NextForm()
                set_crispy_action(request.path, self.nextForm)
        r = fsmStack.event(request, eventName, defaultURL=defaultURL, **kwargs)
        if r: # let FSM override the default URL
            return HttpResponseRedirect(r)
        elif defaultURL: # otherwise follow the default
            return HttpResponseRedirect(defaultURL)
    def render(self, request, templatefile, templateArgs=None, **kwargs):
        'let fsm adjust view / redirect prior to rendering'
        self.path = request.path
        fsmStack = FSMStack(request)
        self.fsmState = fsmStack.state
        if fsmStack.state and fsmStack.state.isModal: # turn off tab interface
            self.navTabs = ()
        if templateArgs: # avoid side-effects of modifying caller's dict
            templateArgs = templateArgs.copy()
        else:
            templateArgs = {}
        templateArgs['user'] = request.user
        templateArgs['actionTarget'] = request.path
        templateArgs['pageData'] = self
        templateArgs['fsmStack'] = fsmStack
        return self.fsm_redirect(request, pageData=self, fsmStack=fsmStack) \
            or render(request, templatefile, templateArgs, **kwargs)
    def fsm_push(self, request, name, *args, **kwargs):
        'create a new FSM and redirect to its START page'
        fsmStack = FSMStack(request)
        url = fsmStack.push(request, name, *args, **kwargs)
        return HttpResponseRedirect(url)
    def fsm_on_path(self):
        'True if we are on same page as current FSMState'
        return self.path == self.fsmState.path

def ul_page_data(request, unit_id, ul_id, currentTab, includeText=True,
                 tabFunc=None, checkUnitStatus=False, includeNavTabs=True,
                 **kwargs):
    'generate standard set of page data for a unitLesson'
    unit = get_object_or_404(Unit, pk=unit_id)
    ul = get_object_or_404(UnitLesson, pk=ul_id)
    if not tabFunc:
        tabFunc = auto_tabs
    pageData = PageData(title=ul.lesson.title, **kwargs)
    if checkUnitStatus and not UnitStatus.is_done(unit, request.user):
        includeNavTabs = False
    if includeNavTabs:
        pageData.navTabs = tabFunc(request.path, currentTab, ul)
    if includeText:
        pageData.headText = md2html(ul.lesson.text)
        ulType = ul.get_type()
        if ulType == IS_ERROR:
            pageData.headLabel = 'error model'
        elif ulType == IS_CONCEPT:
            pageData.headLabel = 'concept definition'
        else:
            pageData.headLabel = ul.lesson.get_kind_display()
    return unit, ul, ul.lesson.concept, pageData


###########################################################
# WelcomeMat refactored instructor views

@login_required
def main_page(request):
    'generic home page'
    pageData = PageData()
    return pageData.render(request, 'ct/index.html')

def person_profile(request, user_id):
    'stub for basic user info page'
    person = get_object_or_404(User, pk=user_id)
    pageData = PageData()
    if request.method == 'POST': # signout
        if request.POST.get('task') == 'logout':
            logout(request)
            return HttpResponseRedirect(reverse('ct:home'))
    if request.user == person: # button for user to logout
        logoutForm = LogoutForm()
    else:
        logoutForm = None
    return pageData.render(request, 'ct/person.html',
                           dict(person=person, logoutForm=logoutForm))

def about(request):
    pageData = PageData()
    return pageData.render(request, 'ct/about.html')

# course views

@login_required
def course_view(request, course_id):
    'show courselets in a course'
    course = get_object_or_404(Course, pk=course_id)
    if is_teacher_url(request.path):
        notInstructor = check_instructor_auth(course, request)
        if notInstructor: # redirect students to live session or student page
            return HttpResponseRedirect(reverse('ct:course_student', args=(course.id,)))
        navTabs = course_tabs(request.path, 'Home')
        courseletform = NewUnitTitleForm()
        showReorderForm = True
        unitTable = course.get_course_units(publishedOnly=False)
    else:
        courseletform = showReorderForm = None
        navTabs = ()
        unitTable = course.get_course_units()
    pageData = PageData(title=course.title, headLabel='course description',
                        headText=md2html(course.description), navTabs=navTabs)
    if request.method == 'POST': # create new courselet
        if 'oldOrder' in request.POST and not notInstructor:
            reorderForm = ReorderForm(0, len(unitTable), request.POST)
            if reorderForm.is_valid():
                oldOrder = int(reorderForm.cleaned_data['oldOrder'])
                newOrder = int(reorderForm.cleaned_data['newOrder'])
                unitTable = course.reorder_course_unit(oldOrder, newOrder,
                                                       unitTable)
        else:
            courseletform = NewUnitTitleForm(request.POST)
            if courseletform.is_valid():
                title = courseletform.cleaned_data['title']
                unit = course.create_unit(title, request.user)
                return HttpResponseRedirect(reverse('ct:unit_tasks',
                            args=(course_id, unit.id,)))
    if courseletform:
        set_crispy_action(request.path, courseletform)
    if len(unitTable) < 2:
        showReorderForm = False
    if showReorderForm:
        for cu in unitTable:
            cu.reorderForm = ReorderForm(cu.order, len(unitTable))
    return pageData.render(request, 'ct/course.html',
                  dict(course=course, courseletform=courseletform,
                       unitTable=unitTable, showReorderForm=showReorderForm))

@login_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    notInstructor = check_instructor_auth(course, request)
    if notInstructor: # redirect students to live session or student page
        return HttpResponseRedirect(reverse('ct:course_student', args=(course.id,)))

    pageData = PageData(title=course.title,
                        navTabs=course_tabs(request.path, 'Edit'))
    if request.method == 'POST': # create new courselet
        courseform = CourseTitleForm(request.POST, instance=course)
        if courseform.is_valid():
            courseform.save()
            return HttpResponseRedirect(reverse('ct:course',
                                                args=(course.id,)))
    else:
        courseform = CourseTitleForm(instance=course)
    set_crispy_action(request.path, courseform)
    return render(request, 'ct/edit_course.html',
                  dict(course=course, actionTarget=request.path,
                       courseform=courseform, pageData=pageData))


@login_required
def edit_unit(request, course_id, unit_id):
    course = get_object_or_404(Course, pk=course_id)
    unit = get_object_or_404(Unit, pk=unit_id)
    notInstructor = check_instructor_auth(course, request)
    if notInstructor: # redirect students to live session or student page
        return HttpResponseRedirect(reverse('ct:study_unit',
                                        args=(course_id, unit_id)))

    pageData = PageData(title=unit.title,
                        navTabs=unit_tabs(request.path, 'Edit'))
    cu = course.courseunit_set.get(unit=unit)
    unitform = UnitTitleForm(instance=unit)
    if request.method == 'POST': # create new courselet
        if request.POST.get('task') == 'release':
            cu.releaseTime = timezone.now()
            cu.save() # publish for student access
        else:
            unitform = UnitTitleForm(request.POST, instance=unit)
            if unitform.is_valid():
                unitform.save()
                return HttpResponseRedirect(reverse('ct:unit_tasks',
                                            args=(course.id, unit_id)))
    set_crispy_action(request.path, unitform)
    return render(request, 'ct/edit_unit.html',
                  dict(unit=unit, actionTarget=request.path, courseUnit=cu,
                       unitform=unitform, pageData=pageData))


def update_concept_link(request, conceptLinks):
    cl = get_object_or_404(ConceptLink, pk=int(request.POST.get('clID')))
    clform = ConceptLinkForm(request.POST, instance=cl)
    if clform.is_valid():
        clform.save()
        conceptLinks.replace(cl, clform)

def _concepts(request, msg='', ignorePOST=False, conceptLinks=None,
              toTable=None, fromTable=None, unit=None,
              actionLabel='Link to this Concept',
              errorModels=None, isError=False, **kwargs):
    'search or create a Concept'
    cset = wset = ()
    if errorModels is not None:
        conceptForm = NewConceptForm()
    else:
        conceptForm = None
    searchForm = ConceptSearchForm()
    if request.method == 'POST' and not ignorePOST:
        if 'wikipediaID' in request.POST:
            concept, lesson = \
              Concept.get_from_sourceDB(request.POST.get('wikipediaID'),
                                        request.user)
            if unit:
                lesson.unitlesson_set.create(unit=unit, treeID=lesson.treeID,
                                             addedBy=concept.addedBy)
            return concept
        elif 'clID' in request.POST:
            update_concept_link(request, conceptLinks)
        elif request.POST.get('task') == 'reverse' and 'cgID' in request.POST:
            cg = get_object_or_404(ConceptGraph,
                                   pk=int(request.POST.get('cgID')))
            c = cg.fromConcept
            cg.fromConcept = cg.toConcept
            cg.toConcept = c
            cg.save() # save the reversed relationship
            toTable.move_between_tables(cg, fromTable)
        elif 'cgID' in request.POST:
            cg = get_object_or_404(ConceptGraph,
                                   pk=int(request.POST.get('cgID')))
            cgform = ConceptGraphForm(request.POST, instance=cg)
            if cgform.is_valid():
                cgform.save()
                toTable.replace(cg, cgform)
                fromTable.replace(cg, cgform)
        elif 'conceptID' in request.POST:
            return Concept.objects.get(pk=int(request.POST.get('conceptID')))
        elif 'title' in request.POST: # create new concept
            conceptForm = NewConceptForm(request.POST)
            if conceptForm.is_valid():
                return Concept.new_concept(conceptForm.cleaned_data['title'],
                            conceptForm.cleaned_data['description'],
                            unit, request.user, isError)
        else:
            return 'please write POST error message'
    elif 'search' in request.GET:
        searchForm = ConceptSearchForm(request.GET)
        if searchForm.is_valid():
            s = searchForm.cleaned_data['search']
            if errorModels is not None: # search errors only
                cset = UnitLesson.search_text(s, IS_ERROR)
            else: # search correct concepts only
                cset = UnitLesson.search_text(s, IS_CONCEPT)
                wset = Lesson.search_sourceDB(s)
            conceptForm = NewConceptForm() # let user define new concept
    if conceptForm:
        set_crispy_action(request.path, conceptForm)
    kwargs.update(dict(cset=cset, actionTarget=request.path, msg=msg,
                       searchForm=searchForm, wset=wset,
                       toTable=toTable, fromTable=fromTable,
                       conceptForm=conceptForm, conceptLinks=conceptLinks,
                       actionLabel=actionLabel, 
                       errorModels=errorModels, user=request.user))
    return render(request, 'ct/concepts.html', kwargs)


## def edit_concept(request, course_id, unit_id, ul_id,
##                  tabsFunc=concept_tabs):
##     ul = get_object_or_404(UnitLesson, pk=ul_id)
##     navTabs = tabsFunc(request.path, 'Edit')
##     if request.user == ul.lesson.addedBy:
##         titleform = ConceptForm(instance=ul.lesson)
##         if request.method == 'POST':
##             if 'title' in request.POST:
##                 titleform = ConceptForm(request.POST, instance=concept)
##                 if titleform.is_valid():
##                     titleform.save()
##             elif request.POST.get('task') == 'delete':
##                 concept.delete()
##                 return HttpResponseRedirect(reverse('ct:unit_concepts',
##                                 args=(course_id, unit_id,)))
##         set_crispy_action(request.path, titleform)
##     else:
##         titleform = None
##     return render(request, 'ct/edit_concept.html',
##                   dict(actionTarget=request.path, concept=concept,
##                        atime=display_datetime(concept.atime),
##                        titleform=titleform, navTabs=navTabs))

## def edit_error(request, course_id, unit_id, concept_id):
##     return edit_concept(request, course_id, unit_id, concept_id,
##                         tabsFunc=error_tabs)

class ConceptLinkTable(object):
    def __init__(self, data=(), formClass=ConceptLinkForm, noEdit=False,
                 **kwargs):
        self.formClass = formClass
        self.noEdit = noEdit
        self.data = []
        for cl in data:
            self.append(cl)
        for k,v in kwargs.items():
            setattr(self, k, v)
    def append(self, cl):
        self.data.append((cl, self.formClass(instance=cl)))
    def replace(self, cl, clform):
        for i,t in enumerate(self.data):
            if t[0] == cl:
                self.data[i] = (cl, clform)
    def remove(self, cl):
        for i,t in enumerate(self.data):
            if t[0] == cl:
                del self.data[i]
                return True
    def move_between_tables(self, cl, other):
        if self.remove(cl):
            other.append(cl)
        elif other.remove(cl):
            self.append(cl)

@login_required
def unit_concepts(request, course_id, unit_id):
    'page for viewing or adding concepts relevant to this courselet'
    unit = get_object_or_404(Unit, pk=unit_id)
    pageData = PageData(title=unit.title,
                        navTabs=unit_tabs(request.path, 'Concepts'))
    unitConcepts = unit.get_main_concepts().items()
    r = _concepts(request, '''To add a concept to this courselet, start by
    typing a search for relevant concepts. ''', unitConcepts=unitConcepts,
                  unit=unit, pageData=pageData,
                  actionLabel='Add to courselet')
    if isinstance(r, Concept): # newly created concept
        return HttpResponseRedirect(get_object_url(request.path, r))
    return r

@login_required
def ul_concepts(request, course_id, unit_id, ul_id, tabFunc=None):
    'page for viewing or adding concept links to this UnitLesson'
    unit, unitLesson, _, pageData = ul_page_data(request, unit_id, ul_id,
                                                 'Concepts', tabFunc=tabFunc)
    cLinks = ConceptLink.objects.filter(lesson=unitLesson.lesson)
    clTable = ConceptLinkTable(cLinks, headers=('This lesson...', 'Concept'),
                               title='Concepts Linked to this Lesson')
    r = _concepts(request, '''To add a concept to this lesson, start by
    typing a search for relevant concepts. ''', conceptLinks=clTable,
                  pageData=pageData, unit=unit, showConceptAction=True)
    if isinstance(r, Concept):
        cl = unitLesson.lesson.conceptlink_set.create(concept=r,
                                                      addedBy=request.user)
        clTable.append(cl)
        return _concepts(request, '''Successfully added concept.
            Thank you!''', ignorePOST=True, conceptLinks=clTable,
                  pageData=pageData, unit=unit, showConceptAction=True)
    return r

@login_required
def concept_concepts(request, course_id, unit_id, ul_id):
    unit, ul, concept, pageData = ul_page_data(request, unit_id, ul_id,
                                               'Concepts')
    toConcepts = concept.relatedTo.all()
    fromConcepts = concept.relatedFrom \
      .exclude(relationship=ConceptGraph.MISUNDERSTANDS)
    toTable = ConceptLinkTable(toConcepts, ConceptGraphForm,
                    headers=('This concept...', 'Related Concept'),
                    title='Concepts Linked from this Concept')
    fromTable = ConceptLinkTable(fromConcepts, ConceptGraphForm,
                    headers=('Related Concept', '...this concept',),
                    title='Concepts Linking to this Concept')
    r = _concepts(request, '''To add a concept link, start by
    typing a search for relevant concepts. ''', toTable=toTable,
                  fromTable=fromTable, unit=unit, pageData=pageData,
                  showConceptAction=True)
    if isinstance(r, Concept):
        cg = concept.relatedTo.create(toConcept=r, addedBy=request.user)
        toTable.append(cg)
        return _concepts(request, '''Successfully added concept.
            Thank you!''', ignorePOST=True, toTable=toTable,
            fromTable=fromTable, unit=unit, pageData=pageData)
    return r

@login_required
def concept_errors(request, course_id, unit_id, ul_id):
    unit, ul, concept, pageData = ul_page_data(request, unit_id, ul_id,
                                               'Errors')
    errorModels = list(concept.relatedFrom
      .filter(relationship=ConceptGraph.MISUNDERSTANDS))
    r = _concepts(request, '''To add an error model to this concept, start by
    typing a search for relevant errors.''', errorModels=errorModels,
                  pageData=pageData, unit=unit, showConceptAction=True,
                  isError=True)
    if isinstance(r, Concept):
        cg = concept.relatedFrom.create(fromConcept=r, addedBy=request.user,
                                    relationship=ConceptGraph.MISUNDERSTANDS)
        errorModels.append(cg)
        return _concepts(request, '''Successfully added error model.
            Thank you!''', ignorePOST=True, errorModels=errorModels,
            pageData=pageData, unit=unit)
    return r

def create_unit_lesson(lesson, concept, unit, parentUL):
    'save new lesson, bind to concept, and append to this unit'
    lesson.save_root(concept)
    return UnitLesson.create_from_lesson(lesson, unit, order='APPEND',
                                         addAnswer=True)

def _lessons(request, concept=None, msg='',
             ignorePOST=False, conceptLinks=None,
             unit=None, actionLabel='Add to This Courselet',
             allowSearch=True, creationInstructions=None,
             templateFile='ct/lessons.html', lessonTable=(),
             createULFunc=create_unit_lesson, selectULFunc=None,
             newLessonFormClass=NewLessonForm, showReorderForm=False,
             searchType=None, parentUL=None, **kwargs):
    'search or create a Lesson'
    if creationInstructions:
        lessonForm = newLessonFormClass()
    else:
        lessonForm = None
    if searchType == IS_ERROR:
        searchFormClass = ErrorSearchForm
    else:
        searchFormClass = LessonSearchForm
    if allowSearch:
        searchForm = searchFormClass()
    else:
        searchForm = None
    lessonSet = ()
    if request.method == 'POST' and not ignorePOST:
        if 'clID' in request.POST:
            update_concept_link(request, conceptLinks)
        elif 'newOrder' in request.POST:
            reorderForm = ReorderForm(0, len(lessonTable), request.POST)
            if reorderForm.is_valid():
                oldOrder = int(reorderForm.cleaned_data['oldOrder'])
                newOrder = int(reorderForm.cleaned_data['newOrder'])
                lessonTable = unit.reorder_exercise(oldOrder, newOrder,
                                                    lessonTable)
        elif 'ulID' in request.POST:
            ul = UnitLesson.objects.get(pk=int(request.POST.get('ulID')))
            if selectULFunc:
                ul = selectULFunc(ul, concept, unit, request.user, parentUL)
                if isinstance(ul, UnitLesson):
                    return ul
                msg = ul # treat as error message to display
            else:
                return ul
        elif 'title' in request.POST: # create new lesson
            lessonForm = newLessonFormClass(request.POST)
            if lessonForm.is_valid():
                lesson = lessonForm.save(commit=False)
                lesson.addedBy = request.user
                return createULFunc(lesson, concept, unit, parentUL)
        else:
            return 'please write POST error message'

    elif allowSearch and 'search' in request.GET:
        searchForm = searchFormClass(request.GET)
        if searchForm.is_valid():
            s = searchForm.cleaned_data['search']
            if searchType is None:
                searchType = searchForm.cleaned_data['searchType']
            lessonSet = UnitLesson.search_text(s, searchType)
    if showReorderForm and lessonTable:
        for ul in lessonTable:
            ul.reorderForm = ReorderForm(ul.order, len(lessonTable))
    if lessonForm:
        set_crispy_action(request.path, lessonForm)
    kwargs.update(dict(lessonSet=lessonSet, actionTarget=request.path,
                       searchForm=searchForm, msg=msg,
                       lessonForm=lessonForm, conceptLinks=conceptLinks,
                       actionLabel=actionLabel, user=request.user,
                       creationInstructions=creationInstructions,
                       lessonTable=lessonTable,
                       showReorderForm=showReorderForm))
    return render(request, templateFile, kwargs)

def make_cl_table(concept, unit):
    cLinks = concept.get_conceptlinks(unit)
    return ConceptLinkTable(cLinks, headers=('Lesson', '...this concept'),
                            title='Lessons Linked to this Concept')

@login_required
def concept_lessons(request, course_id, unit_id, ul_id):
    unit, ul, concept, pageData = ul_page_data(request, unit_id, ul_id,
                                               'Lessons')
    clTable = make_cl_table(concept, unit)
    creationInstructions='''You can type a new lesson on this
        concept below (if you add an open-response question,
        you will be prompted later to write an answer). '''
    r = _lessons(request, concept, conceptLinks=clTable,
                 pageData=pageData, unit=unit, allowSearch=False,
                 creationInstructions=creationInstructions)
    if isinstance(r, UnitLesson):
        if r.lesson.kind == Lesson.ORCT_QUESTION:
            if r.get_errors().count() == 0: # copy error models from concept
                concept.copy_error_models(r)
            if getattr(r, '_answer', None): # redirect to edit empty answer
                return HttpResponseRedirect(reverse('ct:edit_lesson',
                                args=(course_id, unit_id, r._answer.id,)))
        clTable = make_cl_table(concept, unit) # refresh table
        return _lessons(request, concept, '''Successfully added lesson.
            Thank you!''', ignorePOST=True, conceptLinks=clTable,
            pageData=pageData, unit=unit, allowSearch=False,
            creationInstructions=creationInstructions)
    return r

@login_required
def unit_tasks(request, course_id, unit_id):
    'suggest next steps on this courselet'
    course = get_object_or_404(Course, pk=course_id)
    unit = get_object_or_404(Unit, pk=unit_id)
    cu = course.courseunit_set.get(unit=unit)
    pageData = PageData(title=unit.title,
                        navTabs=unit_tabs(request.path, 'Tasks'))
    newInquiryULs = frozenset(unit.get_new_inquiry_uls())
    ulDict = {}
    for ul in newInquiryULs:
        ulDict[ul] = ['inquiry']
    for ul in unit.get_errorless_uls():
        ulDict.setdefault(ul, []).append('em')
    for ul in unit.get_resoless_uls():
        ulDict.setdefault(ul, []).append('reso')
    taskTable = [(ul, ulDict[ul]) for ul in newInquiryULs]
    taskTable += [(ul, ulDict[ul]) for ul in ulDict
                  if ul not in newInquiryULs]
    return render(request, 'ct/unit_tasks.html',
                  dict(user=request.user, actionTarget=request.path,
                       pageData=pageData, unit=unit, taskTable=taskTable,
                       courseUnit=cu))

    


def copy_unit_lesson(ul, concept, unit, addedBy, parentUL):
    'copy lesson and append to this unit'
    if ul.unit == unit:
        return 'Lesson already in this unit, so no change made.'
    return ul.copy(unit, addedBy, order='APPEND')

@login_required
def unit_lessons(request, course_id, unit_id, lessonTable=None,
                 currentTab='Lessons', showReorderForm=True):
    unit = get_object_or_404(Unit, pk=unit_id)
    pageData = PageData(title=unit.title,
                        navTabs=unit_tabs(request.path, currentTab))
    if lessonTable is None:
        lessonTable = unit.get_exercises()
    r = _lessons(request, msg='''You can search for a lesson to add
          to this courselet, or write a new lesson for a concept by
          clicking on the Concepts tab.''', 
                  pageData=pageData, unit=unit,
                  showReorderForm=showReorderForm,
                  lessonTable=lessonTable, selectULFunc=copy_unit_lesson)
    if isinstance(r, UnitLesson):
        lessonTable.append(r)
        return _lessons(request, msg='''Successfully added lesson.
            Thank you!''', ignorePOST=True, showReorderForm=showReorderForm,
            pageData=pageData, unit=unit, lessonTable=lessonTable)
    return r

@login_required
def unit_resources(request, course_id, unit_id):
    unit = get_object_or_404(Unit, pk=unit_id)
    lessonTable = list(unit.unitlesson_set \
            .filter(kind=UnitLesson.COMPONENT, order__isnull=True))
    return unit_lessons(request, course_id, unit_id, lessonTable,
                        'Resources', showReorderForm=False)


@login_required
def ul_teach(request, course_id, unit_id, ul_id):
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id, 'Home',
                                         False)
    query = Q(unitLesson=ul, selfeval__isnull=False,
              kind=Response.ORCT_RESPONSE)
    statusTable, evalTable, n = Response.get_counts(query)
    if request.method == 'POST' and request.POST.get('task') == 'append' \
            and ul.unit != unit:
        ulNew = ul.copy(unit, request.user, order='APPEND')
        return HttpResponseRedirect(reverse('ct:ul_teach',
                                args=(course_id, unit_id, ulNew.pk)))
    return render(request, 'ct/lesson.html',
                  dict(user=request.user, actionTarget=request.path,
                       unitLesson=ul, pageData=pageData, unit=unit,
                       statusTable=statusTable, evalTable=evalTable))

@login_required
def ul_tasks(request, course_id, unit_id, ul_id):
    'suggest next steps on this question'
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id, 'Tasks')
    newInquiries = list(ul.get_new_inquiries())
    if ul.lesson.kind == Lesson.ORCT_QUESTION:
        pageData.isQuestion = True
        errorModels = list(ul.get_errors())
        for em in errorModels:
            newInquiries += list(em.get_new_inquiries())
        for em in ul.get_answers():
            newInquiries += list(em.get_new_inquiries())
        errorTable = [(em, len(em.get_em_resolutions()[1]))
                      for em in errorModels]
    else:
        errorTable = ()
    return render(request, 'ct/ul_tasks.html',
                  dict(user=request.user, actionTarget=request.path,
                       unitLesson=ul, pageData=pageData, unit=unit,
                       errorTable=errorTable, newInquiries=newInquiries))

    
@login_required
def edit_lesson(request, course_id, unit_id, ul_id):
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id, 'Edit',
                                         False)
    if ul.get_type() == IS_LESSON:
        if ul.lesson.kind == Lesson.ANSWER:
            formClass = AnswerLessonForm
        else:
            formClass = LessonForm
    else:
        formClass = ErrorForm
    if request.user == ul.addedBy:
        titleform = formClass(instance=ul.lesson)
        if request.method == 'POST':
            if 'title' in request.POST:
                titleform = formClass(request.POST, instance=ul.lesson)
                if titleform.is_valid():
                    titleform.save()
                    return HttpResponseRedirect(get_object_url(request.path,
                                                               ul))
            elif request.POST.get('task') == 'delete':
                ul.delete()
                unit.reorder_exercise() # renumber all lessons
                return HttpResponseRedirect(reverse('ct:unit_lessons',
                                args=(course_id, unit_id,)))
        set_crispy_action(request.path, titleform)
    else:
        titleform = None
    return render(request, 'ct/edit_lesson.html',
                  dict(actionTarget=request.path, unitLesson=ul,
                       atime=display_datetime(ul.atime), user=request.user,
                       titleform=titleform, pageData=pageData))


def create_error_ul(lesson, concept, unit, parentUL):
    'create UnitLesson, Concept etc. for new error model'
    lesson.kind = lesson.ERROR_MODEL
    em = concept.create_error_model(title=lesson.title,
                                    addedBy=lesson.addedBy)
    lesson.concept = em
    lesson.save_root()
    return UnitLesson.create_from_lesson(lesson, unit, parent=parentUL)

def copy_error_ul(ul, concept, unit, addedBy, parentUL):
    'copy error and append to this unit'
    if ul.unit == unit:
        return 'Lesson already in this unit, so no change made.'
    return ul.copy(unit, addedBy, parent=parentUL)


@login_required
def ul_errors(request, course_id, unit_id, ul_id, showNETable=True):
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id, 'Errors')
    n = Response.objects.filter(unitLesson=ul,
                                selfeval__isnull=False).count()
    showNovelErrors = False
    if n > 0:
        query = Q(response__unitLesson=ul, response__selfeval__isnull=False)
        seTable = StudentError.get_counts(query, n)
    else:
        seTable = []
    if n > 0 and showNETable:
        neArgs = {}
        if request.method == 'GET' and 'selfeval' in request.GET:
            neForm = ResponseFilterForm(request.GET)
            if neForm.is_valid():
                showNovelErrors = True
                if neForm.cleaned_data['selfeval']:
                    neArgs['selfeval'] = neForm.cleaned_data['selfeval']
                if neForm.cleaned_data['status']:
                    neArgs['status'] = neForm.cleaned_data['status']
                if neForm.cleaned_data['confidence']:
                    neArgs['confidence'] = neForm.cleaned_data['confidence']
        else:
            neForm = ResponseFilterForm(request.GET)
        novelErrors = Response.get_novel_errors(ul, **neArgs)
    else:
        novelErrors = ()
        neForm = False
    cLinks = list(ul.get_linked_concepts())
    if cLinks:
        concept = cLinks[0].concept
        for cl in cLinks:
            if cl.relationship == ConceptLink.TESTS:
                concept = cl.concept
                break
        creationInstructions = '''You can write a new error model
        for the concept: %s.''' % concept.title
        msg = '''You can search for existing error models to add
          to this lesson, or write a new error model below.'''
    else:
        concept = creationInstructions = None
        msg = '''This lesson is not linked to any concept.  Please
        add a concept link (by clicking on the Concepts tab) before
        adding error models to this lesson. '''
    errorModels = set([t[0] for t in seTable])
    for em in ul.get_errors():
        if em not in errorModels:
            seTable.append((em, fmt_count(0, n or 1)))
    r = _lessons(request, concept, msg, pageData=pageData, unit=unit, 
                  seTable=seTable, templateFile='ct/errors.html',
                  showNovelErrors=showNovelErrors,
                  novelErrors=novelErrors, responseFilterForm=neForm,
                  creationInstructions=creationInstructions,
                  newLessonFormClass=NewErrorForm, parentUL=ul,
                  createULFunc=create_error_ul, selectULFunc=copy_error_ul,
                  searchType=IS_ERROR, actionLabel='Add error model')
    if isinstance(r, UnitLesson):
        seTable.append((r, fmt_count(0, n)))
        return _lessons(request, concept, msg='''Successfully added error
            model.  Thank you!''', ignorePOST=True, 
            pageData=pageData, unit=unit, seTable=seTable, 
            templateFile='ct/errors.html', novelErrors=novelErrors,
            creationInstructions=creationInstructions,
            newLessonFormClass=NewErrorForm)
    return r

def create_resolution_ul(lesson, em, unit, parentUL):
    'create UnitLesson as resolution linked to error model'
    lesson.save_root(em, ConceptLink.RESOLVES) # link as resolution
    return UnitLesson.create_from_lesson(lesson, unit, addAnswer=True,
                                         kind=UnitLesson.RESOLVES)

def link_resolution_ul(ul, em, unit, addedBy, parentUL):
    'link ul as resolution for error model'
    if ul.lesson.conceptlink_set.filter(concept=em,
                    relationship=ConceptLink.RESOLVES).count() == 0:
        ul.lesson.conceptlink_set.create(concept=em, addedBy=addedBy,
                                  relationship=ConceptLink.RESOLVES)
    return ul


@login_required
def resolutions(request, course_id, unit_id, ul_id):
    'UI for user to add or write remediations for a specific error'
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id,
                                         'Resolutions', showHead=True)
    em, lessonTable = ul.get_em_resolutions()
    msg = '''This page lists lessons, exercises, or review
    suggested for students who make this error, to help them
    overcome it.  You can add to the list by either searching
    for relevant lessons, or writing a new lesson below.'''
    creationInstructions = '''You can write a new lesson that
                  helps students overcome this error, and click Add.'''
    r = _lessons(request, em, msg, lessonTable=lessonTable,
                 pageData=pageData, unit=unit, 
                 actionLabel='Add to suggestion list',
                 creationInstructions=creationInstructions,
                 createULFunc=create_resolution_ul,
                 selectULFunc=link_resolution_ul)
    if isinstance(r, UnitLesson):
        if r not in lessonTable:
            lessonTable.append(r)
        return _lessons(request, em, msg='''Successfully added resolution
                  Thank you!''', ignorePOST=True, lessonTable=lessonTable,
                  pageData=pageData, unit=unit,
                  actionLabel='Add to suggestion list',
                  creationInstructions=creationInstructions)
    return r

@login_required
def error_resources(request, course_id, unit_id, ul_id):
    unit, ul, concept, pageData = ul_page_data(request, unit_id, ul_id,
                                               'Resources')
    toConcepts = concept.relatedTo.all()
    fromConcepts = concept.relatedFrom.all()
    testLessons = concept.get_error_tests()
    alternativeDefs = ul.get_alternative_defs()
    return render(request, 'ct/error_resources.html',
                  dict(user=request.user, actionTarget=request.path,
                       pageData=pageData, toConcepts=toConcepts,
                       fromConcepts=fromConcepts, testLessons=testLessons,
                       alternativeDefs=alternativeDefs))

###########################################################
# welcome mat refactored student UI for courses

@login_required
def study_unit(request, course_id, unit_id):
    unit = get_object_or_404(Unit, pk=unit_id)
    unitStatus = None
    pageData = PageData(title=unit.title)
    if request.method == 'POST'  and request.POST.get('task') == 'next':
        return pageData.fsm_push(request, 'lessonseq', dict(unit=unit))
    if unitStatus:
        nextUL = unitStatus.get_lesson()
        if unitStatus.endTime: # already completed unit
            pageData.navTabs = unit_tabs_student(request.path, 'Study')
    else:
        nextUL = None
    return render(request, 'ct/study_unit.html',
                  dict(user=request.user, actionTarget=request.path,
                       unitLesson=nextUL, unit=unit, pageData=pageData))

@login_required
def unit_tasks_student(request, course_id, unit_id):
    'suggest next steps on this courselet'
    unit = get_object_or_404(Unit, pk=unit_id)
    pageData = PageData(title=unit.title,
                        navTabs=unit_tabs_student(request.path, 'Tasks'))
    taskTable = [(ul, 'start')
                 for ul in unit.get_unanswered_uls(request.user)]
    taskTable += [(ul, 'selfeval')
                  for ul in unit.get_selfeval_uls(request.user)]
    taskTable += [(ul, 'classify')
                  for ul in unit.get_serrorless_uls(request.user)]
    taskTable += [(ul, 'resolve')
                  for ul in unit.get_unresolved_uls(request.user)]
    return render(request, 'ct/unit_tasks_student.html',
                  dict(user=request.user, actionTarget=request.path,
                       pageData=pageData, unit=unit, taskTable=taskTable))

def unit_lessons_student(request, course_id, unit_id):
    unit = get_object_or_404(Unit, pk=unit_id)
    pageData = PageData(title=unit.title,
                        navTabs=unit_tabs_student(request.path, 'Lessons'))
    lessonTable = unit.unitlesson_set \
            .filter(kind=UnitLesson.COMPONENT, order__isnull=False) \
            .order_by('order')
    return render(request, 'ct/lessons_student.html',
                  dict(user=request.user, actionTarget=request.path,
                       pageData=pageData, lessonTable=lessonTable))

@login_required
def unit_concepts_student(request, course_id, unit_id):
    'student concept glossary for  this courselet'
    unit = get_object_or_404(Unit, pk=unit_id)
    pageData = PageData(title=unit.title,
                        navTabs=unit_tabs_student(request.path, 'Concepts'))
    l1 = list(UnitLesson.objects.filter(kind=UnitLesson.COMPONENT,
        lesson__concept__conceptlink__lesson__unitlesson__unit=unit)
        .distinct())
    l2 = list(unit.unitlesson_set.filter(kind=UnitLesson.COMPONENT,
        lesson__concept__isnull=False))
    conceptTable = distinct_subset(l1 + l2)
    conceptTable.sort(lambda x,y:cmp(x.lesson.concept.title,
                                     y.lesson.concept.title))
    return render(request, 'ct/concepts_student.html',
                  dict(user=request.user, actionTarget=request.path,
                       pageData=pageData, conceptTable=conceptTable))


def lesson_next_url(request, ul):
    'get URL for the next lesson, or URL to exit to courselet tasks view'
    try:
        nextUL = ul.get_next_lesson()
    except UnitLesson.DoesNotExist:
        return get_base_url(request.path, ['tasks']) # exit to unit tasks view
    return nextUL.get_study_url(request.path)
    
        
def lesson(request, course_id, unit_id, ul_id):
    'show student a reading assignment'
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id,'Study',
            checkUnitStatus=True, includeText=False)
    if request.method == 'POST':
        nextForm = NextLikeForm(request.POST)
        if nextForm.is_valid():
            if nextForm.cleaned_data['liked']:
                liked = Liked(unitLesson=ul, addedBy=request.user)
                liked.save()
            defaultURL = lesson_next_url(request, ul)
            # let fsm redirect this event if it wishes
            return pageData.fsm_redirect(request, 'next', defaultURL)
    elif ul.lesson.kind == Lesson.ORCT_QUESTION:
        return HttpResponseRedirect(request.path + 'ask/')
    pageData.nextForm = NextLikeForm()
    set_crispy_action(request.path, pageData.nextForm)
    return pageData.render(request, 'ct/lesson_student.html',
                           dict(unitLesson=ul, unit=unit))

def ul_tasks_student(request, course_id, unit_id, ul_id):
    'suggest next steps on this question'
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id, 'Tasks')
    responseTable = []
    if ul.lesson.kind == Lesson.ORCT_QUESTION:
        pageData.isQuestion = True
        for r in ul.response_set.filter(author=request.user).order_by('atime'):
            pageData.isAnswered = True
            step = r.get_next_step()
            if step and (r.kind == Response.ORCT_RESPONSE or
                         step == Response.CLASSIFY_STEP):
                responseTable.append((r, step[0], step[1]))
            ## else:
            ##     responseTable.append((r, None, None))
        d = {}
        for se in StudentError.get_ul_errors(ul,
                response__author=request.user).exclude(status=DONE_STATUS):
            d[se.errorModel] = se
        errorTable = d.values()
    else:
        pageData.isQuestion = errorTable = False
    return render(request, 'ct/lesson_tasks.html',
                  dict(user=request.user, actionTarget=request.path,
                       unitLesson=ul, unit=unit, pageData=pageData,
                       responseTable=responseTable, errorTable=errorTable))
    
def ul_errors_student(request, course_id, unit_id, ul_id):
    return ul_errors(request, course_id, unit_id, ul_id, showNETable=False)

@login_required
def study_concept(request, course_id, unit_id, ul_id):
    unit, ul, concept, pageData = ul_page_data(request, unit_id, ul_id,
                                               'Study')
    defsTable = distinct_subset(UnitLesson.objects
        .filter(lesson__concept=concept).exclude(treeID=ul.treeID))
    return render(request, 'ct/concept_student.html',
                  dict(user=request.user, actionTarget=request.path,
                       unitLesson=ul, pageData=pageData,
                       defsTable=defsTable))

@login_required
def concept_lessons_student(request, course_id, unit_id, ul_id):
    unit, ul, concept, pageData = ul_page_data(request, unit_id, ul_id,
                                               'Lessons')
    clTable = concept.get_conceptlinks(unit)
    return render(request, 'ct/concept_lessons_student.html',
                  dict(user=request.user, actionTarget=request.path,
                       unitLesson=ul, unit=unit, pageData=pageData,
                       clTable=clTable))


@login_required
def resolutions_student(request, course_id, unit_id, ul_id):
    'UI for user to add or write remediations for a specific error'
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id,
                                         'Resolutions')
    em, lessonTable = ul.get_em_resolutions()
    concepts = UnitLesson.objects.filter(kind=UnitLesson.COMPONENT,
        lesson__concept__relatedFrom__fromConcept=em,
        lesson__concept__relatedFrom__relationship=ConceptGraph.MISUNDERSTANDS)
    for conceptUL in distinct_subset(concepts):
        lessonTable.append(conceptUL)
    try:
        se = ul.studenterror_set.filter(author=request.user) \
          .order_by('-atime')[0]
    except IndexError:
        form = None
    else:
        if request.method == 'POST':
            form = ErrorStatusForm(request.POST, instance=se)
            if form.is_valid():
                form.save()
                form = ErrorStatusForm(instance=se) # clear the form
        else:
            form = ErrorStatusForm(instance=se)
    return render(request, 'ct/resolutions_student.html',
                  dict(user=request.user, actionTarget=request.path,
                       unitLesson=ul, unit=unit, pageData=pageData,
                       lessonTable=lessonTable, statusForm=form))

@login_required
def ul_faq_student(request, course_id, unit_id, ul_id):
    'UI for student to view or write inquiry about this lesson'
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id,
                                         'FAQ')
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            r = save_response(form, ul, request.user, course_id,
                              kind=Response.STUDENT_QUESTION, needsEval=True)
            form = CommentForm() # clear the form
    else:
        form = CommentForm()
    faqs = ul.response_set.filter(kind=Response.STUDENT_QUESTION) \
         .order_by('atime')
    faqTable = []
    for r in faqs:
        faqTable.append((r, r.inquirycount_set.count()))
    return render(request, 'ct/faq_student.html',
                  dict(user=request.user, actionTarget=request.path,
                       unitLesson=ul, unit=unit, pageData=pageData,
                       faqTable=faqTable, form=form))

@login_required
def ul_thread_student(request, course_id, unit_id, ul_id, resp_id):
    'UI for student to view or comment on discussion of an inquiry'
    inquiry = get_object_or_404(Response, pk=resp_id)
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id,
                                         'FAQ')
    form = ReplyForm()
    if request.method == 'POST':
        if request.POST.get('task') == 'meToo':
            inquiry.inquirycount_set.create(addedBy=request.user)
        else:
            form = ReplyForm(request.POST)
            if form.is_valid():
                reply = save_response(form, ul, request.user, course_id,
                                  kind=Response.COMMENT, needsEval=True,
                                  parent=inquiry)
                form = ReplyForm() # clear the form
    pageData.numPeople = inquiry.inquirycount_set.count()
    replyTable = [(r, r.studenterror_set.all())
                  for r in inquiry.response_set.all().order_by('atime')]
    faqTable = inquiry.faq_set.all() # ORCT created for this thread
    errorTable = inquiry.studenterror_set.all()
    return render(request, 'ct/thread_student.html',
                  dict(user=request.user, actionTarget=request.path,
                       unitLesson=ul, unit=unit, pageData=pageData,
                       faqTable=faqTable, form=form, inquiry=inquiry,
                       errorTable=errorTable, replyTable=replyTable))

def save_response(form, ul, user, course_id, **kwargs):
    course = get_object_or_404(Course, pk=course_id)
    r = form.save(commit=False)
    r.lesson = ul.lesson
    r.unitLesson = ul
    r.course = course
    r.author = user
    for k,v in kwargs.items():
        setattr(r, k, v)
    r.save()
    return r

@login_required
def ul_respond(request, course_id, unit_id, ul_id):
    'ask student a question'
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id,'Study',
            checkUnitStatus=True, includeText=False)
    if request.method == 'POST':
        form = ResponseForm(request.POST)
        if form.is_valid():
            r = save_response(form, ul, request.user, course_id)
            kwargs = dict(course_id=course_id, unit_id=unit_id, ul_id=ul_id,
                          resp_id=r.id)
            defaultURL = reverse('ct:assess', kwargs=kwargs)
            return pageData.fsm_redirect(request, 'next', defaultURL,
                                         reverseArgs=kwargs, response=r)
    else:
        form = ResponseForm()
    set_crispy_action(request.path, form)
    return pageData.render(request, 'ct/ask.html',
                  dict(unitLesson=ul, qtext=md2html(ul.lesson.text), form=form))

@login_required
def assess(request, course_id, unit_id, ul_id, resp_id, doSelfEval=True,
           redirectURL=None):
    'student self-assessment'
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id, 'Study')
    r = get_object_or_404(Response, pk=resp_id)
    allErrors = list(r.unitLesson.get_errors()) + unit.get_aborts()
    choices = [(e.id, e.lesson.title) for e in allErrors]
    if doSelfEval:
        formClass = SelfAssessForm
    else:
        formClass = AssessErrorsForm
    if request.method == 'POST':
        form = formClass(request.POST)
        form.fields['emlist'].choices = choices
        if form.is_valid():
            if doSelfEval:
                r.selfeval = form.cleaned_data['selfeval']
                r.status = form.cleaned_data['status']
                r.save()
                if form.cleaned_data['liked']:
                    liked = Liked(unitLesson=r.unitLesson,
                                  addedBy=request.user)
                    liked.save()
            for emID in form.cleaned_data['emlist']:
                em = get_object_or_404(UnitLesson, pk=emID)
                se = r.studenterror_set.create(errorModel=em,
                    author=request.user, status=form.cleaned_data['status'])
            if not redirectURL: # default: go to next lesson
                redirectURL = lesson_next_url(request, r.unitLesson)
            return pageData.fsm_redirect(request, 'next', redirectURL)
    else:
        form = formClass()
        form.fields['emlist'].choices = choices
    try:
        answer = r.unitLesson.get_answers()[0]
    except IndexError:
        answer = '(author has not provided an answer)'
    else:
        answer = md2html(answer.lesson.text)
    return pageData.render(request, 'ct/assess.html',
                  dict(response=r, answer=answer, form=form,
                       doSelfEval=doSelfEval))

def assess_errors(request, course_id, unit_id, ul_id, resp_id):
    ul = get_object_or_404(UnitLesson, pk=ul_id)
    redirectURL = get_object_url(request.path, ul, subpath='tasks')
    return assess(request, course_id, unit_id, ul_id, resp_id, False,
           redirectURL)

###############################################################
# FSM user interface


    
