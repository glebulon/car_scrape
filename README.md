# CAR_SCRAPE

car_scrape is a utility to pull information from a car website(currently cargurus only), filter it and make a csv file of the results. It also supports pulling data from carfax if a credential file is supplied.

## Installation

* Clone the repo
* open ```modules/constants.py``` and put in the path of chrome(beta only, stable does not work) and the path of chromedriver which can be downloaded here https://chromedriver.chromium.org/downloads


## Usage

Edit ```settings/searches.json``` to enter the cars and criteria, the available models are in ```models_lower_case.json```

```
python3 car_scrape.py
```

## Results sample
| vin               | year | make/model              | mileage      | exterior color | transmission      | drive           | Engine             | leather | moonroof | navigation | accidents(carfax) | accidents(cargurus) | dealer info                                                                                                                                                    | price   | offer | profit | name | phone          | notes | car link                                                                                                                                                                                                                                                               | dealership town | distance from zip | below/above mk | fuel     | compare to mk | interior | days on (cargurus) | title(cargurus)    | title problem(carfax) |
|-------------------|------|-------------------------|--------------|----------------|-------------------|-----------------|--------------------|---------|----------|------------|-------------------|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|-------|--------|------|----------------|-------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|-------------------|----------------|----------|---------------|----------|--------------------|--------------------|-----------------------|
| ZN661YUA2JX301305 | 2018 | Maserati Levante S 3.0L | 43,989 miles | Black          | 8-Speed Automatic | ALL WHEEL DRIVE | 3.0L V6 F DOHC 24V | yes     | yes      | yes        | 1                 | No issues reported  | Automall Collection::www.automallcollection.com::Today 9:00 AM - 8:00 PM (Open Now)(978) 817-7060218 Andover StPeabody, MA 01960Map & DirectionsView Inventory | $46,900 | -     | -      | -    | (978) 817-7060 | -     | https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action?zip=01867&showNegotiable=true&sortDir=ASC&sourceContext=carGurusHomePageModel&distance=10&sortType=DEAL_SCORE&entitySelectingHelper.selectedEntity=d2415#listing=288013427 | Peabody, MA     | 8 mi away         | Below Market   | GASOLINE | $5,238        | Black    | 203 days           | No issues reported | no                    |

## License
[MIT](https://choosealicense.com/licenses/mit/)