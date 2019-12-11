from django.db.models import Q
from django.utils import timezone

from ct.models import UnitStatus, Response, InquiryCount
from core.common.mongo import c_faq_data, c_chat_context

from .chat import get_lesson_url


class START(object):
    """
    Initialize data for viewing a courselet, and go immediately
    to first lesson (not yet completed).
    """
    def start_event(self, node, fsmStack, request, **kwargs):
        """
        Event handler for START node.
        """
        unit = fsmStack.state.get_data_attr('unit')
        fsmStack.state.title = 'Study: %s' % unit.title

        try:  # use unitStatus if provided
            unitStatus = fsmStack.state.get_data_attr('unitStatus')
        except AttributeError:  # create new, empty unitStatus
            unitStatus = UnitStatus(unit=unit, user=request.user)
            unitStatus.save()
            fsmStack.state.set_data_attr('unitStatus', unitStatus)

        unit_lesson, chat = kwargs.get('unitlesson'), kwargs.get('chat')
        fsmStack.state.unitLesson = unit_lesson

        faqs_for_ul = unit_lesson.response_set.filter(
            ~Q(author=request.user),
            kind=Response.STUDENT_QUESTION,
            is_preview=False,
            is_test=False
        ).exclude(title__isnull=True).exclude(title__exact='').exists()
        if faqs_for_ul:
            c_faq_data().update_one(
                {
                    "chat_id": chat.id,
                    "ul_id": unit_lesson.id
                },
                {"$set": {"faqs": {}}},
                upsert=True
            )
        _next = 'show_faq' if faqs_for_ul else 'ask_new_faq'
        c_chat_context().update_one(
            {"chat_id": chat.id},
            {"$set": {
                f"activity.{unit_lesson.parent.id}": timezone.now()
            }},
            upsert=True
        )
        return fsmStack.state.transition(
            fsmStack, request, _next, useCurrent=True, **kwargs
        )

    # node specification data goes here
    title = 'Start This Courselet'
    edges = (
        dict(name='show_faq', toNode='INTRO_MSG', title='View Next Lesson'),
        dict(name='ask_new_faq', toNode='ASK_NEW_FAQ', title='View Next Lesson'),
    )


class INTRO_MSG(object):
    path = 'fsm:fsm_node'
    title = 'Would any of the following questions help you? Select the one(s) you with to view.'

    edges = (
        dict(name='next', toNode='SHOW_FAQS', title='Go to the end'),
    )


class SHOW_FAQS(object):
    get_path = get_lesson_url

    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        fsm = edge.fromNode.fsm

        return edge.toNode if request.data.get('selected') else fsm.get_node(name='ASK_NEW_FAQ')

    title = 'SHOW_FAQS'
    edges = (
        dict(name='next', toNode='SHOW_FAQ_BY_ONE', title='Go to the end'),
    )


class MSG_FOR_INQUIRY(object):
    path = 'fsm:fsm_node'
    title = 'MSG_FOR_INQUIRY'

    edges = (
        dict(name='next', toNode='SHOW_FAQ_BY_ONE', title='Go to the end'),
    )


class SHOW_FAQ_BY_ONE(object):
    path = 'fsm:fsm_node'
    title = 'SHOW_FAQ_BY_ONE'

    edges = (
        dict(name='next', toNode='ASK_FOR_FAQ_ANSWER', title='Go to the end'),
    )


class ASK_FOR_FAQ_ANSWER(object):
    path = 'fsm:fsm_node'
    title = 'Would the answer to this question help you?'

    edges = (
        dict(name='next', toNode='GET_FOR_FAQ_ANSWER', title='Go to the end'),
    )


class GET_FOR_FAQ_ANSWER(object):
    path = 'fsm:fsm_node'
    title = 'GET_FOR_FAQ_ANSWER'

    @staticmethod
    def get_pending_faqs(chat_id, ul_id):
        # TODO change to the Assignment expressions in Python3.8
        faq_data = c_faq_data().find_one({"chat_id": chat_id, "ul_id": ul_id})
        return faq_data.get('faqs', {}) if faq_data else {}

    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        fsm = edge.fromNode.fsm
        next_node = edge.toNode
        ul_id = c_chat_context().find_one({"chat_id": fsmStack.id}).get('actual_ul_id')
        if fsmStack.next_point.text.lower() == 'yes':
            actual_faq_id = c_chat_context().find_one(
                {"chat_id": fsmStack.id}).get('actual_faq_id', None)
            faq = Response.objects.filter(id=int(actual_faq_id)).first()
            try:
                ob, _ = InquiryCount.objects.get_or_create(response=faq, addedBy=request.user)
            except InquiryCount.MultipleObjectsReturned:
                ob = InquiryCount.objects.filter(
                    response=faq, addedBy=request.user
                ).order_by('-atime').first()
            faq.notify_instructors()
            c_chat_context().update_one(
                {"chat_id": fsmStack.id},
                {"$set": {"actual_inquiry_id": ob.id}},
            )

            faq_answers = faq.response_set.all()
            if faq_answers:
                next_node = fsm.get_node('SHOW_FAQ_ANSWERS')
                c_faq_data().update_one(
                    {
                        "chat_id": fsmStack.id,
                        "ul_id": ul_id
                    },
                    {"$set": {"faqs.{}.answers".format(actual_faq_id): [
                        {"done": False, "answer_id": answer.id} for answer in faq_answers
                    ]}}
                )
            else:
                next_node = fsm.get_node('WILL_TRY_MESSAGE_2')
        else:
            show_another_faq = False
            for key, value in list(self.get_pending_faqs(chat_id=fsmStack.id, ul_id=ul_id).items()):
                if not value.get('status').get('done', False):
                    show_another_faq = True
                    break
            if show_another_faq:
                next_node = fsm.get_node('SHOW_FAQ_BY_ONE')

        return next_node

    edges = (
        dict(name='next', toNode='ASK_NEW_FAQ', title='Go to the end'),
    )


class SHOW_FAQ_ANSWERS(object):
    path = 'fsm:fsm_node'
    title = 'SHOW_FAQ_ANSWERS'

    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        fsm = edge.fromNode.fsm

        ul_id = c_chat_context().find_one({"chat_id": fsmStack.id}).get('actual_ul_id')
        actual_faq_id = c_chat_context().find_one(
            {"chat_id": fsmStack.id}).get('actual_faq_id', None)
        if actual_faq_id:
            faq_answers = c_faq_data().find_one(
                {
                    "chat_id": fsmStack.id,
                    "ul_id": ul_id,
                    "faqs.{}.answers.done".format(actual_faq_id): False
                }
            )
            next_node = fsm.get_node('SHOW_FAQ_ANSWERS') if faq_answers else fsm.get_node('ASK_UNDERSTANDING')
            return next_node

        return edge.toNode

    edges = (
        dict(name='next', toNode='ASK_UNDERSTANDING', title='Go to the end'),
    )


class ASK_UNDERSTANDING(object):
    path = 'fsm:fsm_node'
    title = 'How well do you feel you understand now? If you need more clarification, tell us.'

    edges = (
        dict(name='next', toNode='GET_UNDERSTANDING', title='Go to the end'),
    )


class GET_UNDERSTANDING(object):
    path = 'fsm:fsm_node'
    title = 'GET_UNDERSTANDING'

    @staticmethod
    def get_pending_faqs(chat_id, ul_id):
        # TODO change to the Assignment expressions in Python3.8
        faq_data = c_faq_data().find_one({"chat_id": chat_id, "ul_id": ul_id})
        return faq_data.get('faqs', {}) if faq_data else {}

    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        fsm = edge.fromNode.fsm
        inquiry_id = c_chat_context().find_one({"chat_id": fsmStack.id}).get('actual_inquiry_id')
        if inquiry_id:
            ob = InquiryCount.objects.filter(id=inquiry_id).first()
            ob.status = fsmStack.next_point.text.lower()
            ob.save()

        # Defaul value - go to asking new faq from Student
        next_node = edge.toNode

        if fsmStack.next_point.text.lower() == 'help':
            next_node = fsm.get_node('WILL_TRY_MESSAGE_3')
        else:
            ul_id = c_chat_context().find_one({"chat_id": fsmStack.id}).get('actual_ul_id')

            show_another_faq = False
            for key, value in list(self.get_pending_faqs(chat_id=fsmStack.id, ul_id=ul_id).items()):
                if not value.get('status').get('done', False):
                    show_another_faq = True
                    break
            if show_another_faq:
                next_node = fsm.get_node('SHOW_FAQ_BY_ONE')

        return next_node

    edges = (
        dict(name='next', toNode='ASK_NEW_FAQ', title='Go to the end'),
    )


class WILL_TRY_MESSAGE_2(object):
    path = 'fsm:fsm_node'
    title = 'We will try to get you an answer to this.'

    @staticmethod
    def get_pending_faqs(chat_id, ul_id):
        # TODO change to the Assignment expressions in Python3.8
        faq_data = c_faq_data().find_one({"chat_id": chat_id, "ul_id": ul_id})
        return faq_data.get('faqs', {}) if faq_data else {}

    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        fsm = edge.fromNode.fsm
        ul_id = c_chat_context().find_one({"chat_id": fsmStack.id}).get('actual_ul_id')

        show_another_faq = False
        for key, value in list(self.get_pending_faqs(chat_id=fsmStack.id, ul_id=ul_id).items()):
            if not value.get('status').get('done', False):
                show_another_faq = True
                break
        return fsm.get_node('SHOW_FAQ_BY_ONE') if show_another_faq else edge.toNode

    edges = (
        dict(name='next', toNode='ASK_NEW_FAQ', title='Go to the end'),
    )


class WILL_TRY_MESSAGE_3(object):
    path = 'fsm:fsm_node'
    title = 'We will try to provide more explanation for this.'

    @staticmethod
    def get_pending_faqs(chat_id, ul_id):
        # TODO change to the Assignment expressions in Python3.8
        faq_data = c_faq_data().find_one({"chat_id": chat_id, "ul_id": ul_id})
        return faq_data.get('faqs', {}) if faq_data else {}

    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        fsm = edge.fromNode.fsm
        ul_id = c_chat_context().find_one({"chat_id": fsmStack.id}).get('actual_ul_id')

        show_another_faq = False
        for key, value in list(self.get_pending_faqs(chat_id=fsmStack.id, ul_id=ul_id).items()):
            if not value.get('status').get('done', False):
                show_another_faq = True
                break
        return fsm.get_node('SHOW_FAQ_BY_ONE') if show_another_faq else edge.toNode

    edges = (
        dict(name='next', toNode='ASK_NEW_FAQ', title='Go to the end'),
    )


class SELECT_NEXT_FAQ(object):
    path = 'fsm:fsm_node'
    title = 'SELECT_NEXT_FAQ'

    @staticmethod
    def get_pending_faqs(chat_id, ul_id):
        # TODO change to the Assignment expressions in Python3.8
        faq_data = c_faq_data().find_one({"chat_id": chat_id, "ul_id": ul_id})
        return faq_data.get('faqs', {}) if faq_data else {}

    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        fsm = edge.fromNode.fsm
        ul_id = c_chat_context().find_one({"chat_id": fsmStack.id}).get('actual_ul_id')

        show_another_faq = False
        for key, value in list(self.get_pending_faqs(chat_id=fsmStack.id, ul_id=ul_id).items()):
            if not value.get('status').get('done', False):
                show_another_faq = True
                break
        return fsm.get_node('SHOW_FAQ_BY_ONE') if show_another_faq else edge.toNode

    edges = (
        dict(name='next', toNode='ASK_NEW_FAQ', title='Go to the end'),
    )


class ASK_NEW_FAQ(object):
    path = 'fsm:fsm_node'
    title = 'Is there anything else you\'re wondering about, where you\'d like clarification or something you\'re unsure about this point?'

    edges = (
        dict(name='next', toNode='GET_NEW_FAQ', title='Go to the end'),
    )


class GET_NEW_FAQ(object):
    path = 'fsm:fsm_node'
    title = 'GET_NEW_FAQ'

    def next_edge(self, edge, fsmStack, request, useCurrent=False, **kwargs):
        fsm = edge.fromNode.fsm
        return fsm.get_node('NEW_FAQ_TITLE') if fsmStack.next_point.text.lower() == 'yes' else edge.toNode

    edges = (
        dict(name='next', toNode='END', title='Go to the end'),
    )


class FUCK(object):
    path = 'fsm:fsm_node'
    title = 'FUCK'

    edges = (
        dict(name='next', toNode='END', title='Go to the end'),
    )


class ADDING_FAQ(object):
    path = 'fsm:fsm_node'
    title = 'ADDING_FAQ'

    def get_help(self, node, state, request):
        return """
            First, write a 'headline version' of you question
            as a single sentence, as clearly and simply
            as you can. (You'll have a chance to explain your
            question fully in the next step)
        """

    edges = (
        dict(name='next', toNode='NEW_FAQ_TITLE', title='Go to the end'),
    )


class NEW_FAQ_TITLE(object):
    path = 'fsm:fsm_node'
    title = 'First, write a \'headline version\' of your question as a single sentence, as cleary and simply as you can. (You\'ll have a chance to explain your question fully in the next step)'

    edges = (
        dict(name='next', toNode='GET_NEW_FAQ_TITLE', title='Go to the end'),
    )


class GET_NEW_FAQ_TITLE(object):
    path = 'fsm:fsm_node'
    title = 'GET_NEW_FAQ_TITLE'

    edges = (
        dict(name='next', toNode='NEW_FAQ_DESCRIPTION', title='Go to the end'),
    )


class NEW_FAQ_DESCRIPTION(object):
    path = 'fsm:fsm_node'
    title = 'Next, let\'s nail down exactly what you\'re unsure about, by applying your question to a real-world situation, to indentify what specific outcome you\'re unsure about (e.g. is A going to happen, or B?\')'

    edges = (
        dict(name='next', toNode='GET_NEW_FAQ_DESCRIPTION', title='Go to the end'),
    )


class GET_NEW_FAQ_DESCRIPTION(object):
    path = 'fsm:fsm_node'
    title = 'GET_NEW_FAQ_DESCRIPTION'

    edges = (
        dict(name='next', toNode='WILL_TRY_MESSAGE', title='Go to the end'),
    )


class WILL_TRY_MESSAGE(object):
    path = 'fsm:fsm_node'
    title = 'We\'ll try to get you an answer to this.'

    edges = (
        dict(name='next', toNode='END', title='Go to the end'),
    )


class END(object):
    def get_path(self, node, state, request, **kwargs):
        """
        Get URL for next steps in this unit.
        """
        unitStatus = state.get_data_attr('unitStatus')
        return unitStatus.unit.get_study_url(request.path)
    # node specification data goes here
    title = 'Additional lessons completed'
    help = '''OK, let's continue.'''


def get_specs():
    """
    Get FSM specifications stored in this file.
    """
    from fsm.fsmspec import FSMSpecification
    spec = FSMSpecification(
        name='faq',
        hideTabs=True,
        title='Take the courselet core lessons',
        pluginNodes=[
            START,
            SHOW_FAQS,
            INTRO_MSG,
            MSG_FOR_INQUIRY,
            SHOW_FAQ_BY_ONE,
            ASK_FOR_FAQ_ANSWER,
            GET_FOR_FAQ_ANSWER,
            SHOW_FAQ_ANSWERS,
            ASK_UNDERSTANDING,
            GET_UNDERSTANDING,
            WILL_TRY_MESSAGE_2,
            WILL_TRY_MESSAGE_3,
            SELECT_NEXT_FAQ,
            ASK_NEW_FAQ,
            GET_NEW_FAQ,
            ADDING_FAQ,
            NEW_FAQ_TITLE,
            GET_NEW_FAQ_TITLE,
            NEW_FAQ_DESCRIPTION,
            GET_NEW_FAQ_DESCRIPTION,
            WILL_TRY_MESSAGE,
            FUCK,
            END],
    )
    return (spec,)
