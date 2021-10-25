#!/usr/bin/env python3
# install the required packages:
# - pip3 install -U selenium
# - pip3 install -U python-dotenv
# - (only if local browser on your host machine should be used:) pip3 install chromedriver-py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import time

# load environment variables from .env file.
from dotenv import load_dotenv
load_dotenv()

import os

class PrimocoExportDownloader():
    RUN_LOCALLY = False

    def __init__(self):
        print('Connecting to driver...')
        if self.RUN_LOCALLY:
            from chromedriver_py import binary_path # this will get you the path variable
            self.browser = webdriver.Chrome(executable_path=binary_path)
        else:
            self.browser = webdriver.Remote(
                command_executor='http://localhost:4444/wd/hub', # selenium in Docker
                options=webdriver.ChromeOptions()
            )

    def login(self):
        if not 'PRIMOCO_USER' in os.environ or not 'PRIMOCO_PASSWORD' in os.environ:
            raise Exception("PRIMOCO_USER and/or PRIMOCO_PASSWORD environment variables must be set.")

        print('Trying to login')

        self.browser.get('https://primoco.me/en/user/login')
        login_form = self.browser.find_elements(By.CSS_SELECTOR, '#login-form')

        if login_form:
            username = self.browser.find_element(By.CSS_SELECTOR, '#login-form #username')
            username.send_keys(os.environ['PRIMOCO_USER'])

            password = self.browser.find_element(By.CSS_SELECTOR, '#login-form #password')
            password.send_keys(os.environ['PRIMOCO_PASSWORD'])
            password.send_keys(Keys.RETURN)

            body = self.browser.find_element(By.CSS_SELECTOR, 'body')
            bodyClass = body.get_attribute("class")

            if "Overview" in self.browser.title:
                print("Login successful.")
            else:
                raise Exception("Login failed.")
        else:
            raise Exception("Login form not available.")

    def download(self):
        self.browser.get('https://primoco.me/app/extras/export')
        submitBtn = self.browser.find_element(By.CSS_SELECTOR, '#app_booking_filter_submit')
        print('Starting file download...')
        submitBtn.click()
        time.sleep(5)

        existing = os.path.join(os.environ['DOWNLOAD_LOCATION'], "bookings-current.csv")
        downloaded = os.path.join(os.environ['DOWNLOAD_LOCATION'], "bookings.csv")

        # delete existing export + rename downloaded export
        if os.path.exists(existing):
            if os.path.exists(downloaded):
                print('File downloaded. Deleting old export...')
                os.remove(existing)
                print('Renaming new export...')
                os.rename(downloaded, existing)
                print('File successfully downloaded & renamed.')
            else:
                raise Exception("Downloaded file not found.")
        else:
            if os.path.exists(downloaded):
                os.rename(downloaded, existing)
                print('File successfully downloaded & renamed.')
            else:
                raise Exception("Downloaded file not found.")


    def quitBrowser(self):
        print('Quit the browser')
        self.browser.quit()


if __name__ == '__main__':
    ped = PrimocoExportDownloader()
    try:
        ped.login()
        ped.download()
    finally:
        # make sure the driver connection is properly closed in any case.
        ped.quitBrowser()
