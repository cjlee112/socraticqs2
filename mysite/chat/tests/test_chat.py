import pytest

from ct.models import Lesson, UnitLesson
from chat.fsm_plugin.chat import get_specs
from chat.fsm_plugin.additional import get_specs as get_specs_additional
from chat.fsm_plugin.resource import get_specs as get_specs_resource
from chat.fsm_plugin.faq import get_specs as get_specs_faq
from . utils.session import Session


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.django_db
def test_simple_chat_flow(fsm, enroll_unit_code, client, user):
    """
    Try to test very simply chat flow.
    """
    get_specs()[0].save_graph('admin')
    get_specs_additional()[0].save_graph('admin')
    get_specs_resource()[0].save_graph('admin')
    get_specs_faq()[0].save_graph('admin')

    lesson = Lesson(title='title', text='きつね', addedBy=user, url='/test/url/')
    lesson.save()
    unitlesson = UnitLesson(
        unit=enroll_unit_code.courseUnit.unit, order=0, lesson=lesson, addedBy=user, treeID=lesson.id
    )
    unitlesson.save()
    client.login(username='admin', password='test_admin')

    page = Session(enroll_unit_code, client)
    page.create_session()

    assert page.show_input() is None
    assert len(page.show_messages()) == 3
    assert page.show_extras() == {'updates': {'threadId': None}}
