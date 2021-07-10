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


# get information about a specific car
def car_details(url, href, driver):
    driver.get(url + href)
    timeout = 60
    try:
        # wait for details to load
        WebDriverWait(driver, timeout).until(ec.visibility_of_element_located((By.CLASS_NAME, "_5PSqaB")))
        # click the details tab
        details_tab(driver)
    except TimeoutException:
        # print("Timed out waiting for page to load")
        pass
    try:
        current_car_html = driver.page_source
        current_car_soup = BeautifulSoup(current_car_html, 'html.parser')
        # data model is follows
        # [year, make-model, transmission, mileage, price, fuel, exterior color, interior, vin, moon/sun,
        # leather, navigation, car link, dealer info, dealership town, distance from zip, days on cargurus, accidents,
        # from cargurus, title from cargurus, price vs market ]
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
        elements_list = ["Transmission", "Mileage", "Dealer's Price", "Fuel Type", "Exterior Color",
                         "Interior Color", "VIN"]
        # pull out info for each and append
        for e in elements_list:
            current_car_info.append(m.check_get_key(details, e))

        # get the major options of the car
        major_options = current_car_soup.find("dl", {"class": "_249mSX"})
        # moon/sun
        moon = "no"
        for i in major_options.contents:
            if "moonroof" in i.text.lower() or "sunroof" in i.text.lower():
                moon = "yes"
        current_car_info.append(moon)
        # leather seats
        leather = "no"
        for i in major_options.contents:
            if "leather" in i.text.lower():
                leather = "yes"
        current_car_info.append(leather)
        # navigation
        navigation = "no"
        for i in major_options.contents:
            if "navigation" in i.text.lower():
                navigation = "yes"
        current_car_info.append(navigation)
        # add car link
        current_car_info.append("".join((url + href).split()))
        # dealer info
        dealer_info = current_car_soup.select('#cargurus-listing-search > div:nth-child(1) > div._36TanG > \
        div._24ffzL > div._5jSLnT > section._2WWLMX._5PSqaB')
        try:
            dealer_info = [x.text for x in dealer_info[0].contents]
            dealer_info = "::".join(dealer_info)
        except Exception as e:
            dealer_info = "-"
        current_car_info.append(dealer_info)
        # dealer phone number
        try:
            phone = current_car_soup.find("div", {"class": "_3fXy3w"}).contents[0]
        except Exception as e:
            phone = "-"
        current_car_info.append(phone)
        # leaving blank, vic wants the manager's name
        name = "-"
        current_car_info.append(name)
        # distance from zipcode
        distance_town = current_car_soup.find_all(class_="_3CFFR5")[0].text
        try:
            current_car_info.append(distance_town.split("·")[0].strip())
        except Exception as e:
            current_car_info.append("-")
        try:
            current_car_info.append(distance_town.split("·")[1].strip())
        except Exception as e:
            current_car_info.append("-")
        # days on cargurus
        try:
            current_car_info.append(current_car_soup.select('#cargurus-listing-search > div:nth-child(1) > \
                div._36TanG > div._24ffzL > div._5jSLnT > div._2Bszua._5PSqaB > div._5j5D2G > div:nth-child(1) > \
                div._5kdMnf > div:nth-child(2) > strong')[0].text)
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
        try:
            price_anal = current_car_soup.select("#cargurus-listing-search > div:nth-child(1) > div._36TanG > \
            div._24ffzL > div._3Wnbei > section > div > div > section._2Xfg8g")[0]
        except Exception as e:
            print("url: {}".format(url + href))
            print(e)
            exc_type, exc_value, exc_tb = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_tb)
        try:
            # by how much
            current_car_info.append(price_anal.contents[0].text)
            # above or below
            current_car_info.append(price_anal.contents[1].strip())
        except Exception as e:
            try:
                current_car_info.append(str(price_anal.contents[1].strip()))
            except Exception as e:
                # append 2 spots
                current_car_info.append("-")
                current_car_info.append("-")
        print(current_car_info)
        # return data
        return current_car_info
    except Exception as e:
        print("url: {}".format(url + href))
        print(e)
        exc_type, exc_value, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_tb)
        return ""


# load the page and waits for a specific element to be there

def load_page(driver):
    timeout = 60
    # wait for the javascript to load
    try:
        WebDriverWait(driver, timeout).until(ec.visibility_of_element_located((By.ID, "cargurus-listing-search")))
    except TimeoutException:
        # print("Timed out waiting for page to load")
        pass
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    elements = soup.find_all("div", {"class": "EUQoKn"})
    return elements


# fetches car links and returns car information, wrapper function

def get_details(driver, elements, url):
    # find hrefs and get details of all cars
    car_details_list = []
    for element in elements:
        for a in element.find_all('a', href=True):
            car_details_list.append(car_details(url, a['href'], driver))
    car_details_list = [entry for entry in car_details_list if entry != '']
    return car_details_list


def next_page_exists(driver):
    return "page-navigation-next-page" in driver.page_source


def wait_to_load(driver):
    WebDriverWait(driver, 10).until(ec.visibility_of_element_located((By.CLASS_NAME, "_3K15rt")))
    time.sleep(3)


def next_page(driver, first=True):
    if first:
        button_click('selector', '#cargurus-listing-search > div:nth-child(1) > div > div.FwdiZf >\
            div._5K96zi._3QziWR > div.UiqxWZ._2nqerW > div.VXnaDS._55Yy37 > button', driver)
    else:
        button_click('selector', '#cargurus-listing-search > div:nth-child(1) > div > div.FwdiZf >\
            div._5K96zi._3QziWR > div.UiqxWZ._2nqerW > div.VXnaDS._55Yy37 > button:nth-child(4)', driver)


# unclick the checkbox that shows cars with no price
def remove_no_price(driver):
    driver.find_element_by_xpath("//*[text()='{}']".format('Include Listings Without Available Pricing')).click()


# press the clear button for CPO/used/new
def remove_cpo(driver):
    button_click("selector", "#cargurus-listing-search > div:nth-child(1) > div > div.FwdiZf > div._4VrDe1 > \
                                       div._3K15rt > div:nth-child(2) > fieldset:nth-child(13) > legend > button",
                 driver)
    button_click("css", ".mT6hMz", driver)


# select good priced car only
def good_price_only(driver, deal):
    if deal == "good":
        good_deal = driver.find_element_by_xpath("//*[text()='{}']".format('Good Deal'))
        great_deal = driver.find_element_by_xpath("//*[text()='{}']".format('Great Deal'))
        good_deal.click()
        great_deal.click()
    if deal == "great":
        great_deal = driver.find_element_by_xpath("//*[text()='{}']".format('Great Deal'))
        great_deal.click


# pull out mileage from element
def get_mileage(element):
    mileage = 0
    for i in element.find_all('p'):
        if re.search(r" mi$", str(i.contents[0])):
            mileage = int(str(i.contents[0]).strip(' mi').replace(',', ''))
    return mileage


def button_click(type, identifier, driver):
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
    wait_to_load(driver)


# click the detials tab, just in case the summary shows up
def details_tab(driver):
    try:
        button_click('selector', '#cargurus-listing-search > div:nth-child(1) > div._36TanG > div._24ffzL > \
            div._5jSLnT > div:nth-child(4) > ul > li._46hqDA.ZGdsg6', driver)
        button_click('selector', '#cargurus-listing-search > div:nth-child(1) > div._36TanG > div._24ffzL > \
            div._5jSLnT > div:nth-child(4) > ul > li:nth-child(2)', driver)
        button_click('selector', '#cargurus-listing-search > div:nth-child(1) > div._36TanG > div._24ffzL > \
            div._5jSLnT > div:nth-child(4) > ul > li:nth-child(3)', driver)
        button_click('xpath', '/html/body/main/div[2]/div[1]/div[3]/div[2]/div[2]/div[2]/ul/li[3]', driver)
    except Exception:
        pass


def hide_delivery(driver):
    button_click('selector', '#cargurus-listing-search > div:nth-child(1) > div > div.FwdiZf > div._4VrDe1 > \
    div._3K15rt > div:nth-child(2) > fieldset:nth-child(5) > label > p', driver)


# select the year range
def year_range(start, end, driver):
    driver.find_element_by_name("selectedStartYear").click()
    Select(driver.find_element_by_name("selectedStartYear")).select_by_visible_text(str(start))
    driver.find_element_by_name("selectedStartYear").click()
    driver.find_element_by_name("selectedEndYear").click()
    Select(driver.find_element_by_name("selectedEndYear")).select_by_visible_text(str(end))
    driver.find_element_by_name("selectedEndYear").click()
    driver.find_element_by_xpath("(//button[@type='submit'])[2]").click()


# remove anything that is sponsored, authorized or delivers or above mileage
def remove_auth_del_spon(raw_elements, mileage):
    # move to a new list all elements that do NOT contain:
    # Sponsored, Authorized.*Dealer, are not not empty and if mileage is provided filter on mileage
    elements = [x for x in raw_elements if (
                not re.search('Sponsored', x.text))
                and (not re.search('Authorized.*Dealer', x.text))
                and (x.select('#cargurus-listing-search > div:nth-child(1) > div > div.FwdiZf > \
                    div._5K96zi._3QziWR > div._3LnDeD > div:nth-child(6) > div > a > div._4yP575._2PDkfp > div > \
                    div._37Fr4g > div > svg') == [])
                and (x.text.lower() != '') and (get_mileage(x) != 0)
                and ((not mileage) or (get_mileage(x) < mileage))
                ]
    return elements


# this is the main function, the entry point to the other ones for cargurus
def cars(driver, model="", make="", zip="02062", distance="3", number_of_listings=0, deal_quality="",
         start="", end="", mileage=""):

    # build cargurus url
    if model:
        # look up the code for the model of car
        with open('models_lower_case.json') as f:
            models = json.load(f)
        model_code = models[model]

        url = "https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action?zip={0}\
            &showNegotiable=true&sortDir=ASC&sourceContext=carGurusHomePageModel&distance={1}&sortType=DEAL_SCORE&\
            entitySelectingHelper.selectedEntity={2}".format(zip, distance, model_code)
    if make:
        with open('car_makes.json') as f:
            makes = json.load(f)
        make_code = makes[make]

        url = "https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action?zip={0}\
            &showNegotiable=true&sortDir=ASC&sourceContext=carGurusHomePageModel&distance={1}&sortType=DEAL_SCORE&\
                entitySelectingHelper.selectedEntity={2}'".format(zip, distance, make_code)

    if not make and not model:
        url = "https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action?zip={0}\
            &showNegotiable=true&sortDir=ASC&sourceContext=carGurusHomePageModel&distance={1}&sortType=DEAL_SCORE"\
                .format(zip, distance)

    # load page
    driver.get(url)
    # wait to load
    wait_to_load(driver)
    # select years if provided
    try:
        if (start or end) and model:
            year_range(start, end, driver)
    except Exception:
        print(traceback.format_exc())
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
    # get all cars on the page
    raw_elements = load_page(driver)
    # filter out all cars that are sponsored and are above mileage threshold
    elements = remove_auth_del_spon(raw_elements, mileage)
    # create a list of all cars from every page, then get details from all of them
    all_elements = elements

    while (len(all_elements) < number_of_listings) and (number_of_listings != 0) and next_page_exists(driver):
        # go to next page, different locators if page 1 or not
        if page == 1:
            next_page(driver, first=True)
        else:
            next_page(driver, first=False)
        page += 1
        logging.critical("Fetching more cars")
        raw_elements = load_page(driver)
        elements = remove_auth_del_spon(raw_elements, mileage)
        for element in elements:
            all_elements.append(element)

    # remove all elements that are higher in number than requested number of cars
    if len(all_elements) > number_of_listings:
        all_elements = all_elements[0:number_of_listings]

    # find hrefs and get details of all cars
    new_details = get_details(driver, all_elements, url)
    # append details to our master list
    for x in new_details:
        cars.append(x)

    # remove duplicate entries, not sure why they are there
    deduped_cars = []
    for car in cars:
        if car not in deduped_cars:
            deduped_cars.append(car)

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
