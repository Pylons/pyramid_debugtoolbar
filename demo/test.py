# -*- coding: utf-8 -*-

import unittest

# TODO
# to run:
# console 1: java -jar selenium-server.jar
# console 2: start the debug toolbar demo app (python demo.py)
# console 3: python test.py

# Instead of using -browserSessionReuse as an arg to
# selenium-server.jar to speed up tests, we rely on
# setUpModule/tearDownModule functionality.

browser = None


def setUpModule():
    from selenium import webdriver
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

    global browser

    browser = webdriver.Remote(
        command_executor='http://127.0.0.1:4444/wd/hub',
        desired_capabilities=DesiredCapabilities.FIREFOX)

    return browser


def tearDownModule():
    browser.close()


class PageTest(unittest.TestCase):
    def visit_dbtb(self):
        browser.get('http://127.0.0.1:8080')
        browser.find_element_by_id('pShowToolBarButton') .click()
        browser.switch_to_window(browser.window_handles[-1])

    def test_home_page(self):
        browser.get('http://127.0.0.1:8080')
        self.assertTrue("example" in browser.page_source)
        browser.find_element_by_id('pDebug')

    def test_home_page_gt_255_in_uri(self):
        browser.get('http://127.0.0.1:8080/%C3%A9')
        self.assertTrue("example" in browser.page_source)
        browser.find_element_by_id('pDebug')

    def test_redirect(self):
        browser.get('http://127.0.0.1:8080/redirect')
        self.assertTrue("Redirect" in browser.page_source)
        browser.find_element_by_id('pDebug')

    def test_exception(self):
        browser.get('http://127.0.0.1:8080/exc')
        self.assertTrue("NotImplementedError" in browser.page_source)
        browser.find_element_by_id('pDebug')
        browser.find_element_by_css_selector('.debugger')

    def test_notfound(self):
        browser.get('http://127.0.0.1:8080/notfound')
        self.assertTrue("Not Found" in browser.page_source)
        browser.find_element_by_id('pDebug')

    def test_exception_console(self):
        browser.get('http://127.0.0.1:8080/exc')
        browser.find_element_by_css_selector('.console-icon')
        self.assertRaises(Exception,
                          browser.find_element_by_css_selector,
                          ('.console',))
        browser.find_element_by_css_selector('.console-icon').click()
        browser.find_element_by_css_selector('.console')


class ToolbarTest(unittest.TestCase):
    """docstring for ToolbarTest"""

    def setUp(self):
        browser.get('http://127.0.0.1:8080/test_sqla')
        browser.find_element_by_id('pShowToolBarButton') .click()
        browser.switch_to_window(browser.window_handles[-1])

    def tearDown(self):
        browser.close()
        browser.switch_to_window(browser.window_handles[-1])

    def test_version_panel(self):
        import time
        time.sleep(0.2)
        browser.find_element_by_link_text('Global').click()
        browser.find_element_by_css_selector('a#pDebugVersionPanel').click()
        browser.find_element_by_css_selector('#pDebugVersionPanel-content')

    def test_settings_panel(self):
        import time
        time.sleep(0.2)
        browser.find_element_by_link_text('Global').click()
        browser.find_element_by_css_selector('a#pDebugSettingsPanel').click()
        browser.find_element_by_css_selector('#pDebugSettingsPanel-content')

    def test_routes_panel(self):
        import time
        time.sleep(0.2)
        browser.find_element_by_link_text('Global').click()
        browser.find_element_by_css_selector('a#pDebugRoutesPanel').click()
        browser.find_element_by_css_selector('#pDebugRoutesPanel-content')

    def test_tweens_panel(self):
        import time
        time.sleep(0.2)
        browser.find_element_by_link_text('Global').click()
        browser.find_element_by_css_selector('a#pDebugTweensPanel').click()
        browser.find_element_by_css_selector('#pDebugTweensPanel-content')

    def test_headers_panel(self):
        import time
        time.sleep(0.2)
        browser.find_element_by_css_selector('a#pDebugHeaderPanel').click()
        browser.find_element_by_css_selector('#pDebugHeaderPanel-content')

    def test_requestvars_panel(self):
        import time
        time.sleep(0.2)
        browser.find_element_by_css_selector('a#pDebugRequestVarsPanel').click()
        browser.find_element_by_css_selector('#pDebugRequestVarsPanel-content')

    def test_renderings_panel(self):
        import time
        time.sleep(0.2)
        browser.find_element_by_css_selector('a#pDebugTemplatePanel').click()
        browser.find_element_by_css_selector('#pDebugTemplatePanel-content')

    def test_logging_panel(self):
        import time
        time.sleep(0.2)
        browser.find_element_by_css_selector('a#pDebugLoggingPanel').click()
        browser.find_element_by_css_selector('#pDebugLoggingPanel-content')

    #def test_sqla_select_panel(self):
        #browser.open('/test_sqla')
        #browser.wait_for_page_to_load("30000")
        #self.visit_dbtb()
        #browser.fire_event("css=a.pDebugSQLAlchemyPanel", 'click')
        #browser.fire_event("link=SELECT", 'click')
        #browser.wait_for_condition(
            #"selenium.isElementPresent(\"//table[@id='pSqlaTable']\")",
            #"30000")
        #result = browser.get_text('css=#pDebugWindow .pDebugPanelTitle h3')
        #self.assertEqual(result, 'SQL Select')

    #def test_sqla_explain_panel(self):
        #browser.open('/test_sqla')
        #browser.wait_for_page_to_load("30000")
        #self.visit_dbtb()
        #browser.fire_event("css=a.pDebugSQLAlchemyPanel", 'click')
        #browser.fire_event("link=EXPLAIN", 'click')
        #browser.wait_for_condition(
            #"selenium.isElementPresent(\"//table[@id='pSqlaTable']\")",
            #"30000")
        #result = browser.get_text('css=#pDebugWindow .pDebugPanelTitle h3')
        #self.assertEqual(result, 'SQL Explained')

    def test_performance_panel(self):
        import time
        time.sleep(0.2)
        browser.find_element_by_css_selector('a#pDebugPerformancePanel').click()
        browser.find_element_by_css_selector('#pDebugPerformancePanel-content')

    def test_sqla_panel(self):
        import time
        time.sleep(0.2)
        browser.find_element_by_css_selector('a#pDebugSQLAlchemyPanel').click()
        browser.find_element_by_css_selector('#pDebugSQLAlchemyPanel-content')

    #def test_performance_panel_with_profiling(self):
        #browser.open('/')
        #browser.wait_for_page_to_load("30000")
        #self.visit_dbtb()
        #browser.fire_event('css=span.switch.inactive', 'click') # turn on
        #browser.open('/')
        #browser.wait_for_page_to_load("30000")
        #self.visit_dbtb()
        #browser.fire_event("css=a.pDebugPerformancePanel", 'click')
        #browser.fire_event('css=span.switch.active', 'click') # turn off
        #result = browser.get_text('css=#pDebugPerformancePanel-content')
        #self.failIf('profiler is not activ' in result, result)


    #def test_introspection_panel(self):
        #try:
            #from pyramid.registry import Introspectable # 1.3 only
            #Introspectable
            #browser.open('/')
            #browser.wait_for_page_to_load("30000")
            #self.visit_dbtb()
            #browser.fire_event("css=a.pDebugIntrospectionPanel", 'click')
            #result = browser.is_visible('css=#pDebugIntrospectionPanel-content')
            #self.failUnless(result)
        #except:
            #pass

    #def test_highorder(self):
        #try:
            #from urllib import quote
        #except ImportError:
            #from urllib.parse import quote
        #browser.open(quote(b'/La Pe\xc3\xb1a'))
        #browser.wait_for_page_to_load("30000")
        #self.failUnless(browser.is_element_present('id=pDebug'))


if __name__ == '__main__':
    setUpModule()
    try:
        unittest.main()
    finally:
        tearDownModule()
