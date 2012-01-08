# -*- coding: utf-8 -*-

import unittest

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
        self.failUnless(browser.is_element_present('id=pDebugToolbar'))

    def test_home_page_gt_255_in_uri(self):
        browser.open('/%C3%A9')
        browser.wait_for_page_to_load("30000")
        self.failUnless(browser.is_text_present("example"))
        self.failUnless(browser.is_element_present('id=pDebugToolbar'))

    def test_redirect(self):
        browser.open('/redirect')
        browser.wait_for_page_to_load("30000")
        self.failUnless(browser.is_text_present("Redirect"))
        self.failUnless(browser.is_element_present('id=pDebugToolbar'))

    def test_exception(self):
        browser.open('/exc')
        browser.wait_for_page_to_load("30000")
        self.failUnless(browser.is_text_present("NotImplementedError"))
        self.failUnless(browser.is_element_present('id=pDebugToolbar'))
        self.failUnless(browser.is_element_present('css=.debugger'))

    def test_notfound(self):
        browser.open('/notfound')
        browser.wait_for_page_to_load("30000")
        self.failUnless(browser.is_text_present("Not Found"))
        self.failUnless(browser.is_element_present('id=pDebugToolbar'))

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
        browser.fire_event("css=a#pShowToolBarButton", 'click')
        browser.fire_event("css=a.pDebugSettingsPanel", 'click')
        result = browser.is_visible('css=#pDebugSettingsPanel-content')
        self.failUnless(result)

    def test_logging_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#pShowToolBarButton", 'click')
        browser.fire_event("css=a.pDebugLoggingPanel", 'click')
        result = browser.is_visible('css=#pDebugLoggingPanel-content')
        self.failUnless(result)

    def test_routes_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#pShowToolBarButton", 'click')
        browser.fire_event("css=a.pDebugRoutesPanel", 'click')
        result = browser.is_visible('css=#pDebugRoutesPanel-content')
        self.failUnless(result)

    def test_headers_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#pShowToolBarButton", 'click')
        browser.fire_event("css=a.pDebugHeaderPanel", 'click')
        result = browser.is_visible('css=#pDebugHeaderPanel-content')
        self.failUnless(result)

    def test_sqla_panel(self):
        browser.open('/test_sqla')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#pShowToolBarButton", 'click')
        browser.fire_event("css=a.pDebugSQLAlchemyPanel", 'click')
        result = browser.is_visible('css=#pDebugSQLAlchemyPanel-content')
        self.failUnless(result)

    def test_sqla_select_panel(self):
        browser.open('/test_sqla')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#pShowToolBarButton", 'click')
        browser.fire_event("css=a.pDebugSQLAlchemyPanel", 'click')
        browser.fire_event("link=SELECT", 'click')
        browser.wait_for_condition(
            "selenium.isElementPresent(\"//table[@id='pSqlaTable']\")",
            "30000")
        result = browser.get_text('css=#pDebugWindow .pDebugPanelTitle h3')
        self.assertEqual(result, 'SQL Select')

    def test_sqla_explain_panel(self):
        browser.open('/test_sqla')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#pShowToolBarButton", 'click')
        browser.fire_event("css=a.pDebugSQLAlchemyPanel", 'click')
        browser.fire_event("link=EXPLAIN", 'click')
        browser.wait_for_condition(
            "selenium.isElementPresent(\"//table[@id='pSqlaTable']\")",
            "30000")
        result = browser.get_text('css=#pDebugWindow .pDebugPanelTitle h3')
        self.assertEqual(result, 'SQL Explained')

    def test_performance_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#pShowToolBarButton", 'click')
        browser.fire_event("css=a.pDebugPerformancePanel", 'click')
        result = browser.is_visible('css=#pDebugPerformancePanel-content')
        self.failUnless(result)

    def test_performance_panel_with_profiling(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#pShowToolBarButton", 'click')
        browser.fire_event('css=span.switch.inactive', 'click') # turn on
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a.pDebugPerformancePanel", 'click')
        browser.fire_event('css=span.switch.active', 'click') # turn off
        result = browser.get_text('css=#pDebugPerformancePanel-content')
        self.failIf('profiler is not activ' in result, result)

    def test_renderings_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#pShowToolBarButton", 'click')
        browser.fire_event("css=a.pDebugTemplatePanel", 'click')
        result = browser.is_visible('css=#pDebugTemplatePanel-content')
        self.failUnless(result)

    def test_version_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#pShowToolBarButton", 'click')
        browser.fire_event("css=a.pDebugVersionPanel", 'click')
        result = browser.is_visible('css=#pDebugVersionPanel-content')
        self.failUnless(result)

    def test_requestvars_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#pShowToolBarButton", 'click')
        browser.fire_event("css=a.pDebugRequestVarsPanel", 'click')
        result = browser.is_visible('css=#pDebugRequestVarsPanel-content')
        self.failUnless(result)

    def test_tweens_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#pShowToolBarButton", 'click')
        browser.fire_event("css=a.pDebugTweensPanel", 'click')
        result = browser.is_visible('css=#pDebugTweensPanel-content')
        self.failUnless(result)

    def test_introspection_panel(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        browser.fire_event("css=a#pShowToolBarButton", 'click')
        browser.fire_event("css=a.pDebugIntrospectionPanel", 'click')
        result = browser.is_visible('css=#pDebugIntrospectionPanel-content')
        self.failUnless(result)

    def test_highorder(self):
        try:
            from urllib import quote
        except ImportError:
            from urllib.parse import quote
        browser.open(quote(b'/La Pe\xc3\xb1a'))
        browser.wait_for_page_to_load("30000")
        self.failUnless(browser.is_element_present('id=pDebugToolbar'))
        

if __name__ == '__main__':
    setUpModule()
    try:
        unittest.main()
    finally:
        tearDownModule()
