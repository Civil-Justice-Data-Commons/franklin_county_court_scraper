###
# Franklin County Court Database Scraper Prototype
# v0.1
# July 2022
#
# By James Carey for the Georgetown Civil Justice Data Commons
# For use to scrape the Franklin Co. Court Records website (with their permission)
# Unfortunately not currently working due to being IP blocked after a few hundred requests in an hour
# Designed to search one year and block of case numbers at a time, change constants to update
#
#
#
# Currently a work in progress, with the timing of scrapes and the output needing to be firmed up.
#
#
#
###

# Importing all needed Selenium stuff
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# Import csv and json for writing to file
import pandas as pd
import numpy as np
import csv
import json

# Import regular expressions for searching final page
import re

# Import time and random to use for spacing out requests
import time
import random

# Constants
CASE_YEAR = 1998 # Year to look at cases from
CASE_CODE = 'CVI' # Case ID code to use, 'CVI' for civil
RANGE_START = 3000 # Case num to start looking from (will be padded to 6 char)
RANGE_END = 9000 # Case num to end looking at
PAUSE_TIME = 60 # Used to space out requests, in sec
JITTER = True # Introduces a time jitter to make scrapping seem more human
WEB_DRIVER_WAIT_TIME = 10 # Used to tell selenium how long to wait while trying to find stuff


# Set up dictonary to hold data
case_records = {}
chrome_options = Options()

# Uncomment to let selenium run headless
# chrome_options.add_argument('--headless')

# Set up for using with Chrome
web_driver = webdriver.Chrome(service = Service(ChromeDriverManager().install()), options = chrome_options) 


def scrape_record(driver,case_num):

    driver.get('http://www.fcmcclerk.com/case/search/')

    try:
         element = WebDriverWait(driver, WEB_DRIVER_WAIT_TIME).until(EC.presence_of_element_located((By.NAME, 'case_number')))
    finally:
        driver.find_element('name','case_number').clear()
        driver.find_element('name', 'case_number').send_keys(f'{CASE_YEAR} {CASE_CODE} {str(case_num).zfill(6)}' + Keys.ENTER)

        try:
            button = WebDriverWait(driver, WEB_DRIVER_WAIT_TIME).until(
            EC.presence_of_element_located((By.CLASS, 'btn btn-primary btn-xs')))
        finally:
            possible_view_button = driver.find_element('class','btn btn-primary btn-xs')
            if possible_view_button.getAttribute('value') == 'View':
                print (f'Located Case: {CASE_YEAR} {CASE_CODE} {str(case_num).zfill(6)}')

                    # Click view button and go to next page
                    possible_view_button.click()
                    wait.until(EC.number_of_windows_to_be(2))
                    driver.switch_to.window(driver.window_handles[1])

                    # Check to make sure the case ID matches the page we're looking at
                    if driver.find_element(By.CLASS_NAME, 'nav-bar-brand').text != f'{CASE_YEAR} {CASE_CODE} {str(case_num).zfill(6)}':
                        print (f'Something went wrong when looking at case {CASE_YEAR} {CASE_CODE} {str(i).zfill(6)}')
                        break
                    else:
                        possible_print_button = driver.find_element('class', 'btn btn-success btn-xs btn-block')
                        if possible_print_button.text == 'Print':
                            print (f'"Printing" info...')
                            possible_print_button.click()
                            wait.until(EC.number_of_windows_to_be(3))
                            driver.switch_to.window(driver.window_handles[2])
                            source_code = driver.page_source
                            temp_case_record = {}   
                            temp_case_record['case_number'] = f'{CASE_YEAR} {CASE_CODE} {str(case_num).zfill(6)}'
                            temp_case_record['status'] = re.search(r'Status:\s(\w*)', source_code).group(1)
                            temp_case_record['file_date'] = re.search(r'Filed:\s\d\d/\d\d/\d\d\d\d', source_code).group(1)
                            temp_plaintiffs = re.findall(r'>(.*)</td>\s*<td\sclass="title">Type</td>\s*<td\sclass="data">PLAINTIFF</td>')
                            for p in temp_plaintiffs:
                                temp_case_record

def bulk_scrape(driver,start,end):

    for cur_case_num in range(start,end):
    
        scrape_record(driver, cur_case_num)

        pt = PAUSE_TIME
        if JITTER:
            pt += random.randint(1,30)
        time.sleep(pt)



driver.close()