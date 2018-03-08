## proj_nps.py
## Skeleton for Project 2, Winter 2018
## ~~~ modify this file, but don"t rename it ~~~
import requests
import json
import secret
import plotly.plotly as py
from bs4 import BeautifulSoup

## you can, and should add to and modify this class any way you see fit
## you can add attributes and modify the __init__ parameters,
##   as long as tests still pass
##
## the starter code is here just to make the tests run (and fail)
class NationalSite():
    def __init__(self, type, name, desc="", url=None):
        self.type = type
        self.name = name
        self.description = desc
        self.url = url

        # needs to be changed, obvi.
        self.address_street = "123 Main St."
        self.address_city = "Smallville"
        self.address_state = "KS"
        self.address_zip = "11111"

    def __str__(self):
        return "{} ({}): {}, {}, {} {}".format(self.name, self.type, self.address_street, self.address_city, self.address_state, self.address_zip)

## you can, and should add to and modify this class any way you see fit
## you can add attributes and modify the __init__ parameters,
##   as long as tests still pass
##
## the starter code is here just to make the tests run (and fail)
class NearbyPlace():
    def __init__(self, name):
        self.name = name
        # lag & lng
        self.lag = ""
        self.lng = ""

    def __str__(self):
        return self.name


## Must return the list of NationalSites for the specified state
## param: the 2-letter state abbreviation, lowercase
##        (OK to make it work for uppercase too)
## returns: all of the NationalSites
##        (e.g., National Parks, National Heritage Sites, etc.) that are listed
##        for the state at nps.gov

# ---------- Caching ----------
CACHE_FNAME = "cache.json"
try:
    cache_file = open(CACHE_FNAME, "r")
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()
except:
    CACHE_DICTION = {}

def get_unique_key(url):
    return url

def make_request_using_cache(url):
    unique_ident = get_unique_key(url)

    if unique_ident in CACHE_DICTION:
        # access the existing data
        return CACHE_DICTION[unique_ident]
    else:
        # make the request and cache the new data
        resp = requests.get(url)
        CACHE_DICTION[unique_ident] = resp.text # only store the html
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file

        return CACHE_DICTION[unique_ident]

def get_sites_for_state(state_abbr):
    # baseurl
    baseurl = "https://www.nps.gov"

    # scrap the homepage
    homepage_url = baseurl + "/index.htm" # set the url of the homepage
    page_text = make_request_using_cache(homepage_url)
    page_soup = BeautifulSoup(page_text, "html.parser")

    # get state abbrs and end nodes
    dropdown_menu_items = page_soup.find(class_ = "dropdown-menu")
    end_node_dic = {} # create a dic to store the abbrs of states and the end nodes
    for item in dropdown_menu_items:
        try:
            end_node = item.find("a")["href"]
            end_node_dic[end_node[7:9]] = end_node
        except:
            continue

    # scrape the state page
    national_sites_page_url = baseurl + end_node_dic[state_abbr] # set the url of the target page
    sites_page_text = make_request_using_cache(national_sites_page_url)
    sites_page_soup = BeautifulSoup(sites_page_text, "html.parser")

    # get sites
    sites_lst_items = sites_page_soup.find(id = "list_parks")
    results_lst = [] # create a list to store the instances of NaitonalSite
    for site in sites_lst_items:
        try:
            # get the basic info: type, name, description, and url
            site_type = site.find("h2").string
            site_name = site.find("a").string
            site_description = site.find("p").text
            site_url = baseurl + site.find("a")["href"]

            # create instance using the basic info as its params
            national_site = NationalSite(site_type, site_name, site_description, site_url)

            # scrape the detail page to get the address
            detail_page_text = make_request_using_cache(site_url)
            detail_page_soup = BeautifulSoup(detail_page_text, "html.parser")
            adr_items = detail_page_soup.find(class_ = "adr")

            # assign the values
            national_site.address_street = adr_items.find("span", class_ = "street-address").text.replace("\n","")
            national_site.address_city = adr_items.find(itemprop = "addressLocality").text
            national_site.address_state = adr_items.find(class_ = "region").text
            national_site.address_zip = adr_items.find(class_ = "postal-code").text[0:5]

            # add the instance to the list
            results_lst.append(national_site)
        except:
            continue

    return results_lst


## Must return the list of NearbyPlaces for the specifite NationalSite
## param: a NationalSite object
## returns: a list of NearbyPlaces within 10km of the given site
##          if the site is not found by a Google Places search, this should
##          return an empty list
def get_nearby_places_for_site(national_site):
    # set the key
    google_api_key = secret.google_places_key

    # get the GPS information using Google Geocode API
    ## form the url, params: name, type, and key
    google_geo_url = "https://maps.googleapis.com/maps/api/place/textsearch/json?query={}&tyepe={}&key={}".format(national_site.name, national_site.type, google_api_key)
    ## request the data
    geo_results = make_request_using_cache(url = google_geo_url)
    geo_results_py = json.loads(geo_results)
    ## get the lat & lng for nearby places search
    site_lat = geo_results_py["results"][0]["geometry"]["location"]["lat"]
    site_lng = geo_results_py["results"][0]["geometry"]["location"]["lng"]

    # get the places nearby using Google Places API
    # for the url, params: lat, lng, radius, and key
    google_places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={}, {}&radius=10000&key={}".format(site_lat, site_lng, google_api_key)
    ## requesting the data
    nearby_results = make_request_using_cache(url = google_places_url)
    nearby_results_py = json.loads(nearby_results)

    # get places
    results_lst = [] # create a list to store the instances of NearbyPlace
    for place in nearby_results_py["results"]:
        try:
            # get the name
            place_name = place["name"]

            # create instance using the basic info as its param
            nearby_place = NearbyPlace(place_name)
            nearby_place.lat = place["geometry"]["location"]["lat"]
            nearby_place.lng = place["geometry"]["location"]["lng"]

            # add the instance to the list
            results_lst.append(nearby_place)
        except:
            continue

    return results_lst


## Must plot all of the NationalSites listed for the state on nps.gov
## Note that some NationalSites might actually be located outside the state.
## If any NationalSites are not found by the Google Places API they should
##  be ignored.
## param: the 2-letter state abbreviation
## returns: nothing
## side effects: launches a plotly page in the web browser
def plot_sites_for_state(state_abbr):
    # get a list of NationalSite instances in the state
    sites_lst = get_sites_for_state(state_abbr)

    # create lists for plotly
    lat_lst = []
    lng_lst = []
    name_lst = []

    # get the data (lat, lng, and name) of each site and add to the lists
    for site in sites_lst:
        # set the key
        google_api_key = secret.google_places_key
        # get the GPS information using Google Geocode API
        ## form the url, params: name, type, and key
        google_geo_url = "https://maps.googleapis.com/maps/api/place/textsearch/json?query={}&tyepe={}&key={}".format(site.name, site.type, google_api_key)
        ## request the data
        site_geo = make_request_using_cache(url = google_geo_url)
        site_geo_py = json.loads(site_geo)
        try:
            ## get the lat & lng for nearby places search
            site_lat = site_geo_py["results"][0]["geometry"]["location"]["lat"]
            site_lng = site_geo_py["results"][0]["geometry"]["location"]["lng"]
            ## add data to the lists
            lat_lst.append(site_lat)
            lng_lst.append(site_lng)
            name_lst.append(site.name)
        except:
            print("N/A")

    # plotly
    mapbox_access_token = "v6sd6xz0qu"

    trace1 = dict(
            type = 'scattergeo',
            locationmode = 'USA-states',
            lon = lng_lst,
            lat = lat_lst,
            text = name_lst,
            mode = 'markers',
            marker = dict(
                size = 20,
                symbol = 'star',
                color = 'red'
            ))

    data = [trace1]

    min_lat = 10000
    max_lat = -10000
    min_lon = 10000
    max_lon = -10000

    lat_vals = lat_lst
    lon_vals = lng_lst
    for str_v in lat_vals:
        v = float(str_v)
        if v < min_lat:
            min_lat = v
        if v > max_lat:
            max_lat = v
    for str_v in lon_vals:
        v = float(str_v)
        if v < min_lon:
            min_lon = v
        if v > max_lon:
            max_lon = v

    center_lat = (max_lat+min_lat) / 2
    center_lon = (max_lon+min_lon) / 2

    max_range = max(abs(max_lat - min_lat), abs(max_lon - min_lon))
    padding = max_range * .10
    lat_axis = [min_lat - padding, max_lat + padding]
    lon_axis = [min_lon - padding, max_lon + padding]

    layout = dict(
            geo = dict(
                scope='usa',
                projection=dict( type='albers usa' ),
                showland = True,
                landcolor = "rgb(250, 250, 250)",
                subunitcolor = "rgb(100, 217, 217)",
                countrycolor = "rgb(217, 100, 217)",
                lataxis = {'range': lat_axis},
                lonaxis = {'range': lon_axis},
                center = {'lat': center_lat, 'lon': center_lon },
                countrywidth = 3,
                subunitwidth = 3
            ),
        )

    fig = dict(data=data, layout=layout)
    py.plot(fig, validate=False, filename='usa - national sites')


## Must plot up to 20 of the NearbyPlaces found using the Google Places API
## param: the NationalSite around which to search
## returns: nothing
## side effects: launches a plotly page in the web browser
def plot_nearby_for_site(site_object):
    # get the data (lat, lng) of the site object
    google_api_key = secret.google_places_key
    # get the GPS information using Google Geocode API
    ## form the url, params: name, type, and key
    google_geo_url = "https://maps.googleapis.com/maps/api/place/textsearch/json?query={}&tyepe={}&key={}".format(site_object.name, site_object.type, google_api_key)
    ## request the data
    site_geo = make_request_using_cache(url = google_geo_url)
    site_geo_py = json.loads(site_geo)

    # create lists for plotly
    site_lat_lst = []
    site_lng_lst = []
    site_name_lst = []

    site_name_lst.append(site_object.name)
    site_lat_lst.append(site_geo_py["results"][0]["geometry"]["location"]["lat"])
    site_lng_lst.append(site_geo_py["results"][0]["geometry"]["location"]["lng"])

    # get a list of  NearbyPlace instances near the site object
    nearby_places_lst = get_nearby_places_for_site(site_object)

    # create lists for plotly
    place_lat_lst = []
    place_lng_lst = []
    place_name_lst = []

    # get the data (lat, lng, and name) of each place and add to the lists
    for place in nearby_places_lst:
        place_lat_lst.append(place.lat)
        place_lng_lst.append(place.lng)
        place_name_lst.append(place.name)

    # plotly
    mapbox_access_token = "v6sd6xz0qu"
    trace1 = dict(
            type = 'scattergeo',
            locationmode = 'USA-states',
            lon = site_lng_lst,
            lat = site_lat_lst,
            text = site_name_lst,
            mode = 'markers',
            marker = dict(
                size = 20,
                symbol = 'star',
                color = 'red'
            ))

    trace2 = dict(
            type = 'scattergeo',
            locationmode = 'USA-states',
            lon = place_lng_lst,
            lat = place_lat_lst,
            text = place_name_lst,
            mode = 'markers',
            marker = dict(
                size = 8,
                symbol = 'circle',
                color = 'blue'
            ))

    data = [trace1, trace2]
    print(data)

    min_lat = 10000
    max_lat = -10000
    min_lon = 10000
    max_lon = -10000

    lat_vals = place_lat_lst
    lon_vals = place_lng_lst
    for str_v in lat_vals:
        v = float(str_v)
        if v < min_lat:
            min_lat = v
        if v > max_lat:
            max_lat = v
    for str_v in lon_vals:
        v = float(str_v)
        if v < min_lon:
            min_lon = v
        if v > max_lon:
            max_lon = v

    center_lat = (max_lat+min_lat) / 2
    center_lon = (max_lon+min_lon) / 2

    max_range = max(abs(max_lat - min_lat), abs(max_lon - min_lon))
    padding = max_range * .10
    lat_axis = [min_lat - padding, max_lat + padding]
    lon_axis = [min_lon - padding, max_lon + padding]

    layout = dict(
            geo = dict(
                scope='usa',
                projection=dict( type='albers usa' ),
                showland = True,
                landcolor = "rgb(250, 250, 250)",
                subunitcolor = "rgb(100, 217, 217)",
                countrycolor = "rgb(217, 100, 217)",
                lataxis = {'range': lat_axis},
                lonaxis = {'range': lon_axis},
                center = {'lat': center_lat, 'lon': center_lon },
                countrywidth = 3,
                subunitwidth = 3
            ),
        )

    fig = dict(data=data, layout=layout)
    py.plot(fig, validate=False, filename='usa - national sites')

# ---------- Interactive Program ----------
## functions for the Interactive program
def prompt():
    user_input = input("Enter command (or 'help' for options) ")
    return user_input

def help_command():
    # options
    command_dic = {}
    command_dic["list"] = "    available anytime\n    lists all National Sites in a state\n    valid inputs: a two-letter state abbreviation"
    command_dic["nearby"] = "    available only if there is an active result set\n    lists all Places nearby a given result\n    valid inputs: an integer 1-len(result_set_size)"
    command_dic["map"] = "    available only if there is an active result set\n    displays the current results on a map"
    command_dic["exit"] = "    exits the program"
    command_dic["help"] = "    lists available commands (these instructions)"

    # print the options
    for command in command_dic:
        if command == "list":
            print(command + " <stateabbr>")
            print(command_dic[command])
        elif command == "nearby":
            print(command + " <result_number>")
            print(command_dic[command])
        else:
            print(command)
            print(command_dic[command])

def check_if_nearby_or_map(user_input):
    if user_input == "nearby" or user_input == "map":
        return True

## run the program
if __name__ == "__main__":
    user_input = prompt() # prompt user for input
    result_set = [] # create an empty list to store the results

    # end the program if user enters "exist"
    while user_input != "exit":
        # if user enter a search term (str), make data using the string
        if check_if_nearby_or_map(user_input) != True:
            if user_input == "help":
                help_command()
            elif "list" in user_input:
                # set an integer variable for indexing
                index_num = 1

                if len(user_input) <= len("list "):
                    print("Please include <state_abbr>")
                    user_input = input("Enter command (or 'help' for options) ")
                else:
                    try:
                        param = user_input[5:]
                        result_set = get_sites_for_state(param)
                        for result in result_set:
                            print(index_num, result)
                            index_num += 1
                    except:
                        print("Invalid search query.")
        # if user enters a num
        else:
            # if user hasn't done any search yet, ask for input again
            if result_set == []:
                print("You haven't done any search yet.\nPlease use the 'list' command first.")
                user_input = prompt()
                continue
            # if user has done a search before
            else:
                if "nearby" in user_input:
                    print("nearby")
                elif user_input == "map":
                    print("map")

        # prompt user for input again
        user_input = prompt()
