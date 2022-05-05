'''''''''''''''
This is part one of project FuelPrices.

The programm below scrapes http://www.fuelprices.gr/deltia_dn.view
and downloads all pdf files.

Each pdf contains daily fuel prices for every prefecture in Greece.

'''''''''''''''

import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from tkinter import Tk, filedialog
from datetime import datetime
import pickle

url = 'http://www.fuelprices.gr/deltia_dn.view'

root = Tk()
root.withdraw()

to_folder_location = filedialog.askdirectory(title="Select Directory")
from_folder_location = to_folder_location.replace("/", "\\")

'''Failsafe: If askdirectory closed or canceled'''
if to_folder_location=='':
    import sys
    msg="Must pick a directory."
    sys.exit(msg)

'''Creates necessary folders for the pdf scraping part'''
if not os.path.exists(from_folder_location+"\\FuelPriceNomos"):
    os.mkdir(from_folder_location+"\\FuelPriceNomos")
if not os.path.exists(from_folder_location+"\\FuelPriceData"):
    os.mkdir(from_folder_location+"\\FuelPriceData")


'''
Checking for historical data.
With this no collection of old already used pdfs is neaded.
'''
os.chdir(from_folder_location+"/FuelPriceData")
try:
    with open("errors", "rb") as fp:
        errors = pickle.load(fp)
    with open("dates", "rb") as fp:
        dates = pickle.load(fp)
    with open("errors2", "rb") as fp:
        errors2 = pickle.load(fp)
except:
    print("Couldn't find historical data.")
    errors=[]
    errors2=[]
    dates=[]

from_folder_location_nomos=from_folder_location+"\\FuelPriceNomos"
response = requests.get(url)
soup= BeautifulSoup(response.text, "html.parser")     

file_counter=0
print(f'Chosen Directory: {to_folder_location}')
print('**Initializing Web Scraping**')

print('Downloading files...')
for link in soup.select("a[href$='.pdf']"):

    '''Naming the pdf files using the last portion of each link '''
    filename = os.path.join(from_folder_location_nomos,link['href'].split('NOMO')[-1]).replace("_","")


    file=filename.split("\\")[-1]
    d_file=file.split(".")[0]

    '''Unwanted files.'''
    unwanted=["l.pdf","?.pdf",").pdf"]
    if file[-5:] in unwanted:
        pass
    else:
        d1_file=datetime.strptime(d_file, "%d%m%Y").date()

        '''
        Checking if file is in the folder or in historical data. 
        Downloading only new files, so updating is easier.
        
        '''
        if file not in os.listdir(from_folder_location_nomos) and d1_file not in dates and d1_file not in errors and d1_file not in errors2:
            file_counter+=1
            with open(filename, 'wb') as f:
                f.write(requests.get(urljoin(url,link['href'])).content)

print('Downloaded',file_counter,'pdf files.')