"""Selenium tests.

Integration tests via Selenium Firefox webdriver.
To run this test we need to install Firefox.
"""
from django.test import LiveServerTestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.ui import Select


class MySeleniumTests(LiveServerTestCase):
    fixtures = ['ct/tests/fixtures/initial_data.json']

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

    def test_lessonseq(self):
        call_command('fsm_deploy')
        driver = self.selenium
        driver.get(self.live_server_url + "/login/?next=/ct/")
        driver.find_element_by_link_text("Sign in").click()
        driver.find_element_by_id("username").clear()
        driver.find_element_by_id("username").send_keys("admin")
        driver.find_element_by_id("password").clear()
        driver.find_element_by_id("password").send_keys("testonly")
        driver.find_element_by_css_selector("button.btn").click()
        driver.find_element_by_link_text("Courses").click()
        driver.find_element_by_xpath("//tr[1]/td/a/b").click()
        driver.find_element_by_link_text("What is a Concept Inventory?").click()
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_id("id_liked").click()
        driver.find_element_by_id("id_liked").click()
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_id("id_text").clear()
        driver.find_element_by_id("id_text").send_keys("50 %")
        Select(driver.find_element_by_id("id_confidence")).select_by_visible_text("Not quite sure")
        driver.find_element_by_id("submit-id-submit").click()
        Select(driver.find_element_by_id("id_selfeval")).select_by_visible_text("Essentially the same")
        Select(driver.find_element_by_id("id_status"))\
            .select_by_visible_text("OK, but need further review and practice")
        driver.find_element_by_id("id_liked").click()
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_id("id_text").clear()
        driver.find_element_by_id("id_text")\
            .send_keys(
                """not enough worked examples demonstrating procedures for students to follow,"""
                """or practice problems for students to train on these procedures"""
            )
        Select(driver.find_element_by_id("id_confidence")).select_by_visible_text("Pretty sure")
        driver.find_element_by_id("submit-id-submit").click()
        Select(driver.find_element_by_id("id_selfeval")).select_by_visible_text("Different")
        Select(driver.find_element_by_id("id_status")).select_by_visible_text("Solidly")
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_xpath("(//input[@name='emlist'])[2]").click()
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_id("id_text").clear()
        driver.find_element_by_id("id_text").send_keys("Some answer")
        Select(driver.find_element_by_id("id_confidence")).select_by_visible_text("Pretty sure")
        driver.find_element_by_id("submit-id-submit").click()
        Select(driver.find_element_by_id("id_selfeval")).select_by_visible_text("Essentially the same")
        Select(driver.find_element_by_id("id_status")).select_by_visible_text("Solidly")
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_id("id_text").clear()
        driver.find_element_by_id("id_text").send_keys("Average student use thinking about concepts ;)")
        Select(driver.find_element_by_id("id_confidence")).select_by_visible_text("Pretty sure")
        driver.find_element_by_id("submit-id-submit").click()
        Select(driver.find_element_by_id("id_selfeval")).select_by_visible_text("Essentially the same")
        Select(driver.find_element_by_id("id_status")).select_by_visible_text("Solidly")
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_id("id_text").clear()
        driver.find_element_by_id("id_text").send_keys("Test")
        Select(driver.find_element_by_id("id_confidence")).select_by_visible_text("Pretty sure")
        driver.find_element_by_id("submit-id-submit").click()
        Select(driver.find_element_by_id("id_selfeval")).select_by_visible_text("Close")
        Select(driver.find_element_by_id("id_status")).select_by_visible_text("Solidly")
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_name("emlist").click()
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_link_text("The Teacher").click()
        driver.find_element_by_link_text("Logout").click()

    def test_teacher_edit_course(self):
        call_command('fsm_deploy')
        driver = self.selenium
        driver.get(self.live_server_url + "/")
        driver.find_element_by_link_text("Sign in").click()
        driver.find_element_by_id("username").clear()
        driver.find_element_by_id("username").send_keys("admin")
        driver.find_element_by_id("password").clear()
        driver.find_element_by_id("password").send_keys("testonly")
        driver.find_element_by_css_selector("button.btn").click()
        driver.find_element_by_link_text("An Introduction to Courselets").click()
        Select(driver.find_element_by_id("id_newOrder")).select_by_visible_text("2")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        Select(driver.find_element_by_xpath("(//select[@id='id_newOrder'])[2]")).select_by_visible_text("1")
        driver.find_element_by_xpath("(//input[@value='Move'])[2]").click()
        driver.find_element_by_link_text("Edit").click()
        driver.find_element_by_id("id_title").clear()
        driver.find_element_by_id("id_title").send_keys("An Introduction to Courselets [new title]")
        Select(driver.find_element_by_id("id_access")).select_by_visible_text("By author only")
        driver.find_element_by_id("id_description").clear()
        driver.find_element_by_id("id_description").send_keys(
            "my first attempt to explain what it's all about\nAdding new description"
        )
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_id("id_title").clear()
        driver.find_element_by_id("id_title").send_keys("New test courselet")
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_link_text("Concepts").click()
        driver.find_element_by_link_text("Lessons").click()
        driver.find_element_by_link_text("Resources").click()
        driver.find_element_by_link_text("Edit").click()
        driver.find_element_by_id("id_title").clear()
        driver.find_element_by_id("id_title").send_keys("New test courselet [new title]")
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_link_text("Edit").click()
        driver.find_element_by_css_selector("form > input[type=\"submit\"]").click()
        driver.find_element_by_link_text("Tasks").click()
        driver.find_element_by_link_text("Start Activity").click()
        driver.find_element_by_link_text("Start Activity").click()
        driver.find_element_by_link_text("Start Activity").click()
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_id("id_search").clear()
        driver.find_element_by_id("id_search").send_keys("test")
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_css_selector("form > input[type=\"submit\"]").click()
        driver.find_element_by_link_text("Home").click()
        driver.find_element_by_link_text("Courselets.org").click()
        driver.get(self.live_server_url + "/ct/")
        driver.find_element_by_link_text("An Introduction to Courselets [new title]").click()
        Select(driver.find_element_by_xpath("(//select[@id='id_newOrder'])[3]")).select_by_visible_text("1")
        driver.find_element_by_xpath("(//input[@value='Move'])[3]").click()
        driver.find_element_by_link_text("Edit").click()
        driver.find_element_by_link_text("Home").click()
        driver.find_element_by_link_text("The Teacher").click()
        driver.find_element_by_link_text("Logout").click()

    def test_add_lesson_search_concept(self):
        call_command('fsm_deploy')
        driver = self.selenium
        driver.get(self.live_server_url + "/")
        driver.find_element_by_link_text("Sign in").click()
        driver.find_element_by_id("username").clear()
        driver.find_element_by_id("username").send_keys("admin")
        driver.find_element_by_id("password").clear()
        driver.find_element_by_id("password").send_keys("testonly")
        driver.find_element_by_css_selector("button.btn").click()
        driver.find_element_by_link_text("An Introduction to Courselets").click()
        driver.find_element_by_link_text("What is a Concept Inventory?").click()
        driver.find_element_by_link_text("Start Activity").click()
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_link_text("Add a New Lesson").click()
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        driver.find_element_by_id("id_search").clear()
        driver.find_element_by_id("id_search").send_keys("Ukraine")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        driver.find_element_by_link_text("Ukraine").click()
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_id("id_title").clear()
        driver.find_element_by_id("id_title").send_keys("Test lesson")
        driver.find_element_by_id("id_text").clear()
        driver.find_element_by_id("id_text").send_keys("Test text.")
        driver.find_element_by_id("submit-id-submit").click()
        driver.find_element_by_link_text("The Teacher").click()
        driver.find_element_by_link_text("Logout").click()
