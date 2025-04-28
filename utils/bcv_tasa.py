import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from urllib.request import urlopen
from bs4 import BeautifulSoup

def tasa_bs():
    url = "https://www.tcambio.app/"
    html = urlopen(url)

    soup = BeautifulSoup(html, 'lxml')
    type(soup)

    e = soup.find_all('strong')
    cleantext = BeautifulSoup(str(e[0]), "lxml").get_text()
    tasa = float(cleantext)
    return tasa

