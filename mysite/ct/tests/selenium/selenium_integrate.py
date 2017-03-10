"""
Selenium integration tests.
"""
from django.core.urlresolvers import reverse


def test_main_page(selenium, live_server):
    selenium.get(live_server.url)


def test_user_courses(selenium, live_server):
    selenium.get('%s%s' % (live_server.url, reverse('ct:home')))
