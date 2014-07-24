from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from ct.models import *
from ct.forms import *

@login_required
def main_page(request):
    return render(request, 'ct/index.html')

@login_required
def respond_unitq(request, unitq_id):
    unitq = get_object_or_404(UnitQ, pk=unitq_id)
    return _respond(request, unitq.question, unitq)


@login_required
def respond(request, ct_id):
    return _respond(request, get_object_or_404(Question, pk=ct_id))


def _respond(request, q, unitq=None):
    if request.method == 'POST':
        form = ResponseForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.question = q
            r.unitq = unitq
            r.atime = timezone.now()
            r.author = request.user
            r.save()
            if unitq: # let LIVE mode override default next step
                target = unitq.get_next_target(UnitQ.RESPONSE_STAGE)
                if target:
                    return render(request, target, dict(unitq=unitq))
            return HttpResponseRedirect(reverse('ct:assess', args=(r.id,)))
    else:
        form = ResponseForm()

    return render(request, 'ct/ask.html',
                  dict(question=q, qtext=mark_safe(q.qtext), form=form,
                       actionTarget=request.path))

@login_required
def wait(request, unitq_id):
    unitq = get_object_or_404(UnitQ, pk=unitq_id)
    stage, r = unitq.get_user_stage(request.user)
    if not unitq.liveStage or stage < unitq.liveStage: # redirect to next
        target = unitq_next_url(unitq, stage, r)
        return HttpResponseRedirect(target)
    return render(request, 'ct/wait.html', dict(unitq=unitq)) # keep waiting

def unitq_next_url(unitq, stage, response=None):
    'get URL for next stage'
    if stage == unitq.START_STAGE:
        return reverse('ct:respond_unitq', args=(unitq.id,))
    elif stage == unitq.RESPONSE_STAGE:
        return reverse('ct:assess', args=(response.id,))
    elif stage == unitq.ASSESSMENT_STAGE:
        return reverse('ct:unit', args=(unitq.unit.id,))

@login_required
def unitq_control(request, unitq_id):
    unitq = get_object_or_404(UnitQ, pk=unitq_id)
    role = unitq.unit.course.get_user_role(request.user)
    if role != Role.INSTRUCTOR:
        return HttpResponse("Only the instructor can access this",
                            status_code=403)
    if not unitq.liveStage: # activate live session
        unitq.liveStage = unitq.RESPONSE_STAGE
    if request.method == 'POST':
        pass
    return render(request, 'ct/control.html', dict(unitq=unitq))


@login_required
def assess(request, resp_id):
    r = get_object_or_404(Response, pk=resp_id)
    errors = list(r.question.errormodel_set.all()) \
           + list(ErrorModel.get_generic())
    choices = [(e.id, e.description) for e in errors]
    if request.method == 'POST':
        form = SelfAssessForm(request.POST)
        form.fields['emlist'].choices = choices
        if form.is_valid():
            r.selfeval = form.cleaned_data['selfeval']
            r.save()
            print form.cleaned_data['emlist']
            for emID in form.cleaned_data['emlist']:
                em = get_object_or_404(ErrorModel, pk=emID)
                se = r.studenterror_set.create(atime=timezone.now(),
                                               errorModel=em,
                                               author=r.author)
            return HttpResponseRedirect('/ct')
    else:
        form = SelfAssessForm()
        form.fields['emlist'].choices = choices 

    return render(request, 'ct/assess.html',
                  dict(response=r, qtext=mark_safe(r.question.qtext),
                       answer=mark_safe(r.question.answer), form=form,
                       actionTarget=request.path))

############################################################33
# NOT USED... JUST EXPERIMENTAL

@login_required
def remedy_page(request, em_id):
    em = get_object_or_404(ErrorModel, pk=em_id)
    return render_remedy_form(request, em)

def render_remedy_form(request, em, **context):
    context.update(dict(errorModel=em, qtext=mark_safe(em.question.qtext),
                        answer=mark_safe(em.question.answer)))
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
