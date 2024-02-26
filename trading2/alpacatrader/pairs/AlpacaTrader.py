#!/usr/bin/env python3
import adf

import alpaca_trade_api as tradeapi
from twilio.rest import Client

import csv
import datetime
import logging
import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import smtplib
import time

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

logging.basicConfig(filename='results/trading.log')

class Currency:
    # Holds info on each currency to be traded
    def __init__(self,ticker):
        self.ticker = ticker
        self.ratio = 0.5
        
class AccountData:
    # Account data class do later
    def __init__(self,auth):
        self.client = auth.client

    def getPositions(self):
        try:
            a = self.client.list_positions()
        except Exception as e:
            logging.exception(datetime.datetime.now().strftime('%Y-%m-%d %H:%M')+"error getting positions")
        self.allPositions = {}
        for w in a:
            symbol = w.symbol
            currQty = w.qty      #row many of each future we hold already
            if currQty != 0.0:   # may not need this
                self.allPositions.update({symbol : currQty})
        return self.allPositions

    def getBalances(self):
        try:
            a = self.client.get_account()
        except Exception as e:
            logging.exception(datetime.datetime.now().strftime('%Y-%m-%d %H:%M')+"error getting balances")
        return a
    
    def makePlot(self):
        a = pd.read_csv('results/account_value.csv', index_col=0, header=0, parse_dates=True)
        if len(a.index)>0 and len(a.columns)>0:
            plt.plot(a.index,a['dollars'])
            plt.xticks(rotation=70)
            plt.savefig("results/value_hist.png")
    

class Reporter:
    # Error and message reporting
    def __init__(self,auth):
        self.twilClient = auth.twilClient
        self.phonelist = ['+14352276526']
        self.emaillist = ['jaredclambert@gmail.com']
        self.message = ""
        
    def text(self,message):
        # Text this to the phone list
        try:
            for i in self.phonelist:
              self.twilClient.messages.create(
              to=i,
              from_="+14352654408",
              body=message)
        except Exception as e:
            logging.exception(datetime.datetime.now().strftime('%Y-%m-%d %H:%M')+"error sending text")
            
    def email(self,subject,message):
        # Email this to email list
        try:    
            server = smtplib.SMTP('smtp.gmail.com',587)
            server.starttls()
            server.login("usucodemaster@gmail.com","we are code master")
            for i in self.emaillist:
                msg = MIMEMultipart()
                msg['From']="usucodemaster@gmail.com"
                msg['To']=i
                msg['Subject']=subject
                body = "Alpaca pairs trading algorithm :)"
                msg.attach(MIMEText(message,'plain'))
                text = msg.as_string()
                server.sendmail("usucodemaster@gmail.com",i,text)
        except Exception as e:
            logging.exception("error sending emails")
                
    def save(self,message):
        # Save message into file.
        file = open("results/report.txt","a")
        file.write(message+"\n")
        file.close()
        #next function:
        #parse the result. get the html return codes. if it's successful then somehow text it out....log it.  

class Executor:
    # Executes trades after decision is made
    def __init__(self, trade1, trade2, tradeDetails, reporter, auth, accountData):
        self.client = auth.client
        self.trade1 = trade1
        self.trade2 = trade2
        self.reporter = reporter
        self.accountData = accountData
        self.results = []
        self.td = tradeDetails
        self.message = ""
        self.tradeable = auth.tradeable
        
    def execute(self):
        # Execute trades
        # LIST DETAILS
        ##########
        positions = self.accountData.getPositions()  #get positions
        self.message += datetime.datetime.today().strftime('%Y-%m-%d %H:%M') + "\n"  #get date
        #get current spread difference and the limit
        self.message += ("dif: "+ str(self.td.dif)+" curr dif: "+str('%.3f'%self.td.sprdif)+"\n")

        for x , y in positions.items():
            if x == self.trade1.symbol or x == self.trade2.symbol:
                self.message += str(x)+":"+str(y) + "\n"  #format positions

        # MAKE TRADES
        if(self.trade2.trade and self.trade1.trade and self.tradeable):
            self.trade1.newQty = int(self.trade1.newQty)
            self.trade1.balanceQty = int(self.trade1.balanceQty)
            self.trade2.newQty = int(self.trade2.newQty)
            self.trade2.balanceQty = int(self.trade2.balanceQty)
            print(self.trade1.newQty,self.trade1.balanceQty,self.trade2.newQty,self.trade2.balanceQty)
            try:
                if self.trade1.balanceQty > 0:
                    self.results.append(self.client.submit_order(self.trade1.symbol,
                                                                    self.trade1.balanceQty,
                                                                    self.trade1.side,
                                                                    'market','day'))
                if self.trade2.balanceQty > 0:
                    self.results.append(self.client.submit_order(self.trade2.symbol,
                                                                    self.trade2.balanceQty,
                                                                    self.trade2.side,
                                                                    'market','day'))
                time.sleep(5)
                self.results.append(self.client.submit_order(self.trade1.symbol,
                                                                self.trade1.newQty,
                                                                self.trade1.side,
                                                                'market','day'))
                self.results.append(self.client.submit_order(self.trade2.symbol,
                                                                self.trade2.newQty,
                                                                self.trade2.side,
                                                                'market','day'))
            except Exception as e:
                self.message += "Error in execution\n"
                logging.exception(e._error['message'])
                self.reporter.text(self.message)
                self.reporter.email("ERROR!",self.message)

            dataDf = pd.read_csv('results/trades.csv', header=0, index_col=0, parse_dates=True)
            dataAppend = []
            for i in range(len(self.results)):
                x = self.results[i]
                self.message += "%s of %s %s at %s.\n"%(x.side,x.qty,x.symbol,self.td.currPrices[x.symbol])                     
                dataAppend.append([x.symbol,x.side,x.qty,self.td.currPrices[x.symbol],datetime.date.today()])
            for i in range(len(dataAppend)):
                dataDf.loc[len(dataDf.index)] = dataAppend[i]
            dataDf.to_csv('results/trades.csv')

        else:
            self.message += "NO TRADE\n"  
        self.reporter.save(self.message)
        self.accountData.makePlot()

class Authenticator:
    # Authenticates API clients
    def __init__(self):
        try:
            self.client = tradeapi.REST('PK13VHG72L8ZTSPQ5S6D', 'jk4CzKaN5hZurhTk5iO5l46QTdoHY8nqdfXRqt5o',
                                         'https://paper-api.alpaca.markets',api_version='v2')
            self.twilClient = Client("AC75d0955da6c1d381c1c9cb7988cb179b", "5ef1670787121eec1fa10d2ff125c0ba")
        except Exception as e:
            logging.exception(datetime.datetime.now().strftime('%Y-%m-%d %H:%M')+"error authenticating")
        currentTime = datetime.datetime.now().time()
        viableDate = datetime.date.today() in pd.read_csv('data/calendar.csv', header = 0, index_col = 0, parse_dates = True).index
        viableTime =  currentTime > datetime.time(7,30,0,0) and currentTime < datetime.time(14,0,0,0)
        self.tradeable = viableDate and viableTime


class PairsInfo:
    # Contains information on the pair to be traded
    def __init__(self,currency1, currency2, ratio2=0.5):
        self.currency1 = currency1     
        self.currency2 = currency2
        self.currency1.ratio = (1-ratio2)
        self.currency2.ratio = ratio2
        self.pairs_lags = pd.read_csv("data/pairs_lags.csv", index_col = 0, header = 0)
        self.pairs_difs = pd.read_csv("data/pairs_difs.csv", index_col = 0, header = 0)

    def getParams(self):
        # Get parameters for pairs trading (lag, % dif)
        return self.pairs_lags[self.currency1.ticker][self.currency2.ticker],self.pairs_difs[self.currency1.ticker][self.currency2.ticker]


class Trade:
    # Class to pass trade information on to be executed.
    def __init__(self, trade, symbol, side, newQty, balanceQty):
        self.trade = trade    #execute trade or not
        self.symbol = symbol  #trade symbol/ticker
        self.side = side      #buy or sell
        self.newQty = newQty        #quantity in transaction
        self.balanceQty = balanceQty #quantity to get back to 0


class Details:
    # Another class to return, gives info to be printed for reports
    def __init__(self, dif, lag, sprdif, currPrices):
        self.dif = dif                #spread difference limit (%)
        self.lag = lag                #current lag setting
        self.sprdif = sprdif          #curr spread difference (%)
        self.currPrices = currPrices  #curr price of asset 1 & 2


class Decider:
    # Decide whether to trade or not
    def __init__(self, pairInfo, numPairs, accountData, auth, reporter):
        self.pairInfo = pairInfo
        self.accountData = accountData
        self.reporter = reporter
        self.numPairs = numPairs

    def getCurrQty(self, allPositions, currency1, currency2):
        # Get the quantities of assets currently held
        currQty1 = currQty2 = 0
        for key, value in allPositions.items():
            if key == currency1.ticker:
                currQty1=float(value)
            if key == currency2.ticker:
                currQty2=float(value)
        return currQty1, currQty2

    def writeAccountBalance(self, allBalances):
        # Record my account value to use later and to graph
        equity_usd = float(allBalances.portfolio_value)
        rn = datetime.date.today()
        valueDf = pd.read_csv('results/account_value.csv', header=0, index_col=0, parse_dates=True)
        valueDf.loc[rn] = equity_usd
        valueDf.to_csv('results/account_value.csv')

        return equity_usd

    def getHistoricalPrices(self, lag, currency1, currency2):
        # Get price data frames
        toRead = 'data/daily.csv'
        data = pd.read_csv(toRead, header=0, index_col=0, parse_dates=True)
        prcs1 = data[currency1.ticker][-(lag+1):-1]
        prcs2 = data[currency2.ticker][-(lag+1):-1]
        p1 = data[currency1.ticker][-1]
        p2 = data[currency2.ticker][-1]
        return prcs1, prcs2, p1, p2

    def getOrderQty(self, equity_usd, fraction, p, currQty):
        # Get quantity of potential trade
        return int(equity_usd*fraction/p/self.numPairs), abs(currQty)

    def checkAdf(self, currency1, currency2):
        # Perform augmented dickey-fuller test to confirm cointegration
        pval = adf.adf(currency1.ticker,currency2.ticker)
        if(pval > 0.01):
            with open('results/cointegration.csv','a') as file:
                file.write(currency1.ticker + ', ' + currency2.ticker + ', ' + str(pval) + '\n')
            #self.reporter.email("CRITICAL","cointegration failing %.3f"%pval)

    def checkErrors(self, trade1, trade2):
        # Look for errors in the details of potential trade
        if(trade1.trade==True and trade2.trade==True and trade1.side==trade2.side):
            logging.critical("trading same side")
            #self.reporter.text("trading same side")
            self.reporter.email("CRITICAL", "trading same side")

    def decide(self, prcs1, prcs2, p1, p2, lag, spreaddif, currQty1, currQty2, currency1, currency2, newQty1, newQty2, balanceQty1, balanceQty2):
        # Prepare simple moving averages and decide whether to trade, which side to trade
        mva1=0.0
        mva2=0.0
        trade1 = Trade(trade=False,symbol='',side='',newQty=0, balanceQty=0) #initialize trade object
        trade2 = Trade(trade=False,symbol='',side='',newQty=0, balanceQty=0) #initialize trade object
        for z in range(lag):
            mva1+=(prcs1[z])/lag      #mva of asset 1 in USD
            mva2+=(prcs2[z])/lag      #mva of asset 2 in USD
        currentSpread = p1-p2       #calculate spreads
        averageSpread = mva1-mva2   #^^
        # Logic to purchase/sell if spread is too big
        # Buy currency 2 and sell currency 1
        if (currentSpread > averageSpread * (1.0 + spreaddif)):
            if (currQty2 == 0 or currQty2 < 0):
                trade1 = Trade(trade=True,symbol=currency1.ticker, side='sell', newQty=newQty1,
                               balanceQty=balanceQty1)
                trade2 = Trade(trade=True,symbol=currency2.ticker, side='buy', newQty=newQty2,
                               balanceQty=balanceQty2)
        # Logic to purchase/sell if spread is too small
        # Buy currency 1 and sell currency 2
        elif(currentSpread < averageSpread * (1.0 - spreaddif)):
            if (currQty2 == 0 or currQty2 > 0):
                trade1 = Trade(trade=True,symbol=currency1.ticker, side='buy', newQty=newQty1,
                               balanceQty=balanceQty1)
                trade2 = Trade(trade=True,symbol=currency2.ticker, side='sell', newQty=newQty2,
                               balanceQty=balanceQty2)
        tradeDetails = Details(dif=spreaddif, lag=lag, sprdif=(currentSpread-averageSpread)/averageSpread,currPrices={currency1.ticker:p1,currency2.ticker:p2})
        return trade1, trade2, tradeDetails

    def tradeit(self):
        # Run all trade decision methods 
        #INITIALIZING IMPORTANT VARIABLES
        currency1 = self.pairInfo.currency1                     #contain info for btc
        currency2 = self.pairInfo.currency2                     #contain info for bch
        lag, spreaddif = self.pairInfo.getParams()              #lag,dif to be used, generated from file
        allPositions = self.accountData.getPositions()          #get current positions
        allBalances = self.accountData.getBalances()            #get balances: equity,margin level, etc
        fraction1 = currency1.ratio
        fraction2 = currency2.ratio

        #GETTING CURRENT POSITIONS
        currQty1, currQty2 = self.getCurrQty(allPositions, currency1, currency2)
        #GETTING ACCOUNT BALANCES
        equity_usd = self.writeAccountBalance(allBalances)
        #GET HISTORICAL PRICES FOR BTC AND BCH
        prcs1, prcs2, p1, p2 = self.getHistoricalPrices(lag, currency1, currency2)
        #GET QUANTITIES FOR ORDERS
        newQty1, balanceQty1 = self.getOrderQty(equity_usd, fraction1, p1, currQty1)
        newQty2, balanceQty2 = self.getOrderQty(equity_usd, fraction2, p2, currQty2)
        #DECIDE
        trade1, trade2, tradeDetails = self.decide(prcs1, prcs2, p1, p2, lag, spreaddif, currQty1, currQty2,
                                                   currency1, currency2, newQty1, newQty2,
                                                   balanceQty1, balanceQty2
                                                  )
        #CHECK ADF
        self.checkAdf(currency1, currency2)
        #CHECK FOR ERRORS IN TRADE DECISION
        self.checkErrors(trade1, trade2)

        return(trade1, trade2, tradeDetails)


class GetPrices:
    # Class to update historical prices and get current price
    def __init__(self,auth):
        self.client = auth.client
        self.tradeable = auth.tradeable
        self.now = datetime.datetime.now()
    def update(self):
        # Append new prices to data file
        # If market is open
        # For every stock in the prices dataframe
        df = pd.read_csv('data/daily.csv', header=0, index_col=0, parse_dates=True)
        tickers = df.columns
        prices = []
        if(self.tradeable):
            for tick in tickers:
                p1 = 0.
                # Get the price
                try:
                    p1 = self.client.polygon.last_quote(tick)._raw['askprice']
                except Exception as e:
                    p1=df[tick][-1]
                    logging.exception(self.now.strftime('%Y-%m-%d %H:%M')+" failed to retrieve %s price" %tick)
                prices.append(p1)

            # Add prices onto dataframe
            df.loc[datetime.date.today()] = prices

            # Write dataframe to file
            df.to_csv('data/daily.csv')

