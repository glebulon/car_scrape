#!/usr/bin/python3
import json
import logging
import re
import sys
sys.path.append("../")
import time
import traceback

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium import webdriver
import misc as m

user_agent = r"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.109 Safari/537.36 OPR/84.0.4316.31"
options = webdriver.ChromeOptions()
options.headless = False
options.add_argument("--window-size=1920,1080")
options.add_argument(user_agent)
options.add_argument("--disable-gpu")
options.add_argument('disable-infobars')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
chrome_driver_binary = r"D:\my documents\car_scrape\chromedriver.exe"
driver = webdriver.Chrome(chrome_driver_binary, chrome_options=options)

# open page
driver.get('https://cars.com')
# wait to page to load, makes a js call/check
m.wait_for_page_to_load(driver)
driver.switch_to.default_content()
codes = {}
makes = driver.find_element(By.ID, "makes")
selections = Select(makes)
for i in selections.options[1:]:
    selections.select_by_index(selections.options.index(i))
    models_elem = driver.find_element(By.ID, "models")
    model_selections = Select(models_elem)
    models = [x.text for x in model_selections.options[1:]]
    codes[i.text] = models

print("A")
