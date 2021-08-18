#!/usr/bin/python3

from pathlib import Path
import traceback
import logging
import json
import re
from bs4 import BeautifulSoup
from retrying import retry
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait

import modules.constants as const


@retry(stop_max_attempt_number=5)
def carfax_viewer(vin, driver):
    driver = driver
    driver.get("https://www.carfaxonline.com/vhrs/{}".format(vin))
    # wait to load in here
    try:
        if not WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.ID, "cfxHdrBar"))):
            logging.error(driver.page_source)
    except Exception as e:
        # driver.save_screenshot("screenshots/cfax/{}.png".format(vin))
        carfax_login(driver)
        driver.get("https://www.carfaxonline.com/vhrs/{}".format(vin))
    soup = BeautifulSoup(driver.page_source, "lxml")
    # get the columns we need
    sources = soup.find_all(class_="source-line")
    fuel = soup.select('#headerFuel')[0].contents[0].strip() if soup.select('#headerFuel')[0].contents[0].strip() \
        else ''
    engine = soup.select('#headerEngineInfo')[0].contents[0].strip() if soup.select('#headerFuel')[0].contents[0].\
        strip() else ''
    drive = soup.select('#headerDriveline')[0].contents[0].strip() if soup.select('#headerDriveline')[0].contents[0].\
        strip() else ''
    # find all occurences of damage
    damage = 0
    for i in sources:
        if i.find_all(string=re.compile("Damage Report")) != []:
            damage += 1
    # find title problems
    title_problem = "yes" if len(soup.findAll('tr', {'id': "nonDamageBrandedTitleRowTableRow"})) != 0 else "no"
    return([damage, title_problem, fuel, engine, drive])

def carfax_mock():
    return([1, "no title issue carfax", "GAS", "V8", "4WD"])


def carfax_login(driver):
    with open(const.creds) as f:
        login = json.load(f)
    driver.get("https://www.carfaxonline.com")
    try:
        driver.find_element_by_id('landing_signin_item-link').click()
        WebDriverWait(driver, 5).until(ec.element_to_be_clickable((By.ID, "username"))).\
            send_keys(login['carfax']['username'])
        WebDriverWait(driver, 5).until(ec.element_to_be_clickable((By.ID, "password"))).\
            send_keys(login['carfax']['password'])
        driver.find_element_by_id('login_button').click()
    except Exception as e:
        pass
    WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.ID, "account_menu_item-link")))

def populate_carfax_info(cars, driver):
    for car in cars:
        # mock
        if not Path(const.creds).is_file():
            results = carfax_mock()
        else:
            results = carfax_viewer(car[8], driver)
        # append the results
        car.append(results[0])
        car.append(results[1])
        car.append(results[2])
        car.append(results[3])
        car.append(results[4])
    return cars
