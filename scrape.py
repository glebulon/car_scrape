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
logging.basicConfig(filename='run.log', encoding='utf-8', level=logging.INFO)
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

cars_com_url = "https://www.autotrader.com/cars-for-sale/all-cars/ferrari/458-italia/reading-ma-01867?dma=&searchRadius=0&\
       location=&marketExtension=off&isNewSearch=true&showAccelerateBanner=false&sortBy=relevance&numRecords=25"


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
            carfax_login()
    except Exception as e:
        print(e)
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


def cargurus_car_details(url, href, model):
    driver.get(url + href)
    timeout = 60
    try:
        # wait for details to load
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.CLASS_NAME, "_5PSqaB")))
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


# fetches car links and returns car information
def cargurus_get_details(elements, model, url):
    # find hrefs and get details of all cars
    car_details = []
    for element in elements:
        if ("Sponsored") in element.text:
            pass
        else:
            for a in element.find_all('a', href=True):
                car_details.append(cargurus_car_details(url, a['href'], model))
    car_details = [entry for entry in car_details if entry != '']
    return car_details


def cargurus_next_page_exists(driver):
    return "page-navigation-next-page" in driver.page_source


def cargurus_cars(model="camry", year="", zip="02062", distance="3", number_of_listings=0):
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
    # create a list of cars
    cargurus_cars = []
    page = 1
    elements = cargurus_load_page(driver)
    # find hrefs and get details of all cars
    new_details = cargurus_get_details(elements, model, url)
    # append details to our master list
    for x in new_details:
        cargurus_cars.append(x)

    # if number of listings loaded is less than desired check if there are more pages
    # this will not be granular, if you ask for 20 but there is 15 on the page
    # you'll load page 2, and can get 30 listings
    # go back before checking
    driver.get(url)
    while len(cargurus_cars) < number_of_listings and number_of_listings != 0 and cargurus_next_page_exists(driver):
        page += 1
        logging.info("Fetching more cars")
        logging.info(driver.page_source)
        # load page
        driver.get(url + "#resultsPage=" + str(page))
        elements = cargurus_load_page(driver)
        # get new details and add all elements of the list into master list
        new_details = cargurus_get_details(elements, model, url)
        for x in new_details:
            cargurus_cars.append(x)
        # load page
        driver.get(url + "#resultsPage=" + str(page))
    logging.info("Number of cars: {}".format(len(cargurus_cars)))
    return cargurus_cars


def date_stamp():
    EST = pytz.timezone('America/New_York')
    return(time.strftime('%Y-%m-%d--%I-%M-%p-'))


def write_to_csv(header="yes", file_name="", payload=None, source="cargurus"):
    with open(file_name + '.csv', 'a+', newline='') as file:
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


def main():
    # carfax_viewer("WDDUG8FB6EA054379") # no accident
    # carfax_viewer("JF1VA1B69G9819563") # 1 accident
    # carfax_viewer("JF1VA1J6XG8800589") # 6 accidents
    # carfax_viewer("JF1VA1A61J9839671") # title problem
    logging.info("Start: " + time.strftime('%Y-%m-%d--%I-%M-%S'))
    cars = []
    file_name_stamp = date_stamp()
    file_name = file_name_stamp + "test"
    # get the car listings
    cars = cars + cargurus_cars(model="impreza wrx", year="", zip="02062", distance="300",
                                number_of_listings=100)
    logging.info("Number of cars found: {}".format(len(cars)))
    # populate the carfax history
    cars = populate_carfax_info(cars)
    # close the window
    driver.close()
    # write to csv file
    write_to_csv(header="yes", payload=cars, file_name=file_name)
    logging.info("End: " + time.strftime('%Y-%m-%d--%I-%M-%S'))
if __name__ == "__main__":
    # execute only if run as a script
    main()
