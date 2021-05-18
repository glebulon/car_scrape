#!/usr/bin/python

import csv
import json
import os
import re
import time
from datetime import datetime

import pytz
from bs4 import BeautifulSoup
from fuzzysearch import find_near_matches
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# global vars
user_agent = r"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) \
    Chrome/68.0.3440.84 Safari/537.36"
options = webdriver.ChromeOptions()
options.headless = True
options.add_argument("--window-size=1920,1080")
options.add_argument(user_agent)
options.add_argument("--disable-gpu")
options.binary_location = r"C:\Program Files (x86)\Google\Chrome Beta\Application\chrome.exe"
chrome_driver_binary = r"D:\my documents\car_scrape\chromedriver.exe"
driver = webdriver.Chrome(chrome_driver_binary, chrome_options=options)


cars_com_url = "https://www.autotrader.com/cars-for-sale/all-cars/ferrari/458-italia/reading-ma-01867?dma=&searchRadius=0&\
       location=&marketExtension=off&isNewSearch=true&showAccelerateBanner=false&sortBy=relevance&numRecords=25"


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
        print("Timed out waiting for page to load")
    try:
        current_car_html = driver.page_source
        current_car_soup = BeautifulSoup(current_car_html, 'html.parser')
        # data model is follows
        # [year, make, model, transmission, price, drive, fuel, exterior color, interior, vin, dealership link ]
        current_car_info = []
        year_make_model = current_car_soup.find_all(class_="_2Nz9KW")[0].text
        # add year
        current_car_info.append(year_make_model.split()[0])
        # add make and model
        # do some searching and formatting
        nm_model = find_near_matches(model, year_make_model[5:].split(' - ')[0], max_l_dist=7, max_deletions=2,
                                     max_insertions=2)[0].matched
        full_model = (nm_model + ' ' + re.sub('.*' + nm_model, '', year_make_model[5:].split(' - ')[0], count=1,
                                              flags=0)).strip()
        make = year_make_model[5:].split('-')[0].split(full_model)[0].strip()
        current_car_info.append(make)
        current_car_info.append(full_model)
        # get all info available
        values = current_car_soup.find_all(class_="_5grpKY")
        fields = current_car_soup.find_all(class_="aHpS63")
        element = 0
        details = {}
        for i in fields:
            details[i.text.strip(':')] = values[element].text
            element += 1
        # add transmission
        current_car_info.append(checkAndGetKey(details, "Transmission"))
        # add price
        current_car_info.append(checkAndGetKey(details, "Dealer's Price"))
        # add drive
        current_car_info.append(checkAndGetKey(details, "Drivetrain"))
        # add fuel
        current_car_info.append(checkAndGetKey(details, "Fuel Type"))
        # add exterior
        current_car_info.append(checkAndGetKey(details, "Exterior Color"))
        # add interior
        current_car_info.append(checkAndGetKey(details, "Interior Color"))
        # add vin
        current_car_info.append(checkAndGetKey(details, "VIN"))
        # add dealer link
        current_car_info.append(current_car_soup.find_all(class_="_4ipBMn")[0].text)
        return current_car_info
    except Exception as e:
        print(e)
        return ""

# load the page and waits for a specific element to be there
def cargurus_load_page(driver):
    timeout = 60
    # wait for the javascript to load
    try:
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.ID, "cargurus-listing-search")))
    except TimeoutException:
        print("Timed out waiting for page to load")

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
                print("Getting details for:", a['href'])
                car_details.append(cargurus_car_details(url, a['href'], model))
    car_details = [entry for entry in car_details if entry != '']
    return car_details


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
    while len(cargurus_cars) < number_of_listings and number_of_listings != 0:
        page += 1
        # load page
        driver.get(url + "#resultsPage=" + str(page))
        elements = cargurus_load_page(driver)
        # get new details and add all elements of the list into master list
        new_details = cargurus_get_details(elements, model, url)
        for x in new_details:
            cargurus_cars.append(x)
    return cargurus_cars


def date_stamp():
    EST = pytz.timezone('America/New_York')
    return(time.strftime('%Y-%m-%d--%I-%M-%p-'))


def write_to_csv(header="yes", file_name="", payload=None, source="cargurus"):

    with open(file_name + '.csv', 'a+', newline='') as file:
        writer = csv.writer(file, dialect='excel')
        if header == "yes":
            writer.writerow(["year", "make", "model", "transmission", "price", "drive", "fuel", "exterior color",
                             "interior", "vin", "dealership link", "carfax", "source"])
        for entry in payload:
            if entry != "":
                entry.append("")
                entry.append(source)
                writer.writerow(entry)


def remove_empty_lines(file):
    with open(file) as myFile:
        lines = myFile.readlines()
    with open(file, 'w', newline="") as myFile:
        myFile.writelines([item for item in lines if item != ''])


def main():
    cars = []
    file_name_stamp = date_stamp()
    file_name = file_name_stamp + "test"
    cars = cars + cargurus_cars(model="s-class", year="", zip="02062", distance="90",
                                number_of_listings=10)
    # write_to_csv(header="yes", payload=cars, file_name=file_name)
    cars = cars + cargurus_cars(model="c-class", year="", zip="02062", distance="90",
                                number_of_listings=10)
    cars = cars + cargurus_cars(model="corvette", year="", zip="01864", distance="30",
                                number_of_listings=10)
    driver.close()
    write_to_csv(header="yes", payload=cars, file_name=file_name)

if __name__ == "__main__":
    # execute only if run as a script
    main()
