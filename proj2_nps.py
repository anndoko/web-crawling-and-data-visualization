## proj_nps.py
## Skeleton for Project 2, Winter 2018
## ~~~ modify this file, but don"t rename it ~~~
import requests
import json
import secret
from bs4 import BeautifulSoup

## you can, and should add to and modify this class any way you see fit
## you can add attributes and modify the __init__ parameters,
##   as long as tests still pass
##
## the starter code is here just to make the tests run (and fail)
class NationalSite():
    def __init__(self, type, name, desc, url=None):
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
        print("Getting cached data...")
        return CACHE_DICTION[unique_ident]
    else:
        print("Making a request for new data...")
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
    pass

## Must plot up to 20 of the NearbyPlaces found using the Google Places API
## param: the NationalSite around which to search
## returns: nothing
## side effects: launches a plotly page in the web browser
def plot_nearby_for_site(site_object):
    pass
