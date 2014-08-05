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
from ct.templatetags.ct_extras import md2html

######################################################
# student live session UI

@login_required
def respond_unitq(request, unitq_id):
    unitq = get_object_or_404(UnitQ, pk=unitq_id)
    return _respond(request, unitq.question, unitq)


@login_required
def respond(request, ct_id):
    return _respond(request, get_object_or_404(Question, pk=ct_id))

def _respond(request, q, unitq=None):
    'ask student a question'
    if request.method == 'POST':
        form = ResponseForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.question = q
            r.unitq = unitq
            r.atime = timezone.now()
            r.author = request.user
            r.save()
            # let LIVE mode override default next step
            if unitq and unitq.iswait(UnitQ.RESPONSE_STAGE):
                return render(request, 'ct/wait.html',
                    dict(actionTarget=reverse('ct:wait', args=(unitq.id,))))
            return HttpResponseRedirect(reverse('ct:assess', args=(r.id,)))
    else:
        form = ResponseForm()

    return render(request, 'ct/ask.html',
                  dict(question=q, qtext=md2html(q.qtext), form=form,
                       actionTarget=request.path))

@login_required
def assess(request, resp_id):
    'student self-assessment'
    r = get_object_or_404(Response, pk=resp_id)
    errors = list(r.question.errormodel_set.all()) \
           + list(ErrorModel.get_generic())
    choices = [(e.id, md2html(e.description, stripP=True)) for e in errors]
    if request.method == 'POST':
        form = SelfAssessForm(request.POST)
        form.fields['emlist'].choices = choices
        if form.is_valid():
            r.selfeval = form.cleaned_data['selfeval']
            r.status = form.cleaned_data['status']
            r.save()
            for emID in form.cleaned_data['emlist']:
                em = get_object_or_404(ErrorModel, pk=emID)
                se = r.studenterror_set.create(atime=timezone.now(),
                                               errorModel=em,
                                               author=r.author)
            if r.unitq:
                return render(request, 'ct/wait.html',
                    dict(actionTarget=reverse('ct:wait', args=(r.unitq.id,))))
            return HttpResponseRedirect('/ct/')
    else:
        form = SelfAssessForm()
        form.fields['emlist'].choices = choices 

    return render(request, 'ct/assess.html',
                  dict(response=r, qtext=md2html(r.question.qtext),
                       answer=md2html(r.question.answer), form=form,
                       actionTarget=request.path))


@login_required
def unit_wait(request, unit_id):
    'keep student waiting until instructor starts live exercise'
    unit = get_object_or_404(Unit, pk=unit_id)
    if unit.liveUnitQ: 
        return HttpResponseRedirect(reverse('ct:wait',
                                            args=(unit.liveUnitQ.id,)))
    return render(request, 'ct/wait.html',
                  dict(actionTarget=request.path)) # keep waiting

@login_required
def wait(request, unitq_id):
    'keep student waiting until instructor advances live session stage'
    unitq = get_object_or_404(UnitQ, pk=unitq_id)
    unitq.start_user_session(request.user) # user in live session
    stage, r = unitq.get_user_stage(request.user)
    if not unitq.liveStage or stage < unitq.liveStage: # redirect to next
        target = unitq_next_url(unitq, stage, r)
        return HttpResponseRedirect(target)
    return render(request, 'ct/wait.html',
                  dict(actionTarget=request.path)) # keep waiting

def unitq_next_url(unitq, stage, response=None):
    'get URL for next stage'
    if stage == unitq.START_STAGE:
        return reverse('ct:respond_unitq', args=(unitq.id,))
    elif stage == unitq.RESPONSE_STAGE:
        return reverse('ct:assess', args=(response.id,))
    elif stage == unitq.ASSESSMENT_STAGE:
        return reverse('ct:unit_wait', args=(unitq.unit.id,))

    
#############################################################
# instructor UnitQ live session UI
    
def check_instructor_auth(course, request):
    role = course.get_user_role(request.user)
    if role != Role.INSTRUCTOR:
        return HttpResponse("Only the instructor can access this",
                            status_code=403)
    
@login_required
def unitq_live_start(request, unitq_id):
    'instructor live session START page'
    unitq = get_object_or_404(UnitQ, pk=unitq_id)
    notInstructor = check_instructor_auth(unitq.unit.course, request)
    if notInstructor:
        return notInstructor
    if request.method != 'GET':
        return HttpResponse("not allowed", status_code=405)
    return render(request, 'ct/livestart.html',
                  dict(unitq=unitq, qtext=md2html(unitq.question.qtext),
                       answer=md2html(unitq.question.answer)))

@login_required
def unitq_control(request, unitq_id):
    'instructor live session UI for monitoring student responses'
    unitq = get_object_or_404(UnitQ, pk=unitq_id)
    notInstructor = check_instructor_auth(unitq.unit.course, request)
    if notInstructor: # must be instructor to use this interface
        return notInstructor
    if unitq.startTime is None:
        unitq.startTime = timezone.now()
        unitq.save() # save time stamp
    responses = unitq.response_set.all() # get responses from live session
    sure = responses.filter(confidence=Response.SURE)
    unsure = responses.filter(confidence=Response.UNSURE)
    guess = responses.filter(confidence=Response.GUESS)
    nuser = unitq.liveuser_set.count() # count logged in users
    counts = [guess.count(), unsure.count(), sure.count(), 0]
    counts[-1] = nuser - sum(counts)
    sec = (timezone.now() - unitq.startTime).seconds
    elapsedTime = '%d:%02d' % (sec / 60, sec % 60)
    emlist = [e.description for e in unitq.question.errormodel_set.all()]
    ndisplay = 25 # set default values
    sortOrder = '-atime'
    rlform = ResponseListForm()
    if request.method == 'POST': # create a new ErrorModel
        emform = ErrorModelForm(request.POST)
        if emform.is_valid():
            e = emform.save(commit=False)
            e.question = unitq.question
            e.atime = timezone.now()
            e.author = request.user
            e.save()
    else:
        emform = ErrorModelForm()
        if request.GET: # new query parameters for displaying responses
            rlform = ResponseListForm(request.GET)
            if rlform.is_valid():
                ndisplay = int(rlform.cleaned_data['ndisplay'])
                sortOrder = rlform.cleaned_data['sortOrder']
    responses.order_by(sortOrder) # apply the desired sort order
    return render(request, 'ct/control.html',
                  dict(unitq=unitq, qtext=md2html(unitq.question.qtext),
                       answer=md2html(unitq.question.answer),
                       counts=counts, elapsedTime=elapsedTime, 
                       emlist=emlist, actionTarget=request.path,
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
def unitq_end(request, unitq_id):
    'instructor live session UI for monitoring student self-assessment'
    unitq = get_object_or_404(UnitQ, pk=unitq_id)
    notInstructor = check_instructor_auth(unitq.unit.course, request)
    if notInstructor: # must be instructor to use this interface
        return notInstructor
    if request.method == 'POST':
        if request.POST.get('task') == 'finish':
            unitq.livestart(end=True)
            return HttpResponseRedirect(reverse('ct:unit',
                                                args=(unitq.unit.id,)))
    unitq.liveStage = unitq.ASSESSMENT_STAGE
    unitq.save()
    n = unitq.response_set.count() # count all responses from live session
    responses = unitq.response_set.exclude(selfeval=None) # self-assessed
    statusCounts, evalCounts, ndata = status_confeval_tables(responses, n)
    errorCounts = errormodel_table(unitq, ndata)
    sec = (timezone.now() - unitq.startTime).seconds
    elapsedTime = '%d:%02d' % (sec / 60, sec % 60)
    return render(request, 'ct/end.html',
                  dict(unitq=unitq, qtext=md2html(unitq.question.qtext),
                       answer=md2html(unitq.question.answer),
                       statusCounts=statusCounts, elapsedTime=elapsedTime,
                       evalCounts=evalCounts, actionTarget=request.path,
                       refreshRate=15, errorCounts=errorCounts))


def status_confeval_tables(responses, n):
    data = [(r.confidence, r.selfeval, r.status) for r in responses]
    ndata = len(data)
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

def errormodel_table(unitq, n, question=None, fmt='%d (%.0f%%)',
                     includeAll=False):
    if question:
        studentErrors = StudentError.objects.filter(response__question=question)
    else:
        studentErrors = StudentError.objects.filter(response__unitq=unitq)
        question = unitq.question
    d = {}
    for se in studentErrors:
        try:
            d[se.errorModel].append(se)
        except KeyError:
            d[se.errorModel] = [se]
    l = d.items()
    if includeAll: # add all EM for this question
        extraEM = ErrorModel.objects.filter(question=question) \
          .exclude(studenterror__response__unitq=unitq)
        for em in extraEM:
            l.append((em, ()))
    l.sort(lambda x,y:cmp(len(x[1]), len(y[1])), reverse=True)
    fmt_count = lambda c: fmt % (c, c * 100. / n)
    return [(t[0],t[1],fmt_count(len(t[1]))) for t in l]


######################################################3
# UI for searching, creating Question entries

def new_question(request):
    'create new Question from POST form data'
    form = QuestionForm(request.POST)
    if form.is_valid():
        question = form.save(commit=False)
        question.author = request.user
        question.save()
        return question, form
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
    try:
        sl = StudyList.objects.get(question=q, user=request.user)
        inStudylist = 1
    except ObjectDoesNotExist:
        inStudylist = 0
    return render(request, 'ct/question.html',
                  dict(question=q, qtext=md2html(q.qtext),
                       answer=md2html(q.answer),
                       actionTarget=request.path,
                       inStudylist=inStudylist,
                       allowEdit=(q.author == request.user),
                       atime=display_datetime(q.atime)))


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
    if em.commonError:
        relatedErrors = em.commonError.errormodel_set.exclude(pk=em.pk)
    else:
        relatedErrors = ()
    if em.question:
        n = em.question.response_set.filter(selfeval__isnull=False).count()
    elif em.alwaysAsk:
        n = Response.objects.count()
    else:
        n = 0
    if n > 0:
        nerr = Response.objects.filter(studenterror__errorModel=em).count()
        emPercent = '%.0f' % (nerr * 100. / n)
    else:
        emPercent = None
    ceform = CommonErrorForm()
    ceform.fields['synopsis'].initial = em.description
    
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
        elif 'commonError' in request.POST:
            emceForm = ErrorModelCEForm(None, request.POST, instance=em)
            if emceForm.is_valid():
                emceForm.save()
        else:
            ceform = CommonErrorForm(request.POST)
            if ceform.is_valid():
                ce = ceform.save(commit=False)
                ce.concept = em.question.concept
                ce.author = request.user
                ce.save()
                em.commonError = ce
                em.save()
    if em.question and em.question.concept:
        commonErrors = em.question.concept.commonerror_set.all()
        emceForm = ErrorModelCEForm(commonErrors)
        if em.commonError:
            emceForm.fields['commonError'].initial = em.commonError.id
    else:
        emceForm = ''
    set_crispy_action(request.path, nrform) # set actionTarget directly
    return render(request, 'ct/errormodel.html',
                  dict(em=em, actionTarget=request.path, emform=emform,
                       atime=display_datetime(em.atime), nrform=nrform,
                       relatedErrors=relatedErrors, ceform=ceform,
                       emPercent=emPercent, N=n, emceForm=emceForm))

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
    courseform = CourseTitleForm()
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

    courseSet = Course.objects.filter(unit__unitq__isnull=False)
    return render(request, 'ct/courses.html', dict(courses=courseSet))


@login_required
def course(request, course_id):
    'instructor UI for managing a course'
    course = get_object_or_404(Course, pk=course_id)
    notInstructor = check_instructor_auth(course, request)
    if notInstructor: # redirect students to live session or student page
        return redirect_live(course.liveUnit,
          HttpResponseRedirect(reverse('ct:course_study', args=(course.id,))))
    unitform = UnitTitleForm()
    titleform = CourseTitleForm(instance=course)
    if request.method == 'POST':
        if 'access' in request.POST: # update course attrs
            titleform = CourseTitleForm(request.POST, instance=course)
            if titleform.is_valid():
                titleform.save()
        elif 'title' in request.POST: # create new unit
            unitform = UnitTitleForm(request.POST)
            if unitform.is_valid():
                unit = unitform.save(commit=False)
                unit.course = course
                unit.addedBy = request.user
                unit.save()
                return HttpResponseRedirect(reverse('ct:unit',
                                                    args=(unit.id,)))
        elif request.POST.get('task') == 'delete': # delete me
            course.delete()
            return HttpResponseRedirect(reverse('ct:teach'))
    return render(request, 'ct/course.html',
                  dict(course=course, actionTarget=request.path,
                       titleform=titleform, unitform=unitform))

@login_required
def unit(request, unit_id):
    'instructor UI for managing a course unit'
    unit = get_object_or_404(Unit, pk=unit_id)
    notInstructor = check_instructor_auth(unit.course, request)
    if notInstructor: # must be instructor to use this interface
        return notInstructor
    qform = QuestionForm()
    titleform = UnitTitleForm(instance=unit)
    if request.method == 'POST':
        if 'qtext' in request.POST: # create new exercise
            question, qform = new_question(request)
            if question:
                unitq = UnitQ(unit=unit, question=question)
                unitq.save()
                qform = QuestionForm() # new blank form to display
        elif 'question' in request.POST: # add new UnitQ
            unitqform = UnitQForm(None, request.POST)
            if unitqform.is_valid():
                unitq = unitqform.save(commit=False)
                unitq.unit = unit
                unitq.addedBy = request.user
                unitq.save()
                if unitq.question.concept is None: # need to choose concept
                    return HttpResponseRedirect(reverse('ct:unitq_concept',
                                                args=(unitq.id,)))
        elif 'title' in request.POST: # update unit attributes
            titleform = UnitTitleForm(request.POST, instance=unit)
            if titleform.is_valid():
                titleform.save()
        elif request.POST.get('task') == 'liveend': # end live session
            unit.liveUnitQ = None
            unit.save()
            unit.course.liveUnit = None
            unit.course.save()
        elif request.POST.get('task') == 'delete': # delete me
            course = unit.course
            unit.delete()
            return HttpResponseRedirect(reverse('ct:course',
                                                args=(course.id,)))
    questions = Question.objects.filter(studylist__user=request.user)
    slform = UnitQForm(questions)
    return render(request, 'ct/unit.html',
                  dict(unit=unit, actionTarget=request.path, slform=slform,
                       titleform=titleform, qform=qform))

@login_required
def unitq(request, unitq_id):
    'instructor UnitQ report / management page'
    unitq = get_object_or_404(UnitQ, pk=unitq_id)
    notInstructor = check_instructor_auth(unitq.unit.course, request)
    if notInstructor:
        return notInstructor
    emform = ErrorModelForm()
    if request.method == 'POST':
        if 'description' in request.POST:
            emform = ErrorModelForm(request.POST)
            if emform.is_valid():
                e = emform.save(commit=False)
                e.question = unitq.question
                e.atime = timezone.now()
                e.author = request.user
                e.save()
                emform = ErrorModelForm() # new blank form
        elif request.POST.get('task') == 'livestart':
            unitq.livestart()
            return HttpResponseRedirect(reverse('ct:livestart',
                                                args=(unitq.id,)))
        elif request.POST.get('task') == 'delete':
            unit = unitq.unit
            unitq.delete()
            return HttpResponseRedirect(reverse('ct:unit', args=(unit.id,)))
    n = unitq.response_set.count() # count all responses from live session
    responses = unitq.response_set.exclude(selfeval=None) # self-assessed
    statusCounts, evalCounts, ndata = status_confeval_tables(responses, n)
    errorCounts = errormodel_table(unitq, ndata, includeAll=True)
    uncats = Response.objects.filter(unitq=unitq, studenterror__isnull=True) \
      .exclude(selfeval=Response.CORRECT)
    uncats.order_by('status')
    return render(request, 'ct/unitq.html',
                  dict(unitq=unitq, qtext=md2html(unitq.question.qtext),
                       answer=md2html(unitq.question.answer),
                       statusCounts=statusCounts, uncategorized=uncats,
                       evalCounts=evalCounts, actionTarget=request.path,
                       errorCounts=errorCounts, emform=emform))

@login_required
def unitq_concept(request, unitq_id):
    unitq = get_object_or_404(UnitQ, pk=unitq_id)
    notInstructor = check_instructor_auth(unitq.unit.course, request)
    if notInstructor: # must be instructor to use this interface
        return notInstructor
    r = _concepts(request, '''Please choose a Concept that best describes
    what this question aims to test, by entering a search term to
    find relevant concepts.''')
    if isinstance(r, Concept): # user chose a concept to link
        unitq.question.concept = r # link question to this concept
        unitq.question.save()
        return HttpResponseRedirect(reverse('ct:unit', args=(unitq.unit.id,)))
    return r


@login_required
def concepts(request):
    r = _concepts(request)
    if isinstance(r, Concept):
        return 'write a success message!'
    return r

def _concepts(request, msg=''):
    'search or create a Concept'
    cset = wset = ()
    if request.method == 'POST':
        if 'wikipediaID' in request.POST:
            t = Concept.get_from_sourceDB(request.POST.get('wikipediaID'),
                                          request.user)
            return t[0] # return concept object
        elif 'conceptID' in request.POST:
            return Concept.objects.get(pk=int(request.POST.get('conceptID')))
        return 'please write POST error message'
    elif 'search' in request.GET:
        searchForm = ConceptSearchForm(request.GET)
        if searchForm.is_valid():
            s = searchForm.cleaned_data['search']
            cset = Concept.objects.filter(Q(title__icontains=s) |
                                          Q(description__icontains=s))
            wset = Lesson.search_sourceDB(s)
    else:
        searchForm = ConceptSearchForm()
    return render(request, 'ct/concepts.html',
                  dict(cset=cset, actionTarget=request.path, msg=msg,
                       searchForm=searchForm, wset=wset))


def concept(request, concept_id):
    concept = get_object_or_404(Concept, pk=concept_id)
    return render(request, 'ct/concept.html',
                  dict(actionTarget=request.path, concept=concept,
                       atime=display_datetime(concept.atime)))
        

###########################################################
# student UI for courses

@login_required
def main_page(request):
    'generic home page'
    return render(request, 'ct/index.html')

def course_study(request, course_id):
    'generic page for student course view'
    course = get_object_or_404(Course, pk=course_id)
    target = redirect_live(course.liveUnit)
    if target:
        return target
    return render(request, 'ct/course_study.html',
                  dict(course=course, actionTarget=request.path))

def redirect_live(unit, default=None):
    'redirect student to live exercise if ongoing'
    if not unit:
        return default
    elif unit.liveUnitQ:
        return HttpResponseRedirect(unitq_next_url(unit.liveUnitQ,
                                                   UnitQ.START_STAGE))
    return HttpResponseRedirect(reverse('ct:unit_wait', args=(unit.id,)))
        
            


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
