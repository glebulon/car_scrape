#!/usr/bin/python

import csv
import json
import logging
import os
import re
import time
from datetime import datetime

import pdfkit
import pytz
from bs4 import BeautifulSoup
from fuzzysearch import find_near_matches
from retrying import retry
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# constants
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', filename='run.log', encoding='utf-8',
                    level=logging.CRITICAL, datefmt='%Y-%m-%d %H:%M:%S')
user_agent = r"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) \
    Chrome/68.0.3440.84 Safari/537.36"
options = webdriver.ChromeOptions()
options.headless = False
options.add_argument("--window-size=1920,1080")
options.add_argument(user_agent)
options.add_argument("--disable-gpu")
options.binary_location = r"C:\Program Files (x86)\Google\Chrome Beta\Application\chrome.exe"
chrome_driver_binary = r"D:\my documents\car_scrape\chromedriver.exe"
driver = webdriver.Chrome(chrome_driver_binary, chrome_options=options)

def carfax_login():
    with open('carfax_creds.json') as f:
        login = json.load(f)
    driver.get("https://www.carfaxonline.com")
    driver.find_element_by_id('landing_signin_item-link').click()
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "username"))).send_keys(login['username'])
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "password"))).send_keys(login['password'])
    driver.find_element_by_id('login_button').click()
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "account_menu_item-link")))


@retry(stop_max_attempt_number=5)
def carfax_viewer(vin):
    driver.get("https://www.carfaxonline.com/vhrs/{}".format(vin))
    # wait to load in here
    try:
        if not WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "cfxHdrBar"))):
            logging.error(driver.page_source)
    except Exception as e:
        carfax_login()
        driver.get("https://www.carfaxonline.com/vhrs/{}".format(vin))
    soup = BeautifulSoup(driver.page_source, "lxml")
    # get the columns we need
    sources = soup.find_all(class_="source-line")
    # find all occurences of damage
    damage = 0
    for i in sources:
        if i.find_all(string=re.compile("Damage Report")) != []:
            damage += 1
    # find title problems
    title_problem = "yes" if len(soup.findAll('tr', {'id': "nonDamageBrandedTitleRowTableRow"})) != 0 else "no"
    return([damage, title_problem])

def checkAndGetKey(dict, key):
    if key in dict.keys():
        return dict[key]
    else:
        return ""


# get information about a specific car
def cargurus_car_details(url, href):
    driver.get(url + href)
    timeout = 60
    try:
        # wait for details to load
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.CLASS_NAME, "_5PSqaB")))
        # click the details tab
        cargurus_details_tab()
    except TimeoutException:
        # print("Timed out waiting for page to load")
        pass
    try:
        current_car_html = driver.page_source
        current_car_soup = BeautifulSoup(current_car_html, 'html.parser')
        # data model is follows
        # [year, make-model, transmission, mileage, price, drive, fuel, exterior color, interior, vin, dealership link,
        # dealership town, distance from zip ]
        current_car_info = []
        year_make_model = current_car_soup.find_all(class_="_2Nz9KW")[0].text
        # add year
        current_car_info.append(year_make_model[:4])
        # add make/model
        make_model = year_make_model[5:].split(' - ')[0]
        current_car_info.append(make_model)
        # get all info available
        values = current_car_soup.find_all(class_="_5grpKY")
        fields = current_car_soup.find_all(class_="aHpS63")
        element = 0
        details = {}
        for i in fields:
            details[i.text.strip(':')] = values[element].text
            element += 1
        # list of info that we need
        elements_list = ["Transmission", "Mileage", "Dealer's Price", "Drivetrain", "Fuel Type", "Exterior Color",
                         "Interior Color", "VIN"]
        # pull out info for each and append
        for e in elements_list:
            current_car_info.append(checkAndGetKey(details, e))
        # add dealer link
        current_car_info.append(current_car_soup.find_all(class_="_4ipBMn")[0].text)
        # distance from zipcode
        distance_town = current_car_soup.find_all(class_="_3CFFR5")[0].text
        current_car_info.append(distance_town.split("·")[0].strip())
        current_car_info.append(distance_town.split("·")[1].strip())
        print(current_car_info)
        # return data
        return current_car_info
    except Exception as e:
        # print(e)
        return ""

# load the page and waits for a specific element to be there
def cargurus_load_page(driver):
    timeout = 60
    # wait for the javascript to load
    try:
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.ID, "cargurus-listing-search")))
    except TimeoutException:
        # print("Timed out waiting for page to load")
        pass
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    elements = soup.find_all("div", {"class": "EUQoKn"})
    return elements


# fetches car links and returns car information, wrapper function
def cargurus_get_details(elements, model, url):
    # find hrefs and get details of all cars
    car_details = []
    for element in elements:
        if ("Sponsored") in element.text:
            pass
        else:
            for a in element.find_all('a', href=True):
                car_details.append(cargurus_car_details(url, a['href']))
    car_details = [entry for entry in car_details if entry != '']
    return car_details

def cargurus_next_page_exists(driver):
    return "page-navigation-next-page" in driver.page_source

def cargurus_wait_to_load():
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "_3K15rt")))

def cargurus_next_page(first=True):
    if first:
        cargurus_button_click('selector', '#cargurus-listing-search > div:nth-child(1) > div > div.FwdiZf >\
            div._5K96zi._3QziWR > div.UiqxWZ._2nqerW > div.VXnaDS._55Yy37 > button')
    else:
        cargurus_button_click('selector', '#cargurus-listing-search > div:nth-child(1) > div > div.FwdiZf >\
            div._5K96zi._3QziWR > div.UiqxWZ._2nqerW > div.VXnaDS._55Yy37 > button:nth-child(4)')

# unclick the checkbox that shows cars with no price
def cargurus_remove_no_price():
    cargurus_button_click("css", "div > .XHYfqj > .\\_2dnSXG")

# select good priced car only
def cargurus_good_price_only(deal):
    if deal == "good":
        cargurus_button_click("css", ".\\_5pN1ma:nth-child(12) li:nth-child(2) .\\_2dnSXG")
    if deal == "great":
        cargurus_button_click("css", ".\\_5pN1ma:nth-child(13) li:nth-child(1) .\_2dnSXG")

def cargurus_button_click(type, identifier):
    try:
        if type == "class_name":
            driver.find_element_by_class_name(identifier).click()
        if type == "xpath":
            driver.find_element_by_xpath(identifier).click()
        if type == "selector":
            driver.find_element_by_css_selector(identifier).click()
        if type == "css":
            driver.find_element(By.CSS_SELECTOR, identifier).click()
    except Exception as e:
        logging.error(e)
    cargurus_wait_to_load()

def cargurus_details_tab():
    logging.critical("Clicking the details tab")
    try:
        cargurus_button_click('selector', '#cargurus-listing-search > div:nth-child(1) > div._36TanG > div._24ffzL > \
            div._5jSLnT > div:nth-child(4) > ul > li._46hqDA.ZGdsg6')
        cargurus_button_click('selector', '#cargurus-listing-search > div:nth-child(1) > div._36TanG > div._24ffzL > \
            div._5jSLnT > div:nth-child(4) > ul > li:nth-child(2)')
    except Exception as e:
        pass


def cargurus_cars(model="camry", year="", zip="02062", distance="3", number_of_listings=0, deal_quality=""):
    # look up the code for the model of car
    f = open('models_lower_case.json',)
    models = json.load(f)
    model_code = models[model]
    # Closing file
    f.close()
    # build cargurus url
    url = "https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action?zip={0}\
           &showNegotiable=true&sortDir=ASC&sourceContext=carGurusHomePageModel&distance={1}&sortType=DEAL_SCORE&\
           entitySelectingHelper.selectedEntity={2}".format(zip, distance, model_code)

    # load page
    driver.get(url)
    # wait to load
    cargurus_wait_to_load()
    # select deal if option passed
    if deal_quality != "":
        cargurus_good_price_only(deal_quality)
    # uncheck cars with no price, don't want those
    cargurus_remove_no_price()
    # create a list of cars
    cargurus_cars = []
    page = 1
    elements = cargurus_load_page(driver)
    # find hrefs and get details of all cars
    new_details = cargurus_get_details(elements, model, url)
    # append details to our master list
    for x in new_details:
        cargurus_cars.append(x)

    # if number of listings loaded is less than desired and there are more pages then next page will be loaded
    # this will not be granular, if you ask for 20 but there is 15 on the page
    # you'll load page 2, and can get 30 listings
    # go back before checking
    cargurus_button_click('class_name', '_2aBVWp')
    while len(cargurus_cars) < number_of_listings and number_of_listings != 0 and cargurus_next_page_exists(driver):
        # go to next page, different locators if page 1 or not
        if page == 1:
            cargurus_next_page(first=True)
        else:
            cargurus_next_page(first=False)
        page += 1
        logging.critical("Fetching more cars")
        elements = cargurus_load_page(driver)
        # get new details and add all elements of the list into master list
        new_details = cargurus_get_details(elements, model, url)
        for x in new_details:
            cargurus_cars.append(x)
        # back to results
        cargurus_button_click('class_name', '_2aBVWp')
    logging.critical("Number of cars: {}".format(len(cargurus_cars)))
    return cargurus_cars


def date_stamp():
    EST = pytz.timezone('America/New_York')
    return(time.strftime('%Y-%m-%d--%I-%M-%p'))


def write_to_csv(header="yes", file_name="", payload=None, source="cargurus"):
    with open(r'reports/' + file_name + '.csv', 'a+', newline='') as file:
        writer = csv.writer(file, dialect='excel')
        if header == "yes":
            writer.writerow(["year", "make/model", "transmission", "mileage", "price", "drive", "fuel",
                             "exterior color", "interior", "vin", "dealership link", "dealership town",
                             "distance from zip", "accidents", "title problem", "source"])
        for entry in payload:
            if entry != "":
                entry.append(source)
                writer.writerow(entry)


def remove_empty_lines(file):
    with open(file) as myFile:
        lines = myFile.readlines()
    with open(file, 'w', newline="") as myFile:
        myFile.writelines([item for item in lines if item != ''])


def populate_carfax_info(cars):
    carfax_login()
    for car in cars:
        results = carfax_viewer(car[9])
        car.append(results[0])
        car.append(results[1])
    return cars

# read in search
def search_read():
    with open('settings/searches.json') as f:
        return(json.load(f))

def main():
    logging.critical("Start")
    cars = []
    # get the car listings
    criteria = search_read()
    # output file name, add suffix if exists
    file_name = date_stamp() if not criteria[0]['file_suffix'] else date_stamp() + '-' + criteria[0]['file_suffix']
    # run search
    for c in criteria:
        cars = cars + cargurus_cars(model=c['model'], year="", zip=c['zipcode'], distance=c['distance'],
                                    number_of_listings=c['number_of_listings'], deal_quality=c['deal_quality'])

    # cars = cars + cargurus_cars(model="wrx", year="", zip="01602", distance="10",
    #                             number_of_listings=50)
    logging.critical("Number of cars found: {}".format(len(cars)))
    # populate the carfax history
    cars = populate_carfax_info(cars)
    # close the window
    driver.close()
    # write to csv file
    write_to_csv(header="yes", payload=cars, file_name=file_name)
    logging.critical("Cars found: {}".format(len(cars)))
    logging.critical("End")
if __name__ == "__main__":
    # execute only if run as a script
    main()
