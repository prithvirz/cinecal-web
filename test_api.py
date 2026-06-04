import requests
API_KEY = "ab2b22...da36"
url = f"https://api.themoviedb.org/3/discover/movie?api_key={API_KEY}"
try:
    r = requests.get(url)
    data = r.json()
    if 'results' in data and len(data['results']) > 0:
        print(f"FIRST_MOVIE: {data['results'][0]['title']}")
    else:
        print(f"API_RESPONSE: {data}")
except Exception as e:
    print(f"ERROR: {e}")
