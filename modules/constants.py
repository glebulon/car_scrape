#!/usr/bin/python3

import logging
from selenium import webdriver

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
chrome_driver_binary = r"C:\Users\Gleb\Documents\code\car_scrape\chromedriver.exe"
driver = webdriver.Chrome(chrome_driver_binary, chrome_options=options)
carfax_creds = "carfax_creds.json"
