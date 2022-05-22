#!/usr/bin/python3
import json
import logging
import re
import sys
import time
import traceback

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait

import modules.misc as m

def select_make_model(driver, _make_model, type):
    code = "makeCode" if type == "make" else "ModelCode"
    # wait until the dropdown is clickable
    WebDriverWait(driver, 5).until(ec.element_to_be_clickable((By.NAME, code)))
    # select dropdown
    _dropdown = driver.find_element_by_name(code)
    # open drowp down
    _dropdown.click()
    # click the car
    _dropdown.find_element(By.XPATH, "//option[. = '{}']".format(_make_model)).click()
    # click on the background
    # driver.find_element_by_xpath("//html").click()

def enter_zip_code(driver, zip):
    zip_code = driver.find_element_by_name("zipcode")
    zip_code.clear()
    time.sleep(1)
    zip_code.clear()
    zip_code.send_keys(zip)

def press_search(driver):
    # press search
    driver.find_element_by_xpath("//html").click()
    driver.find_element_by_id("search").click()

# enter the radius
def select_radius(driver, distance):
    radius = driver.find_element_by_name("searchRadius")
    radius.click()
    radius.find_element(By.XPATH, "//option[. = '{} Miles']".format(distance)).click()

def remove_delivery(driver):
    driver.find_element_by_xpath("//*[text()='{}']".format('Include Extended Home Delivery')).click()

# this is the main function, the entry point to the other ones for cargurus
def cars(driver, model="", make="", zip="02062", distance="3", number_of_listings=0, deal_quality="",
         start="", end="", mileage="", dealer_url=""):

    # get the list of cars and models available to search on autotrader
    with open('atrad_make_models.json') as f:
        makes_models = json.load(f)

    # if model is give use it to lookup the make
    if model:
        _make = [k for k, v in makes_models.items() if model.capitalize() in v][0]
        _model = model.capitalize()
    else:
        # capitalize the make, leave model blank
        _make = make.capitalize()
        _model = model

    # load page
    driver.get('https://autotrader.com')
    # wait to page to load, makes a js call/check
    m.wait_for_page_to_load(driver)

    if _make:
        select_make_model(driver, _make, "make")
    if _model:
        select_make_model(driver, _model, "model")
    
    enter_zip_code(driver, zip)
    press_search(driver)
    
    #select distance
    select_radius(driver, distance)
    # don't include home delivery
    remove_delivery(driver)
    
    # stopped here
    cars = []
    page = 1
    # get all possible trims of a given car
    trims = get_trims(driver)
    colors = get_colors(driver)
    m.wait_for_page_to_load(driver)
    wait_for_listing(driver)
    # get all cars on the page
    raw_elements = load_page(driver)
    print("Before filtering: {}".format(len(raw_elements)))
    if not dealer_url:
        # filter out all cars that are sponsored and are above mileage threshold
        elements = remove_auth_del_spon(raw_elements, mileage)
        # create a list of all cars from every page, then get details from all of them
        all_elements = elements
    else:
        all_elements = raw_elements
    print("After filtering: {}".format(len(all_elements)))

    # if either number of listing desired is zero(all of them) or if we got less than we need
    # and if next page exists
    while ((len(all_elements) < number_of_listings) or (number_of_listings == 0)) and next_page_exists(driver):
        # go to next page, different locators if page 1 or not
        if page == 1:
            next_page(driver, first=True)
        else:
            next_page(driver, first=False)
        page += 1
        wait_to_load(driver)
        wait_for_listing(driver)
        print("Fetching more cars")
        raw_elements = load_page(driver)
        print("Before filtering: {}".format(len(raw_elements)))
        if not dealer_url:
            elements = remove_auth_del_spon(raw_elements, mileage)
        else:
            elements = raw_elements
        print("After filtering: {}".format(len(elements)))
        for element in elements:
            all_elements.append(element)

    # remove all elements that are higher in number than requested number of cars
    if (len(all_elements) > number_of_listings) and (number_of_listings != 0):
        all_elements = all_elements[0:number_of_listings]

    # find hrefs and get details of all cars
    new_details = get_details(driver, all_elements, url)
    # append details to our master list
    for x in new_details:
        cars.append(x)

    # remove duplicate entries, not sure why they are there
    print("Before deduping: {}".format(len(cars)))
    deduped_cars = []
    for car in cars:
        if car not in deduped_cars:
            deduped_cars.append(car)
    print("After deduping: {}".format(len(deduped_cars)))
    # add trim if it exists for every car
    for car in deduped_cars:
        trim = [x for x in car[1].split() if x in trims]
        if trim:
            car.append(trim[0])
        else:
            car.append("-")

    # replace color with a more common name
    for car in deduped_cars:
        # only do this if a color is available
        if colors != ["-"]:
            # only replace the color if there is a  match, otherwise leave it the way it was
            color = [x for x in car[6].split() if x in colors]
            if color:
                car[6] = (color[0])

    logging.critical("Number of cars: {}".format(len(deduped_cars)))
    return deduped_cars

# get all the possible trims for this car
def get_trims(driver):
    try:
        trims = driver.find_element_by_xpath("//*[@data-cg-ft='filters-panel-filter-trim_name']")
        trims = trims.find_elements_by_xpath(".//ul/li")
        trim_list = [x.text.split('(')[0] for x in trims]
        return trim_list
    except Exception:
        return ["-"]

# get all the possible trims for this car
def get_colors(driver):
    # try:
    #     colors = driver.find_element_by_xpath("//*[text()='{}']".format('Exterior Color')).click()
    #     black = driver.find_element_by_xpath("//*[text()='{}']".format('Black'))
    #     color_list = [x.text.split('(')[0] for x in colors]
    #     return color_list
    # except Exception:
    return ["-"]
