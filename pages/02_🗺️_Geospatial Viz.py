import streamlit as st
import pandas as pd
import geopandas
from streamlit_folium import st_folium

st.set_page_config(layout="centered", page_title="Fuel Forecasting Dashboard",
                   page_icon="⛽")

st.markdown("# 🗺️ Geospatial Viz ")
fuels=['Unleaded 95','Diesel','Autogas']

@st.cache(suppress_st_warning=True)
def fuel_data(fuels):
    df = pd.read_csv("nomos_cleaned.csv", usecols=fuels+['date','nomos'])
    df[fuels] = df[fuels].apply(pd.to_numeric, errors='coerce', axis=1)
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna(axis=0,how="any")
    df = df.set_index("date")
    df=df.groupby('nomos').resample('D').mean().interpolate()
    df['year'] = pd.DatetimeIndex(df.index.get_level_values(1)).year

    return df

df = fuel_data(fuels)

enable_time_filter=st.sidebar.radio('Enable yearly filtering?', ('No','Yes'))
if enable_time_filter=='Yes':
    year_list = set(df['year'].values)
    year = st.sidebar.selectbox('Year', year_list, len(year_list)-1)
    df=df.reset_index().set_index('year').loc[year]

@st.cache(suppress_st_warning=True)
def mean_geo_data(df):
    gdf=geopandas.read_file('./gr/nomoi.shp')
    gdf=gdf[['NAME_ENG','geometry']]

    nomoi=['N. ATHINON','N. ETOLOAKARNANIAS','N. ARGOLIDAS','N. ARKADIAS','N. ARTAS','N. ACHAIAS','N. VIOTIAS','N. GREVENON','N. DRAMAS',
        'N. DODEKANISON','N. EVROU','N. EVVIAS','N. EVRYTANIAS','N. ZAKYNTHOU','N. ILIAS','N. IMATHIAS','N. IRAKLIOU','N. THESPROTIAS','N. THESSALONIKIS',
        'N. IOANNINON','N. KAVALAS','N. KARDITSAS','N. KASTORIAS','N. KERKYRAS','N. KEFALLONIAS','N. KILKIS','N. KOZANIS','N. KORINTHOU','N. KYKLADON',
        'N. LAKONIAS','N. LARISAS','N. LASITHIOU','N. LESVOU','N. LEFKADAS','N. MAGNISIAS','N. MESSINIAS','N. XANTHIS','N. PELLAS','N. PIERIAS','N. PREVEZAS',
        'N. RETHYMNOU','N. RODOPIS','N. SAMOU','N. SERRON','N. TRIKALON','N. FTHIOTIDAS','N. FLORINAS','N. FOKIDAS','N. CHALKIDIKIS','N. CHANION','N. CHIOU']

    temp=dict()
    temp['Unleaded 95']={}
    temp['Diesel']={}
    temp['Autogas']={}
    for n in nomoi:
        for fuel in fuels:
            temp[fuel][n]=df.query(f'nomos == "{n}"')[fuel].mean()

    mean_nomoi=pd.DataFrame(temp)

    geo_nomoi=gdf.set_index('NAME_ENG').join(mean_nomoi)

    for i in ['N. DYTIKIS ATTIKIS', 'N. ANATOLIKIS ATTIKIS', 'N. PIREOS KE NISON']:
        geo_nomoi.loc[i,['Unleaded 95','Diesel','Autogas']]=geo_nomoi.loc['N. ATHINON',['Unleaded 95','Diesel','Autogas']]
    geo_nomoi.reset_index(inplace=True)
    geo_nomoi.rename(columns = {'NAME_ENG':'nomos'}, inplace = True)
    geo_nomoi = geo_nomoi.round(2)
    return geo_nomoi

geo_nomoi=mean_geo_data(df)

fuel = st.sidebar.selectbox(
    "Select Fuel:",
    options=fuels
)


col1, col2 = st.columns(2)
with col1:
    min=geo_nomoi[fuel].min()
    st.metric('Lowest Price',str(round(min,2))+"€")
    st.metric('At:',geo_nomoi.loc[geo_nomoi[fuel]==min]['nomos'].values[0])
with col2:
    max=geo_nomoi[fuel].max()
    st.metric('Lowest Price',str(round(max,2))+"€")
    st.metric('At:',geo_nomoi.loc[geo_nomoi[fuel]==max]['nomos'].values[0])


m = geo_nomoi.explore(
     column=fuel,  # make choropleth based on "Diesel" column
     scheme="naturalbreaks",  # use mapclassify's natural breaks scheme
     legend=True, # show legend
     k=5, # use 5 bins
     legend_kwds=dict(colorbar=True), # do not use colorbar
     name=fuel # name of the layer in the map
)

st_folium(m)