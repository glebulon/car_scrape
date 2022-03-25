#!/usr/bin/python3

import logging
from selenium import webdriver

# constants
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', filename='run.log', encoding='utf-8',
                    level=logging.CRITICAL, datefmt='%Y-%m-%d %H:%M:%S')
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
options.binary_location = r"C:\Program Files (x86)\Google\Chrome Beta\Application\chrome.exe"
chrome_driver_binary = r"D:\my documents\car_scrape\chromedriver.exe"
driver = webdriver.Chrome(chrome_driver_binary, chrome_options=options)
creds = "creds.json"
