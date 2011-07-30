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

class HomePageTest(unittest.TestCase):
    def test_it(self):
        browser.open('/')
        browser.wait_for_page_to_load("30000")
        self.failUnless(browser.is_text_present("example"))
        self.failUnless(browser.is_element_present('id=flDebugToolbar'))

class RedirectTest(unittest.TestCase):
    def test_it(self):
        browser.open('/redirect')
        browser.wait_for_page_to_load("30000")
        self.failUnless(browser.is_text_present("Redirect"))
        self.failUnless(browser.is_element_present('id=flDebugToolbar'))

class ExceptionTest(unittest.TestCase):
    def test_it(self):
        browser.open('/exc')
        browser.wait_for_page_to_load("30000")
        self.failUnless(browser.is_text_present("NotImplementedError"))
        self.failUnless(browser.is_element_present('id=flDebugToolbar'))
        self.failUnless(browser.is_element_present('css=.debugger'))

if __name__ == '__main__':
    setUpModule()
    try:
        unittest.main()
    finally:
        tearDownModule()
