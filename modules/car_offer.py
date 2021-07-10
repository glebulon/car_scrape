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
    driver.find_element(By.ID, "userName").send_keys("vl@larinautomotive.com")
    driver.find_element(By.ID, "password").click()
    driver.find_element(By.ID, "password").send_keys("ViewSonic900!")
    WebDriverWait(driver, 5).until(ec.visibility_of_element_located((By.CSS_SELECTOR, ".ant-btn")))
    driver.find_element(By.CSS_SELECTOR, ".ant-btn").click()
    # wait for the instant offer button to show up
    WebDriverWait(driver, 20).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="content"]/div/div/div/div[3]/\
        div[1]/div[2]/div[1]/div[2]/div[1]/div[2]/button')))
    print("A")


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
    colors = ["Black", "Blue", "Brown", "Gold", "Gray", "Green", "Maroon", "Orange", "Purple", "Red", "Silver", "Tan", "White", "Yellow"]
    selector = driver.find_element(By.CSS_SELECTOR, "div:nth-child(3) > .ant-select:nth-child(2) \
                                                    .ant-select-selection__placeholder")
    # if the color matches, use it, otherwise just pick black
    color = [x for x in colors if color.capitalize() == x]
    # if the list is empty add Black to it
    color = color or ["Black"]
    # pick the color
    selector.click()
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
    driver.find_element(By.XPATH, '//*[@id="content"]/div/div/div/div[3]/div[1]/div[2]/div[1]/div[2]/div[1]/div[2]\
                                    /button').click()
    # dont't think these are needed
    # driver.find_element(By.CSS_SELECTOR, ".ant-layout-sider-children").click()
    # driver.find_element(By.CSS_SELECTOR, ".ant-input-lg").click()
    WebDriverWait(driver, 5).until(ec.visibility_of_element_located((By.CSS_SELECTOR, ".ant-input-lg")))
    driver.find_element(By.CSS_SELECTOR, ".ant-input-lg").send_keys(vin)
    driver.find_element(By.CSS_SELECTOR, ".goButton___wC2QZ").click()


def enter_mileage(driver, mileage):
    WebDriverWait(driver, 15).until(ec.visibility_of_element_located((By.ID, "tradeGradeMileage")))
    driver.find_element(By.ID, "tradeGradeMileage").click()
    driver.find_element(By.ID, "tradeGradeMileage").send_keys(mileage)

def has_leather(driver, leather):
    xpath = "/html/body/div[6]/div/div/div/div/div[2]/div/div[2]/div/div[8]/div/div[2]/div/div/div[1]/div/"
    xpath = xpath + "button[1]" if leather == "yes" else xpath + "button[2]"
    driver.find_element(By.XPATH, xpath).click()

def has_moonroof(driver, moonroof):
    xpath = "/html/body/div[6]/div/div/div/div/div[2]/div/div[2]/div/div[8]/div/div[2]/div/div/div[2]/div/"
    xpath = xpath + "button[1]" if moonroof == "yes" else xpath + "button[2]"
    driver.find_element(By.XPATH, xpath).click()

def has_navi(driver, navi):
    xpath = "/html/body/div[6]/div/div/div/div/div[2]/div/div[2]/div/div[8]/div/div[2]/div/div/div[3]/div/"
    xpath = xpath + "button[1]" if navi == "yes" else xpath + "button[2]"
    driver.find_element(By.XPATH, xpath).click()

def press_vehicle_option(driver):
    driver.find_element(By.CSS_SELECTOR, "#optionsCard > button").click()
    WebDriverWait(driver, 10).until(ec.visibility_of_element_located((By.CSS_SELECTOR, "#trimsCard > h5")))

def get_offer(driver, cars):
    # log in first
    login(driver)
    for car in cars:
        details = get_car_info(car)
        enter_vin(driver, details['vin'])
        enter_mileage(driver, details['mileage'])
        select_color(driver, details['color'])
        press_vehicle_option(driver)
        has_leather(driver, details['leather'])
        has_moonroof(driver, details['moonroof'])
        has_navi(driver, details['navigation'])
        print("")