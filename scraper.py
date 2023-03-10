###
# Franklin County Court Database Scraper Prototype
# v0.9
# March 2023
#
# By James Carey for the Georgetown Civil Justice Data Commons
# For use to scrape the Franklin Co. Court Records website (with their permission)
# Unfortunately not currently working due to being IP blocked after a few hundred requests in an hour
# Designed to search one year and block of case numbers at a time, change constants to update
#
#
#
# Currently a work in progress, with the timing of scrapes and the output needing to be firmed up to avoid IP blocks.
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
# Import Beautiful Soup for parsing the HTML
from bs4 import BeautifulSoup
# Import csv and json for writing to file
import csv
import json
# Import regular expressions for searching final page
import re
# Import time and random to use for spacing out requests
import time
import random
# Import Pretty Printing to make the printing pretty
import pprint
# tqdm to make progress bars look nice
from tqdm import tqdm

def scrape_record(driver, year, code, case_num, wait_time):

    driver.get('http://www.fcmcclerk.com/case/search/')

    try:
        element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.NAME, 'case_number')))
        driver.find_element('name','case_number').clear()
        driver.find_element('name', 'case_number').send_keys(f'{year} {code} {str(case_num).zfill(6)}' + Keys.ENTER)

        try:
            button = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, '//input[@value="View"]')))
            possible_view_button = driver.find_element(By.XPATH, '//input[@value="View"]')
            print (f'Located Case: {year} {code} {str(case_num).zfill(6)}')

            # Click view button and go to next page
            possible_view_button.click()
            WebDriverWait(driver, wait_time).until(EC.number_of_windows_to_be(2))
            driver.switch_to.window(driver.window_handles[1])

            # Check to make sure the case ID matches the page we're looking at
            if driver.find_element(By.CLASS_NAME, 'hidden-xxs').text != f'{year} {code} {str(case_num).zfill(6)}':
                print (f'Something went wrong when looking at case {year} {code} {str(i).zfill(6)}')
                return None
            else:
                try:
                    possible_print_button = driver.find_element(By.XPATH, '//button[contains(text(), "Print")]')
                    print (f'"Printing" info...')
                    possible_print_button.click()
                    WebDriverWait(driver, wait_time).until(EC.number_of_windows_to_be(3))
                    driver.switch_to.window(driver.window_handles[2])
                    source_code = driver.page_source

                    # Define the case ID, which we will return later and will ID the case in a batch scrape
                    case_ID = f'{year} {code} {str(case_num).zfill(6)}'

                    # Set up the temp case record, to store all the info we're scraping
                    temp_case_record = {}
                    temp_case_record['parties'] = {}
                    temp_case_record['parties']['plaintiffs'] = {}
                    temp_case_record['parties']['defendants'] = {}
                    temp_case_record['attorneys'] = {}
                    temp_case_record['dispositions'] = {}
                    # Financial info not collected in this version of the scraper
                    # temp_case_record['financial_summary'] = {}
                    # temp_case_record['receipts'] = {}
                    temp_case_record['docket'] = {}
                    temp_case_record['status'] = re.search(r'Status:\s(?P<status>\w*)', source_code).group('status')
                    temp_case_record['file_date'] = re.search(r'Filed:\s(?P<file_date>\d\d/\d\d/\d\d\d\d)', source_code).group('file_date')
                    
                    # Make some soup
                    soup = BeautifulSoup(source_code, 'html.parser')

                    try:
                        # Soup for Parties
                        temp_parties_snip = soup.find_all('div', title='PARTIES')
                        temp_parties = temp_parties_snip[0].find_all('td', string = 'Name')

                        # This slightly confusing loop goes through the nodes that make up a party and sort them into either plaintiff or defendant, then store that info
                        for tp in tqdm(temp_parties, desc='Parties', colour='blue'):
                            tp_name = tp.find_next()
                            tp_party_type_raw = tp_name.find_next('td','data')

                            # Work out if it's a plaintiff or defendant, if we aren't sure, skip
                            if tp_party_type_raw.text == 'PLAINTIFF': tp_party_type = 'plaintiffs'
                            elif tp_party_type_raw.text == 'DEFENDANT': tp_party_type = 'defendants'
                            else: continue
                            
                            # Grab the address info
                            tp_address = tp.find_next('tr').find_next('td','data')
                            tp_city = tp_address.find_next('tr').find_next('td','data')
                            
                            # Some regex to mangle the state/zip string into separate fields
                            tp_state_zip_raw = tp_city.find_next('td','data')
                            tp_state_zip_search = re.search(r'(?P<state>\D*)/(?P<zip>\d*)', tp_state_zip_raw.text)
                            tp_state = tp_state_zip_search.group('state')
                            tp_zip = tp_state_zip_search.group('zip')
                            
                            # Store all that party data and address info in the right place in the case record
                            temp_case_record['parties'][tp_party_type][tp_name.text] = {'address':tp_address.text, 'city':tp_city.text, 'state':tp_state, 'zip':tp_zip}
                    except:
                        print('Oops! No Parties!')

                    try:
                        # Soup for Attorneys
                        temp_attorneys_snip = soup.find_all('div', title='ATTORNEYS')
                        ########
                        # NB: The current (Feb 2023) HTML uses 'Name:' WITH A COLON for the Attorneys name field, but 'Name' without one for the Parties name field
                        ########
                        temp_attorneys = temp_attorneys_snip[0].find_all('td', string = 'Name:')

                        # Similar Loop for Attorneys to what we had for Parties
                        for ta in tqdm(temp_attorneys, desc='Attorneys', colour='blue'):
                            ta_name = ta.find_next()
                            ta_party = ta_name.find_next('td','data')
                            # A little fiddling with the address if it has multiple lines, as they often seem to be for attorneys here
                            ta_address_raw = ta.find_next('tr').find_next('td','data')
                            if ta_address_raw.text is None: continue
                            ta_address = ta_address_raw.text
                            ta_city_state_zip_raw = ta_address_raw.find_next('td','data')
                            ta_city_state_zip_search = re.search(r'(?P<city>\D*),\s(?P<state>\D*)\s(?P<zip>\d*)',ta_city_state_zip_raw.text)
                            ta_city = ta_city_state_zip_search.group('city')
                            ta_state = ta_city_state_zip_search.group('state')
                            ta_zip = ta_city_state_zip_search.group('zip')
                            # Store all that attorney data in the case record
                            temp_case_record['attorneys'][ta_party.text] = {'name':ta_name.text, 'address':ta_address, 'city':ta_city, 'state':ta_state, 'zip':ta_zip}
                    except:
                        print('Oops! No Attorneys!')

                    try:
                        # Soup for dispositions
                        temp_dispositions_snip = soup.find_all('div', title='CASE DISPOSITION')
                        # Pop off the first header row, as it is a title row
                        temp_dispositions = temp_dispositions_snip[0].find_all('tr')[1:]

                        for td in tqdm(temp_dispositions, desc='Dispositions', colour='blue'):
                            td_status = td.find_next('td','data')
                            td_status_date = td_status.find_next('td','data')
                            td_dis_code = td_status_date.find_next('td','data')
                            td_dis_date = td_dis_code.find_next('td','data')
                            temp_case_record['dispositions'][td_dis_code.text] = {'status':td_status.text, 'status_date':td_status_date.text, 'disposition_date':td_dis_date.text}
                    except:
                        print('Oops! No dispositions!')

                    # We skip over doing soup for Financial Summary or Receipts, as we are not super concerned about court finances at this time.
                    # Might want to consider adding before doing a large scrape

                    try:
                        # Soup for dockets
                        temp_docket_snip = soup.find_all('div', title='DOCKET')
                        temp_docket = temp_docket_snip[0]
                        # Like the dispositions, pop off the header row
                        # Turn the snip to rows
                        temp_docket_rows = temp_docket.find_all('tr')[1:]

                        # For dockets, we are only going to care about info from events which have a date. 
                        # These events usually are formatted to have the date in the first column, title in second, fees in the last two columns, and further info in the row below
                        cur_date = 'UNDATED'
                        for row in tqdm(temp_docket_rows, desc='Docket', colour='blue'):
                            cells = row.find_all('td')
                            if len(cells) == 4:
                                if cur_date.split('|')[0] == cells[0].text:
                                    cur_date = f'{cells[0].text}|{int(cur_date.split("|")[1]) + 1}'
                                else:
                                    cur_date = f'{cells[0].text}|1'
                                temp_case_record['docket'].setdefault(cur_date, {})
                                temp_case_record['docket'][cur_date]['event'] = fix_blanks(cells[1].text)
                                temp_case_record['docket'][cur_date]['amount'] = fix_blanks(cells[2].text)
                                temp_case_record['docket'][cur_date]['balance'] = fix_blanks(cells[3].text)
                            else:
                                temp_case_record['docket'][cur_date]['details'] = fix_blanks(cells[1].text)
                    except:
                        print('Oops! No dockets!')

                    # Now we have to return all that info for storage
                    clean_tabs(driver)
                    return temp_case_record
                except:
                    print('\nSomething went wrong while "printing".')
                    clean_tabs(driver)
                    return None
        except:
            print('\nDid not get case in search results.')
            clean_tabs(driver)
            return None
    except:
        print('\nCould not search.')
        clean_tabs(driver)
        return None

# Quick helper for blank cells in the Docket section                           
def fix_blanks(text):
    if text == '\xa0':
        return ''
    else:
        return text

# Quick helper for closing extra browser tabs
def clean_tabs(driver):
    main_tab = driver.window_handles[0]
    for handle in driver.window_handles[1:]:
        try:
            driver.switch_to.window(handle)
            driver.close()
        except:
            pass
    driver.switch_to.window(main_tab)

def bulk_scrape(driver, year, code, start, end, pause, jitter, jitter_time, wait_time,):

    results = {}

    for cur_case_num in tqdm(range(start,end), desc='Bulk Scraping Cases...', colour='green'):
    
        returned_results = scrape_record(driver, year, code, cur_case_num, wait_time)

        if returned_results != None:
            results[f'{year} {code} {str(cur_case_num).zfill(6)}'] = returned_results

        pt = pause_time
        if jitter:
            pt += random.uniform(0.25,jitter_time)
        print(f'Sleeping for {pt} seconds in between cases...')
        time.sleep(pt)

    return results

# Called to scrape a single record without setting up any init factors etc. Mostly used for testing.
def single_scrape(case_year=1998, case_code='CVI', case_num=3001, web_driver_wait_time=10, headless=False):

    # Set up for using with Chrome
    op = webdriver.ChromeOptions()
    if headless :
        op.add_argument('headless')
    web_driver = webdriver.Chrome(service = Service(ChromeDriverManager().install()), options = op) 

    # Run the single scrape
    results = scrape_record(web_driver, case_year, case_code, case_num, web_driver_wait_time)

    if results != None:
        # Pretty Print those results
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(results)

    return results

if __name__ == '__main__':

    # Set up dictionary to hold data
    case_records = {}
    
    chrome_options = Options()


    cur_dir = os.path.dirname(__file__)

    # Handle arguments if we don't want to use the defaults
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_file', type=str, required=False)
    parser.add_argument('--case_year', type=int, required=False)
    parser.add_argument('--case_code', type=str, required=False)
    parser.add_argument('--range_start', type=int, required=False)
    parser.add_argument('--range_end', type=int, required=False)
    parser.add_argument('--pause_time', type=int, required=False)
    parser.add_argument('--jitter', type=bool, required=False)
    parser.add_argument('--jitter_time', type=float, required=False)
    parser.add_argument('--web_driver_wait_time', type=int, required=False)
    parser.add_argument('--headless', type=bool, required=False)
    parser.add_argument('--results_dir', type=str, required=False)
    args = parser.parse_args()

    # If there is an argument supplied for an option, use that, otherwise use defaults from file
    if args.data_file is not None:
        with open(args.data_file, 'r') as d_file: 
            default_data = json.load(d_file)
    else:
        with open('defaults.json', 'r') as d_file: 
            default_data = json.load(d_file)
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
    # Sets how many max seconds for the jitter.
    if args.jitter_time is not None:
        jitter_time = args.jitter_time
    else:
        jitter_time = default_data['jitter_time']
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

    # Bulk Scrape, to get a big dictionary of all the results
    results = bulk_scrape(web_driver, case_year, case_code, range_start, range_end, pause_time, jitter, jitter_time, web_driver_wait_time)

    # Put those results in a file
    results_json = json.dumps(results)
    results_path = f'results/{case_year}_{case_code}_{str(range_start).zfill(6)}-{str(range_end).zfill(6)}.json'
    full_file_path = os.path.join(cur_dir, results_path)
    with open(full_file_path, 'w') as write_file:
        write_file.write(results_json)

    # Print a happy success message
    print(f'Wrote the available cases from case number {case_year} {case_code} {str(range_start).zfill(6)} to {case_year} {case_code} {str(range_end).zfill(6)}')

    # Quit the driver
    web_driver.quit()