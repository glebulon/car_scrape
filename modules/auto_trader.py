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



# a=driver.find_element_by_name("makeCode")
# "modelCode"
# for make in makes:
#     dropdown = driver.find_element_by_name("makeCode")
#     dropdown.find_element(By.XPATH, "//option[. = '{}']".format(make)).click()
#     dropdown2 = driver.find_element_by_name("modelCode")
#     modelselections = Select(dropdown2)
#     cars[make] = [x.text for x in modelselections.options]

# d = Select(dropdown)
# d.select_by_visible_text("BMW")

# z = driver.find_element_by_name("zipcode")
# z.click()
# z.clear()
# z.send_keys("02135")

# driver.find_element_by_id("search").click()

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
    
        
    if make:
        with open('car_makes.json') as f:
            makes = json.load(f)
        make_code = makes[make]

        url = "https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action?zip={0}" \
              "&showNegotiable=true&sortDir=ASC&sourceContext=carGurusHomePageModel&distance={1}&sortType=DEAL_SCORE&" \
              "entitySelectingHelper.selectedEntity={2}".format(zip, distance, make_code)

    if not make and not model and not dealer_url:
        url = "https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action?zip={0}" \
              "&showNegotiable=true&sortDir=ASC&sourceContext=carGurusHomePageModel&distance={1}&sortType=DEAL_SCORE" \
              .format(zip, distance)

    # load page
    driver.get(url)
    # wait to load
    wait_to_load(driver)
    wait_for_listing(driver)
    # select years if provided
    if not dealer_url:
        # if (start or end) and model:
        if (start or end):
            year_range(start, end, driver)
        # select deal if option passed
        if deal_quality:
            good_price_only(driver, deal_quality)
        # uncheck cars with no price, don't want those
        remove_no_price(driver)
        # remove CPO only cars
        remove_cpo(driver)
        # remove delivery cars
        hide_delivery(driver)
    # create a list of cars
    cars = []
    page = 1
    # get all possible trims of a given car
    trims = get_trims(driver)
    colors = get_colors(driver)
    wait_to_load(driver)
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
    try:
        colors = driver.find_element_by_xpath("//*[@data-cg-ft='filters-panel-filter-color']")
        colors = colors.find_elements_by_xpath(".//ul/li")
        color_list = [x.text.split('(')[0] for x in colors]
        return color_list
    except Exception:
        return ["-"]
