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
    file_prefix = misc.get_prefix(search)
    file_name = date_stamp if not file_prefix else date_stamp + '-' + file_prefix + '-' + misc.gen_unique()
    logging.critical("Start: " + file_name)
    logging.critical(search)
    # run search
    cars = []
    cars = cars + cgur.cars(driver, make=search['make'], model=search['model'], zip=search['zipcode'],
                            distance=search['distance'], number_of_listings=search['number_of_listings'],
                            start=search['start_year'], end=search['end_year'], mileage=search['mileage'],
                            deal_quality=search['deal_quality'])
    # populate the carfax history
    cars = cfax.populate_carfax_info(cars, driver)
    # get a car offer offer
    cars = coffer.get_offer(driver, cars)
    # write to csv file
    csv.write_to_csv(header="yes", payload=cars, file_name=file_name)
    logging.critical("Cars found: {}".format(len(cars)))
    logging.critical("End: " + file_name)
# close the window
driver.close()
print("All done, close this window")
