"""Selenium tests.

Integration tests via Selenium Firefox webdriver.
To run this test we need to install Firefox.
"""
from django.test import LiveServerTestCase
from django.core.urlresolvers import reverse

from selenium.webdriver.firefox.webdriver import WebDriver


class MySeleniumTests(LiveServerTestCase):
    fixtures = ['dumpdata/debug-wo-fsm.json']

    @classmethod
    def setUpClass(cls):
        cls.selenium = WebDriver()
        super(MySeleniumTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(MySeleniumTests, cls).tearDownClass()

    def test_courses(self):
        self.selenium.get('%s%s' % (self.live_server_url, reverse('ct:courses')))
