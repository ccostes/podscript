from urllib.request import urlopen
import json

"""
Retrieve podcast data from itunes catalog - currently unused 
since everything we need is in the feed.
"""

lookup_url = "https://itunes.apple.com/lookup?id="

# Lookup apple podcast record by collection ID
def get_apple_podcast(id):
    url = lookup_url + id
    response = urlopen(url)
    data = json.loads(response.read())
    if data.get('resultCount') == 1:
        return data.get('results')[0]

if __name__ == "__main__":
    print(get_apple_podcast('1200361736'))