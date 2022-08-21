#!/usr/bin/env -S python3 -u
# install the required packages:
# - (only if local browser on your host machine should be used:) pip3 install chromedriver-py

"""Tests that the remote webdriver works."""
import unittest
from selenium import webdriver
# from chromedriver_py import binary_path # this will get you the path variable

# class LocalGoogleTestCase(unittest.TestCase):
#
#     def setUp(self):
#         self.browser = webdriver.Chrome(executable_path=binary_path)
#         self.addCleanup(self.browser.quit)
#
#     def testPageTitle(self):
#         self.browser.get('http://www.google.com')
#         self.assertIn('Google', self.browser.title)


class RemoteGoogleTestCase(unittest.TestCase):

    def setUp(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.browser = webdriver.Remote(
            command_executor='http://chrome:4444/wd/hub',
            options=options
		)
        self.addCleanup(self.browser.quit)

    def testPageTitle(self):
        self.browser.get('http://www.google.com')
        self.assertIn('Google', self.browser.title)


if __name__ == '__main__':
    print("\n\n=====================================================================\n")
    unittest.main(verbosity=2)

