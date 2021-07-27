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
import modules.constants as cons


# log in to the website, needs some work
def login(driver):
    driver.get("https://caroffer.pearlsolutions.com/?redirect=%2Fuser%2Flogin#/user/login")
    # wait for the box to show up
    WebDriverWait(driver, 10).until(ec.visibility_of_element_located((By.ID, "userName")))
    driver.find_element(By.ID, "userName").click()
    driver.find_element(By.ID, "userName").send_keys("xxx")
    driver.find_element(By.ID, "password").click()
    driver.find_element(By.ID, "password").send_keys("xxx")
    WebDriverWait(driver, 5).until(ec.visibility_of_element_located((By.CSS_SELECTOR, ".ant-btn")))
    driver.find_element(By.CSS_SELECTOR, ".ant-btn").click()
    # wait for the instant offer button to show up
    WebDriverWait(driver, 20).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="content"]/div/div/div/div[3]/\
        div[1]/div[2]/div[1]/div[2]/div[1]/div[2]/button')))


def find_click_element(driver, type="ID", element="", click=False):
    if type == "CSS_SELECTOR":
        element = driver.find_element(By.CSS_SELECTOR, element)
    elif type == "ID":
        element = driver.find_element(By.ID, ".ant-layout-sider-children")
    if click:
        element.click()

def get_color(color):
    # list of available colors
    caroffer_colors = ["Black", "Blue", "Brown", "Gold", "Gray", "Green", "Maroon", "Orange", "Purple", "Red",
                       "Silver", "Tan", "White", "Yellow"]
    caroffer_color = "Black"
    for i in caroffer_colors:
        if i.lower() in color.lower():
            caroffer_color = i
    return caroffer_color

def select_color(driver, color):
    colors = ["Black", "Blue", "Brown", "Gold", "Gray", "Green", "Maroon", "Orange", "Purple", "Red", "Silver", "Tan",
              "White", "Yellow"]
    selector = driver.find_element(By.CSS_SELECTOR, "div:nth-child(3) > .ant-select:nth-child(2) \
                                                    .ant-select-selection__placeholder")
    # if the color matches, use it, otherwise just pick black
    color = [x for x in colors if color.capitalize() == x]
    # if the list is empty add Black to it
    color = color or ["Black"]
    # pick the color
    selector.click()
    # might need to fogure this out
    WebDriverWait(driver, 20).until(ec.element_to_be_clickable((By.XPATH, '//*[text()="{}"]'.format(color[0]))))
    selector.find_element_by_xpath("//*[text()='{}']".format(color[0])).click()

def get_car_info(car):
    details = {}
    try:
        details['mileage'] = "".join(filter(str.isdigit, str(car[3].split()[0])))
        details['vin'] = car[8]
        details['year'] = car[0]
        details['make_model'] = car[1]
        details['trans'] = car[2]
        details['exterior'] = car[6]
        details['fuel'] = car[26]
        details['moonroof'] = car[9]
        details['leather'] = car[10]
        details['navigation'] = car[11]
        details['engine'] = car[27]
        details['drive'] = car[28]
        details['accidents'] = car[24]
        details['title_problem'] = car[25]
        details['color'] = get_color(car[6])

    except Exception as e:
        print(e)
        exc_type, exc_value, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_tb)
    return details

def enter_vin(driver, vin):
    xpath = '//*[@id="content"]/div/div/div/div[3]/div[1]/div[2]/div[1]/div[2]/div[1]/div[2]/button'
    try:
        # press the get offer button from hopmepage
        WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_element(By.XPATH, xpath).click()
    except Exception:
        print("Didn't press Get Instant Offer")
        print(traceback.format_exc())
    # wait for vin box
    WebDriverWait(driver, 15).until(ec.visibility_of_element_located((By.CSS_SELECTOR, ".ant-input-lg")))
    driver.find_element(By.CSS_SELECTOR, ".ant-input-lg").clear()
    driver.find_element(By.CSS_SELECTOR, ".ant-input-lg").send_keys(vin)
    driver.find_element(By.CSS_SELECTOR, ".goButton___wC2QZ").click()


def enter_mileage(driver, mileage):
    WebDriverWait(driver, 15).until(ec.visibility_of_element_located((By.ID, "tradeGradeMileage")))
    driver.find_element(By.ID, "tradeGradeMileage").click()
    driver.find_element(By.ID, "tradeGradeMileage").send_keys(mileage)

def has_leather(driver, leather):
    try:
        xpath = "/html/body/div[6]/div/div/div/div/div[2]/div/div[2]/div/div[8]/div/div[2]/div/div/div[1]/div/"
        xpath = xpath + "button[1]" if leather == "yes" else xpath + "button[2]"
        driver.find_element(By.XPATH, xpath).click()
    except Exception:
        xpath = "/html/body/div[7]/div/div/div/div/div[2]/div/div[2]/div/div[8]/div/div[2]/div/div/div[1]/div/"
        xpath = xpath + "button[1]" if leather == "yes" else xpath + "button[2]"
        driver.find_element(By.XPATH, xpath).click()

def has_moonroof(driver, moonroof):
    try:
        xpath = "/html/body/div[6]/div/div/div/div/div[2]/div/div[2]/div/div[8]/div/div[2]/div/div/div[2]/div/"
        xpath = xpath + "button[1]" if moonroof == "yes" else xpath + "button[2]"
        driver.find_element(By.XPATH, xpath).click()
    except Exception:
        xpath = "/html/body/div[7]/div/div/div/div/div[2]/div/div[2]/div/div[8]/div/div[2]/div/div/div[2]/div/"
        xpath = xpath + "button[1]" if moonroof == "yes" else xpath + "button[2]"
        driver.find_element(By.XPATH, xpath).click()

def has_navi(driver, navi):
    try:
        xpath = "/html/body/div[6]/div/div/div/div/div[2]/div/div[2]/div/div[8]/div/div[2]/div/div/div[3]/div/"
        xpath = xpath + "button[1]" if navi == "yes" else xpath + "button[2]"
        driver.find_element(By.XPATH, xpath).click()
    except Exception:
        xpath = "/html/body/div[7]/div/div/div/div/div[2]/div/div[2]/div/div[8]/div/div[2]/div/div/div[3]/div/"
        xpath = xpath + "button[1]" if navi == "yes" else xpath + "button[2]"
        driver.find_element(By.XPATH, xpath).click()

def press_vehicle_option(driver):
    driver.find_element(By.CSS_SELECTOR, "#optionsCard > button").click()
    WebDriverWait(driver, 10).until(ec.visibility_of_element_located((By.CSS_SELECTOR, "#trimsCard > h5")))

def next_condition(driver):
    next = driver.find_element_by_xpath("//*[text()='{}']".format('Next: Condition'))
    next.find_element_by_xpath("./..").click()

def certified_no(driver):
    WebDriverWait(driver, 20).until(ec.element_to_be_clickable((By.CSS_SELECTOR,
                                                               "#IS_CPO > div > button:nth-child(2)")))
    driver.find_element_by_css_selector("#IS_CPO > div > button:nth-child(2)").click()

def select_accidents(driver, accidents):
    selector_base = "#ACCIDENT > div > button:nth-child"
    if accidents >= 2:
        button = "(1)"
    elif accidents == 1:
        button = "(2)"
    else:
        button = None
    # select
    if button:
        WebDriverWait(driver, 20).until(ec.element_to_be_clickable((By.CSS_SELECTOR, selector_base + button)))
        driver.find_element_by_css_selector(selector_base + button).click()
        WebDriverWait(driver, 20).until(ec.element_to_be_clickable((By.CSS_SELECTOR, selector_base + button)))
        driver.find_element_by_css_selector(selector_base + button).click()

def get_offer_button(driver):
    try:
        driver.find_element_by_xpath('/html/body/div[6]/div/div/div/div/div[2]/div/div[1]/div[3]/div[2]/button').\
            click()
    except Exception:
        buttons = driver.find_elements_by_xpath('//*/button')
        for button in buttons:
            if "Get Offer" in button.text:
                button.click


def get_price(driver, vin):
    # close the offer dialog
    try:
        driver.find_element_by_class_name('ant-drawer-close').click()
    except Exception:
        pass
    driver.find_element_by_css_selector("div.filtersSearch___pA52_ > span > input").click()
    # clear text from field
    driver.find_element_by_css_selector("div.filtersSearch___pA52_ > span > input").clear()
    driver.find_element_by_css_selector("div.filtersSearch___pA52_ > span > input").send_keys(vin)
    try:
        selector = "div.offerAmount___ooWOd.highlighted___2pqMl"
        WebDriverWait(driver, 60).until(ec.visibility_of_element_located((By.CSS_SELECTOR, selector)))
        price = driver.find_element_by_css_selector(selector).text
    except Exception:
        price = "FAIL"
    return price

# if no engine is selected pick one
def fix_engine_tranny_drive(driver):
    etd = [["1", "Automatic"], ["2", "Liter"], ["3", "WD"]]
    for x in etd:
        selector = "//*[@id='kbbOptions']/div[{}]/div/div/div".format(x[0])
        element = driver.find_element_by_xpath(selector)
        if not element.text:
            # click the dropdown
            element.click()
            # this is a pita
            ul = driver.find_elements_by_tag_name("ul")
            for i in ul:
                if "{}".format(x[1]) in i.text:
                    i.click()

def flip_choice(choice):
    if choice == "no":
        return "yes"
    else:
        return "no"

# sun/navi doesn't match
def kbb_discrepancy_fix(driver, details):
    # check if the element exists
    try:
        disc = driver.find_element_by_css_selector("body > div:nth-child(38) > div > div > div > div > \
            div.ant-drawer-body > div > div.tradeWalkInfoContainer___2fgX- > div > div:nth-child(8) > div > \
                div.ant-collapse-content.ant-collapse-content-active > div > div > div.attentionContainer___f1u-P")
        options = ["LEATHER", "SUNROOF", "NAVIGATION"]
        # these need to be swapped
        flip = [x.lower() for x in options if x in disc.text]
        # there is a better way to do this
        if "sunroof" in flip:
            has_moonroof(driver, flip_choice(details['moonroof']))
        if "navigation" in flip:
            has_navi(driver, flip_choice(details['navigation']))
        if "leather" in flip:
            has_leather(driver, flip_choice(details['leather']))
    except Exception:
        pass

def select_style(driver, make_model=""):

    selector = "#optionsCard > div:nth-child(1) > div > div > div"
    WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.CSS_SELECTOR, selector)))
    style = driver.find_element_by_css_selector(selector)

    if style.text == "Style":
        style.click()
        tags = style.find_elements_by_xpath("//*/ul/li/*")
        trims = [x for x in tags if x.tag_name == "span"]
        # compare text in each trim versus text in make_model, if matches click
        for i in trims:
            # split each section on space and convert to lowercase
            trim = i.text.lower().split()
            trim = [x.lower() for x in trim]
            # do the same for make and model
            model = [x.lower() for x in make_model.split()]
            # check if any of the words are the same
            if not set(trim).isdisjoint(model):
                # if same the click
                i.click()
                break


def confirm_trims(driver, make_model=""):
    list_of_divs = [
        '#trimsCard > div:nth-child(2) > div > div > div',
        '#trimsCard > div:nth-child(3) > div > div > div > div.ant-select-selection-selected-value',
        '#trimsCard > div:nth-child(4) > div > div > div > div',
        '#trimsCard > div:nth-child(5) > div > div > div > div'
    ]
    for div in list_of_divs:
        WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.CSS_SELECTOR, div)))
        style = driver.find_element_by_css_selector(div)
        if "Select" in style.text:
            style.click()
            tags = style.find_elements_by_xpath("//*/ul/li/*")
            trims = [x for x in tags if x.tag_name == "span"]
            # set a var if no matches are found
            matches = 0
            # compare text in each trim versus text in make_model, if matches click
            for i in trims:
                # split each section on space and convert to lowercase
                trim = i.text.lower().split()
                trim = [x.lower() for x in trim]
                # do the same for make and model
                model = [x.lower() for x in make_model.split()]
                # check if any of the words are the same
                if not set(trim).isdisjoint(model):
                    # if same the click
                    try:
                        i.click()
                    except Exception:
                        pass
                    matches = 1
            # select the last one if none matches
            if matches == 0:
                trims[-1].click()

def check_if_entered(driver):
    string = 'Sorry. This vehicle cannot be submitted because an offer has been received and pending a response.'
    try:
        WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, "//*[text()='{}']".format(string))))
        entered_already = True
    except Exception:
        entered_already = None
        pass
    return entered_already

def mileage_is_correct(driver):
    try:
        driver.find_element_by_name("isCorrectMileage").click()
    except Exception:
        pass

def get_offer(driver, cars):
    # log in first
    login(driver)
    for car in cars:
        try:
            details = get_car_info(car)
            enter_vin(driver, details['vin'])
            # do this if the car wasn't entered already
            if not check_if_entered(driver):
                select_style(driver, details['make_model'])
                enter_mileage(driver, details['mileage'])
                select_color(driver, details['color'])
                mileage_is_correct(driver)
                press_vehicle_option(driver)
                confirm_trims(driver, details['make_model'])
                fix_engine_tranny_drive(driver)
                has_leather(driver, details['leather'])
                has_moonroof(driver, details['moonroof'])
                has_navi(driver, details['navigation'])
                kbb_discrepancy_fix(driver, details)
                next_condition(driver)
                certified_no(driver)
                select_accidents(driver, details['accidents'])
                get_offer_button(driver)
            car.append(get_price(driver, details['vin']))
        except Exception:
            print(traceback.format_exc())
            car.append("FAIL")
            driver.refresh()
            continue
    return cars