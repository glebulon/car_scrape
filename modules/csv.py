#!/usr/bin/python3

import csv
import modules.misc as m

def write_to_csv(header="yes", file_name="", payload=None, source="cargurus"):
    with open(r'reports/' + file_name + '.csv', 'a+', newline='') as file:
        writer = csv.writer(file, dialect='excel')
        if header == "yes":
            writer.writerow(["vin", "year", "make/model", "mileage", "exterior color", "transmission", "drive",
                             "Engine", "leather", "moonroof", "navigation", "accidents(carfax)",
                             "accidents({})".format(source), "dealer info", "price", "offer", "profit", "name",
                             "phone", "notes", "car link", "dealership town", "distance from zip", "below/above mk",
                             "fuel", "compare to mk", "interior", "days on ({})".format(source),
                             "title({})".format(source), "title problem(carfax)"
                             ]
                            )
        for entry in payload:
            if entry != "":
                writer.writerow(m.format_entry(entry))