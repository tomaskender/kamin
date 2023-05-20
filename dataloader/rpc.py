import itertools
import os
import pandas as pd
import requests
import xmlrpc.server

ESTATES_SELECTOR = ['_embedded', 'estates']

class DataLoaderService:
    def find(self, town):
        dfs = []
        for i in itertools.count(start=0):
            r = requests.get(f"https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_type_cb=1&per_page=999&region={town}&page={i}")
            if not r.ok:
                raise Exception('Request to API failed')

            if r.json()['filter']['suggested_districtId'] == -1 and r.json()['filter']['suggested_regionId'] != -1:
                raise Exception('City not found')

            df = pd.json_normalize(r.json(), ESTATES_SELECTOR)
            if df.empty:
                # No more entries have been found
                break

            df = df[['name', 'locality', 'price', 'gps.lat', 'gps.lon', 'hash_id']].rename(columns={'gps.lat': 'lat', 'gps.lon': 'lon'})
            df['rooms'] = df.name.str.extract(r'(?P<rooms>\d((\+kk)|(\+1)))')['rooms'].fillna('')
            df['price_formatted'] = df.price.map('{:,.0f}'.format)
            dfs.append(df)
        df = pd.concat(dfs)
        return df.to_json()

server = xmlrpc.server.SimpleXMLRPCServer(('0.0.0.0', int(os.environ['RPC_PORT'])))
server.register_instance(DataLoaderService())
server.serve_forever()