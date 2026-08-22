import requests

def fetch_json(url):
    response = requests.get(url)
    return response.json()
