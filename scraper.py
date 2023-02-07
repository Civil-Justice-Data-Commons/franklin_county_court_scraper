###
# Franklin County Court Database Scraper Prototype
# v0.1
# Feb 2023
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
###

# Importing sys, os, and argparse to do command prompt interaction etc
import sys
import os
import argparse
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
# Import Pretty Printing to make the printing pretty
import pprint

def scrape_record(driver, year, code, case_num, wait_time):

    driver.get('http://www.fcmcclerk.com/case/search/')

    try:
         element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.NAME, 'case_number')))
    finally:
        driver.find_element('name','case_number').clear()
        driver.find_element('name', 'case_number').send_keys(f'{year} {code} {str(case_num).zfill(6)}' + Keys.ENTER)

        try:
            button = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CLASS, 'btn btn-primary btn-xs')))
        finally:
            possible_view_button = driver.find_element('class','btn btn-primary btn-xs')
            if possible_view_button.getAttribute('value') == 'View':
                print (f'Located Case: {year} {code} {str(case_num).zfill(6)}')

                # Click view button and go to next page
                possible_view_button.click()
                wait.until(EC.number_of_windows_to_be(2))
                driver.switch_to.window(driver.window_handles[1])

                # Check to make sure the case ID matches the page we're looking at
                if driver.find_element(By.CLASS_NAME, 'nav-bar-brand').text != f'{year} {code} {str(case_num).zfill(6)}':
                    print (f'Something went wrong when looking at case {year} {code} {str(i).zfill(6)}')
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
                        temp_case_record['case_number'] = f'{year} {code} {str(case_num).zfill(6)}'
                        temp_case_record['status'] = re.search(r'Status:\s(\w*)', source_code).group(1)
                        temp_case_record['file_date'] = re.search(r'Filed:\s\d\d/\d\d/\d\d\d\d', source_code).group(1)
                        # This very long regex is fairly specific to the current html and grabs the name, address, city, state, and zip of the plaintiff
                        temp_plaintiffs = re.findall(r'>(?P<name>.*)</td>\s*<td\sclass="title">Type</td>\s*<td\sclass="data">PLAINTIFF</td>\s*.*\s*<td\sclass="title">Address</td>\s*<td\sclass="data"\scolspan="\d">(?P<address>.*)</td>\s*</tr><tr\svalign="top">\s*.*\s*<td\sclass="data">(?P<city>.*)</td>\s*.*\s*<td\sclass="data">(?P<state>[a-zA-Z]*)/(?P<zip>\d*)</td>')
                        temp_case_record['plaintiffs'] = {}
                        for p in temp_plaintiffs:
                            temp_case_record['plaintiffs'].append()

def bulk_scrape(driver, year, code, start, end, pause, jitter=False, wait_time):

    results = {}

    for cur_case_num in range(start,end):
    
        scrape_record(driver, year, code, cur_case_num, wait_time)

        pt = pause_time
        if jitter:
            pt += random.randint(1,30)
        time.sleep(pt)

# Called to scrape a single record without setting up any init factors etc. Mostly used for testing.
def single_scrape(case_year=1998, case_code='CVI', case_number=3000, headless=False):

    # Set up for using with Chrome
    chrome_options = Options
    if headless :
        chrome_options.add_argument('--headless')
    web_driver = webdriver.Chrome(service = Service(ChromeDriverManager().install()), options = chrome_options) 

    # Run the single scrape
    results = scrape_record(web_driver, case_year, case_code, case_num, web_driver_wait_time)

    # Pretty Print those results
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(results)

    return results


if __name__ == '__main__':

    # Set up dictonary to hold data
    case_records = {}
    
    chrome_options = Options()

    # Handle arguments if we don't want to use the defaults
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_file', type=str, required=False)
    parser.add_argument('--case_year', type=int, required=False)
    parser.add_argument('--case_code', type=str, required=False)
    parser.add_argument('--range_start', type=int, required=False)
    parser.add_argument('--range_end', type=int, required=False)
    parser.add_argument('--pause_time', type=int, required=False)
    parser.add_argument('--jitter', type=bool, required=False)
    parser.add_argument('--web_driver_wait_time', type=int, required=False)
    parser.add_argument('--headless', type=bool, required=False)
    parser.add_argument('--results_dir', type=str, required=False)
    args = parser.parse_args()

    # If there is an argument supplied for an option, use that, otherwise use defaults from file
    if args.default_data is not None: 
        default_data = json.load(args.default_data,'r')
    else:
        default_data = json.load('defaults.json','r')
    # Year to look at cases from
    if args.case_year is not None:
        case_year = args.case_year
    else:
        case_year = default_data['case_year']
    # Case ID code to use, 'CVI' for civil
    if args.case_code is not None:
        case_code = args.case_code
    else:
        case_code = default_data['case_code']  
    # Case num to start looking from (will be padded to 6 char)
    if args.range_start is not None:
        range_start = args.range_start
    else:
        range_start = default_data['range_start']
    # Case num to end looking at
    if args.range_end is not None:
        range_end = args.range_end
    else:
        range_end = default_data['range_end']  
    # Used to space out requests, in sec
    if args.pause_time is not None:
        pause_time = args.pause_time
    else:
        pause_time = default_data['pause_time']
    # Introduces a time jitter to make scrapping seem more human
    if args.jitter is not None:
        jitter = args.jitter
    else:
        jitter = default_data['jitter']
    # Used to tell selenium how long to wait while trying to find stuff
    if args.web_driver_wait_time is not None:
        web_driver_wait_time = args.web_driver_wait_time
    else:
        web_driver_wait_time = default_data['web_driver_wait_time']
     # Tell selenium to run headless or not
    if args.headless is not None:
        if args.headless :
            chrome_options.add_argument('--headless')
    else:
        if default_data['headless']:
            chrome_options.add_argument('--headless')
    # Used to tell selenium how long to wait while trying to find stuff
    if args.results_dir is not None:
        results_dir = args.results_dir
    else:
        results_dir = default_data['results_dir']

    # Set up for using with Chrome
    web_driver = webdriver.Chrome(service = Service(ChromeDriverManager().install()), options = chrome_options) 

    # Bulk Scrape
    results = bulk_scrape(web_driver, case_year, case_code, range_start, range_end, pause_time, jitter, web_driver_wait_time)

    # Close the driver
    driver.close()