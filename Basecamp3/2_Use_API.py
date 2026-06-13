# Import requests module to make http requests
import requests
import json

# The URL and the query params, as indicated by the API spec / doc.
# Refer https://rapidapi.com/hub
url = "https://real-time-news-data.p.rapidapi.com/search"
querystring = {"query":"AI Research","limit":"10","time_published":"anytime","country":"US","lang":"en"}

# Add Headers to the request
headers = {
	"x-rapidapi-key": "aaf2f390b7msheaa8d215f651e4p14658jsnfd40ab2b478",					   
	"x-rapidapi-host": "real-time-news-data.p.rapidapi.com"
}

# Place a request and receive the response
response = requests.get(url, headers=headers, params=querystring)
response_data = response.json ()

# Align better the JSON content
print(json.dumps(response_data, indent=4))
