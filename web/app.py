import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import xmlrpc.client

TITLE = 'KAMIN'
CAPTION = 'Visualize houses and flats for sale'
PLOT_COLORS = ['darkblue', 'darkpurple', 'orange', 'pink', 'darkgreen', 'darkred', 'lightgreen', 'cadetblue', 'red', 'white', 'lightgray', 'lightred', 'blue', 'purple', 'beige', 'black', 'green', 'gray', 'lightblue']

@st.cache(show_spinner=False)
def download_data(town):
    server = xmlrpc.client.ServerProxy(f"http://dataloader:{os.environ['DATALOADER_RPC_PORT']}")
    return server.find(town)

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

    df_json = download_data(city)
    df = pd.read_json(df_json)
    if df:
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