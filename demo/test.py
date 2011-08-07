# -*- coding: utf-8 -*-

import unittest
import time

# to run:
# console 1: java -jar selenium-server.jar
# console 2: start the debug toolbar demo app (python demo.py)
# console 3: python test.py

# Instead of using -browserSessionReuse as an arg to
# selenium-server.jar to speed up tests, we rely on
# setUpModule/tearDownModule functionality.

browser = None

def setUpModule():
    from selenium import selenium
    global browser
    browser = selenium("localhost", 4444, "*chrome", "http://localhost:8080/")
    browser.start()
    return browser

def tearDownModule():
    browser.stop()

class PageTest(unittest.TestCase):
    def test_home_page(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        self.failUnless(browser.is_text_present("example"))
        self.failUnless(browser.is_element_present('id=flDebugToolbar'))

    def test_redirect(self):
        browser.open('/redirect')
        browser.wait_for_page_to_load("30000")
        self.failUnless(browser.is_text_present("Redirect"))
        self.failUnless(browser.is_element_present('id=flDebugToolbar'))

    def test_exception(self):
        browser.open('/exc')
        browser.wait_for_page_to_load("30000")
        self.failUnless(browser.is_text_present("NotImplementedError"))
        self.failUnless(browser.is_element_present('id=flDebugToolbar'))
        self.failUnless(browser.is_element_present('css=.debugger'))

    def test_exception_console(self):
        browser.open('/exc')
        browser.wait_for_page_to_load("30000")
        self.failUnless(browser.is_element_present("css=.console-icon"))
        self.failIf(browser.is_element_present("css=.console"))
        browser.fire_event("css=.console-icon", "click")
        self.failUnless(browser.is_element_present("css=.console"))

    def test_settings_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#flShowToolbarButton", 'click')
        browser.fire_event("css=a.flDebugSettingsPanel", 'click')
        result = browser.is_visible('css=#flDebugSettingsPanel-content')
        self.failUnless(result)

    def test_logging_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#flShowToolbarButton", 'click')
        browser.fire_event("css=a.flDebugLoggingPanel", 'click')
        result = browser.is_visible('css=#flDebugLoggingPanel-content')
        self.failUnless(result)

    def test_routes_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#flShowToolbarButton", 'click')
        browser.fire_event("css=a.flDebugRoutesPanel", 'click')
        result = browser.is_visible('css=#flDebugRoutesPanel-content')
        self.failUnless(result)

    def test_headers_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#flShowToolbarButton", 'click')
        browser.fire_event("css=a.flDebugHeaderPanel", 'click')
        result = browser.is_visible('css=#flDebugHeaderPanel-content')
        self.failUnless(result)

    def test_sqla_panel(self):
        browser.open('/test_sqla')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#flShowToolbarButton", 'click')
        browser.fire_event("css=a.flDebugSQLAlchemyPanel", 'click')
        result = browser.is_visible('css=#flDebugSQLAlchemyPanel-content')
        self.failUnless(result)

    def test_sqla_select_panel(self):
        browser.open('/test_sqla')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#flShowToolbarButton", 'click')
        browser.fire_event("css=a.flDebugSQLAlchemyPanel", 'click')
        browser.fire_event("link=SELECT", 'click')
        browser.wait_for_condition(
            '!selenium.isElementPresent("id=flSqlaTable")',
            "30000")
        result = browser.get_text('css=#flDebugWindow .flDebugPanelTitle h3')
        self.assertEqual(result, 'SQL Select')

    def test_sqla_explain_panel(self):
        browser.open('/test_sqla')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#flShowToolbarButton", 'click')
        browser.fire_event("css=a.flDebugSQLAlchemyPanel", 'click')
        browser.fire_event("link=EXPLAIN", 'click')
        browser.wait_for_condition(
            '!selenium.isElementPresent("id=flSqlaTable")',
            "30000")
        result = browser.get_text('css=#flDebugWindow .flDebugPanelTitle h3')
        self.assertEqual(result, 'SQL Explained')

    def test_performance_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#flShowToolbarButton", 'click')
        browser.fire_event("css=a.flDebugPerformancePanel", 'click')
        result = browser.is_visible('css=#flDebugPerformancePanel-content')
        self.failUnless(result)

    def test_renderings_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#flShowToolbarButton", 'click')
        browser.fire_event("css=a.flDebugTemplatePanel", 'click')
        result = browser.is_visible('css=#flDebugTemplatePanel-content')
        self.failUnless(result)

    def test_version_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#flShowToolbarButton", 'click')
        browser.fire_event("css=a.flDebugVersionPanel", 'click')
        result = browser.is_visible('css=#flDebugVersionPanel-content')
        self.failUnless(result)

    def test_requestvars_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#flShowToolbarButton", 'click')
        browser.fire_event("css=a.flDebugRequestVarsPanel", 'click')
        result = browser.is_visible('css=#flDebugRequestVarsPanel-content')
        self.failUnless(result)

if __name__ == '__main__':
    setUpModule()
    try:
        unittest.main()
    finally:
        tearDownModule()
