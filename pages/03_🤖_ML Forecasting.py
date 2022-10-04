import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from copy import copy
from sklearn.neural_network import MLPRegressor
from sktime.performance_metrics.forecasting import MeanAbsoluteScaledError
from sktime.performance_metrics.forecasting import MeanAbsolutePercentageError
from statsmodels.tsa.stattools import adfuller
from darts.utils.statistics import check_seasonality
from darts.timeseries import TimeSeries

st.set_page_config(layout="centered", page_title="Fuel Forecasting Dashboard",
                   page_icon="⛽")

st.markdown("# 🤖 ML Forecasting")


@st.cache(suppress_st_warning=True)
def fuel_data(fuels):
    df = pd.read_csv("nomos_cleaned.csv", usecols=fuels+['date','nomos'])
    df[fuels] = df[fuels].apply(pd.to_numeric, errors='coerce', axis=1)
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna(axis=0,how="any")
    df = df.set_index("date")
    df = df.groupby('nomos').resample('D').mean().interpolate()
    df.reset_index(inplace=True)
    df = df.set_index("date")
    df["nomos"] = df["nomos"].str.upper()
    return df

def detrend_deseasonalize(ts, f:str):
    #Make ts stationary
    for i in range(1,10):
        temp=np.diff(ts,i)
        if adfuller(temp)[1]<=0.05:
            break

    dti = pd.date_range("2015-01-01", periods=len(ts), freq=f)
    temp2 = pd.DataFrame(ts,index=dti)

    #Deseasonalize if needed
    temp3=TimeSeries.from_dataframe(temp2)
    status,p=check_seasonality(temp3, alpha=0.05)
    
    if status :
        rolling_mean = temp2.rolling(window = p).mean()
        new_ts = rolling_mean - rolling_mean.shift()
        new_ts.dropna(inplace=True)
        new_ts = new_ts.values.ravel()
        return new_ts
    return temp

def split_into_train_test(data, in_num, fh):
    train, test = data[:-fh], data[-(fh + in_num):]
    x_train, y_train = train[:-1], np.roll(train, -in_num)[:-in_num]
    x_test, y_test = train[-in_num:], np.roll(test, -in_num)[:-in_num]


    x_train = np.reshape(x_train, (-1, 1))
    x_test = np.reshape(x_test, (-1, 1))
    temp_test = np.roll(x_test, -1)
    temp_train = np.roll(x_train, -1)
    for x in range(1, in_num):
        x_train = np.concatenate((x_train[:-1], temp_train[:-1]), 1)
        x_test = np.concatenate((x_test[:-1], temp_test[:-1]), 1)
        temp_test = np.roll(temp_test, -1)[:-1]
        temp_train = np.roll(temp_train, -1)[:-1]

    return x_train, y_train, x_test, y_test

def mlp(x_train, y_train, x_test, layers:tuple, predictions:int, act:str, solv:str):
    x_test1=copy(x_test)
    
    mlp=MLPRegressor(hidden_layer_sizes=layers, activation=act,
                solver=solv, learning_rate='adaptive',learning_rate_init=0.001, 
                max_iter=2000, random_state=5, tol=0.001, early_stopping=True, verbose=False,
                validation_fraction=0.3).fit(x_train, y_train)

    y_hat_test = []
    for i in range(0, predictions):
        last_prediction = mlp.predict(x_test1)[0]
        y_hat_test.append(last_prediction)

        x_test1[0] = np.roll(x_test1[0], -1)
        x_test1[0, (len(x_test1[0]) - 1)] = last_prediction

    mlp_results=np.asarray(y_hat_test)
    return mlp_results

def save_results(y_test,y_pred, method):
    global y_train

    results={}
    results['MASE']=[]
    results['sMAPE']=[]
    results['Average']=[]
    results['Method']=[]
    
    temp = MeanAbsoluteScaledError()
    mase = temp(y_test,y_pred,y_train=y_train)
    temp = MeanAbsolutePercentageError(symmetric=True)
    smape = temp(y_test,y_pred)
    avg = (mase+smape)/2

    results['MASE'].append(round(mase,2))
    results['sMAPE'].append(round(smape,2))
    results['Average'].append(round(avg,2))
    results['Method'].append(method)
    return pd.DataFrame(results).set_index('Method')

fuels=['Unleaded 95','Diesel','Autogas']
df = fuel_data(fuels)

fuel = st.sidebar.selectbox(
    "Fuel:",
    options=fuels
)

city = st.sidebar.selectbox(
    "Preferacture:",
    options=sorted(df["nomos"].unique().tolist())
)

temp_df=df.query(f'nomos=="{city}"')[fuel]

if adfuller(temp_df)[1]>0.05:
    ts=detrend_deseasonalize(temp_df,'D')
else:
    ts=temp_df

view = st.sidebar.selectbox(
    "View:",
    options=['30 Days','60 Days','All Data']
)

try:
    view=int(view.split(' ')[0])
except:
    view=len(temp_df)


st.header('Features:')
cols= st.columns(3)

fh=cols[2].radio("Future Horizon:",options=[14, 28])

activation = cols[1].selectbox(
    "Activation Function:",
    options=['relu','tanh','logistic','identity'])

solver = cols[1].selectbox(
    "Solver:",
    options=['adam','sgd','lbfgs'])

layer1=cols[0].slider("Layer 1:", min_value=30, max_value=120, step=30)
layer2=cols[0].slider("Layer 2:", min_value=15, max_value=60, step=15)

mode = st.sidebar.radio('Mode:', ('Evaluate','Predict'))
if mode=='Evaluate':
    x_train, y_train, x_test, y_test = split_into_train_test(list(ts),layer1,fh)
    mlpResults = mlp(x_train, y_train, x_test,(layer1,layer2), fh, activation, solver)
    results = save_results(y_test, mlpResults, method ='MLP')

    mlpResults2 = pd.DataFrame(mlpResults.cumsum(),index=temp_df.index[-fh:])
    shift = temp_df[:-fh+1].values[-1]-mlpResults2.values[0][0]

    st.header('Metrics:')
    st.table(results.style.format("{:.3}"))
    fig = go.Figure()
    fig.add_traces(go.Scatter(x=temp_df[-view:].index, y=temp_df[-view:], name=fuel ,  mode = 'lines'))
    fig.add_traces(go.Scatter(x=mlpResults2.index, y=mlpResults2[0]+shift, name='Prediction',  mode = 'lines', line=dict(color='red')))
elif mode=='Predict':
    x_train, y_train, x_test, y_test = split_into_train_test(list(ts),layer1,1)
    mlpResults = mlp(x_train, y_train, x_test,(layer1,layer2), fh, activation, solver)

    future=pd.date_range(start=temp_df.index[-1],periods=fh)
    mlpResults2 = pd.DataFrame(mlpResults.cumsum(),index=future)

    shift = temp_df.values[-1]-mlpResults2.values[0][0]
    fig = go.Figure()
    fig.add_traces(go.Scatter(x=temp_df[-view:].index, y=temp_df[-view:], name=fuel,  mode = 'lines'))
    fig.add_traces(go.Scatter(x=mlpResults2.index, y=mlpResults2[0]+shift, name='Prediction',  mode = 'lines', line=dict(color='red')))

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Euros",
    font=dict(
        family="Arial Black",
        size=12,
    )
)
st.plotly_chart(fig, use_container_width=True)