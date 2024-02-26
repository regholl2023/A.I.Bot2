#!/usr/bin/env python3
"""
augmented dickey fuller
need one month of data points at hourly resolution to test cointegration for my daily method
assumes both data sets are updated to current date
"""
#()()()()()()()()()(NOTES)()()()()()()()()()()
#()()()()()()()()()(NOTES)()()()()()()()()()()

from scipy import stats
import statsmodels.tsa.stattools as ts
import pandas as pd
import matplotlib.pyplot as plt
import datetime

def adf(ticker1,ticker2):
    #retrieve data
    fulldata = pd.read_csv('data/daily.csv',header=0,index_col=0,parse_dates=True)
    #define the relevant series
    rn = datetime.date.today()
    start = rn - datetime.timedelta(365)
    data = fulldata[[ticker1, ticker2]][start:].dropna()
    temp1 = data[ticker1]
    temp2 = data[ticker2]

    #get slope and intercept 
    slope, intercept, r_value, p_value, std_err = stats.linregress(temp1,temp2)
    #use slope and intercept to calculate error
    error = temp2 - (slope * temp1 + intercept)
    #calculate adf p valuef
    result = ts.adfuller(x=error)
    pVal = result[1]

    return pVal
    
