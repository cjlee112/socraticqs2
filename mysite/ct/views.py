from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from ct.models import *

@login_required
def main_page(request):
    return render(request, 'ct/index.html')

@login_required
def question_page(request, ct_id):
    q = get_object_or_404(Question, pk=ct_id)
    return render_ask_form(request, q)

def render_ask_form(request, q, **context):
    context.update(dict(question=q, conf_choices=Response.CONF_CHOICES,
                        qtext=mark_safe(q.qtext)))
    return render(request, 'ct/ask.html', context)

@login_required
def submit_answer(request, ct_id):
    q = get_object_or_404(Question, pk=ct_id)
    try:
        answer = request.POST['atext'].strip()
        if not answer:
            raise KeyError
    except KeyError:
        return render_ask_form(request, q, 
                               error_message='You must give an answer.')
    try:
        confidence = request.POST['confidence']
    except KeyError:
        return render_ask_form(request, q, answer=answer,
                         error_message='You must choose a confidence level.')
    r = q.response_set.create(atext=answer, atime=timezone.now(),
                              confidence=confidence, author=request.user)
    return HttpResponseRedirect(reverse('ct:assess', args=(r.id,)))


@login_required
def assess_page(request, resp_id):
    r = get_object_or_404(Response, pk=resp_id)
    return render_assess_form(request, r)

def render_assess_form(request, r, **context):
    context.update(dict(response=r, qtext=mark_safe(r.question.qtext),
                        answer=mark_safe(r.question.answer)))
    return render(request, 'ct/assess.html', context)


@login_required
def submit_eval(request, resp_id):
    r = get_object_or_404(Response, pk=resp_id)
    try:
        score = request.POST['score']
    except KeyError:
        return render_assess_form(request, r,
                         error_message='You must choose an assessment.')
    if score == r.CORRECT:
        return HttpResponseRedirect('/ct')
    
    try:
        em_id = int(request.POST['knownError'])
        em = get_object_or_404(ErrorModel, pk=em_id)
    except (KeyError,ValueError):
        try:
            novelError = request.POST['novelError'].strip()
            if not novelError:
                raise KeyError
        except KeyError:
            return render_assess_form(request, r,
               error_message='You must choose an existing error or write a new error description.')
        else:
            em = r.question.errormodel_set.create(description=novelError, 
                                                  isAbort=False)
    r.studenterror_set.create(atime=timezone.now(), errorModel=em, 
                              author=request.user)
    return HttpResponseRedirect(reverse('ct:remedy', args=(em.id,)))
            
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
