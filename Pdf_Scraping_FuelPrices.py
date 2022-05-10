'''''''''''''''

This is part two of project FuelPrices.

Part one of the programm scraped http://www.fuelprices.gr/deltia_dn.view
and downloaded all pdf files.

In this part the programm reads all pdfs and gets table data for each one.
Each table contains daily fuel prices for every prefecture in Greece.

The ojective of this programm is to create a concatenated file with all the information.


'''''''''''''''

import camelot
import os
import pandas as pd
from datetime import datetime
import numpy as np
import pickle
import warnings
from tqdm.auto import tqdm


print('**Initializing Pdf Scraping**')
from Web_Scraping_FuelPrices import to_folder_location, from_folder_location
warnings.filterwarnings("ignore")


'''
If the process is completed, it retaines necessary lists.
Doing that the process in much faster the next time.
Also provides the opportunity to update the data in the future.

'''


'''Checking if historical data are found, else start from scratch'''
if os.path.exists(from_folder_location+"\\FuelPriceData"):
    os.chdir(to_folder_location+"/FuelPriceData")
    try:
        with open("errors", "rb") as fp:
            errors = pickle.load(fp)
        with open("dates", "rb") as fp:
            dates = pickle.load(fp)
        with open("pdfs", "rb") as fp:
            pdfs = pickle.load(fp)
        with open("errors2", "rb") as fp:
            errors2 = pickle.load(fp)
    except:
        print("Couldn't find historical data.")
        pdfs = []
        errors=[]
        errors2=[]
        dates=[]
else:
    os.mkdir(from_folder_location)
    pdfs = []
    errors=[]
    errors2=[]
    dates=[]

'''
Reading pdf tables. 
Some pdfs include the desired table in one page,
while others have the table in two parts.

'''

'''Errors is a list with malformed pdfs'''

os.chdir(to_folder_location+"/FuelPriceNomos")
filenames =os.listdir()
number=0
for i in tqdm(range(len(filenames))):

    d=filenames[i].split(".")[0]
    d1=datetime.strptime(d, "%d%m%Y").date()

    if d1 not in dates and d1 not in errors and d1 not in errors2:
        number+=1
        try:
            temp_table=camelot.read_pdf(filenames[i],pages='1,2')
            try:
                dates.append(d1)

                a=temp_table[0].df
                b=temp_table[1].df
                c=pd.concat([a,b])

                c.reset_index(inplace=True,drop=True)  
                pdfs.append(c)

            except:
                errors.append(d1)
        except:
            dates.append(d1)

            temp_table=camelot.read_pdf(filenames[i])
            pdfs.append(temp_table[0].df)

print(f"Added {number} Files")

'''Saving desired lists in order to update files in the future'''
os.chdir(to_folder_location+"/FuelPriceData")

with open('pdfs', "wb") as fp:
    pickle.dump(pdfs, fp)
with open('errors', "wb") as fp:
    pickle.dump(errors, fp)
with open('dates', "wb") as fp:
    pickle.dump(dates, fp)

'''Check if errors are excluded'''
try:
    for i in range(len(errors)):
        dates.remove(errors[i])
except ValueError:
    pass

'''Special reforming in needed for some pdfs'''
dfs=[]
for i in range(len(pdfs)):

    if len(pdfs[i])==52:
        temp = pdfs[i]
    else:
        temp = pdfs[i][1:]

    if len(pdfs[i].columns)==1:
        temp = pdfs[i][0][1:]
        temp = temp.str.split('\n', 7, expand=True)

    dfs.append(temp)

'''Cleaning process'''
print("Cleaning the data...")
errors2_index=[]
for i in tqdm(range(len(dfs))):
    try:
        dfs[i][0]=['N. ATTIKIS','N. ETOLOAKARNANIAS','N. ARGOLIDAS','N. ARKADIAS','N. ARTAS','N. ACHAIAS','N. VIOTIAS','N. GREVENON','N. DRAMAS',
        'N. DODEKANISON','N. EVROU','N. EVVIAS','N. EVRYTANIAS','N. ZAKYNTHOU','N. ILIAS','N. IMATHIAS','N. IRAKLIOU','N. THESPROTIAS','N. THESSALONIKIS',
        'N. IOANNINON','N. KAVALAS','N. KARDITSAS','N. KASTORIAS','N. KERKYRAS','N. KEFALLONIAS','N. KILKIS','N. KOZANIS','N. KORINTHOU','N. KYKLADON',
        'N. LAKONIAS','N. LARISAS','N. LASITHIOU','N. LESVOU','N. LEFKADAS','N. MAGNISIAS','N. MESSINIAS','N. XANTHIS','N. PELLAS','N. PIERIAS','N. PREVEZAS',
        'N. RETHYMNOU','N. RODOPIS','N. SAMOU','N. SERRON','N. TRIKALON','N. FTHIOTIDAS','N. FLORINAS','N. FOKIDAS','N. CHALKIDIKIS','N. CHANION','N. CHIOU','all']
        dfs[i].set_index(0,inplace=True)

        dfs[i]=dfs[i].apply(lambda x: x.astype(str).str.strip())
        dfs[i].replace({'-':'', 'nan':'', '0,0':'', 'None':'' }, regex=True, inplace=True)
        dfs[i]=dfs[i].apply(lambda x: x.str.replace(',','.')).apply(pd.to_numeric)  

    except ValueError:
        errors2.append(dates[i])
        errors2_index.append(i)

'''Errors2 is a list with pdfs that cant be formated properly'''
with open('errors2', "wb") as fp:
    pickle.dump(errors2, fp)

'''Exclude errors2'''
for i in sorted(errors2_index, reverse=True):
    del dfs[i]
    del dates[i]


'''Create one concatenated df, named all_data, and save as csv'''
all_data=pd.concat(dfs,keys=dates)
all_data=all_data.drop(6,axis=1)
all_data=all_data.replace( 0, np.nan).round(3).sort_index()
all_data.index.set_names(['date','nomos'],inplace=True)
all_data.columns=['Unleaded 95','Unleaded 100','Super','Diesel','Autogas']

os.chdir(to_folder_location)
all_data.to_csv('nomos.csv')
print("Created nomos.csv")