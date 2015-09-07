from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from fsm.models import (
    FSMState,
    FSMBadUserError,
    FSMStackResumeError,
)
from ct.views import PageData
from ct.forms import (
    set_crispy_action,
    CancelForm,
    LogoutForm
)


@login_required
def fsm_node(request, node_id):
    """
    Display standard FSM node explanation & next steps page.
    """
    pageData = PageData(request)
    if not pageData.fsmStack.state or pageData.fsmStack.state.fsmNode.pk != int(node_id):
        return HttpResponseRedirect('/ct/')
    if request.method == 'POST' and 'fsmedge' in request.POST:
        return pageData.fsm_redirect(request, request.POST['fsmedge'])
    addNextButton = (pageData.fsmStack.state.fsmNode.outgoing.count() == 1)
    return pageData.render(
        request, 'fsm/fsm_node.html', addNextButton=addNextButton
    )


@login_required
def fsm_status(request):
    """
    Display Activity Center UI.
    """
    pageData = PageData(request)
    cancelForm = logoutForm = None
    nextSteps = ()
    if request.method == 'POST':
        task = request.POST.get('task', '')
        if 'fsmstate_id' in request.POST:
            try:
                url = pageData.fsmStack.resume(
                    request, request.POST['fsmstate_id']
                )
            except FSMBadUserError:
                pageData.errorMessage = 'Cannot access activity belonging to another user'
            except FSMStackResumeError:
                pageData.errorMessage = """This activity is waiting for a sub-activity to complete,
                                         and hence cannot be resumed (you should complete or cancel
                                         the sub-activity first)."""
            except FSMState.DoesNotExist:
                pageData.errorMessage = 'Activity not found!'
            else:  # redirect to this activity
                return HttpResponseRedirect(url)
        elif not pageData.fsmStack.state:
            pageData.errorMessage = 'No activity ongoing currently!'
        elif 'abort' == task:
            pageData.fsmStack.pop(request, eventName='exceptCancel')
            pageData.statusMessage = 'Activity canceled.'
        # follow this optional edge
        elif pageData.fsmStack.state.fsmNode.outgoing.filter(name=task).count() > 0:
            return pageData.fsm_redirect(request, task, vagueEvents=())
    if not pageData.fsmStack.state:  # search for unfinished activities
        unfinished = FSMState.objects.filter(user=request.user, children__isnull=True)
    else:  # provide options to cancel or quit this activity
        unfinished = None
        cancelForm = CancelForm()
        set_crispy_action(request.path, cancelForm)
        edges = pageData.fsmStack.state.fsmNode.outgoing
        nextSteps = edges.filter(showOption=True)
        logoutForm = LogoutForm()
        set_crispy_action(
            reverse('ct:person_profile', args=(request.user.id,)),
            logoutForm
        )
    return pageData.render(
        request,
        'fsm/fsm_status.html',
        dict(
            cancelForm=cancelForm,
            unfinished=unfinished,
            logoutForm=logoutForm,
            nextSteps=nextSteps
        )
    )
