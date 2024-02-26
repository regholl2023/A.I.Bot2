#!/usr/bin/env python3

#live trader with mean reversion on alpaca
import matplotlib.pyplot as plt
import datetime
import pandas as pd
import numpy as np
import alpaca_trade_api as tradeapi
from twilio.rest import Client
import logging
logging.basicConfig(filename='/home/jared/Desktop/Trading/alpaca/logger.log')

#verify and get accounts
api = tradeapi.REST('AKWXRMSWW249KVHABZ33', '31cqCd4x19uEI/RZ2lk6dF7jbqES1CISWtTq3U3y','https://paper-api.alpaca.markets')
account = api.get_account()
#twilio
account_sid = "AC75d0955da6c1d381c1c9cb7988cb179b" 
auth_token = "5ef1670787121eec1fa10d2ff125c0ba"
texter = Client(account_sid, auth_token) # get texter
message = ""    #message for reporting trades
#define relevant variables
cash = float(account.cash)
lag = 26
dif = 0.039
tick1 = 'CF'
tick2 = 'RL'

#get data: last 26 prices and current price
end = datetime.datetime.now()
begin = end - datetime.timedelta(lag)
asset1 = api.polygon.historic_agg('day', tick1, begin, end, limit=1000).df
asset2 = api.polygon.historic_agg('day', tick2, begin, end, limit=1000).df

prcs1 = asset1['close'][-lag:]
prcs2 = asset2['close'][-lag:]
p1 = api.polygon.last_quote(tick1)._raw['askprice']
p2 = api.polygon.last_quote(tick2)._raw['askprice']
quantity1 = int(cash // (p1+0.5))
quantity2 = int(cash // (p2+0.5))

#list positions
held1=False
held2=False
qty1=0
qty2=0
value=0.0
positions = api.list_positions()
for l in positions:
    value+=float(l.market_value)
    if l.symbol == tick1:
        held1=True
        qty1=l.qty
    elif l.symbol == tick2:    
        held2=True
        qty2=l.qty

####################################
####################################
#Purchasing #####
def fbuy(ticker,quantity):
    api.submit_order(ticker,quantity,'buy','market','day')
#Selling#####
def fsell(ticker, quantity):
    api.submit_order(ticker,quantity,'sell','market','day')
#Updating#####

#Plotting#####

#Reporting#####
def report():
    print("Total cash: ", cash)
    print("Total value: ",cash+value)
    
def text(message):
    message = texter.messages.create(
    to="+14352276526",
    from_="+14352654408",
    body=message)
####################################
####################################

mva=0.0 
for z in prcs:  #calculate moving average
    mva+=z/lag
message += datetime.datetime.now().strftime('%m/%d/%Y') + ": "
if(p<mva*(1-dif) and quantity>0 and not held): #if price is lower than mva, buy
    try:
        fbuy(ticker,quantity)
        message+="bought %s shares of %s. "%(quantity,ticker)
    except:
        message+="failed to buy %s"%ticker
        logging.exception("failed to buy")
elif(p>mva*(1+dif) and qty!=0.0 and held): #if prf=ice is higher than mva, sell
    try:
        fsell(ticker,qty)
        message+="sold %s shares of %s. "%(qty,ticker)
    except:
        message+="failed to sell"
        logging.exception("failed to sell")
else: # don't buy/sell
    message += "NO TRADE TODAY"
text(message)
file = open("/home/pi/Desktop/Alpaca/livetrading/results.txt","a")
file.write(message + "\n")
file.close()

report()



