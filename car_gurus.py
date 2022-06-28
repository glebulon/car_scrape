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
        WebDriverWait(driver, timeout).until(ec.visibility_of_element_located((By.XPATH, "//*[text()='Vehicle details']")))
        WebDriverWait(driver, timeout).until(ec.visibility_of_element_located((By.XPATH, "//*[text()='Vehicle history']")))
        # WebDriverWait(driver, timeout).until(ec.visibility_of_element_located((By.CLASS_NAME, "_mEDnu")))
        # WebDriverWait(driver, timeout).until(ec.visibility_of_element_located((By.CLASS_NAME, "v8gU2_")))
        # close banner if it's there
        banner_close(driver)
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
        year_make_model = current_car_soup.find_all(class_="tOvI3U")[0].text
        # add year
        current_car_info.append(year_make_model[:4])
        # add make/model
        make_model = year_make_model[5:].split(' - ')[0]
        current_car_info.append(make_model)
        # get all info available
        values = current_car_soup.find_all(class_="tSbcGe")
        fields = current_car_soup.find_all(class_="wv1MO3")
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

        # moon/sun
        moon = "no"
        if ("moonroof" in details['Major Options'].lower()) or ("sunroof" in details['Major Options'].lower()):
            moon = "yes"
        current_car_info.append(moon)
        # leather seats
        leather = "no"
        if "leather" in details['Major Options'].lower():
            leather = "yes"
        current_car_info.append(leather)
        # navigation
        navigation = "no"
        if "navigation" in details['Major Options'].lower():
            navigation = "yes"
        current_car_info.append(navigation)
        # add car link
        current_car_info.append("".join((url + href).split()))
        # dealer info
        try:
            dealer_info = current_car_soup.find("section", {"class": "_ruC5I _mEDnu"}).contents[0].text
        except Exception as e:
            dealer_info = "-"
        current_car_info.append(dealer_info)
        # dealer phone number
        try:
            phone = current_car_soup.find("a", {"class": "wHoz5o"})['href'].strip('tel:')
        except Exception as e:
            try:
                phone = current_car_soup.find_all(class_="_68Dk5")[0].text
            except Exception as e:
                phone = "-"
        current_car_info.append(phone)
        # leaving blank, vic wants the manager's name
        name = "-"
        current_car_info.append(name)
        try:
            # distance from zipcode
            distance_town = current_car_soup.find_all(class_="obQcJn")[0].text
            # town
            current_car_info.append(distance_town.split("·")[0].strip())
        except Exception as e:
            current_car_info.append("-")
        try:
            # distance
            current_car_info.append(distance_town.split("·")[1].strip())
        except Exception as e:
            current_car_info.append("-")
        # days on cargurus
        try:
            days = current_car_soup.find_all(class_="ksX2ni")[0].text
            if "days" not in days:
                days = current_car_soup.find_all(class_="BiX5ju")[0].text
            current_car_info.append(days)
        except Exception as e:
            current_car_info.append("-")
        # accidents from cargurus
        try:
            current_car_info.append(current_car_soup.find_all(class_="XMMcff")[1].text.strip("Accident Check").
                                    strip(" repor"))
            # title issues
            current_car_info.append(current_car_soup.find_all(class_="XMMcff")[0].text.strip("Title Check"))
        except Exception:
            current_car_info.append("-")
            current_car_info.append("-")
        # price versus market
        # store the element
        try:
            price_anal = current_car_soup.find(class_="fJS7pW").contents
        except Exception as e:
            print("url: {}".format(url + href))
            print(e)
            exc_type, exc_value, exc_tb = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_tb)
        try:
            # by how much
            current_car_info.append(price_anal[1].strip())
            # above or below
            current_car_info.append(price_anal[0].text)
        except Exception as e:
            try:
                current_car_info.append(str(price_anal.contents[1].strip()))
            except Exception as e:
                # append 2 spots
                current_car_info.append("-")
                current_car_info.append("-")
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
    timeout = 120
    # wait for the javascript to load
    try:
        WebDriverWait(driver, timeout).until(ec.visibility_of_element_located((By.ID, "cargurus-listing-search")))
    except TimeoutException:
        # print("Timed out waiting for page to load")
        pass
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    elements = soup.find_all("div", {"class": "lmXF4B c7jzqC A1f6zD"})
    # # try another class if can't get any info
    # if len(elements) == 0:
    #     elements = soup.find_all("div", {"class": "t9zEoM Xw8J6j"})
    # if len(elements) == 0:
    #     elements = soup.find_all("div", {"class": "_ajVSv WLAITe wcSLm2"})
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
    WebDriverWait(driver, 10).until(ec.visibility_of_element_located((By.CLASS_NAME, "ww9K1z")))
    time.sleep(5)

def wait_for_listing(driver):
    WebDriverWait(driver, 15).until(ec.visibility_of_element_located((By.CLASS_NAME, "IWo5PZ.orzDm5")))
    time.sleep(3)

def next_page(driver, first=True):
    if first:
        button_click('selector', '#cargurus-listing-search > div:nth-child(1) > div > div.AtkUbr >\
            div.lJPoT2.L_uQTe > div.KCJEd3._0ma0Q > div.YTDx_x.G_wJFb > button', driver)
    else:
        button_click('selector', '#cargurus-listing-search > div:nth-child(1) > div > div.AtkUbr >\
            div.lJPoT2.L_uQTe > div.KCJEd3._0ma0Q > div.YTDx_x.G_wJFb > button:nth-child(4) > span', driver)

# unclick the checkbox that shows cars with no price
def remove_no_price(driver):
    try:
        driver.find_element_by_xpath("//*[text()='{}']".format('Include Listings Without Available Pricing')).click()
    except Exception:
        print("Couldn't unclick cars with no price")

# close the stupid popup
def banner_close(driver):
    try:
        driver.find_element_by_xpath("//*[text()='{}']".format('No thanks')).click()
    except Exception:
        pass

# press the clear button for CPO/used/new
def remove_cpo(driver):
    # click the button for "Used"
    button_click("xpath", "//*[text()='{}']".format('Used'), driver)


# select good priced car only
def good_price_only(driver, deal):
    if deal == "fair":
        try:
            fair_deal = driver.find_element_by_xpath("//*[text()='{}']".format('Fair Deal'))
            good_deal = driver.find_element_by_xpath("//*[text()='{}']".format('Good Deal'))
            great_deal = driver.find_element_by_xpath("//*[text()='{}']".format('Great Deal'))
            fair_deal.click()
            good_deal.click()
            great_deal.click()
        except Exception:
            print("No fair deals found")
    if deal == "good":
        try:
            good_deal = driver.find_element_by_xpath("//*[text()='{}']".format('Good Deal'))
            great_deal = driver.find_element_by_xpath("//*[text()='{}']".format('Great Deal'))
            good_deal.click()
            great_deal.click()
        except Exception:
            print("No good deals found")
    if deal == "great":
        try:
            great_deal = driver.find_element_by_xpath("//*[text()='{}']".format('Great Deal'))
            great_deal.click
        except Exception:
            print("No great deals found")


# pull out mileage from element
def get_mileage(element):
    mileage = 0
    for i in element.find_all('p'):
        if re.search(r" mi$", str(i.text)):
            mileage = int(str(i.text).strip(' mi').replace(',', ''))
    # if mileage == 0:
    #     no_mileage = ""
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
    m.wait_for_page_to_load(driver, 90)


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
    # cargurus changed the way they show delivery
    button_click("xpath", "//*[text()='{}']".format("Nearby listings"), driver)


# select the year range
def year_range(start, end, driver):
    try:
        driver.find_element_by_css_selector("[aria-label='Select Minimum Year']").click()
        Select(driver.find_element_by_css_selector("[aria-label='Select Minimum Year']")).select_by_visible_text(str(start))
        driver.find_element_by_css_selector("[aria-label='Select Minimum Year']").click()
    except Exception:
        print("Couldn't find the start year")
    try:
        driver.find_element_by_css_selector("[aria-label='Select Maximum Year']").click()
        Select(driver.find_element_by_css_selector("[aria-label='Select Maximum Year']")).select_by_visible_text(str(end))
        driver.find_element_by_css_selector("[aria-label='Select Maximum Year']").click()
    except Exception:
        print("Couldn't find the end year")
    # driver.find_element_by_xpath("(//button[@type='submit'])[2]").click()


# remove anything that is sponsored, authorized or delivers or above mileage
def remove_auth_del_spon(raw_elements, mileage):
    # move to a new list all elements that do NOT contain:
    # Sponsored, Authorized.*Dealer, are not not empty and if mileage is provided filter on mileage
    elements = []
    for x in raw_elements:
        sponsored = re.search('Sponsored', x.text)
        transfer = re.search('store transfer', x.text)
        authorized = re.search('Authorized.*Dealer', x.text)
        not_sure = (x.select('#cargurus-listing-search > div:nth-child(1) > div > div.FwdiZf > \
                   div._5K96zi._3QziWR > div._3LnDeD > div:nth-child(6) > div > a > div._4yP575._2PDkfp > div > \
                   div._37Fr4g > div > svg') == [])
        has_miles = (x.text.lower() != '') and (get_mileage(x) != 0)
        less_miles_than_desired = ((not mileage) or (get_mileage(x) < mileage))
        if (not sponsored) and (not transfer) and (not authorized) and (not_sure) and (has_miles) and \
           (less_miles_than_desired):
            elements.append(x)
        else:
            print("removed car")
            print("sponsored: {}".format("sponsored"))
            print("transfer: {}".format(transfer))
            print("authorized: {}".format(authorized))
            print("not_sure: {}".format(not_sure))
            print("has_miles: {}".format(has_miles))
            print("miles: {}".format(get_mileage(x)))
            print("less_miles_than_desired: {}".format(less_miles_than_desired))
            print("*" * 30)
    return elements


# this is the main function, the entry point to the other ones for cargurus
def cars(driver, model="", make="", zip="02062", distance="3", number_of_listings=0, deal_quality="",
         start="", end="", mileage="", dealer_url=""):

    # this is supplied for a specific dealer
    if dealer_url:
        url = dealer_url

    # build cargurus url
    if model:
        # look up the code for the model of car
        with open('models_lower_case.json') as f:
            models = json.load(f)
        model_code = models[model]

        url = "https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action?zip={0}" \
              "&showNegotiable=true&sortDir=ASC&sourceContext=carGurusHomePageModel&distance={1}&sortType=DEAL_SCORE&" \
              "entitySelectingHelper.selectedEntity={2}".format(zip, distance, model_code)
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
    m.wait_for_page_to_load(driver, 90)
    # wait_for_listing(driver)
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
    m.wait_for_page_to_load(driver, 90)
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
        m.wait_for_page_to_load(driver, 90)
        print("Fetching more cars")
        # close banner if it's there
        banner_close(driver)
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
