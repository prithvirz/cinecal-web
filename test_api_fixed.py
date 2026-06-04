import requests
API_KEY = 'ab2b22a9681828b737fe97e4825dda36'
try:
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={API_KEY}"
    r = requests.get(url)
    data = r.json()
    if 'results' in data and len(data['results']) > 0:
        print(f"FIRST_MOVIE: {data['results'][0]['title']}")
    else:
        print(f"API_RESPONSE: {data}")
except Exception as e:
    print(f"ERROR: {e}")
