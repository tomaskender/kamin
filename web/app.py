import folium
import pandas as pd
import itertools
import streamlit as st
from streamlit_folium import st_folium
import requests

ESTATES_SELECTOR = ['_embedded', 'estates']
TITLE = 'KAMIN'
CAPTION = 'Visualize houses and flats for sale'
PLOT_COLORS = ['darkblue', 'darkpurple', 'orange', 'pink', 'darkgreen', 'darkred', 'lightgreen', 'cadetblue', 'red', 'white', 'lightgray', 'lightred', 'blue', 'purple', 'beige', 'black', 'green', 'gray', 'lightblue']

@st.cache(show_spinner=False)
def download_data(city):
    dfs = []
    for i in itertools.count(start=0):
        r = requests.get(f"https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_type_cb=1&per_page=999&region={city}&page={i}")
        if not r.ok:
            # Request failed
            return []

        if r.json()['filter']['suggested_districtId'] == -1 and r.json()['filter']['suggested_regionId'] != -1:
            # City not found
            return []

        df = pd.json_normalize(r.json(), ESTATES_SELECTOR)
        if df.empty:
            # No more entries have been found
            break

        df = df[['name', 'locality', 'price', 'gps.lat', 'gps.lon', 'hash_id']].rename(columns={'gps.lat': 'lat', 'gps.lon': 'lon'})
        df['rooms'] = df.name.str.extract(r'(?P<rooms>\d((\+kk)|(\+1)))')['rooms'].fillna('')
        df['price_formatted'] = df.price.map('{:,.0f}'.format)
        dfs.append(df)
    return dfs

@st.cache
def apply_filter(df, category):
    if category != 'Any':
        df = df[df.rooms == category]
    return df

def main():
    st.set_page_config(page_title=TITLE)
    st.title(TITLE)
    st.caption(CAPTION)

    st.sidebar.title('Filter')
    city = st.sidebar.text_input('City', 'Brno')

    dfs = download_data(city)

    if dfs:
        df = pd.concat(dfs)
        category = st.sidebar.selectbox('Flat category', ['Any'] + sorted(filter(None, df['rooms'].unique()))) # Display non-empty categories
        df = apply_filter(df, category)
        st.metric(label=category + ' flats available', value=len(df))
        
        m = folium.Map(location=[df.lat.mean(), df.lon.mean()])
        
        for i, (category, df) in enumerate(df.groupby(['rooms'])):
            for _, flat in df.iterrows():
                icon = folium.Icon(color=PLOT_COLORS[i % len(PLOT_COLORS)])
                folium.Marker([flat.lat, flat.lon], tooltip=f"<strong>{flat['name']}</strong></br>Price: <strong>{flat.price_formatted}</strong> CZK", icon=icon).add_to(m)

        st_folium(m, returned_objects=[])
    else:
        st.error(city + ' has not been found!')

if __name__ == '__main__':
    main()