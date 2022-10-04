import pandas as pd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go
import random
import os

os.chdir(os.path.join(r"C:\Users\Admin\Documents\GitHub\FuelPricesGreece","Fuel"))

def space(num_lines=1):
    """Adds empty lines to the Streamlit app."""
    for _ in range(num_lines):
        st.write("")

st.set_page_config(layout="centered", page_title="Fuel Forecasting Dashboard",
                   page_icon="⛽")
st.markdown("# ⛽ Exploratory Analysis")
space(2)

fuels=['Unleaded 95','Diesel','Autogas']
from scipy.interpolate import interp1d
@st.cache(suppress_st_warning=True)
def fuel_data(fuels):

    df = pd.read_csv("nomos_cleaned.csv", usecols=fuels+['date','nomos'])
    df[fuels] = df[fuels].apply(pd.to_numeric, errors='coerce', axis=1)
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna(axis=0,how="any")
    df = df.set_index("date")
    df = df.groupby('nomos').resample('D').mean().interpolate(method='linear')
    df['year'] = pd.DatetimeIndex(df.index.get_level_values(1)).year
    df.reset_index(inplace=True)
    df = df.set_index("date")
    df["nomos"] = df["nomos"].str.upper()
    
    return df

df = fuel_data(fuels)

city = st.sidebar.multiselect(
    "Select Preferacture:",
    options=sorted(df["nomos"].unique().tolist()),
    default=sorted(df["nomos"].unique().tolist())[0]
)

fuels = st.sidebar.multiselect(
    "Select Fuel:",
    options=fuels,
    default=fuels[0]
)

enable_time_filter=st.sidebar.radio('Enable yearly filtering?', ('No','Yes'))
if enable_time_filter=='Yes':
    year_list = set(df['year'].values)
    year = st.sidebar.selectbox('Year', year_list, len(year_list)-1)
    df=df.reset_index().set_index('year').loc[year]


st.header('Average Prices:')
col1, col2, col3 = st.columns(3)
with col1:
    st.metric('Unleaded 95',str(round(df['Unleaded 95'].mean(),2))+"€")
with col2:
    st.metric('Diesel',str(round(df['Diesel'].mean(),2))+"€")
with col3:
    st.metric('Autogas',str(round(df['Autogas'].mean(),2))+"€")

space(2)

st.header('Features:')
col1, col2, col3 = st.columns(3)
with col1:
    rolling_mean=st.radio('Enable Rolling Mean?', ('No','Yes'))
    
with col2:
    if rolling_mean=='Yes':
        roll_mean=st.selectbox(
        "Select Backstep:",
        options=[7,14,30,60]
    )
with col3:
    average=st.radio('Enable Average?', ('No','Yes'))

fig = go.Figure()
colors1 = px.colors.qualitative.Dark24
colors2 = px.colors.qualitative.Alphabet
colors3 = px.colors.qualitative.Light24
colors=[colors1,colors2,colors3]
for c, fuel in enumerate(fuels):
    color=colors[c]
    for index,i in enumerate(city):
        a=df.query(f'nomos == "{i}"')
        a.reset_index(inplace=True)
        fig.add_traces(go.Scatter(x=a['date'], y=a[fuel], name=i+" - "+fuel, mode = 'lines', line=dict(color=color[index])))
        if rolling_mean=='Yes':
            fig.add_traces(go.Scatter(x=a['date'], y=a[fuel].rolling(roll_mean).mean(), name=" Rolling Mean "+str(roll_mean) +" - "+i, mode = 'lines', line=dict(color=color[random.randint(0, len(color)-1)])))
        if average=='Yes':
            fig.add_hline(round(df[fuel].mean(),2), name="Average",line=dict(color='red'))

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Euros",
    font=dict(
        family="Arial Black",
        size=12
    )
)

st.plotly_chart(fig, use_container_width=True)