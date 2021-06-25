import os
import sys
from datetime import datetime
from tkinter import Tk
from tkinter.filedialog import askopenfilename

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

PHREESIA_USERNAME = os.environ.get('PHREESIA_USERNAME')
PHREESIA_PASSWORD = os.environ.get('PHREESIA_PASSWORD')

timeout = 50

Tk().withdraw()
mrn_file = askopenfilename()
source = open(mrn_file)

log_path = mrn_file.split('.')
log_path = log_path[0] + '_log.txt'
log = open(log_path, 'a')

now = datetime.now()
now = now.strftime('%m/%d/%y %H:%M')

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument("--log-level=3") 
driver = webdriver.Chrome(executable_path="H:\chromedriver", options=options)


def hover_over(element):
    hover = ActionChains(driver).move_to_element(element)
    hover.perform()


class LoggingPrinter:
    def __init__(self, filename):
        self.out_file = open(filename, "w")
        self.old_stdout = sys.stdout
        sys.stdout = self

    def write(self, text): 
        self.old_stdout.write(text)
        self.out_file.write(text)

    def __enter__(self): 
        return self

    def __exit__(self, type, value, traceback): 
        sys.stdout = self.old_stdout


with LoggingPrinter(log_path):

    print("""\
     _____  _                        _                     _     _                     ______ _               
    |  __ \| |                      (_)           /\      | |   | |                   |  ____(_)              
    | |__) | |__  _ __ ___  ___  ___ _  __ _     /  \   __| | __| |_ __ ___  ___ ___  | |__   ___  _____ _ __ 
    |  ___/| '_ \| '__/ _ \/ _ \/ __| |/ _` |   / /\ \ / _` |/ _` | '__/ _ \/ __/ __| |  __| | \ \/ / _ \ '__|
    | |    | | | | | |  __/  __/\__ \ | (_| |  / ____ \ (_| | (_| | | |  __/\__ \__ \ | |    | |>  <  __/ |   
    |_|    |_| |_|_|  \___|\___||___/_|\__,_| /_/    \_\__,_|\__,_|_|  \___||___/___/ |_|    |_/_/\_\___|_|   
                                                                                                                                                                                                                        

                        """)

    print(now, 'Starting Log...')
    print('Logging here: ' + log_path)

    print('Launching Chrome in headless mode...')
    driver.get("https://login.phreesia.net/")

    print('Logging into Phreesia...')
    username = driver.find_element_by_id("Username")
    password = driver.find_element_by_id("Password")

    username.clear()
    password.clear()

    username.send_keys(PHREESIA_USERNAME)
    password.send_keys(PHREESIA_PASSWORD)

    driver.find_element_by_id("submit").click()

    padded_mrn_list = []
    missing_mrns = []
    cleared_mrns = set()
    no_clear_mrns = set()

    for short_mrn in source:
        x = str(short_mrn).strip('\n').rjust(10, '0')
        padded_mrn_list.append(x)

    report_tab = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "reportsAndSettingsTab"))
            )

    hover_over(report_tab)

    pt_search_link = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Patients"))
            )

    pt_search_link.click()

    print('Starting patient search...')
    print('--------------------')

    for i in padded_mrn_list:
        # Will get a stale element error if these are not reset at each iteration. 
        pt_name = None
        edit = None
        mrn_search_box = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "tbChart"))
            )
        mrn_search_box.clear()
        mrn_search_box.send_keys(i)
        
        try:
            pt_name = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "patient_name_cell"))
                )
            pt_name.click()
            
            edit = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[7]/div[3]/div/div[3]/a"))
                )
            edit.click()

            pt_first_name = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, "qpRequired.Name_FirstName"))
                )
            pt_last_name = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, "qpRequired.Name_LastName"))
                ) 

            print ('Patient Name: ' + pt_first_name.get_attribute('value'), pt_last_name.get_attribute('value'))
            print ('MRN: ' + i)

            try:
                try:
                    pt_address_2 = WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.ID, 'qpPersonal.Contact.StreetAddress'))
                        )
                except Exception:
                    pt_address_2 = WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.ID, 'qiPersonal.Contact.StreetAddress'))
                        )

                try:    
                    pt_address_1 = driver.find_element_by_id('qpContact.Apt')
                except Exception:
                    pt_address_1 = driver.find_element_by_id('qiContact.Apt')

                pt_addy1 = pt_address_1.get_attribute('value')
                pt_addy2 = pt_address_2.get_attribute('value')

                print('Patient address line 1: ' + pt_addy1)
                print('Patient address line 2: ' + pt_addy2)

                if pt_addy1.strip().upper() == pt_addy2.strip().upper():
                    print('Patient address lines match!')
                    print('Clearing patient address line 1...')
                    pt_address_1.clear()
                    print('Patient address line 1 cleared!')
                    cleared_mrns.add(i)

                else:
                    print('Patient address lines do not match, did not clear address line 1.')
                    no_clear_mrns.add(i)

            except Exception:
                print('Patient address line 1 not found, nothing to clear.')
                no_clear_mrns.add(i)

            try:
                try:
                    billing_address_1 = driver.find_element_by_id('qiBilling.ResponsiblePartyApartmentNumber')
                except:
                    billing_address_1 = driver.find_element_by_id('qpBilling.ResponsiblePartyApartmentNumber')
                
                bill_addy1 = billing_address_1.get_attribute('value')

                print('Billing address line 1: '+ bill_addy1)

                try:
                    billing_address_2 = driver.find_element_by_id('qiBilling.ResponsiblePartyAddress')
                except Exception:
                    billing_address_2 = driver.find_element_by_id('qpBilling.ResponsiblePartyAddress')

                bill_addy2 = billing_address_2.get_attribute('value')

                print('Billing address line 2: '+ bill_addy2)

                if bill_addy1.strip().upper() == bill_addy2.strip().upper():
                    print('Billing address lines match!')
                    print('Clearing billing address line 1...')
                    billing_address_1.clear()
                    print('Billing address line 1 cleared!')         
                    cleared_mrns.add(i)
                else:
                    print('Billing address lines do not match, did not clear address line 1.')
                    no_clear_mrns.add(i)

            except Exception:
                print('Billing address line 1 not found, nothing to clear.')
                no_clear_mrns.add(i)
            
            save_button = driver.find_element_by_id('btnOk')
            save_button.click()
            
        except Exception:
            print('MRN not found in Phreesia: '+ i)
            missing_mrns.append(i)
        print('--------------------')

    for i in no_clear_mrns:
        if i in cleared_mrns:
            no_clear_mrns.remove(i)

    print('Finished', now, '\n')

    if cleared_mrns != set():
        print('These MRNs had address line 1 cleared in Phreesia:')
        for x in cleared_mrns:
            print(x)
        print('')

    if no_clear_mrns != set():
        print('These MRNs did not have matching address lines in Phreesia:')
        for x in no_clear_mrns:
            print(x)
        print('')

    if missing_mrns != []:
        print('These MRNs were not found in Phreesia:')
        for x in missing_mrns:
            print(x)
        print('')
    
    print('++++++++++++++++++++++++++++++++++++++++++++++++++')