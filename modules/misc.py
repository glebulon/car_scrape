#!/usr/bin/python3

import json
import uuid


# read in search
def search_settings_read():
    with open('settings/searches.json') as f:
        return(json.load(f))

# generate a uuid and trim it
def gen_unique():
    return str(uuid.uuid4()).split('-')[0]


# put all info in the correct order
def format_entry(entry):
    car = []
    # vin
    car.append(entry[8])
    # year
    car.append(entry[0])
    # make/model
    car.append(entry[1])
    # mileage
    car.append(entry[3])
    # exterior color
    car.append(entry[6])
    # transmission
    car.append(entry[2])
    # drive
    car.append(entry[27])
    # engine
    car.append(entry[26])
    # leather
    car.append(entry[10])
    # moonroof
    car.append(entry[9])
    # navigation
    car.append(entry[11])
    # accident(carfax)
    car.append(entry[23])
    # accident(cargurus)
    car.append(entry[19])
    # dealer info
    car.append(entry[13])
    # price
    car.append(entry[4])
    # offer
    car.append("-")
    # profit
    car.append("-")
    # name
    car.append(entry[15])
    # phone
    car.append(entry[14])
    # notes
    car.append("-")
    # car link
    car.append(entry[12])
    # dealership town
    car.append(entry[16])
    # disatnce from zip
    car.append(entry[17])
    # below/above mk
    car.append(entry[21])
    # fuel
    car.append(entry[25])
    # compare to mk
    car.append(entry[22])
    # interior
    car.append(entry[7])
    # days on cargurus
    car.append(entry[18])
    # title cargurus
    car.append(entry[19])
    # title carfax
    car.append(entry[24])
    return car
