from datetime import date
import itertools
from mongoengine import connect
from model import *
import os
import pandas as pd
import requests
import subprocess
import urllib.parse
import xmlrpc.server

with open(os.environ['DB_USERNAME_FILE'], 'r') as f:
    username = f.read().rstrip('\n')
with open(os.environ['DB_PASSWORD_FILE'], 'r') as f:
    password = f.read().rstrip('\n')

connect(
    db=os.environ['DB_NAME'],
    username=username,
    password=password,
    host=f"mongodb://mongodb:{os.environ['DB_PORT']}")
ESTATES_SELECTOR = ['_embedded', 'estates']

CATEGORY_ORDER = {
    "region_cz": 0,
    "district_cz": 1,
    "municipality_cz": 2,
    "ward_cz": 3,
    "quarter_cz": 4,
    "street_cz": 5
}

class DataLoaderService:
    def get_tracked_towns(self):
        return Town.objects(tracked=True).to_json()
    
    def suggest(self, query):
        print(f"Getting suggestions for '{query}' from API", flush=True)
        encoded_location = urllib.parse.quote(query)
        r = requests.get(f"https://www.sreality.cz/api/v1/localities/suggest?category=municipality_cz,ward_cz,quarter_cz,street_cz&phrase={encoded_location}&limit=10")
        if not r.ok:
            raise Exception('Request to API failed')

        suggestions = r.json()['results']
        print(f"Raw suggestions: {suggestions}", flush=True)
        
        # sort suggestions by their significance
        suggestions = sorted(suggestions, key=lambda entry: CATEGORY_ORDER[entry['category']])
        print(f"Sorted suggestions: {suggestions}", flush=True)
        
        # extract suggested names from json
        suggestions = list(dict.fromkeys([urllib.parse.unquote(sug['userData']['suggestFirstRow']) for sug in suggestions]))
        print(f"Found suggestions: {suggestions}", flush=True)
        return suggestions

    def update(self, town_name):
        print(f"Scraping '{town_name}' from API", flush=True)
        t = Town.objects(_id=town_name)
        t.update_one(set__last_update=date.today())

        dfs = []
        encoded_town_name = urllib.parse.quote(town_name)
        for i in itertools.count(start=0):
            r = requests.get(f"https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_type_cb=1&per_page=999&region={encoded_town_name}&page={i}")
            if not r.ok:
                raise Exception('Request to API failed')

            if r.json()['filter']['suggested_districtId'] == -1 and r.json()['filter']['suggested_regionId'] != -1:
                raise Exception('City not found')

            df = pd.json_normalize(r.json(), ESTATES_SELECTOR)
            if df.empty:
                # No more entries have been found
                break

            print(f"Processing page {i} from API", flush=True)

            df = df[['name', 'locality', 'price', 'gps.lat', 'gps.lon', 'hash_id']].rename(columns={'gps.lat': 'lat', 'gps.lon': 'lon'})
            room_str = df.name.str.extract(r'(?P<rooms>\d((\+kk)|(\+1)))')['rooms'].fillna('')
            df['rooms'] = room_str.str.extract(r'(?P<rooms>\d)')['rooms'].fillna(0).astype(int)
            df['has_separate_kitchen'] = not room_str.str.contains('kk').any()
            df['size'] = df.name.str.extract(r'(?P<size>\d+) m²')['size'].fillna(0).astype(int)
            dfs.append(df)
        df = pd.concat(dfs)
        df.reset_index(inplace=True)

        print(f"Updating database with new entries for '{town_name}'", flush=True)
        props = []
        for prop in df.to_dict('records'):
            p = Property(
                _id=prop['hash_id'],
                street=prop['locality'],
                name=prop['name'],
                rooms=prop['rooms'],
                has_separate_kitchen=prop['has_separate_kitchen'],
                size=prop['size'],
                latitude=prop['lat'],
                longitude=prop['lon'],
                price=prop['price'],
                checked=date.today()
            )
            props.append(p)
        t.update(set__properties=props)
        print(f"New entries for '{town_name}' have been written into database", flush=True)
        
    def find(self, town_name):
        print(f"Finding entries for '{town_name}'..", flush=True)
        if Town.objects(_id=town_name).count() == 0:
            t = Town(_id=town_name, tracked=True, added=date.today(), last_update=date.today())
            t.save()
            self.update(town_name)

        data = [doc.to_mongo().to_dict() for doc in Town.objects(_id=town_name).first().properties]
        df = pd.DataFrame(data)
        return df.to_json()

# Launch autoscraper scheduler
subprocess.Popen(["python3", "autoscraper.py"])

server = xmlrpc.server.SimpleXMLRPCServer(('0.0.0.0', int(os.environ['RPC_PORT'])))
server.register_instance(DataLoaderService())
server.serve_forever()