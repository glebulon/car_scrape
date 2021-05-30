#!/usr/bin/python

import csv
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime

import pytz
from bs4 import BeautifulSoup
from retrying import retry
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
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
    try:
        driver.find_element_by_id('landing_signin_item-link').click()
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "username"))).send_keys(login['username'])
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "password"))).send_keys(login['password'])
        driver.find_element_by_id('login_button').click()
    except Exception as e:
        pass
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
        # dealership town, distance from zip, days on cargurus, accidents from cargurus, title from cargurus,
        # price vs market ]
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
        try:
            current_car_info.append(distance_town.split("·")[0].strip())
        except Exception as e:
            current_car_info.append("")
        try:
            current_car_info.append(distance_town.split("·")[1].strip())
        except Exception as e:
            current_car_info.append("")
        # days on cargurus
        try:
            current_car_info.append(current_car_soup.select('#cargurus-listing-search > div:nth-child(1) > div._36TanG > \
                div._24ffzL > div._5jSLnT > div._2Bszua._5PSqaB > div._5j5D2G > div:nth-child(1) > div._5kdMnf > \
                div:nth-child(2) > strong')[0].text)
        except Exception as e:
            current_car_info.append(current_car_soup.select('#cargurus-listing-search > div:nth-child(1) > \
            div._36TanG > div._24ffzL > div._5jSLnT > div._2Bszua._5PSqaB > div._5j5D2G > div:nth-child(1) > \
                div._5kdMnf > div._5XcXHD > strong')[0].text)
        # accidents from cargurus
        current_car_info.append(current_car_soup.find_all(class_="_5gudF3")[1].text)
        # title issues
        current_car_info.append(current_car_soup.find_all(class_="_5gudF3")[0].text)
        # price versus market
        # store the element
        price_anal = current_car_soup.select("#cargurus-listing-search > div:nth-child(1) > div._36TanG > \
        div._24ffzL > div._3Wnbei > section > div > div > section._2Xfg8g")[0]
        # above or below
        current_car_info.append(price_anal.contents[0].text)
        # by how much
        try:
            current_car_info.append(price_anal.contents[1].strip())
        except Exception as e:
            current_car_info.append(str(price_anal.contents[1].strip()))
        print(current_car_info)
        # return data
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
        # print("Timed out waiting for page to load")
        pass
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    elements = soup.find_all("div", {"class": "EUQoKn"})
    return elements


# fetches car links and returns car information, wrapper function
def cargurus_get_details(elements, url):
    # find hrefs and get details of all cars
    car_details = []
    for element in elements:
        for a in element.find_all('a', href=True):
            car_details.append(cargurus_car_details(url, a['href']))
    car_details = [entry for entry in car_details if entry != '']
    return car_details

def cargurus_next_page_exists(driver):
    return "page-navigation-next-page" in driver.page_source

def cargurus_wait_to_load():
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "_3K15rt")))
    time.sleep(3)

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
        cargurus_button_click("selector", "#cargurus-listing-search > div:nth-child(1) > div > div.FwdiZf > div._4VrDe1 \
        > div._3K15rt > div:nth-child(2) > fieldset:nth-child(13) > ul > li:nth-child(1) > label > p")
        cargurus_button_click("selector", "#cargurus-listing-search > div:nth-child(1) > div > div.FwdiZf > div._4VrDe1 > \
        div._3K15rt > div:nth-child(2) > fieldset:nth-child(13) > ul > li:nth-child(2) > label > p")
    if deal == "great":
        cargurus_button_click("selector", "#cargurus-listing-search > div:nth-child(1) > div > div.FwdiZf > div._4VrDe1 \
        > div._3K15rt > div:nth-child(2) > fieldset:nth-child(13) > ul > li:nth-child(1) > label > p")

# pull out mileage from element
def cargurus_get_mileage(element):
    mileage = 0
    for i in element.find_all('p'):
        if re.search(r" mi$", str(i.contents[0])):
            mileage = int(str(i.contents[0]).strip(' mi').replace(',', ''))
    return mileage


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

# click the detials tab, just in case the summary shows up
def cargurus_details_tab():
    try:
        cargurus_button_click('selector', '#cargurus-listing-search > div:nth-child(1) > div._36TanG > div._24ffzL > \
            div._5jSLnT > div:nth-child(4) > ul > li._46hqDA.ZGdsg6')
        cargurus_button_click('selector', '#cargurus-listing-search > div:nth-child(1) > div._36TanG > div._24ffzL > \
            div._5jSLnT > div:nth-child(4) > ul > li:nth-child(2)')
        cargurus_button_click('selector', '#cargurus-listing-search > div:nth-child(1) > div._36TanG > div._24ffzL > \
            div._5jSLnT > div:nth-child(4) > ul > li:nth-child(3)')
        cargurus_button_click('xpath', '/html/body/main/div[2]/div[1]/div[3]/div[2]/div[2]/div[2]/ul/li[3]')
    except Exception as e:
        pass

# select the year range
def cargurus_year_range(start, end):
    driver.find_element_by_name("selectedStartYear").click()
    Select(driver.find_element_by_name("selectedStartYear")).select_by_visible_text(str(start))
    driver.find_element_by_name("selectedStartYear").click()
    driver.find_element_by_name("selectedEndYear").click()
    Select(driver.find_element_by_name("selectedEndYear")).select_by_visible_text(str(end))
    driver.find_element_by_name("selectedEndYear").click()
    driver.find_element_by_xpath("(//button[@type='submit'])[2]").click()
# this is the main function, the entry point to the other ones for cargurus
def cargurus_cars(model="camry", year="", zip="02062", distance="3", number_of_listings=0, deal_quality="",
                  start="", end="", mileage=""):
    # look up the code for the model of car
    with open('models_lower_case.json') as f:
        models = json.load(f)
    model_code = models[model]
    # build cargurus url
    url = "https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action?zip={0}\
           &showNegotiable=true&sortDir=ASC&sourceContext=carGurusHomePageModel&distance={1}&sortType=DEAL_SCORE&\
           entitySelectingHelper.selectedEntity={2}".format(zip, distance, model_code)

    # load page
    driver.get(url)
    # wait to load
    cargurus_wait_to_load()
    # select years if provided
    if start or end:
        cargurus_year_range(start, end)
    # select deal if option passed
    if deal_quality:
        cargurus_good_price_only(deal_quality)
    # uncheck cars with no price, don't want those
    cargurus_remove_no_price()
    # create a list of cars
    cargurus_cars = []
    page = 1
    # get all cars on the page
    elements = cargurus_load_page(driver)
    # filter out all cars that are sponsored and are above mileage threshold
    for element in elements:
        if "Sponsored" in element.text:
            elements.remove(element)
        elif mileage and cargurus_get_mileage(element) > mileage:
            elements.remove(element)
    # find hrefs and get details of all cars
    new_details = cargurus_get_details(elements, url)
    # append details to our master list
    for x in new_details:
        cargurus_cars.append(x)

    # if number of listings loaded is less than desired and there are more pages then next page will be loaded
    # this will not be granular, if you ask for 20 but there is 15 on the page
    # you'll load page 2, and can get 30 listings

    # go back before to search results
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
        new_details = cargurus_get_details(elements, url)
        for x in new_details:
            cargurus_cars.append(x)
        # back to results
        cargurus_button_click('class_name', '_2aBVWp')
    # remove duplicate entries, not sure why they are there
    deduped_cars = []
    deduped_cars = [x for x in cargurus_cars if x not in deduped_cars]
    logging.critical("Number of cars: {}".format(len(deduped_cars)))
    return deduped_cars


def date_stamp():
    EST = pytz.timezone('America/New_York')
    return(time.strftime('%Y-%m-%d--%I-%M-%p'))


def write_to_csv(header="yes", file_name="", payload=None, source="cargurus"):
    with open(r'reports/' + file_name + '.csv', 'a+', newline='') as file:
        writer = csv.writer(file, dialect='excel')
        if header == "yes":
            writer.writerow(["year", "make/model", "transmission", "mileage", "price", "drive", "fuel",
                             "exterior color", "interior", "vin", "dealership link", "dealership town",
                             "distance from zip", "days of cargurus", "accidents({})".format(source),
                             "title({})".format(source), "below/above mk", "compare to mk", "accidents(carfax)",
                             "title problem(carfax)", "source"])
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
def search_settings_read():
    with open('settings/searches.json') as f:
        return(json.load(f))

def gen_unique():
    return str(uuid.uuid4()).split('-')[0]

def main():
    # get the car listings
    searches = search_settings_read()
    # itterate over all entries and run a full search for each
    for search in searches:
        file_name = date_stamp() if not search['model'] else date_stamp() + '-' + search['model'] + '-' + gen_unique()
        logging.critical("Start: " + file_name)
        logging.critical(search)
        # run search
        cars = []
        cars = cars + cargurus_cars(model=search['model'], year="", zip=search['zipcode'], distance=search['distance'],
                                    number_of_listings=search['number_of_listings'], start=search['start_year'],
                                    end=search['end_year'], mileage=search['mileage'],
                                    deal_quality=search['deal_quality'])
        # populate the carfax history
        cars = populate_carfax_info(cars)
        # write to csv file
        write_to_csv(header="yes", payload=cars, file_name=file_name)
        logging.critical("Cars found: {}".format(len(cars)))
        logging.critical("End: " + file_name)
    # close the window
    driver.close()
if __name__ == "__main__":
    # execute only if run as a script
    main()
