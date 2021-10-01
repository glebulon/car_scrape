#!/usr/bin/python3

import logging
import time

# my own functions
import modules.car_fax as cfax
import modules.car_gurus as cgur
import modules.car_offer as coffer
import modules.csv as csv
import modules.misc as misc
import modules.constants as cons

# create a driver, open a window
driver = cons.driver

# get the car searches
searches = misc.search_settings_read()
# itterate over all entries and run a full search for each
for search in searches:
    # date stamp to use in report name
    date_stamp = time.strftime('%Y-%m-%d--%I-%M-%p')
    file_prefix = misc.get_prefix(search).replace(' ', '-')
    file_name = date_stamp if not file_prefix else date_stamp + '-' + file_prefix
    logging.critical("Start: " + file_name)
    logging.critical(search)
    # run search
    cars = []
    cars = cars + cgur.cars(driver, make=search['make'], model=search['model'], zip=search['zipcode'],
                            distance=search['distance'], number_of_listings=search['number_of_listings'],
                            start=search['start_year'], end=search['end_year'], mileage=search['mileage'],
                            deal_quality=search['deal_quality'])
    print("Finished cargurus, starting carfax")
    print("Cars found: {}".format(len(cars)))
    # populate the carfax history
    cars = cfax.populate_carfax_info(cars, driver)
    print("Finished carfax, starting car_offer")
    # enter the car details into car_offer
    coffer.enter_car(driver, cars)
    # # sleep in between entering details and getting prices
    # print("Before sleep:" + time.strftime('%I-%M-%S-%p'))
    # time.sleep(3600 / int(len(searches)))
    # print("After sleep:" + time.strftime('%I-%M-%S-%p'))
    cars = coffer.get_car_price(driver, cars)
    # write to csv file
    csv.write_to_csv(header="yes", payload=cars, file_name=file_name)
    logging.critical("Cars found: {}".format(len(cars)))
    logging.critical("End: " + file_name)
# close the window
driver.close()
print("All done, close this window")
