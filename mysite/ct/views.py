from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
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
from ct.templatetags.ct_extras import md2html, get_base_url, get_object_url, is_teacher_url, display_datetime
from ct.fsm import FSMStack

######################################################
# student live session UI

def live_response(request, r=None):
    'if in live session, synchronize students to desired stage'
    fsmStack = FSMStack(request)
    try:
        liveSession = fsmStack.state.liveSession
    except AttributeError:
        return None, None
    if liveSession.endTime: # all done
        rm_live_user(request, liveSession)
        fsmStack.pop(request)
        return None, None
    stage, r = liveSession.get_next_stage(request.user, r)
    if stage == liveSession.WAIT: # just wait
        return render(request, 'ct/wait.html',
                      dict(actionTarget=reverse('ct:live'))), liveSession
    liveQuestion = liveSession.liveQuestion
    url = liveQuestion.next_url(stage, r)
    if r and r.liveQuestion != liveQuestion:
        return render(request, 'ct/wait.html',
                    dict(actionTarget=url,
                    message='''Please click Next to join the new question
                    the instructor has assigned.  You can return to follow
                    up on this exercise after class (online).''')), liveSession
    return HttpResponseRedirect(url), liveSession


def start_live_user(request, courseQuestion):
    try:
        liveSession = LiveSession.get_from_request(request)
    except KeyError:
        return
    if liveSession.liveQuestion and \
      liveSession.liveQuestion.courseQuestion == courseQuestion:
        liveSession.liveQuestion.start_user_session(request.user)

@login_required
def respond_cq(request, cq_id):
    courseQuestion = get_object_or_404(CourseQuestion, pk=cq_id)
    return _respond(request, courseQuestion.question, courseQuestion)


@login_required
def respond(request, ct_id):
    return _respond(request, get_object_or_404(Question, pk=ct_id))


@login_required
def live_session(request):
    'keep student waiting until instructor advances live exercise'
    response, liveSession = live_response(request)
    if response:
        return response
    return HttpResponseRedirect(reverse('ct:home'))

    
#############################################################
# instructor CourseQuestion live session UI
    
def check_instructor_auth(course, request):
    role = course.get_user_role(request.user)
    if role != Role.INSTRUCTOR:
        return HttpResponse("Only the instructor can access this",
                            status_code=403)

def check_liveinst_auth(request):
    fsmStack = FSMStack(request)
    liveSession = fsmStack.state.liveSession
    liveQuestion = fsmStack.state.liveQuestion
    courseQuestion = liveQuestion.courseQuestion
    return (check_instructor_auth(liveSession.course, request),
            liveQuestion, courseQuestion, fsmStack)
    
@login_required
def live_start(request):
    'instructor live session START page'
    notInstructor, liveQuestion, courseQuestion, fsmStack = check_liveinst_auth(request)
    if notInstructor:
        return notInstructor
    if request.method == 'POST':
        if request.POST.get('task') == 'live_control':
            liveQuestion.startTime = timezone.now()
            liveQuestion.save() # save time stamp
            return fsmStack.transition(request, 'live_control')
    return render(request, 'ct/livestart.html',
                  dict(courseQuestion=courseQuestion,
                       actionTarget=request.path,
                       qtext=md2html(courseQuestion.question.qtext),
                       answer=md2html(courseQuestion.question.answer)))

@login_required
def live_control(request):
    'instructor live session UI for monitoring student responses'
    notInstructor, liveQuestion, courseQuestion, fsmStack = check_liveinst_auth(request)
    if notInstructor: # must be instructor to use this interface
        return notInstructor
    responses = liveQuestion.response_set.all() # responses from live session
    sure = responses.filter(confidence=Response.SURE)
    unsure = responses.filter(confidence=Response.UNSURE)
    guess = responses.filter(confidence=Response.GUESS)
    nuser = liveQuestion.liveuser_set.count() # count logged in users
    counts = [guess.count(), unsure.count(), sure.count(), 0]
    counts[-1] = nuser - sum(counts)
    sec = (timezone.now() - liveQuestion.startTime).seconds
    elapsedTime = '%d:%02d' % (sec / 60, sec % 60)
    ndisplay = 25 # set default values
    sortOrder = '-atime'
    rlform = ResponseListForm()
    if request.method == 'POST': # create a new ErrorModel
        if request.POST.get('task') == 'live_end':
            liveQuestion.liveStage = liveQuestion.ASSESSMENT_STAGE
            liveQuestion.save()
            return fsmStack.transition(request, 'live_end')
        else:
            emform = ErrorModelForm(request.POST)
            if emform.is_valid():
                e = emform.save(commit=False)
                e.author = request.user
                e.save()
                courseQuestion.courseerrormodel_set.create(errorModel=e,
                    course=courseQuestion.courselet.course,
                    addedBy=request.user)
    else:
        emform = ErrorModelForm()
        if request.GET: # new query parameters for displaying responses
            rlform = ResponseListForm(request.GET)
            if rlform.is_valid():
                ndisplay = int(rlform.cleaned_data['ndisplay'])
                sortOrder = rlform.cleaned_data['sortOrder']
    responses.order_by(sortOrder) # apply the desired sort order
    set_crispy_action(request.path, emform)
    return render(request, 'ct/control.html',
                  dict(courseQuestion=courseQuestion,
                       qtext=md2html(courseQuestion.question.qtext),
                       answer=md2html(courseQuestion.question.answer),
                       counts=counts, elapsedTime=elapsedTime, 
                       actionTarget=request.path,
                       emform=emform, responses=responses[:ndisplay],
                       rlform=rlform))

def count_vectors(data, start=None, end=None):
    d = {}
    for t in data:
        k = t[start:end]
        d[k] = d.get(k, 0) + 1
    return d

def make_table(d, keyset, func, t=()):
    keys = keyset[0]
    keyset = keyset[1:]
    l = []
    for k in keys:
        kt = t + (k,)
        if keyset:
            l.append(make_table(d, keyset, func, kt))
        else:
            l.append(func(d.get(kt, 0)))
    return l

@login_required
def live_end(request):
    'instructor live session UI for monitoring student self-assessment'
    notInstructor, liveQuestion, courseQuestion, fsmStack = check_liveinst_auth(request)
    if notInstructor: # must be instructor to use this interface
        return notInstructor
    if request.method == 'POST':
        if request.POST.get('task') == 'finish':
            liveQuestion.end()
            return fsmStack.transition(request, 'live_session',
                        dict(courselet_id=courseQuestion.courselet.id))
    n = liveQuestion.response_set.count() # count all responses from live session
    responses = liveQuestion.response_set.exclude(selfeval=None) # self-assessed
    statusCounts, evalCounts, ndata = status_confeval_tables(responses, n)
    errorCounts = liveQuestion.errormodel_table(ndata)
    sec = (timezone.now() - liveQuestion.startTime).seconds
    elapsedTime = '%d:%02d' % (sec / 60, sec % 60)
    return render(request, 'ct/end.html',
                  dict(courseQuestion=courseQuestion,
                       qtext=md2html(courseQuestion.question.qtext),
                       answer=md2html(courseQuestion.question.answer),
                       statusCounts=statusCounts, elapsedTime=elapsedTime,
                       evalCounts=evalCounts, actionTarget=request.path,
                       refreshRate=15, errorCounts=errorCounts))


def status_confeval_tables(responses, n):
    data = [(r.confidence, r.selfeval, r.status) for r in responses]
    ndata = len(data)
    if ndata == 0:
        return (), (), 0
    statusCounts = count_vectors(data, -1)
    evalCounts = count_vectors(data, end=2)
    fmt_count = lambda c: '%d (%.0f%%)' % (c, c * 100. / n)
    confKeys = [t[0] for t in Response.CONF_CHOICES]
    confLabels = [t[1] for t in Response.CONF_CHOICES]
    evalKeys = [t[0] for t in Response.EVAL_CHOICES]
    statusKeys = [t[0] for t in Response.STATUS_CHOICES]
    statusCounts = make_table(statusCounts, (statusKeys,), fmt_count)
    statusCounts.append(fmt_count(n - ndata))
    if ndata > 0: # build the self-assessment table
        fmt_count = lambda c: '%d (%.0f%%)' % (c, c * 100. / ndata)
        evalCounts = make_table(evalCounts, (confKeys, evalKeys), fmt_count)
        evalCounts = zip(confLabels, evalCounts)
    else: # no data so don't display anything
        evalCounts = ()
    return statusCounts, evalCounts, ndata

######################################################3
# UI for searching, creating Question entries

def new_question(request):
    'create new Question from POST form data'
    form = NewQuestionForm(request.POST)
    if form.is_valid():
        question = form.save(commit=False)
        question.author = request.user
        question.save()
        return question, form
    return None, form

def new_lesson(request):
    'create new Lesson from POST form data'
    form = NewLessonForm(request.POST)
    if form.is_valid():
        lesson = form.save(commit=False)
        lesson.addedBy = request.user
        lesson.rustID = ''
        lesson.save()
        return lesson, form
    return None, form

@login_required
def questions(request):
    'search or create a Question'
    qset = ()
    if request.method == 'POST':
        question, qform = new_question(request)
        if question:
            return HttpResponseRedirect(reverse('ct:question',
                                                args=(question.id,)))
    elif 'search' in request.GET:
        searchForm = QuestionSearchForm(request.GET)
        if searchForm.is_valid():
            s = searchForm.cleaned_data['search']
            qset = Question.objects.filter(Q(title__icontains=s) |
                                           Q(qtext__icontains=s) |
                                           Q(answer__icontains=s))
    else:
        searchForm = QuestionSearchForm()
    return render(request, 'ct/questions.html',
                  dict(qset=qset, actionTarget=request.path,
                       searchForm=searchForm))

@ensure_csrf_cookie
def question(request, ct_id):
    'generic page for a specific question'
    q = get_object_or_404(Question, pk=ct_id)
    qform = QuestionForm(instance=q)
    if request.method == 'POST':
        qform = QuestionForm(request.POST, instance=q)
        if qform.is_valid():
            qform.save()    
    try:
        sl = StudyList.objects.get(question=q, user=request.user)
        inStudylist = 1
    except ObjectDoesNotExist:
        inStudylist = 0
    responses = q.response_set.exclude(selfeval=None) # self-assessed
    n = len(responses)
    statusCounts, evalCounts, ndata = status_confeval_tables(responses, n)
    errorCounts = q.errormodel_table(ndata)
    set_crispy_action(request.path, qform)
    return render(request, 'ct/question.html',
                  dict(question=q, qtext=md2html(q.qtext),
                       answer=md2html(q.answer),
                       qform=qform,
                       actionTarget=request.path,
                       inStudylist=inStudylist,
                       allowEdit=(q.author == request.user),
                       atime=display_datetime(q.atime),
                       statusCounts=statusCounts, evalCounts=evalCounts,
                       errorCounts=errorCounts))


@login_required
def flag_question(request, ct_id):
    'JSON POST for adding / removing question from study list'
    q = get_object_or_404(Question, pk=ct_id)
    if request.is_ajax() and request.method == 'POST':
        newstate = int(request.POST['state'])
        try:
            sl = StudyList.objects.get(question=q, user=request.user)
            if not newstate:
                sl.delete()
        except ObjectDoesNotExist:
            if newstate:
                q.studylist_set.create(user=request.user)
        data = json.dumps(dict(newstate=newstate))
        return HttpResponse(data, content_type='application/json')


@login_required
def question_concept(request, ct_id):
    q = get_object_or_404(Question, pk=ct_id)
    if q.author != request.user:
        return HttpResponse("Only the author can edit this",
                            status_code=403)
    r = _concepts(request, '''Please choose a Concept that best describes
    what this question aims to test, by entering a search term to
    find relevant concepts.''')
    if isinstance(r, Concept): # user chose a concept to link
        q.concept = r # link question to this concept
        q.save()
        return HttpResponseRedirect(reverse('ct:question', args=(q.id,)))
    return r

@login_required
def error_model(request, em_id):
    em = get_object_or_404(ErrorModel, pk=em_id)
    if em.author != request.user:
        return HttpResponse("Only the author can edit this",
                            status_code=403)
    relatedErrors = () # need to fix this!!!
    if em.alwaysAsk:
        n = Response.objects.count()
    else:
        n = Response.objects.filter(selfeval__isnull=False,
                courseQuestion__courseerrormodel__errorModel=em).count()
    if n > 0:
        nerr = Response.objects.filter(
            studenterror__courseErrorModel__errorModel=em).count()
        emPercent = '%.0f' % (nerr * 100. / n)
    else:
        emPercent = None
    
    emform = ErrorModelForm(instance=em)
    nrform = NewRemediationForm()
    if request.method == 'POST':
        if 'description' in request.POST:
            emform = ErrorModelForm(request.POST, instance=em)
            if emform.is_valid():
                emform.save()
        elif 'title' in request.POST:
            nrform = NewRemediationForm(request.POST)
            if nrform.is_valid():
                remedy = nrform.save(commit=False)
                remedy.errorModel = em
                remedy.author = request.user
                remedy.save()
                return HttpResponseRedirect(reverse('ct:remediation',
                                                    args=(remedy.id,)))
    set_crispy_action(request.path, nrform) # set actionTarget directly
    return render(request, 'ct/errormodel.html',
                  dict(em=em, actionTarget=request.path, emform=emform,
                       atime=display_datetime(em.atime), nrform=nrform,
                       relatedErrors=relatedErrors,
                       emPercent=emPercent, N=n))

@login_required
def remediation(request, rem_id):
    remedy = get_object_or_404(Remediation, pk=rem_id)
    if remedy.author != request.user:
        return HttpResponse("Only the author can edit this",
                            status_code=403)
    titleform = RemediationForm(instance=remedy)
    searchForm, sourceDB, lessonSet, wset = _search_lessons(request)
    if request.method == 'POST':
        if 'advice' in request.POST:
            titleform = RemediationForm(request.POST, instance=remedy)
            if titleform.is_valid():
                titleform.save()
        else:
            _post_lesson(request, remedy)
    set_crispy_action(request.path, titleform) # set actionTarget directly
    return render(request, 'ct/remediation.html',
                  dict(remedy=remedy, sourceDB=sourceDB,
                       lessonSet=lessonSet, actionTarget=request.path,
                       searchForm=searchForm, wset=wset,
                       titleform=titleform,
                       atime=display_datetime(remedy.atime)))

def _post_lesson(request, remedy):
    'form interface for adding and removing lessons'
    if 'sourceID' in request.POST:
        lesson = Lesson.get_from_sourceDB(request.POST.get('sourceID'),
                    request.user, request.POST.get('sourceDB'))
        remedy.lessons.add(lesson)
    elif request.POST.get('task') == 'rmLesson':
        lesson = Lesson.objects.get(pk=int(request.POST.get('lessonID')))
        remedy.lessons.remove(lesson)
    elif 'lessonID' in request.POST:
        lesson = Lesson.objects.get(pk=int(request.POST.get('lessonID')))
        remedy.lessons.add(lesson)

def _search_lessons(request):
    'form interface for search Lessons and external sourceDB'
    searchForm = LessonSearchForm()
    lessonSet = wset = ()
    sourceDB = ''
    if 'search' in request.GET:
        searchForm = LessonSearchForm(request.GET)
        if searchForm.is_valid():
            s = searchForm.cleaned_data['search']
            sourceDB = searchForm.cleaned_data['sourceDB']
            lessonSet = Lesson.objects.filter(Q(title__icontains=s) |
                                              Q(text__icontains=s))
            wset = Lesson.search_sourceDB(s, sourceDB)
    ## searchForm.helper.form_action = request.path # set actionTarget directly
    return searchForm, sourceDB, lessonSet, wset

#################################################
# instructor course UI

@login_required
def teach(request):
    'top-level instructor UI'
    courseform = NewCourseTitleForm()
    set_crispy_action(reverse('ct:courses'), courseform)
    courses = Course.objects.filter(role__role=Role.INSTRUCTOR,
                                    role__user=request.user)
    return render(request, 'ct/teach.html',
                  dict(user=request.user, actionTarget=request.path,
                       courses=courses, courseform=courseform))

@login_required
def courses(request):
    'list courses or create new course'
    if request.method == 'POST':
        form = CourseTitleForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.addedBy = request.user
            course.save()
            role = Role(course=course, user=request.user,
                        role=Role.INSTRUCTOR)
            role.save()
            return HttpResponseRedirect(reverse('ct:course',
                                                args=(course.id,)))

    courseSet = Course.objects.filter(courselet__coursequestion__isnull=False)
    return render(request, 'ct/courses.html', dict(courses=courseSet))


@login_required
def course(request, course_id):
    'instructor UI for managing a course'
    course = get_object_or_404(Course, pk=course_id)
    notInstructor = check_instructor_auth(course, request)
    if notInstructor: # redirect students to live session or student page
        return redirect_live(request,
          HttpResponseRedirect(reverse('ct:course_study', args=(course.id,))))
    courseletform = NewCourseletTitleForm()
    titleform = CourseTitleForm(instance=course)
    fsmStack = FSMStack(request)
    if request.method == 'POST':
        if 'access' in request.POST: # update course attrs
            titleform = CourseTitleForm(request.POST, instance=course)
            if titleform.is_valid():
                titleform.save()
        elif 'title' in request.POST: # create new courselet
            courseletform = NewCourseletTitleForm(request.POST)
            if courseletform.is_valid():
                courselet = courseletform.save(commit=False)
                courselet.course = course
                courselet.addedBy = request.user
                courselet.save()
                return HttpResponseRedirect(reverse('ct:courselet',
                                                    args=(courselet.id,)))
        elif request.POST.get('task') == 'delete': # delete me
            course.delete()
            return HttpResponseRedirect(reverse('ct:teach'))
        elif request.POST.get('task') == 'livestart': # create live session
            liveSession = LiveSession(course=course, addedBy=request.user)
            liveSession.save()
            fsmStack.push(request, 'liveInstructor',
                          dict(liveSession=liveSession))
        elif request.POST.get('task') == 'liveend': # end live session
            liveSession = fsmStack.state.liveSession
            liveSession.liveQuestion = None
            liveSession.endTime = timezone.now() # mark as completed
            liveSession.save()
            fsmStack.pop(request)
    set_crispy_action(request.path, courseletform, titleform)
    return render(request, 'ct/course.html',
                  dict(course=course, actionTarget=request.path,
                       titleform=titleform, fsmStack=fsmStack,
                       courseletform=courseletform))

def get_slform(courselet, user):
    questions = Question.objects.filter(Q(studylist__user=user) |
                Q(concept__courselet=courselet)) \
                .exclude(coursequestion__courselet=courselet)
    if questions.count() > 0:
        return CourseQuestionForm(questions)

@login_required
def courselet(request, courselet_id):
    'instructor UI for managing a courselet'
    courselet = get_object_or_404(Courselet, pk=courselet_id)
    notInstructor = check_instructor_auth(courselet.course, request)
    if notInstructor: # must be instructor to use this interface
        return notInstructor
    fsmStack = FSMStack(request)
    qform = NewQuestionForm()
    lform = NewLessonForm()
    titleform = CourseletTitleForm(instance=courselet)
    slform = get_slform(courselet, request.user)
    if request.method == 'POST':
        if 'qtext' in request.POST: # create new exercise
            question, qform = new_question(request)
            if question:
                n = courselet.courselesson_set.count() + \
                  courselet.coursequestion_set.count()
                courseQuestion = CourseQuestion(courselet=courselet,
                                                question=question, order=n,
                                                addedBy=request.user)
                courseQuestion.save()
                qform = NewQuestionForm() # new blank form to display
        elif 'kind' in request.POST: # create new lesson
            lesson, lform = new_lesson(request)
            if lesson:
                n = courselet.courselesson_set.count() + \
                  courselet.coursequestion_set.count()
                courseLesson = CourseLesson(courselet=courselet,
                                            lesson=lesson,
                                            order=n, addedBy=request.user)
                courseLesson.save()
                lform = NewLessonForm() # new blank form to display
        elif 'question' in request.POST: # add new CourseQuestion
            slform = CourseQuestionForm(None, request.POST)
            if slform.is_valid():
                courseQuestion = slform.save(commit=False)
                courseQuestion.courselet = courselet
                courseQuestion.addedBy = request.user
                courseQuestion.save()
                if courseQuestion.question.concept is None: # need to choose concept
                    return HttpResponseRedirect(reverse('ct:cq_concept',
                                                args=(courseQuestion.id,)))
                slform = get_slform(courselet, request.user) # fresh form
        elif 'title' in request.POST: # update courselet attributes
            titleform = CourseletTitleForm(request.POST, instance=courselet)
            if titleform.is_valid():
                titleform.save()
        elif request.POST.get('task') == 'delete': # delete me
            course = courselet.course
            courselet.delete()
            return HttpResponseRedirect(reverse('ct:course',
                                                args=(course.id,)))
    set_crispy_action(request.path, qform, lform, titleform)    
    return render(request, 'ct/courselet.html',
                  dict(courselet=courselet, actionTarget=request.path,
                       slform=slform, titleform=titleform, qform=qform,
                       fsmStack=fsmStack,
                       exercises=courselet.get_exercises(), lform=lform))

@login_required
def course_question(request, cq_id):
    'instructor CourseQuestion report / management page'
    courseQuestion = get_object_or_404(CourseQuestion, pk=cq_id)
    notInstructor = check_instructor_auth(courseQuestion.courselet.course,
                                          request)
    if notInstructor:
        return notInstructor
    emform = ErrorModelForm()
    fsmStack = FSMStack(request)
    if request.method == 'POST':
        if 'description' in request.POST:
            emform = ErrorModelForm(request.POST)
            if emform.is_valid():
                e = emform.save(commit=False)
                e.author = request.user
                e.save()
                courseQuestion.courseerrormodel_set.create(errorModel=e,
                    course=courseQuestion.courselet.course,
                    addedBy=request.user)
                emform = ErrorModelForm() # new blank form
        elif request.POST.get('task') == 'livestart':
            liveSession = fsmStack.state.liveSession
            liveQuestion = LiveQuestion(liveSession=liveSession,
                                        courseQuestion=courseQuestion,
                                        addedBy=request.user)
            liveQuestion.start() # calls save()
            fsmStack.state.liveQuestion = liveQuestion
            return fsmStack.transition(request, 'livestart')
        elif request.POST.get('task') == 'delete':
            courselet = courseQuestion.courselet
            courseQuestion.delete()
            return HttpResponseRedirect(reverse('ct:courselet',
                                                args=(courselet.id,)))
    n = courseQuestion.response_set.count() # count all responses
    responses = courseQuestion.response_set.exclude(selfeval=None) # self-assessed
    statusCounts, evalCounts, ndata = status_confeval_tables(responses, n)
    errorCounts = courseQuestion.errormodel_table(ndata, includeAll=True)
    uncats = Response.objects.filter(courseQuestion=courseQuestion,
        studenterror__isnull=True).exclude(selfeval=Response.CORRECT)
    uncats.order_by('status')
    return render(request, 'ct/course_question.html',
                  dict(courseQuestion=courseQuestion,
                       qtext=md2html(courseQuestion.question.qtext),
                       answer=md2html(courseQuestion.question.answer),
                       statusCounts=statusCounts, uncategorized=uncats,
                       evalCounts=evalCounts, actionTarget=request.path,
                       errorCounts=errorCounts, emform=emform))

@login_required
def course_lesson(request, cl_id):
    'instructor CourseLesson report / management page'
    courseLesson = get_object_or_404(CourseLesson, pk=cl_id)
    notInstructor = check_instructor_auth(courseLesson.courselet.course,
                                          request)
    if notInstructor:
        return notInstructor
    if request.method == 'POST':
        if request.POST.get('task') == 'delete':
            courselet = courseLesson.courselet
            courseLesson.delete()
            return HttpResponseRedirect(reverse('ct:courselet',
                                                args=(courselet.id,)))


@login_required
def courselet_concept(request, courselet_id):
    courselet = get_object_or_404(Courselet, pk=courselet_id)
    notInstructor = check_instructor_auth(courselet.course, request)
    if notInstructor: # must be instructor to use this interface
        return notInstructor
    r = _concepts(request, '''Please choose a Concept that this courselet
    will teach, by entering a search term to
    find relevant concepts.''')
    if isinstance(r, Concept): # user chose a concept to link
        if r in tuple(courselet.concepts.all()):
            return _concepts(request, '''You have already added that concept
        to this courselet.''', ignorePOST=True)
        else:
            courselet.concepts.add(r) # link to this concept
            return HttpResponseRedirect(reverse('ct:courselet',
                                            args=(courselet.id,)))
    return r


@login_required
def cq_concept(request, cq_id):
    courseQuestion = get_object_or_404(CourseQuestion, pk=cq_id)
    notInstructor = check_instructor_auth(courseQuestion.courselet.course,
                                          request)
    if notInstructor: # must be instructor to use this interface
        return notInstructor
    r = _concepts(request, '''Please choose a Concept that best describes
    what this question aims to test, by entering a search term to
    find relevant concepts.''')
    if isinstance(r, Concept): # user chose a concept to link
        courseQuestion.question.concept = r # link question to this concept
        courseQuestion.question.save()
        return HttpResponseRedirect(reverse('ct:courselet',
                            args=(courseQuestion.courselet.id,)))
    return r


@login_required
def lesson_concept(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    if request.user != lesson.addedBy:
        return HttpResponse("Only the lesson author can access this",
                            status_code=403)
    r = _concepts(request, '''Please choose a Concept that this lesson
    will teach, by entering a search term to
    find relevant concepts.''')
    if isinstance(r, Concept): # user chose a concept to link
        if r in tuple(Concept.objects.filter(lessonlink__lesson=lesson).all()):
            return _concepts(request, '''You have already added that concept
        to this leson.''', ignorePOST=True)
        else:
            ll = LessonLink(lesson=lesson, concept=r, addedBy=request.user)
            ll.save()
            return HttpResponseRedirect(reverse('ct:lesson',
                                            args=(lesson.id,)))
    return r


@login_required
def concepts(request):
    r = _concepts(request)
    if isinstance(r, Concept):
        return _concepts(request, '''Successfully added concept.
            Thank you!''', ignorePOST=True)
    return r

###########################################################
# WelcomeMat refactored utilities

def make_tabs(path, current, tabs):
    outTabs = []
    for label in tabs:
        try:
            i = label.index(':')
        except ValueError:
            tail = label.lower() + '/' # default, just use label
        else: # use specified URL tail
            tail = label[i + 1:]
            label = label[:i]
        if label == current:
             if tail:
                path = path[:path.rindex(tail)]
             tail = '#%sTabDiv' % label
        outTabs.append((label, tail))
    for i,t in enumerate(outTabs):
        if not t[1].startswith('#'): # add URL prefix
            outTabs[i] = (t[0], path + t[1])
    return outTabs

def concept_tabs(path, current, unitLesson,
                 tabs=('Lessons', 'Concepts', 'Errors', 'Edit'), **kwargs):
    return make_tabs(path, current, tabs, **kwargs)

def error_tabs(path, current, unitLesson,
               tabs=('Tests', 'Examples', 'Resolutions', 'Edit'), **kwargs):
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
                 tabs=('Home:', 'Concepts', 'Errors', 'Edit'),
                 answerTabs=('Home', 'Edit'), **kwargs):
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
    if is_teacher_url(path):
        tabFunc = {IS_ERROR:error_tabs,
                   IS_CONCEPT:concept_tabs,
                   IS_LESSON:lesson_tabs}
    else:
        tabFunc = {IS_ERROR:error_tabs,
                   IS_CONCEPT:concept_tabs,
                   IS_LESSON:lesson_tabs}
    return tabFunc[unitLesson.get_type()](path, current, unitLesson, **kwargs)
    

    
def unit_tabs(path, current,
              tabs=('Concepts', 'Lessons', 'Resources', 'Edit'), **kwargs):
    return make_tabs(path, current, tabs, **kwargs)
    
def unit_tabs_student(path, current,
              tabs=('Study:', 'Lessons', 'Concepts'), **kwargs):
    return make_tabs(path, current, tabs, **kwargs)
    

class PageData(object):
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

def ul_page_data(request, unit_id, ul_id, currentTab, includeText=True,
                 tabFunc=None):
    unit = get_object_or_404(Unit, pk=unit_id)
    ul = get_object_or_404(UnitLesson, pk=ul_id)
    if not tabFunc:
        tabFunc = auto_tabs
    pageData = PageData(title=ul.lesson.title,
                        navTabs=tabFunc(request.path, currentTab, ul))
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
# WelcomeMat refactored views

def update_concept_link(request, conceptLinks):
    cl = get_object_or_404(ConceptLink, pk=int(request.POST.get('clID')))
    clform = ConceptLinkForm(request.POST, instance=cl)
    if clform.is_valid():
        clform.save()
        conceptLinks.replace(cl, clform)

def create_concept(concept, lesson, unit):
    'save concept with newly created UnitLesson representing it'
    concept.save()
    lesson.concept = concept
    lesson.save_root()
    UnitLesson.create_from_lesson(lesson, unit)
    return concept

    
def _concepts(request, msg='', ignorePOST=False, conceptLinks=None,
              toTable=None, fromTable=None, unit=None,
              actionLabel='Link to this Concept',
              errorModels=None, createConceptFunc=create_concept, **kwargs):
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
                lesson = Lesson(title=conceptForm.cleaned_data['title'],
                    text=conceptForm.cleaned_data['description'],
                    addedBy=request.user)
                concept = Concept(title=conceptForm.cleaned_data['title'],
                                  addedBy=request.user)
                return createConceptFunc(concept, lesson, unit)
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
    cLinks = ConceptLink.objects.filter(lesson__unitlesson__unit=unit,
        lesson__unitlesson__kind=UnitLesson.COMPONENT,
        lesson__unitlesson__order__isnull=False)
    cLinks = distinct_subset(cLinks, lambda cl:cl.concept)
    clTable = ConceptLinkTable(cLinks, noEdit=True,
                        headers=('This courselet...', 'Concept'),
                        title='Concepts Linked to this Courselet')
    r = _concepts(request, '''To add a concept to this courselet, start by
    typing a search for relevant concepts. ''', conceptLinks=clTable,
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
                  fromTable=fromTable, unit=unit, pageData=pageData)
    if isinstance(r, Concept):
        cg = concept.relatedTo.create(toConcept=r, addedBy=request.user)
        toTable.append(cg)
        return _concepts(request, '''Successfully added concept.
            Thank you!''', ignorePOST=True, toTable=toTable,
            fromTable=fromTable, unit=unit, pageData=pageData)
    return r

def create_em_concept(concept, lesson, unit):
    concept.isError = True
    lesson.kind = lesson.ERROR_MODEL
    concept.save()
    lesson.concept = concept
    lesson.save_root()
    UnitLesson.create_from_lesson(lesson, unit)
    return concept

@login_required
def concept_errors(request, course_id, unit_id, ul_id):
    unit, ul, concept, pageData = ul_page_data(request, unit_id, ul_id,
                                               'Errors')
    errorModels = list(concept.relatedFrom
      .filter(relationship=ConceptGraph.MISUNDERSTANDS))
    r = _concepts(request, '''To add a concept link, start by
    typing a search for relevant concepts. ''', errorModels=errorModels,
                  pageData=pageData, unit=unit,
                  createConceptFunc=create_em_concept)
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
    return UnitLesson.create_from_lesson(lesson, unit, order='APPEND')

def _lessons(request, concept=None, msg='',
             ignorePOST=False, conceptLinks=None,
             unit=None, actionLabel='Add to This Unit',
             allowSearch=True, creationInstructions=None,
             templateFile='ct/lessons.html',
             createULFunc=create_unit_lesson, selectULFunc=None,
             newLessonFormClass=NewLessonForm,
             searchArgs={}, parentUL=None, **kwargs):
    'search or create a Lesson'
    if creationInstructions:
        lessonForm = newLessonFormClass()
    else:
        lessonForm = None
    if allowSearch:
        searchForm = LessonSearchForm()
    else:
        searchForm = None
    lessonSet = ()
    if request.method == 'POST' and not ignorePOST:
        if 'clID' in request.POST:
            update_concept_link(request, conceptLinks)
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
        searchForm = LessonSearchForm(request.GET)
        if searchForm.is_valid():
            s = searchForm.cleaned_data['search']
            lessonSet = UnitLesson.search_text(s, **searchArgs)
    if lessonForm:
        set_crispy_action(request.path, lessonForm)
    kwargs.update(dict(lessonSet=lessonSet, actionTarget=request.path,
                       searchForm=searchForm, msg=msg,
                       lessonForm=lessonForm, conceptLinks=conceptLinks,
                       actionLabel=actionLabel, user=request.user,
                       creationInstructions=creationInstructions))
    return render(request, templateFile, kwargs)

def make_cl_table(concept, unit):
    cLinks = UnitLesson.get_conceptlinks(concept, unit)
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
            if r.get_answers().count() == 0: # add empty answer to edit
                answer = Lesson(title='Answer', text='write an answer',
                                addedBy=r.addedBy, kind=Lesson.ANSWER)
                answer.save_root()
                ul = UnitLesson.create_from_lesson(answer, unit,
                            kind=UnitLesson.ANSWERS, parent=r)
                return HttpResponseRedirect(reverse('ct:edit_lesson',
                                args=(course_id, unit_id, ul.id,)))
        clTable = make_cl_table(concept, unit) # refresh table
        return _lessons(request, concept, '''Successfully added lesson.
            Thank you!''', ignorePOST=True, conceptLinks=clTable,
            pageData=pageData, unit=unit, allowSearch=False,
            creationInstructions=creationInstructions)
    return r

def copy_unit_lesson(ul, concept, unit, addedBy, parentUL):
    'copy lesson and append to this unit'
    if ul.unit == unit:
        return 'Lesson already in this unit, so no change made.'
    return ul.copy(unit, addedBy, order='APPEND')

@login_required
def unit_lessons(request, course_id, unit_id, lessonTable=None,
                 currentTab='Lessons'):
    unit = get_object_or_404(Unit, pk=unit_id)
    pageData = PageData(title=unit.title,
                        navTabs=unit_tabs(request.path, currentTab))
    if lessonTable is None:
        lessonTable = list(unit.unitlesson_set
            .filter(kind=UnitLesson.COMPONENT, order__isnull=False)
            .order_by('order'))
    r = _lessons(request, msg='''You can search for a lesson to add
          to this courselet, or write a new lesson for a concept by
          clicking on the Concepts tab.''', 
                  pageData=pageData, unit=unit,
                  lessonTable=lessonTable, selectULFunc=copy_unit_lesson)
    if isinstance(r, UnitLesson):
        lessonTable.append(r)
        return _lessons(request, msg='''Successfully added lesson.
            Thank you!''', ignorePOST=True, 
            pageData=pageData, unit=unit, lessonTable=lessonTable)
    return r

def unit_resources(request, course_id, unit_id):
    unit = get_object_or_404(Unit, pk=unit_id)
    lessonTable = list(unit.unitlesson_set \
            .filter(kind=UnitLesson.COMPONENT, order__isnull=True))
    return unit_lessons(request, course_id, unit_id, lessonTable, 'Resources')


def ul_teach(request, course_id, unit_id, ul_id):
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id, 'Home',
                                         False)
    query = Q(unitLesson=ul, selfeval__isnull=False)
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
    
def edit_lesson(request, course_id, unit_id, ul_id):
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id, 'Edit',
                                         False)
    if ul.get_type() == IS_LESSON:
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
            seTable.append((em, fmt_count(0, n)))
    r = _lessons(request, concept, msg, pageData=pageData, unit=unit, 
                  seTable=seTable, templateFile='ct/errors.html',
                  showNovelErrors=showNovelErrors,
                  novelErrors=novelErrors, responseFilterForm=neForm,
                  creationInstructions=creationInstructions,
                  newLessonFormClass=NewErrorForm, parentUL=ul,
                  createULFunc=create_error_ul, selectULFunc=copy_error_ul,
                  searchArgs=dict(searchType=IS_ERROR),
                  actionLabel='Add error model')
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
    return UnitLesson.create_from_lesson(lesson, unit,
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
                                         'Resolutions')
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

###########################################################
# welcome mat refactored student UI for courses

@login_required
def study_unit(request, course_id, unit_id):
    unit = get_object_or_404(Unit, pk=unit_id)
    unitStatus = UnitStatus.get_or_none(unit, request.user)
    if request.method == 'POST'  and request.POST.get('task') == 'next':
        if not unitStatus:
            unitStatus = UnitStatus(unit=unit, user=request.user)
            unitStatus.save()
        nextUL = unitStatus.get_lesson()
        return HttpResponseRedirect(get_study_url(request.path, nextUL))
    if unitStatus:
        nextUL = unitStatus.get_lesson()
    else:
        nextUL = None
    return render(request, 'ct/study_unit.html',
                  dict(user=request.user, actionTarget=request.path,
                       unitLesson=nextUL, unit=unit))

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

def get_study_url(path, nextUL):
    if nextUL.lesson.kind == Lesson.ORCT_QUESTION:
        return get_base_url(path, ['lessons', str(nextUL.pk), 'ask'])
    else:
        return get_base_url(path, ['lessons', str(nextUL.pk)])

def next_lesson_url(path, unitLesson, unitStatus=None):
    'get URL for unit lesson following this one, and record on unitStatus'
    try:
        nextUL = unitLesson.get_next_lesson()
    except UnitLesson.DoesNotExist:
        if unitStatus: # record completion of lesson sequence
            unitStatus.done()
        return get_base_url(path)
    if unitStatus: # record move to next lesson; prevent skipping
        nextUL = unitStatus.set_lesson(nextUL)
    return get_study_url(path, nextUL)

def redirect_next_lesson(request, ul):
    'get redirect to the next lesson, and record on UnitStatus if any'
    unitStatus = UnitStatus.get_or_none(ul.unit, request.user)
    url = next_lesson_url(request.path, ul, unitStatus)
    return HttpResponseRedirect(url)
    
        
def redirect_if_next(request, ul):
    'if POST:task=next, redirect to the next UnitLesson in this sequence'
    if request.method == 'POST'  and request.POST.get('task') == 'next':
        return redirect_next_lesson(request, ul)

    
def lesson(request, course_id, unit_id, ul_id):
    unit = get_object_or_404(Unit, pk=unit_id)
    ul = get_object_or_404(UnitLesson, pk=ul_id)
    r = redirect_if_next(request, ul)
    if r:
        return r
    elif ul.lesson.kind == Lesson.ORCT_QUESTION:
        return HttpResponseRedirect(request.path + 'ask/')
    pageData = PageData(title=ul.lesson.title,
                        navTabs=lesson_tabs(request.path, 'Study', ul))
    return render(request, 'ct/lesson_student.html',
                  dict(user=request.user, actionTarget=request.path,
                       unitLesson=ul, unit=unit, pageData=pageData))

def ul_concepts_student(request, course_id, unit_id, ul_id):
    'use lesson tabs even if UL is a concept'
    return ul_concepts(request, course_id, unit_id, ul_id, lesson_tabs)

def ul_tasks_student(request, course_id, unit_id, ul_id):
    'suggest next steps on this question'
    unit, ul, _, pageData = ul_page_data(request, unit_id, ul_id,'Tasks',
                                         tabFunc=lesson_tabs)
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
    return render(request, 'ct/resolutions_student.html',
                  dict(user=request.user, actionTarget=request.path,
                       unitLesson=ul, unit=unit, pageData=pageData,
                       lessonTable=lessonTable))

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
    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = save_response(form, ul, request.user, course_id,
                              kind=Response.COMMENT, needsEval=True,
                              parent=inquiry)
    else:
        form = ReplyForm()
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
    unit = get_object_or_404(Unit, pk=unit_id)
    ul = get_object_or_404(UnitLesson, pk=ul_id)
    if request.method == 'POST':
        form = ResponseForm(request.POST)
        if form.is_valid():
            r = save_response(form, ul, request.user, course_id)
            return HttpResponseRedirect(reverse('ct:assess',
                    args=(course_id, unit_id, ul_id, r.id,)))
    else:
        form = ResponseForm()
    set_crispy_action(request.path, form)
    return render(request, 'ct/ask.html',
                  dict(unitLesson=ul, qtext=md2html(ul.lesson.text),
                       form=form, actionTarget=request.path,
                       user=request.user))

@login_required
def assess(request, course_id, unit_id, ul_id, resp_id, doSelfEval=True,
           redirectURL=None):
    'student self-assessment'
    r = get_object_or_404(Response, pk=resp_id)
    choices = [(e.id, e.lesson.title) for e in r.unitLesson.get_errors()]
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
            for emID in form.cleaned_data['emlist']:
                em = get_object_or_404(UnitLesson, pk=emID)
                se = r.studenterror_set.create(errorModel=em,
                    author=request.user, status=form.cleaned_data['status'])
            if redirectURL:
                return HttpResponseRedirect(redirectURL)
            else:
                return redirect_next_lesson(request, r.unitLesson)
    else:
        form = formClass()
        form.fields['emlist'].choices = choices
    try:
        answer = r.unitLesson.get_answers()[0]
    except IndexError:
        answer = '(author has not provided an answer)'
    else:
        answer = md2html(answer.lesson.text)
    return render(request, 'ct/assess.html',
                  dict(response=r, qtext=md2html(r.lesson.text),
                       answer=answer, form=form, actionTarget=request.path,
                       user=request.user, doSelfEval=doSelfEval))

def assess_errors(request, course_id, unit_id, ul_id, resp_id):
    ul = get_object_or_404(UnitLesson, pk=ul_id)
    redirectURL = get_object_url(request.path, ul, subpath='tasks')
    return assess(request, course_id, unit_id, ul_id, resp_id, False,
           redirectURL)

###########################################################
# student UI for courses

def get_live_sessions(request):
    return () # !! implement live session finding here!!
    ## return LiveSession.objects.filter(course__role__user=request.user,
    ##                                   endTime__isnull=True)
#                                      course__role__role=Role.ENROLLED)

@login_required
def main_page(request):
    'generic home page'
    fsmStack = FSMStack(request)
    if request.method == 'POST':
        if 'liveID' in request.POST:
            liveID = int(request.POST['liveID'])
            liveSession = LiveSession.objects.get(pk=liveID) # make sure it exists
            return fsmStack.push(request, 'liveStudent',
                  dict(liveSession=liveSession,
                       liveQuestion=liveSession.liveQuestion))
        elif request.POST.get('task') == 'liveend': # end live session
            rm_live_user(request, fsmStack.state.liveSession)
            return fsmStack.pop(request)
    return render(request, 'ct/index.html',
                  dict(liveSessions=get_live_sessions(request),
                       actionTarget=request.path, fsmStack=fsmStack,
                       user=request.user))

def course_study(request, course_id):
    'generic page for student course view'
    course = get_object_or_404(Course, pk=course_id)
    target = redirect_live(request)
    if target:
        return target
    return render(request, 'ct/course_study.html',
                  dict(course=course, actionTarget=request.path))

def redirect_live(request, default=None):
    'redirect student to live exercise if ongoing'
    response, liveSession = live_response(request)
    if not liveSession:
        return default
    elif isinstance(response, HttpResponseRedirect):
        return response
    else:
        return HttpResponseRedirect(reverse('ct:home'))
        
            


###############################################################
# utility functions

def set_crispy_action(actionTarget, *forms):
    'set the form.helper.form_action for one or more forms'
    for form in forms:
        form.helper.form_action = actionTarget
    
    
############################################################
# NOT USED... JUST EXPERIMENTAL

@login_required
def remedy_page(request, em_id):
    em = get_object_or_404(ErrorModel, pk=em_id)
    return render_remedy_form(request, em)

def render_remedy_form(request, em, **context):
    context.update(dict(errorModel=em, qtext=md2html(em.question.qtext),
                        answer=md2html(em.question.answer)))
    return render(request, 'ct/remedy.html', context)

@login_required
def submit_remedy(request, em_id):
    em = get_object_or_404(ErrorModel, pk=em_id)
    try:
        remediation = request.POST['remediation'].strip()
        counterExample = request.POST['counterExample'].strip()
        if not remediation or not counterExample:
            raise KeyError
    except KeyError:
        return render_remedy_form(request, em, 
                   remediation=request.POST.get('remediation', ''),
                   counterExample=request.POST.get('counterExample', ''),
                   error_message='You must give both a remediation and a counter-example.')
    em.remediation_set.create(atime=timezone.now(), remediation=remediation,
                              counterExample=counterExample, 
                              author=request.user)
    return HttpResponseRedirect('/ct')

@login_required
def glossary_page(request, glossary_id):
    g = get_object_or_404(Glossary, pk=glossary_id)
    return render_glossary_form(request, g)

def render_glossary_form(request, g, **context):
    uniqueTerms = set()
    mine = []
    for v in g.vocabulary_set.all():  # condense to unique terms
        uniqueTerms.add(v.term)
        if v.author.id == request.user.id:
            mine.append(v)
    existingTerms = list(uniqueTerms)
    existingTerms.sort()
    existingTerms = ', '.join(existingTerms)
    mine.sort(lambda a,b:cmp(a.term,b.term))
    context.update(dict(glossary=g, existingTerms=existingTerms,
                        vocabulary=mine))
    return render(request, 'ct/write_glossary.html', context)

@login_required
def submit_term(request, glossary_id):
    g = get_object_or_404(Glossary, pk=glossary_id)
    try:
        term = request.POST['term'].strip()
        definition = request.POST['definition'].strip()
        if not term or not definition:
            raise KeyError
    except KeyError:
        return render_glossary_form(request, g, 
                   term=request.POST.get('term', ''),
                   definition=request.POST.get('definition', ''),
                   error_message='You must give both a term and a definition.')
    g.vocabulary_set.create(atime=timezone.now(), term=term,
                            definition=definition, author=request.user)
    return HttpResponseRedirect(reverse('ct:write_glossary', args=(g.id,)))
