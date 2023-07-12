import requests
import logging

# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.
import http.client as http_client

http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

url = "https://api.flickr.com/services/rest/?\
        api_key=78a23dc264331f49233048ea6e1b8d4c&\
        method=flickr.photos.search&\
        bbox=77.71522338867189%2C12.901765441894533%2C77.71534408569337%2C12.901861572265627&\
        accuracy=16&\
        format=json&\
        nojsoncallback=1&\
        page=1&\
        perpage=250&\
        min_taken_date=2019-06-08+00%3A00%3A00&\
        max_taken_date=2019-06-08+00%3A00%3A00&\
        extras=geo,date_taken,tags,url,owner_name&\
        media=photos"

url = f"https://api.flickr.com/services/rest/"

params = {
    "api_key": '78a23dc264331f49233048ea6e1b8d4c',
    "method": "flickr.photos.search",
    "bbox": '77.71522338867189,12.901765441894533,77.71534408569337,12.901861572265627',
    "accuracy": 16,
    "format": "json",
    "nojsoncallback": 1,
    "page": 1,
    "perpage": 250,
    "min_taken_date": '2019-06-08+00:00:00',
    "max_taken_date": '2019-06-08+00:00:00',
    "extras": 'geo,date_taken,tags,url,owner_name',
    "media": "photos"
}

r = requests.get(url, params=params)
print(r)
print(r.json())
