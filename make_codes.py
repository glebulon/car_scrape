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
from selenium import webdriver


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

# open page
driver.get("https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action?sourceContext=\
    carGurusHomePageModel&entitySelectingHelper.selectedEntity=&zip=01602")
driver.switch_to.default_content()
driver.find_element(By.ID, "cargurus-desktop-new-search-form-car-make").click()
dropdown = driver.find_element(By.ID, "cargurus-desktop-new-search-form-car-make")
selections = Select(dropdown)
makes = [x.text for x in selections.options]
# remove "All Makes"
makes.pop(0)
# Get code for all makes
codes = {}
for make in makes:
    dropdown = driver.find_element(By.ID, "cargurus-desktop-new-search-form-car-make")
    dropdown.find_element(By.XPATH, "//option[. = '{}']".format(make)).click()
    driver.find_element(By.CSS_SELECTOR, ".\\_3CLNo6").click()
    codes[make] = driver.current_url.split("=")[-1]

print("A")
