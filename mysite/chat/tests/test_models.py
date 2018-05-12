import re

import pytest


@pytest.mark.django_db
def test_message_canvas(message_canvas):
    html = message_canvas.get_html()
    assert re.search(r'<svg([^>]+)>[\s\S]*?</svg>', html) is not None
