#!/usr/bin/python3
import json
import logging
import re
import sys
import time
import traceback

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait

import modules.misc as m


def select_make_model(driver, elementid, _make):
    _find = driver.find_element_by_id(elementid)
    _select = Select(_find)
    for i in _select.options[1:]:
        # if not i.text.startswith("Any"):
        if _make == i.text.lower():
            _select.select_by_index(_select.options.index(i))
            break

def enter_zip_code(driver, zip):
    zip_code = driver.find_element_by_id("make-model-zip")
    zip_code.clear()
    zip_code.send_keys(zip)

def press_search(driver):
    # press search
    driver.find_element_by_xpath("//html").click()
    driver.find_element_by_class_name("sds-button").click()

def select_mileage(driver, mileage):
    # driver.refresh()
    # m.fancysleep(10)
    _find = driver.find_element_by_id("mileage-select")
    _select = Select(_find)
    for i in _select.options[1:]:
        # if not i.text.startswith("Any"):
        if mileage <= int(i.text.replace(',', '').split()[0]):
            _select.select_by_index(_select.options.index(i))
            break

def deal_select(driver, deal_quality):
    WebDriverWait(driver, 15).until(ec.visibility_of_element_located((By.ID, "deal_rating")))
    if deal_quality == "good":
        try:
            # select both good and great
            driver.find_element_by_id("price-badge-label-deal_rating_good").click()
            m.fancysleep(10)
            driver.find_element_by_id("price-badge-label-deal_rating_great").click()
        except Exception:
            print("Couldn't find good deals")
            pass
    elif deal_quality == "great":
        try:
            driver.find_element_by_id("price-badge-label-deal_rating_great").click()
        except Exception:
            print("Couldn't find great deals")

def select_dealer_only(driver):
    try:
        WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.ID, "trigger_seller_type")))
        m.fancysleep(10)
        driver.find_element_by_id('trigger_seller_type').click()
        sellers = driver.find_element_by_id('panel_seller_type')
        sellers = sellers.find_elements_by_class_name('sds-checkbox')
        for i in sellers:
            if "Dealership" in i.text:
                i.click()
    except Exception:
        print("Couldn't select dealers only")

def get_cars_on_page(driver):
    m.fancysleep(10)
    try:
        WebDriverWait(driver, 15).until(ec.visibility_of_element_located((By.CLASS_NAME, "vehicle-cards")))
        cars = driver.find_element_by_class_name("vehicle-cards")
        return(cars.find_elements_by_css_selector("[phx-hook='VehicleCard']"))
    except Exception as e:
        if "target frame detached" in e.msg:
            WebDriverWait(driver, 15).until(ec.visibility_of_element_located((By.CLASS_NAME, "vehicle-cards")))
            cars = driver.find_element_by_class_name("vehicle-cards")
            return(cars.find_elements_by_css_selector("[phx-hook='VehicleCard']"))
        else:
            print("Couldn't get cars")
            print(e)

# remove sponsored dealers or certified cars
def remove_auth_del_spon(driver, cars):
    # remove sponsores cars or authorized dealers
    for car in cars:
        if 'id=\"sponsored' in car.get_attribute('innerHTML').lower():
            cars.remove(car)
        elif car.find_elements_by_class_name("stock-type")[0].text != "Used":
            cars.remove(car)
    return cars

# check if there are more pages of listing
def next_page_exists(driver):
    exists = driver.find_elements_by_css_selector("[aria-label='Next page']")
    if len(exists) != 0:
        return True
    else:
        return False

def next_page(driver):
    try:
        driver.find_elements_by_css_selector("[aria-label='Next page']")[0].click()
    except Exception:
        print("couldn't go to the next page")

def return_prop_dict(driver, prop_element):
    # find all dt elements and get the text from each one
    # list of property names
    # [Exterior Color, Drivertrain, etc]
    prop_name = prop_element.find_elements_by_tag_name("dt")
    prop_name = [x.text for x in prop_name]
    prop = prop_element.find_elements_by_tag_name("dd")
    prop = [x.text for x in prop]
    # join listst and return
    prop_dict = {prop_name[i]: prop[i] for i in range(len(prop_name))}
    return prop_dict

def get_price(driver):
    price_section = driver.find_element_by_class_name('gallery-header')
    return(price_section.find_element_by_class_name('primary-price').text)

# popup from a car that has more features
def get_more_features(driver):
    more_features = []
    try:
        driver.find_element_by_xpath("//*[text()='View all features']").click()
        all_features_class = driver.find_elements_by_class_name("all-features-item")
        more_features = [x.text for x in all_features_class]
        # close popup
        popup = driver.find_element_by_id("allFeaturesModal")
        popup.find_element_by_tag_name('svg').click()
    except Exception:
        print("Couldn't get more features")
    return more_features

# get dealer information
def dealer_information(driver):
    dealer_info = {}
    try:
        dealer_section = driver.find_element_by_class_name("seller-info")
        dealer_info["name"] = dealer_section.find_element_by_class_name("seller-name").text
        dealer_info['address'] = dealer_section.find_element_by_class_name("dealer-address").text
        dealer_info['town'] = dealer_info['address'].split(",")[0].split()[-1]
    except Exception:
        print("Couldn't get dealer info")
    return dealer_info

def history_information(driver):
    history_info = {}
    try:
        history = driver.find_element_by_class_name("vehicle-history-section")
        history_info.update(return_prop_dict(driver, history))
    except Exception:
        print("Couldn't get history info")
    return history_info

# get the details of a specific car
def get_car_details(driver, href):
    driver.get(href)
    m.wait_for_page_to_load(driver)
    current_car_info = []
    year_make_model = driver.find_element_by_class_name("listing-title").text
    # add year
    current_car_info.append(year_make_model.split(' ')[0])
    # add make and model
    make_model = year_make_model.split(' ')[1::]
    current_car_info.append(" ".join(make_model))
    # basic information element, bunch of stuff inside here
    car_info = driver.find_elements_by_class_name("fancy-description-list")
    car_info_dict = {}
    # go through all elements and create a single dictionary of everything returned
    for i in car_info:
        car_info_dict.update(return_prop_dict(driver, i))
    # get the price
    price = get_price(driver)
    # more features list
    more_features = get_more_features(driver)
    # vehicle history, carfaxy info
    history_dict = history_information(driver)
    # dealer info
    dealer_dict = dealer_information(driver)
    # start populating information to return
    # [year, make-model, transmission, mileage, price, fuel, exterior color, interior, vin, moon/sun,
    # leather, navigation, car link, dealer info, dealership town, distance from zip, days on cargurus, accidents,
    # from cargurus, title from cargurus, price vs market ]
    car_details = []
    try:
        # year
        car_details.append(current_car_info[0])
        # make model
        car_details.append(current_car_info[1])
        # transmission
        car_details.append(car_info_dict['Transmission'])
        # mileage
        mileage = get_miles(car_info_dict['Mileage'])
        car_details.append(mileage)
        # price
        car_details.append(price)
        # fuel
        car_details.append(car_info_dict['Fuel type'])
        # exterior color
        car_details.append(car_info_dict['Exterior color'])
        # interior color
        car_details.append(car_info_dict['Interior color'])
        # vin
        car_details.append(car_info_dict['VIN'])
        # moonroof sunroof
        roof = "no"
        for i in more_features:
            if "moonroof" in i.lower() or "sunroof" in i.lower():
                roof = "yes"
        car_details.append(roof)
        # leather
        leather = "no"
        if car_info_dict.get("Seating"):
            if "Leather" in car_info_dict.get("Seating"):
                leather = "yes"
        car_details.append(leather)
        # navigation
        navigation = "no"
        for i in more_features:
            if "Navigation" in i:
                navigation = "yes"
        car_details.append(navigation)
        # link to car
        car_details.append(href)
        # dealer info
        car_details.append(dealer_dict.get('name'))
        # dealer phone
        car_details.append("-")
        car_details.append("-")
        # dealer town
        car_details.append("-")
        # distance from zip
        car_details.append("-")
        # days on market
        car_details.append("-")
        # accidents
        car_details.append("-")
        # title
        car_details.append("-")
        # price versus market
        car_details.append("-")
        car_details.append("-")
    except:
        traceback.print_exc()
        return [""]

    return car_details

# return the mileage as an int
def get_miles(miles):
    _miles = miles
    # _miles = _miles.strip(' mi.')
    _miles = _miles.replace('mi.', 'miles')
    # _miles = int(_miles)
    return _miles
    

# fetches car links and returns car information, wrapper function
def get_details(driver, hrefs):
    # find hrefs and get details of all cars
    car_details_list = []
    # hrefs = [car.find_element_by_tag_name("a").get_attribute("href") for car in cars]
    for href in hrefs:
        car_details_list.append(get_car_details(driver, href))
    car_details_list = [entry for entry in car_details_list if entry != '']
    return car_details_list

# get the best deals first
def best_deals_first(driver):
    try:
        WebDriverWait(driver, 15).until(ec.visibility_of_element_located((By.CLASS_NAME, "sort-form")))
        selection = driver.find_element_by_class_name("sort-form")
        Select(selection.find_element_by_class_name("sds-text-field")).select_by_visible_text("Best deal")
    except Exception:
        print("Couldn't sort by best deal first")

# this is the main function, the entry point to the other ones for cars.com
def cars(driver, model="", make="", zip="02062", distance="100", number_of_listings=0, deal_quality="",
         start="", end="", mileage="", dealer_url=""):

    # if model is given use it to lookup the make
    if model:
        _model = model
        # open the file with all makes and models and jsonify it
        with open("cars_make_models_lower_case.json") as mm_file:
            mm = mm_file.read()
        make_model = json.loads(mm)
        # get the make by matching the model
        _make = [k for k, v in make_model.items() if _model in v][0]
    else:
        # capitalize the make, leave model blank
        _make = make
        _model = False

    # load page
    driver.get('https://cars.com')
    # wait to page to load, makes a js call/check
    m.wait_for_page_to_load(driver)
    # select used cars only
    m.select_from_drop_down(driver, "make-model-search-stocktype", "Used cars")
    # select make
    select_make_model(driver, "makes", _make)
    # select model if provided
    if _model:
        select_make_model(driver, "models", _model)

    # select distance
    m.select_from_drop_down(driver, "make-model-maximum-distance", f"{str(distance)} miles")
    enter_zip_code(driver, zip)
    press_search(driver)
    # select max mileage
    select_mileage(driver, mileage)
    m.fancysleep(10)
    # select the year range
    m.select_from_drop_down(driver, "year_year_min_select", start)
    m.select_from_drop_down(driver, "year_year_max_select", end)
    # page reloads, wait to load
    m.fancysleep(10)
    cars = []
    hrefs = []
    page = 1
    # get all possible trims of a given car
    m.wait_for_page_to_load(driver)
    trims = get_trims(driver)
    colors = get_colors(driver)
    # select deal type
    deal_select(driver, deal_quality)
    # select dealer type
    select_dealer_only(driver)
    # best deals first
    best_deals_first(driver)
    # get all cars on the page
    cars_on_page = get_cars_on_page(driver)
    ###############
    print("Page: {}\n   Before filtering: {}".format(page, len(cars_on_page)))
    # z = cars_on_page[0].find_element_by_tag_name("a")
    # z.get_property("href")
    if not dealer_url:
        # filter out all cars that are sponsored and are above mileage threshold
        cars_after_filter = remove_auth_del_spon(driver, cars_on_page)
        # create a list of all cars from every page, then get details from all of them
        all_cars = cars_on_page
    else:
        all_cars = cars_on_page
    print("    After filtering: {}".format(len(all_cars)))
    new_hrefs = [car.find_element_by_tag_name("a").get_attribute("href") for car in cars]
    hrefs.extend(new_hrefs)
    # if either number of listing desired is zero(all of them) or if we got less than we need
    # and if next page exists
    while ((len(hrefs) < number_of_listings) or (number_of_listings == 0)) and next_page_exists(driver):
        print("Fetching more cars")
        # go to next page, different locators if page 1 or not
        next_page(driver)
        page += 1
        cars_on_page = get_cars_on_page(driver)
        print("Page: {}\n   Before filtering total: {}".format(page, len(cars_on_page)))
        if not dealer_url:
            cars_after_filter = remove_auth_del_spon(driver, cars_on_page)
            # extend adds elements of one list to another
            # append adds the whole list as a single element, end up with an element that itself is a list
            new_hrefs = [car.find_element_by_tag_name("a").get_attribute("href") for car in cars_after_filter]
            hrefs.extend(new_hrefs)
        else:
            new_hrefs = [car.find_element_by_tag_name("a").get_attribute("href") for car in cars_after_filter]
            hrefs.extend(new_hrefs)
        print("   After filtering total: {}".format(len(cars_after_filter)))

    print("Total: {}".format(len(hrefs)))

    # remove all elements that are higher in number than requested number of cars
    # if (len(all_cars) > number_of_listings) and (number_of_listings != 0):
    #     all_cars = all_cars[0:number_of_listings]

    # find hrefs and get details of all cars
    new_details = get_details(driver, hrefs)
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
        trims = trims = driver.find_element_by_id("trim")
        # remove the first element, that's the description
        trims = trims.text.split('\n')[1:]
        # create a list and add every element while removing the number of cars
        # list comprehension doesn't work with this
        trim_list = []
        for i in trims:
            trim_list.append(" ".join(i.split()[:-1]))
        return trim_list
    except Exception:
        return ["-"]

# get all the possible trims for this car
def get_colors(driver):
    try:
        WebDriverWait(driver, 15).until(ec.visibility_of_element_located((By.ID, "trigger_exterior_colors")))
        # open the colors
        driver.find_element_by_id("trigger_exterior_colors").click()
        # get all colors
        color_panel = driver.find_element_by_id("panel_exterior_colors")
        colors = color_panel.find_elements_by_class_name("sds-label")
        color_list = []
        for i in colors:
            color_list.append(" ".join(i.text.split()[:-1]))
        return color_list
    except Exception:
        return ["-"]
