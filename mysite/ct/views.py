import time
import urllib
from datetime import datetime

from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.contrib.auth import logout, login
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from social.backends.utils import load_backends

from ct.forms import *
from ct.models import *
from ct.ct_util import reverse_path_args, cache_this
from ct.templatetags.ct_extras import (md2html,
                                       get_base_url,
                                       get_object_url,
                                       is_teacher_url,
                                       display_datetime,
                                       get_path_type)
from fsm.fsm_base import FSMStack
from fsm.models import FSM, FSMState, KLASS_NAME_DICT


###########################################################
# WelcomeMat refactored utilities

def check_instructor_auth(course, request):
    'return 403 if not course instructor, else None'
    role = course.get_user_role(request.user, justOne=False)
    if not isinstance(role, list):
        role = [role]
    if not Role.INSTRUCTOR in role:
        return HttpResponse("Only the instructor can access this",
                            status=403)


@cache_this
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
                 user=None, **kwargs):
    if not is_teacher_url(path):
        tabs = ('Study:', 'Lessons', 'FAQ')
    if unitLesson.order is not None:
        tabs = tabs[:1] + ('Tasks',) + tabs[1:]
    return make_tabs(path, current, tabs, **kwargs)

def error_tabs(path, current, unitLesson,
               tabs=('Resolutions:', 'Resources', 'FAQ', 'Edit'), user=None, **kwargs):
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
                studentTabs=('Study:', 'Tasks', 'Concepts', 'Errors', 'FAQ'),
                unansweredTabs=('Study:', 'Concepts', 'FAQ'),
                answerTabs=('Home', 'FAQ', 'Edit'), showAnswer=True,
                user=None, **kwargs):
    if not is_teacher_url(path):
        if unitLesson.lesson.kind != Lesson.ORCT_QUESTION or \
          Response.objects.filter(unitLesson=unitLesson, author=user).exists():
            tabs = studentTabs
        else:
            tabs = unansweredTabs
            showAnswer = False
    outTabs = make_tabs(path, current, tabs, **kwargs)
    if unitLesson.kind == UnitLesson.ANSWERS and unitLesson.parent:
        outTabs = filter_tabs(outTabs, answerTabs)
        outTabs.append(make_tab(path, current, 'Question', get_base_url(path,
                    ['lessons', str(unitLesson.parent.pk)])))
    elif showAnswer:
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
              tabs=('Study:', 'Tasks', 'Lessons', 'Concepts', 'Resources'), **kwargs):
    return make_tabs(path, current, tabs, tail=2, **kwargs)
    
def course_tabs(path, current, tabs=('Home:', 'Edit'), **kwargs):
    return make_tabs(path, current, tabs, tail=2, baseToken='courses',
                     **kwargs)


class PageData(object):
    'generic holder for page UI elements such as tabs'
    def __init__(self, request, **kwargs):
        self.fsmStack = FSMStack(request)
        for k,v in kwargs.items():
            setattr(self, k, v)
        try:
            self.statusMessage = request.session['statusMessage']
            del request.session['statusMessage']
        except KeyError:
            pass
    def fsm_redirect(self, request, eventName=None, defaultURL=None,
                     addNextButton=False, vagueEvents=('next',), **kwargs):
        'check whether fsm intercepts this event and returns redirect'
        if request.method == 'POST' and \
              'launch' == request.POST.get('fsmtask', None):
            fsmName = request.POST['fsmName'] # launch specified FSM
            fsmArgs = self.fsmData[fsmName]
            return self.fsm_push(request, fsmName, fsmArgs)
        if not self.fsmStack.state: # no FSM running, so nothing to do
            return defaultURL and HttpResponseRedirect(defaultURL)
        # now we check here whether event is actually from path matching
        # this node
        referer = request.META.get('HTTP_REFERER', '')
        origin = request.META.get('HTTP_ORIGIN', '/'.join(referer.split('/')[:3]))
        if request.method == 'POST' and referer != origin + self.fsmStack.state.path \
             and eventName in vagueEvents:
            r = None # don't even call FSM with POST events from other pages.
        else: # event from current node's page
            if not eventName: # handle Next and Select POST requests
                if request.method == 'POST' and 'fsmtask' in request.POST:
                    task = request.POST['fsmtask']
                    if 'next' == task:
                        eventName = 'next' # tell FSM this is next event
                    elif task.startswith('select_'):
                        className = task[7:]
                        attr = className[0].lower() + className[1:]
                        try:
                            # TODO import KLASS_NAME_DICT from fsm should be refactored
                            klass = KLASS_NAME_DICT[className]
                            selectID = int(request.POST['selectID'])
                        except (KeyError,ValueError):
                            return HttpResponse('bad select', status=400)
                        eventName = task # pass event and object to FSM
                        kwargs[attr] = get_object_or_404(klass, pk=selectID)
                    else:
                        return HttpResponse('invalid fsm task: %s' % task,
                                            status=400)
                elif addNextButton: # must supply Next form
                    self.nextForm = NextForm()
                    set_crispy_action(request.path, self.nextForm)
            r = self.fsmStack.event(request, eventName, defaultURL=defaultURL,
                                    pageData=self, **kwargs)
        if r: # let FSM override the default URL
            return HttpResponseRedirect(r)
        elif defaultURL: # otherwise follow the default
            return HttpResponseRedirect(defaultURL)
    def render(self, request, templatefile, templateArgs=None,
               addNextButton=False, fsmGroups=(), **kwargs):
        'let fsm adjust view / redirect prior to rendering'
        self.path = request.path
        self.fsmLauncher = {}
        self.fsmData = {}
        if self.fsmStack.state:
            if self.fsmStack.state.hideTabs: # turn off tab interface
                self.navTabs = ()
            self.fsm_help_message = self.fsmStack.state.fsmNode \
              .get_help(self.fsmStack.state, request)
        else: # only show Start Activity menu if no FSM running
            for groupName, data in fsmGroups: # set up fsmLauncher
                for fsm in FSM.objects.filter(fsmgroup__group=groupName):
                    if fsm.description:
                        submitArgs = dict(title=fsm.description)
                    else:
                        submitArgs = {}
                    self.fsmLauncher[fsm.name] = (LaunchFSMForm(fsm.name,
                                    fsm.title, submitArgs=submitArgs), fsm)
                    self.fsmData[fsm.name] = data
        if templateArgs: # avoid side-effects of modifying caller's dict
            templateArgs = templateArgs.copy()
        else:
            templateArgs = {}
        templateArgs['user'] = request.user
        templateArgs['actionTarget'] = request.path
        templateArgs['pageData'] = self
        templateArgs['fsmStack'] = self.fsmStack
        templateArgs['target'] = request.session.get('target', '_self')
        if self.has_refresh_timer(request):
            templateArgs['elapsedTime'] = self.get_refresh_timer(request)
            templateArgs['refreshInterval'] = 15
        return self.fsm_redirect(request, addNextButton=addNextButton) \
            or render(request, templatefile, templateArgs, **kwargs)
    def fsm_push(self, request, name, *args, **kwargs):
        'create a new FSM and redirect to its START page'
        url = self.fsmStack.push(request, name, *args, **kwargs)
        return HttpResponseRedirect(url)
    def fsm_off_path(self):
        'True if not on current node view or Activity Center view'
        return not self.fsmStack.state.fsm_on_path(self.path) and \
          self.path != reverse('fsm:fsm_status')
    def set_refresh_timer(self, request, timer=True):
        'start or end the refresh timer'
        if timer:
            request.session['timerStart'] = time.time()
        elif 'timerStart' in request.session:
            del request.session['timerStart']
    def get_refresh_timer(self, request):
        'return duration string in format 1:03'
        secs = int(time.time() - request.session['timerStart'])
        return '%d:%02d' % (secs / 60, secs % 60)
    def has_refresh_timer(self, request):
        'return True if timer running'
        return 'timerStart' in request.session


def ul_page_data(request, unit_id, ul_id, currentTab, includeText=True,
                 tabFunc=None, includeNavTabs=True, tabArgs={}, **kwargs):
    'generate standard set of page data for a unitLesson'
    unit = get_object_or_404(Unit, pk=unit_id)
    ul = get_object_or_404(UnitLesson, pk=ul_id)
    if not tabFunc:
        tabFunc = auto_tabs
    pageData = PageData(request, title=ul.lesson.title, **kwargs)
    if includeNavTabs:
        pageData.navTabs = tabFunc(request.path, currentTab, ul,
                                   user=request.user, **tabArgs)
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
    pageData = PageData(request)
    if request.method == 'POST' and 'liveID' in request.POST:
        linkState = get_object_or_404(FSMState, pk=int(request.POST['liveID']))
        return pageData.fsm_push(request, 'livestudent', linkState=linkState)
    if pageData.fsmStack.state and \
      pageData.fsmStack.state.fsmNode.fsm.name == 'livestudent':
        liveSessions = None # already in live session, so hide launch buttons!
    else:
        liveSessions = FSMState.find_live_sessions(request.user)
    return pageData.render(request, 'ct/index.html',
                           dict(liveSessions=liveSessions))


def person_profile(request, user_id):
    'stub for basic user info page'
    person = get_object_or_404(User, pk=user_id)
    pageData = PageData(request)
    if request.method == 'POST': # signout
        if request.POST.get('task') == 'logout':
            logout(request)
            return HttpResponseRedirect(reverse('ct:home'))
    if request.user == person: # button for user to logout
        logoutForm = LogoutForm()
    else:
        logoutForm = None
    return pageData.render(request, 'ct/person.html',
                           dict(person=person, logoutForm=logoutForm,
                                next=request.path,
                                available_backends=load_backends(settings.AUTHENTICATION_BACKENDS)))


def about(request):
    pageData = PageData(request)
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
    pageData = PageData(request, title=course.title,
                        headLabel='course description',
                        headText=md2html(course.description), navTabs=navTabs)
    if request.method == 'POST': # create new courselet
        if 'oldOrder' in request.POST and not notInstructor:
            reorderForm = ReorderForm(0, len(unitTable), request.POST)
            if reorderForm.is_valid():
                oldOrder = int(reorderForm.cleaned_data['oldOrder'])
                newOrder = int(reorderForm.cleaned_data['newOrder'])
                unitTable = course.reorder_course_unit(oldOrder, newOrder,
                                                       unitTable)
                red = pageData.fsm_redirect(request, 'reorder_Unit',
                                            defaultURL=None, course=course)
                if red: # let FSM redirect us if desired
                    return red
        else:
            courseletform = NewUnitTitleForm(request.POST)
            if courseletform.is_valid():
                title = courseletform.cleaned_data['title']
                unit = course.create_unit(title, request.user)
                kwargs = dict(course_id=course_id, unit_id=unit.id)
                defaultURL = reverse('ct:unit_tasks', kwargs=kwargs)
                return pageData.fsm_redirect(request, 'create_Unit',
                                defaultURL, reverseArgs=kwargs, unit=unit)
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

    pageData = PageData(request, title=course.title,
                        navTabs=course_tabs(request.path, 'Edit'))
    if request.method == 'POST': # update course description
        courseform = CourseTitleForm(request.POST, instance=course)
        if courseform.is_valid():
            courseform.save()
            kwargs = dict(course_id=course_id)
            defaultURL = reverse('ct:course', kwargs=kwargs)
            return pageData.fsm_redirect(request, 'update_Course', defaultURL,
                                         reverseArgs=kwargs, course=course) 
    else:
        courseform = CourseTitleForm(instance=course)
    set_crispy_action(request.path, courseform)
    return pageData.render(request, 'ct/edit_course.html',
                  dict(course=course, courseform=courseform,
                       domain='https://{0}'.format(Site.objects.get_current().domain)))


def courses(request):
    """Courses view

    Render all courses for all users except anonymous.
    For `anonymous` users render courses with public access.
    """
    user = request.user
    courses = Course.objects.all()
    if isinstance(user, AnonymousUser) or user.groups.filter(name='Temporary').exists():
        courses = courses.filter(access='public')
    pageData = PageData(request)
    return pageData.render(request, 'ct/courses.html',
                           dict(courses=courses))


def courses_subscribe(request, course_id):
    """Courses subscribe view

    Subscribe user to given course by creating Role object.
    For not logged in user (Stranger) we create `anonymous` user
    and login him.
    Also we ask `anonymous` user to enter email to be able to save progress.
    """
    _id = int(time.mktime(datetime.now().timetuple()))
    user = request.user
    is_tmp_user = False
    if isinstance(user, AnonymousUser):
        is_tmp_user = True
        user = User.objects.get_or_create(username='anonymous' + str(_id),
                                          first_name='Temporary User')[0]
        temporary_group, created = Group.objects.get_or_create(name='Temporary')
        user.groups.add(temporary_group)
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        # Set expiry time to year in future
        one_year = 31536000
        request.session.set_expiry(one_year)
    course = Course.objects.get(id=course_id)
    role = 'self'
    Role.objects.get_or_create(course=course,
                               user=user,
                               role=role)
    if is_tmp_user:
        return HttpResponseRedirect('/tmp-email-ask/')
    return HttpResponseRedirect(
        reverse('ct:course_student', args=(course_id,))
    )


@login_required
def edit_unit(request, course_id, unit_id):
    course = get_object_or_404(Course, pk=course_id)
    unit = get_object_or_404(Unit, pk=unit_id)
    notInstructor = check_instructor_auth(course, request)
    if notInstructor: # redirect students to live session or student page
        return HttpResponseRedirect(reverse('ct:study_unit',
                                        args=(course_id, unit_id)))

    pageData = PageData(request, title=unit.title,
                        navTabs=unit_tabs(request.path, 'Edit'))
    cu = course.courseunit_set.get(unit=unit)
    unitform = UnitTitleForm(instance=unit)
    if request.method == 'POST':
        if request.POST.get('task') == 'release':
            cu.releaseTime = timezone.now()
            cu.save() # publish for student access
            red = pageData.fsm_redirect(request, 'release_Unit',
                                        defaultURL=None, courseUnit=cu)
            if red: # let FSM redirect us if desired
                return red
        else: # update unit description
            unitform = UnitTitleForm(request.POST, instance=unit)
            if unitform.is_valid():
                unitform.save()
                kwargs = dict(course_id=course_id, unit_id=unit_id)
                defaultURL = reverse('ct:unit_tasks', kwargs=kwargs)
                return pageData.fsm_redirect(request, 'update_Unit',
                                defaultURL, reverseArgs=kwargs, unit=unit)
    set_crispy_action(request.path, unitform)
    return pageData.render(request, 'ct/edit_unit.html',
                  dict(unit=unit, courseUnit=cu, unitform=unitform,
                       domain='https://{0}'.format(Site.objects.get_current().domain)))


def update_concept_link(request, conceptLinks, unit):
    cl = get_object_or_404(ConceptLink, pk=int(request.POST.get('clID')))
    cl.annotate_ul(unit) # add unitLesson attribute
    clform = ConceptLinkForm(request.POST, instance=cl)
    if clform.is_valid():
        clform.save()
        conceptLinks.replace(cl, clform)

def _concepts(request, pageData, msg='', ignorePOST=False, conceptLinks=None,
              toTable=None, fromTable=None, unit=None,
              actionLabel='Link to this Concept',
              errorModels=None, isError=False, **kwargs):
    'search or create a Concept'
    cset = ()
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
            update_concept_link(request, conceptLinks, unit)
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
    elif 'search' in request.GET:
        searchForm = ConceptSearchForm(request.GET)
        if searchForm.is_valid():
            s = searchForm.cleaned_data['search']
            if errorModels is not None: # search errors only
                cset = [(ul.lesson.title, get_object_url(request.path, ul))
                        for ul in UnitLesson.search_text(s, IS_ERROR)]
            else: # search correct concepts only
                cset = UnitLesson.search_text(s, IS_CONCEPT)
                cset2, wset = UnitLesson.search_sourceDB(s, unit=unit)
                cset = distinct_subset(cset2 + cset, lambda x:x.lesson.concept)
                cset = [(ul.lesson.title, get_object_url(request.path, ul, subpath=''),
                         ul) for ul in cset]
                cset += [(t[0],
                    reverse_path_args('ct:wikipedia_concept', request.path,
                            source_id=urllib.quote(t[0].encode('utf-8'), '')),
                          None) for t in wset]
                cset.sort()
            conceptForm = NewConceptForm() # let user define new concept
    if conceptForm:
        set_crispy_action(request.path, conceptForm)
    kwargs.update(dict(cset=cset, msg=msg, searchForm=searchForm,
                       toTable=toTable, fromTable=fromTable,
                       conceptForm=conceptForm, conceptLinks=conceptLinks,
                       actionLabel=actionLabel, errorModels=errorModels))
    return pageData.render(request, 'ct/concepts.html', kwargs)


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
    pageData = PageData(request, title=unit.title,
                        navTabs=unit_tabs(request.path, 'Concepts'))
    unitConcepts = unit.get_related_concepts().items()
    r = _concepts(request, pageData,
    '''To add a concept to this courselet, start by
    typing a search for relevant concepts. ''', unitConcepts=unitConcepts,
                  unit=unit, actionLabel='Add to courselet')
    if isinstance(r, Concept): # newly created concept
        defaultURL = get_object_url(request.path, r)
        return pageData.fsm_redirect(request, 'create_Concept', defaultURL,
                                     concept=r)
    return r

@login_required
def ul_concepts(request, course_id, unit_id, ul_id, tabFunc=None):
    'page for viewing or adding concept links to this UnitLesson'
    unit, unitLesson, _, pageData = ul_page_data(request, unit_id, ul_id,
                                                 'Concepts', tabFunc=tabFunc)
    cLinks = ConceptLink.objects.filter(lesson=unitLesson.lesson)
    clTable = ConceptLinkTable(cLinks, headers=('This lesson...', 'Concept'),
                               title='Concepts Linked to this Lesson')
    r = _concepts(request, pageData,
    '''To add a concept to this lesson, start by
    typing a search for relevant concepts. ''', conceptLinks=clTable,
                  unit=unit, showConceptAction=True)
    if isinstance(r, Concept):
        cl = unitLesson.lesson.conceptlink_set.create(concept=r,
                                                      addedBy=request.user)
        red = pageData.fsm_redirect(request, 'create_ConceptLink',
                                    defaultURL=None, conceptLink=cl)
        if red: # let FSM redirect us if desired
            return red
        clTable.append(cl)
        return _concepts(request, pageData,
                         'Successfully added concept.  Thank you!',
                         ignorePOST=True, conceptLinks=clTable, unit=unit,
                         showConceptAction=True)
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
    r = _concepts(request, pageData, '''To add a concept link, start by
    typing a search for relevant concepts. ''', toTable=toTable,
                  fromTable=fromTable, unit=unit, showConceptAction=True)
    if isinstance(r, Concept):
        cg = concept.relatedTo.create(toConcept=r, addedBy=request.user)
        red = pageData.fsm_redirect(request, 'create_ConceptGraph',
                                    defaultURL=None, conceptGraph=cg)
        if red: # let FSM redirect us if desired
            return red
        toTable.append(cg)
        return _concepts(request, pageData, '''Successfully added concept.
            Thank you!''', ignorePOST=True, toTable=toTable,
            fromTable=fromTable, unit=unit)
    return r

@login_required
def concept_errors(request, course_id, unit_id, ul_id):
    unit, ul, concept, pageData = ul_page_data(request, unit_id, ul_id,
                                               'Errors')
    errorModels = list(concept.relatedFrom
      .filter(relationship=ConceptGraph.MISUNDERSTANDS))
    r = _concepts(request, pageData,
    '''To add an error model to this concept, start by
    typing a search for relevant errors.''', errorModels=errorModels,
                  unit=unit, showConceptAction=True, isError=True)
    if isinstance(r, Concept):
        cg = concept.relatedFrom.create(fromConcept=r, addedBy=request.user,
                                    relationship=ConceptGraph.MISUNDERSTANDS)
        red = pageData.fsm_redirect(request, 'create_ConceptError',
                                    defaultURL=None, conceptGraph=cg)
        if red: # let FSM redirect us if desired
            return red
        errorModels.append(cg)
        return _concepts(request, pageData,
                         'Successfully added error model. Thank you!',
                         ignorePOST=True, errorModels=errorModels, unit=unit)
    return r

def create_unit_lesson(lesson, concept, unit, parentUL):
    'save new lesson, bind to concept, and append to this unit'
    lesson.save_root(concept)
    return UnitLesson.create_from_lesson(lesson, unit, order='APPEND',
                                         addAnswer=True)

def _lessons(request, pageData, concept=None, msg='',
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
    lessonSet = foundNothing = ()
    if request.method == 'POST' and not ignorePOST:
        if 'clID' in request.POST:
            update_concept_link(request, conceptLinks, unit)
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
                lesson.commitTime = timezone.now()
                lesson.changeLog = 'initial commit'
                lesson.addedBy = request.user
                return createULFunc(lesson, concept, unit, parentUL)
    elif allowSearch and 'search' in request.GET:
        searchForm = searchFormClass(request.GET)
        if searchForm.is_valid():
            s = searchForm.cleaned_data['search']
            if searchType is None:
                searchType = searchForm.cleaned_data['searchType']
            lessonSet = UnitLesson.search_text(s, searchType)
            foundNothing = not lessonSet
    if showReorderForm and lessonTable:
        for ul in lessonTable:
            ul.reorderForm = ReorderForm(ul.order, len(lessonTable))
    if lessonForm:
        set_crispy_action(request.path, lessonForm)
    kwargs.update(dict(lessonSet=lessonSet, searchForm=searchForm, msg=msg,
                       lessonForm=lessonForm, conceptLinks=conceptLinks,
                       actionLabel=actionLabel, lessonTable=lessonTable,
                       creationInstructions=creationInstructions,
                       showReorderForm=showReorderForm,
                       foundNothing=foundNothing))
    return pageData.render(request, templateFile, kwargs)

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
    r = _lessons(request, pageData, concept, conceptLinks=clTable,
                 unit=unit, allowSearch=False,
                 creationInstructions=creationInstructions)
    if isinstance(r, UnitLesson): # created new lesson
        defaultURL = None
        if r.lesson.kind == Lesson.ORCT_QUESTION:
            if r.get_errors().count() == 0: # copy error models from concept
                concept.copy_error_models(r)
            if getattr(r, '_answer', None): # redirect to edit empty answer
                defaultURL = reverse('ct:edit_lesson',
                                     args=(course_id, unit_id, r._answer.id,))
        red = pageData.fsm_redirect(request, 'create_UnitLesson', defaultURL,
                                    unitLesson=r)
        if red: # let FSM redirect us if desired
            return red
        clTable = make_cl_table(concept, unit) # refresh table
        return _lessons(request, pageData, concept,
            'Successfully added lesson. Thank you!', ignorePOST=True,
            conceptLinks=clTable, unit=unit, allowSearch=False,
            creationInstructions=creationInstructions)
    return r

@login_required
def unit_tasks(request, course_id, unit_id):
    'suggest next steps on this courselet'
    course = get_object_or_404(Course, pk=course_id)
    unit = get_object_or_404(Unit, pk=unit_id)
    cu = course.courseunit_set.get(unit=unit)
    pageData = PageData(request, title=unit.title,
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
    fsmGroups=[('teach/unit_tasks', dict(unit=unit, course=course))]
    if cu.releaseTime and cu.releaseTime < timezone.now() \
      and not unit.no_lessons():
        fsmGroups.append(('teach/unit/published',
                          dict(unit=unit, course=course)))
    return pageData.render(request, 'ct/unit_tasks.html',
                           dict(unit=unit, taskTable=taskTable,
                                courseUnit=cu), fsmGroups=fsmGroups)

    


def copy_unit_lesson(ul, concept, unit, addedBy, parentUL):
    'copy lesson and append to this unit'
    if ul.unit == unit:
        return 'Lesson already in this unit, so no change made.'
    return ul.copy(unit, addedBy, order='APPEND')

@login_required
def unit_lessons(request, course_id, unit_id, lessonTable=None,
                 currentTab='Lessons', showReorderForm=True,
                 msg='''You can search for a lesson to add
          to this courselet by entering a search term below.
          (To write a new lesson, click on the Concepts tab to identify
          what concept your new lesson will be about).''', **kwargs):
    unit = get_object_or_404(Unit, pk=unit_id)
    pageData = PageData(request, title=unit.title,
                        navTabs=unit_tabs(request.path, currentTab))
    if lessonTable is None:
        lessonTable = unit.get_exercises()
    r = _lessons(request, pageData, msg=msg, 
                  unit=unit, showReorderForm=showReorderForm,
                  lessonTable=lessonTable, selectULFunc=copy_unit_lesson, **kwargs)
    if isinstance(r, UnitLesson):
        red = pageData.fsm_redirect(request, 'create_UnitLesson',
                                    defaultURL=None, unitLesson=r)
        if red: # let FSM redirect us if desired
            return red
        lessonTable.append(r)
        return _lessons(request, pageData, msg='''Successfully added lesson.
            Thank you!''', ignorePOST=True, showReorderForm=showReorderForm,
            unit=unit, lessonTable=lessonTable, **kwargs)
    return r

@login_required
def unit_resources(request, course_id, unit_id):
    unit = get_object_or_404(Unit, pk=unit_id)
    lessonTable = list(unit.unitlesson_set \
            .filter(kind=UnitLesson.COMPONENT, order__isnull=True))
    lessonTable.sort(lambda x,y:cmp(x.lesson.title, y.lesson.title))
    return unit_lessons(request, course_id, unit_id, lessonTable,
                        'Resources', msg='', showReorderForm=False, allowSearch=False)


@login_required
def wikipedia_concept(request, course_id, unit_id, source_id):
    'page for viewing or adding Wikipedia concept to this courselet'
    unit = get_object_or_404(Unit, pk=unit_id)
    sourceID = urllib.unquote(source_id).encode('iso-8859-1').decode('utf-8')
    pageData = PageData(request, title=unit.title,
                        navTabs=unit_tabs(request.path, 'Concepts'))
    addForm = push_button(request, 'add', 'Add to this courselet')
    if not addForm: # user clicked Add
        concept, lesson = Concept.get_from_sourceDB(sourceID, request.user)
        ul = UnitLesson.create_from_lesson(lesson, unit)
        kwargs = dict(course_id=course_id, unit_id=unit_id, ul_id=ul.pk)
        defaultURL = reverse('ct:concept_teach', kwargs=kwargs)
        return pageData.fsm_redirect(request, 'create_Concept', defaultURL,
                                     reverseArgs=kwargs, unitLesson=ul)
    lesson = Lesson.get_from_sourceDB(sourceID, request.user, doSave=False)
    if lesson.pk is not None:
        addForm = None
    return pageData.render(request, 'ct/wikipedia.html',
                           dict(lesson=lesson, addForm=addForm))

@login_required
def ul_teach(request, course_id, unit_id, ul_id):
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id, 'Home',
                                         False)
    addForm = roleForm = answer = None
    if pageData.fsmStack.state and pageData.fsmStack.state.isLiveSession:
        query = Q(unitLesson=ul, activity=pageData.fsmStack.state.activity,
                  selfeval__isnull=False, kind=Response.ORCT_RESPONSE)
        n = pageData.fsmStack.state.linkChildren.count() # livesession students
        statusTable, evalTable, n = Response.get_counts(query, n=n)
        answer = ul.get_answers().all()[0]
    else: # default: all responses w/ selfeval
        query = Q(unitLesson=ul, selfeval__isnull=False,
                  kind=Response.ORCT_RESPONSE)
        statusTable, evalTable, n = Response.get_counts(query)
    if ul.unit == unit: # ul is part of this unit
        if request.method == 'POST':
            roleForm = LessonRoleForm('', request.POST)
            if roleForm.is_valid():
                if roleForm.cleaned_data['role'] == UnitLesson.RESOURCE_ROLE:
                    ul.order = None
                    ul.save()
                    unit.reorder_exercise()
                elif ul.order is None:
                    unit.append(ul, request.user)
        else:
            if ul.order is not None:
                initial = UnitLesson.LESSON_ROLE
            else:
                initial = UnitLesson.RESOURCE_ROLE
            roleForm = LessonRoleForm(initial)
    elif ul.kind == UnitLesson.COMPONENT: # offer option to add to this unit
        addForm = push_button(request, 'add', 'Add to this Courselet') 
        if not addForm:
            ulNew = unit.append(ul, request.user)
            kwargs = dict(course_id=course_id, unit_id=unit_id, ul_id=ulNew.pk)
            defaultURL = reverse('ct:ul_teach', kwargs=kwargs)
            if request.resolver_match.view_name == 'ct:concept_teach':
                eventName = 'add_Concept'
            else:
                eventName = 'add_UnitLesson'
            return pageData.fsm_redirect(request, eventName, defaultURL,
                                         reverseArgs=kwargs, unitLesson=ulNew)

    return pageData.render(request, 'ct/lesson.html',
                  dict(unitLesson=ul, unit=unit, statusTable=statusTable,
                       evalTable=evalTable, answer=answer, addForm=addForm,
                       roleForm=roleForm), addNextButton=True)

def push_button(request, taskName='start', label='Start', formClass=TaskForm):
    'return None if button was pressed, otherwise return button form'
    if request.method == 'POST' and request.POST.get('task', '') == taskName:
        return None
    else: # provide button for starting some POST action
        taskForm = formClass(taskName, label)
        set_crispy_action(request.path, taskForm)
        return taskForm

@login_required
def live_question(request, course_id, unit_id, ul_id):
    'show response progress during live question'
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id, 'Home',
                                         False)
    startForm = None
    if not pageData.has_refresh_timer(request):
        startForm = push_button(request)
        if not startForm:
            pageData.set_refresh_timer(request) # start the timer
    query = Q(unitLesson=ul, activity=pageData.fsmStack.state.activity,
              kind=Response.ORCT_RESPONSE)
    n = pageData.fsmStack.state.linkChildren.count() # live session students
    statusTable = Response.get_counts(query, n=n, tableKey='confidence',
                    simpleTable=True, title='Student Responses')[0]
    return pageData.render(request, 'ct/lesson.html',
                  dict(unitLesson=ul, unit=unit, statusTable=statusTable,
                       startForm=startForm), addNextButton=True)


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
    return pageData.render(request, 'ct/ul_tasks.html',
                  dict(unitLesson=ul, unit=unit, errorTable=errorTable,
                       newInquiries=newInquiries))

    
@login_required
def edit_lesson(request, course_id, unit_id, ul_id):
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id, 'Edit',
                                         False)
    course = get_object_or_404(Course, pk=course_id)
    notInstructor = check_instructor_auth(course, request)
    if ul.get_type() == IS_LESSON:
        if ul.lesson.kind == Lesson.ANSWER:
            formClass = AnswerLessonForm
        else:
            formClass = LessonForm
    else:
        formClass = ErrorForm
    if notInstructor:
        titleform = None
    else: # let instructor edit this lesson
        titleform = formClass(instance=ul.lesson, initial=dict(changeLog=''))
        if request.method == 'POST':
            if 'title' in request.POST:
                lesson = ul.checkout(request.user)
                titleform = formClass(request.POST, instance=lesson)
                if titleform.is_valid():
                    titleform.save(commit=False)
                    ul.checkin(lesson)
                    defaultURL = get_object_url(request.path, ul)
                    return pageData.fsm_redirect(request, 'update_UnitLesson',
                                                 defaultURL, unitLesson=ul)
            elif request.POST.get('task') == 'delete':
                ul.delete()
                unit.reorder_exercise() # renumber all lessons
                kwargs = dict(course_id=course_id, unit_id=unit_id)
                defaultURL = reverse('ct:unit_lessons', kwargs=kwargs)
                return pageData.fsm_redirect(request, 'delete_UnitLesson',
                                defaultURL, reverseArgs=kwargs, unit=unit)
        set_crispy_action(request.path, titleform)
    return pageData.render(request, 'ct/edit_lesson.html',
                  dict(unitLesson=ul, atime=display_datetime(ul.atime),
                       titleform=titleform))


def create_error_ul(lesson, concept, unit, parentUL):
    'save lesson as error model linked to concept and question UnitLesson'
    return lesson.save_as_error_model(concept, parentUL)

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
    r = _lessons(request, pageData, concept, msg, unit=unit, 
                  seTable=seTable, templateFile='ct/errors.html',
                  showNovelErrors=showNovelErrors,
                  novelErrors=novelErrors, responseFilterForm=neForm,
                  creationInstructions=creationInstructions,
                  newLessonFormClass=NewErrorForm, parentUL=ul,
                  createULFunc=create_error_ul, selectULFunc=copy_error_ul,
                  searchType=IS_ERROR, actionLabel='Add error model')
    if isinstance(r, UnitLesson):
        red = pageData.fsm_redirect(request, 'create_ErrorModel',
                                    defaultURL=None, unitLesson=r)
        if red: # let FSM redirect us if desired
            return red
        seTable.append((r, fmt_count(0, n or 1)))
        return _lessons(request, pageData, concept,
            msg='Successfully added error model.  Thank you!',
            ignorePOST=True, unit=unit, seTable=seTable, 
            templateFile='ct/errors.html', novelErrors=novelErrors,
            creationInstructions=creationInstructions,
            newLessonFormClass=NewErrorForm)
    return r

def create_resolution_ul(lesson, em, unit, parentUL):
    'create UnitLesson as resolution linked to error model'
    return parentUL.save_resolution(lesson)

def link_resolution_ul(ul, em, unit, addedBy, parentUL):
    'link ul as resolution for error model'
    return parentUL.copy_resolution(ul, addedBy)


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
    r = _lessons(request, pageData, em, msg, lessonTable=lessonTable,
                 unit=unit, actionLabel='Add to suggestion list',
                 creationInstructions=creationInstructions,
                 createULFunc=create_resolution_ul,
                 selectULFunc=link_resolution_ul, parentUL=ul)
    if isinstance(r, UnitLesson):
        red = pageData.fsm_redirect(request, 'create_Resolution',
                                    defaultURL=None, unitLesson=r)
        if red: # let FSM redirect us if desired
            return red
        if r not in lessonTable:
            lessonTable.append(r)
        return _lessons(request, pageData, em,
                  msg='Successfully added resolution. Thank you!',
                  ignorePOST=True, lessonTable=lessonTable, unit=unit,
                  actionLabel='Add to suggestion list',
                  creationInstructions=creationInstructions, parentUL=ul)
    return r

@login_required
def error_resources(request, course_id, unit_id, ul_id):
    unit, ul, concept, pageData = ul_page_data(request, unit_id, ul_id,
                                               'Resources')
    toConcepts = concept.relatedTo.all()
    fromConcepts = concept.relatedFrom.all()
    testLessons = concept.get_error_tests()
    alternativeDefs = ul.get_alternative_defs()
    return pageData.render(request, 'ct/error_resources.html',
                  dict(toConcepts=toConcepts,
                       fromConcepts=fromConcepts, testLessons=testLessons,
                       alternativeDefs=alternativeDefs))

###########################################################
# welcome mat refactored student UI for courses

@login_required
def study_unit(request, course_id, unit_id):
    course = get_object_or_404(Course, pk=course_id)
    unit = get_object_or_404(Unit, pk=unit_id)
    pageData = PageData(request, title=unit.title)
    if UnitStatus.objects.filter(user=request.user, unit=unit).exists() \
      or Response.objects.filter(unitLesson__unit=unit, author=request.user).exists():
        pageData.navTabs = unit_tabs_student(request.path, 'Study') # show tabs
    try:
        unitLesson = unit.unitlesson_set.get(order=0)
    except UnitLesson.DoesNotExist:
        startURL = None
    else:
        startURL = unitLesson.get_study_url(course_id)
    return pageData.render(request, 'ct/study_unit.html',
                dict(unit=unit, startURL=startURL))


@login_required
def slideshow(request, course_id, unit_id):
    'launcher for viewing courselet as a slideshow'
    course = get_object_or_404(Course, pk=course_id)
    unit = get_object_or_404(Unit, pk=unit_id)
    pageData = PageData(request, title=unit.title)
    startForm = push_button(request)
    if not startForm: # user clicked Start
        return pageData.fsm_push(request, 'slideshow',
                                 dict(unit=unit, course=course))
    return pageData.render(request, 'ct/study_unit.html',
                dict(unit=unit, startForm=startForm))

@login_required
def unit_tasks_student(request, course_id, unit_id):
    'suggest next steps on this courselet'
    unit = get_object_or_404(Unit, pk=unit_id)
    pageData = PageData(request, title=unit.title,
                        navTabs=unit_tabs_student(request.path, 'Tasks'))
    taskTable = [(ul, 'start')
                 for ul in unit.get_unanswered_uls(request.user)]
    taskTable += [(ul, 'selfeval')
                  for ul in unit.get_selfeval_uls(request.user)]
    taskTable += [(ul, 'classify')
                  for ul in unit.get_serrorless_uls(request.user)]
    taskTable += [(ul, 'resolve')
                  for ul in unit.get_unresolved_uls(request.user)]
    return pageData.render(request, 'ct/unit_tasks_student.html',
                           dict(unit=unit, taskTable=taskTable))

def unit_lessons_student(request, course_id, unit_id, lessonTable=None,
                         currentTab='Lessons'):
    unit = get_object_or_404(Unit, pk=unit_id)
    pageData = PageData(request, title=unit.title,
                        navTabs=unit_tabs_student(request.path, currentTab))
    if lessonTable is None:
        lessonTable = unit.unitlesson_set \
            .filter(kind=UnitLesson.COMPONENT, order__isnull=False) \
            .order_by('order')
    return pageData.render(request, 'ct/lessons_student.html',
                           dict(lessonTable=lessonTable))

def unit_resources_student(request, course_id, unit_id):
    """
    Show additional lesson resources not included in Concepts tab
    """
    unit = get_object_or_404(Unit, pk=unit_id)
    lessonTable = list(unit.unitlesson_set \
            .filter(kind=UnitLesson.COMPONENT, order__isnull=True,
                    lesson__concept__isnull=True)) # exclude concepts
    lessonTable.sort(lambda x,y:cmp(x.lesson.title, y.lesson.title))
    return unit_lessons_student(request, course_id, unit_id, lessonTable,
                                'Resources')

@login_required
def unit_concepts_student(request, course_id, unit_id):
    'student concept glossary for  this courselet'
    unit = get_object_or_404(Unit, pk=unit_id)
    pageData = PageData(request, title=unit.title,
                        navTabs=unit_tabs_student(request.path, 'Concepts'))
    l1 = list(UnitLesson.objects.filter(kind=UnitLesson.COMPONENT,
        lesson__concept__conceptlink__lesson__unitlesson__unit=unit)
        .distinct())
    l2 = list(unit.unitlesson_set.filter(kind=UnitLesson.COMPONENT,
        lesson__concept__isnull=False))
    conceptTable = distinct_subset(l1 + l2)
    conceptTable.sort(lambda x,y:cmp(x.lesson.concept.title,
                                     y.lesson.concept.title))
    return pageData.render(request, 'ct/concepts_student.html',
                           dict(conceptTable=conceptTable))


def lesson_next_url(request, ul, course_id):
    'get URL for the next lesson, or URL to exit to courselet tasks view'
    try:
        nextUL = ul.get_next_lesson()
    except UnitLesson.DoesNotExist:
        return get_base_url(request.path, ['tasks']) # exit to unit tasks view
    return nextUL.get_study_url(course_id)
    
        
def lesson(request, course_id, unit_id, ul_id, redirectQuestions=True):
    'show student a reading assignment'
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id, 'Study', includeText=False)
    if request.method == 'POST':
        nextForm = NextLikeForm(request.POST)
        if nextForm.is_valid():
            if nextForm.cleaned_data['liked']:
                liked = Liked(unitLesson=ul, addedBy=request.user)
                liked.save()
            defaultURL = lesson_next_url(request, ul, course_id)
            # let fsm redirect this event if it wishes
            return pageData.fsm_redirect(request, 'next', defaultURL)
    elif redirectQuestions and ul.lesson.kind == Lesson.ORCT_QUESTION:
        return HttpResponseRedirect(request.path + 'ask/')
    pageData.nextForm = NextLikeForm()
    set_crispy_action(request.path, pageData.nextForm)
    return pageData.render(request, 'ct/lesson_student.html',
                           dict(unitLesson=ul, unit=unit))

def lesson_read(request, course_id, unit_id, ul_id):
    """
    present lesson as passive reading assignment
    """
    return lesson(request, course_id, unit_id, ul_id, redirectQuestions=False)
    
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
    return pageData.render(request, 'ct/lesson_tasks.html',
                           dict(unitLesson=ul, unit=unit,
                                responseTable=responseTable,
                                errorTable=errorTable))
    
def ul_errors_student(request, course_id, unit_id, ul_id):
    return ul_errors(request, course_id, unit_id, ul_id, showNETable=False)

@login_required
def study_concept(request, course_id, unit_id, ul_id):
    unit, ul, concept, pageData = ul_page_data(request, unit_id, ul_id,
                                               'Study')
    defsTable = distinct_subset(UnitLesson.objects
        .filter(lesson__concept=concept).exclude(treeID=ul.treeID))
    return pageData.render(request, 'ct/concept_student.html',
                           dict(unitLesson=ul, defsTable=defsTable))

@login_required
def concept_lessons_student(request, course_id, unit_id, ul_id):
    unit, ul, concept, pageData = ul_page_data(request, unit_id, ul_id,
                                               'Lessons')
    clTable = concept.get_conceptlinks(unit)
    return pageData.render(request, 'ct/concept_lessons_student.html',
                  dict(unitLesson=ul, unit=unit, clTable=clTable))


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
                red = pageData.fsm_redirect(request, 'update_StudentError',
                                            defaultURL=None, studentError=se)
                if red: # let FSM redirect us if desired
                    return red
        else:
            form = ErrorStatusForm(instance=se)
    return pageData.render(request, 'ct/resolutions_student.html',
                  dict(unitLesson=ul, unit=unit,
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
            red = pageData.fsm_redirect(request, 'create_Comment',
                                        defaultURL=None, response=r)
            if red: # let FSM redirect us if desired
                return red
            form = CommentForm() # clear the form
    else:
        form = CommentForm()
    faqs = ul.response_set.filter(kind=Response.STUDENT_QUESTION) \
         .order_by('atime')
    faqTable = []
    for r in faqs:
        faqTable.append((r, r.inquirycount_set.count()))
    return pageData.render(request, 'ct/faq_student.html',
                           dict(unitLesson=ul, unit=unit,
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
                red = pageData.fsm_redirect(request, 'create_Reply',
                                            defaultURL=None, response=reply)
                if red: # let FSM redirect us if desired
                    return red
                form = ReplyForm() # clear the form
    pageData.numPeople = inquiry.inquirycount_set.count()
    replyTable = [(r, r.studenterror_set.all())
                  for r in inquiry.response_set.all().order_by('atime')]
    faqTable = inquiry.faq_set.all() # ORCT created for this thread
    errorTable = inquiry.studenterror_set.all()
    return pageData.render(request, 'ct/thread_student.html',
                  dict(unitLesson=ul, unit=unit,
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
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id, 'Study',
                                         includeText=False)
    if request.method == 'POST':
        form = ResponseForm(request.POST)
        if form.is_valid():
            activity = pageData.fsmStack.state and \
                       pageData.fsmStack.state.activity
            r = save_response(form, ul, request.user, course_id,
                              activity=activity)
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

def get_answer_html(unitLesson):
    'get HTML text for answer associated with this lesson, if any'
    try:
        answer = unitLesson.get_answers()[0]
    except IndexError:
        return '(author has not provided an answer)'
    else:
        return md2html(answer.lesson.text)


@login_required
def assess(request, course_id, unit_id, ul_id, resp_id):
    'student self-assessment'
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id, 'Study')
    r = get_object_or_404(Response, pk=resp_id)
    if request.method == 'POST':
        form = SelfAssessForm(request.POST)
        if form.is_valid():
            r.selfeval = form.cleaned_data['selfeval']
            r.status = form.cleaned_data['status']
            r.save()
            if form.cleaned_data['liked']:
                liked = Liked(unitLesson=r.unitLesson,
                              addedBy=request.user)
                liked.save()
            if r.selfeval == Response.CORRECT: # just go on to next lesson
                eventName = 'next'
                defaultURL = lesson_next_url(request, r.unitLesson, course_id)
            else: # ask student to assess their errors
                eventName = 'error' # student made an error
                defaultURL = reverse('ct:assess_errors',
                    args=(course_id, unit_id, ul_id, resp_id))
            return pageData.fsm_redirect(request, eventName, defaultURL)
    else:
        form = SelfAssessForm()
    answer = get_answer_html(r.unitLesson)
    set_crispy_action(request.path, form)
    return pageData.render(request, 'ct/assess.html',
                dict(response=r, answer=answer, assessForm=form,
                     showAnswer=True))

@login_required
def assess_errors(request, course_id, unit_id, ul_id, resp_id):
    'classify error(s) in a given student response'
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id, 'Study')
    r = get_object_or_404(Response, pk=resp_id)
    allErrors = list(r.unitLesson.get_errors()) + unit.get_aborts()
    if request.method == 'POST':
        if request.user == r.author:
            status = r.status
        else:
            status = NEED_REVIEW_STATUS
        for emID in request.POST.getlist('emlist', []):
            em = get_object_or_404(UnitLesson, pk=int(emID))
            activity = pageData.fsmStack.state and \
                       pageData.fsmStack.state.activity
            se = r.studenterror_set.create(errorModel=em, author=request.user,
                                           status=status, activity=activity)
        defaultURL = lesson_next_url(request, ul, course_id)
        return pageData.fsm_redirect(request, 'next', defaultURL)
    answer = get_answer_html(r.unitLesson)
    return pageData.render(request, 'ct/assess.html',
                dict(response=r, answer=answer, errorModels=allErrors,
                     showAnswer=False))
