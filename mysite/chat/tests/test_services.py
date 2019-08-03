from collections import namedtuple

import pytest

from chat.services import FsmHandler
from fsm.models import FSMState


@pytest.mark.django_db
def test_live_chat_fsm_handler(unit, chat, user, fsm, fsm_state, mocker):
    assert chat.state is None

    request_data = {'session': {}, 'user': user}
    request = namedtuple('Request', list(request_data.keys()))(*list(request_data.values()))
    handler = FsmHandler()

    next_point = handler.start_point(unit, chat, request)
    assert next_point == chat.next_point

    handler.push_state(chat, request, fsm.name)
    assert chat.state.title == fsm_state.title

    with mocker.mock_module.patch.object(FSMState, 'delete', autospec=True):
        handler.pop_state(chat)
        assert FSMState.delete.call_count == 1
